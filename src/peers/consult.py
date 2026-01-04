"""
Consultation System

Manage consultation requests, responses, and lifecycle.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.peers.models import (
    ConsultRequest,
    ConsultResponse,
    ConsultStatus,
    ConsultPriority,
    ConsultType,
    PeerReview,
)


class ConsultationManager:
    """Manages consultation requests and responses."""

    def __init__(self):
        """Initialize consultation manager."""
        # In production, use database
        self.requests: dict[str, ConsultRequest] = {}
        self.responses: dict[str, ConsultResponse] = {}
        self.reviews: dict[str, list[PeerReview]] = {}

    def create_request(
        self,
        requesting_doctor_id: str,
        specialty_needed: str,
        chief_complaint: str,
        case_summary: str,
        specific_question: str,
        priority: ConsultPriority = ConsultPriority.ROUTINE,
        consult_type: ConsultType = ConsultType.ASYNC,
        **kwargs,
    ) -> ConsultRequest:
        """
        Create a consultation request.

        Args:
            requesting_doctor_id: Doctor ID
            specialty_needed: Required specialty
            chief_complaint: Brief complaint
            case_summary: Detailed case
            specific_question: Specific question
            priority: Priority level
            consult_type: Type of consultation
            **kwargs: Additional fields

        Returns:
            ConsultRequest object
        """
        # Set expiration based on priority
        expiration_hours = {
            ConsultPriority.ROUTINE: 48,
            ConsultPriority.URGENT: 6,
            ConsultPriority.EMERGENCY: 1,
        }
        expires_at = datetime.utcnow() + timedelta(
            hours=expiration_hours[priority]
        )

        request = ConsultRequest(
            requesting_doctor_id=requesting_doctor_id,
            specialty_needed=specialty_needed,
            chief_complaint=chief_complaint,
            case_summary=case_summary,
            specific_question=specific_question,
            priority=priority,
            consult_type=consult_type,
            expires_at=expires_at,
            **kwargs,
        )

        self.requests[request.id] = request
        return request

    def get_request(self, request_id: str) -> Optional[ConsultRequest]:
        """
        Get consultation request by ID.

        Args:
            request_id: Request ID

        Returns:
            ConsultRequest or None
        """
        return self.requests.get(request_id)

    def update_request_status(
        self,
        request_id: str,
        status: ConsultStatus,
        **kwargs,
    ) -> Optional[ConsultRequest]:
        """
        Update consultation request status.

        Args:
            request_id: Request ID
            status: New status
            **kwargs: Additional updates

        Returns:
            Updated request or None
        """
        request = self.requests.get(request_id)
        if not request:
            return None

        request.status = status
        request.updated_at = datetime.utcnow()

        # Update status-specific timestamps
        if status == ConsultStatus.MATCHED:
            request.matched_at = datetime.utcnow()
        elif status == ConsultStatus.ACCEPTED:
            request.accepted_at = datetime.utcnow()

        # Apply additional updates
        for key, value in kwargs.items():
            if hasattr(request, key):
                setattr(request, key, value)

        return request

    def assign_specialist(
        self,
        request_id: str,
        specialist_id: str,
    ) -> Optional[ConsultRequest]:
        """
        Assign specialist to consultation request.

        Args:
            request_id: Request ID
            specialist_id: Specialist ID

        Returns:
            Updated request or None
        """
        return self.update_request_status(
            request_id=request_id,
            status=ConsultStatus.MATCHED,
            specialist_id=specialist_id,
        )

    def accept_request(
        self,
        request_id: str,
        specialist_id: str,
    ) -> Optional[ConsultRequest]:
        """
        Specialist accepts consultation request.

        Args:
            request_id: Request ID
            specialist_id: Specialist ID

        Returns:
            Updated request or None
        """
        request = self.requests.get(request_id)
        if not request:
            return None

        if request.specialist_id != specialist_id:
            return None  # Not assigned to this specialist

        return self.update_request_status(
            request_id=request_id,
            status=ConsultStatus.ACCEPTED,
        )

    def decline_request(
        self,
        request_id: str,
        specialist_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Specialist declines consultation request.

        Args:
            request_id: Request ID
            specialist_id: Specialist ID
            reason: Decline reason

        Returns:
            Success status
        """
        request = self.requests.get(request_id)
        if not request or request.specialist_id != specialist_id:
            return False

        # Reset to pending for reassignment
        request.specialist_id = None
        request.status = ConsultStatus.PENDING
        request.updated_at = datetime.utcnow()

        return True

    def create_response(
        self,
        consult_request_id: str,
        specialist_id: str,
        response_text: str,
        recommendations: Optional[list[str]] = None,
        **kwargs,
    ) -> ConsultResponse:
        """
        Create specialist response to consultation.

        Args:
            consult_request_id: Consultation request ID
            specialist_id: Specialist ID
            response_text: Detailed response
            recommendations: Action items
            **kwargs: Additional fields

        Returns:
            ConsultResponse object
        """
        request = self.requests.get(consult_request_id)

        # Calculate response time
        response_time_hours = 0.0
        if request and request.accepted_at:
            time_diff = datetime.utcnow() - request.accepted_at
            response_time_hours = time_diff.total_seconds() / 3600

        response = ConsultResponse(
            consult_request_id=consult_request_id,
            specialist_id=specialist_id,
            response_text=response_text,
            recommendations=recommendations or [],
            response_time_hours=response_time_hours,
            **kwargs,
        )

        self.responses[response.id] = response

        # Update request status
        if request:
            request.status = ConsultStatus.RESPONDED
            request.updated_at = datetime.utcnow()

        return response

    def get_response(self, response_id: str) -> Optional[ConsultResponse]:
        """
        Get consultation response by ID.

        Args:
            response_id: Response ID

        Returns:
            ConsultResponse or None
        """
        return self.responses.get(response_id)

    def get_responses_for_request(
        self,
        request_id: str,
    ) -> list[ConsultResponse]:
        """
        Get all responses for a consultation request.

        Args:
            request_id: Request ID

        Returns:
            List of responses
        """
        return [
            r for r in self.responses.values()
            if r.consult_request_id == request_id
        ]

    def complete_consultation(
        self,
        request_id: str,
    ) -> Optional[ConsultRequest]:
        """
        Mark consultation as completed.

        Args:
            request_id: Request ID

        Returns:
            Updated request or None
        """
        return self.update_request_status(
            request_id=request_id,
            status=ConsultStatus.COMPLETED,
        )

    def cancel_consultation(
        self,
        request_id: str,
        reason: Optional[str] = None,
    ) -> Optional[ConsultRequest]:
        """
        Cancel consultation request.

        Args:
            request_id: Request ID
            reason: Cancellation reason

        Returns:
            Updated request or None
        """
        return self.update_request_status(
            request_id=request_id,
            status=ConsultStatus.CANCELLED,
        )

    def submit_review(
        self,
        consult_request_id: str,
        specialist_id: str,
        reviewer_id: str,
        overall_rating: float,
        expertise_rating: float,
        communication_rating: float,
        timeliness_rating: float,
        **kwargs,
    ) -> PeerReview:
        """
        Submit review for consultation.

        Args:
            consult_request_id: Consultation request ID
            specialist_id: Specialist ID
            reviewer_id: Reviewer (requesting doctor) ID
            overall_rating: Overall rating (1-5)
            expertise_rating: Expertise rating (1-5)
            communication_rating: Communication rating (1-5)
            timeliness_rating: Timeliness rating (1-5)
            **kwargs: Additional fields

        Returns:
            PeerReview object
        """
        review = PeerReview(
            consult_request_id=consult_request_id,
            specialist_id=specialist_id,
            reviewer_id=reviewer_id,
            overall_rating=overall_rating,
            expertise_rating=expertise_rating,
            communication_rating=communication_rating,
            timeliness_rating=timeliness_rating,
            **kwargs,
        )

        # Store review
        if specialist_id not in self.reviews:
            self.reviews[specialist_id] = []
        self.reviews[specialist_id].append(review)

        # Mark consultation as completed
        self.complete_consultation(consult_request_id)

        return review

    def get_reviews_for_specialist(
        self,
        specialist_id: str,
        public_only: bool = True,
    ) -> list[PeerReview]:
        """
        Get reviews for a specialist.

        Args:
            specialist_id: Specialist ID
            public_only: Only return public reviews

        Returns:
            List of reviews
        """
        reviews = self.reviews.get(specialist_id, [])

        if public_only:
            reviews = [r for r in reviews if r.is_public]

        # Sort by creation date (newest first)
        reviews.sort(key=lambda r: r.created_at, reverse=True)

        return reviews

    def get_requests_for_doctor(
        self,
        doctor_id: str,
        status: Optional[ConsultStatus] = None,
    ) -> list[ConsultRequest]:
        """
        Get consultation requests by a doctor.

        Args:
            doctor_id: Doctor ID
            status: Filter by status

        Returns:
            List of requests
        """
        requests = [
            r for r in self.requests.values()
            if r.requesting_doctor_id == doctor_id
        ]

        if status:
            requests = [r for r in requests if r.status == status]

        # Sort by creation date (newest first)
        requests.sort(key=lambda r: r.created_at, reverse=True)

        return requests

    def get_requests_for_specialist(
        self,
        specialist_id: str,
        status: Optional[ConsultStatus] = None,
    ) -> list[ConsultRequest]:
        """
        Get consultation requests for a specialist.

        Args:
            specialist_id: Specialist ID
            status: Filter by status

        Returns:
            List of requests
        """
        requests = [
            r for r in self.requests.values()
            if r.specialist_id == specialist_id
        ]

        if status:
            requests = [r for r in requests if r.status == status]

        # Sort by priority and creation date
        priority_order = {
            ConsultPriority.EMERGENCY: 0,
            ConsultPriority.URGENT: 1,
            ConsultPriority.ROUTINE: 2,
        }
        requests.sort(
            key=lambda r: (priority_order[r.priority], r.created_at)
        )

        return requests

    def get_pending_requests_by_specialty(
        self,
        specialty: str,
        limit: int = 20,
    ) -> list[ConsultRequest]:
        """
        Get pending consultation requests for a specialty.

        Args:
            specialty: Specialty name
            limit: Maximum results

        Returns:
            List of pending requests
        """
        requests = [
            r for r in self.requests.values()
            if r.specialty_needed == specialty
            and r.status == ConsultStatus.PENDING
            and (r.expires_at is None or r.expires_at > datetime.utcnow())
        ]

        # Sort by priority and creation date
        priority_order = {
            ConsultPriority.EMERGENCY: 0,
            ConsultPriority.URGENT: 1,
            ConsultPriority.ROUTINE: 2,
        }
        requests.sort(
            key=lambda r: (priority_order[r.priority], r.created_at)
        )

        return requests[:limit]

    def expire_old_requests(self) -> list[str]:
        """
        Mark expired requests as expired.

        Returns:
            List of expired request IDs
        """
        expired_ids = []
        now = datetime.utcnow()

        for request in self.requests.values():
            if (
                request.status == ConsultStatus.PENDING
                and request.expires_at
                and request.expires_at < now
            ):
                request.status = ConsultStatus.EXPIRED
                request.updated_at = now
                expired_ids.append(request.id)

        return expired_ids

    def mark_response_helpful(
        self,
        response_id: str,
        helpful: bool,
        feedback: Optional[str] = None,
    ) -> Optional[ConsultResponse]:
        """
        Mark response as helpful or not.

        Args:
            response_id: Response ID
            helpful: Was it helpful?
            feedback: Optional feedback

        Returns:
            Updated response or None
        """
        response = self.responses.get(response_id)
        if not response:
            return None

        response.was_helpful = helpful
        response.helpfulness_feedback = feedback

        return response

    def get_consultation_stats(self, specialist_id: str) -> dict[str, Any]:
        """
        Get consultation statistics for specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            Statistics dictionary
        """
        requests = self.get_requests_for_specialist(specialist_id)
        reviews = self.get_reviews_for_specialist(specialist_id, public_only=False)

        total_requests = len(requests)
        completed = len([r for r in requests if r.status == ConsultStatus.COMPLETED])
        accepted = len([r for r in requests if r.status != ConsultStatus.CANCELLED])

        # Calculate average response time
        responses = [
            r for r in self.responses.values()
            if r.specialist_id == specialist_id
        ]
        avg_response_time = (
            sum(r.response_time_hours for r in responses) / len(responses)
            if responses else 0.0
        )

        # Calculate average rating
        avg_rating = (
            sum(r.overall_rating for r in reviews) / len(reviews)
            if reviews else 0.0
        )

        return {
            "total_requests": total_requests,
            "completed_consultations": completed,
            "acceptance_rate": accepted / total_requests if total_requests > 0 else 0.0,
            "average_response_time_hours": avg_response_time,
            "average_rating": avg_rating,
            "total_reviews": len(reviews),
        }
