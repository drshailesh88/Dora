"""
Base Calculator Framework for Medical Calculators

This module provides the foundation for all medical calculators in Dora.
Ensures consistency, validation, and proper error handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re


class RiskLevel(Enum):
    """Risk stratification levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class UnitType(Enum):
    """Medical unit types for conversions"""
    WEIGHT_KG = "kg"
    WEIGHT_LB = "lb"
    WEIGHT_G = "g"
    HEIGHT_CM = "cm"
    HEIGHT_M = "m"
    HEIGHT_INCH = "inch"
    VOLUME_ML = "ml"
    VOLUME_L = "L"
    CREATININE_MG_DL = "mg/dL"
    CREATININE_UMOL_L = "μmol/L"
    ALBUMIN_G_DL = "g/dL"
    ALBUMIN_G_L = "g/L"


@dataclass
class CalculatorResult:
    """Standardized result format for all calculators"""
    value: Union[float, int, str, Dict[str, Any]]
    interpretation: str
    risk_level: Optional[RiskLevel] = None
    reference_range: Optional[str] = None
    recommendations: Optional[List[str]] = None
    citations: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "value": self.value,
            "interpretation": self.interpretation,
            "risk_level": self.risk_level.value if self.risk_level else None,
            "reference_range": self.reference_range,
            "recommendations": self.recommendations,
            "citations": self.citations,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class ValidationError(Exception):
    """Custom exception for input validation errors"""
    pass


class UnitConverter:
    """Medical unit conversion utilities"""

    @staticmethod
    def convert_weight(value: float, from_unit: UnitType, to_unit: UnitType) -> float:
        """Convert weight between units"""
        conversions = {
            (UnitType.WEIGHT_KG, UnitType.WEIGHT_LB): lambda x: x * 2.20462,
            (UnitType.WEIGHT_LB, UnitType.WEIGHT_KG): lambda x: x / 2.20462,
            (UnitType.WEIGHT_KG, UnitType.WEIGHT_G): lambda x: x * 1000,
            (UnitType.WEIGHT_G, UnitType.WEIGHT_KG): lambda x: x / 1000,
        }

        if from_unit == to_unit:
            return value

        converter = conversions.get((from_unit, to_unit))
        if not converter:
            raise ValidationError(f"Cannot convert {from_unit} to {to_unit}")

        return converter(value)

    @staticmethod
    def convert_height(value: float, from_unit: UnitType, to_unit: UnitType) -> float:
        """Convert height between units"""
        conversions = {
            (UnitType.HEIGHT_CM, UnitType.HEIGHT_M): lambda x: x / 100,
            (UnitType.HEIGHT_M, UnitType.HEIGHT_CM): lambda x: x * 100,
            (UnitType.HEIGHT_INCH, UnitType.HEIGHT_CM): lambda x: x * 2.54,
            (UnitType.HEIGHT_CM, UnitType.HEIGHT_INCH): lambda x: x / 2.54,
        }

        if from_unit == to_unit:
            return value

        converter = conversions.get((from_unit, to_unit))
        if not converter:
            raise ValidationError(f"Cannot convert {from_unit} to {to_unit}")

        return converter(value)

    @staticmethod
    def convert_creatinine(value: float, from_unit: UnitType, to_unit: UnitType) -> float:
        """Convert creatinine between mg/dL and μmol/L"""
        if from_unit == to_unit:
            return value

        if from_unit == UnitType.CREATININE_MG_DL and to_unit == UnitType.CREATININE_UMOL_L:
            return value * 88.42
        elif from_unit == UnitType.CREATININE_UMOL_L and to_unit == UnitType.CREATININE_MG_DL:
            return value / 88.42
        else:
            raise ValidationError(f"Cannot convert {from_unit} to {to_unit}")


class Calculator(ABC):
    """
    Abstract base class for all medical calculators.

    All calculators must inherit from this class and implement:
    - calculate() method
    - get_schema() method
    """

    def __init__(self):
        self.name: str = self.__class__.__name__
        self.category: str = "general"
        self.description: str = ""
        self.citations: List[str] = []

    @abstractmethod
    def calculate(self, **kwargs) -> CalculatorResult:
        """
        Perform the calculation.

        Args:
            **kwargs: Calculator-specific parameters

        Returns:
            CalculatorResult object

        Raises:
            ValidationError: If input validation fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the input schema for this calculator.

        Returns:
            Dictionary describing required and optional parameters
        """
        pass

    def validate_range(
        self,
        value: Union[float, int],
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        param_name: str = "value",
    ) -> None:
        """Validate that a value is within acceptable range"""
        if min_val is not None and value < min_val:
            raise ValidationError(f"{param_name} must be >= {min_val}, got {value}")
        if max_val is not None and value > max_val:
            raise ValidationError(f"{param_name} must be <= {max_val}, got {value}")

    def validate_required(self, params: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that all required fields are present"""
        missing = [field for field in required_fields if field not in params or params[field] is None]
        if missing:
            raise ValidationError(f"Missing required parameters: {', '.join(missing)}")

    def validate_choice(
        self,
        value: Any,
        choices: List[Any],
        param_name: str = "value",
    ) -> None:
        """Validate that a value is one of the allowed choices"""
        if value not in choices:
            raise ValidationError(f"{param_name} must be one of {choices}, got {value}")


class CalculatorRegistry:
    """Registry for calculator discovery and access"""

    def __init__(self):
        self._calculators: Dict[str, Calculator] = {}

    def register(self, calculator_id: str, calculator: Calculator) -> None:
        """Register a calculator"""
        self._calculators[calculator_id] = calculator

    def get(self, calculator_id: str) -> Optional[Calculator]:
        """Get a calculator by ID"""
        return self._calculators.get(calculator_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered calculators"""
        return [
            {
                "id": calc_id,
                "name": calc.name,
                "category": calc.category,
                "description": calc.description,
            }
            for calc_id, calc in self._calculators.items()
        ]

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all calculators in a specific category"""
        return [
            {
                "id": calc_id,
                "name": calc.name,
                "category": calc.category,
                "description": calc.description,
            }
            for calc_id, calc in self._calculators.items()
            if calc.category == category
        ]


# Global registry instance
registry = CalculatorRegistry()
