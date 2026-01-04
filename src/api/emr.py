"""EMR API endpoints for patient data and clinical decision support."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.emr import (
    ClinicalAlert,
    FeedbackType,
    Order,
    OutcomeType,
    Patient,
    RecommendationFeedback,
    get_emr_service,
)

router = APIRouter(prefix="/api/emr", tags=["EMR Integration"])


# ==================== Response Models ====================


class PatientInfoResponse(BaseModel):
    """Patient information response."""

    patient: Patient


class PatientContextResponse(BaseModel):
    """Patient context response."""

    patient_id: int
    context: str
    alerts: list[ClinicalAlert]


class MedicationsResponse(BaseModel):
    """Medications response."""

    patient_id: int
    medications: list[dict]


class AllergiesResponse(BaseModel):
    """Allergies response."""

    patient_id: int
    allergies: list[dict]


class LabsResponse(BaseModel):
    """Labs response."""

    patient_id: int
    labs: list[dict]


class AlertsResponse(BaseModel):
    """Clinical alerts response."""

    patient_id: int
    alerts: list[ClinicalAlert]


class OrderRequest(BaseModel):
    """Order creation request."""

    patient_id: int
    order: Order


class OrderResponse(BaseModel):
    """Order creation response."""

    success: bool
    order: Optional[Order] = None
    alerts: list[ClinicalAlert]


class FeedbackRequest(BaseModel):
    """Feedback submission request."""

    patient_id: int
    query: str
    recommendation: str
    recommendation_type: str = "general"
    feedback_type: FeedbackType
    action_taken: str
    rationale: Optional[str] = None
    outcome: Optional[OutcomeType] = None
    outcome_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""

    success: bool
    feedback_id: Optional[int] = None


class SyncStatusResponse(BaseModel):
    """Sync status response."""

    offline_mode: bool
    cached_patients: int
    sync_stats: dict


# ==================== Endpoints ====================


@router.get("/patient/mrn/{mrn}", response_model=PatientInfoResponse)
async def get_patient_by_mrn(mrn: str):
    """
    Get patient information by MRN.

    Args:
        mrn: Medical Record Number

    Returns:
        Patient information
    """
    emr_service = get_emr_service(use_mock=True)  # Using mock for now

    async with emr_service.emr_client as client:
        patient = await client.get_patient(mrn)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientInfoResponse(patient=patient)


@router.get("/patient/{patient_id}", response_model=PatientInfoResponse)
async def get_patient_by_id(patient_id: int):
    """
    Get patient information by ID.

    Args:
        patient_id: Patient ID

    Returns:
        Patient information
    """
    emr_service = get_emr_service(use_mock=True)

    async with emr_service.emr_client as client:
        patient = await client.get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientInfoResponse(patient=patient)


@router.get("/patient/{patient_id}/context", response_model=PatientContextResponse)
async def get_patient_context(
    patient_id: int,
    query: str = Query(..., description="Query to contextualize"),
):
    """
    Get patient context for a query.

    Args:
        patient_id: Patient ID
        query: Query string

    Returns:
        Patient context and alerts
    """
    emr_service = get_emr_service(use_mock=True)

    context = await emr_service.get_patient_context_for_query(
        patient_id=patient_id,
        query=query,
    )

    if not context:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or context unavailable",
        )

    alerts = await emr_service.check_clinical_alerts(patient_id)

    return PatientContextResponse(
        patient_id=patient_id,
        context=context,
        alerts=alerts,
    )


@router.get("/patient/{patient_id}/medications", response_model=MedicationsResponse)
async def get_patient_medications(patient_id: int):
    """
    Get patient's current medications.

    Args:
        patient_id: Patient ID

    Returns:
        List of medications
    """
    emr_service = get_emr_service(use_mock=True)

    async with emr_service.emr_client as client:
        medications = await client.get_current_medications(patient_id)

    return MedicationsResponse(
        patient_id=patient_id,
        medications=[med.model_dump() for med in medications],
    )


@router.get("/patient/{patient_id}/allergies", response_model=AllergiesResponse)
async def get_patient_allergies(patient_id: int):
    """
    Get patient's allergies.

    Args:
        patient_id: Patient ID

    Returns:
        List of allergies
    """
    emr_service = get_emr_service(use_mock=True)

    async with emr_service.emr_client as client:
        allergies = await client.get_allergies(patient_id)

    return AllergiesResponse(
        patient_id=patient_id,
        allergies=[allergy.model_dump() for allergy in allergies],
    )


@router.get("/patient/{patient_id}/labs", response_model=LabsResponse)
async def get_patient_labs(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get patient's lab results.

    Args:
        patient_id: Patient ID
        limit: Max results

    Returns:
        List of lab results
    """
    emr_service = get_emr_service(use_mock=True)

    async with emr_service.emr_client as client:
        labs = await client.get_lab_results(patient_id, limit=limit)

    return LabsResponse(
        patient_id=patient_id,
        labs=[lab.model_dump() for lab in labs],
    )


