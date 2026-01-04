"""
Cardiovascular Calculators

Collection of cardiovascular risk assessment and diagnostic calculators.
"""

import math
from typing import Dict, Any, Optional
from .base import Calculator, CalculatorResult, RiskLevel, ValidationError


class ASCVDRiskCalculator(Calculator):
    """
    ASCVD Risk Score (Pooled Cohort Equations)

    Estimates 10-year risk of atherosclerotic cardiovascular disease.
    For patients 40-79 years without known ASCVD.

    Reference: Goff DC Jr, et al. 2013 ACC/AHA Guideline
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "10-year ASCVD risk estimation"
        self.citations = [
            "Goff DC Jr, et al. Circulation. 2014;129(25 Suppl 2):S49-73"
        ]

    def calculate(
        self,
        age: int,
        sex: str,
        race: str,
        total_cholesterol: float,
        hdl_cholesterol: float,
        systolic_bp: float,
        on_bp_treatment: bool,
        diabetes: bool,
        smoker: bool,
    ) -> CalculatorResult:
        """
        Calculate 10-year ASCVD risk.

        Args:
            age: Age in years (40-79)
            sex: 'male' or 'female'
            race: 'white', 'black', or 'other'
            total_cholesterol: mg/dL
            hdl_cholesterol: mg/dL
            systolic_bp: mmHg
            on_bp_treatment: Boolean
            diabetes: Boolean
            smoker: Boolean
        """
        # Validation
        self.validate_range(age, 40, 79, "age")
        self.validate_choice(sex, ["male", "female"], "sex")
        self.validate_choice(race, ["white", "black", "other"], "race")
        self.validate_range(total_cholesterol, 130, 320, "total_cholesterol")
        self.validate_range(hdl_cholesterol, 20, 100, "hdl_cholesterol")
        self.validate_range(systolic_bp, 90, 200, "systolic_bp")

        # Convert to log values
        ln_age = math.log(age)
        ln_tc = math.log(total_cholesterol)
        ln_hdl = math.log(hdl_cholesterol)
        ln_sbp = math.log(systolic_bp)

        # Coefficients based on sex and race
        if sex == "female":
            if race == "black":
                # Black female
                coeffs = {
                    "ln_age": 17.1141,
                    "ln_age_sq": 0,
                    "ln_tc": 0.9396,
                    "ln_age_tc": 0,
                    "ln_hdl": -18.9196,
                    "ln_age_hdl": 4.4748,
                    "ln_sbp_treated": 29.2907,
                    "ln_sbp_untreated": 27.8197,
                    "ln_age_sbp_treated": -6.4321,
                    "ln_age_sbp_untreated": -6.0873,
                    "smoker": 0.6908,
                    "ln_age_smoker": 0,
                    "diabetes": 0.8738,
                    "baseline_survival": 0.9533,
                    "mean_cv": 86.6081,
                }
            else:
                # White/other female
                coeffs = {
                    "ln_age": -29.799,
                    "ln_age_sq": 4.884,
                    "ln_tc": 13.540,
                    "ln_age_tc": -3.114,
                    "ln_hdl": -13.578,
                    "ln_age_hdl": 3.149,
                    "ln_sbp_treated": 2.019,
                    "ln_sbp_untreated": 1.957,
                    "ln_age_sbp_treated": 0,
                    "ln_age_sbp_untreated": 0,
                    "smoker": 7.574,
                    "ln_age_smoker": -1.665,
                    "diabetes": 0.661,
                    "baseline_survival": 0.9665,
                    "mean_cv": -29.18,
                }
        else:
            if race == "black":
                # Black male
                coeffs = {
                    "ln_age": 2.469,
                    "ln_age_sq": 0,
                    "ln_tc": 0.302,
                    "ln_age_tc": 0,
                    "ln_hdl": -0.307,
                    "ln_age_hdl": 0,
                    "ln_sbp_treated": 1.916,
                    "ln_sbp_untreated": 1.809,
                    "ln_age_sbp_treated": 0,
                    "ln_age_sbp_untreated": 0,
                    "smoker": 0.549,
                    "ln_age_smoker": 0,
                    "diabetes": 0.645,
                    "baseline_survival": 0.8954,
                    "mean_cv": 19.5425,
                }
            else:
                # White/other male
                coeffs = {
                    "ln_age": 12.344,
                    "ln_age_sq": 0,
                    "ln_tc": 11.853,
                    "ln_age_tc": -2.664,
                    "ln_hdl": -7.990,
                    "ln_age_hdl": 1.769,
                    "ln_sbp_treated": 1.797,
                    "ln_sbp_untreated": 1.764,
                    "ln_age_sbp_treated": 0,
                    "ln_age_sbp_untreated": 0,
                    "smoker": 7.837,
                    "ln_age_smoker": -1.795,
                    "diabetes": 0.658,
                    "baseline_survival": 0.9144,
                    "mean_cv": 61.18,
                }

        # Calculate individual sum
        ind_sum = (
            coeffs["ln_age"] * ln_age
            + coeffs["ln_age_sq"] * ln_age * ln_age
            + coeffs["ln_tc"] * ln_tc
            + coeffs["ln_age_tc"] * ln_age * ln_tc
            + coeffs["ln_hdl"] * ln_hdl
            + coeffs["ln_age_hdl"] * ln_age * ln_hdl
        )

        if on_bp_treatment:
            ind_sum += coeffs["ln_sbp_treated"] * ln_sbp + coeffs["ln_age_sbp_treated"] * ln_age * ln_sbp
        else:
            ind_sum += coeffs["ln_sbp_untreated"] * ln_sbp + coeffs["ln_age_sbp_untreated"] * ln_age * ln_sbp

        if smoker:
            ind_sum += coeffs["smoker"] + coeffs["ln_age_smoker"] * ln_age

        if diabetes:
            ind_sum += coeffs["diabetes"]

        # Calculate 10-year risk
        risk_10yr = 1 - coeffs["baseline_survival"] ** math.exp(ind_sum - coeffs["mean_cv"])
        risk_percent = risk_10yr * 100

        # Risk stratification
        if risk_percent < 5:
            risk_level = RiskLevel.LOW
            interpretation = "Low 10-year ASCVD risk"
            recommendations = ["Lifestyle modifications", "Reassess in 4-6 years"]
        elif risk_percent < 7.5:
            risk_level = RiskLevel.MODERATE
            interpretation = "Borderline 10-year ASCVD risk"
            recommendations = [
                "Consider statin if risk enhancers present",
                "Lifestyle modifications",
                "Reassess in 4-6 years"
            ]
        elif risk_percent < 20:
            risk_level = RiskLevel.HIGH
            interpretation = "Intermediate 10-year ASCVD risk"
            recommendations = [
                "Moderate-intensity statin recommended",
                "Consider CAC score if uncertain",
                "Lifestyle modifications"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "High 10-year ASCVD risk"
            recommendations = [
                "High-intensity statin recommended",
                "Lifestyle modifications",
                "Blood pressure control"
            ]

        return CalculatorResult(
            value=round(risk_percent, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<5% low, 5-7.5% borderline, 7.5-20% intermediate, >20% high",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "%", "timeframe": "10-year"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 40, "max": 79, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "race": {"type": "string", "choices": ["white", "black", "other"], "required": True},
                "total_cholesterol": {"type": "float", "unit": "mg/dL", "min": 130, "max": 320, "required": True},
                "hdl_cholesterol": {"type": "float", "unit": "mg/dL", "min": 20, "max": 100, "required": True},
                "systolic_bp": {"type": "float", "unit": "mmHg", "min": 90, "max": 200, "required": True},
                "on_bp_treatment": {"type": "boolean", "required": True},
                "diabetes": {"type": "boolean", "required": True},
                "smoker": {"type": "boolean", "required": True},
            }
        }


class CHA2DS2VAScCalculator(Calculator):
    """
    CHA₂DS₂-VASc Score

    Stroke risk stratification in atrial fibrillation.

    Reference: Lip GY, et al. Chest 2010
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "Stroke risk in atrial fibrillation"
        self.citations = ["Lip GY, et al. Chest. 2010;137(2):263-272"]

    def calculate(
        self,
        age: int,
        sex: str,
        congestive_heart_failure: bool,
        hypertension: bool,
        stroke_tia_thromboembolism: bool,
        vascular_disease: bool,
        diabetes: bool,
    ) -> CalculatorResult:
        """
        Calculate CHA₂DS₂-VASc score.

        Args:
            age: Age in years
            sex: 'male' or 'female'
            congestive_heart_failure: CHF history
            hypertension: Hypertension history
            stroke_tia_thromboembolism: Prior stroke/TIA/thromboembolism (2 points)
            vascular_disease: Prior MI, PAD, or aortic plaque
            diabetes: Diabetes mellitus
        """
        self.validate_range(age, 0, 120, "age")
        self.validate_choice(sex, ["male", "female"], "sex")

        score = 0

        # C - CHF (1 point)
        if congestive_heart_failure:
            score += 1

        # H - Hypertension (1 point)
        if hypertension:
            score += 1

        # A - Age ≥75 (2 points) or 65-74 (1 point)
        if age >= 75:
            score += 2
        elif age >= 65:
            score += 1

        # D - Diabetes (1 point)
        if diabetes:
            score += 1

        # S - Stroke/TIA/Thromboembolism (2 points)
        if stroke_tia_thromboembolism:
            score += 2

        # V - Vascular disease (1 point)
        if vascular_disease:
            score += 1

        # A - Age 65-74 already counted above

        # Sc - Sex category (female = 1 point)
        if sex == "female":
            score += 1

        # Risk stratification
        risk_data = {
            0: (0, "Very low"),
            1: (1.3, "Low"),
            2: (2.2, "Moderate"),
            3: (3.2, "Moderate"),
            4: (4.0, "Moderate-High"),
            5: (6.7, "High"),
            6: (9.8, "High"),
            7: (9.6, "High"),
            8: (6.7, "High"),
            9: (15.2, "Very High"),
        }

        annual_risk, risk_category = risk_data.get(score, (15.2, "Very High"))

        if score == 0:
            risk_level = RiskLevel.VERY_LOW
            recommendations = ["No anticoagulation recommended", "Consider aspirin or no therapy"]
        elif score == 1 and sex == "male":
            risk_level = RiskLevel.LOW
            recommendations = ["Consider anticoagulation", "Shared decision-making with patient"]
        else:
            risk_level = RiskLevel.HIGH if score >= 2 else RiskLevel.MODERATE
            recommendations = ["Oral anticoagulation recommended (DOAC preferred)", "Monitor for bleeding risk"]

        return CalculatorResult(
            value=score,
            interpretation=f"{risk_category} risk - {annual_risk}% annual stroke risk",
            risk_level=risk_level,
            reference_range="0: very low, 1: low, 2+: anticoagulation recommended",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"max_score": 9, "annual_stroke_risk_percent": annual_risk}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "congestive_heart_failure": {"type": "boolean", "required": True},
                "hypertension": {"type": "boolean", "required": True},
                "stroke_tia_thromboembolism": {"type": "boolean", "required": True},
                "vascular_disease": {"type": "boolean", "required": True},
                "diabetes": {"type": "boolean", "required": True},
            }
        }


