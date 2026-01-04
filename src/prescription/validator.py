"""
Prescription validator for Dora.

Validates prescriptions for safety:
- Drug-drug interactions
- Drug-allergy conflicts
- Contraindications
- Dosing issues
- Renal/hepatic adjustments
- Pregnancy/lactation safety
- Pediatric appropriateness
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum

from .models import (
    Prescription,
    PrescriptionItem,
    PatientInfo,
    PrescriptionValidationResult,
)


class InteractionSeverity(str, Enum):
    """Severity of drug-drug interaction."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


class PregnancyCategory(str, Enum):
    """FDA Pregnancy Categories."""
    A = "A"  # Safe
    B = "B"  # Probably safe
    C = "C"  # Use with caution
    D = "D"  # Evidence of risk
    X = "X"  # Contraindicated


class PrescriptionValidator:
    """
    Comprehensive prescription validation.

    Integrates with drug database for interaction checking.
    """

    def __init__(self, drug_database=None):
        """
        Initialize validator.

        Args:
            drug_database: Drug interaction database client
        """
        self.drug_db = drug_database or self._get_default_drug_db()

    def validate(self, prescription: Prescription) -> PrescriptionValidationResult:
        """
        Perform comprehensive validation of prescription.

        Args:
            prescription: Prescription to validate

        Returns:
            Validation result with errors, warnings, and recommendations
        """
        result = PrescriptionValidationResult(is_valid=True)

        # 1. Check drug-drug interactions
        interactions = self._check_drug_interactions(prescription.items)
        result.interactions = interactions

        # Check if any are contraindicated
        for interaction in interactions:
            if interaction['severity'] == InteractionSeverity.CONTRAINDICATED.value:
                result.errors.append(
                    f"CONTRAINDICATED: {interaction['drug1']} + {interaction['drug2']} - {interaction['description']}"
                )
                result.is_valid = False
            elif interaction['severity'] == InteractionSeverity.MAJOR.value:
                result.warnings.append(
                    f"⚠️ MAJOR INTERACTION: {interaction['drug1']} + {interaction['drug2']} - {interaction['description']}"
                )

        # 2. Check drug-allergy conflicts
        allergy_conflicts = self._check_allergies(
            prescription.items,
            prescription.patient.known_allergies
        )
        result.allergy_conflicts = allergy_conflicts

        if allergy_conflicts:
            for conflict in allergy_conflicts:
                result.errors.append(
                    f"ALLERGY CONFLICT: Patient allergic to {conflict['allergen']}, prescribed {conflict['drug']}"
                )
            result.is_valid = False

        # 3. Check contraindications based on patient conditions
        contraindications = self._check_contraindications(
            prescription.items,
            prescription.patient.active_conditions
        )
        result.contraindications = contraindications

        for contra in contraindications:
            if contra['severity'] == 'absolute':
                result.errors.append(
                    f"CONTRAINDICATION: {contra['drug']} contraindicated in {contra['condition']}"
                )
                result.is_valid = False
            else:
                result.warnings.append(
                    f"⚠️ CAUTION: {contra['drug']} - use with caution in {contra['condition']}"
                )

        # 4. Check dosing
        dosing_issues = self._check_dosing(prescription.items, prescription.patient)
        result.dosing_issues = dosing_issues

        for issue in dosing_issues:
            if issue['severity'] == 'error':
                result.errors.append(
                    f"DOSING ERROR: {issue['drug']} - {issue['description']}"
                )
                result.is_valid = False
            else:
                result.warnings.append(
                    f"⚠️ DOSING: {issue['drug']} - {issue['description']}"
                )

        # 5. Check for duplicate therapies
        duplicates = self._check_duplicate_therapies(prescription.items)
        result.duplicate_therapies = duplicates

        for dup in duplicates:
            result.warnings.append(
                f"⚠️ DUPLICATE: {dup} - multiple drugs from same class"
            )

        # 6. Check renal function adjustments
        if prescription.patient.weight_kg:
            # Estimate if renal adjustment needed (simplified - real calc needs Cr)
            result.renal_adjustment_needed = self._check_renal_adjustment_needed(
                prescription.items
            )
            if result.renal_adjustment_needed:
                result.warnings.append(
                    "⚠️ RENAL: Check renal function - dose adjustment may be needed"
                )

        # 7. Check hepatic adjustments
        result.hepatic_adjustment_needed = self._check_hepatic_adjustment_needed(
            prescription.items
        )
        if result.hepatic_adjustment_needed:
            result.warnings.append(
                "⚠️ HEPATIC: Check liver function - dose adjustment may be needed"
            )

        # 8. Pregnancy/lactation safety (if applicable)
        if prescription.patient.gender.upper() == 'F':
            pregnancy_safety = self._check_pregnancy_safety(prescription.items)
            result.pregnancy_safety = pregnancy_safety
            if pregnancy_safety and 'unsafe' in pregnancy_safety.lower():
                result.warnings.append(
                    f"⚠️ PREGNANCY: {pregnancy_safety}"
                )

        # 9. Pediatric appropriateness
        if prescription.patient.age < 18:
            pediatric_issues = self._check_pediatric_safety(
                prescription.items,
                prescription.patient.age
            )
            for issue in pediatric_issues:
                result.warnings.append(
                    f"⚠️ PEDIATRIC: {issue}"
                )

        # 10. Calculate overall risk score
        result.risk_score = self._calculate_risk_score(result)

        # 11. Determine if specialist review needed
        result.requires_specialist_review = (
            result.risk_score > 0.7 or
            len(result.errors) > 0 or
            len(result.interactions) > 3
        )

        return result

    def _check_drug_interactions(
        self,
        items: List[PrescriptionItem]
    ) -> List[Dict[str, Any]]:
        """
        Check for drug-drug interactions.

        Returns list of interactions with severity and description.
        """
        interactions = []

        # Get drug names
        drugs = [item.drug_name.lower() for item in items]

        # Check each pair
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                drug1, drug2 = drugs[i], drugs[j]

                # Query drug database
                interaction = self._query_interaction(drug1, drug2)

                if interaction:
                    interactions.append({
                        'drug1': items[i].drug_name,
                        'drug2': items[j].drug_name,
                        'severity': interaction['severity'],
                        'description': interaction['description'],
                        'management': interaction.get('management', ''),
                    })

        return interactions

    def _query_interaction(self, drug1: str, drug2: str) -> Optional[Dict[str, Any]]:
        """
        Query drug database for interaction between two drugs.

        This is a stub - in production, query real drug database.
        """
        # Common known interactions (stub data)
        known_interactions = {
            ('metformin', 'contrast'): {
                'severity': InteractionSeverity.MAJOR.value,
                'description': 'Risk of lactic acidosis',
                'management': 'Hold metformin 48h before and after contrast',
            },
            ('warfarin', 'aspirin'): {
                'severity': InteractionSeverity.MAJOR.value,
                'description': 'Increased bleeding risk',
                'management': 'Monitor INR closely, use with extreme caution',
            },
            ('atenolol', 'verapamil'): {
                'severity': InteractionSeverity.MAJOR.value,
                'description': 'Risk of heart block and bradycardia',
                'management': 'Avoid combination, use alternative',
            },
            ('simvastatin', 'clarithromycin'): {
                'severity': InteractionSeverity.MAJOR.value,
                'description': 'Increased risk of myopathy/rhabdomyolysis',
                'management': 'Avoid combination or reduce statin dose',
            },
            ('methotrexate', 'nsaid'): {
                'severity': InteractionSeverity.MODERATE.value,
                'description': 'Increased methotrexate toxicity',
                'management': 'Monitor CBC and renal function',
            },
        }

        # Normalize drug names
        d1 = drug1.lower().strip()
        d2 = drug2.lower().strip()

        # Check both orders
        interaction = (
            known_interactions.get((d1, d2)) or
            known_interactions.get((d2, d1))
        )

        # If we have a drug database, query it
        if self.drug_db and not interaction:
            try:
                interaction = self.drug_db.check_interaction(d1, d2)
            except Exception:
                pass

        return interaction

    def _check_allergies(
        self,
        items: List[PrescriptionItem],
        allergies: List[str]
    ) -> List[str]:
        """Check if any prescribed drug conflicts with known allergies."""
        conflicts = []

        if not allergies:
            return conflicts

        # Normalize allergies
        normalized_allergies = [a.lower().strip() for a in allergies]

        for item in items:
            drug_name = item.drug_name.lower()
            generic_name = (item.generic_name or '').lower()

            # Direct match
            for allergy in normalized_allergies:
                if allergy in drug_name or allergy in generic_name:
                    conflicts.append({
                        'drug': item.drug_name,
                        'allergen': allergy,
                    })
                    continue

                # Check drug class (e.g., "sulfa drugs")
                if self._is_drug_class_match(drug_name, allergy):
                    conflicts.append({
                        'drug': item.drug_name,
                        'allergen': allergy,
                    })

        return conflicts

    def _is_drug_class_match(self, drug_name: str, allergy: str) -> bool:
        """Check if drug belongs to allergy class."""
        # Common drug classes
        drug_classes = {
            'penicillin': ['amoxicillin', 'ampicillin', 'penicillin', 'amoxyclav'],
            'sulfa': ['sulfamethoxazole', 'sulfasalazine', 'sulfa'],
            'nsaid': ['ibuprofen', 'diclofenac', 'naproxen', 'aspirin'],
            'statin': ['atorvastatin', 'simvastatin', 'rosuvastatin'],
        }

        for drug_class, members in drug_classes.items():
            if drug_class in allergy.lower():
                for member in members:
                    if member in drug_name:
                        return True

        return False

    def _check_contraindications(
        self,
        items: List[PrescriptionItem],
        conditions: List[str]
    ) -> List[Dict[str, Any]]:
        """Check contraindications based on patient conditions."""
        contraindications = []

        if not conditions:
            return contraindications

        # Known contraindications (stub data)
        known_contras = {
            'metformin': {
                'chronic kidney disease': 'relative',
                'heart failure': 'relative',
                'liver disease': 'absolute',
            },
            'nsaid': {
                'peptic ulcer': 'absolute',
                'chronic kidney disease': 'relative',
                'heart failure': 'relative',
            },
            'glimepiride': {
                'g6pd deficiency': 'absolute',
            },
            'methotrexate': {
                'pregnancy': 'absolute',
                'liver disease': 'absolute',
            },
        }

        for item in items:
            drug_name = item.drug_name.lower()

            for condition in conditions:
                condition_lower = condition.lower()

                # Check if drug has contraindications for this condition
                if drug_name in known_contras:
                    drug_contras = known_contras[drug_name]

                    for contra_condition, severity in drug_contras.items():
                        if contra_condition in condition_lower:
                            contraindications.append({
                                'drug': item.drug_name,
                                'condition': condition,
                                'severity': severity,
                                'recommendation': self._get_contraindication_recommendation(
                                    drug_name, condition, severity
                                )
                            })

        return contraindications

    def _get_contraindication_recommendation(
        self,
        drug: str,
        condition: str,
        severity: str
    ) -> str:
        """Get recommendation for contraindication."""
        if severity == 'absolute':
            return f"Avoid {drug} in {condition}. Use alternative."
        else:
            return f"Use {drug} with caution in {condition}. Monitor closely."

    def _check_dosing(
        self,
        items: List[PrescriptionItem],
        patient: PatientInfo
    ) -> List[Dict[str, Any]]:
        """Check if dosing is appropriate."""
        issues = []

        # Standard dose ranges (stub data - should be from database)
        dose_ranges = {
            'metformin': {'min': 500, 'max': 2000, 'unit': 'mg', 'per': 'dose'},
            'amlodipine': {'min': 2.5, 'max': 10, 'unit': 'mg', 'per': 'day'},
            'atorvastatin': {'min': 10, 'max': 80, 'unit': 'mg', 'per': 'day'},
        }

        for item in items:
            drug_name = item.drug_name.lower()

            if drug_name in dose_ranges:
                range_info = dose_ranges[drug_name]

                # Extract numeric dose
                dose_value = self._extract_numeric_dose(item.strength)

                if dose_value:
                    # Check if in range
                    if dose_value < range_info['min']:
                        issues.append({
                            'drug': item.drug_name,
                            'description': f"Dose {dose_value}{range_info['unit']} below usual minimum {range_info['min']}{range_info['unit']}",
                            'severity': 'warning',
                        })
                    elif dose_value > range_info['max']:
                        issues.append({
                            'drug': item.drug_name,
                            'description': f"Dose {dose_value}{range_info['unit']} exceeds usual maximum {range_info['max']}{range_info['unit']}",
                            'severity': 'error',
                        })

            # Check duration
            if item.dosage.duration_days > 90:
                issues.append({
                    'drug': item.drug_name,
                    'description': f"Duration {item.dosage.duration_days} days exceeds 90 days - consider shorter duration or follow-up",
                    'severity': 'warning',
                })

        return issues

    def _extract_numeric_dose(self, strength: str) -> Optional[float]:
        """Extract numeric dose from strength string."""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', strength)
        if match:
            return float(match.group(1))
        return None

    def _check_duplicate_therapies(
        self,
        items: List[PrescriptionItem]
    ) -> List[str]:
        """Check for duplicate therapeutic classes."""
        duplicates = []

        # Drug classes (stub - should be from database)
        drug_classes = {
            'metformin': 'biguanide',
            'glimepiride': 'sulfonylurea',
            'gliclazide': 'sulfonylurea',
            'amlodipine': 'calcium_channel_blocker',
            'nifedipine': 'calcium_channel_blocker',
            'atorvastatin': 'statin',
            'simvastatin': 'statin',
        }

        # Count by class
        class_counts: Dict[str, List[str]] = {}

        for item in items:
            drug_name = item.drug_name.lower()
            drug_class = drug_classes.get(drug_name, drug_name)

            if drug_class not in class_counts:
                class_counts[drug_class] = []

            class_counts[drug_class].append(item.drug_name)

        # Find duplicates
        for drug_class, drugs in class_counts.items():
            if len(drugs) > 1:
                duplicates.append(f"{drug_class}: {', '.join(drugs)}")

        return duplicates

    def _check_renal_adjustment_needed(
        self,
        items: List[PrescriptionItem]
    ) -> bool:
        """Check if any drugs require renal dose adjustment."""
        # Drugs requiring renal adjustment
        renal_adjusted_drugs = [
            'metformin', 'digoxin', 'gabapentin', 'enoxaparin',
            'methotrexate', 'acyclovir', 'gentamicin'
        ]

        for item in items:
            if any(drug in item.drug_name.lower() for drug in renal_adjusted_drugs):
                return True

        return False

    def _check_hepatic_adjustment_needed(
        self,
        items: List[PrescriptionItem]
    ) -> bool:
        """Check if any drugs require hepatic dose adjustment."""
        # Drugs requiring hepatic adjustment
        hepatic_adjusted_drugs = [
            'simvastatin', 'atorvastatin', 'warfarin', 'methotrexate',
            'paracetamol', 'acetaminophen'
        ]

        for item in items:
            if any(drug in item.drug_name.lower() for drug in hepatic_adjusted_drugs):
                return True

        return False

    def _check_pregnancy_safety(
        self,
        items: List[PrescriptionItem]
    ) -> Optional[str]:
        """Check pregnancy safety of prescribed drugs."""
        # Pregnancy categories (stub data)
        pregnancy_cats = {
            'metformin': PregnancyCategory.B,
            'insulin': PregnancyCategory.B,
            'methotrexate': PregnancyCategory.X,
            'warfarin': PregnancyCategory.X,
            'atorvastatin': PregnancyCategory.X,
            'lisinopril': PregnancyCategory.D,
            'paracetamol': PregnancyCategory.B,
        }

        unsafe_drugs = []

        for item in items:
            drug_name = item.drug_name.lower()
            category = pregnancy_cats.get(drug_name)

            if category in [PregnancyCategory.D, PregnancyCategory.X]:
                unsafe_drugs.append(f"{item.drug_name} (Category {category.value})")

        if unsafe_drugs:
            return f"Unsafe in pregnancy: {', '.join(unsafe_drugs)}"

        return None

    def _check_pediatric_safety(
        self,
        items: List[PrescriptionItem],
        age: int
    ) -> List[str]:
        """Check if drugs are appropriate for pediatric age."""
        issues = []

        # Pediatric contraindications (stub data)
        pediatric_issues = {
            'aspirin': {'min_age': 12, 'reason': 'Risk of Reye syndrome'},
            'tetracycline': {'min_age': 8, 'reason': 'Tooth discoloration'},
            'quinolone': {'min_age': 18, 'reason': 'Cartilage damage risk'},
        }

        for item in items:
            drug_name = item.drug_name.lower()

            for drug, info in pediatric_issues.items():
                if drug in drug_name and age < info['min_age']:
                    issues.append(
                        f"{item.drug_name} not recommended under {info['min_age']} years - {info['reason']}"
                    )

        return issues

    def _calculate_risk_score(self, result: PrescriptionValidationResult) -> float:
        """
        Calculate overall risk score.

        0.0 = No risk
        1.0 = Maximum risk
        """
        score = 0.0

        # Errors (blocking) = high weight
        score += len(result.errors) * 0.3

        # Contraindicated interactions
        contraindicated = sum(
            1 for i in result.interactions
            if i['severity'] == InteractionSeverity.CONTRAINDICATED.value
        )
        score += contraindicated * 0.25

        # Major interactions
        major = sum(
            1 for i in result.interactions
            if i['severity'] == InteractionSeverity.MAJOR.value
        )
        score += major * 0.15

        # Allergy conflicts
        score += len(result.allergy_conflicts) * 0.2

        # Absolute contraindications
        absolute_contras = sum(
            1 for c in result.contraindications
            if c.get('severity') == 'absolute'
        )
        score += absolute_contras * 0.2

        # Cap at 1.0
        return min(score, 1.0)

    def _get_default_drug_db(self):
        """Get default drug database stub."""
        # In production, this would connect to actual drug database
        return None


