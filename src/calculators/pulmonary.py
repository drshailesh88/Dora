"""
Pulmonary Calculators

Collection of respiratory and pulmonary function calculators.
"""

import math
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError


class AaGradientCalculator(Calculator):
    """
    A-a Gradient (Alveolar-arterial Oxygen Gradient)

    Assesses gas exchange and helps differentiate causes of hypoxemia.

    Reference: Standard pulmonary physiology
    """

    def __init__(self):
        super().__init__()
        self.category = "pulmonary"
        self.description = "Alveolar-arterial oxygen gradient"
        self.citations = ["Standard pulmonary physiology formula"]

    def calculate(
        self,
        fio2: float,
        pao2: float,
        paco2: float,
        age: Optional[int] = None,
        altitude: float = 0,
    ) -> CalculatorResult:
        """
        Calculate A-a gradient.

        Args:
            fio2: Fraction of inspired oxygen (0.21-1.0)
            pao2: Arterial oxygen tension (mmHg)
            paco2: Arterial CO2 tension (mmHg)
            age: Age in years (for expected gradient calculation)
            altitude: Altitude in feet above sea level
        """
        self.validate_range(fio2, 0.21, 1.0, "fio2")
        self.validate_range(pao2, 20, 600, "pao2")
        self.validate_range(paco2, 10, 100, "paco2")
        if age is not None:
            self.validate_range(age, 0, 120, "age")

        # Calculate atmospheric pressure based on altitude
        # Patm ≈ 760 - (altitude × 0.025) mmHg (approximate)
        patm = 760 - (altitude * 0.025 / 1000)  # rough approximation

        # Water vapor pressure at 37°C
        ph2o = 47  # mmHg

        # Alveolar gas equation: PAO2 = (FiO2 × (Patm - PH2O)) - (PaCO2 / R)
        # Using R = 0.8 (respiratory quotient)
        pao2_alveolar = (fio2 * (patm - ph2o)) - (paco2 / 0.8)

        # A-a gradient
        aa_gradient = pao2_alveolar - pao2

        # Expected A-a gradient based on age (if provided)
        if age is not None:
            expected_gradient = (age / 4) + 4
        else:
            expected_gradient = 10  # typical for young adult on room air

        # Interpretation
        if aa_gradient <= expected_gradient:
            risk_level = RiskLevel.LOW
            interpretation = "Normal A-a gradient"
            differential = ["Normal gas exchange"]
            recommendations = ["No pulmonary gas exchange abnormality"]
        elif aa_gradient <= expected_gradient + 10:
            risk_level = RiskLevel.LOW
            interpretation = "Mildly elevated A-a gradient"
            differential = ["Early V/Q mismatch", "Mild shunt", "Diffusion limitation"]
            recommendations = ["Assess clinical context", "Consider repeat ABG", "Evaluate for pulmonary pathology"]
        else:
            risk_level = RiskLevel.MODERATE
            interpretation = "Elevated A-a gradient - impaired gas exchange"
            differential = [
                "V/Q mismatch (PE, pneumonia, COPD, asthma)",
                "Shunt (atelectasis, consolidation, ARDS)",
                "Diffusion limitation (ILD, pulmonary edema)"
            ]
            recommendations = [
                "Evaluate for V/Q mismatch vs shunt",
                "Consider imaging (CXR, CT)",
                "Assess for PE if high suspicion",
                "Optimize oxygenation"
            ]

        warnings = []
        if fio2 > 0.6:
            warnings.append("High FiO2 may affect gradient interpretation")
        if aa_gradient > 50:
            warnings.append("Severely elevated gradient - consider significant pulmonary pathology")

        return CalculatorResult(
            value=round(aa_gradient, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range=f"Expected: {round(expected_gradient, 1)} mmHg (based on age)" if age else "Typically <15 mmHg on room air",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "unit": "mmHg",
                "pao2_alveolar": round(pao2_alveolar, 1),
                "expected_gradient": round(expected_gradient, 1) if age else None,
                "differential_diagnosis": differential
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "fio2": {"type": "float", "min": 0.21, "max": 1.0, "description": "0.21 = room air, 1.0 = 100% O2", "required": True},
                "pao2": {"type": "float", "unit": "mmHg", "min": 20, "max": 600, "required": True},
                "paco2": {"type": "float", "unit": "mmHg", "min": 10, "max": 100, "required": True},
                "age": {"type": "integer", "min": 0, "max": 120, "required": False},
                "altitude": {"type": "float", "unit": "feet", "default": 0, "required": False},
            }
        }


