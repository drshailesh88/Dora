"""EMR integration module for patient context."""

# Legacy bridge (backward compatibility)
from .bridge import EMRBridge
from .patient_rag import PatientRAG

# Core models
from .models import (
    Allergy,
    ClinicalNote,
    Diagnosis,
    Encounter,
    Gender,
    LabResult,
    Medication,
    Order,
    OrderStatus,
    OrderType,
    Patient,
    PatientSummary,
    Severity,
    VitalSigns,
)

# EMR client
from .client import EMRClient, EMRConfig, MockEMRClient

# Patient context builder
from .context import PatientContextBuilder

# Clinical alerts
from .alerts import (
    AlertCategory,
    AlertLevel,
    ClinicalAlert,
    ClinicalAlertEngine,
)

# Feedback system
from .feedback import (
    FeedbackAnalytics,
    FeedbackStore,
    FeedbackType,
    OutcomeType,
    RecommendationFeedback,
    feedback_store,
)

# Sync manager
from .sync import (
    ConflictResolution,
    EMRSyncManager,
    SyncDirection,
    SyncRecord,
    SyncStatus,
)

# FHIR converter
from .fhir import FHIRConverter, patient_bundle_to_fhir

# Service layer
from .service import EMRService, get_emr_service, initialize_emr_service

__all__ = [
    # Legacy
    "EMRBridge",
    "PatientRAG",
    # Models
    "Patient",
    "Medication",
    "Allergy",
    "VitalSigns",
    "LabResult",
    "Diagnosis",
    "Encounter",
    "ClinicalNote",
    "Order",
    "PatientSummary",
    "Gender",
    "Severity",
    "OrderType",
    "OrderStatus",
    # Client
    "EMRClient",
    "EMRConfig",
    "MockEMRClient",
    # Context
    "PatientContextBuilder",
    # Alerts
    "ClinicalAlert",
    "ClinicalAlertEngine",
    "AlertLevel",
    "AlertCategory",
    # Feedback
    "RecommendationFeedback",
    "FeedbackStore",
    "FeedbackAnalytics",
    "FeedbackType",
    "OutcomeType",
    "feedback_store",
    # Sync
    "EMRSyncManager",
    "SyncRecord",
    "SyncStatus",
    "SyncDirection",
    "ConflictResolution",
    # FHIR
    "FHIRConverter",
    "patient_bundle_to_fhir",
    # Service
    "EMRService",
    "get_emr_service",
    "initialize_emr_service",
]
