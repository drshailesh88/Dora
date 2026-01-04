"""Clinical Documentation Module for Dora.

Comprehensive clinical documentation generation, validation, and formatting.
"""

# Models
from .models import (
    CertificateType,
    ConsultNote,
    DeathSummary,
    Diagnosis,
    DischargeSummary,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    Investigation,
    MedicalCertificate,
    Medication,
    OperativeNote,
    Patient,
    ProgressNote,
    Provider,
    ReferralLetter,
    SOAPNote,
    UrgencyLevel,
    Vitals,
)

# Generators
from .certificate import MedicalCertificateGenerator, generate_fitness_certificate, generate_sick_leave
from .discharge import DischargeSummaryGenerator, generate_discharge_summary
from .operative import OperativeNoteGenerator, generate_operative_note
from .referral import ReferralLetterGenerator, generate_referral_letter
from .soap import SOAPNoteGenerator, generate_soap_note

# Utilities
from .extractor import MedicalInformationExtractor, extract_medical_entities
from .formatter import EMRFormatter, JSONFormatter, PDFFormatter, TextFormatter, to_json, to_pdf, to_text
from .templates import BOILERPLATE_LIBRARY, Specialty, TemplateManager, get_boilerplate
from .validator import (
    DocumentValidator,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    validate_document,
)

# Main service
from .service import DocumentationService, get_documentation_service

__all__ = [
    # Models
    "CertificateType",
    "ConsultNote",
    "DeathSummary",
    "Diagnosis",
    "DischargeSummary",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentType",
    "Investigation",
    "MedicalCertificate",
    "Medication",
    "OperativeNote",
    "Patient",
    "ProgressNote",
    "Provider",
    "ReferralLetter",
    "SOAPNote",
    "UrgencyLevel",
    "Vitals",
    # Generators
    "MedicalCertificateGenerator",
    "generate_fitness_certificate",
    "generate_sick_leave",
    "DischargeSummaryGenerator",
    "generate_discharge_summary",
    "OperativeNoteGenerator",
    "generate_operative_note",
    "ReferralLetterGenerator",
    "generate_referral_letter",
    "SOAPNoteGenerator",
    "generate_soap_note",
    # Utilities
    "MedicalInformationExtractor",
    "extract_medical_entities",
    "EMRFormatter",
    "JSONFormatter",
    "PDFFormatter",
    "TextFormatter",
    "to_json",
    "to_pdf",
    "to_text",
    "BOILERPLATE_LIBRARY",
    "Specialty",
    "TemplateManager",
    "get_boilerplate",
    "DocumentValidator",
    "ValidationIssue",
    "ValidationLevel",
    "ValidationResult",
    "validate_document",
    # Main service
    "DocumentationService",
    "get_documentation_service",
]
