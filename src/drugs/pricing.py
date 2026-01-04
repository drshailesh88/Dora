"""Indian drug pricing module.

Provides pricing information, generic alternatives, and cost optimization
for the Indian pharmaceutical market.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from .models import (
    Drug,
    DrugPrice,
    GenericEquivalent,
    DrugFormulation,
)
from .database import DrugDatabase

logger = logging.getLogger(__name__)


@dataclass
class PriceComparison:
    """Price comparison result."""

    drug_name: str
    brand_price: float
    generic_price: float
    savings_inr: float
    savings_percent: float
    generic_alternatives: list[str]
    nlem_drug: bool
    price_controlled: bool


@dataclass
class CostOptimization:
    """Cost optimization recommendation."""

    original_drug: str
    original_cost: float
    recommended_drug: str
    recommended_cost: float
    savings: float
    rationale: str
    bioequivalent: bool


class IndianDrugPricing:
    """Indian drug pricing and cost optimization system."""

    # Mock data for major pharmacy chains (would be API-based in production)
    PHARMACY_CHAINS = {
        "apollo": "Apollo Pharmacy",
        "medplus": "MedPlus",
        "netmeds": "Netmeds (Online)",
        "pharmeasy": "PharmEasy (Online)",
        "1mg": "1mg (Online)",
    }

    def __init__(self, database: Optional[DrugDatabase] = None):
        """
        Initialize pricing system.

        Args:
            database: Drug database instance.
        """
        self.db = database or DrugDatabase()

    def get_drug_price(
        self,
        drug_id: str,
        formulation: Optional[str] = None,
        strength: Optional[str] = None,
    ) -> Optional[DrugPrice]:
        """
        Get drug price information.

        Args:
            drug_id: Drug identifier.
            formulation: Formulation type (optional).
            strength: Drug strength (optional).

        Returns:
            DrugPrice object or None.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            logger.warning(f"Drug not found: {drug_id}")
            return None

        # In production, this would query actual pricing database
        # For now, return mock data
        return self._get_mock_price(drug, formulation, strength)

    def compare_generic_vs_brand(
        self,
        drug_id: str,
        formulation: Optional[str] = None,
    ) -> Optional[PriceComparison]:
        """
        Compare generic and brand prices.

        Args:
            drug_id: Drug identifier.
            formulation: Formulation type.

        Returns:
            Price comparison result.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return None

        # Get brand and generic prices
        brand_price = self._get_brand_price(drug, formulation)
        generic_price = self._get_generic_price(drug, formulation)

        if not brand_price or not generic_price:
            logger.warning(f"Incomplete pricing data for {drug.generic_name}")
            return None

        savings_inr = brand_price - generic_price
        savings_percent = (savings_inr / brand_price) * 100

        # Get generic alternatives
        generic_alternatives = self._get_generic_alternatives(drug)

        # Check if NLEM drug (price controlled)
        nlem_drug = self._is_nlem_drug(drug)

        return PriceComparison(
            drug_name=drug.generic_name,
            brand_price=brand_price,
            generic_price=generic_price,
            savings_inr=savings_inr,
            savings_percent=savings_percent,
            generic_alternatives=generic_alternatives,
            nlem_drug=nlem_drug,
            price_controlled=nlem_drug,
        )

    def get_cost_optimization(
        self,
        drug_ids: list[str],
        patient_budget: Optional[float] = None,
    ) -> list[CostOptimization]:
        """
        Get cost optimization recommendations for a list of drugs.

        Args:
            drug_ids: List of drug identifiers.
            patient_budget: Patient's monthly budget (optional).

        Returns:
            List of cost optimization recommendations.
        """
        optimizations = []

        for drug_id in drug_ids:
            drug = self.db.get_drug(drug_id)
            if not drug:
                continue

            # Check if generic alternative exists
            comparison = self.compare_generic_vs_brand(drug_id)

            if comparison and comparison.savings_inr > 10:  # Meaningful savings
                optimizations.append(
                    CostOptimization(
                        original_drug=drug.generic_name,
                        original_cost=comparison.brand_price,
                        recommended_drug=f"{drug.generic_name} (Generic)",
                        recommended_cost=comparison.generic_price,
                        savings=comparison.savings_inr,
                        rationale=f"Save ₹{comparison.savings_inr:.2f} ({comparison.savings_percent:.1f}%) by switching to generic",
                        bioequivalent=True,
                    )
                )

        # Sort by savings (highest first)
        optimizations.sort(key=lambda x: x.savings, reverse=True)

        return optimizations

    def get_pharmacy_prices(
        self,
        drug_id: str,
        formulation: Optional[str] = None,
    ) -> dict[str, float]:
        """
        Get prices from different pharmacy chains.

        Args:
            drug_id: Drug identifier.
            formulation: Formulation type.

        Returns:
            Dictionary mapping pharmacy names to prices.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {}

        # Mock data - in production would query actual APIs
        base_price = self._get_generic_price(drug, formulation) or 100.0

        prices = {
            "apollo": base_price * 1.15,  # Apollo typically 15% higher
            "medplus": base_price * 1.10,  # MedPlus 10% higher
            "netmeds": base_price * 0.95,  # Online 5% discount
            "pharmeasy": base_price * 0.90,  # PharmEasy 10% discount
            "1mg": base_price * 0.88,  # 1mg best online price
        }

        return prices

    def get_insurance_coverage(
        self,
        drug_id: str,
        insurance_provider: Optional[str] = None,
    ) -> dict:
        """
        Check insurance coverage for a drug.

        Args:
            drug_id: Drug identifier.
            insurance_provider: Insurance provider name.

        Returns:
            Coverage information.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {"covered": False, "message": "Drug not found"}

        # Check if NLEM drug (usually covered)
        if self._is_nlem_drug(drug):
            return {
                "covered": True,
                "coverage_type": "Essential Medicine",
                "copay_percent": 0,
                "message": f"{drug.generic_name} is in National List of Essential Medicines",
            }

        # Mock insurance coverage data
        return {
            "covered": True,
            "coverage_type": "Generic",
            "copay_percent": 20,
            "message": "Check with your insurance provider for exact coverage",
        }

    def get_nlem_status(self, drug_id: str) -> dict:
        """
        Get National List of Essential Medicines (NLEM) status.

        Args:
            drug_id: Drug identifier.

        Returns:
            NLEM status information.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {"nlem": False, "message": "Drug not found"}

        is_nlem = self._is_nlem_drug(drug)

        if is_nlem:
            return {
                "nlem": True,
                "price_controlled": True,
                "message": f"{drug.generic_name} is in NLEM - price is government controlled",
                "benefits": [
                    "Price-controlled by government",
                    "Available in government hospitals",
                    "Better insurance coverage",
                    "Quality assured",
                ],
            }
        else:
            return {
                "nlem": False,
                "price_controlled": False,
                "message": f"{drug.generic_name} is not in NLEM",
            }

    def calculate_monthly_cost(
        self,
        drug_id: str,
        daily_dose: str,
        formulation: Optional[str] = None,
    ) -> dict:
        """
        Calculate estimated monthly medication cost.

        Args:
            drug_id: Drug identifier.
            daily_dose: Daily dose (e.g., "10mg once daily", "5mg twice daily").
            formulation: Formulation type.

        Returns:
            Monthly cost breakdown.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {"error": "Drug not found"}

        # Parse daily dose to get frequency
        frequency = self._parse_dose_frequency(daily_dose)

        # Get per-unit price
        unit_price = self._get_generic_price(drug, formulation) or 0

        # Calculate monthly cost
        units_per_month = frequency * 30
        monthly_cost = unit_price * units_per_month

        # Get generic alternative cost
        comparison = self.compare_generic_vs_brand(drug_id, formulation)
        generic_monthly_cost = None
        savings = None

        if comparison:
            generic_monthly_cost = comparison.generic_price * units_per_month
            savings = (comparison.brand_price - comparison.generic_price) * units_per_month

        return {
            "drug_name": drug.generic_name,
            "daily_dose": daily_dose,
            "units_per_month": units_per_month,
            "brand_monthly_cost": monthly_cost if comparison else None,
            "generic_monthly_cost": generic_monthly_cost,
            "monthly_savings": savings,
            "yearly_savings": savings * 12 if savings else None,
        }

    # Helper methods

    def _get_mock_price(
        self,
        drug: Drug,
        formulation: Optional[str],
        strength: Optional[str],
    ) -> DrugPrice:
        """Generate mock price data."""
        # Mock pricing based on therapeutic class
        base_prices = {
            "cardiovascular": 50.0,
            "antidiabetic": 75.0,
            "antibiotic": 100.0,
            "analgesic": 30.0,
            "gastrointestinal": 40.0,
            "psychiatric": 150.0,
        }

        base_price = base_prices.get(drug.therapeutic_class.value, 50.0)

        # Brand is typically 3-5x generic price in India
        mrp = base_price * 4.0
        generic_price = base_price

        return DrugPrice(
            drug_id=drug.id,
            drug_name=drug.generic_name,
            formulation=formulation or "tablet",
            strength=strength or "standard",
            manufacturer="Various",
            is_generic=True,
            mrp=mrp,
            pharmacy_price=generic_price * 1.1,
            online_price=generic_price * 0.9,
            nlem_drug=self._is_nlem_drug(drug),
            price_controlled=self._is_nlem_drug(drug),
        )

    def _get_brand_price(
        self, drug: Drug, formulation: Optional[str]
    ) -> Optional[float]:
        """Get brand drug price."""
        mock_price = self._get_mock_price(drug, formulation, None)
        return mock_price.mrp

    def _get_generic_price(
        self, drug: Drug, formulation: Optional[str]
    ) -> Optional[float]:
        """Get generic drug price."""
        mock_price = self._get_mock_price(drug, formulation, None)
        return mock_price.online_price

    def _get_generic_alternatives(self, drug: Drug) -> list[str]:
        """Get list of generic manufacturers."""
        # In production, would query database of manufacturers
        # Mock data for common generic manufacturers in India
        generic_manufacturers = [
            f"{drug.generic_name} (Cipla)",
            f"{drug.generic_name} (Sun Pharma)",
            f"{drug.generic_name} (Dr. Reddy's)",
            f"{drug.generic_name} (Lupin)",
            f"{drug.generic_name} (Aurobindo)",
        ]

        return generic_manufacturers[:3]  # Return top 3

    def _is_nlem_drug(self, drug: Drug) -> bool:
        """Check if drug is in National List of Essential Medicines."""
        # Common essential medicines - simplified check
        # In production, would have complete NLEM database
        essential_drugs = [
            "metformin",
            "paracetamol",
            "amoxicillin",
            "amlodipine",
            "atenolol",
            "omeprazole",
            "ibuprofen",
            "aspirin",
            "insulin",
            "salbutamol",
        ]

        return any(
            essential in drug.generic_name.lower() for essential in essential_drugs
        )

    def _parse_dose_frequency(self, daily_dose: str) -> int:
        """Parse dose frequency from text."""
        daily_dose_lower = daily_dose.lower()

        if "once" in daily_dose_lower or "daily" in daily_dose_lower:
            return 1
        elif "twice" in daily_dose_lower or "bid" in daily_dose_lower:
            return 2
        elif "thrice" in daily_dose_lower or "three times" in daily_dose_lower or "tid" in daily_dose_lower:
            return 3
        elif "four times" in daily_dose_lower or "qid" in daily_dose_lower:
            return 4
        else:
            # Default to once daily
            return 1

    def get_price_trend(
        self,
        drug_id: str,
        months: int = 12,
    ) -> dict:
        """
        Get price trend for a drug.

        Args:
            drug_id: Drug identifier.
            months: Number of months of history.

        Returns:
            Price trend data.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {"error": "Drug not found"}

        # Mock trend data - in production would have historical pricing
        current_price = self._get_generic_price(drug, None) or 100.0

        return {
            "drug_name": drug.generic_name,
            "current_price": current_price,
            "trend": "stable",  # stable, increasing, decreasing
            "change_percent": 0.0,
            "message": "Historical pricing data not available",
        }

    def get_bulk_pricing(
        self,
        drug_id: str,
        quantity: int,
    ) -> dict:
        """
        Get bulk/wholesale pricing.

        Args:
            drug_id: Drug identifier.
            quantity: Quantity (number of units).

        Returns:
            Bulk pricing information.
        """
        drug = self.db.get_drug(drug_id)
        if not drug:
            return {"error": "Drug not found"}

        unit_price = self._get_generic_price(drug, None) or 0
        total_price = unit_price * quantity

        # Bulk discounts
        discount_percent = 0
        if quantity >= 100:
            discount_percent = 10
        elif quantity >= 50:
            discount_percent = 5

        discounted_price = total_price * (1 - discount_percent / 100)
        savings = total_price - discounted_price

        return {
            "drug_name": drug.generic_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
            "discount_percent": discount_percent,
            "discounted_price": discounted_price,
            "savings": savings,
        }
