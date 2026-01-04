"""
Calculator API Endpoints

FastAPI endpoints for medical calculator access.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import calculator registry
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calculators import registry, ValidationError, CalculatorResult


# API Router
router = APIRouter(prefix="/api/v1/calculators", tags=["calculators"])


# Pydantic Models
class CalculatorListItem(BaseModel):
    """Calculator list item"""
    id: str = Field(..., description="Calculator unique identifier")
    name: str = Field(..., description="Calculator name")
    category: str = Field(..., description="Calculator category")
    description: str = Field(..., description="Calculator description")


class CalculatorSchema(BaseModel):
    """Calculator schema response"""
    id: str = Field(..., description="Calculator unique identifier")
    name: str = Field(..., description="Calculator name")
    category: str = Field(..., description="Calculator category")
    description: str = Field(..., description="Calculator description")
    parameters: Dict[str, Any] = Field(..., description="Input parameter schema")
    citations: List[str] = Field(default_factory=list, description="References")


class CalculationRequest(BaseModel):
    """Calculation request"""
    parameters: Dict[str, Any] = Field(..., description="Calculation parameters")


class CalculationResponse(BaseModel):
    """Calculation response"""
    calculator_id: str = Field(..., description="Calculator used")
    result: Dict[str, Any] = Field(..., description="Calculation result")
    timestamp: str = Field(..., description="Calculation timestamp")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")


# Endpoints

@router.get(
    "",
    response_model=List[CalculatorListItem],
    summary="List all calculators",
    description="Returns a list of all available medical calculators"
)
async def list_calculators(category: Optional[str] = None) -> List[CalculatorListItem]:
    """
    List all calculators or filter by category.

    Args:
        category: Optional category filter (cardiovascular, renal, hepatic, pulmonary,
                 endocrine_metabolic, neurology, obstetrics, general)

    Returns:
        List of available calculators
    """
    if category:
        calculators = registry.get_by_category(category)
    else:
        calculators = registry.list_all()

    return [
        CalculatorListItem(
            id=calc["id"],
            name=calc["name"],
            category=calc["category"],
            description=calc["description"]
        )
        for calc in calculators
    ]


@router.get(
    "/categories",
    response_model=List[str],
    summary="List calculator categories",
    description="Returns all available calculator categories"
)
async def list_categories() -> List[str]:
    """
    Get all calculator categories.

    Returns:
        List of category names
    """
    categories = set()
    for calc in registry.list_all():
        categories.add(calc["category"])
    return sorted(list(categories))


@router.get(
    "/{calculator_id}",
    response_model=CalculatorSchema,
    summary="Get calculator schema",
    description="Returns detailed schema and parameter information for a specific calculator"
)
async def get_calculator_schema(calculator_id: str) -> CalculatorSchema:
    """
    Get calculator schema and metadata.

    Args:
        calculator_id: Calculator identifier

    Returns:
        Calculator schema with input parameters

    Raises:
        HTTPException: If calculator not found
    """
    calculator = registry.get(calculator_id)

    if not calculator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculator '{calculator_id}' not found"
        )

    schema = calculator.get_schema()

    return CalculatorSchema(
        id=calculator_id,
        name=calculator.name,
        category=calculator.category,
        description=calculator.description,
        parameters=schema.get("parameters", {}),
        citations=calculator.citations
    )


@router.post(
    "/{calculator_id}/calculate",
    response_model=CalculationResponse,
    summary="Perform calculation",
    description="Executes a calculation using the specified calculator",
    responses={
        200: {"description": "Calculation successful"},
        400: {"description": "Invalid parameters", "model": ErrorResponse},
        404: {"description": "Calculator not found", "model": ErrorResponse},
    }
)
async def calculate(calculator_id: str, request: CalculationRequest) -> CalculationResponse:
    """
    Perform a medical calculation.

    Args:
        calculator_id: Calculator identifier
        request: Calculation parameters

    Returns:
        Calculation result with interpretation and recommendations

    Raises:
        HTTPException: If calculator not found or parameters invalid
    """
    from datetime import datetime

    calculator = registry.get(calculator_id)

    if not calculator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculator '{calculator_id}' not found"
        )

    try:
        # Perform calculation
        result: CalculatorResult = calculator.calculate(**request.parameters)

        # Convert to response
        return CalculationResponse(
            calculator_id=calculator_id,
            result=result.to_dict(),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}"
        )


@router.get(
    "/{calculator_id}/examples",
    response_model=Dict[str, Any],
    summary="Get example calculations",
    description="Returns example parameter sets for a calculator"
)
async def get_calculator_examples(calculator_id: str) -> Dict[str, Any]:
    """
    Get example calculations for a calculator.

    Args:
        calculator_id: Calculator identifier

    Returns:
        Example parameter sets

    Raises:
        HTTPException: If calculator not found
    """
    calculator = registry.get(calculator_id)

    if not calculator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculator '{calculator_id}' not found"
        )

    # Define examples for common calculators
    examples = {
        "bmi": [
            {
                "name": "Normal weight",
                "parameters": {"weight": 70, "height": 175, "weight_unit": "kg", "height_unit": "cm"}
            },
            {
                "name": "Overweight",
                "parameters": {"weight": 90, "height": 175, "weight_unit": "kg", "height_unit": "cm"}
            }
        ],
        "egfr_ckd_epi": [
            {
                "name": "Normal renal function",
                "parameters": {"creatinine": 1.0, "age": 50, "sex": "male"}
            },
            {
                "name": "CKD Stage 3",
                "parameters": {"creatinine": 2.0, "age": 70, "sex": "female"}
            }
        ],
        "cha2ds2_vasc": [
            {
                "name": "Low risk",
                "parameters": {
                    "age": 55,
                    "sex": "male",
                    "congestive_heart_failure": False,
                    "hypertension": False,
                    "stroke_tia_thromboembolism": False,
                    "vascular_disease": False,
                    "diabetes": False
                }
            },
            {
                "name": "High risk",
                "parameters": {
                    "age": 75,
                    "sex": "female",
                    "congestive_heart_failure": True,
                    "hypertension": True,
                    "stroke_tia_thromboembolism": False,
                    "vascular_disease": False,
                    "diabetes": True
                }
            }
        ]
    }

    return {
        "calculator_id": calculator_id,
        "examples": examples.get(calculator_id, [
            {
                "name": "Example",
                "note": "No predefined examples available. Check schema for parameter details."
            }
        ])
    }


# Health check endpoint
@router.get(
    "/health",
    summary="Health check",
    description="Returns API health status"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Health status and calculator count
    """
    from calculators import TOTAL_CALCULATORS, CALCULATOR_COUNTS

    return {
        "status": "healthy",
        "service": "Medical Calculators API",
        "version": "1.0.0",
        "total_calculators": TOTAL_CALCULATORS,
        "calculators_by_category": CALCULATOR_COUNTS
    }


# Include router in main app with:
# from src.api.calculators import router as calculator_router
# app.include_router(calculator_router)
