"""Drug database API endpoints.

Comprehensive REST API for drug information, interactions, safety checks,
and pricing.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.drugs import (
    DrugService,
    DrugDatabase,
    DrugInteractionChecker,
    DrugSafetyChecker,
    IndianDrugPricing,
    TherapeuticClass,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/drugs", tags=["drugs"])

# Initialize service (will be replaced with dependency injection in production)
drug_service: Optional[DrugService] = None


def get_drug_service() -> DrugService:
    """Get or create drug service instance."""
    global drug_service
    if drug_service is None:
        drug_service = DrugService()
    return drug_service


# Request/Response Models

class DrugSearchRequest(BaseModel):
    """Drug search request."""

    query: str = Field(..., description="Search query (drug name)")
    therapeutic_class: Optional[str] = Field(None, description="Filter by therapeutic class")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class DrugSearchResponse(BaseModel):
    """Drug search response."""

    success: bool
    results: list[dict]
    count: int


class DrugInfoResponse(BaseModel):
    """Drug information response."""

    success: bool
    drug: Optional[dict] = None
    pricing: Optional[dict] = None
    generic_alternatives: list[str] = []
    common_interactions: list[dict] = []
    pregnancy_safety: Optional[dict] = None
    lactation_safety: Optional[dict] = None
    error: Optional[str] = None


class InteractionCheckRequest(BaseModel):
    """Drug interaction check request."""

    drug_ids: list[str] = Field(..., description="List of drug IDs to check")
    drug_names: Optional[list[str]] = Field(None, description="List of drug names (alternative to IDs)")


class InteractionCheckResponse(BaseModel):
    """Drug interaction check response."""

    success: bool
    has_interactions: bool
    interactions: list[dict] = []
    warnings: list[str] = []


class SafetyCheckRequest(BaseModel):
    """Comprehensive safety check request."""

    drug_ids: list[str] = Field(..., description="Drug IDs being prescribed")
    patient_context: Optional[dict] = Field(
        None,
        description="Patient context (pregnancy, lactating, gfr, conditions, allergies, etc.)"
    )


class SafetyCheckResponse(BaseModel):
    """Safety check response."""

    success: bool
    safe: bool
    drug_interactions: list[dict] = []
    pregnancy_warnings: list[str] = []
    lactation_warnings: list[str] = []
    contraindications: list[str] = []
    allergy_warnings: list[str] = []
    renal_warnings: list[str] = []
    hepatic_warnings: list[str] = []
    recommendations: list[str] = []
    alternatives: list[str] = []


class RenalDosingRequest(BaseModel):
    """Renal dosing calculation request."""

    drug_id: str
    gfr: float = Field(..., ge=0, le=200, description="GFR in mL/min/1.73m²")
    current_dose: Optional[str] = None


class PediatricDosingRequest(BaseModel):
    """Pediatric dosing calculation request."""

    drug_id: str
    age_years: Optional[float] = Field(None, ge=0, le=18)
    weight_kg: Optional[float] = Field(None, ge=0, le=150)


class PrescriptionCostRequest(BaseModel):
    """Prescription cost calculation request."""

    prescription: list[dict] = Field(
        ...,
        description="List of prescriptions with drug_id, daily_dose, duration_days"
    )


class PrescriptionCostResponse(BaseModel):
    """Prescription cost response."""

    success: bool
    drug_costs: list[dict] = []
    total_brand_cost: float = 0.0
    total_generic_cost: float = 0.0
    total_savings: float = 0.0
    savings_percent: float = 0.0


# Endpoints

@router.get("/search", response_model=DrugSearchResponse)
async def search_drugs(
    query: str = Query(..., description="Search query"),
    therapeutic_class: Optional[str] = Query(None, description="Filter by class"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search for drugs by name.

    Supports exact match, full-text search, and fuzzy matching.
    """
    try:
        service = get_drug_service()
        results = service.search_drugs(query, therapeutic_class, limit)

        return DrugSearchResponse(
            success=True,
            results=[
                {
                    "drug_id": r.drug_id,
                    "generic_name": r.generic_name,
                    "brand_names": r.brand_names,
                    "therapeutic_class": r.therapeutic_class,
                    "relevance_score": r.relevance_score,
                    "match_type": r.match_type,
                }
                for r in results
            ],
            count=len(results),
        )
    except Exception as e:
        logger.error(f"Drug search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drug_id}", response_model=DrugInfoResponse)
