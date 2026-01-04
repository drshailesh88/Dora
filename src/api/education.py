"""
Patient Education API Endpoints

REST API for generating and delivering patient education materials.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field

from ..auth.middleware import get_current_user
from ..education import (
    EducationService,
    get_education_service,
    PatientHandout,
    ContentType,
    ReadingLevel,
    DeliveryFormat,
)
from ..notifications.models import NotificationChannel

# Router
router = APIRouter(prefix="/api/education", tags=["education"])


# Request/Response Models
class GenerateHandoutRequest(BaseModel):
    """Request to generate patient handout."""

    query_answer: str = Field(..., description="Medical answer text")
    content_type: ContentType = Field(default=ContentType.GENERAL_HANDOUT)
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en", pattern="^(en|hi|ta|te|bn|mr)$")
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None


class MedicationGuideRequest(BaseModel):
    """Request to generate medication guide."""

    generic_name: str = Field(..., description="Generic medication name")
    brand_names: List[str] = Field(default_factory=list)
    indication: Optional[str] = Field(None, description="What it's prescribed for")
    dosage: Optional[str] = Field(None, description="Dosage instructions")
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None


class ConditionExplainerRequest(BaseModel):
    """Request to generate condition explainer."""

    condition_name: str = Field(..., description="Name of medical condition")
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None


class ProcedureGuideRequest(BaseModel):
    """Request to generate procedure guide."""

    procedure_name: str = Field(..., description="Name of procedure")
    procedure_type: str = Field(default="prep", pattern="^(prep|post_care)$")
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    special_instructions: List[str] = Field(default_factory=list)


class TemplateGenerateRequest(BaseModel):
    """Request to generate from template."""

    template_id: str = Field(..., description="Template identifier")
    template_data: dict = Field(default_factory=dict)
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    reading_level: ReadingLevel = Field(default=ReadingLevel.BASIC)
    language: str = Field(default="en")


class TranslateRequest(BaseModel):
    """Request to translate handout."""

    handout_id: str = Field(..., description="Handout identifier")
    target_language: str = Field(..., pattern="^(en|hi|ta|te|bn|mr)$")


class GeneratePDFRequest(BaseModel):
    """Request to generate PDF."""

    handout_id: str = Field(..., description="Handout identifier")
    large_font: bool = Field(default=False)


class SendToPatientRequest(BaseModel):
    """Request to send handout to patient."""

    handout_id: str = Field(..., description="Handout identifier")
    recipient: str = Field(..., description="Phone number or email")
    channel: NotificationChannel = Field(default=NotificationChannel.WHATSAPP)


class HandoutResponse(BaseModel):
    """Response with generated handout."""

    success: bool
    handout_id: str
    handout: Optional[dict] = None
    message: Optional[str] = None


class PDFResponse(BaseModel):
    """Response with PDF file path."""

    success: bool
    file_path: str
    message: Optional[str] = None


class TemplateListResponse(BaseModel):
    """Response with template list."""

    success: bool
    templates: List[dict]
    count: int


# In-memory storage (in production, use database)
_handout_storage: dict = {}


# Endpoints
@router.post("/generate", response_model=HandoutResponse)
async def generate_handout(
    request: GenerateHandoutRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate patient handout from medical answer.

    This endpoint converts a medical query answer into patient-friendly
    educational content at the appropriate reading level and language.
    """
    try:
        # Mock MedicalAnswer (in production, fetch from database)
        from ..core.models import MedicalAnswer, ConfidenceLevel

        answer = MedicalAnswer(
            question="Patient education request",
            answer=request.query_answer,
            confidence=ConfidenceLevel.HIGH,
            model_used="claude-3-5-sonnet",
            latency_ms=0,
        )

        # Generate handout
        handout = service.generate_from_query_answer(
            answer=answer,
            content_type=request.content_type,
            reading_level=request.reading_level,
            language=request.language,
            patient_name=request.patient_name,
            doctor_name=request.doctor_name,
            clinic_name=request.clinic_name,
        )

        # Store in memory
        _handout_storage[handout.id] = handout

        return HandoutResponse(
            success=True,
            handout_id=handout.id,
            handout=handout.model_dump(),
            message="Handout generated successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate handout: {str(e)}")


