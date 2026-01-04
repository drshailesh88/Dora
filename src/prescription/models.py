"""
Prescription data models for Dora.

Comprehensive prescription management including medications, dosages,
digital signatures, and regulatory compliance.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class RouteOfAdministration(str, Enum):
    """Routes of drug administration."""
    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SC = "subcutaneous"
    TOPICAL = "topical"
    RECTAL = "rectal"
    VAGINAL = "vaginal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    NASAL = "nasal"
    INHALED = "inhaled"
    SUBLINGUAL = "sublingual"
    TRANSDERMAL = "transdermal"
    OTHER = "other"


class Frequency(str, Enum):
    """Medication frequency codes."""
    OD = "once_daily"           # 0-0-1 or 1-0-0
    BD = "twice_daily"          # 1-0-1
    TDS = "three_times_daily"   # 1-1-1
    QID = "four_times_daily"    # 1-1-1-1
    QHS = "at_bedtime"          # 0-0-0-1
    QOD = "every_other_day"     # Alternate days
    PRN = "as_needed"           # When required
    STAT = "immediately"        # One-time urgent
    WEEKLY = "once_weekly"      # Weekly
    CUSTOM = "custom"           # Custom schedule


class DosageForm(str, Enum):
    """Pharmaceutical dosage forms."""
    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    SUSPENSION = "suspension"
    SOLUTION = "solution"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"
    GEL = "gel"
    DROPS = "drops"
    SPRAY = "spray"
    PATCH = "patch"
    INHALER = "inhaler"
    POWDER = "powder"
    SUPPOSITORY = "suppository"
    OTHER = "other"


class DrugSchedule(str, Enum):
    """Indian Drug Schedule classification."""
    H = "schedule_h"        # Prescription only
    H1 = "schedule_h1"      # Restricted prescription (narcotics, etc.)
    X = "schedule_x"        # Controlled substances
    G = "schedule_g"        # Caution required
    OTC = "over_the_counter"  # Non-prescription


class PrescriptionStatus(str, Enum):
    """Prescription lifecycle status."""
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    DISPENSED = "dispensed"
    PARTIALLY_DISPENSED = "partially_dispensed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Dosage(BaseModel):
    """Detailed dosage information for a medication."""

    dose: str = Field(..., description="Dose amount (e.g., '500mg', '5ml', '2 puffs')")
    frequency: Frequency = Field(..., description="How often to take")
    frequency_detail: Optional[str] = Field(None, description="Custom frequency like '1-0-1-0'")
    duration_days: int = Field(..., gt=0, description="Duration in days")
    route: RouteOfAdministration = Field(default=RouteOfAdministration.ORAL)

    # Timing
    timing: Optional[str] = Field(None, description="e.g., 'after food', 'before breakfast'")
    specific_times: Optional[List[str]] = Field(None, description="e.g., ['08:00', '20:00']")

    # Special instructions
    take_with_food: Optional[bool] = None
    take_on_empty_stomach: Optional[bool] = None
    avoid_alcohol: Optional[bool] = None

    # Tapering/Variable dosing
    is_tapering: bool = False
    tapering_schedule: Optional[str] = Field(None, description="e.g., '10mg x 7d, 5mg x 7d, stop'")

    # PRN specific
    prn_indication: Optional[str] = Field(None, description="When to take PRN (e.g., 'for pain')")
    max_dose_per_day: Optional[str] = Field(None, description="Max daily dose for PRN")

    class Config:
        use_enum_values = True


class Refill(BaseModel):
    """Prescription refill information."""

    allowed: bool = Field(default=False, description="Are refills allowed?")
    number_of_refills: int = Field(default=0, ge=0, description="Number of refills authorized")
    refills_used: int = Field(default=0, ge=0, description="Number of refills dispensed")
    valid_until: Optional[date] = Field(None, description="Refills valid until this date")

    @validator('refills_used')
    def validate_refills_used(cls, v, values):
        """Ensure refills_used doesn't exceed number_of_refills."""
        if 'number_of_refills' in values and v > values['number_of_refills']:
            raise ValueError("Refills used cannot exceed authorized refills")
        return v


class Substitution(BaseModel):
    """Generic substitution information."""

    allowed: bool = Field(default=True, description="Is generic substitution allowed?")
    reason_if_not_allowed: Optional[str] = Field(None, description="Why substitution not allowed")
    generic_equivalent: Optional[str] = Field(None, description="Recommended generic name")
    brand_medically_necessary: bool = Field(default=False)


