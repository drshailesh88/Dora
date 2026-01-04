"""
Peer Network Data Models

Models for specialist network, consultations, case discussions,
peer reviews, and specialist verification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, EmailStr


class VerificationLevel(str, Enum):
    """Specialist verification levels."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"  # License confirmed
    CERTIFIED = "certified"  # Board certified
    EXPERT = "expert"  # 10+ years, top ratings


class ConsultStatus(str, Enum):
    """Consultation request status."""

    PENDING = "pending"
    MATCHED = "matched"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    RESPONDED = "responded"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ConsultPriority(str, Enum):
    """Consultation priority levels."""

    ROUTINE = "routine"  # 24-48 hours
    URGENT = "urgent"  # 4-6 hours
    EMERGENCY = "emergency"  # <1 hour


class ConsultType(str, Enum):
    """Types of consultations."""

    ASYNC = "async"  # Asynchronous message-based
    REAL_TIME = "real_time"  # Video/voice call
    SECOND_OPINION = "second_opinion"  # Review of case


class MessageType(str, Enum):
    """Message types in consultation."""

    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    VOICE = "voice"
    VIDEO = "video"


class PaymentStatus(str, Enum):
    """Consultation payment status."""

    PENDING = "pending"
    PAID = "paid"
    IN_ESCROW = "in_escrow"
    RELEASED = "released"
    REFUNDED = "refunded"


class CaseVisibility(str, Enum):
    """Case discussion visibility."""

    PRIVATE = "private"
    SPECIALTY = "specialty"  # Visible to specialty
    PUBLIC = "public"  # Visible to all


# ==================== Specialist Models ====================


class Expertise(BaseModel):
    """Specialist expertise area."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialty: str = Field(..., description="Primary specialty")
    sub_specialty: Optional[str] = Field(None, description="Sub-specialty")
    procedures: list[str] = Field(default_factory=list, description="Procedures performed")
    conditions: list[str] = Field(default_factory=list, description="Conditions treated")
    years_experience: int = Field(..., ge=0)
    certifications: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "specialty": "cardiology",
                "sub_specialty": "interventional_cardiology",
                "procedures": ["PCI", "CABG", "pacemaker_implantation"],
                "conditions": ["ACS", "heart_failure", "arrhythmias"],
                "years_experience": 12,
                "certifications": ["DM Cardiology", "Fellow ACC"]
            }
        }


class Availability(BaseModel):
    """Specialist availability."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialist_id: str
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(..., description="HH:MM format")
    end_time: str = Field(..., description="HH:MM format")
    is_active: bool = True
    max_consults_per_day: int = Field(default=10, ge=1)
    current_consults_today: int = Field(default=0, ge=0)

    def is_available(self) -> bool:
        """Check if specialist is available now."""
        return self.is_active and self.current_consults_today < self.max_consults_per_day


class ConsultFee(BaseModel):
    """Fee structure for consultations."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialist_id: str
    consult_type: ConsultType
    fee_amount: int = Field(..., ge=0, description="Amount in paise")
    currency: str = Field(default="INR")
    estimated_response_time_hours: int = Field(default=24, ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "consult_type": "async",
                "fee_amount": 50000,  # ₹500
                "currency": "INR",
                "estimated_response_time_hours": 24
            }
        }


class Specialist(BaseModel):
    """Verified specialist profile."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="Link to User model")

    # Profile
    name: str
    email: EmailStr
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    bio: str = Field(default="", max_length=500)

    # Credentials
    registration_number: str = Field(..., description="Medical license number")
    registration_council: str = Field(default="", description="e.g., MCI, state council")
    qualifications: list[str] = Field(default_factory=list, description="MBBS, MD, etc.")

    # Expertise
    expertise: list[Expertise] = Field(default_factory=list)
    primary_specialty: str = Field(..., description="Primary specialty")

    # Institution
    hospital_affiliations: list[str] = Field(default_factory=list)
    city: str = ""
    state: str = ""
    country: str = Field(default="India")

    # Verification
    verification_level: VerificationLevel = Field(default=VerificationLevel.UNVERIFIED)
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None

    # Stats
    total_consultations: int = Field(default=0, ge=0)
    average_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    total_reviews: int = Field(default=0, ge=0)
    average_response_time_hours: float = Field(default=24.0, ge=0.0)
    acceptance_rate: float = Field(default=1.0, ge=0.0, le=1.0)

    # Availability
    is_accepting_consults: bool = True
    languages: list[str] = Field(default_factory=lambda: ["English", "Hindi"])

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. Rajesh Kumar",
                "email": "rajesh.kumar@hospital.com",
                "registration_number": "MH/12345/2010",
                "primary_specialty": "cardiology",
                "city": "Mumbai",
                "verification_level": "expert",
                "average_rating": 4.8,
                "total_consultations": 156
            }
        }


# ==================== Consultation Models ====================


