"""
Patient Education Module

Automated patient education content generation for Dora.
Converts medical knowledge into patient-friendly handouts in multiple languages.
"""

# Models
from .models import (
    PatientHandout,
    MedicationGuide,
    ConditionExplainer,
    ProcedurePrep,
    PostCareGuide,
    DietPlan,
    LifestyleGuide,
    FollowUpReminder,
    EducationTemplate,
    ReadingLevel,
    ContentType,
    DeliveryFormat,
    SeverityLevel,
    DosageInstruction,
    SideEffect,
    WarningSign,
    DosDonts,
)

# Generators
from .generator import ContentGenerator, ReadingLevelAnalyzer, IconProvider
from .medications import MedicationGuideGenerator, PillIdentifier
from .conditions import ConditionExplainerGenerator
from .procedures import ProcedureGuideGenerator

# Translation
from .translator import EducationTranslator, WhatsAppFormatter, SMSFormatter

# Formatting
from .formatter import PDFFormatter, HTMLFormatter, PlainTextFormatter

# Templates
from .templates import TemplateLibrary, get_template_library

# Service
from .service import (
    EducationService,
    EducationAnalytics,
    get_education_service,
)

__all__ = [
    # Models
    "PatientHandout",
    "MedicationGuide",
    "ConditionExplainer",
    "ProcedurePrep",
    "PostCareGuide",
    "DietPlan",
    "LifestyleGuide",
    "FollowUpReminder",
    "EducationTemplate",
    "ReadingLevel",
    "ContentType",
    "DeliveryFormat",
    "SeverityLevel",
    "DosageInstruction",
    "SideEffect",
    "WarningSign",
    "DosDonts",
    # Generators
    "ContentGenerator",
    "ReadingLevelAnalyzer",
    "IconProvider",
    "MedicationGuideGenerator",
    "PillIdentifier",
    "ConditionExplainerGenerator",
    "ProcedureGuideGenerator",
    # Translation
    "EducationTranslator",
    "WhatsAppFormatter",
    "SMSFormatter",
    # Formatting
    "PDFFormatter",
    "HTMLFormatter",
    "PlainTextFormatter",
    # Templates
    "TemplateLibrary",
    "get_template_library",
    # Service
    "EducationService",
    "EducationAnalytics",
    "get_education_service",
]

__version__ = "1.0.0"
