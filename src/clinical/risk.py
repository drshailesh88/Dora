"""
Risk Stratification Module for Clinical Decision Support

Clinical risk calculators with interpretation and action recommendations.

Includes:
- ASCVD Risk (10-year cardiovascular risk)
- CHADS2-VASc (stroke risk in AFib)
- HAS-BLED (bleeding risk on anticoagulation)
- Wells Score (DVT/PE)
- CURB-65 (pneumonia severity)
- HEART Score (chest pain)
- TIMI Risk Score (ACS)
- CHA2DS2-VASc
- MELD Score (liver disease severity)
- Glasgow Coma Scale

MEDICAL DISCLAIMER:
These are screening tools to guide clinical decision-making.
Always use clinical judgment and consider individual patient factors.
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import math


class RiskLevel(Enum):
    """Risk categorization"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class RiskScore:
    """Risk calculation result"""
    score_name: str
    score_value: float
    risk_level: RiskLevel
    interpretation: str
    recommendations: List[str]
    risk_percentage: Optional[float] = None
    references: List[str] = None


class RiskCalculator:
    """
    Clinical risk stratification calculators.
    """

    def calculate_ascvd_risk(
        self,
        age: int,
        gender: str,
        race: str,
        total_cholesterol: float,
        hdl: float,
        systolic_bp: float,
        on_bp_meds: bool,
        diabetic: bool,
        smoker: bool
    ) -> RiskScore:
        """
        ASCVD 10-year risk calculator (Pooled Cohort Equations).

        Args:
            age: 40-79 years
            gender: "M" or "F"
            race: "white" or "black"
            total_cholesterol: mg/dL
            hdl: mg/dL
            systolic_bp: mmHg
            on_bp_meds: Boolean
            diabetic: Boolean
            smoker: Boolean

        Returns:
            RiskScore with 10-year ASCVD risk percentage
        """
        # Simplified calculation - actual PCE is more complex
        # This is an approximation

        ln_age = math.log(age)
        ln_tc = math.log(total_cholesterol)
        ln_hdl = math.log(hdl)
        ln_sbp_treated = math.log(systolic_bp) if on_bp_meds else 0
        ln_sbp_untreated = math.log(systolic_bp) if not on_bp_meds else 0

        # Coefficients (simplified - actual coefficients vary by race/gender)
        if gender == "M":
            if race == "white":
                ind_sum = (
                    12.344 * ln_age +
                    11.853 * ln_tc +
                    -2.664 * ln_hdl +
                    -7.990 * ln_hdl * ln_age +
                    1.769 * ln_sbp_treated +
                    1.797 * ln_sbp_untreated +
                    (0.658 if diabetic else 0) +
                    (0.549 if smoker else 0)
                )
                baseline_survival = 0.9144
                mean_coef_sum = 61.18
            else:  # Black
                ind_sum = (
                    2.469 * ln_age +
                    0.302 * ln_tc +
                    -0.307 * ln_hdl +
                    1.916 * ln_sbp_treated +
                    1.809 * ln_sbp_untreated +
                    (0.549 if diabetic else 0) +
                    (0.645 if smoker else 0)
                )
                baseline_survival = 0.8954
                mean_coef_sum = 19.54
        else:  # Female
            if race == "white":
                ind_sum = (
                    -29.799 * ln_age +
                    4.884 * ln_age**2 +
                    13.540 * ln_tc +
                    -3.114 * ln_hdl +
                    -13.578 * ln_hdl * ln_age +
                    2.019 * ln_sbp_treated +
                    1.957 * ln_sbp_untreated +
                    (0.661 if diabetic else 0) +
                    (0.817 if smoker else 0)
                )
                baseline_survival = 0.9665
                mean_coef_sum = -29.18
            else:  # Black
                ind_sum = (
                    17.114 * ln_age +
                    0.940 * ln_tc +
                    -18.920 * ln_hdl +
                    4.475 * ln_hdl * ln_age +
                    29.291 * ln_sbp_treated +
                    -6.432 * ln_sbp_treated * ln_age +
                    27.820 * ln_sbp_untreated +
                    -6.087 * ln_sbp_untreated * ln_age +
                    (0.691 if diabetic else 0) +
                    (0.874 if smoker else 0)
                )
                baseline_survival = 0.9533
                mean_coef_sum = 86.61

        # Calculate 10-year risk
        risk_10yr = (1 - baseline_survival ** math.exp(ind_sum - mean_coef_sum)) * 100

        # Risk stratification
        if risk_10yr < 5:
            risk_level = RiskLevel.LOW
            interpretation = f"Low risk ({risk_10yr:.1f}%): Lifestyle modifications, consider statin if LDL >190 or family history"
            recommendations = [
                "Lifestyle: Diet, exercise, weight loss",
                "Repeat lipid panel in 3-5 years",
                "Consider statin if LDL ≥190 mg/dL or strong family history"
            ]
        elif risk_10yr < 7.5:
            risk_level = RiskLevel.MODERATE
            interpretation = f"Borderline risk ({risk_10yr:.1f}%): Consider statin if risk enhancers present"
            recommendations = [
                "Lifestyle modifications",
                "Consider statin if risk enhancers: family history, LDL ≥160, CRP ≥2, CAC score",
                "Shared decision-making"
            ]
        elif risk_10yr < 20:
            risk_level = RiskLevel.HIGH
            interpretation = f"Intermediate-high risk ({risk_10yr:.1f}%): Statin recommended"
            recommendations = [
                "Moderate-intensity statin (Atorvastatin 10-20mg or Rosuvastatin 5-10mg)",
                "LDL goal <100 mg/dL",
                "Lifestyle modifications",
                "Consider aspirin if high bleeding risk is low"
            ]
        else:
            risk_level = RiskLevel.VERY_HIGH
            interpretation = f"High risk ({risk_10yr:.1f}%): High-intensity statin recommended"
            recommendations = [
                "High-intensity statin (Atorvastatin 40-80mg or Rosuvastatin 20-40mg)",
                "LDL goal <70 mg/dL (consider <55 if very high risk)",
                "Add ezetimibe if LDL not at goal on statin",
                "Aspirin 81mg daily",
                "Blood pressure control <130/80",
                "Diabetes control if present"
            ]

        return RiskScore(
            score_name="ASCVD 10-Year Risk",
            score_value=risk_10yr,
            risk_level=risk_level,
            risk_percentage=risk_10yr,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["2019 ACC/AHA Primary Prevention Guidelines", "Pooled Cohort Equations"]
        )

    def calculate_chads_vasc(
        self,
        age: int,
        gender: str,
        chf: bool,
        hypertension: bool,
        stroke_tia: bool,
        vascular_disease: bool,
        diabetes: bool
    ) -> RiskScore:
        """
        CHA2DS2-VASc score for stroke risk in atrial fibrillation.

        Points:
        - CHF: 1
        - Hypertension: 1
        - Age ≥75: 2
        - Diabetes: 1
        - Stroke/TIA/Thromboembolism: 2
        - Vascular disease: 1
        - Age 65-74: 1
        - Sex (Female): 1
        """
        score = 0

        if chf:
            score += 1
        if hypertension:
            score += 1
        if age >= 75:
            score += 2
        elif age >= 65:
            score += 1
        if diabetes:
            score += 1
        if stroke_tia:
            score += 2
        if vascular_disease:
            score += 1
        if gender == "F":
            score += 1

        # Annual stroke risk
        stroke_risks = {
            0: 0, 1: 1.3, 2: 2.2, 3: 3.2, 4: 4.0, 5: 6.7,
            6: 9.8, 7: 9.6, 8: 6.7, 9: 15.2
        }
        annual_risk = stroke_risks.get(score, 15)

        if score == 0:
            risk_level = RiskLevel.LOW
            interpretation = f"Score {score}: Low risk (~0% annual stroke risk)"
            recommendations = [
                "No anticoagulation recommended",
                "Consider aspirin (but no proven benefit)",
                "Reassess annually"
            ]
        elif score == 1:
            risk_level = RiskLevel.LOW
            if gender == "F":
                interpretation = f"Score {score}: Low risk (~1.3% annual stroke risk) - score of 1 due to female gender alone"
                recommendations = [
                    "Anticoagulation reasonable but not mandatory",
                    "Shared decision-making",
                    "Consider patient preference and bleeding risk"
                ]
            else:
                interpretation = f"Score {score}: Low-moderate risk (~1.3% annual stroke risk)"
                recommendations = [
                    "Consider anticoagulation (Class IIa recommendation)",
                    "Evaluate HAS-BLED bleeding risk",
                    "Shared decision-making"
                ]
        else:  # Score ≥2
            risk_level = RiskLevel.HIGH
            interpretation = f"Score {score}: High risk (~{annual_risk}% annual stroke risk)"
            recommendations = [
                "Anticoagulation RECOMMENDED (Class I)",
                "DOAC preferred over warfarin (apixaban, rivaroxaban, edoxaban, dabigatran)",
                "If DOAC contraindicated: Warfarin (INR 2-3)",
                "Assess HAS-BLED bleeding risk",
                "NO aspirin (inferior to anticoagulation)"
            ]

        return RiskScore(
            score_name="CHA2DS2-VASc Score",
            score_value=score,
            risk_level=risk_level,
            risk_percentage=annual_risk,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["2020 ESC AFib Guidelines", "Lip et al. Chest 2010"]
        )

    def calculate_has_bled(
        self,
        hypertension: bool,
        abnormal_renal_liver: bool,
        stroke_history: bool,
        bleeding_history: bool,
        labile_inr: bool,
        elderly: bool,  # >65
        drugs_alcohol: bool
    ) -> RiskScore:
        """
        HAS-BLED score for bleeding risk on anticoagulation.

        Points (max 9):
        H - Hypertension (SBP >160): 1
        A - Abnormal renal/liver function (1 point each): 1-2
        S - Stroke history: 1
        B - Bleeding history or predisposition: 1
        L - Labile INR (<60% time in therapeutic range): 1
        E - Elderly (>65 years): 1
        D - Drugs (antiplatelet, NSAIDs) or alcohol (≥8 drinks/week): 1-2
        """
        score = 0

        if hypertension:
            score += 1
        if abnormal_renal_liver:
            score += 1  # Can be 1 or 2 if both
        if stroke_history:
            score += 1
        if bleeding_history:
            score += 1
        if labile_inr:
            score += 1
        if elderly:
            score += 1
        if drugs_alcohol:
            score += 1  # Can be 1 or 2

        # Annual major bleeding risk
        if score <= 2:
            risk_level = RiskLevel.LOW
            bleed_risk = "1-3%"
            interpretation = f"Score {score}: Low bleeding risk ({bleed_risk} annual major bleeding)"
            recommendations = [
                "Anticoagulation is safe",
                "Routine monitoring",
                "Address modifiable risk factors"
            ]
        elif score == 3:
            risk_level = RiskLevel.MODERATE
            bleed_risk = "4-6%"
            interpretation = f"Score {score}: Moderate bleeding risk ({bleed_risk} annual major bleeding)"
            recommendations = [
                "Anticoagulation generally safe if indicated",
                "Address modifiable risk factors (BP control, avoid NSAIDs, reduce alcohol)",
                "More frequent monitoring",
                "Consider gastric protection (PPI) if GI bleed history"
            ]
        else:  # Score ≥4
            risk_level = RiskLevel.HIGH
            bleed_risk = ">8%"
            interpretation = f"Score {score}: High bleeding risk ({bleed_risk} annual major bleeding)"
            recommendations = [
                "Anticoagulation may still be indicated if stroke risk high",
                "Carefully weigh risks vs benefits",
                "Address ALL modifiable risk factors",
                "Frequent monitoring",
                "Consider left atrial appendage occlusion if bleeding risk prohibitive"
            ]

        return RiskScore(
            score_name="HAS-BLED Score",
            score_value=score,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["Pisters et al. Chest 2010"]
        )

    def calculate_wells_dvt(
        self,
        active_cancer: bool,
        paralysis_paresis: bool,
        bedridden: bool,
        localized_tenderness: bool,
        entire_leg_swollen: bool,
        calf_swelling: bool,
        pitting_edema: bool,
        collateral_veins: bool,
        alternative_diagnosis: bool
    ) -> RiskScore:
        """
        Wells Score for DVT probability.
        """
        score = 0

        if active_cancer:
            score += 1
        if paralysis_paresis:
            score += 1
        if bedridden:
            score += 1
        if localized_tenderness:
            score += 1
        if entire_leg_swollen:
            score += 1
        if calf_swelling:
            score += 1  # >3cm difference
        if pitting_edema:
            score += 1
        if collateral_veins:
            score += 1
        if alternative_diagnosis:
            score -= 2

        if score <= 0:
            risk_level = RiskLevel.LOW
            interpretation = f"Score {score}: DVT unlikely (5% prevalence)"
            recommendations = [
                "D-dimer test",
                "If D-dimer negative: DVT ruled out",
                "If D-dimer positive: Doppler ultrasound"
            ]
        elif score <= 2:
            risk_level = RiskLevel.MODERATE
            interpretation = f"Score {score}: Moderate probability (17% prevalence)"
            recommendations = [
                "D-dimer test OR proceed to Doppler ultrasound",
                "If D-dimer negative and low clinical suspicion: DVT unlikely",
                "If D-dimer positive: Doppler ultrasound"
            ]
        else:
            risk_level = RiskLevel.HIGH
            interpretation = f"Score {score}: DVT likely (53% prevalence)"
            recommendations = [
                "Proceed directly to Doppler ultrasound (skip D-dimer)",
                "If ultrasound positive: Treat for DVT",
                "If ultrasound negative: Repeat in 1 week if high suspicion persists"
            ]

        return RiskScore(
            score_name="Wells Score for DVT",
            score_value=score,
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["Wells PS et al. Lancet 1997"]
        )

    def calculate_curb65(
        self,
        confusion: bool,
        urea: float,  # mg/dL
        respiratory_rate: int,
        systolic_bp: int,
        diastolic_bp: int,
        age: int
    ) -> RiskScore:
        """
        CURB-65 score for pneumonia severity.

        C - Confusion (new onset)
        U - Urea >20 mg/dL (BUN >20)
        R - Respiratory rate ≥30
        B - Blood pressure (SBP <90 or DBP ≤60)
        65 - Age ≥65
        """
        score = 0

        if confusion:
            score += 1
        if urea > 20:
            score += 1
        if respiratory_rate >= 30:
            score += 1
        if systolic_bp < 90 or diastolic_bp <= 60:
            score += 1
        if age >= 65:
            score += 1

        mortality_rates = {
            0: 0.7, 1: 2.7, 2: 6.8, 3: 14.0, 4: 27.8, 5: 27.8
        }
        mortality = mortality_rates.get(score, 27.8)

        if score <= 1:
            risk_level = RiskLevel.LOW
            interpretation = f"Score {score}: Low severity (~{mortality}% 30-day mortality)"
            recommendations = [
                "Outpatient treatment appropriate",
                "Oral antibiotics (amoxicillin or doxycycline)",
                "Close outpatient follow-up"
            ]
        elif score == 2:
            risk_level = RiskLevel.MODERATE
            interpretation = f"Score {score}: Moderate severity (~{mortality}% 30-day mortality)"
            recommendations = [
                "Consider hospital admission",
                "If social support good and patient stable: may treat outpatient with close follow-up",
                "IV or PO antibiotics (beta-lactam + macrolide or fluoroquinolone)"
            ]
        else:  # Score ≥3
            risk_level = RiskLevel.HIGH
            interpretation = f"Score {score}: High severity (~{mortality}% 30-day mortality)"
            recommendations = [
                "Hospital admission RECOMMENDED",
                "Consider ICU if score ≥4",
                "IV antibiotics (ceftriaxone + azithromycin)",
                "Monitor for complications"
            ]

        return RiskScore(
            score_name="CURB-65 Score",
            score_value=score,
            risk_level=risk_level,
            risk_percentage=mortality,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["Lim WS et al. Thorax 2003"]
        )

    def calculate_heart_score(
        self,
        age: int,
        risk_factors: int,  # Number of CV risk factors (0-6)
        history_cad: bool,
        ecg_findings: str,  # "normal", "nonspecific", "significant"
        troponin_elevation: str  # "normal", "1-3x", ">3x"
    ) -> RiskScore:
        """
        HEART Score for chest pain.

        H - History: highly suspicious (2), moderately (1), slightly (0)
        E - ECG: significant ST depression (2), nonspecific repol (1), normal (0)
        A - Age: ≥65 (2), 45-64 (1), <45 (0)
        R - Risk factors: ≥3 (2), 1-2 (1), 0 (0)
        T - Troponin: >3x normal (2), 1-3x (1), normal (0)
        """
        # Simplified - would need more detailed history assessment
        score = 0

        # Age
        if age >= 65:
            score += 2
        elif age >= 45:
            score += 1

        # Risk factors (HTN, DM, smoking, family hx, dyslipidemia, obesity)
        if risk_factors >= 3:
            score += 2
        elif risk_factors >= 1:
            score += 1

        # History of CAD
        if history_cad:
            score += 2  # Likely "highly suspicious" if known CAD

        # ECG
        if ecg_findings == "significant":
            score += 2
        elif ecg_findings == "nonspecific":
            score += 1

        # Troponin
        if troponin_elevation == ">3x":
            score += 2
        elif troponin_elevation == "1-3x":
            score += 1

        # MACE risk (Major Adverse Cardiac Events at 6 weeks)
        mace_risks = {
            0: 1.7, 1: 1.7, 2: 1.7, 3: 2.5, 4: 12.3, 5: 20.3,
            6: 40.8, 7: 65.2, 8: 65.2, 9: 65.2, 10: 65.2
        }
        mace = mace_risks.get(score, 65)

        if score <= 3:
            risk_level = RiskLevel.LOW
            interpretation = f"Score {score}: Low risk (~{mace}% MACE at 6 weeks)"
            recommendations = [
                "Safe for early discharge",
                "Outpatient follow-up with cardiology",
                "Stress testing as outpatient",
                "Aspirin, statin if not already on"
            ]
        elif score <= 6:
            risk_level = RiskLevel.MODERATE
            interpretation = f"Score {score}: Moderate risk (~{mace}% MACE at 6 weeks)"
            recommendations = [
                "Admit for observation",
                "Serial troponins",
                "Consider provocative testing (stress test or CTA)",
                "Cardiology consultation"
            ]
        else:  # Score ≥7
            risk_level = RiskLevel.HIGH
            interpretation = f"Score {score}: High risk (~{mace}% MACE at 6 weeks)"
            recommendations = [
                "Admit to telemetry or CCU",
                "Cardiology consult",
                "Early invasive strategy (angiography)",
                "Dual antiplatelet therapy, anticoagulation, statin"
            ]

        return RiskScore(
            score_name="HEART Score",
            score_value=score,
            risk_level=risk_level,
            risk_percentage=mace,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["Six AJ et al. Neth Heart J 2008"]
        )

    def calculate_meld_score(
        self,
        creatinine: float,
        bilirubin: float,
        inr: float,
        dialysis: bool = False
    ) -> RiskScore:
        """
        MELD score for liver disease severity and transplant prioritization.

        MELD = 3.78×ln[bilirubin (mg/dL)] + 11.2×ln[INR] + 9.57×ln[creatinine (mg/dL)] + 6.43
        """
        # Cap values
        creatinine = min(max(creatinine, 1.0), 4.0)
        if dialysis:
            creatinine = 4.0

        bilirubin = max(bilirubin, 1.0)
        inr = max(inr, 1.0)

        meld = (
            3.78 * math.log(bilirubin) +
            11.2 * math.log(inr) +
            9.57 * math.log(creatinine) +
            6.43
        )
        meld = round(meld)
        meld = max(6, min(meld, 40))  # Range 6-40

        # 3-month mortality
        if meld < 10:
            mortality = 1.9
            risk_level = RiskLevel.LOW
        elif meld < 20:
            mortality = 6.0
            risk_level = RiskLevel.MODERATE
        elif meld < 30:
            mortality = 19.6
            risk_level = RiskLevel.HIGH
        else:
            mortality = 52.6
            risk_level = RiskLevel.VERY_HIGH

        if meld < 15:
            interpretation = f"MELD {meld}: Mild liver disease (~{mortality}% 3-month mortality)"
            recommendations = [
                "Manage complications (ascites, varices, encephalopathy)",
                "Regular follow-up",
                "Not yet transplant candidate"
            ]
        elif meld < 25:
            interpretation = f"MELD {meld}: Moderate-severe liver disease (~{mortality}% 3-month mortality)"
            recommendations = [
                "Hepatology referral",
                "Consider transplant evaluation if MELD ≥15",
                "Manage complications",
                "Avoid nephrotoxins, hepatotoxins"
            ]
        else:
            interpretation = f"MELD {meld}: Severe liver disease (~{mortality}% 3-month mortality)"
            recommendations = [
                "Urgent transplant evaluation",
                "Hepatology/transplant hepatology management",
                "Consider MELD exceptions (HCC, etc.)",
                "ICU monitoring if decompensated"
            ]

        return RiskScore(
            score_name="MELD Score",
            score_value=meld,
            risk_level=risk_level,
            risk_percentage=mortality,
            interpretation=interpretation,
            recommendations=recommendations,
            references=["Kamath PS et al. Hepatology 2001", "UNOS"]
        )