@router.get("/patient/{patient_id}/alerts", response_model=AlertsResponse)
async def get_clinical_alerts(
    patient_id: int,
    proposed_medication: Optional[str] = Query(None),
):
    """
    Get clinical decision support alerts.

    Args:
        patient_id: Patient ID
        proposed_medication: Medication being considered

    Returns:
        List of clinical alerts
    """
    emr_service = get_emr_service(use_mock=True)

    alerts = await emr_service.check_clinical_alerts(
        patient_id=patient_id,
        proposed_medication=proposed_medication,
    )

    return AlertsResponse(
        patient_id=patient_id,
        alerts=alerts,
    )


@router.post("/patient/{patient_id}/note")
async def create_clinical_note(
    patient_id: int,
    note_text: str,
):
    """
    Push clinical note to EMR.

    Args:
        patient_id: Patient ID
        note_text: Note content

    Returns:
        Success status
    """
    emr_service = get_emr_service(use_mock=True)

    from src.emr.models import ClinicalNote

    note = ClinicalNote(
        patient_id=patient_id,
        note_type="progress",
        full_note=note_text,
        author="Dora AI",
    )

    success = await emr_service.sync_manager.push_clinical_note(
        patient_id=patient_id,
        note=note,
    )

    return {"success": success}


@router.post("/patient/{patient_id}/order", response_model=OrderResponse)
async def create_order(request: OrderRequest):
    """
    Create clinical order (medication, lab, imaging).

    Args:
        request: Order creation request

    Returns:
        Order creation response with alerts
    """
    emr_service = get_emr_service(use_mock=True)

    # Check alerts first
    alerts = await emr_service.check_clinical_alerts(
        patient_id=request.patient_id,
        proposed_medication=(
            request.order.order_name
            if request.order.order_type.value == "medication"
            else None
        ),
    )

    # Check for critical alerts
    critical_alerts = [
        a for a in alerts if a.level.value in ["critical", "fatal"]
    ]

    if critical_alerts:
        return OrderResponse(
            success=False,
            order=None,
            alerts=alerts,
        )

    # Create order
    created_order = await emr_service.create_order(
        patient_id=request.patient_id,
        order=request.order,
    )

    return OrderResponse(
        success=created_order is not None,
        order=created_order,
        alerts=alerts,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on recommendation.

    Args:
        request: Feedback data

    Returns:
        Feedback submission response
    """
    emr_service = get_emr_service(use_mock=True)

    feedback = RecommendationFeedback(
        patient_id=request.patient_id,
        query=request.query,
        recommendation=request.recommendation,
        recommendation_type=request.recommendation_type,
        feedback_type=request.feedback_type,
        action_taken=request.action_taken,
        rationale=request.rationale,
        outcome=request.outcome,
        outcome_notes=request.outcome_notes,
    )

    saved = await emr_service.record_feedback(feedback)

    return FeedbackResponse(
        success=True,
        feedback_id=saved.id,
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """
    Get current EMR sync status.

    Returns:
        Sync status and statistics
    """
    emr_service = get_emr_service(use_mock=True)
    status = emr_service.get_sync_status()

    return SyncStatusResponse(**status)


@router.post("/sync/refresh/{patient_id}")
async def refresh_patient_context(patient_id: int):
    """
    Force refresh patient context from EMR.

    Args:
        patient_id: Patient ID

    Returns:
        Success status
    """
    emr_service = get_emr_service(use_mock=True)

    success = await emr_service.refresh_patient_context(patient_id)

    return {"success": success}


@router.post("/sync/offline-queue")
async def sync_offline_queue():
    """
    Sync pending offline items.

    Returns:
        Sync results
    """
    emr_service = get_emr_service(use_mock=True)

    results = await emr_service.sync_offline_queue()

    return results


@router.get("/search/patients")
async def search_patients(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Search patients by name or MRN.

    Args:
        query: Search query
        limit: Max results

    Returns:
        List of matching patients
    """
    emr_service = get_emr_service(use_mock=True)

    async with emr_service.emr_client as client:
        patients = await client.search_patients(query, limit=limit)

    return {
        "query": query,
        "count": len(patients),
        "patients": [p.model_dump() for p in patients],
    }


@router.get("/prescription-context/{patient_id}")
async def get_prescription_context(
    patient_id: int,
    drug_name: str = Query(...),
):
    """
    Get specialized context for prescription decision.

    Args:
        patient_id: Patient ID
        drug_name: Drug being prescribed

    Returns:
        Context and alerts for prescription
    """
    emr_service = get_emr_service(use_mock=True)

    context, alerts = await emr_service.get_prescription_context(
        patient_id=patient_id,
        drug_name=drug_name,
    )

    return {
        "patient_id": patient_id,
        "drug_name": drug_name,
        "context": context,
        "alerts": [alert.model_dump() for alert in alerts],
    }
