"""Unified drug service orchestration.

Provides comprehensive drug information, safety screening, and pricing
through a single, easy-to-use service interface.
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

from .models import (
    Drug,
    DrugInteraction,
    ComprehensiveDrugInfo,
    DrugSearchResult,
)
from .database import DrugDatabase
from .interactions import DrugInteractionChecker
from .safety import DrugSafetyChecker, SafetyCheckResult
from .pricing import IndianDrugPricing

logger = logging.getLogger(__name__)


@dataclass
class DrugLookupResult:
    """Comprehensive drug lookup result."""

    drug: Drug
    formulations: list = field(default_factory=list)
    pricing: Optional[dict] = None
    generic_alternatives: list[str] = field(default_factory=list)
    common_interactions: list[DrugInteraction] = field(default_factory=list)
    pregnancy_safety: Optional[SafetyCheckResult] = None
    lactation_safety: Optional[SafetyCheckResult] = None


@dataclass
class PrescriptionSafetyCheck:
    """Complete prescription safety check result."""

    safe: bool
    drug_interactions: list[DrugInteraction] = field(default_factory=list)
    pregnancy_warnings: list[str] = field(default_factory=list)
    lactation_warnings: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    allergy_warnings: list[str] = field(default_factory=list)
    renal_warnings: list[str] = field(default_factory=list)
    hepatic_warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)


class DrugService:
    """Unified drug service providing comprehensive drug information and safety."""

    def __init__(
        self,
        database: Optional[DrugDatabase] = None,
        interaction_checker: Optional[DrugInteractionChecker] = None,
        safety_checker: Optional[DrugSafetyChecker] = None,
        pricing: Optional[IndianDrugPricing] = None,
    ):
        """
        Initialize drug service.

        Args:
            database: Drug database instance.
            interaction_checker: Drug interaction checker.
            safety_checker: Safety checker instance.
            pricing: Pricing service instance.
        """
        self.db = database or DrugDatabase()
        self.interaction_checker = interaction_checker or DrugInteractionChecker()
        self.safety_checker = safety_checker or DrugSafetyChecker(self.db)
        self.pricing = pricing or IndianDrugPricing(self.db)

        logger.info("DrugService initialized")

    def search_drugs(
        self,
        query: str,
        therapeutic_class: Optional[str] = None,
        limit: int = 20,
    ) -> list[DrugSearchResult]:
        """
        Search for drugs by name.

        Args:
            query: Search query (drug name).
            therapeutic_class: Filter by therapeutic class.
            limit: Maximum results.

        Returns:
            List of search results.
        """
        logger.info(f"Searching drugs: {query}")
        return self.db.search_drugs(query, therapeutic_class, limit)

    def get_drug_info(
        self,
        drug_id: str,
        include_pricing: bool = True,
        include_interactions: bool = True,
    ) -> Optional[DrugLookupResult]:
        """
        Get comprehensive drug information.

        Args:
            drug_id: Drug identifier.
            include_pricing: Include pricing information.
            include_interactions: Include common interactions.

        Returns:
            Complete drug information.
        """
        logger.info(f"Looking up drug: {drug_id}")

        drug = self.db.get_drug(drug_id)
        if not drug:
            logger.warning(f"Drug not found: {drug_id}")
            return None

        # Get pricing if requested
        pricing = None
        generic_alternatives = []
        if include_pricing:
            price_comparison = self.pricing.compare_generic_vs_brand(drug_id)
            if price_comparison:
                pricing = {
                    "brand_price": price_comparison.brand_price,
                    "generic_price": price_comparison.generic_price,
                    "savings_inr": price_comparison.savings_inr,
                    "savings_percent": price_comparison.savings_percent,
                    "nlem_drug": price_comparison.nlem_drug,
                }
                generic_alternatives = price_comparison.generic_alternatives

        # Get common interactions if requested
        common_interactions = []
        if include_interactions:
            common_interactions = self.db.get_interactions(drug_id)[:10]  # Top 10

        # Get safety information
        pregnancy_safety = self.safety_checker.check_pregnancy_safety(drug_id)
        lactation_safety = self.safety_checker.check_lactation_safety(drug_id)

        return DrugLookupResult(
            drug=drug,
            pricing=pricing,
            generic_alternatives=generic_alternatives,
            common_interactions=common_interactions,
            pregnancy_safety=pregnancy_safety,
            lactation_safety=lactation_safety,
        )

    def check_prescription_safety(
        self,
        drug_ids: list[str],
        patient_context: Optional[dict] = None,
    ) -> PrescriptionSafetyCheck:
        """
        Comprehensive safety check for a prescription.

        Args:
            drug_ids: List of drug IDs being prescribed.
            patient_context: Patient information (optional).
                - pregnancy: bool
                - lactating: bool
                - gfr: float (renal function)
                - child_pugh_score: int (hepatic function)
                - age_years: float
                - weight_kg: float
                - conditions: list[str]
                - allergies: list[str]

        Returns:
            Complete safety check result.
        """
        logger.info(f"Checking prescription safety for {len(drug_ids)} drugs")

        result = PrescriptionSafetyCheck(safe=True)

        patient_context = patient_context or {}

        # Check drug-drug interactions
        if len(drug_ids) > 1:
            drug_names = []
            for drug_id in drug_ids:
                drug = self.db.get_drug(drug_id)
                if drug:
                    drug_names.append(drug.generic_name)

            if drug_names:
                interactions = self.interaction_checker.check_multiple(drug_names)
                result.drug_interactions = interactions

                for interaction in interactions:
                    if interaction.severity.value in ["contraindicated", "severe"]:
                        result.safe = False
                        result.recommendations.append(
                            f"CRITICAL: {interaction.drug1} + {interaction.drug2} - {interaction.management}"
                        )

        # Check each drug individually
        for drug_id in drug_ids:
            drug = self.db.get_drug(drug_id)
            if not drug:
                continue

            # Pregnancy check
            if patient_context.get("pregnancy"):
                preg_check = self.safety_checker.check_pregnancy_safety(drug_id)
                if not preg_check.safe:
                    result.safe = False
                result.pregnancy_warnings.extend(preg_check.warnings)
                result.contraindications.extend(preg_check.contraindications)
                result.recommendations.extend(preg_check.recommendations)

            # Lactation check
            if patient_context.get("lactating"):
                lact_check = self.safety_checker.check_lactation_safety(drug_id)
                if not lact_check.safe:
                    result.safe = False
                result.lactation_warnings.extend(lact_check.warnings)
                result.contraindications.extend(lact_check.contraindications)
                result.recommendations.extend(lact_check.recommendations)

            # Renal check
            if "gfr" in patient_context:
                renal_check = self.safety_checker.calculate_renal_dose(
                    drug_id, patient_context["gfr"]
                )
                result.renal_warnings.extend(renal_check.warnings)
                result.contraindications.extend(renal_check.contraindications)
                result.recommendations.extend(renal_check.recommendations)

            # Hepatic check
            if "child_pugh_score" in patient_context:
                hepatic_check = self.safety_checker.calculate_hepatic_dose(
                    drug_id, patient_context["child_pugh_score"]
                )
                if not hepatic_check.safe:
                    result.safe = False
                result.hepatic_warnings.extend(hepatic_check.warnings)
                result.contraindications.extend(hepatic_check.contraindications)
                result.recommendations.extend(hepatic_check.recommendations)

            # Contraindications check
            if "conditions" in patient_context:
                contraind_check = self.safety_checker.check_contraindications(
                    drug_id, patient_context["conditions"]
                )
                if not contraind_check.safe:
                    result.safe = False
                result.contraindications.extend(contraind_check.contraindications)
                result.recommendations.extend(contraind_check.recommendations)

            # Allergy check
            if "allergies" in patient_context:
                allergy_check = self.safety_checker.check_allergy_cross_reactivity(
                    drug_id, patient_context["allergies"]
                )
                if not allergy_check.safe:
                    result.safe = False
                result.allergy_warnings.extend(allergy_check.warnings)
                result.contraindications.extend(allergy_check.contraindications)
                result.recommendations.extend(allergy_check.recommendations)

        # Remove duplicates from warnings and recommendations
        result.pregnancy_warnings = list(set(result.pregnancy_warnings))
        result.lactation_warnings = list(set(result.lactation_warnings))
        result.contraindications = list(set(result.contraindications))
        result.allergy_warnings = list(set(result.allergy_warnings))
        result.renal_warnings = list(set(result.renal_warnings))
        result.hepatic_warnings = list(set(result.hepatic_warnings))
        result.recommendations = list(set(result.recommendations))

        logger.info(f"Prescription safety check complete. Safe: {result.safe}")
        return result

    def get_alternatives(
        self,
        drug_id: str,
        reason: str = "generic",
    ) -> list[str]:
        """
        Get alternative drugs.

        Args:
            drug_id: Drug identifier.
            reason: Reason for alternatives ("generic", "pregnancy", "lactation", "cost").

        Returns:
            List of alternative drug names.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return []

        alternatives = []

        if reason == "generic":
            # Get generic alternatives
            comparison = self.pricing.compare_generic_vs_brand(drug_id)
            if comparison:
                alternatives = comparison.generic_alternatives

        elif reason == "cost":
            # Get cheaper alternatives in same class
            class_drugs = self.db.get_drugs_by_class(drug.therapeutic_class.value)
            for alt_drug in class_drugs:
                if alt_drug.id != drug_id:
                    alternatives.append(alt_drug.generic_name)

        elif reason == "pregnancy":
            # Get pregnancy-safe alternatives
            pregnancy_check = self.safety_checker.check_pregnancy_safety(drug_id)
            alternatives = pregnancy_check.alternatives

        elif reason == "lactation":
            # Get lactation-safe alternatives
            lactation_check = self.safety_checker.check_lactation_safety(drug_id)
            alternatives = lactation_check.alternatives

        return alternatives[:5]  # Limit to top 5

    def calculate_prescription_cost(
        self,
        prescription: list[dict],
    ) -> dict:
        """
        Calculate total prescription cost.

        Args:
            prescription: List of prescriptions with:
                - drug_id: str
                - daily_dose: str (e.g., "10mg twice daily")
                - duration_days: int

        Returns:
            Cost breakdown.
        """
        total_brand_cost = 0.0
        total_generic_cost = 0.0
        drug_costs = []

        for item in prescription:
            drug_id = item["drug_id"]
            daily_dose = item.get("daily_dose", "once daily")
            duration_days = item.get("duration_days", 30)

            # Get monthly cost
            cost_info = self.pricing.calculate_monthly_cost(drug_id, daily_dose)

            if "error" not in cost_info:
                # Pro-rate for duration
                days_ratio = duration_days / 30.0
                brand_cost = (cost_info.get("brand_monthly_cost") or 0) * days_ratio
                generic_cost = (cost_info.get("generic_monthly_cost") or 0) * days_ratio

                total_brand_cost += brand_cost
                total_generic_cost += generic_cost

                drug_costs.append({
                    "drug_name": cost_info["drug_name"],
                    "daily_dose": daily_dose,
                    "duration_days": duration_days,
                    "brand_cost": brand_cost,
                    "generic_cost": generic_cost,
                })

        total_savings = total_brand_cost - total_generic_cost

        return {
            "drug_costs": drug_costs,
            "total_brand_cost": total_brand_cost,
            "total_generic_cost": total_generic_cost,
            "total_savings": total_savings,
            "savings_percent": (total_savings / total_brand_cost * 100) if total_brand_cost > 0 else 0,
        }

    def get_drug_by_name(self, drug_name: str) -> Optional[Drug]:
        """
        Get drug by name (exact or fuzzy match).

        Args:
            drug_name: Drug name to search.

        Returns:
            Drug object or None.
        """
        results = self.search_drugs(drug_name, limit=1)

        if results and results[0].relevance_score > 0.7:
            return self.db.get_drug(results[0].drug_id)

        return None

    def add_drug_to_database(self, drug: Drug) -> bool:
        """
        Add a new drug to the database.

        Args:
            drug: Drug object to add.

        Returns:
            True if successful.
        """
        logger.info(f"Adding drug to database: {drug.generic_name}")
        return self.db.add_drug(drug)

    def get_statistics(self) -> dict:
        """
        Get database statistics.

        Returns:
            Statistics about drugs, interactions, etc.
        """
        return self.db.get_database_stats()

    def close(self):
        """Close all underlying connections."""
        self.db.close()
        self.interaction_checker.close()
        logger.info("DrugService closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
