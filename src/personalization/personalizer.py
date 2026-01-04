"""Query personalization based on doctor profile."""

from typing import Optional

from src.core.models import RetrievalResult
from src.personalization.models import (
    DoctorProfile,
    MedicalSpecialty,
    PersonalizationConfig,
)


class QueryPersonalizer:
    """Personalizes query results based on doctor profile."""

    def __init__(self, config: Optional[PersonalizationConfig] = None):
        """
        Initialize personalizer.

        Args:
            config: Personalization configuration.
        """
        self.config = config or PersonalizationConfig()

    def personalize_results(
        self,
        results: list[RetrievalResult],
        profile: DoctorProfile,
        query: str,
    ) -> list[RetrievalResult]:
        """
        Personalize retrieval results based on doctor profile.

        Args:
            results: Retrieved results to personalize.
            profile: Doctor's profile.
            query: Original query.

        Returns:
            Reranked and filtered results.
        """
        if not results:
            return results

        # Get doctor's specialties
        specialties = profile.get_all_specialties()
        if not specialties:
            # Try detected specialties
            if profile.detected_specialties:
                top_detected = profile.detected_specialties[0]
                if top_detected.confidence > 0.5:
                    specialties = [top_detected.specialty]

        if not specialties:
            # No personalization possible
            return results

        # Adjust scores based on specialty relevance
        personalized = []
        for result in results:
            adjusted_score = self._adjust_score(result, specialties, profile)

            # Create new result with adjusted score
            personalized.append(
                RetrievalResult(
                    chunk=result.chunk,
                    score=adjusted_score,
                    retriever=result.retriever,
                )
            )

        # Filter out very low relevance results
        filtered = [
            r for r in personalized
            if r.score > self.config.specialty_filter_threshold
        ]

        # Re-sort by adjusted score
        filtered.sort(key=lambda x: x.score, reverse=True)

        return filtered

    def _adjust_score(
        self,
        result: RetrievalResult,
        specialties: list[MedicalSpecialty],
        profile: DoctorProfile,
    ) -> float:
        """
        Adjust result score based on specialty and preferences.

        Args:
            result: Retrieval result.
            specialties: Doctor's specialties.
            profile: Doctor's profile.

        Returns:
            Adjusted score.
        """
        score = result.score
        metadata = result.chunk.metadata

        # Boost if from preferred resource
        if "source" in metadata:
            source = metadata["source"].lower()
            for fav_resource in profile.favorite_resources:
                if fav_resource.lower() in source:
                    score *= 1.2
                    break

        # Boost if specialty matches
        if "specialty" in metadata:
            doc_specialty = metadata["specialty"]
            if isinstance(doc_specialty, str):
                try:
                    doc_specialty_enum = MedicalSpecialty(doc_specialty.lower().replace(" ", "_"))
                    if doc_specialty_enum in specialties:
                        score *= self.config.specialty_boost_factor
                except ValueError:
                    pass

        # Boost if document type matches experience level
        if "doc_type" in metadata:
            doc_type = metadata["doc_type"]

            if profile.years_of_experience:
                if profile.years_of_experience < 5:
                    # Junior doctors prefer guidelines and textbooks
                    if doc_type in ["guideline", "textbook"]:
                        score *= 1.3
                elif profile.years_of_experience > 10:
                    # Senior doctors may prefer papers and case reports
                    if doc_type in ["paper", "case_report"]:
                        score *= 1.2

        # Boost if relevant to common conditions
        if profile.common_conditions and "conditions" in metadata:
            doc_conditions = metadata["conditions"]
            if isinstance(doc_conditions, list):
                for condition in profile.common_conditions:
                    if condition.lower() in [c.lower() for c in doc_conditions]:
                        score *= 1.15
                        break

        return score

    def add_specialty_context(
        self,
        query: str,
        profile: DoctorProfile,
    ) -> str:
        """
        Add specialty-specific context to query.

        Args:
            query: Original query.
            profile: Doctor's profile.

        Returns:
            Enhanced query with context.
        """
        top_specialty = profile.get_top_specialty()

        if not top_specialty:
            return query

        # Add specialty context
        specialty_contexts = {
            MedicalSpecialty.CARDIOLOGY: "In the context of cardiology and cardiovascular medicine",
            MedicalSpecialty.PEDIATRICS: "In pediatric patients",
            MedicalSpecialty.GERIATRIC: "In geriatric patients",
            MedicalSpecialty.EMERGENCY_MEDICINE: "In emergency medicine and acute care settings",
            MedicalSpecialty.CRITICAL_CARE: "In intensive care and critical care settings",
        }

        context = specialty_contexts.get(top_specialty, f"In the context of {top_specialty.value}")

        return f"{context}: {query}"

    def filter_metadata(
        self,
        profile: DoctorProfile,
    ) -> dict:
        """
        Create metadata filters based on profile.

        Args:
            profile: Doctor's profile.

        Returns:
            Metadata filter dictionary.
        """
        filters = {}

        # Filter by specialty
        specialties = profile.get_all_specialties()
        if specialties:
            filters["specialty"] = [s.value for s in specialties]

        # Filter by practice setting
        if profile.practice_settings:
            filters["practice_setting"] = [s.value for s in profile.practice_settings]

        # Add pediatric filter
        if profile.show_pediatric_dosing:
            filters["includes_pediatric"] = True
        elif MedicalSpecialty.PEDIATRICS not in specialties:
            # Exclude pediatric content for non-pediatricians
            filters["excludes_pediatric"] = True

        return filters

    def adjust_response_detail(
        self,
        response: str,
        profile: DoctorProfile,
    ) -> str:
        """
        Adjust response detail level based on preferences.

        Args:
            response: Generated response.
            profile: Doctor's profile.

        Returns:
            Adjusted response.
        """
        # This is a placeholder - in production, this would use LLM
        # to rewrite the response at the desired detail level

        detail_level = profile.preferred_detail_level

        if detail_level == "brief":
            # Could truncate or summarize
            # For now, just add a note
            return response + "\n\n(Brief mode - use 'detailed' mode for more information)"
        elif detail_level == "detailed":
            # Could expand
            return response
        else:
            return response

    def get_preferred_drug_alternatives(
        self,
        drug: str,
        profile: DoctorProfile,
    ) -> list[str]:
        """
        Get alternative drugs based on doctor's preferences.

        Args:
            drug: Drug name.
            profile: Doctor's profile.

        Returns:
            List of preferred alternatives.
        """
        # This would query a drug database filtered by preferred classes
        # Placeholder implementation

        alternatives = []

        if profile.preferred_drug_classes:
            # In production, query drug database
            # For now, return empty list
            pass

        return alternatives

    def should_show_drug_interactions(self, profile: DoctorProfile) -> bool:
        """Check if drug interactions should be shown."""
        return profile.show_drug_interactions

    def should_show_pediatric_dosing(self, profile: DoctorProfile) -> bool:
        """Check if pediatric dosing should be shown."""
        return (
            profile.show_pediatric_dosing
            or MedicalSpecialty.PEDIATRICS in profile.get_all_specialties()
        )
