"""
Renal Calculators

Collection of renal function and electrolyte calculators.
"""

import math
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError, UnitConverter, UnitType


class eGFRCKDEPICalculator(Calculator):
    """
    eGFR using CKD-EPI 2021 Equation

    Race-free equation for estimated glomerular filtration rate.

    Reference: Inker LA, et al. NEJM 2021
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "eGFR calculation (CKD-EPI 2021)"
        self.citations = ["Inker LA, et al. N Engl J Med. 2021;385(19):1737-1749"]

    def calculate(
        self,
        creatinine: float,
        age: int,
        sex: str,
        creatinine_unit: str = "mg/dL",
    ) -> CalculatorResult:
        """
        Calculate eGFR using CKD-EPI 2021 (race-free).

        Args:
            creatinine: Serum creatinine
            age: Age in years
            sex: 'male' or 'female'
            creatinine_unit: 'mg/dL' or 'μmol/L'
        """
        self.validate_range(age, 18, 120, "age")
        self.validate_choice(sex, ["male", "female"], "sex")
        self.validate_range(creatinine, 0.1, 20, "creatinine")

        # Convert to mg/dL if needed
        if creatinine_unit == "μmol/L":
            creatinine_mg_dl = UnitConverter.convert_creatinine(
                creatinine, UnitType.CREATININE_UMOL_L, UnitType.CREATININE_MG_DL
            )
        else:
            creatinine_mg_dl = creatinine

        # CKD-EPI 2021 (race-free)
        kappa = 0.7 if sex == "female" else 0.9
        alpha = -0.241 if sex == "female" else -0.302
        sex_factor = 1.012 if sex == "female" else 1.0

        min_ratio = min(creatinine_mg_dl / kappa, 1.0)
        max_ratio = max(creatinine_mg_dl / kappa, 1.0)

        egfr = 142 * (min_ratio ** alpha) * (max_ratio ** -1.200) * (0.9938 ** age) * sex_factor

        # CKD Staging
        if egfr >= 90:
            stage = "G1"
            risk_level = RiskLevel.LOW
            interpretation = "Normal or high kidney function"
            recommendations = ["No CKD if no other kidney damage markers"]
        elif egfr >= 60:
            stage = "G2"
            risk_level = RiskLevel.LOW
            interpretation = "Mild reduction in kidney function"
            recommendations = ["Monitor annually", "Control blood pressure and diabetes"]
        elif egfr >= 45:
            stage = "G3a"
            risk_level = RiskLevel.MODERATE
            interpretation = "Mild to moderate reduction in kidney function"
            recommendations = ["Nephrology referral if progressive", "Adjust drug dosing", "Monitor every 6-12 months"]
        elif egfr >= 30:
            stage = "G3b"
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate to severe reduction in kidney function"
            recommendations = ["Nephrology referral recommended", "Adjust drug dosing", "Monitor every 3-6 months"]
        elif egfr >= 15:
            stage = "G4"
            risk_level = RiskLevel.HIGH
            interpretation = "Severe reduction in kidney function"
            recommendations = ["Nephrology referral required", "Prepare for renal replacement therapy", "Monitor monthly"]
        else:
            stage = "G5"
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Kidney failure"
            recommendations = ["Nephrology management", "Dialysis or transplant planning", "Frequent monitoring"]

        warnings = []
        if egfr < 60:
            warnings.append("Chronic kidney disease present - assess for complications")
        if egfr < 30:
            warnings.append("Increased risk of cardiovascular disease and mineral bone disorder")

        return CalculatorResult(
            value=round(egfr, 1),
            interpretation=f"CKD Stage {stage}: {interpretation}",
            risk_level=risk_level,
            reference_range="≥90: G1, 60-89: G2, 45-59: G3a, 30-44: G3b, 15-29: G4, <15: G5",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={"unit": "mL/min/1.73m²", "ckd_stage": stage, "formula": "CKD-EPI 2021"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "creatinine": {"type": "float", "min": 0.1, "max": 20, "required": True},
                "age": {"type": "integer", "min": 18, "max": 120, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "creatinine_unit": {"type": "string", "choices": ["mg/dL", "μmol/L"], "default": "mg/dL", "required": False},
            }
        }


class CockcroftGaultCalculator(Calculator):
    """
    Creatinine Clearance (Cockcroft-Gault)

    Estimates creatinine clearance, useful for drug dosing.

    Reference: Cockcroft DW, Gault MH. Nephron 1976
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "Creatinine clearance estimation"
        self.citations = ["Cockcroft DW, Gault MH. Nephron. 1976;16(1):31-41"]

    def calculate(
        self,
        age: int,
        sex: str,
        weight: float,
        creatinine: float,
        creatinine_unit: str = "mg/dL",
    ) -> CalculatorResult:
        """
        Calculate creatinine clearance.

        Args:
            age: Age in years
            sex: 'male' or 'female'
            weight: Weight in kg
            creatinine: Serum creatinine
            creatinine_unit: 'mg/dL' or 'μmol/L'
        """
        self.validate_range(age, 18, 120, "age")
        self.validate_choice(sex, ["male", "female"], "sex")
        self.validate_range(weight, 20, 300, "weight")
        self.validate_range(creatinine, 0.1, 20, "creatinine")

        # Convert to mg/dL if needed
        if creatinine_unit == "μmol/L":
            creatinine_mg_dl = UnitConverter.convert_creatinine(
                creatinine, UnitType.CREATININE_UMOL_L, UnitType.CREATININE_MG_DL
            )
        else:
            creatinine_mg_dl = creatinine

        # Cockcroft-Gault formula
        sex_factor = 0.85 if sex == "female" else 1.0
        crcl = ((140 - age) * weight * sex_factor) / (72 * creatinine_mg_dl)

        if crcl >= 90:
            risk_level = RiskLevel.LOW
            interpretation = "Normal creatinine clearance"
            recommendations = ["No dose adjustment needed for most medications"]
        elif crcl >= 60:
            risk_level = RiskLevel.LOW
            interpretation = "Mild reduction in creatinine clearance"
            recommendations = ["Monitor renal function", "Some medications may need dose adjustment"]
        elif crcl >= 30:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate reduction in creatinine clearance"
            recommendations = ["Adjust doses of renally cleared medications", "Avoid nephrotoxic drugs"]
        elif crcl >= 15:
            risk_level = RiskLevel.HIGH
            interpretation = "Severe reduction in creatinine clearance"
            recommendations = ["Careful medication dosing required", "Nephrology consultation", "Avoid nephrotoxic drugs"]
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Kidney failure"
            recommendations = ["Nephrology management", "Most medications need dose adjustment", "Consider dialysis"]

        warnings = ["Use ideal body weight if obese", "Less accurate in extremes of age or weight"]

        return CalculatorResult(
            value=round(crcl, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="≥90: normal, 60-89: mild, 30-59: moderate, 15-29: severe, <15: failure",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings,
            metadata={"unit": "mL/min", "formula": "Cockcroft-Gault"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 18, "max": 120, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "weight": {"type": "float", "unit": "kg", "min": 20, "max": 300, "required": True},
                "creatinine": {"type": "float", "min": 0.1, "max": 20, "required": True},
                "creatinine_unit": {"type": "string", "choices": ["mg/dL", "μmol/L"], "default": "mg/dL", "required": False},
            }
        }


class FENaCalculator(Calculator):
    """
    Fractional Excretion of Sodium (FENa)

    Differentiates prerenal from intrinsic acute kidney injury.

    Reference: Espinel CH. JAMA 1976
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "Differentiates prerenal vs intrinsic AKI"
        self.citations = ["Espinel CH. JAMA. 1976;236(6):579-581"]

    def calculate(
        self,
        serum_sodium: float,
        urine_sodium: float,
        serum_creatinine: float,
        urine_creatinine: float,
    ) -> CalculatorResult:
        """
        Calculate fractional excretion of sodium.

        Args:
            serum_sodium: mEq/L
            urine_sodium: mEq/L
            serum_creatinine: mg/dL
            urine_creatinine: mg/dL
        """
        self.validate_range(serum_sodium, 100, 200, "serum_sodium")
        self.validate_range(urine_sodium, 1, 300, "urine_sodium")
        self.validate_range(serum_creatinine, 0.1, 20, "serum_creatinine")
        self.validate_range(urine_creatinine, 1, 500, "urine_creatinine")

        # FENa = (UNa × SCr) / (SNa × UCr) × 100
        fena = (urine_sodium * serum_creatinine) / (serum_sodium * urine_creatinine) * 100

        if fena < 1:
            risk_level = RiskLevel.LOW
            interpretation = "Prerenal azotemia (most likely)"
            recommendations = [
                "Consider volume resuscitation",
                "Address underlying cause (hypovolemia, heart failure, cirrhosis)",
                "Monitor response to fluids"
            ]
            etiology = "Prerenal"
        elif fena < 2:
            risk_level = RiskLevel.MODERATE
            interpretation = "Indeterminate - could be prerenal or intrinsic"
            recommendations = [
                "Consider clinical context",
                "May trial fluid resuscitation",
                "Monitor trends",
                "Consider other causes of AKI"
            ]
            etiology = "Indeterminate"
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "Intrinsic renal disease (most likely)"
            recommendations = [
                "Evaluate for ATN, AIN, glomerulonephritis",
                "Review medications (nephrotoxins)",
                "Urine sediment analysis",
                "Consider nephrology consultation"
            ]
            etiology = "Intrinsic"

        warnings = [
            "Not accurate if on diuretics (use FEUrea instead)",
            "Not reliable in CKD",
            "Interpretation depends on clinical context"
        ]

        return CalculatorResult(
            value=round(fena, 2),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<1%: prerenal, 1-2%: indeterminate, >2%: intrinsic",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings,
            metadata={"unit": "%", "likely_etiology": etiology}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "serum_sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "urine_sodium": {"type": "float", "unit": "mEq/L", "min": 1, "max": 300, "required": True},
                "serum_creatinine": {"type": "float", "unit": "mg/dL", "min": 0.1, "max": 20, "required": True},
                "urine_creatinine": {"type": "float", "unit": "mg/dL", "min": 1, "max": 500, "required": True},
            }
        }


class UrineAnionGapCalculator(Calculator):
    """
    Urine Anion Gap

    Helps determine cause of normal anion gap metabolic acidosis.

    Reference: Batlle DC, et al. NEJM 1988
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "Evaluates renal vs GI cause of NAGMA"
        self.citations = ["Batlle DC, et al. N Engl J Med. 1988;318(10):594-599"]

    def calculate(
        self,
        urine_sodium: float,
        urine_potassium: float,
        urine_chloride: float,
    ) -> CalculatorResult:
        """
        Calculate urine anion gap.

        Args:
            urine_sodium: mEq/L
            urine_potassium: mEq/L
            urine_chloride: mEq/L
        """
        self.validate_range(urine_sodium, 1, 300, "urine_sodium")
        self.validate_range(urine_potassium, 1, 200, "urine_potassium")
        self.validate_range(urine_chloride, 1, 300, "urine_chloride")

        # UAG = (Na + K) - Cl
        uag = (urine_sodium + urine_potassium) - urine_chloride

        if uag < 0:
            risk_level = RiskLevel.LOW
            interpretation = "Negative UAG: Appropriate renal response (GI losses likely)"
            recommendations = [
                "Consider GI causes: diarrhea, laxative abuse, ileostomy",
                "Renal acidification intact",
                "Treat underlying GI condition"
            ]
            likely_cause = "Extrarenal (GI losses)"
        else:
            risk_level = RiskLevel.MODERATE
            interpretation = "Positive UAG: Impaired renal acidification (RTA likely)"
            recommendations = [
                "Consider renal tubular acidosis (Type 1 or 4)",
                "Check serum potassium (low in Type 1, high in Type 4)",
                "Consider urine pH",
                "Nephrology consultation may be warranted"
            ]
            likely_cause = "Renal (RTA)"

        return CalculatorResult(
            value=round(uag, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<0: GI losses, >0: RTA",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "mEq/L", "likely_cause": likely_cause}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "urine_sodium": {"type": "float", "unit": "mEq/L", "min": 1, "max": 300, "required": True},
                "urine_potassium": {"type": "float", "unit": "mEq/L", "min": 1, "max": 200, "required": True},
                "urine_chloride": {"type": "float", "unit": "mEq/L", "min": 1, "max": 300, "required": True},
            }
        }


class SerumOsmolalityCalculator(Calculator):
    """
    Serum Osmolality

    Calculates serum osmolality and osmolar gap.

    Reference: Standard formula
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "Calculated serum osmolality"
        self.citations = ["Standard clinical formula"]

    def calculate(
        self,
        sodium: float,
        glucose: float,
        bun: float,
    ) -> CalculatorResult:
        """
        Calculate serum osmolality.

        Args:
            sodium: mEq/L
            glucose: mg/dL
            bun: mg/dL (blood urea nitrogen)
        """
        self.validate_range(sodium, 100, 200, "sodium")
        self.validate_range(glucose, 10, 1000, "glucose")
        self.validate_range(bun, 1, 200, "bun")

        # Formula: 2×Na + Glucose/18 + BUN/2.8
        osm_calc = 2 * sodium + glucose / 18 + bun / 2.8

        if osm_calc < 275:
            risk_level = RiskLevel.LOW
            interpretation = "Low serum osmolality (hypo-osmolar)"
            recommendations = [
                "Evaluate for hyponatremia causes",
                "Consider SIADH, psychogenic polydipsia, low solute intake"
            ]
        elif osm_calc <= 295:
            risk_level = RiskLevel.LOW
            interpretation = "Normal serum osmolality"
            recommendations = ["No specific intervention needed"]
        else:
            risk_level = RiskLevel.MODERATE
            interpretation = "High serum osmolality (hyperosmolar)"
            recommendations = [
                "Evaluate for hypernatremia, hyperglycemia, uremia",
                "If measured osm significantly higher, calculate osmolar gap",
                "Consider toxic alcohols if gap present"
            ]

        return CalculatorResult(
            value=round(osm_calc, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="275-295 mOsm/kg",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "mOsm/kg", "formula": "2×Na + Gluc/18 + BUN/2.8"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "glucose": {"type": "float", "unit": "mg/dL", "min": 10, "max": 1000, "required": True},
                "bun": {"type": "float", "unit": "mg/dL", "min": 1, "max": 200, "required": True},
            }
        }


class OsmolarGapCalculator(Calculator):
    """
    Osmolar Gap

    Difference between measured and calculated osmolality.
    Useful for detecting unmeasured osmoles (toxic alcohols).

    Reference: Glaser DS. Am J Clin Pathol 1996
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "Detects unmeasured osmoles"
        self.citations = ["Glaser DS. Am J Clin Pathol. 1996;105(2):200-204"]

    def calculate(
        self,
        measured_osmolality: float,
        sodium: float,
        glucose: float,
        bun: float,
        ethanol: Optional[float] = 0,
    ) -> CalculatorResult:
        """
        Calculate osmolar gap.

        Args:
            measured_osmolality: Measured serum osmolality (mOsm/kg)
            sodium: mEq/L
            glucose: mg/dL
            bun: mg/dL
            ethanol: mg/dL (optional, if known)
        """
        self.validate_range(measured_osmolality, 200, 400, "measured_osmolality")
        self.validate_range(sodium, 100, 200, "sodium")
        self.validate_range(glucose, 10, 1000, "glucose")
        self.validate_range(bun, 1, 200, "bun")

        # Calculate expected osmolality
        osm_calc = 2 * sodium + glucose / 18 + bun / 2.8

        # Add ethanol contribution if present
        if ethanol:
            osm_calc += ethanol / 4.6

        # Osmolar gap
        osm_gap = measured_osmolality - osm_calc

        if osm_gap < 10:
            risk_level = RiskLevel.LOW
            interpretation = "Normal osmolar gap"
            recommendations = ["No unmeasured osmoles detected"]
            likely_toxins = None
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "Elevated osmolar gap - unmeasured osmoles present"
            recommendations = [
                "Consider toxic alcohol ingestion",
                "Check ethylene glycol, methanol, isopropanol levels",
                "Toxicology consultation",
                "Consider fomepizole if high suspicion"
            ]
            likely_toxins = [
                "Methanol",
                "Ethylene glycol",
                "Isopropanol",
                "Propylene glycol (high dose lorazepam IV)",
                "Diethylene glycol"
            ]

        warnings = ["Gap >10 with high anion gap acidosis suggests toxic alcohol"]

        return CalculatorResult(
            value=round(osm_gap, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<10 mOsm/kg normal",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if osm_gap >= 10 else None,
            metadata={"unit": "mOsm/kg", "likely_toxins": likely_toxins}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "measured_osmolality": {"type": "float", "unit": "mOsm/kg", "min": 200, "max": 400, "required": True},
                "sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": True},
                "glucose": {"type": "float", "unit": "mg/dL", "min": 10, "max": 1000, "required": True},
                "bun": {"type": "float", "unit": "mg/dL", "min": 1, "max": 200, "required": True},
                "ethanol": {"type": "float", "unit": "mg/dL", "default": 0, "required": False},
            }
        }


