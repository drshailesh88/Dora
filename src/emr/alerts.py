"""Clinical Decision Support Alerts."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .models import Allergy, LabResult, Medication, PatientSummary, Severity


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"  # Informational
    WARNING = "warning"  # Caution advised
    CRITICAL = "critical"  # Must address before proceeding
    FATAL = "fatal"  # Contraindicated, do not proceed


class AlertCategory(str, Enum):
    """Alert categories."""

    ALLERGY = "allergy"
    DRUG_INTERACTION = "drug_interaction"
    CONTRAINDICATION = "contraindication"
    DOSING = "dosing"
    LAB_VALUE = "lab_value"
    DUPLICATE_THERAPY = "duplicate_therapy"
    AGE_RELATED = "age_related"


class ClinicalAlert(BaseModel):
    """Clinical decision support alert."""

    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    level: AlertLevel
    category: AlertCategory
    title: str = Field(..., description="Brief alert title")
    message: str = Field(..., description="Detailed alert message")
    recommendation: Optional[str] = Field(
        None, description="Recommended action"
    )
    evidence: Optional[str] = Field(None, description="Supporting evidence/citation")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_display_string(self) -> str:
        """Format for display."""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "⛔",
            AlertLevel.FATAL: "🚨",
        }
        emoji = emoji_map[self.level]
        lines = [
            f"{emoji} {self.title}",
            f"   {self.message}",
        ]
        if self.recommendation:
            lines.append(f"   → {self.recommendation}")
        return "\n".join(lines)


class ClinicalAlertEngine:
    """
    Clinical decision support alert engine.

    Checks for:
    - Drug-allergy interactions
    - Drug-drug interactions
    - Contraindications
    - Dosing adjustments (renal/hepatic)
    - Critical lab values
    - Duplicate therapy
    - Age-related concerns
    """

    def __init__(self):
        """Initialize alert engine."""
        # Drug class definitions
        self.drug_classes = {
            "ace_inhibitor": [
                "lisinopril",
                "enalapril",
                "ramipril",
                "benazepril",
                "captopril",
            ],
            "arb": ["losartan", "valsartan", "irbesartan", "olmesartan"],
            "beta_blocker": [
                "metoprolol",
                "atenolol",
                "carvedilol",
                "bisoprolol",
            ],
            "nsaid": [
                "ibuprofen",
                "naproxen",
                "diclofenac",
                "celecoxib",
                "indomethacin",
            ],
            "statin": [
                "atorvastatin",
                "rosuvastatin",
                "simvastatin",
                "pravastatin",
            ],
            "anticoagulant": ["warfarin", "apixaban", "rivaroxaban", "dabigatran"],
            "antiplatelet": ["aspirin", "clopidogrel", "prasugrel"],
            "diuretic": [
                "furosemide",
                "hydrochlorothiazide",
                "spironolactone",
                "torsemide",
            ],
            "sulfonylurea": ["glipizide", "glyburide", "glimepiride"],
        }

        # Drug-drug interactions (moderate to severe)
        self.interactions = {
            ("ace_inhibitor", "arb"): (
                AlertLevel.WARNING,
                "Dual RAAS blockade increases hyperkalemia risk",
                "Consider using single agent only",
            ),
            ("nsaid", "ace_inhibitor"): (
                AlertLevel.WARNING,
                "NSAIDs reduce ACE inhibitor efficacy and increase renal risk",
                "Use acetaminophen instead if possible",
            ),
            ("nsaid", "anticoagulant"): (
                AlertLevel.CRITICAL,
                "Increased bleeding risk with NSAIDs + anticoagulants",
                "Avoid NSAIDs; use acetaminophen",
            ),
            ("nsaid", "antiplatelet"): (
                AlertLevel.WARNING,
                "Increased GI bleeding risk",
                "Add PPI for gastroprotection",
            ),
            ("statin", "statin"): (
                AlertLevel.CRITICAL,
                "Duplicate statin therapy",
                "Consolidate to single statin",
            ),
            ("sulfonylurea", "sulfonylurea"): (
                AlertLevel.CRITICAL,
                "Duplicate sulfonylurea increases hypoglycemia risk",
                "Use single sulfonylurea only",
            ),
        }

        # Cross-allergen reactions
        self.cross_allergens = {
            "penicillin": ["amoxicillin", "ampicillin", "cephalosporin"],
            "sulfa": ["sulfamethoxazole", "trimethoprim", "furosemide"],
            "aspirin": ["nsaid", "salicylate"],
        }

    def check_all_alerts(
        self,
        patient_summary: PatientSummary,
        proposed_medication: Optional[str] = None,
    ) -> list[ClinicalAlert]:
        """
        Check all clinical alerts for a patient.

        Args:
            patient_summary: Patient data
            proposed_medication: New medication being considered (optional)

        Returns:
            List of clinical alerts
        """
        alerts = []

        # 1. Drug-allergy checks
        if proposed_medication:
            alerts.extend(
                self._check_drug_allergy(
                    proposed_medication, patient_summary.allergies
                )
            )

        # 2. Drug-drug interaction checks
        alerts.extend(
            self._check_drug_interactions(
                patient_summary.current_medications,
                proposed_medication,
            )
        )

        # 3. Disease-drug contraindications
        alerts.extend(
            self._check_contraindications(
                patient_summary.active_diagnoses,
                patient_summary.current_medications,
                proposed_medication,
            )
        )

        # 4. Renal dosing adjustments
        alerts.extend(
            self._check_renal_dosing(
                patient_summary.recent_labs,
                patient_summary.current_medications,
                proposed_medication,
                patient_summary.patient.age,
                patient_summary.patient.gender.value,
            )
        )

        # 5. Critical lab values
        alerts.extend(self._check_critical_labs(patient_summary.recent_labs))

        # 6. Duplicate therapy
        alerts.extend(
            self._check_duplicate_therapy(
                patient_summary.current_medications,
                proposed_medication,
            )
        )

        # 7. Age-related alerts
        if patient_summary.patient.age >= 65:
            alerts.extend(
                self._check_elderly_concerns(
                    patient_summary.patient.age,
                    patient_summary.current_medications,
                    proposed_medication,
                )
            )

        return sorted(alerts, key=lambda x: (x.level.value, x.category.value))

    def _check_drug_allergy(
        self, drug_name: str, allergies: list[Allergy]
    ) -> list[ClinicalAlert]:
        """Check for drug-allergy interactions."""
        alerts = []
        drug_lower = drug_name.lower()

        for allergy in allergies:
            allergen_lower = allergy.allergen.lower()

            # Direct match
            if allergen_lower in drug_lower or drug_lower in allergen_lower:
                level = (
                    AlertLevel.FATAL
                    if allergy.severity == Severity.FATAL
                    else AlertLevel.CRITICAL
                )
                alerts.append(
                    ClinicalAlert(
                        level=level,
                        category=AlertCategory.ALLERGY,
                        title=f"ALLERGY: {allergy.allergen}",
                        message=f"Patient has {allergy.severity.value} allergy to {allergy.allergen}: {allergy.reaction}",
                        recommendation="DO NOT PRESCRIBE. Select alternative medication.",
                    )
                )
                continue

            # Cross-allergen check
            for main_allergen, related_drugs in self.cross_allergens.items():
                if main_allergen in allergen_lower:
                    for related in related_drugs:
                        if related in drug_lower:
                            alerts.append(
                                ClinicalAlert(
                                    level=AlertLevel.WARNING,
                                    category=AlertCategory.ALLERGY,
                                    title=f"Cross-allergy risk: {allergy.allergen}",
                                    message=f"Patient allergic to {allergy.allergen}. {drug_name} may have cross-reactivity.",
                                    recommendation="Consider alternative if available. Monitor closely if used.",
                                )
                            )

        return alerts

    def _check_drug_interactions(
        self,
        current_medications: list[Medication],
        proposed_medication: Optional[str] = None,
    ) -> list[ClinicalAlert]:
        """Check for drug-drug interactions."""
        alerts = []

        # Get all active medications
        all_meds = [med.drug_name.lower() for med in current_medications]
        if proposed_medication:
            all_meds.append(proposed_medication.lower())

        # Classify medications by drug class
        med_classes = {}
        for med in all_meds:
            for drug_class, drugs in self.drug_classes.items():
                if any(drug in med for drug in drugs):
                    if drug_class not in med_classes:
                        med_classes[drug_class] = []
                    med_classes[drug_class].append(med)

        # Check for interactions
        for (class1, class2), (level, message, rec) in self.interactions.items():
            if class1 in med_classes and class2 in med_classes:
                alerts.append(
                    ClinicalAlert(
                        level=level,
                        category=AlertCategory.DRUG_INTERACTION,
                        title=f"Drug interaction: {class1} + {class2}",
                        message=message,
                        recommendation=rec,
                    )
                )

        return alerts

    def _check_contraindications(
        self,
        diagnoses: list,
        current_medications: list[Medication],
        proposed_medication: Optional[str] = None,
    ) -> list[ClinicalAlert]:
        """Check for disease-drug contraindications."""
        alerts = []

        # Get all medications
        all_meds = [med.drug_name.lower() for med in current_medications]
        if proposed_medication:
            all_meds.append(proposed_medication.lower())

        # Check diagnosis-based contraindications
        for dx in diagnoses:
            dx_lower = dx.diagnosis_name.lower()

            # CKD contraindications
            if any(
                kw in dx_lower for kw in ["chronic kidney", "ckd", "renal failure"]
            ):
                for med in all_meds:
                    if any(nsaid in med for nsaid in self.drug_classes["nsaid"]):
                        alerts.append(
                            ClinicalAlert(
                                level=AlertLevel.CRITICAL,
                                category=AlertCategory.CONTRAINDICATION,
                                title="NSAIDs contraindicated in CKD",
                                message=f"Patient has {dx.diagnosis_name}. NSAIDs worsen kidney function.",
                                recommendation="Use acetaminophen for pain instead.",
                            )
                        )

            # Heart failure contraindications
            if "heart failure" in dx_lower or "hf" in dx_lower:
                for med in all_meds:
                    if any(nsaid in med for nsaid in self.drug_classes["nsaid"]):
                        alerts.append(
                            ClinicalAlert(
                                level=AlertLevel.WARNING,
                                category=AlertCategory.CONTRAINDICATION,
                                title="NSAIDs worsen heart failure",
                                message="NSAIDs cause fluid retention and HF exacerbation.",
                                recommendation="Avoid NSAIDs in heart failure patients.",
                            )
                        )

            # Asthma + beta blocker
            if "asthma" in dx_lower or "copd" in dx_lower:
                for med in all_meds:
                    if any(
                        bb in med for bb in self.drug_classes["beta_blocker"]
                    ):
                        alerts.append(
                            ClinicalAlert(
                                level=AlertLevel.WARNING,
                                category=AlertCategory.CONTRAINDICATION,
                                title="Beta blocker in reactive airway disease",
                                message="Non-selective beta blockers can cause bronchospasm.",
                                recommendation="Use cardioselective beta blocker (e.g., metoprolol) if needed.",
                            )
                        )

        return alerts

    def _check_renal_dosing(
        self,
        labs: list[LabResult],
        current_medications: list[Medication],
        proposed_medication: Optional[str],
        age: int,
        gender: str,
    ) -> list[ClinicalAlert]:
        """Check for renal dosing adjustments."""
        alerts = []

        # Find creatinine
        creatinine = None
        for lab in labs:
            if "creatinine" in lab.test_name.lower():
                try:
                    creatinine = float(lab.result)
                except ValueError:
                    pass
                break

        if not creatinine:
            return alerts

        # Calculate eGFR (simplified CKD-EPI)
        k = 0.7 if gender == "F" else 0.9
        alpha = -0.329 if gender == "F" else -0.411
        sex_factor = 1.018 if gender == "F" else 1.0
        egfr = (
            141
            * min(creatinine / k, 1) ** alpha
            * max(creatinine / k, 1) ** -1.209
            * 0.993**age
            * sex_factor
        )

        # Drugs requiring renal dose adjustment
        renal_adjust_drugs = {
            "metformin": (30, "Contraindicated if eGFR <30; use caution if <45"),
            "gabapentin": (60, "Reduce dose if eGFR <60"),
            "enoxaparin": (30, "Reduce dose if eGFR <30"),
            "digoxin": (50, "Reduce dose if eGFR <50"),
            "atenolol": (35, "Reduce dose if eGFR <35"),
        }

        all_meds = [med.drug_name.lower() for med in current_medications]
        if proposed_medication:
            all_meds.append(proposed_medication.lower())

        for med in all_meds:
            for drug, (threshold, message) in renal_adjust_drugs.items():
                if drug in med and egfr < threshold:
                    level = (
                        AlertLevel.CRITICAL if egfr < 30 else AlertLevel.WARNING
                    )
                    alerts.append(
                        ClinicalAlert(
                            level=level,
                            category=AlertCategory.DOSING,
                            title=f"Renal dose adjustment needed: {drug}",
                            message=f"eGFR {egfr:.0f} mL/min. {message}",
                            recommendation="Adjust dose per renal function or select alternative.",
                        )
                    )

        return alerts

    def _check_critical_labs(
        self, labs: list[LabResult]
    ) -> list[ClinicalAlert]:
        """Check for critical lab values."""
        alerts = []

        critical_ranges = {
            "potassium": (2.5, 6.0, "mEq/L"),
            "sodium": (120, 155, "mEq/L"),
            "glucose": (40, 400, "mg/dL"),
            "creatinine": (0.5, 5.0, "mg/dL"),
            "hemoglobin": (7.0, 20.0, "g/dL"),
        }

        for lab in labs:
            test_lower = lab.test_name.lower()
            for test_name, (low, high, unit) in critical_ranges.items():
                if test_name in test_lower:
                    try:
                        value = float(lab.result)
                        if value < low or value > high:
                            alerts.append(
                                ClinicalAlert(
                                    level=AlertLevel.CRITICAL,
                                    category=AlertCategory.LAB_VALUE,
                                    title=f"Critical {test_name}: {value} {unit}",
                                    message=f"Lab value outside critical range ({low}-{high} {unit})",
                                    recommendation="Address abnormal lab value before new medications.",
                                )
                            )
                    except ValueError:
                        pass

        return alerts

    def _check_duplicate_therapy(
        self,
        current_medications: list[Medication],
        proposed_medication: Optional[str],
    ) -> list[ClinicalAlert]:
        """Check for duplicate drug therapy."""
        alerts = []

        if not proposed_medication:
            return alerts

        proposed_lower = proposed_medication.lower()

        # Check for duplicate from same class
        for drug_class, drugs in self.drug_classes.items():
            proposed_in_class = any(drug in proposed_lower for drug in drugs)
            if not proposed_in_class:
                continue

            for med in current_medications:
                if any(drug in med.drug_name.lower() for drug in drugs):
                    alerts.append(
                        ClinicalAlert(
                            level=AlertLevel.WARNING,
                            category=AlertCategory.DUPLICATE_THERAPY,
                            title=f"Duplicate {drug_class} therapy",
                            message=f"Patient already on {med.drug_name} ({drug_class})",
                            recommendation="Consolidate to single agent or verify indication for both.",
                        )
                    )

        return alerts

    def _check_elderly_concerns(
        self,
        age: int,
        current_medications: list[Medication],
        proposed_medication: Optional[str],
    ) -> list[ClinicalAlert]:
        """Check for elderly-specific concerns (Beers Criteria)."""
        alerts = []

        # Beers criteria drugs to avoid in elderly
        beers_drugs = [
            "diphenhydramine",
            "diazepam",
            "amitriptyline",
            "indomethacin",
            "glyburide",
        ]

        all_meds = [med.drug_name.lower() for med in current_medications]
        if proposed_medication:
            all_meds.append(proposed_medication.lower())

        for med in all_meds:
            for beers_drug in beers_drugs:
                if beers_drug in med:
                    alerts.append(
                        ClinicalAlert(
                            level=AlertLevel.WARNING,
                            category=AlertCategory.AGE_RELATED,
                            title=f"Beers Criteria: Avoid {beers_drug} in elderly",
                            message=f"Increased risk of adverse effects in patients ≥65",
                            recommendation="Consider safer alternative.",
                        )
                    )

        # Polypharmacy warning
        if len(current_medications) >= 5:
            alerts.append(
                ClinicalAlert(
                    level=AlertLevel.INFO,
                    category=AlertCategory.AGE_RELATED,
                    title="Polypharmacy in elderly patient",
                    message=f"Patient on {len(current_medications)} medications. Risk of interactions and falls.",
                    recommendation="Review medication list for deprescribing opportunities.",
                )
            )

        return alerts