class PrescriptionItem(BaseModel):
    """Individual medication item in a prescription."""

    # Drug identification
    drug_name: str = Field(..., description="Generic or brand name")
    generic_name: Optional[str] = Field(None, description="Generic name if brand prescribed")
    strength: str = Field(..., description="e.g., '500mg', '5mg/ml'")
    dosage_form: DosageForm = Field(...)

    # Dosing
    dosage: Dosage = Field(...)

    # Quantity
    quantity: int = Field(..., gt=0, description="Number of units to dispense")
    quantity_unit: str = Field(default="units", description="e.g., 'tablets', 'ml', 'vials'")

    # Classification
    schedule: DrugSchedule = Field(default=DrugSchedule.H)

    # Instructions
    instructions: Optional[str] = Field(None, description="Patient instructions in simple language")
    pharmacy_notes: Optional[str] = Field(None, description="Notes for pharmacist")

    # Refills and substitution
    refill: Refill = Field(default_factory=Refill)
    substitution: Substitution = Field(default_factory=Substitution)

    # Metadata
    item_sequence: int = Field(..., ge=1, description="Order in prescription (1-indexed)")
    indication: Optional[str] = Field(None, description="Why prescribed (optional)")

    # Extraction metadata (for AI-extracted prescriptions)
    extracted_from_text: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    needs_confirmation: bool = Field(default=True, description="Requires physician confirmation")

    class Config:
        use_enum_values = True


class PrescriptionTemplate(BaseModel):
    """Saved prescription template for common conditions."""

    id: Optional[str] = None
    name: str = Field(..., description="Template name (e.g., 'Type 2 DM - Initial')")
    description: Optional[str] = None
    specialty: Optional[str] = Field(None, description="Medical specialty")
    condition: Optional[str] = Field(None, description="Condition/diagnosis")

    items: List[PrescriptionItem] = Field(..., min_items=1)
    advice: Optional[str] = None

    # Template metadata
    created_by: str = Field(..., description="Doctor ID who created template")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = Field(default=0, ge=0)
    is_public: bool = Field(default=False, description="Share with other doctors?")
    tags: List[str] = Field(default_factory=list)


class DoctorInfo(BaseModel):
    """Prescribing doctor information."""

    doctor_id: str
    name: str
    qualifications: str = Field(..., description="e.g., 'MD, MBBS, FRCP'")
    specialization: Optional[str] = None
    registration_number: str = Field(..., description="Medical council registration")
    registration_council: str = Field(default="Medical Council of India")

    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None

    # Clinic/Hospital
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None


class PatientInfo(BaseModel):
    """Patient demographic information for prescription."""

    patient_id: str
    mrn: Optional[str] = Field(None, description="Medical Record Number")
    name: str
    age: int = Field(..., gt=0)
    age_unit: str = Field(default="years")
    gender: str = Field(..., description="M/F/O")

    # Optional demographics
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)

    # Contact
    phone: Optional[str] = None

    # Allergies (critical)
    known_allergies: List[str] = Field(default_factory=list)

    # Relevant medical conditions
    active_conditions: List[str] = Field(default_factory=list)


class DigitalSignature(BaseModel):
    """Digital signature for e-prescription."""

    signature_id: str = Field(..., description="Unique signature identifier")
    doctor_id: str
    signature_data: str = Field(..., description="Base64 encoded signature or hash")
    signature_method: str = Field(default="digital_certificate", description="Signing method")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Verification
    certificate_id: Optional[str] = Field(None, description="Digital certificate ID")
    verified: bool = Field(default=False)
    verification_timestamp: Optional[datetime] = None

    # Audit
    ip_address: Optional[str] = None
    device_info: Optional[str] = None


