"""EMR integration module for patient context."""

from .bridge import EMRBridge
from .patient_rag import PatientRAG

__all__ = ["EMRBridge", "PatientRAG"]
