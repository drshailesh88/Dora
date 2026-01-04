"""FastAPI endpoints for clinical documentation.

Provides REST API for all documentation functionality.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from ..documentation import (
    DischargeSummary,
    MedicalCertificate,
    OperativeNote,
    Patient,
    Provider,
    ReferralLetter,
    SOAPNote,
    UrgencyLevel,
    get_documentation_service,
)

router = APIRouter(prefix="/api/docs", tags=["documentation"])


# Request/Response Models
class SOAPNoteRequest(BaseModel):
    """Request to generate SOAP note."""

    text: str = Field(..., description="Clinical encounter text or voice transcript")
    patient: Optional[dict[str, Any]] = None
    provider: Optional[dict[str, Any]] = None


class SOAPNoteStructuredRequest(BaseModel):
    """Request to generate SOAP note from structured data."""

    data: dict[str, Any]
    patient: Optional[dict[str, Any]] = None
    provider: Optional[dict[str, Any]] = None


class DischargeSummaryRequest(BaseModel):
    """Request to generate discharge summary."""

    patient: dict[str, Any]
    provider: dict[str, Any]
    admission_data: dict[str, Any]
    enhance: bool = True


class ReferralLetterRequest(BaseModel):
    """Request to generate referral letter."""

    patient: dict[str, Any]
    referring_provider: dict[str, Any]
    specialty: str
    reason: str
    clinical_summary: Optional[str] = None
    specialist: Optional[dict[str, Any]] = None
    urgency: str = "routine"
    diagnoses: Optional[list[dict[str, Any]]] = None
    medications: Optional[list[dict[str, Any]]] = None
    investigations: Optional[list[dict[str, Any]]] = None
    specific_questions: Optional[list[str]] = None


class SickLeaveRequest(BaseModel):
    """Request to generate sick leave certificate."""

    patient: dict[str, Any]
    provider: dict[str, Any]
    diagnosis: str
    days: int = 3


class FitnessCertificateRequest(BaseModel):
    """Request to generate fitness certificate."""

    patient: dict[str, Any]
    provider: dict[str, Any]
    purpose: str
    fit_for: str = "normal duties"
    restrictions: Optional[str] = None


class OperativeNoteRequest(BaseModel):
    """Request to generate operative note."""

    patient: dict[str, Any]
    surgeon: dict[str, Any]
    operative_data: dict[str, Any]
    assistants: Optional[list[dict[str, Any]]] = None


class OperativeDictationRequest(BaseModel):
    """Request to generate operative note from dictation."""

    dictation: str
    patient: dict[str, Any]
    surgeon: dict[str, Any]
    assistants: Optional[list[dict[str, Any]]] = None


class ExtractionRequest(BaseModel):
    """Request to extract medical entities."""

    text: str
    is_voice: bool = False


class ValidationRequest(BaseModel):
    """Request to validate document."""

    document: dict[str, Any]
    document_type: str  # soap, discharge, referral, operative, certificate


class FormatRequest(BaseModel):
    """Request to format document."""

    document: dict[str, Any]
    document_type: str
    format: str = "text"  # text, json, pdf


class SignDocumentRequest(BaseModel):
    """Request to sign document."""

    document: dict[str, Any]
    document_type: str


# Endpoints

# SOAP Notes
@router.post("/soap", response_model=dict[str, Any])
async def generate_soap_note(request: SOAPNoteRequest):
    """Generate SOAP note from text."""
    service = get_documentation_service()

    # Parse patient and provider
    patient = Patient(**request.patient) if request.patient else None
    provider = Provider(**request.provider) if request.provider else None

    # Generate SOAP note
    soap = await service.generate_soap_from_text(request.text, patient, provider)

    return soap.model_dump()


@router.post("/soap/structured", response_model=dict[str, Any])
async def generate_soap_note_structured(request: SOAPNoteStructuredRequest):
    """Generate SOAP note from structured data."""
    service = get_documentation_service()

    patient = Patient(**request.patient) if request.patient else None
    provider = Provider(**request.provider) if request.provider else None

    soap = await service.soap_generator.generate_from_structured(
        request.data, patient, provider
    )

    return soap.model_dump()


@router.post("/soap/voice", response_model=dict[str, Any])
async def generate_soap_from_voice(request: SOAPNoteRequest):
    """Generate SOAP note from voice transcript."""
    service = get_documentation_service()

    patient = Patient(**request.patient) if request.patient else None
    provider = Provider(**request.provider) if request.provider else None

    soap = await service.generate_soap_from_voice(request.text, patient, provider)

    return soap.model_dump()


# Discharge Summaries
@router.post("/discharge", response_model=dict[str, Any])
async def generate_discharge_summary(request: DischargeSummaryRequest):
    """Generate discharge summary."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    provider = Provider(**request.provider)

    summary = await service.generate_discharge_summary(
        patient, provider, request.admission_data, request.enhance
    )

    return summary.model_dump()