class PFRatioCalculator(Calculator):
    """
    PaO2/FiO2 Ratio (P/F Ratio)

    Assesses severity of hypoxemia and ARDS.

    Reference: ARDS Definition Task Force. JAMA 2012
    """

    def __init__(self):
        super().__init__()
        self.category = "pulmonary"
        self.description = "P/F ratio for ARDS severity"
        self.citations = ["ARDS Definition Task Force. JAMA. 2012;307(23):2526-2533"]

    def calculate(
        self,
        pao2: float,
        fio2: float,
    ) -> CalculatorResult:
        """
        Calculate P/F ratio.

        Args:
            pao2: Arterial oxygen tension (mmHg)
            fio2: Fraction of inspired oxygen (0.21-1.0 or 21-100 if percentage)
        """
        self.validate_range(pao2, 20, 600, "pao2")

        # Handle percentage input
        if fio2 > 1.0:
            fio2 = fio2 / 100

        self.validate_range(fio2, 0.21, 1.0, "fio2")

        # Calculate P/F ratio
        pf_ratio = pao2 / fio2

        # ARDS severity classification (Berlin Definition)
        if pf_ratio > 300:
            risk_level = RiskLevel.LOW
            interpretation = "No ARDS - normal oxygenation"
            ards_severity = None
            mortality = "N/A"
            recommendations = ["No ARDS present", "Assess for other causes of hypoxemia if symptomatic"]
        elif pf_ratio > 200:
            risk_level = RiskLevel.MODERATE
            interpretation = "Mild ARDS"
            ards_severity = "Mild"
            mortality = "27%"
            recommendations = [
                "Low tidal volume ventilation (6 mL/kg IBW)",
                "PEEP optimization",
                "Treat underlying cause",
                "Consider recruitment maneuvers"
            ]
        elif pf_ratio > 100:
            risk_level = RiskLevel.HIGH
            interpretation = "Moderate ARDS"
            ards_severity = "Moderate"
            mortality = "32%"
            recommendations = [
                "Low tidal volume ventilation",
                "Higher PEEP strategy",
                "Prone positioning if P/F <150",
                "Neuromuscular blockade consideration",
                "Conservative fluid management"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Severe ARDS"
            ards_severity = "Severe"
            mortality = "45%"
            recommendations = [
                "Lung protective ventilation mandatory",
                "Prone positioning strongly recommended",
                "Consider neuromuscular blockade",
                "ECMO evaluation if available",
                "Avoid fluid overload"
            ]

        warnings = []
        if pf_ratio <= 200:
            warnings.append("ARDS criteria met - requires PEEP ≥5 cmH2O and bilateral infiltrates")
        if pf_ratio < 100:
            warnings.append("Severe hypoxemia - consider ECMO center transfer")

        return CalculatorResult(
            value=round(pf_ratio, 0),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range=">300: normal, 200-300: mild ARDS, 100-200: moderate ARDS, <100: severe ARDS",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings if warnings else None,
            metadata={
                "unit": "mmHg",
                "ards_severity": ards_severity,
                "hospital_mortality": mortality if ards_severity else None
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "pao2": {"type": "float", "unit": "mmHg", "min": 20, "max": 600, "required": True},
                "fio2": {"type": "float", "description": "0.21-1.0 or 21-100 (will auto-convert)", "required": True},
            }
        }


class CURB65Calculator(Calculator):
    """
    CURB-65 Score

    Pneumonia severity and mortality prediction.

    Reference: Lim WS, et al. Thorax 2003
    """

    def __init__(self):
        super().__init__()
        self.category = "pulmonary"
        self.description = "Pneumonia severity assessment"
        self.citations = ["Lim WS, et al. Thorax. 2003;58(5):377-382"]

    def calculate(
        self,
        confusion: bool,
        bun: float,
        respiratory_rate: int,
        systolic_bp: float,
        diastolic_bp: float,
        age: int,
    ) -> CalculatorResult:
        """
        Calculate CURB-65 score.

        Args:
            confusion: New onset confusion
            bun: Blood urea nitrogen (mg/dL)
            respiratory_rate: Breaths per minute
            systolic_bp: mmHg
            diastolic_bp: mmHg
            age: Age in years
        """
        self.validate_range(bun, 1, 200, "bun")
        self.validate_range(respiratory_rate, 5, 60, "respiratory_rate")
        self.validate_range(systolic_bp, 50, 250, "systolic_bp")
        self.validate_range(diastolic_bp, 20, 150, "diastolic_bp")
        self.validate_range(age, 0, 120, "age")

        score = 0

        # C - Confusion
        if confusion:
            score += 1

        # U - Urea (BUN >20 mg/dL or >7 mmol/L)
        if bun > 20:
            score += 1

        # R - Respiratory rate ≥30
        if respiratory_rate >= 30:
            score += 1

        # B - Blood pressure (SBP <90 or DBP ≤60)
        if systolic_bp < 90 or diastolic_bp <= 60:
            score += 1

        # 65 - Age ≥65
        if age >= 65:
            score += 1

        # Risk stratification
        if score == 0:
            risk_level = RiskLevel.LOW
            mortality = "0.7%"
            interpretation = "Low risk - outpatient management"
            recommendations = [
                "Outpatient treatment appropriate",
                "Oral antibiotics",
                "Close outpatient follow-up"
            ]
            disposition = "Outpatient"
        elif score == 1:
            risk_level = RiskLevel.LOW
            mortality = "2.1%"
            interpretation = "Low risk - consider outpatient vs brief observation"
            recommendations = [
                "Outpatient treatment usually appropriate",
                "Consider brief ED observation",
                "Ensure good social support"
            ]
            disposition = "Outpatient or observation"
        elif score == 2:
            risk_level = RiskLevel.MODERATE
            mortality = "9.2%"
            interpretation = "Moderate risk - hospitalization recommended"
            recommendations = [
                "Hospital admission recommended",
                "IV antibiotics initially",
                "Monitor for deterioration"
            ]
            disposition = "Admission"
        elif score == 3:
            risk_level = RiskLevel.HIGH
            mortality = "14.5%"
            interpretation = "High risk - hospitalization required"
            recommendations = [
                "Hospital admission required",
                "Consider ICU evaluation",
                "Aggressive antibiotic therapy",
                "Close monitoring"
            ]
            disposition = "Admission (consider ICU)"
        else:  # 4-5
            risk_level = RiskLevel.VERY_HIGH
            mortality = "40%"
            interpretation = "Very high risk - ICU consideration"
            recommendations = [
                "Hospital admission required",
                "Strong consideration for ICU",
                "Broad spectrum antibiotics",
                "Hemodynamic support if needed"
            ]
            disposition = "ICU consideration"

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-1: outpatient, 2: admission, ≥3: consider ICU",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "max_score": 5,
                "30_day_mortality": mortality,
                "disposition": disposition
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "confusion": {"type": "boolean", "required": True},
                "bun": {"type": "float", "unit": "mg/dL", "min": 1, "max": 200, "required": True},
                "respiratory_rate": {"type": "integer", "unit": "per minute", "min": 5, "max": 60, "required": True},
                "systolic_bp": {"type": "float", "unit": "mmHg", "min": 50, "max": 250, "required": True},
                "diastolic_bp": {"type": "float", "unit": "mmHg", "min": 20, "max": 150, "required": True},
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
            }
        }


