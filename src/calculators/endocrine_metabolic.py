"""
Endocrine and Metabolic Calculators

Collection of endocrine, metabolic, and nutritional calculators.
"""

import math
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError, UnitConverter, UnitType


class BMICalculator(Calculator):
    """
    Body Mass Index (BMI)

    Assesses body weight relative to height.

    Reference: WHO classification
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Body mass index calculation"
        self.citations = ["WHO BMI Classification"]

    def calculate(
        self,
        weight: float,
        height: float,
        weight_unit: str = "kg",
        height_unit: str = "cm",
    ) -> CalculatorResult:
        """
        Calculate BMI.

        Args:
            weight: Body weight
            height: Height
            weight_unit: 'kg' or 'lb'
            height_unit: 'cm', 'm', or 'inch'
        """
        # Convert to kg and meters
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        if height_unit == "cm":
            height_m = UnitConverter.convert_height(height, UnitType.HEIGHT_CM, UnitType.HEIGHT_M)
        elif height_unit == "inch":
            height_m = UnitConverter.convert_height(height, UnitType.HEIGHT_INCH, UnitType.HEIGHT_M)
        else:
            height_m = height

        self.validate_range(weight_kg, 20, 300, "weight")
        self.validate_range(height_m, 0.5, 2.5, "height")

        # BMI = weight(kg) / height(m)²
        bmi = weight_kg / (height_m ** 2)

        # Classification (WHO)
        if bmi < 16.0:
            risk_level = RiskLevel.HIGH
            category = "Severe underweight"
            interpretation = "Severe thinness - health risks"
            recommendations = [
                "Medical evaluation for malnutrition",
                "Nutritional counseling",
                "Screen for eating disorders",
                "Assess for underlying medical conditions"
            ]
        elif bmi < 18.5:
            risk_level = RiskLevel.MODERATE
            category = "Underweight"
            interpretation = "Below healthy weight"
            recommendations = [
                "Nutritional assessment",
                "Increase caloric intake",
                "Rule out underlying causes",
                "Consider dietitian referral"
            ]
        elif bmi < 25:
            risk_level = RiskLevel.LOW
            category = "Normal weight"
            interpretation = "Healthy weight range"
            recommendations = [
                "Maintain current weight",
                "Regular exercise",
                "Balanced diet"
            ]
        elif bmi < 30:
            risk_level = RiskLevel.MODERATE
            category = "Overweight"
            interpretation = "Above healthy weight"
            recommendations = [
                "Weight loss recommended",
                "Diet and exercise counseling",
                "Target 5-10% weight reduction",
                "Screen for metabolic complications"
            ]
        elif bmi < 35:
            risk_level = RiskLevel.HIGH
            category = "Obesity Class I"
            interpretation = "Obesity with increased health risks"
            recommendations = [
                "Weight loss intervention needed",
                "Screen for diabetes, hypertension, dyslipidemia",
                "Structured weight loss program",
                "Consider medications if appropriate"
            ]
        elif bmi < 40:
            risk_level = RiskLevel.HIGH
            category = "Obesity Class II"
            interpretation = "Severe obesity with high health risks"
            recommendations = [
                "Aggressive weight management",
                "Screen for obesity-related complications",
                "Consider bariatric surgery referral",
                "Comprehensive lifestyle intervention"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            category = "Obesity Class III"
            interpretation = "Extreme obesity with very high health risks"
            recommendations = [
                "Urgent weight management",
                "Bariatric surgery evaluation",
                "Intensive medical management",
                "Screen for all obesity-related complications"
            ]

        return CalculatorResult(
            value=round(bmi, 1),
            interpretation=f"{category}: {interpretation}",
            risk_level=risk_level,
            reference_range="18.5-24.9: normal, <18.5: underweight, 25-29.9: overweight, ≥30: obese",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "kg/m²", "category": category}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "weight": {"type": "float", "min": 20, "max": 300, "required": True},
                "height": {"type": "float", "min": 50, "max": 250, "required": True},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
                "height_unit": {"type": "string", "choices": ["cm", "m", "inch"], "default": "cm", "required": False},
            }
        }


class BSACalculator(Calculator):
    """
    Body Surface Area (BSA)

    Calculates body surface area using Mosteller formula.
    Used for chemotherapy dosing and cardiac index calculation.

    Reference: Mosteller RD. NEJM 1987
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Body surface area (Mosteller)"
        self.citations = ["Mosteller RD. N Engl J Med. 1987;317(17):1098"]

    def calculate(
        self,
        weight: float,
        height: float,
        weight_unit: str = "kg",
        height_unit: str = "cm",
    ) -> CalculatorResult:
        """Calculate BSA using Mosteller formula."""
        # Convert to kg and cm
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        if height_unit == "m":
            height_cm = UnitConverter.convert_height(height, UnitType.HEIGHT_M, UnitType.HEIGHT_CM)
        elif height_unit == "inch":
            height_cm = UnitConverter.convert_height(height, UnitType.HEIGHT_INCH, UnitType.HEIGHT_CM)
        else:
            height_cm = height

        self.validate_range(weight_kg, 20, 300, "weight")
        self.validate_range(height_cm, 50, 250, "height")

        # Mosteller formula: BSA = √((height × weight) / 3600)
        bsa = math.sqrt((height_cm * weight_kg) / 3600)

        # Interpretation
        if bsa < 1.5:
            interpretation = "Below average BSA"
        elif bsa <= 2.0:
            interpretation = "Average BSA"
        else:
            interpretation = "Above average BSA"

        return CalculatorResult(
            value=round(bsa, 2),
            interpretation=interpretation,
            risk_level=RiskLevel.LOW,
            reference_range="Average adult: 1.7-2.0 m²",
            recommendations=["Use for chemotherapy dosing", "Cardiac index calculation (CI = CO/BSA)"],
            citations=self.citations,
            metadata={"unit": "m²", "formula": "Mosteller"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "weight": {"type": "float", "required": True},
                "height": {"type": "float", "required": True},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
                "height_unit": {"type": "string", "choices": ["cm", "m", "inch"], "default": "cm", "required": False},
            }
        }


