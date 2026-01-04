"""
General Calculators

Collection of general medical calculators for dosing, fluids, and utilities.
"""

import math
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError, UnitConverter, UnitType


class IVFluidRateCalculator(Calculator):
    """
    IV Fluid Rate Calculator

    Calculates infusion rate for IV fluids.
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "IV fluid infusion rate"
        self.citations = ["Standard clinical calculation"]

    def calculate(
        self,
        volume_ml: float,
        duration_hours: float,
        drop_factor: int = 20,
    ) -> CalculatorResult:
        """
        Calculate IV fluid rate.

        Args:
            volume_ml: Total volume to infuse (mL)
            duration_hours: Infusion duration (hours)
            drop_factor: Drop factor (drops/mL) - 10, 15, 20, or 60
        """
        self.validate_range(volume_ml, 1, 10000, "volume_ml")
        self.validate_range(duration_hours, 0.1, 72, "duration_hours")
        self.validate_choice(drop_factor, [10, 15, 20, 60], "drop_factor")

        # mL/hr
        ml_per_hour = volume_ml / duration_hours

        # drops/min
        drops_per_min = (volume_ml * drop_factor) / (duration_hours * 60)

        # Interpretation
        if ml_per_hour > 500:
            risk_level = RiskLevel.MODERATE
            interpretation = "High infusion rate"
            warnings = ["Monitor for fluid overload", "Ensure large bore IV access"]
        elif ml_per_hour > 200:
            risk_level = RiskLevel.LOW
            interpretation = "Moderate infusion rate"
            warnings = None
        else:
            risk_level = RiskLevel.LOW
            interpretation = "Standard infusion rate"
            warnings = None

        return CalculatorResult(
            value={
                "ml_per_hour": round(ml_per_hour, 1),
                "drops_per_minute": round(drops_per_min, 0)
            },
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="Varies by clinical indication",
            recommendations=[
                f"Set pump to {round(ml_per_hour, 1)} mL/hr",
                f"Or manually regulate to {round(drops_per_min, 0)} drops/min"
            ],
            citations=self.citations,
            warnings=[warnings] if warnings else None,
            metadata={
                "volume_ml": volume_ml,
                "duration_hours": duration_hours,
                "drop_factor": drop_factor
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "volume_ml": {"type": "float", "unit": "mL", "min": 1, "max": 10000, "required": True},
                "duration_hours": {"type": "float", "unit": "hours", "min": 0.1, "max": 72, "required": True},
                "drop_factor": {"type": "integer", "choices": [10, 15, 20, 60], "default": 20, "description": "Macrodrip: 10-20, Microdrip: 60", "required": False},
            }
        }


class DrugDosingCalculator(Calculator):
    """
    Drug Dosing by Weight

    Calculates drug dose based on weight.
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Weight-based drug dosing"
        self.citations = ["Standard pharmacology"]

    def calculate(
        self,
        weight: float,
        dose_per_kg: float,
        frequency_per_day: int = 1,
        max_dose: Optional[float] = None,
        weight_unit: str = "kg",
    ) -> CalculatorResult:
        """
        Calculate drug dose.

        Args:
            weight: Patient weight
            dose_per_kg: Dose per kg (e.g., 5 for 5 mg/kg)
            frequency_per_day: Doses per day
            max_dose: Maximum single dose (optional)
            weight_unit: 'kg' or 'lb'
        """
        # Convert to kg
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        self.validate_range(weight_kg, 0.5, 300, "weight")
        self.validate_range(dose_per_kg, 0.001, 1000, "dose_per_kg")
        self.validate_range(frequency_per_day, 1, 24, "frequency_per_day")

        # Calculate dose
        single_dose = weight_kg * dose_per_kg

        # Apply max dose if specified
        if max_dose and single_dose > max_dose:
            actual_dose = max_dose
            capped = True
        else:
            actual_dose = single_dose
            capped = False

        daily_dose = actual_dose * frequency_per_day

        # Generate recommendations
        recommendations = [
            f"Single dose: {round(actual_dose, 2)} (unit as prescribed)",
            f"Frequency: {frequency_per_day} times daily",
            f"Total daily dose: {round(daily_dose, 2)} (unit as prescribed)"
        ]

        if capped:
            recommendations.append(f"Dose capped at maximum of {max_dose}")

        return CalculatorResult(
            value=round(actual_dose, 2),
            interpretation=f"Weight-based dosing: {round(actual_dose, 2)} per dose",
            risk_level=RiskLevel.LOW,
            reference_range="N/A - verify with drug reference",
            recommendations=recommendations,
            citations=self.citations,
            warnings=["Always verify dose with drug reference", "Consider renal/hepatic adjustment"] if not capped else ["Dose capped at maximum", "Always verify with drug reference"],
            metadata={
                "weight_kg": round(weight_kg, 1),
                "dose_per_kg": dose_per_kg,
                "single_dose": round(actual_dose, 2),
                "daily_dose": round(daily_dose, 2),
                "frequency": frequency_per_day,
                "dose_capped": capped
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "weight": {"type": "float", "min": 0.5, "max": 300, "required": True},
                "dose_per_kg": {"type": "float", "description": "Dose per kilogram", "min": 0.001, "max": 1000, "required": True},
                "frequency_per_day": {"type": "integer", "min": 1, "max": 24, "default": 1, "required": False},
                "max_dose": {"type": "float", "description": "Maximum single dose", "required": False},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
            }
        }


