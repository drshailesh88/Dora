"""
Evidence level grading system for medical recommendations.

This module provides functionality for assessing and displaying evidence quality,
grading recommendations, and evaluating source credibility.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from .models import (
    EvidenceLevel,
    RecommendationStrength,
    EvidenceBadge,
    Citation,
    SourceType,
)


class EvidenceGrader:
    """Grade evidence quality for medical recommendations."""

    # Evidence level criteria
    LEVEL_CRITERIA = {
        EvidenceLevel.A: {
            "min_rcts": 2,
            "min_sources": 3,
            "min_confidence": 0.85,
            "allowed_types": [SourceType.META_ANALYSIS, SourceType.SYSTEMATIC_REVIEW, SourceType.RCT],
        },
        EvidenceLevel.B: {
            "min_rcts": 1,
            "min_sources": 2,
            "min_confidence": 0.70,
            "allowed_types": [SourceType.RCT, SourceType.OBSERVATIONAL, SourceType.SYSTEMATIC_REVIEW],
        },
        EvidenceLevel.C: {
            "min_rcts": 0,
            "min_sources": 1,
            "min_confidence": 0.50,
            "allowed_types": [SourceType.OBSERVATIONAL, SourceType.GUIDELINE, SourceType.TEXTBOOK],
        },
        EvidenceLevel.D: {
            "min_rcts": 0,
            "min_sources": 1,
            "min_confidence": 0.30,
            "allowed_types": [SourceType.EXPERT_OPINION, SourceType.TEXTBOOK],
        },
    }

    # Source type scores
    SOURCE_SCORES = {
        SourceType.META_ANALYSIS: 10,
        SourceType.SYSTEMATIC_REVIEW: 9,
        SourceType.RCT: 8,
        SourceType.GUIDELINE: 7,
        SourceType.OBSERVATIONAL: 6,
        SourceType.TEXTBOOK: 5,
        SourceType.DRUG_DATABASE: 5,
        SourceType.EXPERT_OPINION: 3,
    }

    @classmethod
    def grade_evidence(
        cls,
        citations: List[Citation],
        confidence_score: float = 0.0,
        publication_years: Optional[List[int]] = None,
    ) -> EvidenceBadge:
        """
        Grade evidence quality based on citations and metadata.

        Args:
            citations: List of supporting citations
            confidence_score: AI model confidence score (0-1)
            publication_years: Publication years for recency scoring

        Returns:
            EvidenceBadge with evidence level and details
        """
        if not citations:
            return EvidenceBadge(
                level=EvidenceLevel.E,
                strength=RecommendationStrength.INSUFFICIENT,
                source_count=0,
                confidence_score=0.0,
            )

        # Count source types
        source_types = [c.source_type for c in citations]
        rct_count = sum(
            1
            for t in source_types
            if t in [SourceType.RCT, SourceType.META_ANALYSIS, SourceType.SYSTEMATIC_REVIEW]
        )

        # Calculate evidence level
        level = cls._calculate_evidence_level(citations, confidence_score, rct_count)

        # Calculate recommendation strength
        strength = cls._calculate_recommendation_strength(level, confidence_score, len(citations))

        # Get most recent update
        last_updated = cls._get_last_updated(citations)

        return EvidenceBadge(
            level=level,
            strength=strength,
            source_count=len(citations),
            confidence_score=confidence_score,
            last_updated=last_updated,
        )

    @classmethod
    def _calculate_evidence_level(
        cls, citations: List[Citation], confidence: float, rct_count: int
    ) -> EvidenceLevel:
        """Calculate evidence level from citations."""
        source_count = len(citations)
        source_types = [c.source_type for c in citations]

        # Check Level A
        criteria_a = cls.LEVEL_CRITERIA[EvidenceLevel.A]
        if (
            rct_count >= criteria_a["min_rcts"]
            and source_count >= criteria_a["min_sources"]
            and confidence >= criteria_a["min_confidence"]
            and any(t in criteria_a["allowed_types"] for t in source_types)
        ):
            return EvidenceLevel.A

        # Check Level B
        criteria_b = cls.LEVEL_CRITERIA[EvidenceLevel.B]
        if (
            rct_count >= criteria_b["min_rcts"]
            and source_count >= criteria_b["min_sources"]
            and confidence >= criteria_b["min_confidence"]
            and any(t in criteria_b["allowed_types"] for t in source_types)
        ):
            return EvidenceLevel.B

        # Check Level C
        criteria_c = cls.LEVEL_CRITERIA[EvidenceLevel.C]
        if (
            source_count >= criteria_c["min_sources"]
            and confidence >= criteria_c["min_confidence"]
            and any(t in criteria_c["allowed_types"] for t in source_types)
        ):
            return EvidenceLevel.C

        # Check Level D
        criteria_d = cls.LEVEL_CRITERIA[EvidenceLevel.D]
        if source_count >= criteria_d["min_sources"] and confidence >= criteria_d["min_confidence"]:
            return EvidenceLevel.D

        return EvidenceLevel.E

    @classmethod
    def _calculate_recommendation_strength(
        cls, level: EvidenceLevel, confidence: float, source_count: int
    ) -> RecommendationStrength:
        """Calculate recommendation strength."""
        if level == EvidenceLevel.A and confidence >= 0.85:
            return RecommendationStrength.STRONG
        elif level in [EvidenceLevel.A, EvidenceLevel.B] and confidence >= 0.70:
            return RecommendationStrength.STRONG
        elif level in [EvidenceLevel.B, EvidenceLevel.C] and confidence >= 0.50:
            return RecommendationStrength.WEAK
        elif level == EvidenceLevel.C:
            return RecommendationStrength.CONDITIONAL
        else:
            return RecommendationStrength.INSUFFICIENT

    @classmethod
    def _get_last_updated(cls, citations: List[Citation]) -> Optional[datetime]:
        """Get most recent publication date from citations."""
        years = [c.year for c in citations if c.year]
        if years:
            most_recent_year = max(years)
            return datetime(most_recent_year, 1, 1)
        return None

    @classmethod
    def calculate_source_credibility(cls, citation: Citation) -> float:
        """
        Calculate credibility score for a source (0-1).

        Factors:
        - Source type (meta-analysis > RCT > observational > opinion)
        - Publication recency (newer = better)
        - Has DOI/PMID (more credible)
        - Journal impact (if available)
        """
        score = 0.0

        # Source type score (0-0.5)
        type_score = cls.SOURCE_SCORES.get(citation.source_type, 0)
        score += (type_score / 10) * 0.5

        # Recency score (0-0.25)
        if citation.year:
            current_year = datetime.now().year
            age = current_year - citation.year
            if age <= 2:
                score += 0.25
            elif age <= 5:
                score += 0.20
            elif age <= 10:
                score += 0.10
            else:
                score += 0.05

        # Has identifier (0-0.15)
        if citation.doi or citation.pmid:
            score += 0.15

        # Has full metadata (0-0.10)
        if citation.authors and citation.journal:
            score += 0.10

        return min(score, 1.0)

    @classmethod
    def is_evidence_outdated(
        cls, badge: EvidenceBadge, threshold_years: int = 5
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if evidence is outdated.

        Args:
            badge: Evidence badge to check
            threshold_years: Years before considered outdated

        Returns:
            Tuple of (is_outdated, warning_message)
        """
        if not badge.last_updated:
            return False, None

        age = datetime.now() - badge.last_updated
        years_old = age.days / 365

        if years_old > threshold_years:
            return True, f"Evidence is {int(years_old)} years old. Consider reviewing recent guidelines."

        return False, None

    @classmethod
    def compare_evidence(cls, badge1: EvidenceBadge, badge2: EvidenceBadge) -> int:
        """
        Compare two evidence badges.

        Returns:
            -1 if badge1 < badge2, 0 if equal, 1 if badge1 > badge2
        """
        # Level order: A > B > C > D > E
        level_order = {
            EvidenceLevel.A: 5,
            EvidenceLevel.B: 4,
            EvidenceLevel.C: 3,
            EvidenceLevel.D: 2,
            EvidenceLevel.E: 1,
            EvidenceLevel.UNKNOWN: 0,
        }

        score1 = level_order.get(badge1.level, 0)
        score2 = level_order.get(badge2.level, 0)

        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            # Same level, compare confidence
            if badge1.confidence_score > badge2.confidence_score:
                return 1
            elif badge1.confidence_score < badge2.confidence_score:
                return -1
            else:
                return 0

    @classmethod
    def get_evidence_summary(cls, badge: EvidenceBadge) -> str:
        """
        Get human-readable evidence summary.

        Returns:
            Summary text like "Strong recommendation (Level A, 5 sources, 89% confidence)"
        """
        parts = []

        if badge.strength:
            parts.append(f"{badge.strength.value} recommendation")

        parts.append(f"Level {badge.level.value}")

        if badge.source_count > 0:
            parts.append(f"{badge.source_count} source{'s' if badge.source_count > 1 else ''}")

        if badge.confidence_score > 0:
            confidence_pct = int(badge.confidence_score * 100)
            parts.append(f"{confidence_pct}% confidence")

        return ", ".join(parts)

    @classmethod
    def filter_citations_by_quality(
        cls, citations: List[Citation], min_credibility: float = 0.5
    ) -> List[Citation]:
        """
        Filter citations by minimum credibility score.

        Args:
            citations: List of citations to filter
            min_credibility: Minimum credibility score (0-1)

        Returns:
            Filtered list of high-quality citations
        """
        filtered = []
        for citation in citations:
            score = cls.calculate_source_credibility(citation)
            if score >= min_credibility:
                citation.evidence_level = cls._citation_to_evidence_level(citation)
                filtered.append(citation)

        return filtered

    @classmethod
    def _citation_to_evidence_level(cls, citation: Citation) -> EvidenceLevel:
        """Map individual citation to evidence level."""
        if citation.source_type in [SourceType.META_ANALYSIS, SourceType.SYSTEMATIC_REVIEW]:
            return EvidenceLevel.A
        elif citation.source_type == SourceType.RCT:
            return EvidenceLevel.B
        elif citation.source_type in [SourceType.GUIDELINE, SourceType.OBSERVATIONAL]:
            return EvidenceLevel.C
        elif citation.source_type == SourceType.EXPERT_OPINION:
            return EvidenceLevel.D
        else:
            return EvidenceLevel.C  # Textbooks, drug databases


def create_evidence_badge(
    citations: List[Citation],
    confidence: float = 0.0,
) -> EvidenceBadge:
    """
    Convenience function to create evidence badge.

    Args:
        citations: Supporting citations
        confidence: Model confidence score

    Returns:
        Graded evidence badge
    """
    return EvidenceGrader.grade_evidence(citations, confidence)


def get_evidence_icon(level: EvidenceLevel) -> str:
    """Get icon for evidence level."""
    icons = {
        EvidenceLevel.A: "🟢",
        EvidenceLevel.B: "🔵",
        EvidenceLevel.C: "🟡",
        EvidenceLevel.D: "🔴",
        EvidenceLevel.E: "⚫",
        EvidenceLevel.UNKNOWN: "⚪",
    }
    return icons.get(level, "⚪")


def format_evidence_badge_text(badge: EvidenceBadge) -> str:
    """Format evidence badge for text display."""
    icon = get_evidence_icon(badge.level)
    summary = EvidenceGrader.get_evidence_summary(badge)
    return f"{icon} {summary}"
