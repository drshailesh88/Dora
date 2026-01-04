"""
Information card generation for drugs, diseases, and calculations.

This module provides utilities for creating compact, scannable information
cards for medical entities.
"""

from typing import List, Dict, Any, Optional
from .models import DrugCard, CalculatorResult, EvidenceBadge, Citation


class CardBuilder:
    """Build information cards for medical entities."""

    @staticmethod
    def create_drug_card(
        name: str,
        generic_name: Optional[str] = None,
        drug_class: Optional[str] = None,
        mechanism: Optional[str] = None,
        indications: Optional[List[str]] = None,
        dosing: Optional[str] = None,
        contraindications: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        interactions: Optional[List[str]] = None,
        side_effects: Optional[List[str]] = None,
        monitoring: Optional[str] = None,
        evidence: Optional[EvidenceBadge] = None,
    ) -> DrugCard:
        """
        Create a drug information card.

        Args:
            name: Brand/trade name
            generic_name: Generic name
            drug_class: Pharmacologic class
            mechanism: Mechanism of action
            indications: List of indications
            dosing: Standard dosing
            contraindications: List of contraindications
            warnings: Black box/major warnings
            interactions: Key drug interactions
            side_effects: Common side effects
            monitoring: Required monitoring
            evidence: Evidence quality

        Returns:
            Formatted drug card
        """
        return DrugCard(
            name=name,
            generic_name=generic_name,
            class_name=drug_class,
            mechanism=mechanism,
            indications=indications or [],
            dosing=dosing,
            contraindications=contraindications or [],
            warnings=warnings or [],
            interactions=interactions or [],
            side_effects=side_effects or [],
            monitoring=monitoring,
            evidence=evidence,
        )

    @staticmethod
    def create_calculator_result_card(
        calculator_name: str,
        result_value: str,
        interpretation: str,
        inputs: Dict[str, Any],
        risk_category: Optional[str] = None,
        recommendations: Optional[List[str]] = None,
        evidence: Optional[EvidenceBadge] = None,
        citations: Optional[List[Citation]] = None,
    ) -> CalculatorResult:
        """
        Create calculator result card.

        Args:
            calculator_name: Name of calculator
            result_value: Calculated value
            interpretation: Clinical interpretation
            inputs: Input parameters used
            risk_category: Risk stratification
            recommendations: Clinical recommendations
            evidence: Calculator validation evidence
            citations: Supporting references

        Returns:
            Formatted calculator result
        """
        return CalculatorResult(
            calculator_name=calculator_name,
            result_value=result_value,
            interpretation=interpretation,
            risk_category=risk_category,
            recommendations=recommendations or [],
            inputs=inputs,
            evidence=evidence,
            citations=citations,
        )


def create_aspirin_card() -> DrugCard:
    """Example: Aspirin drug card."""
    return CardBuilder.create_drug_card(
        name="Aspirin",
        generic_name="Acetylsalicylic Acid",
        drug_class="Antiplatelet Agent, NSAID",
        mechanism="Irreversibly inhibits COX-1 and COX-2, reducing platelet aggregation and prostaglandin synthesis",
        indications=[
            "Acute coronary syndrome",
            "Ischemic stroke prevention",
            "Post-MI prophylaxis",
            "Pain/fever (analgesic/antipyretic)",
        ],
        dosing="ACS: 162-325mg loading, then 81mg daily. Stroke prevention: 81mg daily. Pain: 325-650mg q4-6h PRN",
        contraindications=[
            "Active bleeding",
            "Hemophilia",
            "Peptic ulcer disease",
            "Severe renal/hepatic impairment",
            "Children with viral illness (Reye's syndrome risk)",
        ],
        warnings=[
            "Increased bleeding risk",
            "GI ulceration/bleeding",
            "Reye's syndrome in children",
        ],
        interactions=[
            "Warfarin/anticoagulants (increased bleeding)",
            "Other NSAIDs (reduced cardioprotection)",
            "Methotrexate (increased toxicity)",
        ],
        side_effects=[
            "Dyspepsia",
            "GI bleeding",
            "Bruising",
            "Tinnitus (high doses)",
        ],
        monitoring="CBC if long-term use, renal function, signs of bleeding",
    )


