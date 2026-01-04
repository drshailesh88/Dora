"""Clinical documentation models for Dora.

All documentation types following medical standards and formats.
Draft-mode by default - requires physician review before persistence.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Status of a clinical document."""

    DRAFT = "draft"
    REVIEWED = "reviewed"
    SIGNED = "signed"
    AMENDED = "amended"
    DELETED = "deleted"


class UrgencyLevel(str, Enum):
    """Urgency level for referrals and consultations."""

    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class DocumentType(str, Enum):
    """Types of clinical documents."""

    SOAP = "soap"
    PROGRESS = "progress"
    DISCHARGE = "discharge"
    REFERRAL = "referral"
    CERTIFICATE = "certificate"
    OPERATIVE = "operative"
    CONSULT = "consult"
    DEATH = "death"


class Provider(BaseModel):
    """Healthcare provider information."""

    name: str
    qualification: Optional[str] = None
    registration_number: Optional[str] = None
    specialty: Optional[str] = None
    contact: Optional[str] = None
    signature: Optional[str] = None  # Digital signature or path to signature image


class Patient(BaseModel):
    """Patient demographic information."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    mrn: Optional[str] = Field(None, description="Medical Record Number")
    name: str
    age: int
    gender: str
    contact: Optional[str] = None
    address: Optional[str] = None


class Vitals(BaseModel):
    """Patient vital signs."""

    bp_systolic: Optional[int] = Field(None, description="Blood pressure systolic (mmHg)")
    bp_diastolic: Optional[int] = Field(None, description="Blood pressure diastolic (mmHg)")
    heart_rate: Optional[int] = Field(None, description="Heart rate (bpm)")
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate (/min)")
    temperature: Optional[float] = Field(None, description="Temperature (°F or °C)")
    spo2: Optional[int] = Field(None, description="Oxygen saturation (%)")
    weight: Optional[float] = Field(None, description="Weight (kg)")
    height: Optional[float] = Field(None, description="Height (cm)")
    bmi: Optional[float] = Field(None, description="BMI")

    def __str__(self) -> str:
        """Format vitals for display."""
        parts = []
        if self.bp_systolic and self.bp_diastolic:
            parts.append(f"BP {self.bp_systolic}/{self.bp_diastolic}")
        if self.heart_rate:
            parts.append(f"HR {self.heart_rate}")
        if self.respiratory_rate:
            parts.append(f"RR {self.respiratory_rate}")
        if self.spo2:
            parts.append(f"SpO2 {self.spo2}%")
        if self.temperature:
            parts.append(f"Temp {self.temperature}°F")
        return ", ".join(parts) if parts else "Not recorded"


class Diagnosis(BaseModel):
    """A clinical diagnosis."""

    description: str
    icd10_code: Optional[str] = None
    is_primary: bool = False
    status: str = "active"  # active, resolved, chronic
    onset_date: Optional[datetime] = None


class Medication(BaseModel):
    """Medication prescription."""

    name: str
    dosage: str
    route: str = "PO"  # PO, IV, IM, SC, etc.
    frequency: str
    duration: Optional[str] = None
    instructions: Optional[str] = None
    indication: Optional[str] = None


class Investigation(BaseModel):
    """Lab or imaging investigation."""

    name: str
    result: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    flag: Optional[str] = None  # H (high), L (low), N (normal)
    date: Optional[datetime] = None


class SOAPNote(BaseModel):
    """SOAP (Subjective, Objective, Assessment, Plan) Clinical Note."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    provider: Provider
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    # Subjective
    chief_complaint: str
    history_present_illness: str
    past_medical_history: Optional[str] = None
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    social_history: Optional[str] = None
    family_history: Optional[str] = None
    review_of_systems: Optional[str] = None

    # Objective
    vitals: Optional[Vitals] = None
    general_exam: Optional[str] = None
    system_exams: dict[str, str] = Field(default_factory=dict)  # e.g., {"cardiovascular": "S1S2 normal"}
    investigations: list[Investigation] = Field(default_factory=list)

    # Assessment
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    differential_diagnoses: list[str] = Field(default_factory=list)

    # Plan
    plan_medications: list[Medication] = Field(default_factory=list)
    plan_investigations: list[str] = Field(default_factory=list)
    plan_procedures: list[str] = Field(default_factory=list)
    plan_referrals: list[str] = Field(default_factory=list)
    plan_followup: Optional[str] = None
    plan_patient_education: Optional[str] = None

    # Metadata
    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProgressNote(BaseModel):
    """Progress note for follow-up visits."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    provider: Provider
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    interval_history: str  # What happened since last visit
    vitals: Optional[Vitals] = None
    exam_findings: Optional[str] = None
    investigations: list[Investigation] = Field(default_factory=list)

    assessment: str
    diagnoses: list[Diagnosis] = Field(default_factory=list)

    plan: str
    medications_continued: list[Medication] = Field(default_factory=list)
    medications_changed: list[Medication] = Field(default_factory=list)
    followup: Optional[str] = None

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class DischargeSummary(BaseModel):
    """Hospital discharge summary."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    provider: Provider
    status: DocumentStatus = DocumentStatus.DRAFT

    # Admission details
    admission_date: datetime
    discharge_date: datetime
    length_of_stay: Optional[int] = None  # Days
    admission_department: str
    discharge_department: str

    # Clinical information
    chief_complaint: str
    admitting_diagnosis: str
    final_diagnosis: list[Diagnosis] = Field(default_factory=list)

    hospital_course: str  # Narrative of what happened during stay
    procedures_performed: list[str] = Field(default_factory=list)
    consultations: list[str] = Field(default_factory=list)

    # Discharge details
    condition_at_discharge: str  # Improved, stable, critical, expired
    discharge_medications: list[Medication] = Field(default_factory=list)
    discharge_instructions: str
    diet_restrictions: Optional[str] = None
    activity_restrictions: Optional[str] = None

    # Follow-up
    followup_instructions: str
    followup_date: Optional[datetime] = None
    followup_provider: Optional[str] = None
    warning_signs: list[str] = Field(default_factory=list)

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ReferralLetter(BaseModel):
    """Referral letter to specialist."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    referring_provider: Provider
    specialist_provider: Optional[Provider] = None
    specialty: str
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    reason_for_referral: str
    clinical_summary: str

    diagnoses: list[Diagnosis] = Field(default_factory=list)
    current_medications: list[Medication] = Field(default_factory=list)
    relevant_investigations: list[Investigation] = Field(default_factory=list)

    specific_questions: list[str] = Field(default_factory=list)
    additional_notes: Optional[str] = None

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class CertificateType(str, Enum):
    """Types of medical certificates."""

    FITNESS = "fitness"
    SICK_LEAVE = "sick_leave"
    FITNESS_TRAVEL = "fitness_travel"
    FITNESS_SURGERY = "fitness_surgery"
    FITNESS_SPORTS = "fitness_sports"
    WORK_ABSENCE = "work_absence"
    SCHOOL_ABSENCE = "school_absence"
    DISABILITY = "disability"


class MedicalCertificate(BaseModel):
    """Medical certificate."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    provider: Provider
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    certificate_type: CertificateType
    purpose: str  # What the certificate is for

    # For sick leave
    diagnosis: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    days_of_rest: Optional[int] = None

    # For fitness
    fitness_statement: Optional[str] = None  # "Fit for duty", "Fit to travel", etc.
    restrictions: Optional[str] = None

    additional_notes: Optional[str] = None

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class OperativeNote(BaseModel):
    """Operative/surgical note."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    surgeon: Provider
    assistants: list[Provider] = Field(default_factory=list)
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    # Pre-operative
    preop_diagnosis: str
    indication_for_surgery: str

    # Intra-operative
    procedure_performed: str
    procedure_type: str  # Elective, emergency
    anesthesia_type: str  # General, spinal, local
    anesthesiologist: Optional[str] = None

    operative_findings: str
    technique: str  # Detailed description of surgical technique
    estimated_blood_loss: Optional[str] = None
    specimens_sent: list[str] = Field(default_factory=list)

    complications: Optional[str] = None
    implants_used: list[str] = Field(default_factory=list)

    # Post-operative
    postop_diagnosis: str
    postop_condition: str
    postop_destination: str  # Recovery room, ICU, ward
    postop_instructions: str

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ConsultNote(BaseModel):
    """Consultation note from specialist."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    consultant: Provider
    requesting_provider: Optional[Provider] = None
    date: datetime = Field(default_factory=datetime.now)
    status: DocumentStatus = DocumentStatus.DRAFT

    reason_for_consult: str
    history: str

    vitals: Optional[Vitals] = None
    examination: str

    investigations_reviewed: list[Investigation] = Field(default_factory=list)
    investigations_ordered: list[str] = Field(default_factory=list)

    impression: str
    diagnoses: list[Diagnosis] = Field(default_factory=list)

    recommendations: str
    medications_recommended: list[Medication] = Field(default_factory=list)
    followup_plan: Optional[str] = None

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class DeathSummary(BaseModel):
    """Death summary (sad but necessary)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    patient: Patient
    provider: Provider
    status: DocumentStatus = DocumentStatus.DRAFT

    date_of_death: datetime
    time_of_death: str
    place_of_death: str  # Ward, ICU, Emergency, etc.

    admission_date: datetime
    admission_diagnosis: str

    cause_of_death: str
    immediate_cause: str
    underlying_cause: str
    contributing_factors: list[str] = Field(default_factory=list)

    hospital_course: str
    resuscitation_attempted: bool = False
    resuscitation_details: Optional[str] = None

    family_notified: bool = False
    family_notified_by: Optional[str] = None
    family_notified_at: Optional[datetime] = None

    autopsy_requested: bool = False
    body_handed_over_to: Optional[str] = None
    body_handed_over_at: Optional[datetime] = None

    signed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class DocumentMetadata(BaseModel):
    """Metadata for any clinical document."""

    document_id: str
    document_type: DocumentType
    patient_id: str
    provider_id: str
    created_at: datetime
    updated_at: datetime
    signed_at: Optional[datetime] = None
    status: DocumentStatus
    version: int = 1
    parent_document_id: Optional[str] = None  # For amendments
    emr_synced: bool = False
    emr_sync_at: Optional[datetime] = None