class HASBLEDCalculator(Calculator):
    """
    HAS-BLED Score

    Bleeding risk in patients on anticoagulation for atrial fibrillation.

    Reference: Pisters R, et al. Chest 2010
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "Bleeding risk on anticoagulation"
        self.citations = ["Pisters R, et al. Chest. 2010;138(5):1093-1100"]

    def calculate(
        self,
        hypertension: bool,
        renal_disease: bool,
        liver_disease: bool,
        stroke_history: bool,
        prior_bleeding: bool,
        labile_inr: bool,
        age_over_65: bool,
        medication_predisposing: bool,
        alcohol_excess: bool,
    ) -> CalculatorResult:
        """
        Calculate HAS-BLED score.

        Args:
            hypertension: Uncontrolled SBP >160
            renal_disease: Chronic dialysis, transplant, Cr >2.26 mg/dL
            liver_disease: Cirrhosis or bilirubin >2x normal or AST/ALT >3x normal
            stroke_history: Prior stroke
            prior_bleeding: History or predisposition to bleeding
            labile_inr: Unstable/high INR or <60% time in therapeutic range
            age_over_65: Age >65 years
            medication_predisposing: Antiplatelet or NSAID use
            alcohol_excess: ≥8 drinks/week
        """
        score = sum([
            hypertension,
            renal_disease,
            liver_disease,
            stroke_history,
            prior_bleeding,
            labile_inr,
            age_over_65,
            medication_predisposing,
            alcohol_excess,
        ])

        # Risk stratification
        if score <= 2:
            risk_level = RiskLevel.LOW
            annual_bleed_risk = "1.13-1.02%"
            interpretation = "Low bleeding risk"
            recommendations = ["Anticoagulation generally safe", "Regular monitoring"]
        elif score == 3:
            risk_level = RiskLevel.MODERATE
            annual_bleed_risk = "3.74%"
            interpretation = "Moderate bleeding risk"
            recommendations = [
                "Consider anticoagulation carefully",
                "Address modifiable risk factors",
                "More frequent monitoring"
            ]
        else:
            risk_level = RiskLevel.HIGH
            annual_bleed_risk = "8.70-12.50%"
            interpretation = "High bleeding risk"
            recommendations = [
                "Caution with anticoagulation",
                "Aggressively address modifiable risk factors",
                "Frequent monitoring",
                "Consider risks vs benefits carefully"
            ]

        warnings = []
        if score >= 3:
            warnings.append("High score does NOT mean anticoagulation is contraindicated - address modifiable factors")

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-2: low risk, 3: moderate, ≥4: high risk",
            recommendations=recommendations,
            citations=self.citations,
            warnings=warnings,
            metadata={"max_score": 9, "annual_bleed_risk": annual_bleed_risk}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "hypertension": {"type": "boolean", "description": "Uncontrolled SBP >160", "required": True},
                "renal_disease": {"type": "boolean", "description": "Dialysis, transplant, Cr >2.26", "required": True},
                "liver_disease": {"type": "boolean", "description": "Cirrhosis or abnormal LFTs", "required": True},
                "stroke_history": {"type": "boolean", "required": True},
                "prior_bleeding": {"type": "boolean", "required": True},
                "labile_inr": {"type": "boolean", "description": "If on warfarin", "required": True},
                "age_over_65": {"type": "boolean", "required": True},
                "medication_predisposing": {"type": "boolean", "description": "Antiplatelet/NSAID", "required": True},
                "alcohol_excess": {"type": "boolean", "description": "≥8 drinks/week", "required": True},
            }
        }


class HEARTScoreCalculator(Calculator):
    """
    HEART Score for Chest Pain

    Predicts 6-week risk of major adverse cardiac event (MACE).

    Reference: Six AJ, et al. Neth Heart J 2008
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "Chest pain risk stratification"
        self.citations = ["Six AJ, et al. Neth Heart J. 2008;16(6):191-196"]

    def calculate(
        self,
        history_score: int,
        ecg_score: int,
        age: int,
        risk_factors_count: int,
        troponin_level: str,
    ) -> CalculatorResult:
        """
        Calculate HEART score.

        Args:
            history_score: 0=slightly suspicious, 1=moderately suspicious, 2=highly suspicious
            ecg_score: 0=normal, 1=non-specific repol, 2=significant ST deviation
            age: Age in years
            risk_factors_count: Number of risk factors (0-5+)
            troponin_level: 'normal', 'slightly_elevated', 'significantly_elevated'
        """
        self.validate_range(history_score, 0, 2, "history_score")
        self.validate_range(ecg_score, 0, 2, "ecg_score")
        self.validate_range(age, 0, 120, "age")
        self.validate_range(risk_factors_count, 0, 10, "risk_factors_count")
        self.validate_choice(troponin_level, ["normal", "slightly_elevated", "significantly_elevated"], "troponin_level")

        score = history_score + ecg_score

        # Age scoring
        if age < 45:
            score += 0
        elif age <= 64:
            score += 1
        else:
            score += 2

        # Risk factors (HTN, hyperlipidemia, DM, smoking, obesity, family history)
        if risk_factors_count == 0:
            score += 0
        elif risk_factors_count <= 2:
            score += 1
        else:
            score += 2

        # Troponin
        if troponin_level == "normal":
            score += 0
        elif troponin_level == "slightly_elevated":
            score += 1
        else:
            score += 2

        # Risk stratification
        if score <= 3:
            risk_level = RiskLevel.LOW
            mace_risk = "1.7%"
            interpretation = "Low risk for MACE"
            recommendations = [
                "Safe for early discharge",
                "Outpatient follow-up",
                "No further cardiac workup needed in ED"
            ]
        elif score <= 6:
            risk_level = RiskLevel.MODERATE
            mace_risk = "12-17%"
            interpretation = "Moderate risk for MACE"
            recommendations = [
                "Admission or observation",
                "Serial troponins",
                "Consider stress testing or coronary CTA"
            ]
        else:
            risk_level = RiskLevel.HIGH
            mace_risk = "50-65%"
            interpretation = "High risk for MACE"
            recommendations = [
                "Admission",
                "Cardiology consultation",
                "Consider early invasive strategy",
                "Medical management per ACS guidelines"
            ]

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-3: low, 4-6: moderate, 7-10: high",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"max_score": 10, "mace_risk_6week": mace_risk}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "history_score": {"type": "integer", "min": 0, "max": 2, "required": True},
                "ecg_score": {"type": "integer", "min": 0, "max": 2, "required": True},
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
                "risk_factors_count": {"type": "integer", "min": 0, "max": 10, "required": True},
                "troponin_level": {"type": "string", "choices": ["normal", "slightly_elevated", "significantly_elevated"], "required": True},
            }
        }


