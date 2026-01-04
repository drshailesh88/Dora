"""UMLS and RxNorm integration for drug data."""

import json
from pathlib import Path
from typing import Optional

import httpx

from src.core.config import settings


class UMLSClient:
    """
    Client for UMLS Terminology Services.

    Provides access to RxNorm for drug normalization and
    NDF-RT for drug interactions.
    """

    RXNORM_API = "https://rxnav.nlm.nih.gov/REST"
    UMLS_API = "https://uts-ws.nlm.nih.gov/rest"

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = None,
    ):
        """
        Initialize UMLS client.

        Args:
            api_key: UMLS API key (optional for RxNorm).
            cache_dir: Directory for caching responses.
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or Path.home() / ".dora" / "umls_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = None

    @property
    def client(self) -> httpx.Client:
        """Lazy HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def normalize_drug_name(self, drug_name: str) -> dict | None:
        """
        Normalize drug name to RxNorm concept.

        Args:
            drug_name: Free-text drug name.

        Returns:
            Dict with rxcui, name, and tty or None.
        """
        cache_key = f"normalize_{drug_name.lower().replace(' ', '_')}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            response = self.client.get(
                f"{self.RXNORM_API}/rxcui.json",
                params={"name": drug_name, "search": 1},
            )
            response.raise_for_status()
            data = response.json()

            if "idGroup" in data and "rxnormId" in data["idGroup"]:
                rxcui = data["idGroup"]["rxnormId"][0]
                result = self._get_rxcui_properties(rxcui)
                self._set_cached(cache_key, result)
                return result

        except Exception:
            pass

        # Try approximate match
        try:
            response = self.client.get(
                f"{self.RXNORM_API}/approximateTerm.json",
                params={"term": drug_name, "maxEntries": 1},
            )
            response.raise_for_status()
            data = response.json()

            candidates = data.get("approximateGroup", {}).get("candidate", [])
            if candidates:
                rxcui = candidates[0]["rxcui"]
                result = self._get_rxcui_properties(rxcui)
                self._set_cached(cache_key, result)
                return result

        except Exception:
            pass

        return None

    def _get_rxcui_properties(self, rxcui: str) -> dict:
        """Get properties for an RxCUI."""
        try:
            response = self.client.get(
                f"{self.RXNORM_API}/rxcui/{rxcui}/properties.json"
            )
            response.raise_for_status()
            data = response.json()

            props = data.get("properties", {})
            return {
                "rxcui": rxcui,
                "name": props.get("name", ""),
                "tty": props.get("tty", ""),  # Term type
                "synonym": props.get("synonym", ""),
            }
        except Exception:
            return {"rxcui": rxcui, "name": "", "tty": ""}

    def get_drug_class(self, rxcui: str) -> list[dict]:
        """
        Get drug classes for an RxCUI.

        Args:
            rxcui: RxNorm concept ID.

        Returns:
            List of drug classes.
        """
        cache_key = f"class_{rxcui}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            response = self.client.get(
                f"{self.RXNORM_API}/rxclass/class/byRxcui.json",
                params={"rxcui": rxcui},
            )
            response.raise_for_status()
            data = response.json()

            classes = []
            for entry in data.get("rxclassDrugInfoList", {}).get(
                "rxclassDrugInfo", []
            ):
                class_info = entry.get("rxclassMinConceptItem", {})
                classes.append(
                    {
                        "class_id": class_info.get("classId", ""),
                        "class_name": class_info.get("className", ""),
                        "class_type": class_info.get("classType", ""),
                    }
                )

            self._set_cached(cache_key, classes)
            return classes

        except Exception:
            return []

    def get_interactions(self, rxcui: str) -> list[dict]:
        """
        Get drug interactions for an RxCUI.

        Args:
            rxcui: RxNorm concept ID.

        Returns:
            List of interaction details.
        """
        cache_key = f"interactions_{rxcui}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            response = self.client.get(
                f"{self.RXNORM_API}/interaction/interaction.json",
                params={"rxcui": rxcui},
            )
            response.raise_for_status()
            data = response.json()

            interactions = []
            for group in data.get("interactionTypeGroup", []):
                for itype in group.get("interactionType", []):
                    for pair in itype.get("interactionPair", []):
                        concepts = pair.get("interactionConcept", [])
                        if len(concepts) >= 2:
                            # Get the other drug in the pair
                            other = None
                            for c in concepts:
                                if c.get("minConceptItem", {}).get("rxcui") != rxcui:
                                    other = c.get("minConceptItem", {})
                                    break

                            if other:
                                interactions.append(
                                    {
                                        "interacting_drug": other.get("name", ""),
                                        "interacting_rxcui": other.get("rxcui", ""),
                                        "description": pair.get("description", ""),
                                        "severity": pair.get("severity", "unknown"),
                                        "source": group.get("sourceName", ""),
                                    }
                                )

            self._set_cached(cache_key, interactions)
            return interactions

        except Exception:
            return []

    def get_multi_interactions(self, rxcuis: list[str]) -> list[dict]:
        """
        Get interactions between multiple drugs.

        Args:
            rxcuis: List of RxNorm concept IDs.

        Returns:
            List of interactions found.
        """
        if len(rxcuis) < 2:
            return []

        cache_key = f"multi_{'_'.join(sorted(rxcuis))}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            response = self.client.get(
                f"{self.RXNORM_API}/interaction/list.json",
                params={"rxcuis": "+".join(rxcuis)},
            )
            response.raise_for_status()
            data = response.json()

            interactions = []
            for group in data.get("fullInteractionTypeGroup", []):
                for itype in group.get("fullInteractionType", []):
                    for pair in itype.get("interactionPair", []):
                        concepts = pair.get("interactionConcept", [])
                        drug_names = [
                            c.get("minConceptItem", {}).get("name", "")
                            for c in concepts
                        ]
                        interactions.append(
                            {
                                "drugs": drug_names,
                                "description": pair.get("description", ""),
                                "severity": pair.get("severity", "unknown"),
                                "source": group.get("sourceName", ""),
                            }
                        )

            self._set_cached(cache_key, interactions)
            return interactions

        except Exception:
            return []

    def _get_cached(self, key: str) -> dict | list | None:
        """Get cached response."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _set_cached(self, key: str, data: dict | list):
        """Cache response."""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def close(self):
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
