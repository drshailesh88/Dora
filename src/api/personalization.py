"""API endpoints for personalization."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user
from src.personalization import (
    DoctorProfile,
    MedicalSpecialty,
    PersonalizationConfig,
    PersonalizedRecommender,
    PracticeSetting,
    ProfileLearner,
    QueryHistory,
    SpecialtyDetector,
    PersonalizationStorage,
)

router = APIRouter(prefix="/api/v1/personalization", tags=["personalization"])

# Initialize components
storage = PersonalizationStorage()
detector = SpecialtyDetector()
learner = ProfileLearner()
recommender = PersonalizedRecommender()


# Request/Response models
class ProfileUpdateRequest(BaseModel):
    """Request to update profile."""

    primary_specialty: Optional[MedicalSpecialty] = None
    subspecialties: Optional[list[MedicalSpecialty]] = None
    years_of_experience: Optional[int] = Field(None, ge=0, le=70)
    practice_settings: Optional[list[PracticeSetting]] = None
    preferred_detail_level: Optional[str] = Field(None, pattern="^(brief|medium|detailed)$")
    show_pediatric_dosing: Optional[bool] = None
    show_drug_interactions: Optional[bool] = None


class QueryFeedbackRequest(BaseModel):
    """Request to provide query feedback."""

    query_id: str
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    clicked_results: Optional[list[str]] = None


class SpecialtyDetectionResponse(BaseModel):
    """Response with detected specialty."""

    detected_specialties: list[dict]
    top_specialty: Optional[str] = None
    confidence: float = 0.0
    evidence_count: int = 0


class RecommendationsResponse(BaseModel):
    """Response with personalized recommendations."""

    guidelines: list[dict] = Field(default_factory=list)
    calculators: list[dict] = Field(default_factory=list)
    cme_topics: list[dict] = Field(default_factory=list)
    reading: list[dict] = Field(default_factory=list)


# Endpoints
@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)) -> DoctorProfile:
    """
    Get doctor profile.

    Returns:
        Doctor profile with specialty detection and preferences.
    """
    user_id = current_user["sub"]

    # Get or create profile
    profile = storage.get_profile(user_id)

    if not profile:
        # Create new profile
        profile = DoctorProfile(user_id=user_id)

        # Try to detect specialty from history
        history = storage.get_recent_query_history(user_id, days=90)
        if len(history) >= 10:  # Minimum queries for detection
            profile = learner.learn_from_history(profile, history)

        storage.save_profile(profile)

    return profile


@router.put("/profile")
async def update_profile(
    update_request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> DoctorProfile:
    """
    Update doctor profile.

    Args:
        update_request: Profile updates.

    Returns:
        Updated profile.
    """
    user_id = current_user["sub"]

    # Get existing profile
    profile = storage.get_profile(user_id)

    if not profile:
        profile = DoctorProfile(user_id=user_id)

    # Update fields
    if update_request.primary_specialty is not None:
        profile.primary_specialty = update_request.primary_specialty

    if update_request.subspecialties is not None:
        profile.subspecialties = update_request.subspecialties

    if update_request.years_of_experience is not None:
        profile.years_of_experience = update_request.years_of_experience

    if update_request.practice_settings is not None:
        profile.practice_settings = update_request.practice_settings

    if update_request.preferred_detail_level is not None:
        profile.preferred_detail_level = update_request.preferred_detail_level

    if update_request.show_pediatric_dosing is not None:
        profile.show_pediatric_dosing = update_request.show_pediatric_dosing

    if update_request.show_drug_interactions is not None:
        profile.show_drug_interactions = update_request.show_drug_interactions

    profile.updated_at = datetime.utcnow()

    # Save
    storage.save_profile(profile)

    return profile


@router.get("/profile/specialty")
async def get_detected_specialty(
    current_user: dict = Depends(get_current_user),
) -> SpecialtyDetectionResponse:
    """
    Get detected specialty from query history.

    Returns:
        Specialty detection results.
    """
    user_id = current_user["sub"]

    # Get profile
    profile = storage.get_profile(user_id)

    if not profile:
        return SpecialtyDetectionResponse(
            detected_specialties=[],
            top_specialty=None,
            confidence=0.0,
            evidence_count=0,
        )

    # Format response
    detected_specialties = [
        {
            "specialty": sc.specialty.value,
            "confidence": round(sc.confidence, 2),
            "evidence_count": sc.evidence_count,
        }
        for sc in profile.detected_specialties
    ]

    top_specialty = None
    confidence = 0.0
    evidence_count = 0

    if profile.detected_specialties:
        top = profile.detected_specialties[0]
        top_specialty = top.specialty.value
        confidence = round(top.confidence, 2)
        evidence_count = top.evidence_count

    return SpecialtyDetectionResponse(
        detected_specialties=detected_specialties,
        top_specialty=top_specialty,
        confidence=confidence,
        evidence_count=evidence_count,
    )


@router.post("/profile/feedback")
async def provide_feedback(
    feedback: QueryFeedbackRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Provide feedback on query results.

    Args:
        feedback: Query feedback.

    Returns:
        Success message.
    """
    user_id = current_user["sub"]

    # Update query history
    storage.update_query_feedback(
        query_id=feedback.query_id,
        feedback_rating=feedback.rating,
        clicked_results=feedback.clicked_results,
    )

    # Get profile and query history
    profile = storage.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Get the specific query record
    history = storage.get_query_history(user_id, limit=1000)
    query_record = next((h for h in history if h.id == feedback.query_id), None)

    if query_record:
        # Update profile based on feedback
        profile = learner.update_from_feedback(
            profile,
            query_record,
            feedback.rating,
            feedback.clicked_results,
        )
        storage.save_profile(profile)

    return {
        "status": "success",
        "message": "Feedback recorded successfully",
        "query_id": feedback.query_id,
        "rating": feedback.rating,
    }