class RIFLECriteriaCalculator(Calculator):
    """
    RIFLE Criteria for Acute Kidney Injury

    Risk, Injury, Failure, Loss, End-stage kidney disease classification.

    Reference: Bellomo R, et al. Crit Care 2004
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "AKI classification (RIFLE)"
        self.citations = ["Bellomo R, et al. Crit Care. 2004;8(4):R204-R212"]

    def calculate(
        self,
        creatinine_increase_fold: Optional[float] = None,
        creatinine_increase_absolute: Optional[float] = None,
        urine_output_ml_kg_hr: Optional[float] = None,
        urine_duration_hours: Optional[int] = None,
    ) -> CalculatorResult:
        """
        Classify AKI by RIFLE criteria.

        Args:
            creatinine_increase_fold: Fold increase from baseline (e.g., 1.5 for 1.5x)
            creatinine_increase_absolute: Absolute increase in mg/dL
            urine_output_ml_kg_hr: Urine output in mL/kg/hr
            urine_duration_hours: Duration of oliguria in hours
        """
        # Determine stage based on creatinine or UOP
        cr_stage = None
        uop_stage = None

        # Creatinine criteria
        if creatinine_increase_fold is not None:
            if creatinine_increase_fold >= 3:
                cr_stage = "Failure"
            elif creatinine_increase_fold >= 2:
                cr_stage = "Injury"
            elif creatinine_increase_fold >= 1.5:
                cr_stage = "Risk"

        if creatinine_increase_absolute is not None and creatinine_increase_absolute >= 0.3:
            if cr_stage is None:
                cr_stage = "Risk"

        # Urine output criteria
        if urine_output_ml_kg_hr is not None and urine_duration_hours is not None:
            if urine_output_ml_kg_hr < 0.3 and urine_duration_hours >= 24:
                uop_stage = "Failure"
            elif urine_output_ml_kg_hr == 0 and urine_duration_hours >= 12:
                uop_stage = "Failure"
            elif urine_output_ml_kg_hr < 0.5 and urine_duration_hours >= 12:
                uop_stage = "Injury"
            elif urine_output_ml_kg_hr < 0.5 and urine_duration_hours >= 6:
                uop_stage = "Risk"

        # Take worst stage
        stages_order = [None, "Risk", "Injury", "Failure"]
        cr_idx = stages_order.index(cr_stage) if cr_stage in stages_order else 0
        uop_idx = stages_order.index(uop_stage) if uop_stage in stages_order else 0
        final_idx = max(cr_idx, uop_idx)

        if final_idx == 0:
            stage = "No AKI"
            risk_level = RiskLevel.LOW
            interpretation = "No acute kidney injury by RIFLE criteria"
            recommendations = ["Continue monitoring renal function"]
        else:
            stage = stages_order[final_idx]
            if stage == "Risk":
                risk_level = RiskLevel.MODERATE
                interpretation = "RIFLE-Risk: Early AKI"
                recommendations = [
                    "Identify and address underlying cause",
                    "Optimize hemodynamics",
                    "Avoid nephrotoxins",
                    "Monitor closely"
                ]
            elif stage == "Injury":
                risk_level = RiskLevel.HIGH
                interpretation = "RIFLE-Injury: Moderate AKI"
                recommendations = [
                    "Nephrology consultation",
                    "Aggressive management of underlying cause",
                    "Daily monitoring",
                    "Adjust medication doses"
                ]
            else:  # Failure
                risk_level = RiskLevel.VERY_HIGH
                interpretation = "RIFLE-Failure: Severe AKI"
                recommendations = [
                    "Urgent nephrology consultation",
                    "Consider renal replacement therapy",
                    "ICU level care if not already",
                    "Hourly urine output monitoring"
                ]

        return CalculatorResult(
            value=stage,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="Risk → Injury → Failure → Loss → ESKD",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"creatinine_stage": cr_stage, "uop_stage": uop_stage}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "creatinine_increase_fold": {"type": "float", "min": 1.0, "max": 10.0, "required": False},
                "creatinine_increase_absolute": {"type": "float", "unit": "mg/dL", "min": 0, "max": 10, "required": False},
                "urine_output_ml_kg_hr": {"type": "float", "unit": "mL/kg/hr", "min": 0, "max": 10, "required": False},
                "urine_duration_hours": {"type": "integer", "unit": "hours", "min": 0, "max": 168, "required": False},
            }
        }


class AKINCriteriaCalculator(Calculator):
    """
    AKIN Criteria for Acute Kidney Injury

    Acute Kidney Injury Network classification.

    Reference: Mehta RL, et al. Crit Care 2007
    """

    def __init__(self):
        super().__init__()
        self.category = "renal"
        self.description = "AKI classification (AKIN)"
        self.citations = ["Mehta RL, et al. Crit Care. 2007;11(2):R31"]

    def calculate(
        self,
        creatinine_increase_fold: Optional[float] = None,
        creatinine_increase_absolute: Optional[float] = None,
        urine_output_ml_kg_hr: Optional[float] = None,
        urine_duration_hours: Optional[int] = None,
    ) -> CalculatorResult:
        """
        Classify AKI by AKIN criteria.

        Args:
            creatinine_increase_fold: Fold increase from baseline
            creatinine_increase_absolute: Absolute increase in mg/dL
            urine_output_ml_kg_hr: Urine output in mL/kg/hr
            urine_duration_hours: Duration of oliguria in hours
        """
        cr_stage = None
        uop_stage = None

        # Creatinine criteria
        if creatinine_increase_absolute is not None and creatinine_increase_absolute >= 0.3:
            cr_stage = 1
        if creatinine_increase_fold is not None:
            if creatinine_increase_fold >= 3:
                cr_stage = 3
            elif creatinine_increase_fold >= 2:
                cr_stage = 2
            elif creatinine_increase_fold >= 1.5:
                cr_stage = 1 if cr_stage is None else max(cr_stage, 1)

        # Urine output criteria
        if urine_output_ml_kg_hr is not None and urine_duration_hours is not None:
            if urine_output_ml_kg_hr < 0.3 and urine_duration_hours >= 24:
                uop_stage = 3
            elif urine_output_ml_kg_hr == 0 and urine_duration_hours >= 12:
                uop_stage = 3
            elif urine_output_ml_kg_hr < 0.5 and urine_duration_hours >= 12:
                uop_stage = 2
            elif urine_output_ml_kg_hr < 0.5 and urine_duration_hours >= 6:
                uop_stage = 1

        # Take worst stage
        stage = max([s for s in [cr_stage, uop_stage] if s is not None], default=0)

        if stage == 0:
            risk_level = RiskLevel.LOW
            interpretation = "No acute kidney injury by AKIN criteria"
            recommendations = ["Continue monitoring renal function"]
        elif stage == 1:
            risk_level = RiskLevel.MODERATE
            interpretation = "AKIN Stage 1: Mild AKI"
            recommendations = [
                "Identify underlying cause",
                "Optimize hemodynamics",
                "Avoid nephrotoxins",
                "Monitor daily"
            ]
        elif stage == 2:
            risk_level = RiskLevel.HIGH
            interpretation = "AKIN Stage 2: Moderate AKI"
            recommendations = [
                "Nephrology consultation recommended",
                "Aggressive management",
                "Adjust medication doses",
                "Monitor closely"
            ]
        else:  # Stage 3
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "AKIN Stage 3: Severe AKI"
            recommendations = [
                "Urgent nephrology consultation",
                "Consider renal replacement therapy",
                "ICU level care",
                "Hourly monitoring"
            ]

        return CalculatorResult(
            value=f"Stage {stage}" if stage > 0 else "No AKI",
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="Stage 1-3 based on creatinine rise and urine output",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"stage": stage, "creatinine_stage": cr_stage, "uop_stage": uop_stage}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "creatinine_increase_fold": {"type": "float", "min": 1.0, "max": 10.0, "required": False},
                "creatinine_increase_absolute": {"type": "float", "unit": "mg/dL", "min": 0, "max": 10, "required": False},
                "urine_output_ml_kg_hr": {"type": "float", "unit": "mL/kg/hr", "min": 0, "max": 10, "required": False},
                "urine_duration_hours": {"type": "integer", "unit": "hours", "min": 0, "max": 168, "required": False},
            }
        }