class PSICalculator(Calculator):
    """
    PSI/PORT Score (Pneumonia Severity Index)

    More detailed pneumonia severity assessment than CURB-65.

    Reference: Fine MJ, et al. NEJM 1997
    """

    def __init__(self):
        super().__init__()
        self.category = "pulmonary"
        self.description = "Pneumonia Severity Index"
        self.citations = ["Fine MJ, et al. N Engl J Med. 1997;336(4):243-250"]

    def calculate(
        self,
        age: int,
        sex: str,
        nursing_home: bool,
        neoplastic_disease: bool,
        liver_disease: bool,
        congestive_heart_failure: bool,
        cerebrovascular_disease: bool,
        renal_disease: bool,
        altered_mental_status: bool,
        respiratory_rate: int,
        systolic_bp: float,
        temperature_c: float,
        heart_rate: int,
        ph: Optional[float] = None,
        bun: Optional[float] = None,
        sodium: Optional[float] = None,
        glucose: Optional[float] = None,
        hematocrit: Optional[float] = None,
        pao2: Optional[float] = None,
        pleural_effusion: bool = False,
    ) -> CalculatorResult:
        """Calculate PSI/PORT score."""
        self.validate_range(age, 0, 120, "age")
        self.validate_choice(sex, ["male", "female"], "sex")
        self.validate_range(respiratory_rate, 5, 60, "respiratory_rate")
        self.validate_range(systolic_bp, 50, 250, "systolic_bp")
        self.validate_range(temperature_c, 30, 45, "temperature_c")
        self.validate_range(heart_rate, 30, 200, "heart_rate")

        points = 0

        # Demographics
        points += age
        if sex == "female":
            points -= 10

        # Comorbidities
        if nursing_home:
            points += 10
        if neoplastic_disease:
            points += 30
        if liver_disease:
            points += 20
        if congestive_heart_failure:
            points += 10
        if cerebrovascular_disease:
            points += 10
        if renal_disease:
            points += 10

        # Physical exam
        if altered_mental_status:
            points += 20
        if respiratory_rate >= 30:
            points += 20
        if systolic_bp < 90:
            points += 20
        if temperature_c < 35 or temperature_c >= 40:
            points += 15
        if heart_rate >= 125:
            points += 10

        # Laboratory findings
        if ph is not None and ph < 7.35:
            points += 30
        if bun is not None and bun >= 30:
            points += 20
        if sodium is not None and sodium < 130:
            points += 20
        if glucose is not None and glucose >= 250:
            points += 10
        if hematocrit is not None and hematocrit < 30:
            points += 10
        if pao2 is not None and pao2 < 60:
            points += 10
        if pleural_effusion:
            points += 10

        # Risk class
        if points <= 50:
            risk_class = "I"
            risk_level = RiskLevel.LOW
            mortality = "0.1%"
            interpretation = "Risk Class I - Very low risk"
            recommendations = ["Outpatient treatment", "Oral antibiotics"]
        elif points <= 70:
            risk_class = "II"
            risk_level = RiskLevel.LOW
            mortality = "0.6%"
            interpretation = "Risk Class II - Low risk"
            recommendations = ["Outpatient treatment usually safe", "Consider brief observation"]
        elif points <= 90:
            risk_class = "III"
            risk_level = RiskLevel.MODERATE
            mortality = "2.8%"
            interpretation = "Risk Class III - Moderate risk"
            recommendations = ["Consider brief hospitalization", "Close monitoring"]
        elif points <= 130:
            risk_class = "IV"
            risk_level = RiskLevel.HIGH
            mortality = "8.2%"
            interpretation = "Risk Class IV - High risk"
            recommendations = ["Hospitalization recommended", "Parenteral antibiotics", "Monitor for complications"]
        else:
            risk_class = "V"
            risk_level = RiskLevel.VERY_HIGH
            mortality = "29.2%"
            interpretation = "Risk Class V - Very high risk"
            recommendations = ["Hospitalization required", "Consider ICU", "Aggressive treatment"]

        return CalculatorResult(
            value=f"Class {risk_class} ({points} points)",
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="I-II: outpatient, III: brief hospitalization, IV-V: admission",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "points": points,
                "risk_class": risk_class,
                "30_day_mortality": mortality
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "nursing_home": {"type": "boolean", "required": True},
                "neoplastic_disease": {"type": "boolean", "required": True},
                "liver_disease": {"type": "boolean", "required": True},
                "congestive_heart_failure": {"type": "boolean", "required": True},
                "cerebrovascular_disease": {"type": "boolean", "required": True},
                "renal_disease": {"type": "boolean", "required": True},
                "altered_mental_status": {"type": "boolean", "required": True},
                "respiratory_rate": {"type": "integer", "unit": "per minute", "min": 5, "max": 60, "required": True},
                "systolic_bp": {"type": "float", "unit": "mmHg", "min": 50, "max": 250, "required": True},
                "temperature_c": {"type": "float", "unit": "°C", "min": 30, "max": 45, "required": True},
                "heart_rate": {"type": "integer", "unit": "bpm", "min": 30, "max": 200, "required": True},
                "ph": {"type": "float", "min": 6.8, "max": 7.8, "required": False},
                "bun": {"type": "float", "unit": "mg/dL", "min": 1, "max": 200, "required": False},
                "sodium": {"type": "float", "unit": "mEq/L", "min": 100, "max": 200, "required": False},
                "glucose": {"type": "float", "unit": "mg/dL", "min": 10, "max": 1000, "required": False},
                "hematocrit": {"type": "float", "unit": "%", "min": 10, "max": 70, "required": False},
                "pao2": {"type": "float", "unit": "mmHg", "min": 20, "max": 600, "required": False},
                "pleural_effusion": {"type": "boolean", "default": False, "required": False},
            }
        }


