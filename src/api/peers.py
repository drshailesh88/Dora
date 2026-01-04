"""
Peer Network API Endpoints

RESTful API for specialist network, consultations, case discussions,
and peer-to-peer features.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user
from src.peers import (
    get_peer_network_service,
    Specialist,
    ConsultRequest,
    ConsultResponse,
    ConsultPriority,
    ConsultType,
    CaseDiscussion,
    CaseVisibility,
    PeerNetworkStats,
    VerificationLevel,
)


router = APIRouter(prefix="/api/v1/peers", tags=["peers"])


# ==================== Request/Response Models ====================

class SpecialistRegistrationRequest(BaseModel):
    """Request to register as specialist."""
    registration_number: str
    primary_specialty: str
    bio: Optional[str] = None
    city: str = ""
    state: str = ""
    hospital_affiliations: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["English", "Hindi"])


class ConsultationRequest(BaseModel):
    """Request to create consultation."""
    specialty_needed: str
    chief_complaint: str = Field(..., max_length=200)
    case_summary: str
    specific_question: str
    priority: ConsultPriority = ConsultPriority.ROUTINE
    consult_type: ConsultType = ConsultType.ASYNC
    patient_age: Optional[int] = Field(None, ge=0, le=150)
    patient_gender: Optional[str] = None
    relevant_history: str = ""
    current_medications: list[str] = Field(default_factory=list)
    max_fee: Optional[int] = Field(None, description="Max fee in paise")
    preferred_language: str = "English"


class ConsultationResponseRequest(BaseModel):
    """Request to respond to consultation."""
    response_text: str
    recommendations: list[str] = Field(default_factory=list)
    differential_diagnosis: list[str] = Field(default_factory=list)
    suggested_investigations: list[str] = Field(default_factory=list)
    treatment_plan: Optional[str] = None
    follow_up_needed: bool = False


class ReviewSubmissionRequest(BaseModel):
    """Request to submit review."""
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    expertise_rating: float = Field(..., ge=1.0, le=5.0)
    communication_rating: float = Field(..., ge=1.0, le=5.0)
    timeliness_rating: float = Field(..., ge=1.0, le=5.0)
    positive_feedback: Optional[str] = Field(None, max_length=500)
    areas_for_improvement: Optional[str] = Field(None, max_length=500)
    would_consult_again: bool = True


class CaseSubmissionRequest(BaseModel):
    """Request to submit case discussion."""
    title: str = Field(..., max_length=200)
    specialty: str
    case_category: str
    case_presentation: str
    diagnosis: str
    learning_points: list[str] = Field(default_factory=list)
    discussion_points: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    visibility: CaseVisibility = CaseVisibility.SPECIALTY


class CommentRequest(BaseModel):
    """Request to add comment."""
    comment_text: str = Field(..., max_length=1000)
    parent_comment_id: Optional[str] = None


class MessageRequest(BaseModel):
    """Request to send message."""
    message_text: str = Field(..., max_length=5000)
    receiver_id: str


# ==================== Specialist Directory Endpoints ====================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_as_specialist(
    request: SpecialistRegistrationRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Register as specialist.

    Returns:
        Specialist profile
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    specialist = service.register_as_specialist(
        user_id=user_id,
        name=current_user.get("name", ""),
        email=current_user.get("email", ""),
        registration_number=request.registration_number,
        primary_specialty=request.primary_specialty,
        bio=request.bio or "",
        city=request.city,
        state=request.state,
        hospital_affiliations=request.hospital_affiliations,
        languages=request.languages,
    )

    return {
        "status": "success",
        "message": "Registered as specialist",
        "specialist": specialist.model_dump(),
    }


@router.get("/specialists")
async def search_specialists(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    min_rating: float = Query(0.0, ge=0.0, le=5.0),
    is_available: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Search for specialists.

    Returns:
        List of matching specialists
    """
    service = get_peer_network_service()

    specialists = service.search_specialists(
        specialty=specialty,
        city=city,
        state=state,
        min_rating=min_rating,
        is_available=is_available,
        limit=limit,
    )

    return {
        "specialists": [s.model_dump() for s in specialists],
        "count": len(specialists),
    }


