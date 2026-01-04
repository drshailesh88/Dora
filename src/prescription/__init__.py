"""
Prescription module for Dora.

One-tap prescription generation from Dora AI answers with:
- AI-powered extraction
- Drug interaction validation
- Cost-saving alternatives
- Digital signatures
- Pharmacy integration
- EMR integration

Usage:
    from src.prescription import PrescriptionService

    service = PrescriptionService()

    result = service.generate_from_dora_answer(
        answer_text="Tab. Metformin 500mg 1-0-1 x 30 days",
        dora_answer_id="DORA-123",
        patient=patient_info,
        doctor=doctor_info,
    )

    prescription = result['prescription']
"""

# Models
from .models import (
    # Enums
    RouteOfAdministration,
    Frequency,
    DosageForm,
    DrugSchedule,
    PrescriptionStatus,

    # Core models
    Dosage,
    Refill,
    Substitution,
    PrescriptionItem,
    PrescriptionTemplate,
    DoctorInfo,
    PatientInfo,
    DigitalSignature,
    Prescription,
    EPrescription,

    # Validation
    PrescriptionValidationResult,
    DrugAlternative,
)

# Services
from .service import PrescriptionService

# Builders
from .builder import (
    PrescriptionBuilder,
    QuickPrescriptionBuilder,
    PrescriptionEditor,
)

# Extractor
from .extractor import PrescriptionExtractor

# Validator
from .validator import PrescriptionValidator

# Alternatives
from .alternatives import (
    AlternativesSuggester,
    CostComparisonReport,
)

# Templates
from .templates import (
    TemplateLibrary,
    CustomTemplateManager,
)

# Signature
from .signature import (
    SignatureService,
    DigitalCertificate,
    PINAuthentication,
)

# Formatter
from .formatter import (
    PrescriptionFormatter,
    ValidationFormatter,
)

# Pharmacy/Dispensing
from .dispense import (
    PharmacyService,
    RefillManager,
    Pharmacy,
    DispenseRecord,
    DispensingStatus,
)

# Version
__version__ = "1.0.0"

# Main exports for convenience
__all__ = [
    # Main service (primary entry point)
    'PrescriptionService',

    # Models
    'Prescription',
    'EPrescription',
    'PrescriptionItem',
    'Dosage',
    'PatientInfo',
    'DoctorInfo',
    'DigitalSignature',
    'PrescriptionValidationResult',
    'DrugAlternative',

    # Enums
    'RouteOfAdministration',
    'Frequency',
    'DosageForm',
    'DrugSchedule',
    'PrescriptionStatus',

    # Builders
    'PrescriptionBuilder',
    'QuickPrescriptionBuilder',

    # Components
    'PrescriptionExtractor',
    'PrescriptionValidator',
    'AlternativesSuggester',
    'TemplateLibrary',
    'SignatureService',
    'PrescriptionFormatter',
    'PharmacyService',

    # Version
    '__version__',
]