class WellsDVTCalculator(Calculator):
    """
    Wells Score for DVT

    Predicts probability of deep vein thrombosis.

    Reference: Wells PS, et al. Lancet 1997
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "DVT probability assessment"
        self.citations = ["Wells PS, et al. Lancet. 1997;350(9094):1795-1798"]

    def calculate(
        self,
        active_cancer: bool,
        paralysis_paresis_immobilization: bool,
        bedridden_3days_surgery_4weeks: bool,
        localized_tenderness: bool,
        entire_leg_swollen: bool,
        calf_swelling_3cm: bool,
        pitting_edema: bool,
        collateral_superficial_veins: bool,
        alternative_diagnosis_likely: bool,
    ) -> CalculatorResult:
        """Calculate Wells DVT score."""
        score = 0

        if active_cancer:
            score += 1
        if paralysis_paresis_immobilization:
            score += 1
        if bedridden_3days_surgery_4weeks:
            score += 1
        if localized_tenderness:
            score += 1
        if entire_leg_swollen:
            score += 1
        if calf_swelling_3cm:
            score += 1
        if pitting_edema:
            score += 1
        if collateral_superficial_veins:
            score += 1
        if alternative_diagnosis_likely:
            score -= 2

        # Risk stratification
        if score <= 0:
            risk_level = RiskLevel.LOW
            dvt_probability = "5%"
            interpretation = "Low probability of DVT"
            recommendations = ["D-dimer testing", "If negative, DVT ruled out"]
        elif score <= 2:
            risk_level = RiskLevel.MODERATE
            dvt_probability = "17%"
            interpretation = "Moderate probability of DVT"
            recommendations = ["D-dimer testing", "If positive, proceed to ultrasound"]
        else:
            risk_level = RiskLevel.HIGH
            dvt_probability = "53%"
            interpretation = "High probability of DVT"
            recommendations = ["Ultrasound imaging recommended", "Consider empiric anticoagulation pending imaging"]

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="≤0: low, 1-2: moderate, ≥3: high",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"dvt_probability": dvt_probability}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "active_cancer": {"type": "boolean", "description": "Treatment within 6 months or palliative", "required": True},
                "paralysis_paresis_immobilization": {"type": "boolean", "required": True},
                "bedridden_3days_surgery_4weeks": {"type": "boolean", "required": True},
                "localized_tenderness": {"type": "boolean", "description": "Along deep venous system", "required": True},
                "entire_leg_swollen": {"type": "boolean", "required": True},
                "calf_swelling_3cm": {"type": "boolean", "description": ">3cm vs asymptomatic leg", "required": True},
                "pitting_edema": {"type": "boolean", "description": "Symptomatic leg only", "required": True},
                "collateral_superficial_veins": {"type": "boolean", "description": "Non-varicose", "required": True},
                "alternative_diagnosis_likely": {"type": "boolean", "description": "-2 points", "required": True},
            }
        }


class WellsPECalculator(Calculator):
    """
    Wells Score for PE

    Predicts probability of pulmonary embolism.

    Reference: Wells PS, et al. Thromb Haemost 2000
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "PE probability assessment"
        self.citations = ["Wells PS, et al. Thromb Haemost. 2000;83(3):416-420"]

    def calculate(
        self,
        clinical_dvt_signs: bool,
        pe_most_likely_diagnosis: bool,
        heart_rate_over_100: bool,
        immobilization_surgery: bool,
        previous_pe_dvt: bool,
        hemoptysis: bool,
        malignancy: bool,
    ) -> CalculatorResult:
        """Calculate Wells PE score."""
        score = 0

        if clinical_dvt_signs:
            score += 3.0
        if pe_most_likely_diagnosis:
            score += 3.0
        if heart_rate_over_100:
            score += 1.5
        if immobilization_surgery:
            score += 1.5
        if previous_pe_dvt:
            score += 1.5
        if hemoptysis:
            score += 1.0
        if malignancy:
            score += 1.0

        # Risk stratification
        if score < 2:
            risk_level = RiskLevel.LOW
            pe_probability = "1.3%"
            interpretation = "Low probability of PE"
            recommendations = ["D-dimer testing", "If negative, PE ruled out"]
        elif score <= 6:
            risk_level = RiskLevel.MODERATE
            pe_probability = "16.2%"
            interpretation = "Moderate probability of PE"
            recommendations = ["D-dimer or CTPA", "PERC rule may help if low risk"]
        else:
            risk_level = RiskLevel.HIGH
            pe_probability = "37.5%"
            interpretation = "High probability of PE"
            recommendations = ["CTPA recommended", "Consider empiric anticoagulation if no contraindications"]

        return CalculatorResult(
            value=score,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<2: low, 2-6: moderate, >6: high",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"pe_probability": pe_probability}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "clinical_dvt_signs": {"type": "boolean", "description": "3 points", "required": True},
                "pe_most_likely_diagnosis": {"type": "boolean", "description": "3 points", "required": True},
                "heart_rate_over_100": {"type": "boolean", "description": "1.5 points", "required": True},
                "immobilization_surgery": {"type": "boolean", "description": "≥3 days or surgery in 4 weeks, 1.5 points", "required": True},
                "previous_pe_dvt": {"type": "boolean", "description": "1.5 points", "required": True},
                "hemoptysis": {"type": "boolean", "description": "1 point", "required": True},
                "malignancy": {"type": "boolean", "description": "Active or within 6 months, 1 point", "required": True},
            }
        }