@router.get("/specialists/{specialist_id}")
async def get_specialist_profile(
    specialist_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get specialist profile.

    Returns:
        Specialist profile with stats
    """
    service = get_peer_network_service()

    specialist = service.get_specialist(specialist_id)
    if not specialist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialist not found"
        )

    # Get reviews
    reviews = service.consultations.get_reviews_for_specialist(specialist_id, public_only=True)

    return {
        "specialist": specialist.model_dump(),
        "reviews": [r.model_dump() for r in reviews[:5]],  # Latest 5 reviews
        "total_reviews": len(reviews),
    }


# ==================== Consultation Endpoints ====================

@router.post("/consult", status_code=status.HTTP_201_CREATED)
async def request_consultation(
    request: ConsultationRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Request a consultation with a specialist.

    Returns:
        Consultation request with matched specialist
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    result = await service.request_consultation(
        requesting_doctor_id=user_id,
        specialty_needed=request.specialty_needed,
        chief_complaint=request.chief_complaint,
        case_summary=request.case_summary,
        specific_question=request.specific_question,
        priority=request.priority,
        consult_type=request.consult_type,
        patient_age=request.patient_age,
        patient_gender=request.patient_gender,
        relevant_history=request.relevant_history,
        current_medications=request.current_medications,
        max_fee=request.max_fee,
        preferred_language=request.preferred_language,
        auto_match=True,
    )

    return {
        "status": "success",
        "message": "Consultation requested",
        "consultation": result["request"].model_dump(),
        "matched_specialist": result["matched_specialist"].model_dump() if result["matched_specialist"] else None,
    }


@router.get("/consult/{consult_id}")
async def get_consultation(
    consult_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get consultation details.

    Returns:
        Consultation with responses and messages
    """
    service = get_peer_network_service()

    consultation = service.consultations.get_request(consult_id)
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )

    # Get responses
    responses = service.consultations.get_responses_for_request(consult_id)

    # Get messages
    messages = service.messaging.get_messages(consult_id)

    return {
        "consultation": consultation.model_dump(),
        "responses": [r.model_dump() for r in responses],
        "messages": [m.model_dump() for m in messages],
    }


@router.post("/consult/{consult_id}/accept")
async def accept_consultation(
    consult_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Accept consultation request (specialist only).

    Returns:
        Updated consultation
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    # Get specialist ID
    specialist = service.directory.get_specialist_by_user_id(user_id)
    if not specialist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not registered as specialist"
        )

    consultation = service.accept_consultation(
        request_id=consult_id,
        specialist_id=specialist.id,
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot accept consultation"
        )

    return {
        "status": "success",
        "message": "Consultation accepted",
        "consultation": consultation.model_dump(),
    }


@router.post("/consult/{consult_id}/respond")
async def respond_to_consultation(
    consult_id: str,
    request: ConsultationResponseRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Respond to consultation (specialist only).

    Returns:
        Consultation response
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    # Get specialist ID
    specialist = service.directory.get_specialist_by_user_id(user_id)
    if not specialist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not registered as specialist"
        )

    response = service.respond_to_consultation(
        consult_request_id=consult_id,
        specialist_id=specialist.id,
        response_text=request.response_text,
        recommendations=request.recommendations,
        differential_diagnosis=request.differential_diagnosis,
        suggested_investigations=request.suggested_investigations,
        treatment_plan=request.treatment_plan,
        follow_up_needed=request.follow_up_needed,
    )

    return {
        "status": "success",
        "message": "Response submitted",
        "response": response.model_dump(),
    }


@router.post("/consult/{consult_id}/review")
async def submit_review(
    consult_id: str,
    request: ReviewSubmissionRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Submit review for consultation.

    Returns:
        Peer review
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    # Get consultation
    consultation = service.consultations.get_request(consult_id)
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found"
        )

    if consultation.requesting_doctor_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only review your own consultations"
        )

    if not consultation.specialist_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No specialist assigned"
        )

    review = service.submit_consultation_review(
        consult_request_id=consult_id,
        specialist_id=consultation.specialist_id,
        reviewer_id=user_id,
        overall_rating=request.overall_rating,
        expertise_rating=request.expertise_rating,
        communication_rating=request.communication_rating,
        timeliness_rating=request.timeliness_rating,
        positive_feedback=request.positive_feedback,
        areas_for_improvement=request.areas_for_improvement,
        would_consult_again=request.would_consult_again,
    )

    return {
        "status": "success",
        "message": "Review submitted",
        "review": review.model_dump(),
    }


