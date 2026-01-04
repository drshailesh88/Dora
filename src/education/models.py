"""
Patient Education Content Models

Data models for patient educational materials including handouts, medication guides,
condition explainers, and procedure instructions.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ReadingLevel(str, Enum):
    """Literacy/reading level for patient materials."""

    BASIC = "basic"  # 5th-8th grade (Flesch-Kincaid 5-8)
    INTERMEDIATE = "intermediate"  # 9th-12th grade (Flesch-Kincaid 9-12)
    ADVANCED = "advanced"  # College level (Flesch-Kincaid 13+)


class ContentType(str, Enum):
    """Type of educational content."""

    MEDICATION_GUIDE = "medication_guide"
    CONDITION_EXPLAINER = "condition_explainer"
    PROCEDURE_PREP = "procedure_prep"
    POST_CARE_GUIDE = "post_care_guide"
    DIET_PLAN = "diet_plan"
    LIFESTYLE_GUIDE = "lifestyle_guide"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    GENERAL_HANDOUT = "general_handout"


class DeliveryFormat(str, Enum):
    """Output format for educational content."""

    PDF = "pdf"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class SeverityLevel(str, Enum):
    """Severity level for side effects or symptoms."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EMERGENCY = "emergency"


class DosageInstruction(BaseModel):
    """Medication dosage instructions."""

    dose: str = Field(..., description="Dose amount (e.g., '500mg', '1 tablet')")
    frequency: str = Field(..., description="How often (e.g., 'twice daily', 'every 6 hours')")
    timing: Optional[str] = Field(None, description="When to take (e.g., 'with food', 'at bedtime')")
    duration: Optional[str] = Field(None, description="How long (e.g., '7 days', 'ongoing')")
    special_instructions: List[str] = Field(default_factory=list)


class SideEffect(BaseModel):
    """Side effect information."""

    name: str = Field(..., description="Side effect name")
    severity: SeverityLevel = Field(default=SeverityLevel.MILD)
    frequency: Optional[str] = Field(None, description="How common (e.g., 'common', 'rare')")
    description: Optional[str] = Field(None, description="Additional details")


class WarningSign(BaseModel):
    """Warning sign that requires medical attention."""

    symptom: str = Field(..., description="Symptom to watch for")
    action: str = Field(..., description="What to do (e.g., 'Call doctor', 'Go to ER')")
    urgency: SeverityLevel = Field(default=SeverityLevel.MODERATE)


class DosDonts(BaseModel):
    """Do's and Don'ts instructions."""

    dos: List[str] = Field(default_factory=list, description="Things to do")
    donts: List[str] = Field(default_factory=list, description="Things to avoid")