class FraminghamCalculator(Calculator):
    """
    Framingham Risk Score

    10-year cardiovascular disease risk (original Framingham).

    Reference: Wilson PW, et al. Circulation 1998
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "10-year CVD risk (Framingham)"
        self.citations = ["Wilson PW, et al. Circulation. 1998;97(18):1837-1847"]

    def calculate(
        self,
        age: int,
        sex: str,
        total_cholesterol: float,
        hdl_cholesterol: float,
        systolic_bp: float,
        on_bp_treatment: bool,
        smoker: bool,
        diabetes: bool,
    ) -> CalculatorResult:
        """Calculate Framingham risk score (simplified ATP III version)."""
        self.validate_range(age, 20, 79, "age")
        self.validate_choice(sex, ["male", "female"], "sex")

        points = 0

        # Age points
        if sex == "male":
            age_points = {range(20, 35): -9, range(35, 40): -4, range(40, 45): 0,
                         range(45, 50): 3, range(50, 55): 6, range(55, 60): 8,
                         range(60, 65): 10, range(65, 70): 11, range(70, 75): 12,
                         range(75, 80): 13}
        else:
            age_points = {range(20, 35): -7, range(35, 40): -3, range(40, 45): 0,
                         range(45, 50): 3, range(50, 55): 6, range(55, 60): 8,
                         range(60, 65): 10, range(65, 70): 12, range(70, 75): 14,
                         range(75, 80): 16}

        for age_range, pts in age_points.items():
            if age in age_range:
                points += pts
                break

        # TC points (simplified)
        if total_cholesterol < 160:
            points += 0
        elif total_cholesterol < 200:
            points += 4 if sex == "male" else 4
        elif total_cholesterol < 240:
            points += 7 if sex == "male" else 8
        elif total_cholesterol < 280:
            points += 9 if sex == "male" else 11
        else:
            points += 11 if sex == "male" else 13

        # HDL points
        if hdl_cholesterol >= 60:
            points -= 1
        elif hdl_cholesterol >= 50:
            points += 0
        elif hdl_cholesterol >= 40:
            points += 1
        else:
            points += 2

        # Blood pressure
        if systolic_bp < 120:
            points += 0
        elif systolic_bp < 130:
            points += 0 if not on_bp_treatment else 1
        elif systolic_bp < 140:
            points += 1 if not on_bp_treatment else 2
        elif systolic_bp < 160:
            points += 1 if not on_bp_treatment else 2
        else:
            points += 2 if not on_bp_treatment else 3

        # Smoking
        if smoker:
            points += 4 if sex == "male" else 4

        # Diabetes
        if diabetes:
            points += 2 if sex == "male" else 4

        # Estimate 10-year risk (simplified)
        if sex == "male":
            if points < 0:
                risk = 1
            elif points <= 4:
                risk = 2
            elif points <= 6:
                risk = 4
            elif points <= 7:
                risk = 6
            elif points <= 9:
                risk = 10
            elif points <= 11:
                risk = 15
            elif points <= 13:
                risk = 20
            else:
                risk = 30
        else:
            if points < 9:
                risk = 1
            elif points <= 12:
                risk = 2
            elif points <= 14:
                risk = 4
            elif points <= 16:
                risk = 6
            elif points <= 18:
                risk = 10
            elif points <= 20:
                risk = 15
            else:
                risk = 20

        if risk < 10:
            risk_level = RiskLevel.LOW
            interpretation = "Low 10-year CVD risk"
            recommendations = ["Lifestyle modifications", "Reassess risk in 5 years"]
        elif risk < 20:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate 10-year CVD risk"
            recommendations = ["Consider statin therapy", "Lifestyle modifications", "Blood pressure control"]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = "High 10-year CVD risk"
            recommendations = ["Statin therapy recommended", "Aggressive lifestyle modifications", "Target LDL <100 mg/dL"]

        return CalculatorResult(
            value=risk,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="<10%: low, 10-20%: moderate, >20%: high",
            recommendations=recommendations,
            citations=self.citations,
            metadata={"unit": "%", "points": points}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 20, "max": 79, "required": True},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
                "total_cholesterol": {"type": "float", "unit": "mg/dL", "required": True},
                "hdl_cholesterol": {"type": "float", "unit": "mg/dL", "required": True},
                "systolic_bp": {"type": "float", "unit": "mmHg", "required": True},
                "on_bp_treatment": {"type": "boolean", "required": True},
                "smoker": {"type": "boolean", "required": True},
                "diabetes": {"type": "boolean", "required": True},
            }
        }


class TIMIRiskCalculator(Calculator):
    """
    TIMI Risk Score for STEMI

    30-day mortality risk in ST-elevation MI.

    Reference: Morrow DA, et al. JAMA 2000
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "STEMI mortality risk"
        self.citations = ["Morrow DA, et al. JAMA. 2000;284(7):835-842"]

    def calculate(
        self,
        age: int,
        diabetes_htn_angina: bool,
        systolic_bp: float,
        heart_rate: int,
        killip_class: int,
        weight: float,
        anterior_stemi_or_lbbb: bool,
        time_to_treatment_over_4h: bool,
    ) -> CalculatorResult:
        """Calculate TIMI risk score for STEMI."""
        points = 0

        # Age
        if age >= 75:
            points += 3
        elif age >= 65:
            points += 2

        # DM/HTN/Angina
        if diabetes_htn_angina:
            points += 1

        # SBP <100
        if systolic_bp < 100:
            points += 3

        # HR >100
        if heart_rate > 100:
            points += 2

        # Killip II-IV
        if killip_class >= 2:
            points += 2

        # Weight <67kg
        if weight < 67:
            points += 1

        # Anterior STE or LBBB
        if anterior_stemi_or_lbbb:
            points += 1

        # Time to treatment >4h
        if time_to_treatment_over_4h:
            points += 1

        # Mortality risk
        mortality_data = {
            0: 0.8, 1: 1.6, 2: 2.2, 3: 4.4, 4: 7.3,
            5: 12.4, 6: 16.1, 7: 23.4, 8: 26.8
        }
        mortality = mortality_data.get(points, 35.9)

        if points <= 2:
            risk_level = RiskLevel.LOW
            interpretation = "Low 30-day mortality risk"
        elif points <= 4:
            risk_level = RiskLevel.MODERATE
            interpretation = "Moderate 30-day mortality risk"
        elif points <= 6:
            risk_level = RiskLevel.HIGH
            interpretation = "High 30-day mortality risk"
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = "Very high 30-day mortality risk"

        return CalculatorResult(
            value=points,
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="0-2: low, 3-4: moderate, 5-6: high, >6: very high",
            recommendations=["Immediate reperfusion therapy", "Intensive care monitoring"],
            citations=self.citations,
            metadata={"max_score": 14, "mortality_30day_percent": mortality}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "age": {"type": "integer", "min": 0, "max": 120, "required": True},
                "diabetes_htn_angina": {"type": "boolean", "required": True},
                "systolic_bp": {"type": "float", "unit": "mmHg", "required": True},
                "heart_rate": {"type": "integer", "unit": "bpm", "required": True},
                "killip_class": {"type": "integer", "min": 1, "max": 4, "required": True},
                "weight": {"type": "float", "unit": "kg", "required": True},
                "anterior_stemi_or_lbbb": {"type": "boolean", "required": True},
                "time_to_treatment_over_4h": {"type": "boolean", "required": True},
            }
        }