def calculate_risk_score(score_name: str, **params) -> Optional[Dict]:
    """
    Calculate risk score.

    Args:
        score_name: Name of score (ascvd, chads_vasc, has_bled, wells_dvt, curb65, heart, meld)
        **params: Score-specific parameters

    Returns:
        Dictionary with risk score results

    Example:
        >>> result = calculate_risk_score("chads_vasc", age=75, gender="M", chf=True,
        ...                                hypertension=True, stroke_tia=False,
        ...                                vascular_disease=True, diabetes=False)
    """
    calculator = RiskCalculator()

    score_methods = {
        'ascvd': calculator.calculate_ascvd_risk,
        'chads_vasc': calculator.calculate_chads_vasc,
        'chadsvasc': calculator.calculate_chads_vasc,
        'has_bled': calculator.calculate_has_bled,
        'hasbled': calculator.calculate_has_bled,
        'wells_dvt': calculator.calculate_wells_dvt,
        'curb65': calculator.calculate_curb65,
        'curb_65': calculator.calculate_curb65,
        'heart': calculator.calculate_heart_score,
        'meld': calculator.calculate_meld_score,
    }

    method = score_methods.get(score_name.lower())
    if not method:
        return {'error': f'Unknown risk score: {score_name}'}

    try:
        result = method(**params)
        return {
            'score_name': result.score_name,
            'score_value': result.score_value,
            'risk_level': result.risk_level.value,
            'risk_percentage': result.risk_percentage,
            'interpretation': result.interpretation,
            'recommendations': result.recommendations,
            'references': result.references
        }
    except Exception as e:
        return {'error': str(e)}
