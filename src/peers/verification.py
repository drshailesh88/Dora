"""
Specialist Verification

Medical license verification, specialty certification, and credential validation.
"""

from datetime import datetime
from typing import Optional

from src.peers.models import (
    VerificationDocument,
    VerificationRequest,
    VerificationLevel,
)


class SpecialistVerificationManager:
    """Manages specialist verification and credential validation."""

    def __init__(self):
        """Initialize verification manager."""
        # In production, use database
        self.documents: dict[str, VerificationDocument] = {}
        self.requests: dict[str, VerificationRequest] = {}

    def submit_verification_request(
        self,
        specialist_id: str,
        requested_level: VerificationLevel,
        document_ids: list[str],
        hospital_name: Optional[str] = None,
        hospital_contact_email: Optional[str] = None,
        hospital_contact_phone: Optional[str] = None,
        **kwargs,
    ) -> VerificationRequest:
        """
        Submit verification request.

        Args:
            specialist_id: Specialist ID
            requested_level: Verification level requested
            document_ids: List of uploaded document IDs
            hospital_name: Hospital affiliation
            hospital_contact_email: Hospital contact
            hospital_contact_phone: Hospital phone
            **kwargs: Additional fields

        Returns:
            VerificationRequest object
        """
        request = VerificationRequest(
            specialist_id=specialist_id,
            requested_level=requested_level,
            document_ids=document_ids,
            hospital_name=hospital_name,
            hospital_contact_email=hospital_contact_email,
            hospital_contact_phone=hospital_contact_phone,
            **kwargs,
        )

        self.requests[request.id] = request
        return request

    def upload_document(
        self,
        specialist_id: str,
        document_type: str,
        document_url: str,
        document_number: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> VerificationDocument:
        """
        Upload verification document.

        Args:
            specialist_id: Specialist ID
            document_type: Type of document
            document_url: Encrypted document URL
            document_number: Document number
            expires_at: Expiration date

        Returns:
            VerificationDocument object
        """
        document = VerificationDocument(
            specialist_id=specialist_id,
            document_type=document_type,
            document_url=document_url,
            document_number=document_number,
            expires_at=expires_at,
        )

        self.documents[document.id] = document
        return document

    def review_verification_request(
        self,
        request_id: str,
        reviewer_id: str,
        approved: bool,
        rejection_reason: Optional[str] = None,
    ) -> Optional[VerificationRequest]:
        """
        Review and approve/reject verification request.

        Args:
            request_id: Request ID
            reviewer_id: Admin reviewer ID
            approved: Approval status
            rejection_reason: Rejection reason if not approved

        Returns:
            Updated request or None
        """
        request = self.requests.get(request_id)
        if not request:
            return None

        request.status = "approved" if approved else "rejected"
        request.reviewed_at = datetime.utcnow()
        request.reviewed_by = reviewer_id
        request.rejection_reason = rejection_reason
        request.updated_at = datetime.utcnow()

        return request

    def verify_document(
        self,
        document_id: str,
        reviewer_id: str,
        verified: bool,
        notes: Optional[str] = None,
    ) -> Optional[VerificationDocument]:
        """
        Verify a document.

        Args:
            document_id: Document ID
            reviewer_id: Admin reviewer ID
            verified: Verification status
            notes: Verification notes

        Returns:
            Updated document or None
        """
        document = self.documents.get(document_id)
        if not document:
            return None

        document.is_verified = verified
        document.verified_at = datetime.utcnow()
        document.verified_by = reviewer_id
        document.verification_notes = notes

        return document

    def get_verification_request(
        self,
        request_id: str,
    ) -> Optional[VerificationRequest]:
        """
        Get verification request by ID.

        Args:
            request_id: Request ID

        Returns:
            VerificationRequest or None
        """
        return self.requests.get(request_id)

    def get_specialist_verification_requests(
        self,
        specialist_id: str,
    ) -> list[VerificationRequest]:
        """
        Get all verification requests for specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            List of verification requests
        """
        requests = [
            r for r in self.requests.values()
            if r.specialist_id == specialist_id
        ]
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests

    def get_pending_verification_requests(self) -> list[VerificationRequest]:
        """
        Get all pending verification requests.

        Returns:
            List of pending requests
        """
        pending = [
            r for r in self.requests.values()
            if r.status == "pending"
        ]
        pending.sort(key=lambda r: r.created_at)
        return pending

    def get_specialist_documents(
        self,
        specialist_id: str,
        verified_only: bool = False,
    ) -> list[VerificationDocument]:
        """
        Get documents for specialist.

        Args:
            specialist_id: Specialist ID
            verified_only: Only verified documents

        Returns:
            List of documents
        """
        documents = [
            d for d in self.documents.values()
            if d.specialist_id == specialist_id
        ]

        if verified_only:
            documents = [d for d in documents if d.is_verified]

        documents.sort(key=lambda d: d.uploaded_at, reverse=True)
        return documents

    def verify_medical_license(
        self,
        license_number: str,
        registration_council: str,
    ) -> dict[str, any]:
        """
        Verify medical license with registry.

        Args:
            license_number: License number
            registration_council: Registration council

        Returns:
            Verification result
        """
        # In production, integrate with:
        # - Medical Council of India (MCI) / National Medical Commission (NMC)
        # - State medical councils
        # - International medical registries

        # For now, return placeholder
        return {
            "valid": True,
            "license_number": license_number,
            "council": registration_council,
            "doctor_name": "Dr. Example",
            "qualification": "MBBS, MD",
            "registration_date": "2010-01-01",
            "status": "active",
        }

    def verify_specialty_certification(
        self,
        certification_number: str,
        certifying_body: str,
    ) -> dict[str, any]:
        """
        Verify specialty board certification.

        Args:
            certification_number: Certification number
            certifying_body: Certifying organization

        Returns:
            Verification result
        """
        # In production, integrate with:
        # - National Board of Examinations (NBE)
        # - Medical specialty colleges (ACC, ASI, etc.)

        # For now, return placeholder
        return {
            "valid": True,
            "certification_number": certification_number,
            "certifying_body": certifying_body,
            "specialty": "Cardiology",
            "certification_date": "2015-06-01",
            "expiration_date": None,  # Most don't expire
            "status": "active",
        }

    def verify_hospital_affiliation(
        self,
        hospital_name: str,
        hospital_contact: str,
    ) -> bool:
        """
        Verify hospital affiliation.

        Args:
            hospital_name: Hospital name
            hospital_contact: Contact email/phone

        Returns:
            True if verified
        """
        # In production, send verification request to hospital
        # For now, return True
        return True

    def check_background(
        self,
        specialist_id: str,
    ) -> dict[str, any]:
        """
        Perform background check.

        Args:
            specialist_id: Specialist ID

        Returns:
            Background check result
        """
        # In production, check:
        # - Malpractice history
        # - License suspensions
        # - Criminal background
        # - Professional references

        # For now, return clean record
        return {
            "malpractice_cases": 0,
            "license_suspensions": 0,
            "criminal_record": False,
            "references_verified": True,
            "status": "clear",
        }

    def calculate_verification_level(
        self,
        specialist_id: str,
    ) -> VerificationLevel:
        """
        Calculate appropriate verification level based on credentials.

        Args:
            specialist_id: Specialist ID

        Returns:
            Recommended verification level
        """
        documents = self.get_specialist_documents(specialist_id, verified_only=True)

        has_license = any(d.document_type == "license" for d in documents)
        has_certification = any(d.document_type == "certificate" for d in documents)
        has_hospital = any(d.document_type == "hospital_affiliation" for d in documents)

        # Determine level
        if has_license and has_certification and has_hospital:
            # Check experience and reviews for Expert level
            # This would integrate with specialist profile
            return VerificationLevel.CERTIFIED
        elif has_license and has_certification:
            return VerificationLevel.CERTIFIED
        elif has_license:
            return VerificationLevel.VERIFIED
        else:
            return VerificationLevel.UNVERIFIED

    def get_verification_stats(self) -> dict[str, int]:
        """
        Get verification statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = len(self.requests)
        pending = len([r for r in self.requests.values() if r.status == "pending"])
        approved = len([r for r in self.requests.values() if r.status == "approved"])
        rejected = len([r for r in self.requests.values() if r.status == "rejected"])

        total_documents = len(self.documents)
        verified_documents = len([d for d in self.documents.values() if d.is_verified])

        return {
            "total_requests": total_requests,
            "pending_requests": pending,
            "approved_requests": approved,
            "rejected_requests": rejected,
            "total_documents": total_documents,
            "verified_documents": verified_documents,
        }

    def send_verification_reminder(
        self,
        specialist_id: str,
    ) -> bool:
        """
        Send reminder to complete verification.

        Args:
            specialist_id: Specialist ID

        Returns:
            Success status
        """
        # In production, send email/SMS reminder
        # For now, return True
        return True

    def expire_old_documents(self) -> list[str]:
        """
        Mark expired documents as unverified.

        Returns:
            List of expired document IDs
        """
        expired_ids = []
        now = datetime.utcnow()

        for document in self.documents.values():
            if (
                document.is_verified
                and document.expires_at
                and document.expires_at < now
            ):
                document.is_verified = False
                document.verification_notes = "Document expired"
                expired_ids.append(document.id)

        return expired_ids