class BODEIndexCalculator(Calculator):
    """
    BODE Index

    Multidimensional grading system for COPD prognosis.
    B: BMI, O: Obstruction (FEV1), D: Dyspnea, E: Exercise capacity (6MWT)

    Reference: Celli BR, et al. NEJM 2004
    """

    def __init__(self):
        super().__init__()
        self.category = "pulmonary"
        self.description = "COPD prognosis (4-year mortality)"
        self.citations = ["Celli BR, et al. N Engl J Med. 2004;350(10):1005-1012"]

    def calculate(
        self,
        bmi: float,
        fev1_percent_predicted: float,
        mmrc_dyspnea_scale: int,
        six_minute_walk_distance_m: float,
    ) -> CalculatorResult:
        """
        Calculate BODE index.

        Args:
            bmi: Body mass index (kg/m²)
            fev1_percent_predicted: FEV1 as % of predicted
            mmrc_dyspnea_scale: Modified MRC dyspnea scale (0-4)
            six_minute_walk_distance_m: 6-minute walk test distance in meters
        """
        self.validate_range(bmi, 10, 60, "bmi")
        self.validate_range(fev1_percent_predicted, 5, 150, "fev1_percent_predicted")
        self.validate_range(mmrc_dyspnea_scale, 0, 4, "mmrc_dyspnea_scale")
        self.validate_range(six_minute_walk_distance_m, 0, 1000, "six_minute_walk_distance_m")

        points = 0

        # B - BMI
        if bmi <= 21:
            points += 1

        # O - Obstruction (FEV1 % predicted)
        if fev1_percent_predicted >= 65:
            points += 0
        elif fev1_percent_predicted >= 50:
            points += 1
        elif fev1_percent_predicted >= 36:
            points += 2
        else:
            points += 3

        # D - Dyspnea (mMRC scale)
        if mmrc_dyspnea_scale <= 1:
            points += 0
        elif mmrc_dyspnea_scale == 2:
            points += 1
        elif mmrc_dyspnea_scale == 3:
            points += 2
        else:  # 4
            points += 3

        # E - Exercise (6MWT distance in meters)
        if six_minute_walk_distance_m >= 350:
            points += 0
        elif six_minute_walk_distance_m >= 250:
            points += 1
        elif six_minute_walk_distance_m >= 150:
            points += 2
        else:
            points += 3

        # Risk stratification
        if points <= 2:
            risk_level = RiskLevel.LOW
            four_year_mortality = 15
            interpretation = "Quartile 1 - Low risk"
            recommendations = [
                "Continue optimal COPD management",
                "Smoking cessation if applicable",
                "Pulmonary rehabilitation",
                "Vaccinations up to date"
            ]
        elif points <= 4:
            risk_level = RiskLevel.MODERATE
            four_year_mortality = 30
            interpretation = "Quartile 2 - Moderate risk"
            recommendations = [
                "Optimize inhaler therapy",
                "Pulmonary rehabilitation strongly recommended",
                "Consider long-term oxygen if hypoxemic",
                "Regular follow-up"
            ]
        elif points <= 6:
            risk_level = RiskLevel.HIGH
            four_year_mortality = 40
            interpretation = "Quartile 3 - High risk"
            recommendations = [
                "Aggressive management",
                "Pulmonary rehabilitation essential",
                "Oxygen therapy evaluation",
                "Frequent monitoring",
                "Advanced care planning discussions"
            ]
        else:  # 7-10
            risk_level = RiskLevel.VERY_HIGH
            four_year_mortality = 80
            interpretation = "Quartile 4 - Very high risk"
            recommendations = [
                "Maximal medical therapy",
                "Consider lung volume reduction/transplant evaluation",
                "Palliative care consultation",
                "Advanced care planning",
                "Frequent monitoring"
            ]

        return CalculatorResult(
            value=points,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-2: Q1, 3-4: Q2, 5-6: Q3, 7-10: Q4",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "max_score": 10,
                "four_year_mortality_percent": four_year_mortality,
                "quartile": (points // 2) + 1 if points <= 6 else 4
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "bmi": {"type": "float", "unit": "kg/m²", "min": 10, "max": 60, "required": True},
                "fev1_percent_predicted": {"type": "float", "unit": "%", "min": 5, "max": 150, "required": True},
                "mmrc_dyspnea_scale": {"type": "integer", "min": 0, "max": 4, "description": "0=dyspnea with strenuous exercise, 4=too dyspneic to leave house", "required": True},
                "six_minute_walk_distance_m": {"type": "float", "unit": "meters", "min": 0, "max": 1000, "required": True},
            }
        }
