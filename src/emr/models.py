"""EMR data models for comprehensive patient information."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """Patient gender."""

    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class Severity(str, Enum):
    """Allergy severity levels."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    FATAL = "fatal"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderType(str, Enum):
    """Type of clinical order."""

    MEDICATION = "medication"
    LAB = "lab"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    REFERRAL = "referral"


class Patient(BaseModel):
    """Patient demographics and identifiers."""

    id: int = Field(..., description="Internal patient ID")
    mrn: str = Field(..., description="Medical Record Number (UHID)")
    name: str = Field(..., description="Full name")
    age: int = Field(..., ge=0, le=150)
    gender: Gender
    date_of_birth: Optional[datetime] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "mrn": "MH2024-001234",
                "name": "Ramesh Kumar",
                "age": 65,
                "gender": "M",
                "phone": "+91-9876543210",
            }
        }


class Medication(BaseModel):
    """Current medication with dosing information."""

    id: Optional[int] = None
    patient_id: int
    drug_name: str = Field(..., description="Generic or brand name")
    dosage: str = Field(..., description="e.g., '500mg'")
    route: str = Field(default="PO", description="Route of administration")
    frequency: str = Field(..., description="e.g., 'BID', 'TID', 'QD'")
    duration: Optional[str] = Field(None, description="e.g., '7 days', '1 month'")
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    is_active: bool = True
    prescribing_doctor: Optional[str] = None
    indication: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "drug_name": "Metformin",
                "dosage": "1000mg",
                "route": "PO",
                "frequency": "BID",
                "instructions": "Take with meals",
                "indication": "Type 2 Diabetes",
            }
        }

    def to_display_string(self) -> str:
        """Format for display."""
        parts = [f"{self.drug_name} {self.dosage} {self.route} {self.frequency}"]
        if self.instructions:
            parts.append(f"({self.instructions})")
        return " ".join(parts)


class Allergy(BaseModel):
    """Patient allergy information."""

    id: Optional[int] = None
    patient_id: int
    allergen: str = Field(..., description="Drug name, food, or environmental")
    allergen_type: str = Field(
        default="drug", description="drug, food, environmental, other"
    )
    reaction: str = Field(..., description="Type of reaction experienced")
    severity: Severity
    onset_date: Optional[datetime] = None
    notes: Optional[str] = None
    verified: bool = Field(
        default=True, description="Whether allergy has been verified"
    )
    verified_date: Optional[datetime] = None
    verified_by: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "allergen": "Penicillin",
                "allergen_type": "drug",
                "reaction": "Anaphylaxis",
                "severity": "fatal",
                "verified": True,
            }
        }

    def to_display_string(self) -> str:
        """Format for display."""
        emoji = {"mild": "ℹ️", "moderate": "⚠️", "severe": "⛔", "fatal": "🚨"}
        return f"{emoji[self.severity]} {self.allergen} → {self.reaction}"