class MedicationGuide(BaseModel):
    """Complete medication guide for patients."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Medication identification
    generic_name: str = Field(..., description="Generic medication name")
    brand_names: List[str] = Field(default_factory=list)
    drug_class: Optional[str] = Field(None, description="Medication class")

    # Purpose
    purpose: str = Field(..., description="What it's for (simple terms)")
    condition_treated: Optional[str] = Field(None)

    # Dosage
    dosage: DosageInstruction = Field(...)

    # How to take
    administration_route: str = Field(default="oral", description="oral, injection, topical, etc.")
    instructions: List[str] = Field(default_factory=list)

    # Side effects
    common_side_effects: List[SideEffect] = Field(default_factory=list)
    serious_side_effects: List[SideEffect] = Field(default_factory=list)

    # Interactions
    food_interactions: List[str] = Field(default_factory=list)
    drug_interactions: List[str] = Field(default_factory=list)
    alcohol_warning: Optional[str] = Field(None)

    # Storage and handling
    storage_instructions: str = Field(default="Store at room temperature")
    expiry_info: Optional[str] = Field(None)

    # Missed dose
    missed_dose_instructions: str = Field(default="Take as soon as you remember")

    # Visual identification
    pill_description: Optional[str] = Field(None, description="Color, shape, imprint")
    pill_image_url: Optional[str] = Field(None)

    # When to seek help
    warning_signs: List[WarningSign] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ConditionExplainer(BaseModel):
    """Patient-friendly condition explanation."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Condition identification
    condition_name: str = Field(..., description="Medical condition name")
    alternate_names: List[str] = Field(default_factory=list)

    # What is it?
    simple_explanation: str = Field(..., description="What is this condition? (simple terms)")
    medical_definition: Optional[str] = Field(None)

    # Causes
    causes: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)

    # Symptoms
    common_symptoms: List[str] = Field(default_factory=list)
    warning_signs: List[WarningSign] = Field(default_factory=list)

    # Diagnosis
    how_diagnosed: List[str] = Field(default_factory=list, description="Tests and procedures")

    # Treatment
    treatment_options: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    lifestyle_changes: List[str] = Field(default_factory=list)

    # Prognosis
    prognosis: Optional[str] = Field(None, description="What to expect")
    complications: List[str] = Field(default_factory=list)

    # Living with condition
    self_care: List[str] = Field(default_factory=list)
    dos_donts: Optional[DosDonts] = Field(None)

    # FAQ
    frequently_asked_questions: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {'question': 'answer'} dicts"
    )

    # Resources
    support_resources: List[str] = Field(default_factory=list)
    useful_websites: List[str] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProcedurePrep(BaseModel):
    """Pre-procedure preparation instructions."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Procedure identification
    procedure_name: str = Field(..., description="Name of procedure")
    procedure_type: Optional[str] = Field(None, description="diagnostic, surgical, etc.")

    # Before procedure
    days_before_instructions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Timeline of prep steps"
    )
    fasting_instructions: Optional[str] = Field(None)
    medication_adjustments: List[str] = Field(default_factory=list)
    what_to_bring: List[str] = Field(default_factory=list)

    # Day of procedure
    arrival_time: Optional[str] = Field(None)
    expected_duration: Optional[str] = Field(None)
    anesthesia_type: Optional[str] = Field(None)

    # What to expect
    procedure_description: str = Field(default="")
    what_happens_during: List[str] = Field(default_factory=list)
    pain_management: Optional[str] = Field(None)

    # After procedure
    recovery_location: Optional[str] = Field(None, description="recovery room, home, etc.")
    discharge_criteria: List[str] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PostCareGuide(BaseModel):
    """Post-procedure or discharge care instructions."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Identification
    title: str = Field(..., description="e.g., 'Post-Surgery Care', 'Discharge Instructions'")
    condition_or_procedure: str = Field(...)

    # Recovery timeline
    recovery_timeline: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Timeline: [{'period': 'First 24 hours', 'expect': '...'}]"
    )
    full_recovery_time: Optional[str] = Field(None)

    # Wound care
    wound_care_instructions: List[str] = Field(default_factory=list)
    dressing_change_schedule: Optional[str] = Field(None)

    # Activity restrictions
    activity_restrictions: List[str] = Field(default_factory=list)
    when_can_resume: Dict[str, str] = Field(
        default_factory=dict,
        description="Activity: timeframe mapping"
    )

    # Diet
    diet_instructions: List[str] = Field(default_factory=list)

    # Medications
    pain_management: List[str] = Field(default_factory=list)
    prescribed_medications: List[str] = Field(default_factory=list)

    # Warning signs
    warning_signs: List[WarningSign] = Field(default_factory=list)
    when_to_call_doctor: List[str] = Field(default_factory=list)
    emergency_signs: List[str] = Field(default_factory=list)

    # Follow-up
    follow_up_appointments: List[Dict[str, str]] = Field(default_factory=list)
    test_results_timeline: Optional[str] = Field(None)

    # Do's and Don'ts
    dos_donts: Optional[DosDonts] = Field(None)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DietPlan(BaseModel):
    """Dietary recommendations for specific conditions."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Identification
    title: str = Field(..., description="e.g., 'Diabetic Diet Plan', 'Heart-Healthy Diet'")
    condition: str = Field(..., description="Condition this diet is for")

    # Goals
    dietary_goals: List[str] = Field(default_factory=list)

    # Foods
    foods_to_eat: List[str] = Field(default_factory=list)
    foods_to_limit: List[str] = Field(default_factory=list)
    foods_to_avoid: List[str] = Field(default_factory=list)

    # Meal planning
    sample_meal_plan: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Meal type -> food items"
    )
    portion_sizes: List[str] = Field(default_factory=list)

    # Specific recommendations
    calorie_target: Optional[str] = Field(None)
    macronutrient_targets: Optional[Dict[str, str]] = Field(None)
    micronutrient_focus: List[str] = Field(default_factory=list)

    # Practical tips
    cooking_tips: List[str] = Field(default_factory=list)
    dining_out_tips: List[str] = Field(default_factory=list)
    shopping_list: List[str] = Field(default_factory=list)

    # Monitoring
    what_to_monitor: List[str] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class LifestyleGuide(BaseModel):
    """Lifestyle modification recommendations."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Identification
    title: str = Field(..., description="e.g., 'Managing Hypertension'")
    condition: str = Field(...)

    # Categories of lifestyle changes
    exercise_recommendations: List[str] = Field(default_factory=list)
    stress_management: List[str] = Field(default_factory=list)
    sleep_hygiene: List[str] = Field(default_factory=list)
    substance_use: List[str] = Field(default_factory=list)

    # Goals
    health_goals: List[str] = Field(default_factory=list)

    # Action plan
    immediate_actions: List[str] = Field(default_factory=list)
    short_term_goals: List[str] = Field(default_factory=list)
    long_term_goals: List[str] = Field(default_factory=list)

    # Do's and Don'ts
    dos_donts: Optional[DosDonts] = Field(None)

    # Support
    support_systems: List[str] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FollowUpReminder(BaseModel):
    """Follow-up appointment and care reminders."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Identification
    patient_name: str = Field(...)
    condition_or_procedure: str = Field(...)

    # Appointments
    next_appointment_date: Optional[datetime] = Field(None)
    appointment_type: Optional[str] = Field(None, description="Follow-up visit, lab work, etc.")

    # Tests needed
    tests_required: List[str] = Field(default_factory=list)
    test_preparation: List[str] = Field(default_factory=list)

    # Medication reminders
    medications_to_continue: List[str] = Field(default_factory=list)
    prescription_refills: List[str] = Field(default_factory=list)

    # Monitoring
    symptoms_to_monitor: List[str] = Field(default_factory=list)
    measurements_to_track: List[str] = Field(default_factory=list)

    # Questions to ask at next visit
    questions_for_doctor: List[str] = Field(default_factory=list)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PatientHandout(BaseModel):
    """Complete patient handout document."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Header information
    title: str = Field(..., description="Handout title")
    content_type: ContentType = Field(...)
    subtitle: Optional[str] = Field(None)

    # Patient information
    patient_name: Optional[str] = Field(None)
    patient_id: Optional[str] = Field(None)
    doctor_name: Optional[str] = Field(None)
    clinic_name: Optional[str] = Field(None)

    # Content (one of these based on content_type)
    medication_guide: Optional[MedicationGuide] = Field(None)
    condition_explainer: Optional[ConditionExplainer] = Field(None)
    procedure_prep: Optional[ProcedurePrep] = Field(None)
    post_care_guide: Optional[PostCareGuide] = Field(None)
    diet_plan: Optional[DietPlan] = Field(None)
    lifestyle_guide: Optional[LifestyleGuide] = Field(None)
    follow_up_reminder: Optional[FollowUpReminder] = Field(None)

    # Custom content for general handouts
    custom_sections: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Custom sections: [{'title': 'Section Title', 'content': '...'}]"
    )

    # Footer information
    contact_information: Optional[Dict[str, str]] = Field(None)
    emergency_contacts: Optional[Dict[str, str]] = Field(None)

    # QR code for digital version
    qr_code_url: Optional[str] = Field(None)
    digital_version_url: Optional[str] = Field(None)

    # Metadata
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    delivery_format: DeliveryFormat = Field(default=DeliveryFormat.PDF)
    large_font: bool = Field(default=False, description="Accessibility option")

    # Tracking
    generated_by: Optional[str] = Field(None, description="Doctor/user ID")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = Field(None)
    delivery_method: Optional[str] = Field(None, description="email, whatsapp, print")

    # Analytics
    viewed: bool = Field(default=False)
    view_count: int = Field(default=0)
    last_viewed_at: Optional[datetime] = Field(None)


class EducationTemplate(BaseModel):
    """Pre-built template for common educational needs."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Template name")
    content_type: ContentType = Field(...)
    description: str = Field(..., description="What this template is for")

    # Template content structure
    template_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template structure with placeholders"
    )

    # Required fields for this template
    required_fields: List[str] = Field(default_factory=list)

    # Supported languages
    languages: List[str] = Field(default_factory=lambda: ["en"])

    # Usage
    times_used: int = Field(default=0)
    last_used: Optional[datetime] = Field(None)

    # Metadata
    created_by: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
