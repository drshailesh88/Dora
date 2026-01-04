"""Drug safety checks module.

Provides comprehensive safety screening including pregnancy, lactation,
renal/hepatic dosing, pediatric dosing, contraindications, and allergies.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from .models import (
    Drug,
    PregnancySafety,
    LactationSafety,
    RenalDosingAdjustment,
    HepaticDosingAdjustment,
    PediatricDosing,
    DrugAllergy,
    Contraindication,
    PregnancyCategory,
    LactationRisk,
    RenalDosing,
    HepaticDosing,
)
from .database import DrugDatabase

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheckResult:
    """Result of a comprehensive safety check."""

    safe: bool
    warnings: list[str]
    contraindications: list[str]
    recommendations: list[str]
    alternatives: list[str]


class DrugSafetyChecker:
    """Comprehensive drug safety checking system."""

    def __init__(self, database: Optional[DrugDatabase] = None):
        """
        Initialize safety checker.

        Args:
            database: Drug database instance.
        """
        self.db = database or DrugDatabase()

    def check_pregnancy_safety(
        self,
        drug_id: str,
        trimester: Optional[str] = None,
    ) -> SafetyCheckResult:
        """
        Check pregnancy safety for a drug.

        Args:
            drug_id: Drug identifier.
            trimester: "first", "second", or "third" (optional).

        Returns:
            Safety check result with warnings and recommendations.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=["Verify drug name"],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []
        alternatives = []

        # Check pregnancy category
        category = drug.pregnancy_category

        if category == PregnancyCategory.X:
            safe = False
            contraindications.append(
                f"{drug.generic_name} is CONTRAINDICATED in pregnancy (Category X)"
            )
            recommendations.append("Do not use - find alternative")
        elif category == PregnancyCategory.D:
            safe = False
            warnings.append(
                f"{drug.generic_name} has positive evidence of fetal risk (Category D)"
            )
            recommendations.append(
                "Use only if benefits outweigh risks and no safer alternatives exist"
            )
        elif category == PregnancyCategory.C:
            safe = True
            warnings.append(
                f"{drug.generic_name} has uncertain fetal risk (Category C)"
            )
            recommendations.append(
                "Risk cannot be ruled out - use with caution after risk-benefit assessment"
            )
        elif category == PregnancyCategory.B:
            safe = True
            recommendations.append(
                f"{drug.generic_name} is generally considered safe in pregnancy (Category B)"
            )
        elif category == PregnancyCategory.A:
            safe = True
            recommendations.append(
                f"{drug.generic_name} is safe in pregnancy (Category A)"
            )
        else:
            safe = True
            warnings.append("Pregnancy safety category unknown - consult references")

        # Trimester-specific warnings
        if trimester:
            trimester_warnings = self._get_trimester_warnings(drug, trimester)
            warnings.extend(trimester_warnings)

        # Get alternatives if unsafe
        if not safe or category in [PregnancyCategory.C, PregnancyCategory.D]:
            alternatives = self._get_pregnancy_alternatives(drug)

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=alternatives,
        )

    def check_lactation_safety(self, drug_id: str) -> SafetyCheckResult:
        """
        Check lactation safety for a drug.

        Args:
            drug_id: Drug identifier.

        Returns:
            Safety check result.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=["Verify drug name"],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []
        alternatives = []

        risk = drug.lactation_risk

        if risk == LactationRisk.L5:
            safe = False
            contraindications.append(
                f"{drug.generic_name} is CONTRAINDICATED during breastfeeding (L5)"
            )
            recommendations.append("Do not use - find alternative or discontinue breastfeeding")
        elif risk == LactationRisk.L4:
            safe = False
            warnings.append(
                f"{drug.generic_name} is possibly hazardous during breastfeeding (L4)"
            )
            recommendations.append(
                "Use only if no safer alternatives exist and benefits outweigh risks"
            )
            recommendations.append("Monitor infant closely for adverse effects")
        elif risk == LactationRisk.L3:
            safe = True
            warnings.append(
                f"{drug.generic_name} is moderately safe during breastfeeding (L3)"
            )
            recommendations.append("Monitor infant for side effects")
            recommendations.append("Consider timing doses after breastfeeding")
        elif risk == LactationRisk.L2:
            safe = True
            recommendations.append(
                f"{drug.generic_name} is safer during breastfeeding (L2) - limited data but no adverse effects reported"
            )
        elif risk == LactationRisk.L1:
            safe = True
            recommendations.append(
                f"{drug.generic_name} is safest during breastfeeding (L1)"
            )
        else:
            safe = True
            warnings.append("Lactation safety data unknown - consult references")

        # Get alternatives if needed
        if not safe or risk in [LactationRisk.L3, LactationRisk.L4]:
            alternatives = self._get_lactation_alternatives(drug)

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=alternatives,
        )

    def calculate_renal_dose(
        self,
        drug_id: str,
        gfr: float,
        current_dose: Optional[str] = None,
    ) -> SafetyCheckResult:
        """
        Calculate renal dose adjustment.

        Args:
            drug_id: Drug identifier.
            gfr: Glomerular filtration rate (mL/min/1.73m²).
            current_dose: Current prescribed dose (optional).

        Returns:
            Safety check result with dose recommendations.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=["Verify drug name"],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []

        # Classify renal function
        if gfr >= 90:
            category = RenalDosing.NORMAL
            recommendations.append("Normal renal function - no dose adjustment needed")
        elif gfr >= 60:
            category = RenalDosing.MILD
            warnings.append("Mild renal impairment (GFR 60-89)")
        elif gfr >= 30:
            category = RenalDosing.MODERATE
            warnings.append("Moderate renal impairment (GFR 30-59)")
        elif gfr >= 15:
            category = RenalDosing.SEVERE
            warnings.append("Severe renal impairment (GFR 15-29)")
        else:
            category = RenalDosing.ESRD
            warnings.append("End-stage renal disease (GFR < 15)")

        # Check for nephrotoxicity
        if self._is_nephrotoxic(drug):
            warnings.append(f"{drug.generic_name} is potentially nephrotoxic - use with caution")
            recommendations.append("Monitor renal function closely")

        # Get dose adjustment recommendations
        if category != RenalDosing.NORMAL:
            adjustment = self._get_renal_dose_adjustment(drug, category)
            if adjustment:
                recommendations.append(adjustment)
            else:
                recommendations.append(
                    f"Consult drug references for specific renal dosing of {drug.generic_name}"
                )

        safe = category in [RenalDosing.NORMAL, RenalDosing.MILD]

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=[],
        )

    def calculate_hepatic_dose(
        self,
        drug_id: str,
        child_pugh_score: int,
    ) -> SafetyCheckResult:
        """
        Calculate hepatic dose adjustment.

        Args:
            drug_id: Drug identifier.
            child_pugh_score: Child-Pugh score (5-15).

        Returns:
            Safety check result with dose recommendations.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=["Verify drug name"],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []

        # Classify hepatic function
        if child_pugh_score <= 6:
            category = HepaticDosing.CHILD_A
            recommendations.append("Mild hepatic impairment (Child-Pugh A)")
        elif child_pugh_score <= 9:
            category = HepaticDosing.CHILD_B
            warnings.append("Moderate hepatic impairment (Child-Pugh B)")
        else:
            category = HepaticDosing.CHILD_C
            warnings.append("Severe hepatic impairment (Child-Pugh C)")

        # Check for hepatotoxicity
        if self._is_hepatotoxic(drug):
            warnings.append(f"{drug.generic_name} is potentially hepatotoxic")
            recommendations.append("Monitor liver function tests closely")

        # Get dose adjustment
        if category != HepaticDosing.NORMAL:
            adjustment = self._get_hepatic_dose_adjustment(drug, category)
            if adjustment:
                if "contraindicated" in adjustment.lower():
                    safe = False
                    contraindications.append(adjustment)
                else:
                    recommendations.append(adjustment)
            else:
                recommendations.append(
                    f"Consult drug references for hepatic dosing of {drug.generic_name}"
                )

        safe = category == HepaticDosing.CHILD_A and not contraindications

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=[],
        )

    def calculate_pediatric_dose(
        self,
        drug_id: str,
        age_years: Optional[float] = None,
        weight_kg: Optional[float] = None,
    ) -> SafetyCheckResult:
        """
        Calculate pediatric dose.

        Args:
            drug_id: Drug identifier.
            age_years: Child's age in years.
            weight_kg: Child's weight in kg.

        Returns:
            Safety check result with pediatric dose.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=["Verify drug name"],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []

        # Check if drug is safe in children
        pediatric_safe = self._check_pediatric_safety(drug, age_years)

        if not pediatric_safe:
            contraindications.append(
                f"{drug.generic_name} may not be approved for this age group"
            )
            recommendations.append("Consult pediatric references before use")

        # Calculate dose if weight provided
        if weight_kg:
            dose = self._calculate_weight_based_dose(drug, weight_kg)
            if dose:
                recommendations.append(f"Weight-based dose: {dose}")
            else:
                recommendations.append(
                    "Weight-based dosing information not available - consult references"
                )

        # Age-specific warnings
        if age_years is not None:
            age_warnings = self._get_pediatric_age_warnings(drug, age_years)
            warnings.extend(age_warnings)

        safe = pediatric_safe and not contraindications

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=[],
        )

    def check_contraindications(
        self,
        drug_id: str,
        patient_conditions: list[str],
    ) -> SafetyCheckResult:
        """
        Check for contraindications based on patient conditions.

        Args:
            drug_id: Drug identifier.
            patient_conditions: List of patient conditions/diagnoses.

        Returns:
            Safety check result.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=[],
                alternatives=[],
            )

        contraindications = []
        warnings = []
        recommendations = []

        # Check each condition against drug contraindications
        drug_contraindications = [c.lower() for c in drug.contraindications]

        for condition in patient_conditions:
            condition_lower = condition.lower()

            # Check for matches
            for contraindication in drug_contraindications:
                if condition_lower in contraindication or contraindication in condition_lower:
                    contraindications.append(
                        f"{drug.generic_name} is contraindicated in {condition}"
                    )
                    break

        safe = len(contraindications) == 0

        if not safe:
            recommendations.append("Consider alternative medication")
        else:
            recommendations.append(f"No contraindications found for {drug.generic_name}")

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=[],
        )

    def check_allergy_cross_reactivity(
        self,
        drug_id: str,
        known_allergies: list[str],
    ) -> SafetyCheckResult:
        """
        Check for allergy cross-reactivity.

        Args:
            drug_id: Drug identifier.
            known_allergies: List of known drug allergies.

        Returns:
            Safety check result.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return SafetyCheckResult(
                safe=False,
                warnings=["Drug not found in database"],
                contraindications=[],
                recommendations=[],
                alternatives=[],
            )

        warnings = []
        contraindications = []
        recommendations = []

        # Check for direct allergy
        for allergy in known_allergies:
            if allergy.lower() in drug.generic_name.lower():
                contraindications.append(
                    f"Patient is allergic to {drug.generic_name}"
                )
                return SafetyCheckResult(
                    safe=False,
                    warnings=warnings,
                    contraindications=contraindications,
                    recommendations=["ABSOLUTE CONTRAINDICATION - Do not prescribe"],
                    alternatives=[],
                )

        # Check for cross-reactivity (simplified - would need full allergy database)
        cross_reactive_warnings = self._check_cross_reactivity(drug, known_allergies)
        warnings.extend(cross_reactive_warnings)

        safe = len(contraindications) == 0

        if warnings:
            recommendations.append("Consider allergy testing before use")
        else:
            recommendations.append("No known cross-reactivity with patient's allergies")

        return SafetyCheckResult(
            safe=safe,
            warnings=warnings,
            contraindications=contraindications,
            recommendations=recommendations,
            alternatives=[],
        )

    # Helper methods

    def _get_trimester_warnings(self, drug: Drug, trimester: str) -> list[str]:
        """Get trimester-specific warnings."""
        # This would be enhanced with actual trimester-specific data
        warnings = []

        if trimester == "first" and drug.pregnancy_category in [
            PregnancyCategory.C,
            PregnancyCategory.D,
            PregnancyCategory.X,
        ]:
            warnings.append("First trimester is critical for organogenesis - extra caution advised")

        return warnings

    def _get_pregnancy_alternatives(self, drug: Drug) -> list[str]:
        """Get safer pregnancy alternatives."""
        # This would query database for safer alternatives in same class
        alternatives = []

        # Example logic - would be replaced with database queries
        if drug.therapeutic_class.value == "cardiovascular":
            alternatives = ["Consult with cardiologist for pregnancy-safe alternatives"]
        elif drug.therapeutic_class.value == "psychiatric":
            alternatives = ["Consider non-pharmacologic interventions if appropriate"]

        return alternatives

    def _get_lactation_alternatives(self, drug: Drug) -> list[str]:
        """Get safer lactation alternatives."""
        # Would query database for L1/L2 alternatives
        return ["Consult lactation references for safer alternatives"]

    def _is_nephrotoxic(self, drug: Drug) -> bool:
        """Check if drug is nephrotoxic."""
        nephrotoxic_keywords = ["nephrotoxic", "renal impairment", "kidney"]
        return any(
            keyword in " ".join(drug.serious_side_effects).lower()
            for keyword in nephrotoxic_keywords
        )

    def _is_hepatotoxic(self, drug: Drug) -> bool:
        """Check if drug is hepatotoxic."""
        hepatotoxic_keywords = ["hepatotoxic", "liver", "hepatic impairment"]
        return any(
            keyword in " ".join(drug.serious_side_effects).lower()
            for keyword in hepatotoxic_keywords
        )

    def _get_renal_dose_adjustment(self, drug: Drug, category: RenalDosing) -> Optional[str]:
        """Get renal dose adjustment recommendation."""
        # This would query actual renal dosing database
        if category == RenalDosing.MODERATE:
            return "Reduce dose by 25-50% for moderate renal impairment"
        elif category == RenalDosing.SEVERE:
            return "Reduce dose by 50-75% for severe renal impairment"
        elif category == RenalDosing.ESRD:
            return "Use with extreme caution in ESRD - consult nephrologist"
        return None

    def _get_hepatic_dose_adjustment(
        self, drug: Drug, category: HepaticDosing
    ) -> Optional[str]:
        """Get hepatic dose adjustment recommendation."""
        # This would query actual hepatic dosing database
        if category == HepaticDosing.CHILD_B:
            return "Reduce dose by 25-50% for moderate hepatic impairment"
        elif category == HepaticDosing.CHILD_C:
            return "Use with extreme caution or avoid in severe hepatic impairment"
        return None

    def _check_pediatric_safety(self, drug: Drug, age_years: Optional[float]) -> bool:
        """Check if drug is safe for pediatric use."""
        # This would check actual pediatric approval data
        # For now, assume most drugs need careful pediatric consideration
        return True

    def _calculate_weight_based_dose(
        self, drug: Drug, weight_kg: float
    ) -> Optional[str]:
        """Calculate weight-based pediatric dose."""
        # This would use actual pediatric dosing formulas
        # Example placeholder
        if drug.adult_dose:
            return f"Consult pediatric references for weight-based dosing (Patient weight: {weight_kg} kg)"
        return None

    def _get_pediatric_age_warnings(self, drug: Drug, age_years: float) -> list[str]:
        """Get age-specific pediatric warnings."""
        warnings = []

        if age_years < 2:
            warnings.append("Infant/toddler - verify appropriate formulation and dose")
        elif age_years < 6:
            warnings.append("Young child - verify dose calculation")

        return warnings

    def _check_cross_reactivity(
        self, drug: Drug, known_allergies: list[str]
    ) -> list[str]:
        """Check for cross-reactivity with known allergies."""
        warnings = []

        # Example: penicillin cross-reactivity with cephalosporins
        penicillin_allergic = any("penicillin" in a.lower() for a in known_allergies)
        if penicillin_allergic and "ceph" in drug.generic_name.lower():
            warnings.append(
                "Patient has penicillin allergy - cephalosporins have ~1-3% cross-reactivity risk"
            )

        # Example: sulfa cross-reactivity
        sulfa_allergic = any("sulfa" in a.lower() or "sulfon" in a.lower() for a in known_allergies)
        if sulfa_allergic and ("sulfa" in drug.generic_name.lower() or "sulfon" in drug.generic_name.lower()):
            warnings.append("Patient has sulfa allergy - potential cross-reactivity")

        return warnings