class IdealBodyWeightCalculator(Calculator):
    """
    Ideal Body Weight (IBW)

    Calculates ideal body weight using Devine formula.
    Used for medication dosing and ventilator settings.

    Reference: Devine BJ. Drug Intell Clin Pharm 1974
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Ideal body weight (Devine)"
        self.citations = ["Devine BJ. Drug Intell Clin Pharm. 1974;8:650-655"]

    def calculate(
        self,
        height: float,
        sex: str,
        height_unit: str = "cm",
    ) -> CalculatorResult:
        """
        Calculate ideal body weight.

        Args:
            height: Height
            sex: 'male' or 'female'
            height_unit: 'cm', 'm', or 'inch'
        """
        self.validate_choice(sex, ["male", "female"], "sex")

        # Convert to inches
        if height_unit == "cm":
            height_inch = UnitConverter.convert_height(height, UnitType.HEIGHT_CM, UnitType.HEIGHT_INCH)
        elif height_unit == "m":
            height_cm = UnitConverter.convert_height(height, UnitType.HEIGHT_M, UnitType.HEIGHT_CM)
            height_inch = UnitConverter.convert_height(height_cm, UnitType.HEIGHT_CM, UnitType.HEIGHT_INCH)
        else:
            height_inch = height

        self.validate_range(height_inch, 48, 84, "height")

        # Devine formula
        # Male: IBW = 50 kg + 2.3 kg × (height in inches - 60)
        # Female: IBW = 45.5 kg + 2.3 kg × (height in inches - 60)
        if sex == "male":
            ibw = 50 + 2.3 * (height_inch - 60)
        else:
            ibw = 45.5 + 2.3 * (height_inch - 60)

        # Ensure reasonable range
        ibw = max(30, ibw)

        return CalculatorResult(
            value=round(ibw, 1),
            interpretation="Ideal body weight for medication dosing and ventilator settings",
            risk_level=RiskLevel.LOW,
            reference_range="N/A",
            recommendations=[
                "Use for aminoglycoside dosing",
                "Tidal volume calculation (6 mL/kg IBW)",
                "Not for actual weight goals"
            ],
            citations=self.citations,
            metadata={"unit": "kg", "formula": "Devine"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "height": {"type": "float", "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "height_unit": {"type": "string", "choices": ["cm", "m", "inch"], "default": "cm", "required": False},
            }
        }


class AdjustedBodyWeightCalculator(Calculator):
    """
    Adjusted Body Weight

    Calculates adjusted body weight for obese patients.
    Used for medication dosing in obesity.

    Reference: Standard pharmacokinetic formula
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Adjusted body weight for obesity"
        self.citations = ["Standard pharmacokinetic formula"]

    def calculate(
        self,
        actual_weight: float,
        ideal_weight: float,
        correction_factor: float = 0.4,
    ) -> CalculatorResult:
        """
        Calculate adjusted body weight.

        Args:
            actual_weight: Actual body weight (kg)
            ideal_weight: Ideal body weight (kg)
            correction_factor: Usually 0.4 (40%) for most drugs
        """
        self.validate_range(actual_weight, 20, 300, "actual_weight")
        self.validate_range(ideal_weight, 20, 150, "ideal_weight")
        self.validate_range(correction_factor, 0.2, 0.5, "correction_factor")

        # ABW = IBW + correction_factor × (actual weight - IBW)
        abw = ideal_weight + correction_factor * (actual_weight - ideal_weight)

        if actual_weight <= ideal_weight:
            interpretation = "Actual weight ≤ IBW, use actual weight"
            use_weight = actual_weight
        else:
            interpretation = "Use adjusted body weight for dosing"
            use_weight = abw

        return CalculatorResult(
            value=round(use_weight, 1),
            interpretation=interpretation,
            risk_level=RiskLevel.LOW,
            reference_range="N/A",
            recommendations=[
                "Use for aminoglycoside dosing in obesity",
                "Use for vancomycin dosing in obesity",
                "Correction factor may vary by drug"
            ],
            citations=self.citations,
            metadata={
                "unit": "kg",
                "actual_weight": actual_weight,
                "ideal_weight": ideal_weight,
                "correction_factor": correction_factor
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "actual_weight": {"type": "float", "unit": "kg", "min": 20, "max": 300, "required": True},
                "ideal_weight": {"type": "float", "unit": "kg", "min": 20, "max": 150, "required": True},
                "correction_factor": {"type": "float", "default": 0.4, "min": 0.2, "max": 0.5, "required": False},
            }
        }


