"""
Rich answer formatting API endpoints.

This module provides FastAPI endpoints for transforming RAG query results
into richly formatted medical answers with evidence grading, tables, and more.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..formatting import (
    FormattingService,
    format_query_response,
    RichAnswer,
    EvidenceLevel,
    create_evidence_badge,
    create_aspirin_card,
    create_chads2vasc_result,
    create_wells_dvt_result,
    create_gcs_result,
    create_chest_pain_algorithm,
    create_sepsis_algorithm,
    create_stroke_algorithm,
    create_anaphylaxis_algorithm,
)
from ..formatting.renderer import render_to_format


router = APIRouter(prefix="/format", tags=["formatting"])


# Request/Response Models
class FormatQueryRequest(BaseModel):
    """Request to format a query response."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer text")
    retrieved_docs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved documents with metadata"
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Model confidence")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FormatDrugRequest(BaseModel):
    """Request to format a drug information query."""

    drug_name: str = Field(..., description="Name of the drug")
    answer: str = Field(..., description="Generated answer text")
    retrieved_docs: List[Dict[str, Any]] = Field(
        default_factory=list, description="Retrieved documents"
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Model confidence")


class CalculatorResultRequest(BaseModel):
    """Request for calculator result formatting."""

    calculator_name: str = Field(..., description="Calculator name")
    result_value: str = Field(..., description="Calculated value")
    interpretation: str = Field(..., description="Clinical interpretation")
    inputs: Dict[str, Any] = Field(..., description="Input parameters")
    risk_category: Optional[str] = Field(None, description="Risk category")
    recommendations: Optional[List[str]] = Field(None, description="Clinical recommendations")
    context: Optional[str] = Field(None, description="Additional context")


class RenderRequest(BaseModel):
    """Request to render formatted answer in specific format."""

    answer: Dict[str, Any] = Field(..., description="Rich answer data")
    format: str = Field(default="json", description="Output format (json, markdown, html, react)")


class FormatResponse(BaseModel):
    """Response containing formatted answer."""

    success: bool = Field(default=True)
    data: Dict[str, Any] = Field(..., description="Formatted answer data")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Endpoints


@router.post("/query", response_model=FormatResponse)
async def format_query(request: FormatQueryRequest):
    """
    Format a RAG query response into rich answer.

    This endpoint transforms plain text answers into structured, formatted
    content with evidence badges, sections, and citations.

    Args:
        request: Format query request

    Returns:
        Formatted rich answer
    """
    try:
        # Create formatting service
        service = FormattingService()

        # Format the response
        rich_answer = service.format_rag_response(
            query=request.query,
            raw_answer=request.answer,
            retrieved_docs=request.retrieved_docs,
            confidence_score=request.confidence_score,
            metadata=request.metadata,
        )

        # Convert to dict
        answer_dict = rich_answer.model_dump(mode="json")

        return FormatResponse(data=answer_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Formatting failed: {str(e)}")


@router.post("/drug", response_model=FormatResponse)
async def format_drug_query(request: FormatDrugRequest):
    """
    Format a drug information query.

    Specialized formatting for medication queries that creates drug cards,
    dosing tables, and structured sections.

    Args:
        request: Drug format request

    Returns:
        Formatted drug answer
    """
    try:
        service = FormattingService()

        rich_answer = service.format_drug_query(
            drug_name=request.drug_name,
            raw_answer=request.answer,
            retrieved_docs=request.retrieved_docs,
            confidence_score=request.confidence_score,
        )

        answer_dict = rich_answer.model_dump(mode="json")

        return FormatResponse(data=answer_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drug formatting failed: {str(e)}")


@router.post("/calculator", response_model=FormatResponse)
async def format_calculator_result(request: CalculatorResultRequest):
    """
    Format a calculator result.

    Creates formatted output for clinical calculators with recommendations
    and risk stratification.

    Args:
        request: Calculator result request

    Returns:
        Formatted calculator answer
    """
    try:
        from ..formatting.cards import CardBuilder

        # Create calculator result
        calc_result = CardBuilder.create_calculator_result_card(
            calculator_name=request.calculator_name,
            result_value=request.result_value,
            interpretation=request.interpretation,
            inputs=request.inputs,
            risk_category=request.risk_category,
            recommendations=request.recommendations,
        )

        # Format as rich answer
        service = FormattingService()
        rich_answer = service.format_calculator_result(
            calculator_name=request.calculator_name,
            result=calc_result,
            context=request.context,
        )

        answer_dict = rich_answer.model_dump(mode="json")

        return FormatResponse(data=answer_dict)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculator formatting failed: {str(e)}")


@router.post("/render", response_model=Dict[str, Any])
async def render_answer(request: RenderRequest):
    """
    Render formatted answer to specific output format.

    Converts rich answer data to markdown, HTML, React components, etc.

    Args:
        request: Render request with format

    Returns:
        Rendered output
    """
    try:
        # Reconstruct RichAnswer from dict
        from ..formatting.models import RichAnswer

        rich_answer = RichAnswer(**request.answer)

        # Render to requested format
        rendered = render_to_format(rich_answer, request.format)

        return {"format": request.format, "content": rendered}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.get("/algorithms", response_model=Dict[str, Any])
async def get_algorithms():
    """
    Get available clinical algorithms.

    Returns:
        Dictionary of available decision trees
    """
    try:
        algorithms = {
            "chest_pain": create_chest_pain_algorithm().model_dump(mode="json"),
            "sepsis": create_sepsis_algorithm().model_dump(mode="json"),
            "stroke": create_stroke_algorithm().model_dump(mode="json"),
            "anaphylaxis": create_anaphylaxis_algorithm().model_dump(mode="json"),
        }

        return {"algorithms": algorithms}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get algorithms: {str(e)}")


@router.get("/calculators/chads2vasc")
async def calculate_chads2vasc(
    age: int,
    sex: str,
    chf: bool = False,
    hypertension: bool = False,
    stroke_tia: bool = False,
    vascular_disease: bool = False,
    diabetes: bool = False,
):
    """
    Calculate CHA2DS2-VASc score.

    Args:
        age: Patient age
        sex: Patient sex (M/F)
        chf: Congestive heart failure
        hypertension: Hypertension
        stroke_tia: Prior stroke/TIA
        vascular_disease: Vascular disease
        diabetes: Diabetes

    Returns:
        Calculator result with recommendations
    """
    try:
        result = create_chads2vasc_result(
            age=age,
            sex=sex,
            chf=chf,
            hypertension=hypertension,
            stroke_tia=stroke_tia,
            vascular_disease=vascular_disease,
            diabetes=diabetes,
        )

        return result.model_dump(mode="json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/calculators/wells-dvt")
async def calculate_wells_dvt(
    active_cancer: bool = False,
    paralysis_paresis: bool = False,
    bedridden_recent_surgery: bool = False,
    localized_tenderness: bool = False,
    entire_leg_swollen: bool = False,
    calf_swelling: bool = False,
    pitting_edema: bool = False,
    collateral_veins: bool = False,
    alternative_diagnosis: bool = False,
):
    """
    Calculate Wells DVT score.

    Returns:
        Calculator result with DVT probability
    """
    try:
        result = create_wells_dvt_result(
            active_cancer=active_cancer,
            paralysis_paresis=paralysis_paresis,
            bedridden_recent_surgery=bedridden_recent_surgery,
            localized_tenderness=localized_tenderness,
            entire_leg_swollen=entire_leg_swollen,
            calf_swelling=calf_swelling,
            pitting_edema=pitting_edema,
            collateral_veins=collateral_veins,
            alternative_diagnosis=alternative_diagnosis,
        )

        return result.model_dump(mode="json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/calculators/gcs")
async def calculate_gcs(
    eye_response: int = Field(..., ge=1, le=4, description="Eye opening (1-4)"),
    verbal_response: int = Field(..., ge=1, le=5, description="Verbal response (1-5)"),
    motor_response: int = Field(..., ge=1, le=6, description="Motor response (1-6)"),
):
    """
    Calculate Glasgow Coma Scale.

    Args:
        eye_response: Eye opening response (1-4)
        verbal_response: Verbal response (1-5)
        motor_response: Motor response (1-6)

    Returns:
        GCS score with interpretation
    """
    try:
        result = create_gcs_result(
            eye_response=eye_response,
            verbal_response=verbal_response,
            motor_response=motor_response,
        )

        return result.model_dump(mode="json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")


@router.get("/drugs/aspirin")
async def get_aspirin_card():
    """
    Get formatted drug card for Aspirin.

    Example endpoint showing drug card generation.

    Returns:
        Aspirin drug card
    """
    try:
        card = create_aspirin_card()
        return card.model_dump(mode="json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drug card: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "formatting",
        "version": "1.0.0",
    }


# Helper function to integrate with main query endpoint


async def format_rag_query(
    query: str, answer: str, retrieved_docs: List[Dict[str, Any]], confidence: float = 0.0
) -> Dict[str, Any]:
    """
    Helper function to format RAG query results.

    This can be called from the main query endpoint to automatically
    format responses.

    Args:
        query: User query
        answer: Generated answer
        retrieved_docs: Retrieved documents
        confidence: Confidence score

    Returns:
        Formatted answer dict
    """
    rich_answer = format_query_response(query, answer, retrieved_docs, confidence)
    return rich_answer.model_dump(mode="json")