class DukeTreadmillCalculator(Calculator):
    """
    Duke Treadmill Score

    Prognosis in patients with suspected coronary artery disease.

    Reference: Mark DB, et al. Am J Cardiol 1987
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "Exercise stress test prognosis"
        self.citations = ["Mark DB, et al. Am J Cardiol. 1987;60(10):849-852"]

    def calculate(
        self,
        exercise_time_minutes: float,
        max_st_deviation_mm: float,
        angina_index: int,
    ) -> CalculatorResult:
        """
        Calculate Duke Treadmill Score.

        Args:
            exercise_time_minutes: Exercise time in minutes (Bruce protocol)
            max_st_deviation_mm: Maximum ST deviation in mm
            angina_index: 0=none, 1=non-limiting, 2=exercise-limiting
        """
        self.validate_range(exercise_time_minutes, 0, 30, "exercise_time_minutes")
        self.validate_range(max_st_deviation_mm, 0, 10, "max_st_deviation_mm")
        self.validate_choice(angina_index, [0, 1, 2], "angina_index")

        score = exercise_time_minutes - (5 * max_st_deviation_mm) - (4 * angina_index)

        if score >= 5:
            risk_level = RiskLevel.LOW
            annual_mortality = 0.25
            five_year_survival = 97
            interpretation = "Low risk"
            recommendations = ["Medical management", "Routine follow-up"]
        elif score >= -10:
            risk_level = RiskLevel.MODERATE
            annual_mortality = 1.25
            five_year_survival = 91
            interpretation = "Moderate risk"
            recommendations = ["Consider coronary angiography", "Medical optimization", "Risk factor modification"]
        else:
            risk_level = RiskLevel.HIGH
            annual_mortality = 5.0
            five_year_survival = 79
            interpretation = "High risk"
            recommendations = ["Coronary angiography recommended", "Cardiology consultation", "Consider revascularization"]

        return CalculatorResult(
            value=round(score, 1),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="≥5: low risk, -10 to 4: moderate, <-10: high risk",
            recommendations=recommendations,
            citations=self.citations,
            metadata={
                "annual_mortality_percent": annual_mortality,
                "five_year_survival_percent": five_year_survival
            }
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "exercise_time_minutes": {"type": "float", "unit": "minutes", "min": 0, "max": 30, "required": True},
                "max_st_deviation_mm": {"type": "float", "unit": "mm", "min": 0, "max": 10, "required": True},
                "angina_index": {"type": "integer", "choices": [0, 1, 2], "description": "0=none, 1=non-limiting, 2=limiting", "required": True},
            }
        }


class CorrectedQTCalculator(Calculator):
    """
    Corrected QT Interval (QTc)

    Calculates heart rate-corrected QT interval using Bazett's formula.

    Reference: Bazett HC. Heart 1920
    """

    def __init__(self):
        super().__init__()
        self.category = "cardiovascular"
        self.description = "QT interval correction for heart rate"
        self.citations = ["Bazett HC. Heart. 1920;7:353-370"]

    def calculate(
        self,
        qt_interval_ms: float,
        heart_rate: Optional[int] = None,
        rr_interval_ms: Optional[float] = None,
        sex: str = "male",
    ) -> CalculatorResult:
        """
        Calculate corrected QT interval.

        Args:
            qt_interval_ms: QT interval in milliseconds
            heart_rate: Heart rate in bpm (optional if RR provided)
            rr_interval_ms: RR interval in milliseconds (optional if HR provided)
            sex: 'male' or 'female'
        """
        self.validate_range(qt_interval_ms, 200, 700, "qt_interval_ms")
        self.validate_choice(sex, ["male", "female"], "sex")

        # Calculate RR interval
        if rr_interval_ms is not None:
            rr_seconds = rr_interval_ms / 1000
        elif heart_rate is not None:
            self.validate_range(heart_rate, 30, 200, "heart_rate")
            rr_seconds = 60 / heart_rate
        else:
            raise ValidationError("Either heart_rate or rr_interval_ms must be provided")

        # Bazett's formula: QTc = QT / √RR
        qtc = qt_interval_ms / math.sqrt(rr_seconds)

        # Interpret results
        if sex == "male":
            if qtc < 430:
                risk_level = RiskLevel.LOW
                interpretation = "Normal QTc for males"
                warnings = None
            elif qtc < 450:
                risk_level = RiskLevel.LOW
                interpretation = "Borderline QTc for males"
                warnings = ["Monitor for QT-prolonging medications"]
            elif qtc < 500:
                risk_level = RiskLevel.MODERATE
                interpretation = "Prolonged QTc for males"
                warnings = ["Increased risk of torsades de pointes", "Avoid QT-prolonging drugs"]
            else:
                risk_level = RiskLevel.HIGH
                interpretation = "Severely prolonged QTc for males"
                warnings = ["High risk of torsades de pointes", "Cardiology consultation", "Correct electrolytes"]
        else:
            if qtc < 450:
                risk_level = RiskLevel.LOW
                interpretation = "Normal QTc for females"
                warnings = None
            elif qtc < 470:
                risk_level = RiskLevel.LOW
                interpretation = "Borderline QTc for females"
                warnings = ["Monitor for QT-prolonging medications"]
            elif qtc < 500:
                risk_level = RiskLevel.MODERATE
                interpretation = "Prolonged QTc for females"
                warnings = ["Increased risk of torsades de pointes", "Avoid QT-prolonging drugs"]
            else:
                risk_level = RiskLevel.HIGH
                interpretation = "Severely prolonged QTc for females"
                warnings = ["High risk of torsades de pointes", "Cardiology consultation", "Correct electrolytes"]

        return CalculatorResult(
            value=round(qtc, 0),
            interpretation=interpretation,
            risk_level=risk_level,
            reference_range="Male: <430 normal, 430-450 borderline, >450 prolonged; Female: <450 normal, 450-470 borderline, >470 prolonged",
            recommendations=["Check electrolytes (K, Mg, Ca)", "Review medications", "ECG monitoring if prolonged"],
            citations=self.citations,
            warnings=warnings,
            metadata={"unit": "ms", "formula": "Bazett"}
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "qt_interval_ms": {"type": "float", "unit": "ms", "min": 200, "max": 700, "required": True},
                "heart_rate": {"type": "integer", "unit": "bpm", "min": 30, "max": 200, "required": False},
                "rr_interval_ms": {"type": "float", "unit": "ms", "required": False},
                "sex": {"type": "string", "choices": ["male", "female"], "required": True},
            }
        }