class CorrectedCalciumCalculator(Calculator):
    """
    Corrected Calcium

    Adjusts serum calcium for albumin level.

    Reference: Standard formula
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Calcium corrected for albumin"
        self.citations = ["Standard clinical formula"]

    def calculate(
        self,
        total_calcium: float,
        albumin: float,
    ) -> CalculatorResult:
        """
        Calculate corrected calcium.

        Args:
            total_calcium: Total serum calcium (mg/dL)
            albumin: Serum albumin (g/dL)
        """
        self.validate_range(total_calcium, 4, 20, "total_calcium")
        self.validate_range(albumin, 1, 6, "albumin")

        # Corrected Ca = Total Ca + 0.8 × (4.0 - albumin)
        corrected_ca = total_calcium + 0.8 * (4.0 - albumin)

        # Interpretation
        if corrected_ca < 8.5:
            risk_level = RiskLevel.MODERATE
            interpretation = "Hypocalcemia"
            recommendations = [
                "Evaluate for causes (vitamin D deficiency, hypoparathyroidism)",
                "Check PTH, vitamin D levels",
                "Consider calcium supplementation",
                "Monitor for symptoms (paresthesias, tetany)"
            ]
        elif corrected_ca <= 10.5:
            risk_level = RiskLevel.LOW
            interpretation = "Normal calcium"
            recommendations = ["No intervention needed"]
        elif corrected_ca <= 12:
            risk_level = RiskLevel.MODERATE
            interpretation = "Mild hypercalcemia"
            recommendations = [
                "Evaluate for causes (hyperparathyroidism, malignancy)",
                "Check PTH, PTHrP if indicated",
                "Hydration",
                "Monitor symptoms"
            ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "Severe hypercalcemia"
            recommendations = [
                "Urgent evaluation and treatment",
                "Aggressive IV hydration",
                "Consider bisphosphonates or calcitonin",
                "Evaluate for malignancy",
                "Monitor for complications"
            ]

        return CalculatorResult(
            value=round(corrected_ca, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="8.5-10.5 mg/dL",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "mg/dL", "uncorrected_calcium": total_calcium, "albumin": albumin}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "total_calcium": {"type": "float", "unit": "mg/dL", "min": 4, "max": 20, "required": True},
                "albumin": {"type": "float", "unit": "g/dL", "min": 1, "max": 6, "required": True},
            }
        }


class CorrectedSodiumCalculator(Calculator):
    """
    Corrected Sodium

    Adjusts serum sodium for hyperglycemia.

    Reference: Katz MA. NEJM 1973
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Sodium corrected for hyperglycemia"
        self.citations = ["Katz MA. N Engl J Med. 1973;289(16):843-844"]

    def calculate(
        self,
        measured_sodium: float,
        glucose: float,
    ) -> CalculatorResult:
        """
        Calculate corrected sodium.

        Args:
            measured_sodium: Measured serum sodium (mEq/L)
            glucose: Serum glucose (mg/dL)
        """
        self.validate_range(measured_sodium, 100, 200, "measured_sodium")
        self.validate_range(glucose, 50, 1000, "glucose")

        # For every 100 mg/dL glucose >100, add 1.6 mEq/L to sodium
        if glucose > 100:
            corrected_na = measured_sodium + 1.6 * ((glucose - 100) / 100)
        else:
            corrected_na = measured_sodium

        # Interpretation
        if corrected_na < 135:
            risk_level = RiskLevel.MODERATE
            interpretation = "True hyponatremia (even after glucose correction)"
            recommendations = [
                "Evaluate for hyponatremia causes",
                "Assess volume status",
                "Check urine osmolality and sodium",
                "Treat underlying cause"
            ]
        elif corrected_na <= 145:
            risk_level = RiskLevel.LOW
            interpretation = "Normal sodium (after correction)"
            if glucose > 100:
                recommendations = [
                    "Measured sodium low due to hyperglycemia",
                    "True sodium is normal",
                    "Treat hyperglycemia"
                ]
            else:
                recommendations = ["Normal sodium level"]
        else:
            risk_level = RiskLevel.MODERATE
            interpretation = "Hypernatremia"
            recommendations = [
                "Evaluate for hypernatremia causes",
                "Assess hydration status",
                "Free water deficit calculation",
                "Gradual correction if chronic"
            ]

        warnings = []
        if glucose > 400:
            warnings.append("Severe hyperglycemia - consider DKA/HHS evaluation")
        if abs(corrected_na - measured_sodium) > 5:
            warnings.append(f"Significant correction: measured {measured_sodium} → corrected {round(corrected_na, 1)}")

        return CalculatorResult(
            value=round(corrected_na, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="135-145 mEq/L",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "unit": "mEq/L",
                "measured_sodium": measured_sodium,
                "glucose": glucose,
                "correction": round(corrected_na - measured_sodium, 1)
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "measured_sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "glucose": {"type": "float", "unit": "mg/dL", "min": 50, "max": 1000, "required": True},
            }
        }