async def get_drug_info(
    drug_id: str,
    include_pricing: bool = Query(True, description="Include pricing"),
    include_interactions: bool = Query(True, description="Include interactions"),
):
    """
    Get comprehensive drug information.

    Returns drug details, pricing, formulations, interactions, and safety information.
    """
    try:
        service = get_drug_service()
        result = service.get_drug_info(drug_id, include_pricing, include_interactions)

        if not result:
            raise HTTPException(status_code=404, detail="Drug not found")

        # Convert to dict
        drug_dict = {
            "id": result.drug.id,
            "generic_name": result.drug.generic_name,
            "brand_names": result.drug.brand_names,
            "indian_brand_names": result.drug.indian_brand_names,
            "therapeutic_class": result.drug.therapeutic_class.value,
            "mechanism_of_action": result.drug.mechanism_of_action,
            "indications": result.drug.indications,
            "contraindications": result.drug.contraindications,
            "common_side_effects": result.drug.common_side_effects,
            "serious_side_effects": result.drug.serious_side_effects,
            "adult_dose": result.drug.adult_dose,
            "max_dose_per_day": result.drug.max_dose_per_day,
            "pregnancy_category": result.drug.pregnancy_category.value,
            "lactation_risk": result.drug.lactation_risk.value,
        }

        # Convert interactions
        interactions = [
            {
                "drug1": i.drug1_name,
                "drug2": i.drug2_name,
                "severity": i.severity.value,
                "mechanism": i.mechanism,
                "clinical_significance": i.clinical_significance,
                "management": i.management_strategy,
            }
            for i in result.common_interactions
        ]

        # Convert safety checks
        pregnancy_safety = None
        if result.pregnancy_safety:
            pregnancy_safety = {
                "safe": result.pregnancy_safety.safe,
                "warnings": result.pregnancy_safety.warnings,
                "contraindications": result.pregnancy_safety.contraindications,
                "recommendations": result.pregnancy_safety.recommendations,
            }

        lactation_safety = None
        if result.lactation_safety:
            lactation_safety = {
                "safe": result.lactation_safety.safe,
                "warnings": result.lactation_safety.warnings,
                "contraindications": result.lactation_safety.contraindications,
                "recommendations": result.lactation_safety.recommendations,
            }

        return DrugInfoResponse(
            success=True,
            drug=drug_dict,
            pricing=result.pricing,
            generic_alternatives=result.generic_alternatives,
            common_interactions=interactions,
            pregnancy_safety=pregnancy_safety,
            lactation_safety=lactation_safety,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interactions", response_model=InteractionCheckResponse)
async def check_interactions(request: InteractionCheckRequest):
    """
    Check for drug-drug interactions.

    Accepts either drug IDs or drug names.
    """
    try:
        service = get_drug_service()

        # Convert drug names to IDs if provided
        drug_ids = request.drug_ids
        if request.drug_names and not drug_ids:
            drug_ids = []
            for name in request.drug_names:
                drug = service.get_drug_by_name(name)
                if drug:
                    drug_ids.append(drug.id)

        if len(drug_ids) < 2:
            return InteractionCheckResponse(
                success=True,
                has_interactions=False,
                interactions=[],
                warnings=["At least 2 drugs required for interaction check"],
            )

        # Get drug names for interaction checker
        drug_names = []
        for drug_id in drug_ids:
            drug = service.db.get_drug(drug_id)
            if drug:
                drug_names.append(drug.generic_name)

        # Check interactions
        interactions = service.interaction_checker.check_multiple(drug_names)

        # Format response
        interaction_dicts = [
            {
                "drug1": i.drug1,
                "drug2": i.drug2,
                "severity": i.severity.value,
                "description": i.description,
                "clinical_effects": i.clinical_effects,
                "management": i.management,
                "source": i.source,
            }
            for i in interactions
        ]

        warnings = [
            service.interaction_checker.format_warning(i) for i in interactions
        ]

        return InteractionCheckResponse(
            success=True,
            has_interactions=len(interactions) > 0,
            interactions=interaction_dicts,
            warnings=warnings,
        )

    except Exception as e:
        logger.error(f"Interaction check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drug_id}/pregnancy", response_model=dict)
async def get_pregnancy_safety(
    drug_id: str,
    trimester: Optional[str] = Query(None, description="first, second, or third"),
):
    """
    Get pregnancy safety information for a drug.
    """
    try:
        service = get_drug_service()
        result = service.safety_checker.check_pregnancy_safety(drug_id, trimester)

        return {
            "success": True,
            "drug_id": drug_id,
            "safe": result.safe,
            "warnings": result.warnings,
            "contraindications": result.contraindications,
            "recommendations": result.recommendations,
            "alternatives": result.alternatives,
        }

    except Exception as e:
        logger.error(f"Pregnancy safety check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drug_id}/lactation", response_model=dict)
async def get_lactation_safety(drug_id: str):
    """
    Get lactation safety information for a drug.
    """
    try:
        service = get_drug_service()
        result = service.safety_checker.check_lactation_safety(drug_id)

        return {
            "success": True,
            "drug_id": drug_id,
            "safe": result.safe,
            "warnings": result.warnings,
            "contraindications": result.contraindications,
            "recommendations": result.recommendations,
            "alternatives": result.alternatives,
        }

    except Exception as e:
        logger.error(f"Lactation safety check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dosing/renal", response_model=dict)
async def calculate_renal_dose(request: RenalDosingRequest):
    """
    Calculate renal dose adjustment based on GFR.
    """
    try:
        service = get_drug_service()
        result = service.safety_checker.calculate_renal_dose(
            request.drug_id, request.gfr, request.current_dose
        )

        return {
            "success": True,
            "drug_id": request.drug_id,
            "gfr": request.gfr,
            "safe": result.safe,
            "warnings": result.warnings,
            "contraindications": result.contraindications,
            "recommendations": result.recommendations,
        }

    except Exception as e:
        logger.error(f"Renal dosing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dosing/pediatric", response_model=dict)
async def calculate_pediatric_dose(request: PediatricDosingRequest):
    """
    Calculate pediatric dose based on age and/or weight.
    """
    try:
        service = get_drug_service()
        result = service.safety_checker.calculate_pediatric_dose(
            request.drug_id, request.age_years, request.weight_kg
        )

        return {
            "success": True,
            "drug_id": request.drug_id,
            "age_years": request.age_years,
            "weight_kg": request.weight_kg,
            "safe": result.safe,
            "warnings": result.warnings,
            "contraindications": result.contraindications,
            "recommendations": result.recommendations,
        }

    except Exception as e:
        logger.error(f"Pediatric dosing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drug_id}/alternatives", response_model=dict)
async def get_drug_alternatives(
    drug_id: str,
    reason: str = Query("generic", description="Reason: generic, pregnancy, lactation, cost"),
):
    """
    Get alternative drugs (generic, pregnancy-safe, etc.).
    """
    try:
        service = get_drug_service()
        alternatives = service.get_alternatives(drug_id, reason)

        return {
            "success": True,
            "drug_id": drug_id,
            "reason": reason,
            "alternatives": alternatives,
        }

    except Exception as e:
        logger.error(f"Get alternatives error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-check", response_model=SafetyCheckResponse)
async def comprehensive_safety_check(request: SafetyCheckRequest):
    """
    Comprehensive prescription safety check.

    Checks interactions, pregnancy, lactation, renal, hepatic, contraindications, and allergies.
    """
    try:
        service = get_drug_service()
        result = service.check_prescription_safety(
            request.drug_ids, request.patient_context
        )

        # Convert interactions to dict
        interactions = [
            {
                "drug1": i.drug1_name,
                "drug2": i.drug2_name,
                "severity": i.severity.value,
                "mechanism": i.mechanism,
                "clinical_significance": i.clinical_significance,
                "management": i.management_strategy,
            }
            for i in result.drug_interactions
        ]

        return SafetyCheckResponse(
            success=True,
            safe=result.safe,
            drug_interactions=interactions,
            pregnancy_warnings=result.pregnancy_warnings,
            lactation_warnings=result.lactation_warnings,
            contraindications=result.contraindications,
            allergy_warnings=result.allergy_warnings,
            renal_warnings=result.renal_warnings,
            hepatic_warnings=result.hepatic_warnings,
            recommendations=result.recommendations,
            alternatives=result.alternatives,
        )

    except Exception as e:
        logger.error(f"Safety check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prescription/cost", response_model=PrescriptionCostResponse)
async def calculate_prescription_cost(request: PrescriptionCostRequest):
    """
    Calculate total prescription cost with brand vs generic comparison.
    """
    try:
        service = get_drug_service()
        result = service.calculate_prescription_cost(request.prescription)

        return PrescriptionCostResponse(
            success=True,
            drug_costs=result["drug_costs"],
            total_brand_cost=result["total_brand_cost"],
            total_generic_cost=result["total_generic_cost"],
            total_savings=result["total_savings"],
            savings_percent=result["savings_percent"],
        )

    except Exception as e:
        logger.error(f"Prescription cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drug_id}/pricing", response_model=dict)
async def get_drug_pricing(
    drug_id: str,
    formulation: Optional[str] = Query(None),
):
    """
    Get drug pricing information including brand vs generic comparison.
    """
    try:
        service = get_drug_service()

        # Get price comparison
        comparison = service.pricing.compare_generic_vs_brand(drug_id, formulation)

        if not comparison:
            raise HTTPException(status_code=404, detail="Pricing information not available")

        # Get pharmacy prices
        pharmacy_prices = service.pricing.get_pharmacy_prices(drug_id, formulation)

        # Get NLEM status
        nlem_status = service.pricing.get_nlem_status(drug_id)

        return {
            "success": True,
            "drug_id": drug_id,
            "drug_name": comparison.drug_name,
            "brand_price": comparison.brand_price,
            "generic_price": comparison.generic_price,
            "savings_inr": comparison.savings_inr,
            "savings_percent": comparison.savings_percent,
            "generic_alternatives": comparison.generic_alternatives,
            "pharmacy_prices": pharmacy_prices,
            "nlem_status": nlem_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pricing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/database", response_model=dict)
async def get_database_stats():
    """
    Get database statistics.
    """
    try:
        service = get_drug_service()
        stats = service.get_statistics()

        return {
            "success": True,
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
