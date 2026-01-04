"""
Alert System

Research papers, guideline updates, drug recalls, and safety alerts.
Personalized by specialty and usage patterns.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.engagement.models import (
    ResearchAlert,
    GuidelineUpdate,
    DrugAlert,
    AlertSeverity,
)


class AlertManager:
    """Manages medical alerts for users."""

    def __init__(self):
        """Initialize alert manager."""
        self.pubmed_api_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.alert_cache = {}

    async def create_research_alert(
        self,
        user_id: str,
        specialty: str,
        paper_data: dict[str, Any],
        relevance_score: float,
    ) -> ResearchAlert:
        """
        Create research paper alert.

        Args:
            user_id: User ID to notify
            specialty: User's specialty
            paper_data: Paper metadata from PubMed
            relevance_score: Relevance score (0-1)

        Returns:
            ResearchAlert object
        """
        # Extract key findings from abstract
        abstract = paper_data.get("abstract", "")
        key_findings = self._extract_key_findings(abstract)

        # Generate clinical relevance explanation
        clinical_relevance = self._generate_clinical_relevance(
            paper_data,
            specialty
        )

        return ResearchAlert(
            user_id=user_id,
            paper_title=paper_data.get("title", ""),
            authors=paper_data.get("authors", []),
            journal=paper_data.get("journal", ""),
            publication_date=paper_data.get("publication_date", ""),
            pubmed_id=paper_data.get("pubmed_id"),
            doi=paper_data.get("doi"),
            url=paper_data.get("url"),
            abstract=abstract,
            key_findings=key_findings,
            clinical_relevance=clinical_relevance,
            specialty=specialty,
            relevance_score=relevance_score,
            keywords=paper_data.get("keywords", []),
        )

    async def create_guideline_alert(
        self,
        user_id: str,
        specialty: str,
        guideline_data: dict[str, Any],
    ) -> GuidelineUpdate:
        """
        Create guideline update alert.

        Args:
            user_id: User ID to notify
            specialty: User's specialty
            guideline_data: Guideline metadata

        Returns:
            GuidelineUpdate object
        """
        # Determine severity based on change type
        severity = self._determine_guideline_severity(guideline_data)

        return GuidelineUpdate(
            user_id=user_id,
            guideline_name=guideline_data.get("name", ""),
            organization=guideline_data.get("organization", ""),
            version=guideline_data.get("version", ""),
            url=guideline_data.get("url"),
            summary=guideline_data.get("summary", ""),
            key_changes=guideline_data.get("key_changes", []),
            impact=guideline_data.get("impact", ""),
            severity=severity,
            specialty=specialty,
            conditions=guideline_data.get("conditions", []),
            effective_date=guideline_data.get("effective_date"),
        )

    async def create_drug_alert(
        self,
        user_id: str,
        drug_data: dict[str, Any],
        affected_patients: int = 0,
    ) -> DrugAlert:
        """
        Create drug recall or safety alert.

        Args:
            user_id: User ID to notify
            drug_data: Drug alert data
            affected_patients: Number of user's patients on this drug

        Returns:
            DrugAlert object
        """
        # Determine severity
        severity = self._determine_drug_alert_severity(
            drug_data.get("alert_type", ""),
            affected_patients,
        )

        return DrugAlert(
            user_id=user_id,
            drug_name=drug_data.get("drug_name", ""),
            brand_names=drug_data.get("brand_names", []),
            alert_type=drug_data.get("alert_type", "safety_update"),
            title=drug_data.get("title", ""),
            description=drug_data.get("description", ""),
            action_required=drug_data.get("action_required", ""),
            severity=severity,
            source=drug_data.get("source", ""),
            source_url=drug_data.get("source_url"),
            alert_date=drug_data.get("alert_date", datetime.utcnow()),
            specialty=drug_data.get("specialty"),
            affected_patients=affected_patients,
        )

    async def fetch_new_research(
        self,
        specialty: str,
        keywords: list[str],
        days_back: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Fetch new research papers from PubMed.

        Args:
            specialty: Medical specialty
            keywords: Search keywords
            days_back: How many days back to search

        Returns:
            List of paper metadata dicts
        """
        # Build PubMed query
        query_parts = []

        # Add specialty-specific terms
        specialty_terms = self._get_specialty_search_terms(specialty)
        if specialty_terms:
            query_parts.append(f"({' OR '.join(specialty_terms)})")

        # Add keywords
        if keywords:
            keyword_query = ' OR '.join([f'"{kw}"' for kw in keywords])
            query_parts.append(f"({keyword_query})")

        # Add date filter
        start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        query_parts.append(f"({start_date}[PDAT]:3000[PDAT])")

        # Combine query
        query = " AND ".join(query_parts)

        # In real implementation, call PubMed API
        # For now, return mock data
        return self._mock_pubmed_results(specialty, keywords)

    async def fetch_guideline_updates(
        self,
        specialty: str,
        organizations: list[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch guideline updates from various sources.

        Args:
            specialty: Medical specialty
            organizations: Filter by specific organizations

        Returns:
            List of guideline update dicts
        """
        if organizations is None:
            organizations = [
                "ICMR",
                "WHO",
                "AHA",
                "ACC",
                "ADA",
                "ESC",
                "NICE",
                "ACOG",
            ]

        # In real implementation, scrape/fetch from guideline websites
        # For now, return mock data
        return self._mock_guideline_updates(specialty, organizations)

    async def fetch_drug_alerts(
        self,
        sources: list[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch drug alerts from FDA, CDSCO, etc.

        Args:
            sources: List of sources to check

        Returns:
            List of drug alert dicts
        """
        if sources is None:
            sources = ["FDA", "CDSCO", "EMA"]

        # In real implementation, fetch from drug alert APIs
        # For now, return mock data
        return self._mock_drug_alerts(sources)

    def filter_alerts_by_relevance(
        self,
        alerts: list[dict[str, Any]],
        user_profile: dict[str, Any],
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Filter alerts by relevance to user.

        Args:
            alerts: List of alert dicts
            user_profile: User's medical profile
            threshold: Minimum relevance score

        Returns:
            Filtered list of alerts
        """
        filtered = []

        for alert in alerts:
            score = self._calculate_relevance_score(alert, user_profile)
            if score >= threshold:
                alert["relevance_score"] = score
                filtered.append(alert)

        # Sort by relevance and severity
        filtered.sort(
            key=lambda x: (
                self._severity_to_priority(x.get("severity", "medium")),
                -x.get("relevance_score", 0),
            )
        )

        return filtered

    def _extract_key_findings(self, abstract: str) -> list[str]:
        """Extract key findings from abstract."""
        # Simple extraction - in real implementation, use NLP
        sentences = abstract.split(". ")

        # Look for conclusion/result sentences
        key_words = [
            "conclude", "found", "showed", "demonstrated",
            "results", "significant", "associated"
        ]

        findings = []
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in key_words):
                findings.append(sentence.strip())

        return findings[:3]  # Top 3 findings

    def _generate_clinical_relevance(
        self,
        paper_data: dict[str, Any],
        specialty: str,
    ) -> str:
        """Generate clinical relevance explanation."""
        # Simplified - in real implementation, use LLM
        title = paper_data.get("title", "")

        if "trial" in title.lower() or "rct" in title.lower():
            return f"This RCT may influence {specialty} practice guidelines."
        elif "meta-analysis" in title.lower():
            return f"This meta-analysis provides high-level evidence for {specialty}."
        elif "case" in title.lower():
            return f"Interesting case relevant to {specialty} practice."
        else:
            return f"New research in {specialty} worth reviewing."

    def _determine_guideline_severity(
        self,
        guideline_data: dict[str, Any],
    ) -> AlertSeverity:
        """Determine severity of guideline update."""
        changes = guideline_data.get("key_changes", [])
        impact = guideline_data.get("impact", "").lower()

        # Check for major changes
        major_keywords = [
            "contraindicated",
            "black box",
            "withdraw",
            "major",
            "significant change",
        ]

        if any(kw in impact for kw in major_keywords):
            return AlertSeverity.HIGH

        if len(changes) > 5:
            return AlertSeverity.MEDIUM

        return AlertSeverity.LOW

    def _determine_drug_alert_severity(
        self,
        alert_type: str,
        affected_patients: int,
    ) -> AlertSeverity:
        """Determine severity of drug alert."""
        if alert_type == "recall":
            if affected_patients > 0:
                return AlertSeverity.CRITICAL
            return AlertSeverity.HIGH

        if alert_type == "black_box_warning":
            return AlertSeverity.HIGH

        if alert_type == "safety_update":
            if affected_patients > 5:
                return AlertSeverity.HIGH
            elif affected_patients > 0:
                return AlertSeverity.MEDIUM
            return AlertSeverity.LOW

        if alert_type == "shortage":
            return AlertSeverity.MEDIUM

        return AlertSeverity.LOW

    def _get_specialty_search_terms(self, specialty: str) -> list[str]:
        """Get PubMed search terms for specialty."""
        specialty_map = {
            "cardiology": ["cardiology", "cardiac", "heart", "cardiovascular"],
            "neurology": ["neurology", "neurological", "brain", "stroke"],
            "pediatrics": ["pediatric", "children", "infant", "neonatal"],
            "diabetes": ["diabetes", "diabetic", "insulin", "glycemic"],
            "oncology": ["cancer", "oncology", "tumor", "neoplasm"],
            # Add more specialties
        }

        return specialty_map.get(specialty.lower(), [specialty])

    def _calculate_relevance_score(
        self,
        alert: dict[str, Any],
        user_profile: dict[str, Any],
    ) -> float:
        """Calculate relevance score for alert."""
        score = 0.0

        # Specialty match
        alert_specialty = alert.get("specialty", "").lower()
        user_specialty = user_profile.get("specialty", "").lower()

        if alert_specialty == user_specialty:
            score += 0.5
        elif alert_specialty in user_profile.get("subspecialties", []):
            score += 0.3

        # Keyword match
        alert_keywords = set(alert.get("keywords", []))
        user_interests = set(user_profile.get("common_conditions", []))

        if alert_keywords & user_interests:
            score += 0.3

        # Affected patients boost
        if alert.get("affected_patients", 0) > 0:
            score += 0.2

        return min(score, 1.0)

    def _severity_to_priority(self, severity: str) -> int:
        """Convert severity to priority (lower = higher priority)."""
        priority_map = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }
        return priority_map.get(severity, 2)

    def _mock_pubmed_results(
        self,
        specialty: str,
        keywords: list[str],
    ) -> list[dict[str, Any]]:
        """Mock PubMed results for testing."""
        return [
            {
                "title": f"Novel approach to {specialty} treatment",
                "authors": ["Smith J", "Doe A"],
                "journal": "New England Journal of Medicine",
                "publication_date": "2026-01-01",
                "pubmed_id": "12345678",
                "doi": "10.1056/nejm.2026.12345",
                "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "abstract": "This randomized controlled trial demonstrates significant improvement...",
                "keywords": keywords[:3] if keywords else [],
            }
        ]

    def _mock_guideline_updates(
        self,
        specialty: str,
        organizations: list[str],
    ) -> list[dict[str, Any]]:
        """Mock guideline updates for testing."""
        return [
            {
                "name": f"{specialty.title()} Management Guidelines",
                "organization": organizations[0] if organizations else "WHO",
                "version": "2026",
                "url": "https://example.com/guidelines",
                "summary": "Updated recommendations for management",
                "key_changes": [
                    "New first-line treatment recommendation",
                    "Revised diagnostic criteria",
                ],
                "impact": "Moderate changes to current practice",
                "conditions": [specialty],
                "effective_date": datetime.utcnow(),
            }
        ]

    def _mock_drug_alerts(self, sources: list[str]) -> list[dict[str, Any]]:
        """Mock drug alerts for testing."""
        return [
            {
                "drug_name": "Example Drug",
                "brand_names": ["BrandX", "BrandY"],
                "alert_type": "safety_update",
                "title": "New safety information for Example Drug",
                "description": "FDA has updated safety information...",
                "action_required": "Review patients on this medication",
                "source": sources[0] if sources else "FDA",
                "source_url": "https://fda.gov/alert",
                "alert_date": datetime.utcnow(),
            }
        ]