class InfusionRateCalculator(Calculator):
    """
    Infusion Rate Calculator

    Calculates infusion rate for medications (e.g., vasopressors, insulin).
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Medication infusion rate"
        self.citations = ["Standard ICU calculation"]

    def calculate(
        self,
        dose_per_time: float,
        weight: float,
        concentration: float,
        dose_unit: str = "mcg/kg/min",
        concentration_unit: str = "mcg/ml",
        weight_unit: str = "kg",
    ) -> CalculatorResult:
        """
        Calculate infusion rate.

        Args:
            dose_per_time: Desired dose rate
            weight: Patient weight
            concentration: Drug concentration in solution
            dose_unit: 'mcg/kg/min', 'mg/kg/hr', 'units/hr', 'mcg/min'
            concentration_unit: 'mcg/ml', 'mg/ml', 'units/ml'
            weight_unit: 'kg' or 'lb'
        """
        # Convert weight to kg
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        self.validate_range(weight_kg, 0.5, 300, "weight")
        self.validate_range(dose_per_time, 0.001, 10000, "dose_per_time")
        self.validate_range(concentration, 0.001, 100000, "concentration")

        # Calculate based on dose unit
        if dose_unit == "mcg/kg/min":
            # Convert to mL/hr
            # (mcg/kg/min × kg × 60 min/hr) / (mcg/mL) = mL/hr
            if concentration_unit == "mcg/ml":
                ml_per_hr = (dose_per_time * weight_kg * 60) / concentration
            elif concentration_unit == "mg/ml":
                ml_per_hr = (dose_per_time * weight_kg * 60) / (concentration * 1000)
            else:
                raise ValidationError("Incompatible concentration unit for mcg/kg/min")

        elif dose_unit == "mg/kg/hr":
            # (mg/kg/hr × kg) / (mg/mL) = mL/hr
            if concentration_unit == "mg/ml":
                ml_per_hr = (dose_per_time * weight_kg) / concentration
            elif concentration_unit == "mcg/ml":
                ml_per_hr = (dose_per_time * weight_kg * 1000) / concentration
            else:
                raise ValidationError("Incompatible concentration unit for mg/kg/hr")

        elif dose_unit == "units/hr":
            # units/hr / (units/mL) = mL/hr
            if concentration_unit == "units/ml":
                ml_per_hr = dose_per_time / concentration
            else:
                raise ValidationError("Incompatible concentration unit for units/hr")

        elif dose_unit == "mcg/min":
            # (mcg/min × 60) / (mcg/mL) = mL/hr
            if concentration_unit == "mcg/ml":
                ml_per_hr = (dose_per_time * 60) / concentration
            elif concentration_unit == "mg/ml":
                ml_per_hr = (dose_per_time * 60) / (concentration * 1000)
            else:
                raise ValidationError("Incompatible concentration unit for mcg/min")

        else:
            raise ValidationError(f"Unsupported dose unit: {dose_unit}")

        return CalculatorResult(
            value=round(ml_per_hr, 2),
            interpretation=f"Infusion rate: {round(ml_per_hr, 2)} mL/hr",
            risk_level=RiskLevel.LOW,
            reference_range="N/A",
            recommendations=[
                f"Set pump to {round(ml_per_hr, 2)} mL/hr",
                "Double-check calculation independently",
                "Titrate to clinical response"
            ],
            citations=self.citations,
            warnings=["Critical medication - verify with second clinician"],
            metadata={
                "dose": dose_per_time,
                "dose_unit": dose_unit,
                "weight_kg": round(weight_kg, 1),
                "concentration": concentration,
                "concentration_unit": concentration_unit,
                "ml_per_hour": round(ml_per_hr, 2)
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "dose_per_time": {"type": "float", "description": "Desired dose", "min": 0.001, "max": 10000, "required": True},
                "weight": {"type": "float", "min": 0.5, "max": 300, "required": True},
                "concentration": {"type": "float", "description": "Drug concentration", "min": 0.001, "max": 100000, "required": True},
                "dose_unit": {"type": "string", "choices": ["mcg/kg/min", "mg/kg/hr", "units/hr", "mcg/min"], "default": "mcg/kg/min", "required": False},
                "concentration_unit": {"type": "string", "choices": ["mcg/ml", "mg/ml", "units/ml"], "default": "mcg/ml", "required": False},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
            }
        }


class MedicalUnitConverter(Calculator):
    """
    Medical Unit Converter

    Converts between common medical units.
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Medical unit conversions"
        self.citations = ["Standard conversion factors"]

    def calculate(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
    ) -> CalculatorResult:
        """
        Convert between medical units.

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
        """
        conversions = {
            # Weight
            ("kg", "lb"): 2.20462,
            ("lb", "kg"): 0.453592,
            ("g", "mg"): 1000,
            ("mg", "g"): 0.001,
            ("mg", "mcg"): 1000,
            ("mcg", "mg"): 0.001,
            # Height
            ("cm", "inch"): 0.393701,
            ("inch", "cm"): 2.54,
            ("m", "cm"): 100,
            ("cm", "m"): 0.01,
            ("feet", "cm"): 30.48,
            ("cm", "feet"): 0.0328084,
            # Temperature
            ("celsius", "fahrenheit"): lambda x: (x * 9/5) + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            # Creatinine
            ("mg/dl_creat", "umol/l_creat"): 88.42,
            ("umol/l_creat", "mg/dl_creat"): 0.0113,
            # Glucose
            ("mg/dl_glucose", "mmol/l_glucose"): 0.0555,
            ("mmol/l_glucose", "mg/dl_glucose"): 18.0,
        }

        conversion_key = (from_unit.lower(), to_unit.lower())

        if conversion_key not in conversions:
            raise ValidationError(f"Conversion from {from_unit} to {to_unit} not supported")

        converter = conversions[conversion_key]
        if callable(converter):
            result = converter(value)
        else:
            result = value * converter

        return CalculatorResult(
            value=round(result, 4),
            interpretation=f"{value} {from_unit} = {round(result, 4)} {to_unit}",
            risk_level=RiskLevel.LOW,
            reference_range="N/A",
            recommendations=["Use converted value in calculations"],
            citations=self.citations,
            metadata={
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": round(result, 4),
                "converted_unit": to_unit
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "value": {"type": "float", "required": True},
                "from_unit": {"type": "string", "required": True},
                "to_unit": {"type": "string", "required": True},
            }
        }