class ConsultRequest(BaseModel):
    """Consultation request from a doctor."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    requesting_doctor_id: str = Field(..., description="Doctor requesting consult")
    specialist_id: Optional[str] = Field(None, description="Specific specialist or auto-match")

    # Request details
    specialty_needed: str = Field(..., description="Specialty required")
    consult_type: ConsultType = Field(default=ConsultType.ASYNC)
    priority: ConsultPriority = Field(default=ConsultPriority.ROUTINE)

    # Case details
    chief_complaint: str = Field(..., max_length=200)
    case_summary: str = Field(..., description="Detailed case description")
    specific_question: str = Field(..., description="What you need help with")

    # Attachments
    lab_results: list[str] = Field(default_factory=list, description="URLs to lab reports")
    imaging_studies: list[str] = Field(default_factory=list, description="URLs to images")
    other_documents: list[str] = Field(default_factory=list)

    # Patient context (anonymized)
    patient_age: Optional[int] = Field(None, ge=0, le=150)
    patient_gender: Optional[str] = None
    relevant_history: str = Field(default="")
    current_medications: list[str] = Field(default_factory=list)

    # Preferences
    preferred_language: str = Field(default="English")
    max_fee: Optional[int] = Field(None, description="Maximum fee in paise")
    preferred_response_time_hours: int = Field(default=24, ge=1)

    # Status
    status: ConsultStatus = Field(default=ConsultStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Matching
    matched_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "specialty_needed": "cardiology",
                "priority": "urgent",
                "chief_complaint": "Chest pain with ECG changes",
                "case_summary": "45M with chest pain for 2 hours. ECG shows ST elevation in leads II, III, aVF.",
                "specific_question": "Is this STEMI? Should I start thrombolysis or transfer for PCI?",
                "patient_age": 45,
                "patient_gender": "male",
                "max_fee": 100000
            }
        }


class ConsultResponse(BaseModel):
    """Specialist's response to consultation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    consult_request_id: str
    specialist_id: str

    # Response
    response_text: str = Field(..., description="Specialist's detailed response")
    recommendations: list[str] = Field(default_factory=list, description="Action items")
    differential_diagnosis: list[str] = Field(default_factory=list)
    suggested_investigations: list[str] = Field(default_factory=list)
    treatment_plan: Optional[str] = None

    # Follow-up
    follow_up_needed: bool = False
    follow_up_timeline: Optional[str] = None
    additional_notes: Optional[str] = None

    # Attachments
    attachments: list[str] = Field(default_factory=list, description="URLs to response files")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_time_hours: float = Field(default=0.0, ge=0.0)

    # Quality
    was_helpful: Optional[bool] = None
    helpfulness_feedback: Optional[str] = None


class PeerReview(BaseModel):
    """Rating and feedback for consultation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    consult_request_id: str
    specialist_id: str
    reviewer_id: str = Field(..., description="Doctor who requested consult")

    # Ratings (1-5 stars)
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    expertise_rating: float = Field(..., ge=1.0, le=5.0)
    communication_rating: float = Field(..., ge=1.0, le=5.0)
    timeliness_rating: float = Field(..., ge=1.0, le=5.0)

    # Feedback
    positive_feedback: Optional[str] = Field(None, max_length=500)
    areas_for_improvement: Optional[str] = Field(None, max_length=500)
    would_consult_again: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_public: bool = Field(default=True, description="Show on specialist profile")


# ==================== Case Library Models ====================


class CaseDiscussion(BaseModel):
    """Anonymized interesting case for learning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    submitted_by: str = Field(..., description="Doctor who submitted case")
    consult_request_id: Optional[str] = Field(None, description="Link to original consult")

    # Case details
    title: str = Field(..., max_length=200)
    specialty: str
    case_category: str = Field(..., description="diagnosis, treatment, complication, etc.")
    case_presentation: str = Field(..., description="Full anonymized case")

    # Clinical content
    diagnosis: str
    learning_points: list[str] = Field(default_factory=list)
    discussion_points: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)

    # Media
    images: list[str] = Field(default_factory=list, description="Anonymized images")
    documents: list[str] = Field(default_factory=list)

    # Engagement
    visibility: CaseVisibility = Field(default=CaseVisibility.SPECIALTY)
    upvotes: int = Field(default=0, ge=0)
    view_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)
    is_featured: bool = False

    # CME
    cme_credits: float = Field(default=0.0, ge=0.0)
    difficulty_level: str = Field(default="intermediate")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Takotsubo Cardiomyopathy Mimicking STEMI",
                "specialty": "cardiology",
                "case_category": "diagnosis",
                "diagnosis": "Takotsubo cardiomyopathy",
                "learning_points": [
                    "ECG changes can mimic anterior STEMI",
                    "Echo shows apical ballooning",
                    "Coronaries are normal"
                ]
            }
        }


