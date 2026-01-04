"""
Peer Network Service

Main service coordinating specialist directory, consultations, matching,
cases, messaging, payments, and verification.
"""

from datetime import datetime
from typing import Any, Optional

from src.peers.models import (
    Specialist,
    ConsultRequest,
    ConsultResponse,
    ConsultStatus,
    ConsultPriority,
    ConsultType,
    PeerReview,
    CaseDiscussion,
    CaseComment,
    CaseVisibility,
    ConsultMessage,
    MessageType,
    ConsultPayment,
    VerificationLevel,
    VerificationRequest,
    PeerNetworkStats,
)
from src.peers.directory import SpecialistDirectory
from src.peers.consult import ConsultationManager
from src.peers.matching import SpecialistMatcher
from src.peers.cases import CaseLibraryManager
from src.peers.messaging import SecureMessaging
from src.peers.payments import ConsultationPaymentManager
from src.peers.verification import SpecialistVerificationManager


class PeerNetworkService:
    """Main peer network service coordinating all features."""

    def __init__(self):
        """Initialize peer network service."""
        self.directory = SpecialistDirectory()
        self.consultations = ConsultationManager()
        self.matcher = SpecialistMatcher()
        self.cases = CaseLibraryManager()
        self.messaging = SecureMessaging()
        self.payments = ConsultationPaymentManager()
        self.verification = SpecialistVerificationManager()

    # ==================== Specialist Directory ====================

    def register_as_specialist(
        self,
        user_id: str,
        name: str,
        email: str,
        registration_number: str,
        primary_specialty: str,
        **kwargs,
    ) -> Specialist:
        """
        Register user as specialist.

        Args:
            user_id: User ID
            name: Full name
            email: Email
            registration_number: Medical license
            primary_specialty: Primary specialty
            **kwargs: Additional fields

        Returns:
            Specialist profile
        """
        return self.directory.register_specialist(
            user_id=user_id,
            name=name,
            email=email,
            registration_number=registration_number,
            primary_specialty=primary_specialty,
            **kwargs,
        )

    def search_specialists(
        self,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        **kwargs,
    ) -> list[Specialist]:
        """
        Search for specialists.

        Args:
            specialty: Filter by specialty
            city: Filter by city
            **kwargs: Additional filters

        Returns:
            List of matching specialists
        """
        return self.directory.search_specialists(
            specialty=specialty,
            city=city,
            **kwargs,
        )

    def get_specialist(self, specialist_id: str) -> Optional[Specialist]:
        """Get specialist profile."""
        return self.directory.get_specialist(specialist_id)

    # ==================== Consultation Workflow ====================

    async def request_consultation(
        self,
        requesting_doctor_id: str,
        specialty_needed: str,
        chief_complaint: str,
        case_summary: str,
        specific_question: str,
        priority: ConsultPriority = ConsultPriority.ROUTINE,
        consult_type: ConsultType = ConsultType.ASYNC,
        auto_match: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Request a consultation.

        Args:
            requesting_doctor_id: Doctor ID
            specialty_needed: Required specialty
            chief_complaint: Brief complaint
            case_summary: Detailed case
            specific_question: Question for specialist
            priority: Priority level
            consult_type: Type of consultation
            auto_match: Auto-match with specialist
            **kwargs: Additional fields

        Returns:
            Consultation request with matched specialist
        """
        # Create consultation request
        request = self.consultations.create_request(
            requesting_doctor_id=requesting_doctor_id,
            specialty_needed=specialty_needed,
            chief_complaint=chief_complaint,
            case_summary=case_summary,
            specific_question=specific_question,
            priority=priority,
            consult_type=consult_type,
            **kwargs,
        )

        # Auto-match with specialist if requested
        matched_specialist = None
        if auto_match:
            available_specialists = self.directory.search_specialists(
                specialty=specialty_needed,
                is_available=True,
            )

            if available_specialists:
                best_match = self.matcher.find_best_match(
                    request=request,
                    available_specialists=available_specialists,
                )

                if best_match:
                    # Assign specialist
                    self.consultations.assign_specialist(
                        request_id=request.id,
                        specialist_id=best_match.id,
                    )
                    matched_specialist = best_match

        return {
            "request": request,
            "matched_specialist": matched_specialist,
        }

    def accept_consultation(
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
        return self.consultations.accept_request(
            request_id=request_id,
            specialist_id=specialist_id,
        )

    def respond_to_consultation(
        self,
        consult_request_id: str,
        specialist_id: str,
        response_text: str,
        recommendations: Optional[list[str]] = None,
        **kwargs,
    ) -> ConsultResponse:
        """
        Specialist responds to consultation.

        Args:
            consult_request_id: Consultation ID
            specialist_id: Specialist ID
            response_text: Response text
            recommendations: Recommendations
            **kwargs: Additional fields

        Returns:
            Consultation response
        """
        response = self.consultations.create_response(
            consult_request_id=consult_request_id,
            specialist_id=specialist_id,
            response_text=response_text,
            recommendations=recommendations,
            **kwargs,
        )

        # Release payment from escrow
        payment = self.payments.get_payment_for_consultation(consult_request_id)
        if payment:
            self.payments.release_payment(payment.id)

        # Update specialist stats
        request = self.consultations.get_request(consult_request_id)
        if request and request.specialist_id:
            self.directory.update_stats(
                specialist_id=request.specialist_id,
                response_time_hours=response.response_time_hours,
                accepted_consult=True,
            )

        return response

    def submit_consultation_review(
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
            consult_request_id: Consultation ID
            specialist_id: Specialist ID
            reviewer_id: Reviewer ID
            overall_rating: Overall rating
            expertise_rating: Expertise rating
            communication_rating: Communication rating
            timeliness_rating: Timeliness rating
            **kwargs: Additional fields

        Returns:
            Peer review
        """
        review = self.consultations.submit_review(
            consult_request_id=consult_request_id,
            specialist_id=specialist_id,
            reviewer_id=reviewer_id,
            overall_rating=overall_rating,
            expertise_rating=expertise_rating,
            communication_rating=communication_rating,
            timeliness_rating=timeliness_rating,
            **kwargs,
        )

        # Update specialist stats
        self.directory.update_stats(
            specialist_id=specialist_id,
            rating=overall_rating,
        )

        return review

    def get_my_consultations(
        self,
        user_id: str,
        as_requester: bool = True,
    ) -> list[ConsultRequest]:
        """
        Get consultations for user.

        Args:
            user_id: User ID
            as_requester: Get as requester (vs as specialist)

        Returns:
            List of consultation requests
        """
        if as_requester:
            return self.consultations.get_requests_for_doctor(user_id)
        else:
            # Get as specialist
            specialist = self.directory.get_specialist_by_user_id(user_id)
            if specialist:
                return self.consultations.get_requests_for_specialist(specialist.id)
            return []

    # ==================== Case Library ====================

    def submit_case(
        self,
        submitted_by: str,
        title: str,
        specialty: str,
        case_category: str,
        case_presentation: str,
        diagnosis: str,
        learning_points: list[str],
        visibility: CaseVisibility = CaseVisibility.SPECIALTY,
        **kwargs,
    ) -> CaseDiscussion:
        """
        Submit a case discussion.

        Args:
            submitted_by: Submitter ID
            title: Case title
            specialty: Specialty
            case_category: Category
            case_presentation: Full case
            diagnosis: Diagnosis
            learning_points: Learning points
            visibility: Visibility level
            **kwargs: Additional fields

        Returns:
            Case discussion
        """
        return self.cases.submit_case(
            submitted_by=submitted_by,
            title=title,
            specialty=specialty,
            case_category=case_category,
            case_presentation=case_presentation,
            diagnosis=diagnosis,
            learning_points=learning_points,
            visibility=visibility,
            **kwargs,
        )

    def browse_cases(
        self,
        specialty: Optional[str] = None,
        user_specialty: Optional[str] = None,
        **kwargs,
    ) -> list[CaseDiscussion]:
        """
        Browse case discussions.

        Args:
            specialty: Filter by specialty
            user_specialty: User's specialty
            **kwargs: Additional filters

        Returns:
            List of cases
        """
        return self.cases.browse_cases(
            specialty=specialty,
            user_specialty=user_specialty,
            **kwargs,
        )

    def add_case_comment(
        self,
        case_id: str,
        commenter_id: str,
        commenter_name: str,
        commenter_specialty: str,
        comment_text: str,
        **kwargs,
    ) -> Optional[CaseComment]:
        """
        Add comment to case.

        Args:
            case_id: Case ID
            commenter_id: Commenter ID
            commenter_name: Commenter name
            commenter_specialty: Commenter specialty
            comment_text: Comment text
            **kwargs: Additional fields

        Returns:
            Case comment or None
        """
        return self.cases.add_comment(
            case_id=case_id,
            commenter_id=commenter_id,
            commenter_name=commenter_name,
            commenter_specialty=commenter_specialty,
            comment_text=comment_text,
            **kwargs,
        )

    # ==================== Messaging ====================

    def send_message(
        self,
        consult_request_id: str,
        sender_id: str,
        receiver_id: str,
        message_text: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        **kwargs,
    ) -> ConsultMessage:
        """
        Send message in consultation.

        Args:
            consult_request_id: Consultation ID
            sender_id: Sender ID
            receiver_id: Receiver ID
            message_text: Message text
            message_type: Message type
            **kwargs: Additional fields

        Returns:
            Consult message
        """
        return self.messaging.send_message(
            consult_request_id=consult_request_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_text=message_text,
            message_type=message_type,
            **kwargs,
        )

    def get_messages(
        self,
        consult_request_id: str,
        limit: int = 100,
    ) -> list[ConsultMessage]:
        """Get messages for consultation."""
        return self.messaging.get_messages(consult_request_id, limit)

    def mark_messages_read(
        self,
        consult_request_id: str,
        user_id: str,
    ) -> int:
        """Mark all messages as read."""
        return self.messaging.mark_all_read(consult_request_id, user_id)

    # ==================== Payments ====================

    async def process_consultation_payment(
        self,
        consult_request_id: str,
        payer_id: str,
        payee_id: str,
        amount: int,
    ) -> ConsultPayment:
        """
        Process payment for consultation.

        Args:
            consult_request_id: Consultation ID
            payer_id: Payer ID
            payee_id: Payee (specialist) ID
            amount: Amount in paise

        Returns:
            Consultation payment
        """
        # Create payment
        payment = self.payments.create_payment(
            consult_request_id=consult_request_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
        )

        # Create Razorpay order
        order = self.payments.create_razorpay_order(payment.id)

        return payment

    def get_specialist_earnings(
        self,
        specialist_id: str,
    ) -> dict[str, int]:
        """Get specialist earnings."""
        return self.payments.get_specialist_earnings(specialist_id)

    # ==================== Verification ====================

    def submit_verification(
        self,
        specialist_id: str,
        requested_level: VerificationLevel,
        document_ids: list[str],
        **kwargs,
    ) -> VerificationRequest:
        """
        Submit verification request.

        Args:
            specialist_id: Specialist ID
            requested_level: Verification level
            document_ids: Document IDs
            **kwargs: Additional fields

        Returns:
            Verification request
        """
        return self.verification.submit_verification_request(
            specialist_id=specialist_id,
            requested_level=requested_level,
            document_ids=document_ids,
            **kwargs,
        )

    def upload_verification_document(
        self,
        specialist_id: str,
        document_type: str,
        document_url: str,
        **kwargs,
    ):
        """Upload verification document."""
        return self.verification.upload_document(
            specialist_id=specialist_id,
            document_type=document_type,
            document_url=document_url,
            **kwargs,
        )

    # ==================== Statistics ====================

    def get_platform_stats(self) -> PeerNetworkStats:
        """
        Get platform-wide statistics.

        Returns:
            Peer network statistics
        """
        dir_stats = self.directory.get_directory_stats()

        # Count by verification level
        verified = 0
        certified = 0
        expert = 0

        for specialist in self.directory.specialists.values():
            if specialist.verification_level == VerificationLevel.VERIFIED:
                verified += 1
            elif specialist.verification_level == VerificationLevel.CERTIFIED:
                certified += 1
            elif specialist.verification_level == VerificationLevel.EXPERT:
                expert += 1

        # Get consultation stats
        total_consults = len(self.consultations.requests)
        recent_consults_24h = len([
            r for r in self.consultations.requests.values()
            if (datetime.utcnow() - r.created_at).total_seconds() < 86400
        ])

        return PeerNetworkStats(
            total_specialists=dir_stats["total_specialists"],
            verified_specialists=verified,
            certified_specialists=certified,
            expert_specialists=expert,
            specialists_by_specialty=dir_stats["by_specialty"],
            total_consultations=total_consults,
            consultations_last_24h=recent_consults_24h,
            total_cases_shared=len(self.cases.cases),
            average_rating=dir_stats["average_rating"],
        )


# Global service instance
_peer_network_service = None


def get_peer_network_service() -> PeerNetworkService:
    """Get global peer network service instance."""
    global _peer_network_service

    if _peer_network_service is None:
        _peer_network_service = PeerNetworkService()

    return _peer_network_service
