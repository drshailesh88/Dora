"""Learning engine for profile updates."""

from datetime import datetime, timedelta
from typing import Optional

from src.personalization.detector import SpecialtyDetector
from src.personalization.models import (
    DoctorProfile,
    PersonalizationConfig,
    QueryHistory,
    QueryPattern,
    SpecialtyConfidence,
)


class ProfileLearner:
    """Learns and updates doctor profile from usage patterns."""

    def __init__(self, config: Optional[PersonalizationConfig] = None):
        """
        Initialize learner.

        Args:
            config: Personalization configuration.
        """
        self.config = config or PersonalizationConfig()
        self.detector = SpecialtyDetector()

    def update_profile_from_query(
        self,
        profile: DoctorProfile,
        query_record: QueryHistory,
    ) -> DoctorProfile:
        """
        Update profile based on a new query.

        Args:
            profile: Current profile.
            query_record: New query record.

        Returns:
            Updated profile.
        """
        # Update query count
        profile.total_queries += 1
        profile.last_query_at = query_record.timestamp
        profile.updated_at = datetime.utcnow()

        # Update specialty detection
        if query_record.detected_specialty and query_record.specialty_confidence > 0.5:
            self._update_specialty_confidence(
                profile,
                query_record.detected_specialty,
                query_record.specialty_confidence,
            )

        # Update drug preferences
        if query_record.mentioned_drugs:
            for drug in query_record.mentioned_drugs:
                # Extract drug class (simplified)
                drug_lower = drug.lower()
                # In production, use drug database
                # For now, just track the drug
                if drug not in profile.preferred_drug_classes:
                    profile.preferred_drug_classes.append(drug)

        # Update common conditions
        if query_record.mentioned_conditions:
            for condition in query_record.mentioned_conditions:
                if condition not in profile.common_conditions:
                    profile.common_conditions.append(condition)
                # Keep only top 50 conditions
                if len(profile.common_conditions) > 50:
                    profile.common_conditions = profile.common_conditions[-50:]

        return profile

    def _update_specialty_confidence(
        self,
        profile: DoctorProfile,
        specialty: str,
        confidence: float,
    ) -> None:
        """
        Update specialty confidence scores.

        Args:
            profile: Profile to update.
            specialty: Detected specialty.
            confidence: Confidence score.
        """
        # Find existing specialty confidence
        found = False
        for spec_conf in profile.detected_specialties:
            if spec_conf.specialty.value == specialty:
                # Update with exponential moving average
                old_confidence = spec_conf.confidence
                new_confidence = (
                    old_confidence * (1 - self.config.learning_rate)
                    + confidence * self.config.learning_rate
                )
                spec_conf.confidence = new_confidence
                spec_conf.evidence_count += 1
                spec_conf.last_updated = datetime.utcnow()
                found = True
                break

        if not found:
            # Add new specialty
            try:
                from src.personalization.models import MedicalSpecialty
                specialty_enum = MedicalSpecialty(specialty)
                profile.detected_specialties.append(
                    SpecialtyConfidence(
                        specialty=specialty_enum,
                        confidence=confidence,
                        evidence_count=1,
                    )
                )
            except ValueError:
                # Invalid specialty
                pass

        # Sort by confidence
        profile.detected_specialties.sort(key=lambda x: x.confidence, reverse=True)

    def learn_from_history(
        self,
        profile: DoctorProfile,
        history: list[QueryHistory],
    ) -> DoctorProfile:
        """
        Batch update profile from query history.

        Args:
            profile: Current profile.
            history: List of query records.

        Returns:
            Updated profile.
        """
        if not history:
            return profile

        # Detect specialties from history
        detected = self.detector.detect_from_history(
            history,
            min_confidence=self.config.specialty_filter_threshold,
        )

        # Update profile specialties
        profile.detected_specialties = detected

        # Aggregate common patterns
        all_drugs = []
        all_conditions = []

        for record in history:
            all_drugs.extend(record.mentioned_drugs)
            all_conditions.extend(record.mentioned_conditions)

        # Update common drugs (top 20)
        from collections import Counter
        drug_counts = Counter(all_drugs)
        profile.preferred_drug_classes = [
            drug for drug, _ in drug_counts.most_common(20)
        ]

        # Update common conditions (top 50)
        condition_counts = Counter(all_conditions)
        profile.common_conditions = [
            cond for cond, _ in condition_counts.most_common(50)
        ]

        profile.total_queries = len(history)
        profile.updated_at = datetime.utcnow()

        if history:
            profile.last_query_at = max(h.timestamp for h in history)

        return profile

    def apply_decay(
        self,
        profile: DoctorProfile,
        days_since_last_query: int,
    ) -> DoctorProfile:
        """
        Apply time-based decay to specialty confidences.

        Args:
            profile: Profile to update.
            days_since_last_query: Days since last activity.

        Returns:
            Updated profile.
        """
        if days_since_last_query == 0:
            return profile

        # Decay factor per day
        decay_per_day = self.config.decay_factor ** days_since_last_query

        for spec_conf in profile.detected_specialties:
            spec_conf.confidence *= decay_per_day

        # Remove very low confidence specialties
        profile.detected_specialties = [
            s for s in profile.detected_specialties
            if s.confidence > 0.1
        ]

        return profile

    def update_from_feedback(
        self,
        profile: DoctorProfile,
        query_record: QueryHistory,
        feedback_rating: int,
        clicked_results: Optional[list[str]] = None,
    ) -> DoctorProfile:
        """
        Update profile based on user feedback.

        Args:
            profile: Current profile.
            query_record: Query that was rated.
            feedback_rating: 1-5 rating.
            clicked_results: IDs of results user clicked.

        Returns:
            Updated profile.
        """
        # Update query record
        query_record.user_feedback = feedback_rating
        if clicked_results:
            query_record.clicked_results = clicked_results

        # Boost specialty confidence on positive feedback
        if feedback_rating >= 4 and query_record.detected_specialty:
            self._update_specialty_confidence(
                profile,
                query_record.detected_specialty,
                query_record.specialty_confidence * 1.2,  # Boost
            )

        # Reduce confidence on negative feedback
        elif feedback_rating <= 2 and query_record.detected_specialty:
            self._update_specialty_confidence(
                profile,
                query_record.detected_specialty,
                query_record.specialty_confidence * 0.8,  # Penalize
            )

        return profile

    def compute_query_patterns(
        self,
        history: list[QueryHistory],
    ) -> QueryPattern:
        """
        Compute aggregated query patterns.

        Args:
            history: Query history.

        Returns:
            Query pattern statistics.
        """
        from collections import Counter

        if not history:
            return QueryPattern(user_id="unknown")

        user_id = history[0].user_id if history else "unknown"

        pattern = QueryPattern(user_id=user_id)
        pattern.total_queries = len(history)

        # Category distribution
        categories = [h.category.value for h in history if h.category]
        pattern.category_distribution = dict(Counter(categories))

        # Time patterns
        hours = [h.timestamp.hour for h in history]
        pattern.hour_distribution = dict(Counter(hours))

        weekdays = [h.timestamp.weekday() for h in history]
        pattern.weekday_distribution = dict(Counter(weekdays))

        # Query complexity
        query_lengths = [len(h.query.split()) for h in history]
        pattern.avg_query_length = sum(query_lengths) / len(query_lengths) if query_lengths else 0

        pattern.uses_patient_context = sum(1 for h in history if h.had_patient_context)

        # Entity patterns
        all_drugs = []
        all_conditions = []

        for h in history:
            all_drugs.extend(h.mentioned_drugs)
            all_conditions.extend(h.mentioned_conditions)

        pattern.common_drugs = dict(Counter(all_drugs).most_common(20))
        pattern.common_conditions = dict(Counter(all_conditions).most_common(30))

        # Feedback patterns
        pattern.positive_feedback_count = sum(
            1 for h in history if h.user_feedback and h.user_feedback >= 4
        )
        pattern.negative_feedback_count = sum(
            1 for h in history if h.user_feedback and h.user_feedback <= 2
        )

        pattern.updated_at = datetime.utcnow()

        return pattern

    def get_learning_insights(
        self,
        profile: DoctorProfile,
        patterns: QueryPattern,
    ) -> dict:
        """
        Generate insights about learning progress.

        Args:
            profile: Doctor profile.
            patterns: Query patterns.

        Returns:
            Dictionary of insights.
        """
        insights = {
            "total_queries": profile.total_queries,
            "specialties_detected": len(profile.detected_specialties),
            "top_specialty": None,
            "confidence": 0.0,
            "common_query_times": [],
            "preferred_categories": [],
            "feedback_score": 0.0,
        }

        # Top specialty
        if profile.detected_specialties:
            top = profile.detected_specialties[0]
            insights["top_specialty"] = top.specialty.value
            insights["confidence"] = round(top.confidence, 2)

        # Peak query times
        insights["common_query_times"] = patterns.get_peak_hours(top_n=3)

        # Preferred categories
        insights["preferred_categories"] = patterns.get_top_categories(top_n=5)

        # Feedback score
        total_feedback = patterns.positive_feedback_count + patterns.negative_feedback_count
        if total_feedback > 0:
            insights["feedback_score"] = round(
                patterns.positive_feedback_count / total_feedback, 2
            )

        return insights