class CaseComment(BaseModel):
    """Comment on case discussion."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    commenter_id: str
    commenter_name: str
    commenter_specialty: str

    comment_text: str = Field(..., max_length=1000)
    parent_comment_id: Optional[str] = Field(None, description="For threaded discussions")

    upvotes: int = Field(default=0, ge=0)
    is_expert_opinion: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Messaging Models ====================


class ConsultMessage(BaseModel):
    """HIPAA-compliant message in consultation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    consult_request_id: str
    sender_id: str
    receiver_id: str

    # Message content
    message_type: MessageType = Field(default=MessageType.TEXT)
    message_text: Optional[str] = Field(None, max_length=5000)
    attachment_url: Optional[str] = Field(None, description="Encrypted file URL")
    attachment_name: Optional[str] = None

    # Voice/Video
    duration_seconds: Optional[int] = Field(None, ge=0)

    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None
    is_encrypted: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    thread_id: Optional[str] = Field(None, description="Message thread")


class MessageThread(BaseModel):
    """Message thread for consultation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    consult_request_id: str
    participants: list[str] = Field(..., description="User IDs in thread")

    last_message_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_preview: str = Field(default="")
    unread_count: dict[str, int] = Field(default_factory=dict, description="Per user")

    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Payment Models ====================


class ConsultPayment(BaseModel):
    """Payment for consultation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    consult_request_id: str
    payer_id: str = Field(..., description="Requesting doctor")
    payee_id: str = Field(..., description="Specialist")

    # Amount
    amount: int = Field(..., ge=0, description="Amount in paise")
    platform_fee: int = Field(default=0, ge=0, description="DocAssist fee")
    specialist_payout: int = Field(..., ge=0, description="Amount to specialist")
    currency: str = Field(default="INR")

    # Payment details
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None

    # Escrow
    held_in_escrow_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    auto_release_at: Optional[datetime] = None  # Auto-release after 7 days

    # Refund
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SpecialistPayout(BaseModel):
    """Payout to specialist."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialist_id: str
    period_start: datetime
    period_end: datetime

    # Amounts
    total_earnings: int = Field(default=0, ge=0)
    platform_fees: int = Field(default=0, ge=0)
    payout_amount: int = Field(..., ge=0)
    currency: str = Field(default="INR")

    # Consultations
    consult_payment_ids: list[str] = Field(default_factory=list)
    total_consultations: int = Field(default=0, ge=0)

    # Banking
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None

    # Status
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    transaction_id: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Verification Models ====================


class VerificationDocument(BaseModel):
    """Document submitted for verification."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialist_id: str
    document_type: str = Field(..., description="license, certificate, id_proof, etc.")
    document_url: str = Field(..., description="Encrypted document URL")
    document_number: Optional[str] = None

    # Verification
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = Field(None, description="Admin who verified")
    verification_notes: Optional[str] = None

    # Metadata
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class VerificationRequest(BaseModel):
    """Request for specialist verification."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    specialist_id: str
    requested_level: VerificationLevel

    # Documents
    document_ids: list[str] = Field(default_factory=list)

    # Hospital verification
    hospital_name: Optional[str] = None
    hospital_contact_email: Optional[EmailStr] = None
    hospital_contact_phone: Optional[str] = None

    # References
    reference_name_1: Optional[str] = None
    reference_email_1: Optional[EmailStr] = None
    reference_name_2: Optional[str] = None
    reference_email_2: Optional[EmailStr] = None

    # Status
    status: str = Field(default="pending", description="pending, approved, rejected")
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== Statistics Models ====================


class SpecialistStats(BaseModel):
    """Statistics for specialist dashboard."""

    specialist_id: str
    period_start: datetime
    period_end: datetime

    # Consultation metrics
    total_requests_received: int = 0
    requests_accepted: int = 0
    requests_declined: int = 0
    consultations_completed: int = 0

    # Performance metrics
    average_response_time_hours: float = 0.0
    average_rating: float = 0.0
    total_reviews: int = 0

    # Earnings
    total_earnings: int = 0
    pending_payments: int = 0

    # Engagement
    profile_views: int = 0
    case_contributions: int = 0

    # Computed metrics
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    computed_at: datetime = Field(default_factory=datetime.utcnow)


class PeerNetworkStats(BaseModel):
    """Platform-wide peer network statistics."""

    # Specialists
    total_specialists: int = 0
    verified_specialists: int = 0
    certified_specialists: int = 0
    expert_specialists: int = 0
    specialists_by_specialty: dict[str, int] = Field(default_factory=dict)

    # Consultations
    total_consultations: int = 0
    consultations_last_24h: int = 0
    consultations_last_7d: int = 0
    consultations_last_30d: int = 0
    average_response_time_hours: float = 0.0

    # Cases
    total_cases_shared: int = 0
    cases_by_specialty: dict[str, int] = Field(default_factory=dict)

    # Quality
    average_rating: float = 0.0
    total_reviews: int = 0

    # Popular specialties
    top_requested_specialties: list[dict[str, Any]] = Field(default_factory=list)

    computed_at: datetime = Field(default_factory=datetime.utcnow)