class Prescription(BaseModel):
    """Complete prescription document."""

    # Identifiers
    prescription_id: str = Field(..., description="Unique prescription ID")
    encounter_id: Optional[str] = Field(None, description="Associated EMR encounter")

    # Parties
    patient: PatientInfo
    doctor: DoctorInfo

    # Prescription details
    items: List[PrescriptionItem] = Field(..., min_items=1)

    # Date information
    date_prescribed: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[date] = Field(None, description="Prescription validity")

    # Clinical information
    diagnosis: Optional[str] = None
    advice: Optional[str] = Field(None, description="Doctor's advice to patient")
    follow_up_date: Optional[date] = None

    # Warnings
    warnings: List[str] = Field(default_factory=list, description="Drug interactions, allergies, etc.")
    precautions: List[str] = Field(default_factory=list)

    # Status and workflow
    status: PrescriptionStatus = Field(default=PrescriptionStatus.DRAFT)

    # Digital signature
    signature: Optional[DigitalSignature] = None

    # Integration
    sent_to_pharmacy: bool = Field(default=False)
    pharmacy_id: Optional[str] = None
    sent_to_emr: bool = Field(default=False)
    emr_id: Optional[str] = None

    # Source tracking (for AI-generated prescriptions)
    source: str = Field(default="manual", description="manual/dora_ai/template/emr")
    source_reference: Optional[str] = Field(None, description="Dora answer ID, template ID, etc.")
    ai_confidence: Optional[float] = Field(None, ge=0, le=1)
    physician_confirmed: bool = Field(default=False, description="Doctor confirmed AI suggestions")

    # Audit trail
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created")

    # Metadata
    notes: Optional[str] = Field(None, description="Internal notes (not on printed Rx)")
    language: str = Field(default="en", description="Prescription language")

    class Config:
        use_enum_values = True

    @validator('valid_until', always=True)
    def set_valid_until(cls, v, values):
        """Set default validity to 30 days if not specified."""
        if v is None and 'date_prescribed' in values:
            from datetime import timedelta
            prescribed_date = values['date_prescribed']
            return (prescribed_date + timedelta(days=30)).date()
        return v


class EPrescription(Prescription):
    """
    Electronic prescription with enhanced digital features.

    Extends Prescription with regulatory compliance for e-prescriptions.
    """

    # Digital identifiers
    e_prescription_id: str = Field(..., description="Government-recognized e-Rx ID")
    qr_code: Optional[str] = Field(None, description="QR code data for verification")

    # Regulatory compliance
    regulatory_compliant: bool = Field(default=True)
    compliance_framework: str = Field(default="India_Digital_Health_Authority")

    # Digital distribution
    sent_via_email: bool = Field(default=False)
    sent_via_sms: bool = Field(default=False)
    sent_via_whatsapp: bool = Field(default=False)
    patient_portal_accessible: bool = Field(default=False)

    # Blockchain/audit (for future)
    blockchain_hash: Optional[str] = None
    immutable: bool = Field(default=False, description="Locked from further edits")

    # Digital signature is REQUIRED for e-prescription
    signature: DigitalSignature = Field(..., description="Digital signature required")

    @validator('signature')
    def validate_signature(cls, v):
        """Ensure signature is verified for e-prescription."""
        if v and not v.verified:
            raise ValueError("E-prescription requires verified digital signature")
        return v


class PrescriptionValidationResult(BaseModel):
    """Result of prescription validation."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list, description="Blocking errors")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    interactions: List[Dict[str, Any]] = Field(default_factory=list)
    contraindications: List[Dict[str, Any]] = Field(default_factory=list)
    dosing_issues: List[Dict[str, Any]] = Field(default_factory=list)

    # Specific checks
    allergy_conflicts: List[str] = Field(default_factory=list)
    duplicate_therapies: List[str] = Field(default_factory=list)
    pregnancy_safety: Optional[str] = None
    lactation_safety: Optional[str] = None
    renal_adjustment_needed: bool = False
    hepatic_adjustment_needed: bool = False

    # Overall risk score
    risk_score: float = Field(default=0.0, ge=0, le=1, description="0=safe, 1=dangerous")
    requires_specialist_review: bool = Field(default=False)

    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validation_engine_version: str = Field(default="1.0.0")


class DrugAlternative(BaseModel):
    """Alternative medication suggestion."""

    original_drug: str
    alternative_drug: str
    alternative_generic_name: str
    strength: str

    # Comparison
    therapeutic_equivalence: str = Field(..., description="identical/similar/different")
    reason_for_suggestion: str = Field(..., description="cheaper/better_safety/formulary/availability")

    # Cost
    original_price: Optional[Decimal] = None
    alternative_price: Optional[Decimal] = None
    savings_per_month: Optional[Decimal] = None

    # Availability
    available_in_formulary: Optional[bool] = None
    availability_status: Optional[str] = None

    # Safety
    safety_comparison: Optional[str] = None

    confidence: float = Field(..., ge=0, le=1, description="Confidence in suggestion")


# Export all models
__all__ = [
    'RouteOfAdministration',
    'Frequency',
    'DosageForm',
    'DrugSchedule',
    'PrescriptionStatus',
    'Dosage',
    'Refill',
    'Substitution',
    'PrescriptionItem',
    'PrescriptionTemplate',
    'DoctorInfo',
    'PatientInfo',
    'DigitalSignature',
    'Prescription',
    'EPrescription',
    'PrescriptionValidationResult',
    'DrugAlternative',
]
