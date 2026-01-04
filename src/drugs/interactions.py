"""Drug interaction checking system."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.config import settings
from .umls import UMLSClient


class InteractionSeverity(str, Enum):
    """Drug interaction severity levels."""

    CONTRAINDICATED = "contraindicated"
    SEVERE = "severe"
    MODERATE = "moderate"
    MILD = "mild"
    UNKNOWN = "unknown"


@dataclass
class DrugInfo:
    """Normalized drug information."""

    original_name: str
    rxcui: str | None
    normalized_name: str
    drug_classes: list[str]


@dataclass
class DrugInteraction:
    """Drug interaction details."""

    drug1: str
    drug2: str
    severity: InteractionSeverity
    description: str
    clinical_effects: str
    management: str
    source: str


class DrugInteractionChecker:
    """
    Check drug-drug interactions using RxNorm and clinical databases.

    Provides:
    - Drug name normalization via RxNorm
    - Interaction checking via NDF-RT
    - Severity classification
    - Clinical management suggestions
    """

    # Common severe interaction patterns (offline fallback)
    KNOWN_SEVERE_INTERACTIONS = {
        ("warfarin", "aspirin"): {
            "severity": InteractionSeverity.SEVERE,
            "description": "Increased risk of bleeding",
            "management": "Monitor INR closely, consider alternative antiplatelet",
        },
        ("metformin", "contrast"): {
            "severity": InteractionSeverity.SEVERE,
            "description": "Risk of lactic acidosis with iodinated contrast",
            "management": "Hold metformin 48h before and after contrast",
        },
        ("ssri", "maoi"): {
            "severity": InteractionSeverity.CONTRAINDICATED,
            "description": "Serotonin syndrome risk",
            "management": "Contraindicated - 14 day washout required",
        },
        ("ace_inhibitor", "potassium"): {
            "severity": InteractionSeverity.MODERATE,
            "description": "Hyperkalemia risk",
            "management": "Monitor potassium levels regularly",
        },
        ("statin", "fibrate"): {
            "severity": InteractionSeverity.MODERATE,
            "description": "Increased myopathy risk",
            "management": "Use lowest effective statin dose, monitor for muscle symptoms",
        },
        ("digoxin", "amiodarone"): {
            "severity": InteractionSeverity.SEVERE,
            "description": "Digoxin toxicity risk - amiodarone increases digoxin levels",
            "management": "Reduce digoxin dose by 50%, monitor levels",
        },
        ("lithium", "nsaid"): {
            "severity": InteractionSeverity.SEVERE,
            "description": "NSAIDs reduce lithium clearance, increasing toxicity risk",
            "management": "Avoid combination or monitor lithium levels closely",
        },
        ("methotrexate", "nsaid"): {
            "severity": InteractionSeverity.SEVERE,
            "description": "NSAIDs reduce methotrexate clearance",
            "management": "Avoid high-dose NSAIDs, monitor for toxicity",
        },
    }

    # Drug class mappings for offline matching
    DRUG_CLASSES = {
        "ssri": [
            "fluoxetine", "sertraline", "paroxetine", "citalopram",
            "escitalopram", "fluvoxamine",
        ],
        "maoi": [
            "phenelzine", "tranylcypromine", "isocarboxazid", "selegiline",
            "moclobemide",
        ],
        "ace_inhibitor": [
            "lisinopril", "enalapril", "ramipril", "captopril", "benazepril",
            "fosinopril", "quinapril", "perindopril",
        ],
        "statin": [
            "atorvastatin", "simvastatin", "rosuvastatin", "pravastatin",
            "lovastatin", "fluvastatin", "pitavastatin",
        ],
        "fibrate": [
            "gemfibrozil", "fenofibrate", "bezafibrate", "ciprofibrate",
        ],
        "nsaid": [
            "ibuprofen", "naproxen", "diclofenac", "indomethacin", "celecoxib",
            "meloxicam", "piroxicam", "ketorolac",
        ],
        "potassium": [
            "potassium chloride", "potassium citrate", "k-dur", "klor-con",
        ],
    }

    def __init__(
        self,
        umls_client: UMLSClient | None = None,
        offline_mode: bool = False,
    ):
        """
        Initialize drug interaction checker.

        Args:
            umls_client: UMLS/RxNorm client.
            offline_mode: Use only local data.
        """
        self.umls = umls_client or UMLSClient()
        self.offline_mode = offline_mode
        self._drug_cache: dict[str, DrugInfo] = {}

    def normalize_drug(self, drug_name: str) -> DrugInfo:
        """
        Normalize a drug name to standard form.

        Args:
            drug_name: Free-text drug name.

        Returns:
            DrugInfo with normalized details.
        """
        drug_lower = drug_name.lower().strip()

        if drug_lower in self._drug_cache:
            return self._drug_cache[drug_lower]

        # Try RxNorm lookup if online
        rxcui = None
        normalized_name = drug_name
        drug_classes = []

        if not self.offline_mode:
            result = self.umls.normalize_drug_name(drug_name)
            if result:
                rxcui = result["rxcui"]
                normalized_name = result["name"]

                # Get drug classes
                classes = self.umls.get_drug_class(rxcui)
                drug_classes = [c["class_name"] for c in classes]

        # Offline class matching
        if not drug_classes:
            for class_name, drugs in self.DRUG_CLASSES.items():
                if any(d in drug_lower for d in drugs):
                    drug_classes.append(class_name)

        info = DrugInfo(
            original_name=drug_name,
            rxcui=rxcui,
            normalized_name=normalized_name,
            drug_classes=drug_classes,
        )

        self._drug_cache[drug_lower] = info
        return info

    def check_interaction(
        self,
        drug1: str,
        drug2: str,
    ) -> DrugInteraction | None:
        """
        Check for interaction between two drugs.

        Args:
            drug1: First drug name.
            drug2: Second drug name.

        Returns:
            DrugInteraction if found, None otherwise.
        """
        info1 = self.normalize_drug(drug1)
        info2 = self.normalize_drug(drug2)

        # Try online lookup first
        if not self.offline_mode and info1.rxcui and info2.rxcui:
            interactions = self.umls.get_multi_interactions(
                [info1.rxcui, info2.rxcui]
            )

            if interactions:
                inter = interactions[0]
                return DrugInteraction(
                    drug1=info1.normalized_name,
                    drug2=info2.normalized_name,
                    severity=self._parse_severity(inter.get("severity", "")),
                    description=inter.get("description", ""),
                    clinical_effects=inter.get("description", ""),
                    management="Consult clinical resources for specific guidance",
                    source=inter.get("source", "RxNorm"),
                )

        # Offline fallback - check known patterns
        return self._check_offline(info1, info2)

    def _check_offline(
        self,
        info1: DrugInfo,
        info2: DrugInfo,
    ) -> DrugInteraction | None:
        """Check interactions using offline data."""
        drug1_lower = info1.original_name.lower()
        drug2_lower = info2.original_name.lower()

        # Check direct drug name matches
        for (d1, d2), details in self.KNOWN_SEVERE_INTERACTIONS.items():
            if (d1 in drug1_lower and d2 in drug2_lower) or (
                d2 in drug1_lower and d1 in drug2_lower
            ):
                return DrugInteraction(
                    drug1=info1.normalized_name or info1.original_name,
                    drug2=info2.normalized_name or info2.original_name,
                    severity=details["severity"],
                    description=details["description"],
                    clinical_effects=details["description"],
                    management=details["management"],
                    source="Dora Offline Database",
                )

        # Check drug class matches
        classes1 = set(info1.drug_classes)
        classes2 = set(info2.drug_classes)

        for (c1, c2), details in self.KNOWN_SEVERE_INTERACTIONS.items():
            if (c1 in classes1 and c2 in classes2) or (
                c2 in classes1 and c1 in classes2
            ):
                return DrugInteraction(
                    drug1=info1.normalized_name or info1.original_name,
                    drug2=info2.normalized_name or info2.original_name,
                    severity=details["severity"],
                    description=details["description"],
                    clinical_effects=details["description"],
                    management=details["management"],
                    source="Dora Offline Database",
                )

        return None

    def check_multiple(
        self,
        drugs: list[str],
    ) -> list[DrugInteraction]:
        """
        Check interactions among multiple drugs.

        Args:
            drugs: List of drug names.

        Returns:
            List of all interactions found.
        """
        interactions = []

        # Normalize all drugs first
        infos = [self.normalize_drug(d) for d in drugs]

        # Try online multi-drug check
        if not self.offline_mode:
            rxcuis = [i.rxcui for i in infos if i.rxcui]
            if len(rxcuis) >= 2:
                online_interactions = self.umls.get_multi_interactions(rxcuis)
                for inter in online_interactions:
                    interactions.append(
                        DrugInteraction(
                            drug1=inter.get("drugs", ["", ""])[0],
                            drug2=inter.get("drugs", ["", ""])[1]
                            if len(inter.get("drugs", [])) > 1
                            else "",
                            severity=self._parse_severity(
                                inter.get("severity", "")
                            ),
                            description=inter.get("description", ""),
                            clinical_effects=inter.get("description", ""),
                            management="Consult clinical resources",
                            source=inter.get("source", "RxNorm"),
                        )
                    )

        # Check pairwise for offline data
        for i in range(len(infos)):
            for j in range(i + 1, len(infos)):
                offline_inter = self._check_offline(infos[i], infos[j])
                if offline_inter:
                    # Avoid duplicates
                    exists = any(
                        (x.drug1 == offline_inter.drug1 and x.drug2 == offline_inter.drug2)
                        or (x.drug1 == offline_inter.drug2 and x.drug2 == offline_inter.drug1)
                        for x in interactions
                    )
                    if not exists:
                        interactions.append(offline_inter)

        return interactions

    def check_patient_medications(
        self,
        current_medications: list[str],
        new_medication: str,
    ) -> list[DrugInteraction]:
        """
        Check if a new medication interacts with current medications.

        Args:
            current_medications: List of current medication names.
            new_medication: New medication being considered.

        Returns:
            List of interactions with the new medication.
        """
        interactions = []

        new_info = self.normalize_drug(new_medication)

        for current in current_medications:
            current_info = self.normalize_drug(current)
            interaction = self.check_interaction(new_medication, current)
            if interaction:
                interactions.append(interaction)

        return interactions

    def _parse_severity(self, severity_str: str) -> InteractionSeverity:
        """Parse severity string to enum."""
        severity_lower = severity_str.lower()

        if "contraindicated" in severity_lower:
            return InteractionSeverity.CONTRAINDICATED
        elif "severe" in severity_lower or "high" in severity_lower:
            return InteractionSeverity.SEVERE
        elif "moderate" in severity_lower:
            return InteractionSeverity.MODERATE
        elif "mild" in severity_lower or "minor" in severity_lower:
            return InteractionSeverity.MILD
        else:
            return InteractionSeverity.UNKNOWN

    def format_warning(self, interaction: DrugInteraction) -> str:
        """
        Format interaction as clinical warning.

        Args:
            interaction: Drug interaction details.

        Returns:
            Formatted warning string.
        """
        severity_emoji = {
            InteractionSeverity.CONTRAINDICATED: "🚫",
            InteractionSeverity.SEVERE: "⚠️",
            InteractionSeverity.MODERATE: "⚡",
            InteractionSeverity.MILD: "ℹ️",
            InteractionSeverity.UNKNOWN: "❓",
        }

        emoji = severity_emoji.get(interaction.severity, "❓")

        return (
            f"{emoji} {interaction.severity.value.upper()}: "
            f"{interaction.drug1} + {interaction.drug2}\n"
            f"   Effect: {interaction.description}\n"
            f"   Management: {interaction.management}\n"
            f"   Source: {interaction.source}"
        )

    def close(self):
        """Close underlying clients."""
        if self.umls:
            self.umls.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