# Referral Letters
@router.post("/referral", response_model=dict[str, Any])
async def generate_referral_letter(request: ReferralLetterRequest):
    """Generate referral letter."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    referring_provider = Provider(**request.referring_provider)
    specialist = Provider(**request.specialist) if request.specialist else None
    urgency = UrgencyLevel(request.urgency)

    referral = await service.generate_referral(
        patient=patient,
        referring_provider=referring_provider,
        specialty=request.specialty,
        reason=request.reason,
        urgency=urgency,
        clinical_summary=request.clinical_summary,
        specialist=specialist,
        diagnoses=[d for d in (request.diagnoses or [])],
        medications=[m for m in (request.medications or [])],
        investigations=[i for i in (request.investigations or [])],
        specific_questions=request.specific_questions,
    )

    return referral.model_dump()


# Medical Certificates
@router.post("/certificate/sick-leave", response_model=dict[str, Any])
async def generate_sick_leave_certificate(request: SickLeaveRequest):
    """Generate sick leave certificate."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    provider = Provider(**request.provider)

    cert = service.generate_sick_leave(
        patient, provider, request.diagnosis, request.days
    )

    return cert.model_dump()


@router.post("/certificate/fitness", response_model=dict[str, Any])
async def generate_fitness_certificate_endpoint(request: FitnessCertificateRequest):
    """Generate fitness certificate."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    provider = Provider(**request.provider)

    cert = service.generate_fitness_certificate(
        patient, provider, request.purpose, request.fit_for, request.restrictions
    )

    return cert.model_dump()


# Operative Notes
@router.post("/operative", response_model=dict[str, Any])
async def generate_operative_note_endpoint(request: OperativeNoteRequest):
    """Generate operative note."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    surgeon = Provider(**request.surgeon)
    assistants = (
        [Provider(**a) for a in request.assistants] if request.assistants else None
    )

    op_note = await service.generate_operative_note(
        patient, surgeon, request.operative_data, assistants
    )

    return op_note.model_dump()


@router.post("/operative/dictation", response_model=dict[str, Any])
async def generate_operative_from_dictation_endpoint(request: OperativeDictationRequest):
    """Generate operative note from surgeon's dictation."""
    service = get_documentation_service()

    patient = Patient(**request.patient)
    surgeon = Provider(**request.surgeon)
    assistants = (
        [Provider(**a) for a in request.assistants] if request.assistants else None
    )

    op_note = await service.generate_operative_from_dictation(
        request.dictation, patient, surgeon, assistants
    )

    return op_note.model_dump()


# Information Extraction
@router.post("/extract", response_model=dict[str, Any])
async def extract_medical_entities(request: ExtractionRequest):
    """Extract medical entities from text."""
    service = get_documentation_service()

    if request.is_voice:
        extracted = await service.extract_from_voice(request.text)
    else:
        extracted = await service.extract_from_text(request.text)

    return extracted


# Validation
@router.post("/validate", response_model=dict[str, Any])
async def validate_document(request: ValidationRequest):
    """Validate a clinical document."""
    service = get_documentation_service()

    # Parse document based on type
    document = _parse_document(request.document, request.document_type)

    # Validate
    validation = service.validate(document)

    return {
        "is_valid": validation.is_valid,
        "has_errors": validation.has_errors,
        "has_warnings": validation.has_warnings,
        "completeness_score": validation.completeness_score,
        "summary": validation.get_summary(),
        "issues": [
            {
                "level": issue.level.value,
                "field": issue.field,
                "message": issue.message,
                "suggestion": issue.suggestion,
            }
            for issue in validation.issues
        ],
    }


# Formatting
@router.post("/format")
async def format_document(request: FormatRequest):
    """Format document to various formats."""
    service = get_documentation_service()

    # Parse document
    document = _parse_document(request.document, request.document_type)

    # Format
    if request.format == "text":
        content = service.to_text(document)
        return {"content": content, "content_type": "text/plain"}

    elif request.format == "json":
        content = service.to_json(document)
        return {"content": content, "content_type": "application/json"}

    elif request.format == "pdf":
        try:
            pdf_bytes = service.to_pdf(document)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="document.pdf"'
                },
            )
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")


# Signing
@router.post("/sign", response_model=dict[str, Any])
async def sign_document(request: SignDocumentRequest):
    """Sign a clinical document."""
    service = get_documentation_service()

    # Parse document
    document = _parse_document(request.document, request.document_type)

    # Sign
    try:
        success = service.sign_document(document)
        return {
            "success": success,
            "signed_at": document.signed_at.isoformat(),
            "status": document.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# EMR Integration
@router.post("/emr/push", response_model=dict[str, Any])
async def push_to_emr(request: dict[str, Any]):
    """Push document to EMR."""
    service = get_documentation_service()

    document = _parse_document(request["document"], request["document_type"])
    emr_system = request.get("emr_system", "docassist")

    result = await service.push_to_emr(document, emr_system)

    return result


# Templates
@router.get("/templates", response_model=list[dict[str, Any]])
async def list_templates(specialty: Optional[str] = None):
    """List available document templates."""
    service = get_documentation_service()

    templates = service.list_templates(specialty)

    return templates


# Helper Functions
def _parse_document(data: dict[str, Any], doc_type: str):
    """Parse document data to appropriate model."""
    if doc_type == "soap":
        return SOAPNote(**data)
    elif doc_type == "discharge":
        return DischargeSummary(**data)
    elif doc_type == "referral":
        return ReferralLetter(**data)
    elif doc_type == "operative":
        return OperativeNote(**data)
    elif doc_type == "certificate":
        return MedicalCertificate(**data)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown document type: {doc_type}")
