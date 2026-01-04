"""Recommendation Feedback System for learning from clinical outcomes."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    """Type of feedback."""

    FOLLOWED = "followed"  # Doctor followed recommendation
    MODIFIED = "modified"  # Doctor modified recommendation
    REJECTED = "rejected"  # Doctor rejected recommendation
    ALTERNATIVE = "alternative"  # Doctor chose different approach


class OutcomeType(str, Enum):
    """Clinical outcome after recommendation."""

    IMPROVED = "improved"  # Patient improved
    UNCHANGED = "unchanged"  # No change
    WORSENED = "worsened"  # Patient worsened
    ADVERSE_EVENT = "adverse_event"  # Adverse drug event occurred
    UNKNOWN = "unknown"  # Outcome not yet known


class RecommendationFeedback(BaseModel):
    """Feedback on a clinical recommendation."""

    id: Optional[int] = None
    patient_id: int
    query: str = Field(..., description="Original clinical query")
    recommendation: str = Field(..., description="System recommendation")
    recommendation_type: str = Field(
        default="general", description="diagnosis, treatment, medication, referral"
    )
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Feedback
    feedback_type: FeedbackType
    action_taken: str = Field(..., description="What doctor actually did")
    rationale: Optional[str] = Field(None, description="Why doctor deviated")

    # Outcome tracking
    outcome: Optional[OutcomeType] = None
    outcome_notes: Optional[str] = None
    days_to_outcome: Optional[int] = Field(None, description="Days until outcome known")

    # Metadata
    doctor_id: Optional[str] = None
    specialty: Optional[str] = None
    feedback_date: datetime = Field(default_factory=datetime.utcnow)
    outcome_date: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": 12345,
                "query": "Best antibiotic for UTI in CKD patient?",
                "recommendation": "Nitrofurantoin 100mg BID x 5 days",
                "feedback_type": "followed",
                "action_taken": "Prescribed nitrofurantoin 100mg BID x 5 days",
                "outcome": "improved",
                "outcome_notes": "Symptoms resolved in 3 days",
            }
        }


class FeedbackAnalytics(BaseModel):
    """Analytics on recommendation feedback."""

    total_recommendations: int = 0
    followed_count: int = 0
    modified_count: int = 0
    rejected_count: int = 0
    alternative_count: int = 0

    # Outcomes
    improved_count: int = 0
    unchanged_count: int = 0
    worsened_count: int = 0
    adverse_event_count: int = 0

    # Metrics
    follow_rate: float = Field(0.0, description="% recommendations followed")
    success_rate: float = Field(
        0.0, description="% followed recommendations that improved patient"
    )
    adverse_event_rate: float = Field(
        0.0, description="% recommendations leading to adverse events"
    )

    @staticmethod
    def calculate(feedbacks: list[RecommendationFeedback]) -> "FeedbackAnalytics":
        """Calculate analytics from feedback list."""
        analytics = FeedbackAnalytics()
        analytics.total_recommendations = len(feedbacks)

        if not feedbacks:
            return analytics

        # Count feedback types
        for fb in feedbacks:
            if fb.feedback_type == FeedbackType.FOLLOWED:
                analytics.followed_count += 1
            elif fb.feedback_type == FeedbackType.MODIFIED:
                analytics.modified_count += 1
            elif fb.feedback_type == FeedbackType.REJECTED:
                analytics.rejected_count += 1
            elif fb.feedback_type == FeedbackType.ALTERNATIVE:
                analytics.alternative_count += 1

            # Count outcomes
            if fb.outcome == OutcomeType.IMPROVED:
                analytics.improved_count += 1
            elif fb.outcome == OutcomeType.UNCHANGED:
                analytics.unchanged_count += 1
            elif fb.outcome == OutcomeType.WORSENED:
                analytics.worsened_count += 1
            elif fb.outcome == OutcomeType.ADVERSE_EVENT:
                analytics.adverse_event_count += 1

        # Calculate rates
        analytics.follow_rate = (
            analytics.followed_count / analytics.total_recommendations * 100
        )

        # Success rate = % of followed recommendations that led to improvement
        if analytics.followed_count > 0:
            followed_and_improved = sum(
                1
                for fb in feedbacks
                if fb.feedback_type == FeedbackType.FOLLOWED
                and fb.outcome == OutcomeType.IMPROVED
            )
            analytics.success_rate = (
                followed_and_improved / analytics.followed_count * 100
            )

        # Adverse event rate
        if analytics.total_recommendations > 0:
            analytics.adverse_event_rate = (
                analytics.adverse_event_count / analytics.total_recommendations * 100
            )

        return analytics


class FeedbackStore:
    """
    Store and retrieve recommendation feedback.

    In production, this would use a database.
    For now, using in-memory storage.
    """

    def __init__(self):
        """Initialize feedback store."""
        self._feedbacks: list[RecommendationFeedback] = []
        self._next_id = 1

    def add_feedback(
        self, feedback: RecommendationFeedback
    ) -> RecommendationFeedback:
        """
        Add new feedback.

        Args:
            feedback: Feedback to add

        Returns:
            Feedback with assigned ID
        """
        feedback.id = self._next_id
        self._next_id += 1
        self._feedbacks.append(feedback)
        return feedback

    def update_outcome(
        self,
        feedback_id: int,
        outcome: OutcomeType,
        outcome_notes: Optional[str] = None,
    ) -> Optional[RecommendationFeedback]:
        """
        Update outcome for existing feedback.

        Args:
            feedback_id: Feedback ID
            outcome: Clinical outcome
            outcome_notes: Notes on outcome

        Returns:
            Updated feedback or None if not found
        """
        for fb in self._feedbacks:
            if fb.id == feedback_id:
                fb.outcome = outcome
                fb.outcome_notes = outcome_notes
                fb.outcome_date = datetime.utcnow()
                if fb.feedback_date and fb.outcome_date:
                    delta = fb.outcome_date - fb.feedback_date
                    fb.days_to_outcome = delta.days
                return fb
        return None

    def get_feedback_by_id(
        self, feedback_id: int
    ) -> Optional[RecommendationFeedback]:
        """Get feedback by ID."""
        for fb in self._feedbacks:
            if fb.id == feedback_id:
                return fb
        return None

    def get_patient_feedbacks(
        self, patient_id: int
    ) -> list[RecommendationFeedback]:
        """Get all feedback for a patient."""
        return [fb for fb in self._feedbacks if fb.patient_id == patient_id]

    def get_recent_feedbacks(self, limit: int = 100) -> list[RecommendationFeedback]:
        """Get recent feedbacks."""
        return sorted(
            self._feedbacks,
            key=lambda x: x.feedback_date,
            reverse=True,
        )[:limit]

    def get_analytics(
        self,
        specialty: Optional[str] = None,
        doctor_id: Optional[str] = None,
    ) -> FeedbackAnalytics:
        """
        Get analytics on recommendations.

        Args:
            specialty: Filter by specialty
            doctor_id: Filter by doctor

        Returns:
            Feedback analytics
        """
        feedbacks = self._feedbacks

        if specialty:
            feedbacks = [fb for fb in feedbacks if fb.specialty == specialty]
        if doctor_id:
            feedbacks = [fb for fb in feedbacks if fb.doctor_id == doctor_id]

        return FeedbackAnalytics.calculate(feedbacks)

    def get_similar_cases(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RecommendationFeedback]:
        """
        Find similar past cases for learning.

        Args:
            query: Current query
            limit: Max results

        Returns:
            Similar feedback cases
        """
        # Simple keyword matching
        # In production, use semantic similarity with embeddings
        query_lower = query.lower()
        keywords = set(query_lower.split())

        scored_feedbacks = []
        for fb in self._feedbacks:
            fb_keywords = set(fb.query.lower().split())
            similarity = len(keywords & fb_keywords) / len(keywords | fb_keywords)
            if similarity > 0.3:  # Threshold
                scored_feedbacks.append((similarity, fb))

        scored_feedbacks.sort(key=lambda x: x[0], reverse=True)
        return [fb for _, fb in scored_feedbacks[:limit]]


class ABTestManager:
    """
    A/B testing manager for recommendation formats.

    Tests different presentation formats to see which leads to
    better outcomes.
    """

    def __init__(self, feedback_store: FeedbackStore):
        """
        Initialize A/B test manager.

        Args:
            feedback_store: Feedback storage
        """
        self.feedback_store = feedback_store
        self.active_tests: dict[str, dict] = {}

    def create_test(
        self,
        test_name: str,
        variant_a: str,
        variant_b: str,
        description: str,
    ):
        """
        Create new A/B test.

        Args:
            test_name: Unique test identifier
            variant_a: Description of variant A
            variant_b: Description of variant B
            description: What is being tested
        """
        self.active_tests[test_name] = {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "description": description,
            "created_at": datetime.utcnow(),
        }

    def get_variant_for_user(self, test_name: str, user_id: str) -> str:
        """
        Get A/B test variant for user (consistent assignment).

        Args:
            test_name: Test name
            user_id: User ID

        Returns:
            "A" or "B"
        """
        # Simple hash-based assignment (consistent per user)
        hash_val = hash(f"{test_name}:{user_id}")
        return "A" if hash_val % 2 == 0 else "B"

    def get_test_results(self, test_name: str) -> dict:
        """
        Get results of A/B test.

        Args:
            test_name: Test name

        Returns:
            Test results with analytics for each variant
        """
        if test_name not in self.active_tests:
            return {}

        # Get all feedbacks and split by variant
        # Note: In production, we'd tag feedbacks with variant info
        # For now, just showing the structure
        return {
            "test_name": test_name,
            "test_info": self.active_tests[test_name],
            "variant_a_analytics": {},  # Would calculate from tagged feedbacks
            "variant_b_analytics": {},  # Would calculate from tagged feedbacks
            "recommendation": "Insufficient data",  # Statistical analysis
        }


# Global feedback store
feedback_store = FeedbackStore()
ab_test_manager = ABTestManager(feedback_store)