@router.post("/medication", response_model=HandoutResponse)
async def generate_medication_guide(
    request: MedicationGuideRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate medication guide for patient.

    Provides comprehensive information about a medication including dosage,
    side effects, interactions, and when to seek help.
    """
    try:
        handout = service.generate_medication_guide(
            generic_name=request.generic_name,
            brand_names=request.brand_names,
            indication=request.indication,
            dosage=request.dosage,
            reading_level=request.reading_level,
            language=request.language,
            patient_name=request.patient_name,
            doctor_name=request.doctor_name,
        )

        # Store
        _handout_storage[handout.id] = handout

        return HandoutResponse(
            success=True,
            handout_id=handout.id,
            handout=handout.model_dump(),
            message="Medication guide generated successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate medication guide: {str(e)}")


@router.post("/condition", response_model=HandoutResponse)
async def generate_condition_explainer(
    request: ConditionExplainerRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate condition explainer for patient.

    Provides patient-friendly explanation of a medical condition including
    symptoms, causes, treatment, and lifestyle modifications.
    """
    try:
        handout = service.generate_condition_explainer(
            condition_name=request.condition_name,
            reading_level=request.reading_level,
            language=request.language,
            patient_name=request.patient_name,
            doctor_name=request.doctor_name,
        )

        # Store
        _handout_storage[handout.id] = handout

        return HandoutResponse(
            success=True,
            handout_id=handout.id,
            handout=handout.model_dump(),
            message="Condition explainer generated successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate condition explainer: {str(e)}")


@router.post("/procedure", response_model=HandoutResponse)
async def generate_procedure_guide(
    request: ProcedureGuideRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate procedure preparation or post-care guide.

    Provides instructions for preparing for a medical procedure or
    caring for yourself after a procedure.
    """
    try:
        # Generate based on type
        if request.procedure_type == "prep":
            prep_guide = service.procedure_generator.generate_prep_guide(
                procedure_name=request.procedure_name,
                special_instructions=request.special_instructions,
                reading_level=request.reading_level,
                language=request.language,
            )

            handout = PatientHandout(
                title=f"Preparing for {request.procedure_name}",
                content_type=ContentType.PROCEDURE_PREP,
                procedure_prep=prep_guide,
                patient_name=request.patient_name,
                doctor_name=request.doctor_name,
                reading_level=request.reading_level,
                language=request.language,
            )
        else:  # post_care
            post_care = service.procedure_generator.generate_post_care_guide(
                procedure_name=request.procedure_name,
                special_instructions=request.special_instructions,
                reading_level=request.reading_level,
                language=request.language,
            )

            handout = PatientHandout(
                title=f"After Your {request.procedure_name}",
                content_type=ContentType.POST_CARE_GUIDE,
                post_care_guide=post_care,
                patient_name=request.patient_name,
                doctor_name=request.doctor_name,
                reading_level=request.reading_level,
                language=request.language,
            )

        # Store
        _handout_storage[handout.id] = handout

        return HandoutResponse(
            success=True,
            handout_id=handout.id,
            handout=handout.model_dump(),
            message="Procedure guide generated successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate procedure guide: {str(e)}")


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Get list of available education templates.

    Returns pre-built templates for common conditions and scenarios
    like diabetes management, hypertension care, medication adherence, etc.
    """
    try:
        templates = service.get_templates()

        return TemplateListResponse(
            success=True,
            templates=templates,
            count=len(templates),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """Get template details by ID."""
    try:
        template = service.get_template_by_id(template_id)
        return {"success": True, "template": template}

    except KeyError:
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch template: {str(e)}")


@router.post("/template/generate", response_model=HandoutResponse)
async def generate_from_template(
    request: TemplateGenerateRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate handout from template.

    Use a pre-built template and customize it with patient-specific data.
    """
    try:
        handout = service.generate_from_template(
            template_id=request.template_id,
            template_data=request.template_data,
            patient_name=request.patient_name,
            doctor_name=request.doctor_name,
            reading_level=request.reading_level,
            language=request.language,
        )

        # Store
        _handout_storage[handout.id] = handout

        return HandoutResponse(
            success=True,
            handout_id=handout.id,
            handout=handout.model_dump(),
            message="Handout generated from template successfully",
        )

    except KeyError:
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate from template: {str(e)}")


@router.post("/translate", response_model=HandoutResponse)
async def translate_handout(
    request: TranslateRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Translate handout to another language.

    Supports English, Hindi, Tamil, Telugu, Bengali, and Marathi.
    """
    try:
        # Get original handout
        original = _handout_storage.get(request.handout_id)
        if not original:
            raise HTTPException(status_code=404, detail="Handout not found")

        # Translate
        translated = service.translate_handout(original, request.target_language)

        # Store translated version
        _handout_storage[translated.id] = translated

        return HandoutResponse(
            success=True,
            handout_id=translated.id,
            handout=translated.model_dump(),
            message=f"Handout translated to {request.target_language}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to translate handout: {str(e)}")


@router.post("/pdf", response_model=PDFResponse)
async def generate_pdf(
    request: GeneratePDFRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Generate PDF from handout.

    Creates a professionally formatted PDF document that can be
    printed or emailed to patients.
    """
    try:
        # Get handout
        handout = _handout_storage.get(request.handout_id)
        if not handout:
            raise HTTPException(status_code=404, detail="Handout not found")

        # Update large font setting
        handout.large_font = request.large_font

        # Generate PDF
        file_path = service.save_handout_pdf(handout)

        return PDFResponse(
            success=True,
            file_path=file_path,
            message="PDF generated successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/pdf/{handout_id}/download")
async def download_pdf(
    handout_id: str,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Download handout as PDF.

    Returns the PDF file for download.
    """
    try:
        # Get handout
        handout = _handout_storage.get(handout_id)
        if not handout:
            raise HTTPException(status_code=404, detail="Handout not found")

        # Generate PDF bytes
        pdf_bytes = service.format_handout(handout, DeliveryFormat.PDF)

        # Return as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=handout_{handout_id}.pdf"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")


@router.post("/send")
async def send_to_patient(
    request: SendToPatientRequest,
    current_user: dict = Depends(get_current_user),
    service: EducationService = Depends(get_education_service),
):
    """
    Send handout to patient via WhatsApp, SMS, or email.

    Delivers the educational material to the patient through their
    preferred communication channel.
    """
    try:
        # Get handout
        handout = _handout_storage.get(request.handout_id)
        if not handout:
            raise HTTPException(status_code=404, detail="Handout not found")

        # Send to patient
        success = service.send_to_patient(
            handout=handout,
            recipient=request.recipient,
            channel=request.channel,
            user_id=current_user.get("user_id"),
        )

        if success:
            return {
                "success": True,
                "message": f"Handout sent to {request.recipient} via {request.channel.value}",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send handout")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send handout: {str(e)}")


@router.get("/handout/{handout_id}")
async def get_handout(
    handout_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get handout by ID."""
    handout = _handout_storage.get(handout_id)
    if not handout:
        raise HTTPException(status_code=404, detail="Handout not found")

    # Track view
    handout.viewed = True
    handout.view_count += 1

    return {
        "success": True,
        "handout": handout.model_dump(),
    }


@router.get("/analytics")
async def get_analytics(
    current_user: dict = Depends(get_current_user),
):
    """
    Get education module analytics.

    Returns statistics on handout generation, delivery, and usage.
    """
    return {
        "success": True,
        "analytics": {
            "total_handouts": len(_handout_storage),
            "by_type": {},
            "by_language": {},
        },
    }