# Example usage
if __name__ == "__main__":
    from .models import (
        Prescription, PrescriptionItem, PatientInfo, DoctorInfo,
        Dosage, DosageForm, Frequency, RouteOfAdministration
    )
    from datetime import datetime

    # Create test patient with allergies
    patient = PatientInfo(
        patient_id="PAT-001",
        name="Test Patient",
        age=45,
        gender="M",
        known_allergies=["Sulfa drugs"],
        active_conditions=["Type 2 Diabetes", "Chronic Kidney Disease"],
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Test",
        qualifications="MD",
        registration_number="REG-001",
    )

    # Create prescription with potential issues
    items = [
        PrescriptionItem(
            drug_name="Metformin",
            strength="500mg",
            dosage_form=DosageForm.TABLET,
            dosage=Dosage(
                dose="1 tablet",
                frequency=Frequency.BD,
                duration_days=30,
                route=RouteOfAdministration.ORAL,
            ),
            quantity=60,
            quantity_unit="tablets",
            item_sequence=1,
        ),
    ]

    prescription = Prescription(
        prescription_id="RX-TEST-001",
        patient=patient,
        doctor=doctor,
        items=items,
        created_by="system",
    )

    # Validate
    validator = PrescriptionValidator()
    result = validator.validate(prescription)

    print(f"Valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Risk Score: {result.risk_score}")
    print(f"\nWarnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
