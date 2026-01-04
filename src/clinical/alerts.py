"""
Clinical Alert Engine for Decision Support

Provides safety alerts for:
- Critical lab values
- Drug allergies
- Drug-drug interactions
- Contraindications
- Dose limit warnings
- Duplicate therapy

MEDICAL DISCLAIMER:
This is a clinical decision support tool. Alerts should be reviewed in clinical
context. Not all alerts require action. Use clinical judgment.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"              # Informational
    WARNING = "warning"        # Important but not critical
    CRITICAL = "critical"      # Requires immediate attention
    LIFE_THREATENING = "life_threatening"  # Immediate action required


@dataclass
class ClinicalAlert:
    """Clinical decision support alert"""
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    recommendations: List[str]
    override_reason_required: bool = False


class AlertEngine:
    """
    Clinical alert generation system.
    """

    def __init__(self):
        self._initialize_alert_rules()

    def _initialize_alert_rules(self):
        """Initialize alert rule database"""
        # Critical lab thresholds
        self.critical_lab_values = {
            'potassium': {'low': 2.5, 'high': 6.0},
            'sodium': {'low': 120, 'high': 160},
            'glucose': {'low': 40, 'high': 500},
            'creatinine': {'high': 5.0},
            'hemoglobin': {'low': 6.0},
            'platelet': {'low': 20},
            'inr': {'high': 5.0},
            'troponin': {'high': 10.0},
        }

        # Common drug-drug interactions
        self.drug_interactions = self._build_interaction_database()

        # Drug allergies cross-sensitivity
        self.allergy_cross_sensitivity = {
            'penicillin': ['amoxicillin', 'ampicillin', 'piperacillin', 'cephalosporins'],
            'sulfa': ['sulfamethoxazole', 'furosemide', 'hydrochlorothiazide'],
            'nsaid': ['ibuprofen', 'naproxen', 'ketorolac', 'celecoxib'],
        }

    def _build_interaction_database(self) -> Dict:
        """Build drug-drug interaction database"""
        return {
            ('warfarin', 'nsaid'): {
                'severity': AlertSeverity.CRITICAL,
                'description': 'Increased bleeding risk',
                'recommendation': 'Use alternative analgesic (acetaminophen). If NSAID essential, monitor INR closely and consider PPI for GI protection.'
            },
            ('warfarin', 'amiodarone'): {
                'severity': AlertSeverity.CRITICAL,
                'description': 'Amiodarone inhibits warfarin metabolism - increases INR',
                'recommendation': 'Reduce warfarin dose by 30-50%. Check INR in 3-5 days.'
            },
            ('ace_inhibitor', 'potassium_sparing_diuretic'): {
                'severity': AlertSeverity.WARNING,
                'description': 'Risk of hyperkalemia',
                'recommendation': 'Monitor potassium closely (weekly initially, then monthly).'
            },
            ('ace_inhibitor', 'nsaid'): {
                'severity': AlertSeverity.WARNING,
                'description': 'Reduced ACE-I effectiveness, increased AKI risk',
                'recommendation': 'Avoid NSAIDs if possible. Monitor BP and renal function.'
            },
            ('metformin', 'iv_contrast'): {
                'severity': AlertSeverity.CRITICAL,
                'description': 'Risk of lactic acidosis if contrast-induced AKI',
                'recommendation': 'Hold metformin day of and 48h after contrast. Restart after confirming stable renal function.'
            },
            ('digoxin', 'amiodarone'): {
                'severity': AlertSeverity.CRITICAL,
                'description': 'Amiodarone increases digoxin levels',
                'recommendation': 'Reduce digoxin dose by 50%. Check digoxin level in 1 week.'
            },
            ('simvastatin', 'amiodarone'): {
                'severity': AlertSeverity.WARNING,
                'description': 'Increased rhabdomyolysis risk',
                'recommendation': 'Limit simvastatin to ≤20mg daily with amiodarone. Consider alternative statin.'
            },
            ('macrolide', 'simvastatin'): {
                'severity': AlertSeverity.WARNING,
                'description': 'Macrolides inhibit statin metabolism - rhabdomyolysis risk',
                'recommendation': 'Hold statin during macrolide course or use azithromycin (no interaction).'
            },
            ('ssri', 'nsaid'): {
                'severity': AlertSeverity.WARNING,
                'description': 'Increased GI bleeding risk',
                'recommendation': 'Use caution. Consider PPI if both needed.'
            },
            ('tramadol', 'ssri'): {
                'severity': AlertSeverity.CRITICAL,
                'description': 'Serotonin syndrome risk',
                'recommendation': 'Avoid combination. Use alternative analgesic.'
            },
        }

    def check_critical_lab_value(self, lab_name: str, value: float) -> Optional[ClinicalAlert]:
        """Check if lab value is critically abnormal"""
        lab_lower = lab_name.lower()

        if lab_lower not in self.critical_lab_values:
            return None

        thresholds = self.critical_lab_values[lab_lower]

        if 'low' in thresholds and value < thresholds['low']:
            severity = AlertSeverity.CRITICAL if value < thresholds['low'] * 0.8 else AlertSeverity.WARNING

            recommendations_map = {
                'potassium': [
                    f"HYPOKALEMIA (K={value})",
                    "Check ECG (U waves, flattened T, prolonged QT)",
                    "IV potassium replacement if <2.5 or symptomatic",
                    "Check magnesium (hypomagnesemia prevents K repletion)",
                    "Monitor closely - cardiac arrhythmia risk"
                ],
                'sodium': [
                    f"SEVERE HYPONATREMIA (Na={value})",
                    "Assess for symptoms (confusion, seizures)",
                    "Check serum osmolality, urine sodium",
                    "If symptomatic: 3% saline (max correction 6-8 mEq/L per 24h)",
                    "RISK: Osmotic demyelination with rapid correction"
                ],
                'glucose': [
                    f"SEVERE HYPOGLYCEMIA (Glucose={value})",
                    "Immediate treatment: D50 25-50mL IV or glucagon 1mg IM",
                    "Continuous monitoring",
                    "Identify cause (insulin, sulfonylurea, missed meal)"
                ],
                'hemoglobin': [
                    f"SEVERE ANEMIA (Hgb={value})",
                    "Consider RBC transfusion if symptomatic",
                    "Type and cross match",
                    "Assess for active bleeding",
                    "Hemodynamic monitoring"
                ],
                'platelet': [
                    f"SEVERE THROMBOCYTOPENIA (Plt={value}K)",
                    "Platelet transfusion if active bleeding or procedure planned",
                    "Hold anticoagulation/antiplatelets",
                    "Hematology consult",
                    "Assess for HIT, ITP, TTP"
                ]
            }

            return ClinicalAlert(
                alert_type="critical_lab_low",
                severity=severity,
                title=f"CRITICAL LOW {lab_name.upper()}",
                message=f"{lab_name.capitalize()} = {value} (Critical threshold: <{thresholds['low']})",
                recommendations=recommendations_map.get(lab_lower, [f"Urgent evaluation and treatment required"]),
                override_reason_required=True
            )

        elif 'high' in thresholds and value > thresholds['high']:
            severity = AlertSeverity.CRITICAL

            recommendations_map = {
                'potassium': [
                    f"HYPERKALEMIA (K={value})",
                    "STAT ECG (peaked T, wide QRS, bradycardia)",
                    "If ECG changes: Calcium gluconate 10% 10mL IV (membrane stabilization)",
                    "Shift K intracellularly: Insulin 10U + D50 50mL IV; Albuterol nebs",
                    "Remove K: Kayexalate, Patiromer, or dialysis if severe",
                    "Continuous telemetry - life-threatening arrhythmia risk"
                ],
                'sodium': [
                    f"SEVERE HYPERNATREMIA (Na={value})",
                    "Calculate free water deficit",
                    "Replace free water carefully (D5W or hypotonic saline)",
                    "Max correction: 10-12 mEq/L per 24h",
                    "Assess for diabetes insipidus if euvolemic"
                ],
                'glucose': [
                    f"SEVERE HYPERGLYCEMIA (Glucose={value})",
                    "Check for DKA: VBG, beta-hydroxybutyrate or urine ketones",
                    "Check for HHS: serum osmolality",
                    "If DKA/HHS: IV insulin infusion, aggressive IV fluids, ICU",
                    "Monitor electrolytes (especially K)"
                ],
                'creatinine': [
                    f"SEVERE RENAL FAILURE (Cr={value})",
                    "Nephrology consult",
                    "Assess for uremia, hyperkalemia, acidosis, volume overload",
                    "Consider emergent dialysis (AEIOU indications)",
                    "Adjust all medication doses for renal function"
                ],
                'inr': [
                    f"CRITICAL INR ELEVATION (INR={value})",
                    "Assess for bleeding",
                    "If active bleeding: 4-factor PCC + Vitamin K 10mg IV",
                    "If no bleeding: Hold warfarin, Vitamin K 2.5-5mg PO",
                    "Recheck INR in 12-24h"
                ],
                'troponin': [
                    f"MARKEDLY ELEVATED TROPONIN (Troponin={value})",
                    "STAT ECG",
                    "Cardiology consult",
                    "Consider acute coronary syndrome, myocarditis, PE, demand ischemia",
                    "Serial troponins, echocardiogram"
                ]
            }

            return ClinicalAlert(
                alert_type="critical_lab_high",
                severity=severity,
                title=f"CRITICAL HIGH {lab_name.upper()}",
                message=f"{lab_name.capitalize()} = {value} (Critical threshold: >{thresholds['high']})",
                recommendations=recommendations_map.get(lab_lower, [f"Urgent evaluation and treatment required"]),
                override_reason_required=True
            )

        return None

    def check_drug_allergy(
        self,
        drug_ordered: str,
        known_allergies: List[str]
    ) -> Optional[ClinicalAlert]:
        """Check for drug allergy contraindication"""
        drug_lower = drug_ordered.lower()

        for allergy in known_allergies:
            allergy_lower = allergy.lower()

            # Direct match
            if allergy_lower in drug_lower or drug_lower in allergy_lower:
                return ClinicalAlert(
                    alert_type="drug_allergy_direct",
                    severity=AlertSeverity.LIFE_THREATENING,
                    title="DRUG ALLERGY ALERT",
                    message=f"Patient has documented allergy to {allergy}. Ordered drug: {drug_ordered}",
                    recommendations=[
                        "DO NOT ADMINISTER - Direct allergy match",
                        "Select alternative medication",
                        "If no alternative: Consult allergy/immunology for desensitization"
                    ],
                    override_reason_required=True
                )

            # Cross-sensitivity
            for allergen, cross_sensitive_drugs in self.allergy_cross_sensitivity.items():
                if allergen in allergy_lower:
                    if any(cross_drug in drug_lower for cross_drug in cross_sensitive_drugs):
                        severity = AlertSeverity.CRITICAL if 'penicillin' in allergen else AlertSeverity.WARNING

                        return ClinicalAlert(
                            alert_type="drug_allergy_cross_sensitivity",
                            severity=severity,
                            title="POSSIBLE CROSS-SENSITIVITY ALERT",
                            message=f"Patient allergic to {allergy}. Potential cross-sensitivity with {drug_ordered}",
                            recommendations=[
                                f"Cross-sensitivity risk with {allergen} allergy",
                                "Verify allergy severity (rash vs anaphylaxis)",
                                "If severe allergy (anaphylaxis): Use alternative",
                                "If mild allergy and essential drug: May use with caution and monitoring"
                            ],
                            override_reason_required=severity == AlertSeverity.CRITICAL
                        )

        return None

    def check_drug_interaction(
        self,
        new_drug: str,
        current_medications: List[str]
    ) -> List[ClinicalAlert]:
        """Check for drug-drug interactions"""
        alerts = []
        new_drug_lower = new_drug.lower()

        # Normalize drug names to classes
        def normalize_drug(drug: str) -> str:
            drug = drug.lower()
            # Map specific drugs to classes
            if any(x in drug for x in ['lisinopril', 'enalapril', 'ramipril', 'benazepril']):
                return 'ace_inhibitor'
            if any(x in drug for x in ['ibuprofen', 'naproxen', 'ketorolac', 'diclofenac', 'meloxicam']):
                return 'nsaid'
            if any(x in drug for x in ['spironolactone', 'amiloride', 'triamterene']):
                return 'potassium_sparing_diuretic'
            if any(x in drug for x in ['azithromycin', 'clarithromycin', 'erythromycin']):
                return 'macrolide'
            if any(x in drug for x in ['fluoxetine', 'sertraline', 'citalopram', 'escitalopram', 'paroxetine']):
                return 'ssri'
            return drug

        new_drug_normalized = normalize_drug(new_drug_lower)

        for current_med in current_medications:
            current_med_normalized = normalize_drug(current_med.lower())

            # Check both directions
            interaction_key = (new_drug_normalized, current_med_normalized)
            reverse_key = (current_med_normalized, new_drug_normalized)

            interaction = self.drug_interactions.get(interaction_key) or self.drug_interactions.get(reverse_key)

            if interaction:
                alerts.append(ClinicalAlert(
                    alert_type="drug_interaction",
                    severity=interaction['severity'],
                    title=f"DRUG-DRUG INTERACTION: {new_drug} + {current_med}",
                    message=interaction['description'],
                    recommendations=[interaction['recommendation']],
                    override_reason_required=interaction['severity'] == AlertSeverity.CRITICAL
                ))

        return alerts

    def check_dose_limit(
        self,
        drug: str,
        dose: float,
        frequency: str,
        patient_weight: Optional[float] = None,
        patient_age: Optional[int] = None
    ) -> Optional[ClinicalAlert]:
        """Check for dose limit violations"""
        drug_lower = drug.lower()

        # Common dose limits
        dose_limits = {
            'acetaminophen': {'max_single': 1000, 'max_daily': 4000, 'unit': 'mg'},
            'ibuprofen': {'max_single': 800, 'max_daily': 3200, 'unit': 'mg'},
            'gabapentin': {'max_daily': 3600, 'unit': 'mg'},
            'metformin': {'max_daily': 2550, 'unit': 'mg'},
        }

        for drug_name, limits in dose_limits.items():
            if drug_name in drug_lower:
                # Calculate daily dose (simplified)
                freq_multiplier = {
                    'daily': 1, 'qd': 1,
                    'bid': 2, 'twice': 2,
                    'tid': 3, 'three': 3,
                    'qid': 4, 'four': 4,
                    'q6h': 4, 'q8h': 3, 'q12h': 2
                }
                multiplier = 1
                for key, val in freq_multiplier.items():
                    if key in frequency.lower():
                        multiplier = val
                        break

                daily_dose = dose * multiplier

                if 'max_daily' in limits and daily_dose > limits['max_daily']:
                    return ClinicalAlert(
                        alert_type="dose_limit_exceeded",
                        severity=AlertSeverity.CRITICAL,
                        title=f"DOSE LIMIT EXCEEDED: {drug}",
                        message=f"Ordered daily dose {daily_dose}{limits['unit']} exceeds maximum {limits['max_daily']}{limits['unit']}/day",
                        recommendations=[
                            f"Reduce dose to ≤{limits['max_daily']}{limits['unit']}/day",
                            "Verify order is correct",
                            "If intentional high dose, document justification"
                        ],
                        override_reason_required=True
                    )

                if 'max_single' in limits and dose > limits['max_single']:
                    return ClinicalAlert(
                        alert_type="dose_limit_exceeded",
                        severity=AlertSeverity.WARNING,
                        title=f"SINGLE DOSE HIGH: {drug}",
                        message=f"Ordered dose {dose}{limits['unit']} exceeds typical max single dose {limits['max_single']}{limits['unit']}",
                        recommendations=[
                            f"Typical max single dose: {limits['max_single']}{limits['unit']}",
                            "Verify dose is appropriate for indication"
                        ],
                        override_reason_required=False
                    )

        return None

    def check_contraindication(
        self,
        drug: str,
        patient_conditions: List[str],
        labs: Optional[Dict] = None
    ) -> Optional[ClinicalAlert]:
        """Check for contraindications based on patient conditions"""
        drug_lower = drug.lower()
        conditions_lower = [c.lower() for c in patient_conditions]

        # Common contraindications
        contraindications = {
            'metformin': {
                'conditions': ['severe renal failure', 'acute kidney injury'],
                'lab_check': {'creatinine': 1.5},
                'message': 'Contraindicated if CrCl <30 or severe renal impairment',
                'severity': AlertSeverity.CRITICAL
            },
            'nsaid': {
                'conditions': ['active gi bleed', 'peptic ulcer disease', 'severe heart failure'],
                'message': 'NSAIDs increase bleeding and heart failure risk',
                'severity': AlertSeverity.WARNING
            },
            'ace_inhibitor': {
                'conditions': ['pregnancy', 'bilateral renal artery stenosis', 'angioedema'],
                'message': 'Contraindicated - risk of fetal harm (pregnancy) or angioedema',
                'severity': AlertSeverity.LIFE_THREATENING
            },
            'warfarin': {
                'conditions': ['pregnancy', 'active bleeding'],
                'message': 'Contraindicated due to bleeding risk',
                'severity': AlertSeverity.CRITICAL
            },
        }

        for drug_name, contraindication in contraindications.items():
            if drug_name in drug_lower:
                # Check conditions
                for condition in contraindication['conditions']:
                    if any(condition in cond for cond in conditions_lower):
                        return ClinicalAlert(
                            alert_type="contraindication",
                            severity=contraindication['severity'],
                            title=f"CONTRAINDICATION: {drug} + {condition}",
                            message=contraindication['message'],
                            recommendations=[
                                "DO NOT USE - Contraindicated",
                                "Select alternative medication"
                            ],
                            override_reason_required=True
                        )

                # Check labs
                if labs and 'lab_check' in contraindication:
                    for lab_name, threshold in contraindication['lab_check'].items():
                        if lab_name in labs and labs[lab_name] > threshold:
                            return ClinicalAlert(
                                alert_type="contraindication_lab",
                                severity=contraindication['severity'],
                                title=f"CONTRAINDICATION: {drug}",
                                message=f"{contraindication['message']} ({lab_name}={labs[lab_name]})",
                                recommendations=[
                                    "Check renal function before prescribing",
                                    "Consider alternative if CrCl <30"
                                ],
                                override_reason_required=True
                            )

        return None


def check_clinical_alerts(
    alert_type: str,
    **params
) -> List[Dict]:
    """
    Check for clinical alerts.

    Args:
        alert_type: Type of alert to check (critical_lab, drug_allergy, drug_interaction, etc.)
        **params: Alert-specific parameters

    Returns:
        List of alert dictionaries

    Examples:
        >>> alerts = check_clinical_alerts("critical_lab", lab_name="potassium", value=6.5)
        >>> alerts = check_clinical_alerts("drug_allergy", drug_ordered="amoxicillin", known_allergies=["penicillin"])
    """
    engine = AlertEngine()
    alerts = []

    if alert_type == "critical_lab":
        alert = engine.check_critical_lab_value(params['lab_name'], params['value'])
        if alert:
            alerts.append(alert)

    elif alert_type == "drug_allergy":
        alert = engine.check_drug_allergy(params['drug_ordered'], params['known_allergies'])
        if alert:
            alerts.append(alert)

    elif alert_type == "drug_interaction":
        interaction_alerts = engine.check_drug_interaction(params['new_drug'], params['current_medications'])
        alerts.extend(interaction_alerts)

    elif alert_type == "dose_limit":
        alert = engine.check_dose_limit(
            params['drug'],
            params['dose'],
            params['frequency'],
            params.get('patient_weight'),
            params.get('patient_age')
        )
        if alert:
            alerts.append(alert)

    elif alert_type == "contraindication":
        alert = engine.check_contraindication(
            params['drug'],
            params['patient_conditions'],
            params.get('labs')
        )
        if alert:
            alerts.append(alert)

    # Convert to dictionaries
    return [
        {
            'alert_type': a.alert_type,
            'severity': a.severity.value,
            'title': a.title,
            'message': a.message,
            'recommendations': a.recommendations,
            'override_reason_required': a.override_reason_required
        }
        for a in alerts
    ]
