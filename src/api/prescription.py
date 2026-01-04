"""
Prescription API endpoints for Dora.

FastAPI endpoints for prescription management:
- Extract prescription from Dora answer
- Build and validate prescriptions
- Get drug alternatives
- Sign prescriptions
- Send to pharmacy/EMR
- Template management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from src.prescription import (
    PrescriptionService,
    Prescription,
    EPrescription,
    PrescriptionItem,
    PatientInfo,
    DoctorInfo,
    PrescriptionValidationResult,
    DrugAlternative,
    DigitalCertificate,
    TemplateLibrary,
)
from src.prescription.signature import DigitalCertificate as DigitalCertClass
from datetime import datetime, timedelta


# Initialize router
router = APIRouter(prefix="/api/prescription", tags=["prescription"])

# Initialize service (singleton)
_prescription_service = None


def get_prescription_service() -> PrescriptionService:
    """Get prescription service singleton."""
    global _prescription_service
    if _prescription_service is None:
        _prescription_service = PrescriptionService()
    return _prescription_service


# Request/Response models

class ExtractRequest(BaseModel):
    """Request to extract prescription from Dora answer."""
    answer_text: str = Field(..., description="Dora AI answer text")
    dora_answer_id: str = Field(..., description="Dora answer ID")
    patient: PatientInfo
    doctor: DoctorInfo
    diagnosis: Optional[str] = None
    advice: Optional[str] = None
    use_llm: bool = Field(default=True, description="Use LLM for extraction")
    min_confidence: float = Field(default=0.7, ge=0, le=1)


class ExtractResponse(BaseModel):
    """Response from extraction."""
    success: bool
    prescription: Optional[Prescription] = None
    validation: Optional[PrescriptionValidationResult] = None
    alternatives: Optional[List[DrugAlternative]] = None
    preview: Optional[str] = None
    requires_confirmation: bool = Field(default=True)
    ai_confidence: Optional[float] = None
    extracted_count: int = Field(default=0)
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    """Request to validate prescription."""
    prescription: Prescription


class AlternativesRequest(BaseModel):
    """Request to get drug alternatives."""
    drug_name: str
    strength: str
    quantity: int
    max_alternatives: int = Field(default=5, le=10)


class SignRequest(BaseModel):
    """Request to sign prescription."""
    prescription: Prescription
    certificate_id: str
    pin: Optional[str] = None


class PharmacyRequest(BaseModel):
    """Request to send to pharmacy."""
    prescription_id: str
    pharmacy_id: str
    delivery_method: str = Field(default="pickup", regex="^(pickup|delivery)$")
    delivery_address: Optional[str] = None


class EMRRequest(BaseModel):
    """Request to send to EMR."""
    prescription_id: str
    encounter_id: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    """Request to create custom template."""
    name: str
    items: List[PrescriptionItem]
    doctor_id: str
    description: Optional[str] = None
    specialty: Optional[str] = None
    condition: Optional[str] = None
    advice: Optional[str] = None
    tags: Optional[List[str]] = None


# Endpoints

@router.post("/extract", response_model=ExtractResponse)
async def extract_prescription(
    request: ExtractRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """
    Extract prescription from Dora AI answer.

    This is the MAGIC one-tap prescription endpoint!
    """
    try:
        result = service.generate_from_dora_answer(
            answer_text=request.answer_text,
            dora_answer_id=request.dora_answer_id,
            patient=request.patient,
            doctor=request.doctor,
            diagnosis=request.diagnosis,
            advice=request.advice,
            use_llm=request.use_llm,
            min_confidence=request.min_confidence,
        )

        return ExtractResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_prescription(
    patient: PatientInfo,
    doctor: DoctorInfo,
    items: List[PrescriptionItem],
    diagnosis: Optional[str] = None,
    advice: Optional[str] = None,
):
    """Build prescription from items."""
    from src.prescription import PrescriptionBuilder

    try:
        builder = PrescriptionBuilder()
        prescription = (
            builder
            .with_patient(patient)
            .with_doctor(doctor)
            .add_items(items)
            .with_diagnosis(diagnosis)
            .with_advice(advice)
            .build()
        )

        return {"success": True, "prescription": prescription}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=PrescriptionValidationResult)
async def validate_prescription(
    request: ValidateRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Validate prescription for safety."""
    try:
        validation = service.validate_prescription(request.prescription)
        return validation

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alternatives/{drug_name}")
async def get_drug_alternatives(
    drug_name: str,
    strength: str,
    quantity: int = 30,
    max_alternatives: int = 5,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Get alternative drugs for cost savings."""
    from src.prescription.models import (
        PrescriptionItem, Dosage, DosageForm, Frequency, RouteOfAdministration
    )

    try:
        # Create temporary item for alternatives lookup
        item = PrescriptionItem(
            drug_name=drug_name,
            strength=strength,
            dosage_form=DosageForm.TABLET,
            dosage=Dosage(
                dose="1 tablet",
                frequency=Frequency.OD,
                duration_days=30,
                route=RouteOfAdministration.ORAL,
            ),
            quantity=quantity,
            quantity_unit="tablets",
            item_sequence=1,
        )

        alternatives = service.alternatives.suggest_alternatives(
            item,
            max_alternatives=max_alternatives
        )

        return {
            "success": True,
            "drug": drug_name,
            "alternatives": alternatives,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates():
    """List all available prescription templates."""
    try:
        templates = TemplateLibrary.list_templates()
        return {
            "success": True,
            "templates": templates,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}")
async def get_template(template_name: str):
    """Get specific prescription template."""
    try:
        template = TemplateLibrary.get_template(template_name)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")

        return {
            "success": True,
            "template": template,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def create_custom_template(
    request: TemplateCreateRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Create custom prescription template."""
    try:
        template = service.template_manager.create_template(
            name=request.name,
            items=request.items,
            doctor_id=request.doctor_id,
            description=request.description,
            specialty=request.specialty,
            condition=request.condition,
            advice=request.advice,
            tags=request.tags,
        )

        return {
            "success": True,
            "template_id": template.id,
            "template": template,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sign")
async def sign_prescription(
    request: SignRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """
    Digitally sign prescription to create e-prescription.

    Requires valid digital certificate.
    """
    try:
        # Get certificate (in production, retrieve from secure storage)
        # For demo, create mock certificate
        certificate = DigitalCertClass(
            certificate_id=request.certificate_id,
            doctor_id=request.prescription.doctor.doctor_id,
            doctor_name=request.prescription.doctor.name,
            registration_number=request.prescription.doctor.registration_number,
            issuer="India Digital Health Authority",
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            public_key="PUBLIC_KEY_DEMO",
            private_key="PRIVATE_KEY_DEMO",
        )

        e_prescription = service.sign_prescription(
            request.prescription,
            certificate,
            pin=request.pin,
        )

        return {
            "success": True,
            "e_prescription": e_prescription,
            "signature_id": e_prescription.signature.signature_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def generate_pdf(
    prescription: Prescription,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Generate PDF prescription."""
    from fastapi.responses import Response

    try:
        pdf_bytes = service.format_prescription(prescription, format_type="pdf")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=prescription_{prescription.prescription_id}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pharmacy")
async def send_to_pharmacy(
    request: PharmacyRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Send prescription to pharmacy."""
    try:
        # In production, retrieve prescription from database
        # For demo, we'll need the full prescription object
        raise HTTPException(
            status_code=501,
            detail="Not implemented - requires prescription database integration"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emr")
async def send_to_emr(
    request: EMRRequest,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Send prescription to EMR system."""
    try:
        # In production, retrieve prescription from database and send to EMR
        # For demo, we'll need the full prescription object
        raise HTTPException(
            status_code=501,
            detail="Not implemented - requires prescription database and EMR integration"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pharmacy/nearby")
async def find_nearby_pharmacies(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    home_delivery: Optional[bool] = None,
    service: PrescriptionService = Depends(get_prescription_service)
):
    """Find nearby pharmacies."""
    try:
        filters = {}
        if home_delivery is not None:
            filters['home_delivery'] = home_delivery

        pharmacies = service.pharmacy_service.find_nearby_pharmacies(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            filters=filters if filters else None,
        )

        return {
            "success": True,
            "count": len(pharmacies),
            "pharmacies": [p.to_dict() for p in pharmacies],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/format")
async def format_prescription(
    prescription: Prescription,
    format_type: str = "text",
    service: PrescriptionService = Depends(get_prescription_service)
):
    """
    Format prescription in various formats.

    Supported formats: text, json, emr, whatsapp
    """
    try:
        if format_type not in ["text", "json", "emr", "whatsapp"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format type. Supported: text, json, emr, whatsapp"
            )

        formatted = service.format_prescription(prescription, format_type=format_type)

        return {
            "success": True,
            "format": format_type,
            "output": formatted,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "prescription",
        "version": "1.0.0",
    }


# Export router
__all__ = ['router']