class AnionGapCalculator(Calculator):
    """
    Anion Gap

    Assesses metabolic acidosis and electrolyte balance.

    Reference: Oh MS, Carroll HJ. NEJM 1977
    """

    def __init__(self):
        super().__init__()
        self.category = "endocrine_metabolic"
        self.description = "Serum anion gap calculation"
        self.citations = ["Oh MS, Carroll HJ. N Engl J Med. 1977;297(15):814-818"]

    def calculate(
        self,
        sodium: float,
        chloride: float,
        bicarbonate: float,
        albumin: Optional[float] = None,
    ) -> CalculatorResult:
        """
        Calculate anion gap.

        Args:
            sodium: Serum sodium (mEq/L)
            chloride: Serum chloride (mEq/L)
            bicarbonate: Serum bicarbonate/CO2 (mEq/L)
            albumin: Serum albumin (g/dL) - for corrected AG
        """
        self.validate_range(sodium, 100, 200, "sodium")
        self.validate_range(chloride, 50, 150, "chloride")
        self.validate_range(bicarbonate, 5, 50, "bicarbonate")

        # Anion Gap = Na - (Cl + HCO3)
        anion_gap = sodium - (chloride + bicarbonate)

        # Albumin correction if provided
        if albumin is not None:
            self.validate_range(albumin, 1, 6, "albumin")
            # Corrected AG = AG + 2.5 × (4.0 - albumin)
            corrected_ag = anion_gap + 2.5 * (4.0 - albumin)
            used_gap = corrected_ag
            corrected = True
        else:
            used_gap = anion_gap
            corrected = False

        # Interpretation (using 12 as upper limit of normal)
        if used_gap <= 12:
            risk_level = RiskLevel.LOW
            interpretation = "Normal anion gap"
            differential = []
            recommendations = ["No anion gap metabolic acidosis"]

            if bicarbonate < 22:
                recommendations.append("If acidotic, consider normal anion gap metabolic acidosis (NAGMA)")
                differential = [
                    "Diarrhea/GI losses",
                    "Renal tubular acidosis",
                    "Urinary diversion",
                    "Iatrogenic (normal saline)"
                ]
        else:
            risk_level = RiskLevel.MODERATE
            interpretation = "Elevated anion gap"
            recommendations = [
                "Evaluate for anion gap metabolic acidosis",
                "Check lactate, ketones, renal function",
                "Consider toxic ingestions if very high",
                "Treat underlying cause"
            ]

            # MUDPILES differential
            differential = [
                "Methanol",
                "Uremia",
                "Diabetic/alcoholic ketoacidosis",
                "Propylene glycol",
                "Iron/Isoniazid",
                "Lactic acidosis",
                "Ethylene glycol",
                "Salicylates"
            ]

        warnings = []
        if used_gap > 20:
            warnings.append("Markedly elevated AG - consider toxic ingestion")
        if used_gap > 30:
            warnings.append("Severe AGMA - urgent evaluation and treatment needed")

        return CalculatorResult(
            value=round(used_gap, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="8-12 mEq/L (may vary by lab)",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "unit": "mEq/L",
                "uncorrected_ag": round(anion_gap, 1),
                "corrected_for_albumin": corrected,
                "differential_diagnosis": differential if differential else None
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "chloride": {"type": "float", "unit": "mEq/L", "min": 50, "max": 150, "required": True},
                "bicarbonate": {"type": "float", "unit": "mEq/L", "min": 5, "max": 50, "required": True},
                "albumin": {"type": "float", "unit": "g/dL", "min": 1, "max": 6, "required": False},
            }
        }