def create_chads2vasc_result(
    age: int,
    sex: str,
    chf: bool,
    hypertension: bool,
    stroke_tia: bool,
    vascular_disease: bool,
    diabetes: bool,
) -> CalculatorResult:
    """
    Calculate and create CHA2DS2-VASc score result card.

    Args:
        age: Patient age
        sex: Patient sex (M/F)
        chf: Congestive heart failure
        hypertension: Hypertension
        stroke_tia: Prior stroke/TIA
        vascular_disease: Vascular disease
        diabetes: Diabetes

    Returns:
        Calculator result card with anticoagulation recommendation
    """
    score = 0

    # CHF
    if chf:
        score += 1

    # Hypertension
    if hypertension:
        score += 1

    # Age ≥75
    if age >= 75:
        score += 2
    elif age >= 65:
        score += 1

    # Diabetes
    if diabetes:
        score += 1

    # Stroke/TIA
    if stroke_tia:
        score += 2

    # Vascular disease
    if vascular_disease:
        score += 1

    # Sex (female)
    if sex.upper() == "F":
        score += 1

    # Interpretation
    if score == 0:
        interpretation = "Very low risk of stroke"
        risk_category = "Low Risk"
        recommendations = [
            "No anticoagulation recommended",
            "Consider aspirin or no treatment",
        ]
    elif score == 1:
        if sex.upper() == "F":
            interpretation = "Low risk (score 1 from sex only)"
            risk_category = "Low Risk"
            recommendations = [
                "Consider no treatment or aspirin",
                "Shared decision-making",
            ]
        else:
            interpretation = "Low-moderate risk"
            risk_category = "Moderate Risk"
            recommendations = [
                "Consider oral anticoagulation",
                "Discuss risks/benefits with patient",
            ]
    else:  # score ≥2
        interpretation = "Moderate to high risk of stroke"
        risk_category = "High Risk"
        recommendations = [
            "Oral anticoagulation recommended (unless contraindicated)",
            "Options: Warfarin (INR 2-3) or DOAC (apixaban, rivaroxaban, edoxaban, dabigatran)",
            "Assess HAS-BLED score for bleeding risk",
        ]

    inputs = {
        "age": age,
        "sex": sex,
        "congestive_heart_failure": chf,
        "hypertension": hypertension,
        "stroke_tia_history": stroke_tia,
        "vascular_disease": vascular_disease,
        "diabetes": diabetes,
    }

    return CardBuilder.create_calculator_result_card(
        calculator_name="CHA₂DS₂-VASc Score",
        result_value=str(score),
        interpretation=interpretation,
        risk_category=risk_category,
        recommendations=recommendations,
        inputs=inputs,
    )


def create_wells_dvt_result(
    active_cancer: bool,
    paralysis_paresis: bool,
    bedridden_recent_surgery: bool,
    localized_tenderness: bool,
    entire_leg_swollen: bool,
    calf_swelling: bool,
    pitting_edema: bool,
    collateral_veins: bool,
    alternative_diagnosis: bool,
) -> CalculatorResult:
    """
    Calculate and create Wells DVT score result card.

    Returns:
        Calculator result with DVT probability and testing recommendation
    """
    score = 0

    if active_cancer:
        score += 1
    if paralysis_paresis:
        score += 1
    if bedridden_recent_surgery:
        score += 1
    if localized_tenderness:
        score += 1
    if entire_leg_swollen:
        score += 1
    if calf_swelling:
        score += 1
    if pitting_edema:
        score += 1
    if collateral_veins:
        score += 1
    if alternative_diagnosis:
        score -= 2

    # Interpretation
    if score <= 0:
        interpretation = "Low probability of DVT (5%)"
        risk_category = "Low Probability"
        recommendations = [
            "D-dimer testing",
            "If D-dimer negative, DVT ruled out",
            "If D-dimer positive, proceed to ultrasound",
        ]
    elif score <= 2:
        interpretation = "Moderate probability of DVT (17%)"
        risk_category = "Moderate Probability"
        recommendations = [
            "D-dimer testing",
            "If negative, DVT unlikely",
            "If positive, venous ultrasound required",
        ]
    else:  # score ≥3
        interpretation = "High probability of DVT (53%)"
        risk_category = "High Probability"
        recommendations = [
            "Proceed directly to venous duplex ultrasound",
            "Consider empiric anticoagulation while awaiting results if clinically appropriate",
        ]

    inputs = {
        "active_cancer": active_cancer,
        "paralysis_or_paresis": paralysis_paresis,
        "bedridden_or_recent_surgery": bedridden_recent_surgery,
        "localized_tenderness": localized_tenderness,
        "entire_leg_swollen": entire_leg_swollen,
        "calf_swelling_3cm": calf_swelling,
        "pitting_edema": pitting_edema,
        "collateral_superficial_veins": collateral_veins,
        "alternative_diagnosis_likely": alternative_diagnosis,
    }

    return CardBuilder.create_calculator_result_card(
        calculator_name="Wells DVT Score",
        result_value=str(score),
        interpretation=interpretation,
        risk_category=risk_category,
        recommendations=recommendations,
        inputs=inputs,
    )