@router.get("/recommendations")
async def get_recommendations(
    context: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> RecommendationsResponse:
    """
    Get personalized recommendations.

    Args:
        context: Optional context (e.g., specific condition).

    Returns:
        Personalized recommendations.
    """
    user_id = current_user["sub"]

    # Get profile
    profile = storage.get_profile(user_id)

    if not profile:
        return RecommendationsResponse()

    # Get query patterns
    pattern = storage.get_query_pattern(user_id)
    if not pattern:
        # Compute from history
        history = storage.get_recent_query_history(user_id, days=90)
        pattern = learner.compute_query_patterns(history)
        if pattern.total_queries > 0:
            storage.save_query_pattern(pattern)

    # Generate recommendations
    guidelines = recommender.recommend_guidelines(profile, context)
    calculators = recommender.recommend_calculators(profile)
    cme_topics = recommender.recommend_cme_topics(profile, pattern) if pattern else []
    reading = recommender.recommend_reading(profile)

    return RecommendationsResponse(
        guidelines=guidelines,
        calculators=calculators,
        cme_topics=cme_topics,
        reading=reading,
    )


@router.get("/insights")
async def get_insights(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get learning insights about the profile.

    Returns:
        Learning insights and statistics.
    """
    user_id = current_user["sub"]

    # Get profile
    profile = storage.get_profile(user_id)

    if not profile:
        return {
            "error": "Profile not found",
            "total_queries": 0,
        }

    # Get patterns
    pattern = storage.get_query_pattern(user_id)

    if not pattern:
        history = storage.get_recent_query_history(user_id, days=90)
        pattern = learner.compute_query_patterns(history)

    # Generate insights
    insights = learner.get_learning_insights(profile, pattern)

    return insights


@router.delete("/profile")
async def delete_profile(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Delete all user data (GDPR compliance).

    Returns:
        Success message.
    """
    user_id = current_user["sub"]

    # Delete all data
    storage.delete_user_data(user_id)

    return {
        "status": "success",
        "message": "All user data deleted successfully",
        "user_id": user_id,
    }


@router.get("/statistics")
async def get_statistics(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get overall platform statistics (admin only).

    Returns:
        Platform statistics.
    """
    # In production, check if user is admin
    # For now, return stats for all users

    stats = storage.get_statistics()

    return stats