class VitalSigns(BaseModel):
    """Patient vital signs measurement."""

    id: Optional[int] = None
    patient_id: int
    measured_at: datetime = Field(default_factory=datetime.utcnow)
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    height_cm: Optional[float] = Field(None, ge=0, le=300)
    bmi: Optional[float] = Field(None, ge=0, le=100)
    temperature_c: Optional[float] = Field(None, ge=30, le=45)
    blood_pressure_systolic: Optional[int] = Field(None, ge=0, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=0, le=200)
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    respiratory_rate: Optional[int] = Field(None, ge=0, le=60)
    spo2: Optional[int] = Field(None, ge=0, le=100, description="Oxygen saturation %")
    recorded_by: Optional[str] = None
    notes: Optional[str] = None

    @property
    def blood_pressure(self) -> Optional[str]:
        """Get blood pressure as string."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

    def calculate_bmi(self) -> Optional[float]:
        """Calculate BMI from height and weight."""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m**2), 1)
        return None


class LabResult(BaseModel):
    """Laboratory test result."""

    id: Optional[int] = None
    patient_id: int
    test_name: str = Field(..., description="Name of the test")
    test_code: Optional[str] = Field(None, description="LOINC or local code")
    result: str = Field(..., description="Test result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal range")
    is_abnormal: bool = Field(default=False)
    abnormal_flag: Optional[str] = Field(
        None, description="H (high), L (low), HH (critical high), LL (critical low)"
    )
    test_date: datetime = Field(default_factory=datetime.utcnow)
    result_date: Optional[datetime] = None
    ordering_doctor: Optional[str] = None
    lab_name: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "test_name": "Creatinine",
                "result": "1.8",
                "unit": "mg/dL",
                "reference_range": "0.7-1.3",
                "is_abnormal": True,
                "abnormal_flag": "H",
            }
        }

    def to_display_string(self) -> str:
        """Format for display."""
        parts = [self.test_name, ":", self.result]
        if self.unit:
            parts.append(self.unit)
        if self.reference_range:
            parts.append(f"(Ref: {self.reference_range})")
        if self.is_abnormal:
            parts.append(f"[{self.abnormal_flag or 'ABNORMAL'}]")
        return " ".join(parts)


class Diagnosis(BaseModel):
    """Patient diagnosis with ICD coding."""

    id: Optional[int] = None
    patient_id: int
    diagnosis_code: Optional[str] = Field(None, description="ICD-10 code")
    diagnosis_name: str = Field(..., description="Diagnosis description")
    diagnosis_type: str = Field(
        default="primary", description="primary, secondary, chronic, rule_out"
    )
    onset_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    is_active: bool = True
    is_chronic: bool = False
    severity: Optional[str] = None
    notes: Optional[str] = None
    diagnosed_by: Optional[str] = None
    diagnosed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis_code": "E11.9",
                "diagnosis_name": "Type 2 Diabetes Mellitus",
                "diagnosis_type": "chronic",
                "is_chronic": True,
                "is_active": True,
            }
        }


class Encounter(BaseModel):
    """Clinical encounter/visit."""

    id: Optional[int] = None
    patient_id: int
    encounter_date: datetime = Field(default_factory=datetime.utcnow)
    encounter_type: str = Field(
        default="outpatient", description="outpatient, inpatient, emergency, telehealth"
    )
    chief_complaint: Optional[str] = None
    provider_name: Optional[str] = None
    department: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    follow_up: Optional[str] = None
    duration_minutes: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "encounter_type": "outpatient",
                "chief_complaint": "Follow-up for diabetes management",
                "provider_name": "Dr. Sharma",
                "diagnosis": "Type 2 DM, controlled",
            }
        }


class ClinicalNote(BaseModel):
    """Clinical documentation note."""

    id: Optional[int] = None
    patient_id: int
    encounter_id: Optional[int] = None
    note_type: str = Field(
        default="progress", description="progress, soap, admission, discharge, procedure"
    )
    note_date: datetime = Field(default_factory=datetime.utcnow)
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    full_note: Optional[str] = None
    author: Optional[str] = None
    signed: bool = False
    signed_at: Optional[datetime] = None

    def to_soap_string(self) -> str:
        """Format as SOAP note."""
        parts = []
        if self.subjective:
            parts.append(f"S: {self.subjective}")
        if self.objective:
            parts.append(f"O: {self.objective}")
        if self.assessment:
            parts.append(f"A: {self.assessment}")
        if self.plan:
            parts.append(f"P: {self.plan}")
        return "\n\n".join(parts) if parts else self.full_note or ""


class Order(BaseModel):
    """Clinical order (medication, lab, imaging, etc.)."""

    id: Optional[int] = None
    patient_id: int
    encounter_id: Optional[int] = None
    order_type: OrderType
    order_name: str = Field(..., description="Name of medication, test, procedure")
    order_details: dict[str, Any] = Field(
        default_factory=dict, description="Type-specific details"
    )
    status: OrderStatus = OrderStatus.PENDING
    priority: str = Field(default="routine", description="routine, urgent, stat")
    ordered_by: Optional[str] = None
    ordered_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "order_type": "lab",
                "order_name": "Complete Blood Count",
                "order_details": {"fasting": True, "priority": "routine"},
                "status": "pending",
                "ordered_by": "Dr. Sharma",
            }
        }


class PatientSummary(BaseModel):
    """Comprehensive patient summary for RAG context."""

    patient: Patient
    active_diagnoses: list[Diagnosis] = Field(default_factory=list)
    current_medications: list[Medication] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    recent_vitals: Optional[VitalSigns] = None
    recent_labs: list[LabResult] = Field(default_factory=list)
    recent_encounters: list[Encounter] = Field(default_factory=list)
    pending_orders: list[Order] = Field(default_factory=list)

    def to_context_string(self) -> str:
        """Convert to string for RAG context injection."""
        lines = [
            "=== PATIENT CONTEXT ===",
            f"{self.patient.name}, {self.patient.age}y {self.patient.gender.value}",
            f"MRN: {self.patient.mrn}",
            "",
        ]

        # Active diagnoses
        if self.active_diagnoses:
            lines.append("Active Diagnoses:")
            for dx in self.active_diagnoses:
                status = "chronic" if dx.is_chronic else "active"
                lines.append(f"  • {dx.diagnosis_name} ({status})")
            lines.append("")

        # Current medications
        if self.current_medications:
            lines.append("Current Medications:")
            for med in self.current_medications:
                lines.append(f"  • {med.to_display_string()}")
            lines.append("")

        # Allergies
        if self.allergies:
            lines.append("ALLERGIES:")
            for allergy in self.allergies:
                lines.append(f"  {allergy.to_display_string()}")
            lines.append("")

        # Recent vitals
        if self.recent_vitals:
            lines.append("Recent Vitals:")
            v = self.recent_vitals
            if v.weight_kg:
                lines.append(f"  • Weight: {v.weight_kg}kg")
            if v.bmi:
                lines.append(f"  • BMI: {v.bmi}")
            if v.blood_pressure:
                lines.append(f"  • BP: {v.blood_pressure} mmHg")
            if v.heart_rate:
                lines.append(f"  • HR: {v.heart_rate} bpm")
            if v.spo2:
                lines.append(f"  • SpO2: {v.spo2}%")
            lines.append("")

        # Recent labs
        if self.recent_labs:
            lines.append("Recent Labs:")
            for lab in self.recent_labs[:10]:  # Top 10 most recent
                lines.append(f"  • {lab.to_display_string()}")
            lines.append("")

        return "\n".join(lines)

    def get_risk_factors(self) -> list[str]:
        """Extract risk factors from patient data."""
        risks = []

        # Age-based risks
        if self.patient.age >= 65:
            risks.append("Elderly patient (≥65y)")

        # Diagnosis-based risks
        chronic_conditions = {
            "diabetes": ["diabetes", "dm", "diabetic"],
            "ckd": ["chronic kidney", "renal", "ckd"],
            "heart_failure": ["heart failure", "hf", "chf"],
            "copd": ["copd", "emphysema", "chronic bronchitis"],
        }

        for risk_name, keywords in chronic_conditions.items():
            for dx in self.active_diagnoses:
                if any(kw in dx.diagnosis_name.lower() for kw in keywords):
                    risks.append(risk_name.upper().replace("_", " "))
                    break

        # Vital signs based risks
        if self.recent_vitals:
            v = self.recent_vitals
            if v.bmi and v.bmi >= 30:
                risks.append("Obesity (BMI ≥30)")
            if v.blood_pressure_systolic and v.blood_pressure_systolic >= 140:
                risks.append("Hypertension")

        # Lab-based risks (renal function)
        for lab in self.recent_labs:
            if "creatinine" in lab.test_name.lower():
                try:
                    creat = float(lab.result)
                    if creat > 1.5:
                        risks.append("Impaired renal function")
                except ValueError:
                    pass

        return list(set(risks))  # Remove duplicates