def create_gcs_result(eye_response: int, verbal_response: int, motor_response: int) -> CalculatorResult:
    """
    Calculate Glasgow Coma Scale result.

    Args:
        eye_response: Eye opening (1-4)
        verbal_response: Verbal response (1-5)
        motor_response: Motor response (1-6)

    Returns:
        GCS calculator result
    """
    score = eye_response + verbal_response + motor_response

    if score <= 8:
        interpretation = "Severe brain injury / Coma"
        risk_category = "Severe"
        recommendations = [
            "Airway management - consider intubation",
            "CT head emergent",
            "Neurosurgery consult",
            "ICU admission",
        ]
    elif score <= 12:
        interpretation = "Moderate brain injury"
        risk_category = "Moderate"
        recommendations = [
            "CT head",
            "Close monitoring",
            "Consider ICU vs step-down",
            "Neurosurgery evaluation",
        ]
    else:  # score 13-15
        interpretation = "Mild brain injury"
        risk_category = "Mild"
        recommendations = [
            "CT head if indicated by clinical criteria",
            "Observation",
            "Discharge instructions for head injury",
        ]

    inputs = {
        "eye_opening": eye_response,
        "verbal_response": verbal_response,
        "motor_response": motor_response,
    }

    return CardBuilder.create_calculator_result_card(
        calculator_name="Glasgow Coma Scale (GCS)",
        result_value=f"{score}/15",
        interpretation=interpretation,
        risk_category=risk_category,
        recommendations=recommendations,
        inputs=inputs,
    )


def format_drug_card_markdown(card: DrugCard) -> str:
    """
    Format drug card as markdown.

    Args:
        card: Drug card to format

    Returns:
        Markdown representation
    """
    lines = [f"# {card.name}"]

    if card.generic_name:
        lines.append(f"*{card.generic_name}*")

    if card.class_name:
        lines.append(f"\n**Class:** {card.class_name}")

    if card.mechanism:
        lines.append(f"\n**Mechanism:** {card.mechanism}")

    if card.indications:
        lines.append("\n**Indications:**")
        for indication in card.indications:
            lines.append(f"- {indication}")

    if card.dosing:
        lines.append(f"\n**Dosing:** {card.dosing}")

    if card.warnings:
        lines.append("\n**⚠️ Warnings:**")
        for warning in card.warnings:
            lines.append(f"- {warning}")

    if card.contraindications:
        lines.append("\n**Contraindications:**")
        for ci in card.contraindications:
            lines.append(f"- {ci}")

    if card.side_effects:
        lines.append("\n**Side Effects:**")
        for se in card.side_effects[:5]:  # Top 5
            lines.append(f"- {se}")

    if card.interactions:
        lines.append("\n**Key Interactions:**")
        for interaction in card.interactions:
            lines.append(f"- {interaction}")

    if card.monitoring:
        lines.append(f"\n**Monitoring:** {card.monitoring}")

    return "\n".join(lines)