class PediatricWeightCalculator(Calculator):
    """
    Pediatric Weight Estimation

    Estimates pediatric weight when scale unavailable (emergency situations).

    Reference: Luscombe M, Owens B. BMJ 2007
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Pediatric weight estimation"
        self.citations = ["Luscombe M, Owens B. BMJ. 2007;334(7593):s49"]

    def calculate(
        self,
        age_years: float,
        method: str = "apls",
    ) -> CalculatorResult:
        """
        Estimate pediatric weight.

        Args:
            age_years: Age in years (can be fractional, e.g., 2.5)
            method: 'apls' (Advanced Paediatric Life Support) or 'best_guess'
        """
        self.validate_range(age_years, 0, 12, "age_years")
        self.validate_choice(method, ["apls", "best_guess"], "method")

        if method == "apls":
            if age_years < 1:
                # Infant: (age in months / 2) + 4
                age_months = age_years * 12
                weight = (age_months / 2) + 4
                formula = f"(age_months/2) + 4 = ({age_months}/2) + 4"
            elif age_years <= 5:
                # 1-5 years: (age × 2) + 8
                weight = (age_years * 2) + 8
                formula = f"(age × 2) + 8 = ({age_years} × 2) + 8"
            else:
                # 6-12 years: (age × 3) + 7
                weight = (age_years * 3) + 7
                formula = f"(age × 3) + 7 = ({age_years} × 3) + 7"
        else:
            # Best Guess formula: (age + 4) × 2
            weight = (age_years + 4) * 2
            formula = f"(age + 4) × 2 = ({age_years} + 4) × 2"

        return CalculatorResult(
            value=round(weight, 1),
            interpretation=f"Estimated weight: {round(weight, 1)} kg",
            risk_level=RiskLevel.MODERATE,
            reference_range="N/A",
            recommendations=[
                "This is an ESTIMATE for emergency use only",
                "Obtain actual weight as soon as possible",
                "Use for emergency drug dosing when scale unavailable"
            ],
            citations=self.citations,
            warnings=[
                "Estimation formula - NOT a substitute for measured weight",
                "May be inaccurate in obese or malnourished children",
                "For emergency use only"
            ],
            metadata={
                "age_years": age_years,
                "estimated_weight_kg": round(weight, 1),
                "method": method,
                "formula": formula
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age_years": {"type": "float", "unit": "years", "min": 0, "max": 12, "required": True},
                "method": {"type": "string", "choices": ["apls", "best_guess"], "default": "apls", "required": False},
            }
        }


class ParklandFormulaCalculator(Calculator):
    """
    Parkland Formula for Burns

    Calculates fluid resuscitation for burn patients.

    Reference: Baxter CR, Shires T. Ann Surg 1968
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Burn fluid resuscitation"
        self.citations = ["Baxter CR, Shires T. Ann Surg. 1968;168(4):693-703"]

    def calculate(
        self,
        weight: float,
        tbsa_percent: float,
        weight_unit: str = "kg",
    ) -> CalculatorResult:
        """
        Calculate Parkland formula fluid requirements.

        Args:
            weight: Patient weight
            tbsa_percent: Total body surface area burned (%)
            weight_unit: 'kg' or 'lb'
        """
        # Convert to kg
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        self.validate_range(weight_kg, 10, 300, "weight")
        self.validate_range(tbsa_percent, 0, 100, "tbsa_percent")

        # Parkland Formula: 4 mL × kg × %TBSA
        # First 24 hours: Give half in first 8 hours, half in next 16 hours
        total_24hr = 4 * weight_kg * tbsa_percent
        first_8hr = total_24hr / 2
        next_16hr = total_24hr / 2

        # Rates
        rate_first_8hr = first_8hr / 8
        rate_next_16hr = next_16hr / 16

        if tbsa_percent < 15:
            risk_level = RiskLevel.LOW
            interpretation = "Minor burn"
            recommendations = [
                "May not need full Parkland resuscitation",
                "Consider oral hydration if <10% TBSA",
                "Monitor urine output",
                "Wound care"
            ]
        elif tbsa_percent < 30:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate burn"
            recommendations = [
                "Parkland formula as guideline",
                "Titrate to urine output 0.5-1 mL/kg/hr",
                "Lactated Ringer's solution",
                "Burn center consultation"
            ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "Severe burn"
            recommendations = [
                "Transfer to burn center",
                "Aggressive fluid resuscitation",
                "Target urine output 0.5-1 mL/kg/hr",
                "Consider albumin after 24 hours",
                "ICU admission"
            ]

        return CalculatorResult(
            value={
                "total_24hr_ml": round(total_24hr, 0),
                "first_8hr_ml": round(first_8hr, 0),
                "next_16hr_ml": round(next_16hr, 0),
                "rate_first_8hr_ml_per_hr": round(rate_first_8hr, 0),
                "rate_next_16hr_ml_per_hr": round(rate_next_16hr, 0)
            },
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="N/A",
            recommendations=recommendations,
            citations=self.citations,
            warnings=[
                "Formula is a GUIDELINE - titrate to urine output",
                "Start time from time of burn, not arrival",
                "Monitor for fluid overload and compartment syndrome"
            ],
            metadata={
                "weight_kg": round(weight_kg, 1),
                "tbsa_percent": tbsa_percent,
                "formula": "4 mL × kg × %TBSA over 24 hours"
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "weight": {"type": "float", "min": 10, "max": 300, "required": True},
                "tbsa_percent": {"type": "float", "unit": "%", "min": 0, "max": 100, "required": True},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
            }
        }


class MaintenanceFluidCalculator(Calculator):
    """
    Maintenance Fluid Calculator (4-2-1 Rule)

    Calculates pediatric and adult maintenance fluid requirements.

    Reference: Holliday MA, Segar WE. Pediatrics 1957
    """

    def __init__(self):
        super().__init__()
        self.category = "general"
        self.description = "Maintenance fluid (4-2-1 rule)"
        self.citations = ["Holliday MA, Segar WE. Pediatrics. 1957;19(5):823-832"]

    def calculate(
        self,
        weight: float,
        weight_unit: str = "kg",
    ) -> CalculatorResult:
        """
        Calculate maintenance fluid rate.

        Args:
            weight: Patient weight
            weight_unit: 'kg' or 'lb'

        4-2-1 Rule:
        - 4 mL/kg/hr for first 10 kg
        - 2 mL/kg/hr for next 10 kg (11-20 kg)
        - 1 mL/kg/hr for each kg above 20 kg
        """
        # Convert to kg
        if weight_unit == "lb":
            weight_kg = UnitConverter.convert_weight(weight, UnitType.WEIGHT_LB, UnitType.WEIGHT_KG)
        else:
            weight_kg = weight

        self.validate_range(weight_kg, 1, 300, "weight")

        # Apply 4-2-1 rule
        if weight_kg <= 10:
            hourly_rate = 4 * weight_kg
        elif weight_kg <= 20:
            hourly_rate = 40 + 2 * (weight_kg - 10)
        else:
            hourly_rate = 40 + 20 + 1 * (weight_kg - 20)

        daily_total = hourly_rate * 24

        # Interpretation
        if weight_kg < 3:
            interpretation = "Neonate/infant - special considerations"
            warnings = ["Neonatal fluid management may differ", "Consult pediatrics"]
        elif weight_kg < 20:
            interpretation = "Pediatric maintenance fluids"
            warnings = None
        else:
            interpretation = "Adult/adolescent maintenance fluids"
            warnings = ["Rule developed for children - adult requirements may vary"]

        return CalculatorResult(
            value=round(hourly_rate, 1),
            interpretation=interpretation,
            risk_level=RiskLevel.LOW,
            reference_range="N/A",
            recommendations=[
                f"Hourly rate: {round(hourly_rate, 1)} mL/hr",
                f"Daily total: {round(daily_total, 0)} mL/day",
                "Adjust for fever, losses, renal function",
                "Monitor fluid balance"
            ],
            citations=self.citations,
            warnings=[warnings] if warnings else None,
            metadata={
                "weight_kg": round(weight_kg, 1),
                "hourly_rate_ml": round(hourly_rate, 1),
                "daily_total_ml": round(daily_total, 0),
                "formula": "4-2-1 rule"
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "weight": {"type": "float", "min": 1, "max": 300, "required": True},
                "weight_unit": {"type": "string", "choices": ["kg", "lb"], "default": "kg", "required": False},
            }
        }
