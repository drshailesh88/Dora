"""Data models for doctor personalization."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PracticeSetting(str, Enum):
    """Types of practice settings."""

    HOSPITAL = "hospital"
    CLINIC = "clinic"
    ACADEMIC = "academic"
    TELEMEDICINE = "telemedicine"
    GOVERNMENT = "government"
    PRIVATE = "private"


class MedicalSpecialty(str, Enum):
    """Supported medical specialties."""

    INTERNAL_MEDICINE = "internal_medicine"
    CARDIOLOGY = "cardiology"
    PULMONOLOGY = "pulmonology"
    NEPHROLOGY = "nephrology"
    GASTROENTEROLOGY = "gastroenterology"
    ENDOCRINOLOGY = "endocrinology"
    RHEUMATOLOGY = "rheumatology"
    NEUROLOGY = "neurology"
    PSYCHIATRY = "psychiatry"
    PEDIATRICS = "pediatrics"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    SURGERY_GENERAL = "surgery_general"
    CARDIOTHORACIC_SURGERY = "cardiothoracic_surgery"
    NEUROSURGERY = "neurosurgery"
    ORTHOPEDICS = "orthopedics"
    DERMATOLOGY = "dermatology"
    OPHTHALMOLOGY = "ophthalmology"
    ENT = "ent"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    CRITICAL_CARE = "critical_care"
    FAMILY_MEDICINE = "family_medicine"
    ONCOLOGY = "oncology"
    HEMATOLOGY = "hematology"
    INFECTIOUS_DISEASE = "infectious_disease"
    UROLOGY = "urology"
    ANESTHESIOLOGY = "anesthesiology"


class QueryCategory(str, Enum):
    """Categories of medical queries."""

    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    DRUG_INFORMATION = "drug_information"
    DIFFERENTIAL = "differential"
    INVESTIGATION = "investigation"
    PROGNOSIS = "prognosis"
    PATHOPHYSIOLOGY = "pathophysiology"
    CLINICAL_GUIDELINE = "clinical_guideline"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    CHRONIC_MANAGEMENT = "chronic_management"


class SpecialtyConfidence(BaseModel):
    """Confidence score for a detected specialty."""

    specialty: MedicalSpecialty
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, description="Number of queries supporting this")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DoctorProfile(BaseModel):
    """Complete doctor profile for personalization."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID from auth system")

    # Specialty information
    primary_specialty: Optional[MedicalSpecialty] = None
    subspecialties: list[MedicalSpecialty] = Field(default_factory=list)
    detected_specialties: list[SpecialtyConfidence] = Field(default_factory=list)

    # Practice details
    years_of_experience: Optional[int] = None
    practice_settings: list[PracticeSetting] = Field(default_factory=list)

    # Common clinical patterns
    common_conditions: list[str] = Field(default_factory=list, description="ICD codes or condition names")
    preferred_drug_classes: list[str] = Field(default_factory=list)
    favorite_resources: list[str] = Field(default_factory=list, description="Preferred textbooks/guidelines")

    # Query preferences
    preferred_detail_level: str = Field(default="medium", description="brief/medium/detailed")
    preferred_citation_style: str = Field(default="inline", description="inline/numbered/endnotes")
    show_pediatric_dosing: bool = Field(default=False)
    show_drug_interactions: bool = Field(default=True)

    # Metadata
    total_queries: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_query_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def get_top_specialty(self) -> Optional[MedicalSpecialty]:
        """Get the most confident specialty."""
        if self.primary_specialty:
            return self.primary_specialty
        if self.detected_specialties:
            top = max(self.detected_specialties, key=lambda x: x.confidence)
            return top.specialty if top.confidence > 0.5 else None
        return None

    def get_all_specialties(self) -> list[MedicalSpecialty]:
        """Get all relevant specialties (primary + sub)."""
        specialties = []
        if self.primary_specialty:
            specialties.append(self.primary_specialty)
        specialties.extend(self.subspecialties)
        return specialties


class QueryPattern(BaseModel):
    """Aggregated patterns from query history."""

    user_id: str

    # Category patterns
    category_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="QueryCategory -> count"
    )

    # Time patterns
    hour_distribution: dict[int, int] = Field(
        default_factory=dict,
        description="Hour of day -> count"
    )
    weekday_distribution: dict[int, int] = Field(
        default_factory=dict,
        description="Day of week -> count"
    )

    # Complexity patterns
    avg_query_length: float = 0.0
    uses_patient_context: int = 0
    total_queries: int = 0

    # Topic patterns
    common_keywords: dict[str, int] = Field(default_factory=dict)
    common_drugs: dict[str, int] = Field(default_factory=dict)
    common_conditions: dict[str, int] = Field(default_factory=dict)

    # Feedback patterns
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_peak_hours(self, top_n: int = 3) -> list[int]:
        """Get top N hours when user queries most."""
        sorted_hours = sorted(
            self.hour_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [hour for hour, _ in sorted_hours[:top_n]]

    def get_top_categories(self, top_n: int = 5) -> list[str]:
        """Get top N query categories."""
        sorted_cats = sorted(
            self.category_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [cat for cat, _ in sorted_cats[:top_n]]


class QueryHistory(BaseModel):
    """Individual query record for learning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    query: str
    category: Optional[QueryCategory] = None
    detected_specialty: Optional[MedicalSpecialty] = None
    specialty_confidence: float = 0.0

    # Extracted entities
    mentioned_drugs: list[str] = Field(default_factory=list)
    mentioned_conditions: list[str] = Field(default_factory=list)
    mentioned_procedures: list[str] = Field(default_factory=list)

    # Metadata
    had_patient_context: bool = False
    result_count: int = 0
    user_feedback: Optional[int] = Field(None, description="1-5 rating or None")
    clicked_results: list[str] = Field(default_factory=list, description="IDs of clicked results")

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class PersonalizationConfig(BaseModel):
    """Configuration for personalization behavior."""

    # Specialty boosting
    specialty_boost_factor: float = Field(default=1.5, ge=1.0, le=3.0)
    specialty_filter_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # Learning parameters
    learning_rate: float = Field(default=0.1, ge=0.01, le=0.5)
    decay_factor: float = Field(default=0.95, ge=0.8, le=1.0)
    min_queries_for_detection: int = Field(default=10, ge=5, le=50)

    # Recommendation parameters
    recommendation_count: int = Field(default=5, ge=3, le=20)
    related_topics_count: int = Field(default=3, ge=1, le=10)

    # Privacy
    store_query_text: bool = Field(default=True)
    anonymize_after_days: int = Field(default=90)