@router.get("/my-consults")
async def get_my_consultations(
    as_specialist: bool = Query(False),
    status_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get my consultations.

    Returns:
        List of consultations
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    consultations = service.get_my_consultations(
        user_id=user_id,
        as_requester=not as_specialist,
    )

    return {
        "consultations": [c.model_dump() for c in consultations],
        "count": len(consultations),
    }


# ==================== Case Library Endpoints ====================

@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def submit_case(
    request: CaseSubmissionRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Submit a case discussion.

    Returns:
        Case discussion
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    case = service.submit_case(
        submitted_by=user_id,
        title=request.title,
        specialty=request.specialty,
        case_category=request.case_category,
        case_presentation=request.case_presentation,
        diagnosis=request.diagnosis,
        learning_points=request.learning_points,
        discussion_points=request.discussion_points,
        references=request.references,
        visibility=request.visibility,
    )

    return {
        "status": "success",
        "message": "Case submitted",
        "case": case.model_dump(),
    }


@router.get("/cases")
async def browse_cases(
    specialty: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Browse case discussions.

    Returns:
        List of cases
    """
    service = get_peer_network_service()
    user_specialty = current_user.get("specialty")

    cases = service.browse_cases(
        specialty=specialty,
        category=category,
        featured_only=featured_only,
        user_specialty=user_specialty,
        limit=limit,
    )

    return {
        "cases": [c.model_dump() for c in cases],
        "count": len(cases),
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get case discussion with comments.

    Returns:
        Case with comments
    """
    service = get_peer_network_service()

    case = service.cases.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    comments = service.cases.get_comments(case_id)

    return {
        "case": case.model_dump(),
        "comments": [c.model_dump() for c in comments],
    }


@router.post("/cases/{case_id}/comments")
async def add_comment(
    case_id: str,
    request: CommentRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Add comment to case.

    Returns:
        Case comment
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    comment = service.add_case_comment(
        case_id=case_id,
        commenter_id=user_id,
        commenter_name=current_user.get("name", "Doctor"),
        commenter_specialty=current_user.get("specialty", "general"),
        comment_text=request.comment_text,
        parent_comment_id=request.parent_comment_id,
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    return {
        "status": "success",
        "message": "Comment added",
        "comment": comment.model_dump(),
    }


@router.post("/cases/{case_id}/upvote")
async def upvote_case(
    case_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Upvote a case.

    Returns:
        Success message
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    success = service.cases.upvote_case(case_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    return {
        "status": "success",
        "message": "Case upvoted",
    }


# ==================== Messaging Endpoints ====================

@router.post("/consult/{consult_id}/messages")
async def send_message(
    consult_id: str,
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Send message in consultation.

    Returns:
        Message
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    message = service.send_message(
        consult_request_id=consult_id,
        sender_id=user_id,
        receiver_id=request.receiver_id,
        message_text=request.message_text,
    )

    return {
        "status": "success",
        "message": "Message sent",
        "data": message.model_dump(),
    }


@router.post("/consult/{consult_id}/messages/read")
async def mark_messages_read(
    consult_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Mark all messages as read.

    Returns:
        Count of marked messages
    """
    user_id = current_user["sub"]
    service = get_peer_network_service()

    count = service.mark_messages_read(consult_id, user_id)

    return {
        "status": "success",
        "message": f"{count} messages marked as read",
        "count": count,
    }


# ==================== Statistics Endpoints ====================

@router.get("/stats", response_model=PeerNetworkStats)
async def get_platform_stats(
    current_user: dict = Depends(get_current_user),
) -> PeerNetworkStats:
    """
    Get platform-wide statistics.

    Returns:
        Peer network statistics
    """
    service = get_peer_network_service()
    return service.get_platform_stats()


@router.get("/specialists/{specialist_id}/stats")
async def get_specialist_stats(
    specialist_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get specialist statistics.

    Returns:
        Specialist stats
    """
    service = get_peer_network_service()

    stats = service.consultations.get_consultation_stats(specialist_id)
    earnings = service.get_specialist_earnings(specialist_id)

    return {
        **stats,
        **earnings,
    }
