"""
Drug alternatives suggester for Dora.

Suggests alternative medications based on:
- Generic equivalents (cost savings)
- Therapeutic alternatives (same class)
- Insurance formulary
- Availability
- Safety profile
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from dataclasses import dataclass

from .models import DrugAlternative, PrescriptionItem


@dataclass
class DrugPrice:
    """Drug pricing information."""
    drug_name: str
    strength: str
    price_per_unit: Decimal
    package_size: int
    total_price: Decimal
    pharmacy: Optional[str] = None


class AlternativesSuggester:
    """Suggest drug alternatives for cost savings and availability."""

    def __init__(self, drug_database=None, pricing_database=None):
        """
        Initialize suggester.

        Args:
            drug_database: Drug information database
            pricing_database: Drug pricing database
        """
        self.drug_db = drug_database
        self.pricing_db = pricing_database or self._get_default_pricing()

    def suggest_alternatives(
        self,
        item: PrescriptionItem,
        include_generics: bool = True,
        include_therapeutic: bool = True,
        max_alternatives: int = 5
    ) -> List[DrugAlternative]:
        """
        Suggest alternatives for a prescription item.

        Args:
            item: Prescription item to find alternatives for
            include_generics: Include generic equivalents
            include_therapeutic: Include therapeutic alternatives
            max_alternatives: Maximum number of suggestions

        Returns:
            List of drug alternatives ranked by recommendation
        """
        alternatives = []

        # 1. Generic equivalents (if brand prescribed)
        if include_generics:
            generics = self._find_generic_equivalents(item)
            alternatives.extend(generics)

        # 2. Therapeutic alternatives (same drug class)
        if include_therapeutic:
            therapeutics = self._find_therapeutic_alternatives(item)
            alternatives.extend(therapeutics)

        # 3. Formulary alternatives (insurance coverage)
        formulary = self._find_formulary_alternatives(item)
        alternatives.extend(formulary)

        # 4. Remove duplicates
        alternatives = self._deduplicate_alternatives(alternatives)

        # 5. Rank by priority (cost savings, safety, availability)
        alternatives = self._rank_alternatives(alternatives)

        # 6. Limit to max
        return alternatives[:max_alternatives]

    def _find_generic_equivalents(
        self,
        item: PrescriptionItem
    ) -> List[DrugAlternative]:
        """Find generic equivalents for brand-name drugs."""
        generics = []

        # Get generic name if brand
        generic_name = self._get_generic_name(item.drug_name)

        if not generic_name or generic_name.lower() == item.drug_name.lower():
            # Already generic
            return generics

        # Get pricing
        original_price = self._get_drug_price(item.drug_name, item.strength, item.quantity)
        generic_price = self._get_drug_price(generic_name, item.strength, item.quantity)

        if generic_price and original_price:
            savings = original_price - generic_price

            if savings > 0:
                alternative = DrugAlternative(
                    original_drug=item.drug_name,
                    alternative_drug=generic_name,
                    alternative_generic_name=generic_name,
                    strength=item.strength,
                    therapeutic_equivalence="identical",
                    reason_for_suggestion="cheaper",
                    original_price=original_price,
                    alternative_price=generic_price,
                    savings_per_month=savings,
                    available_in_formulary=True,
                    availability_status="widely_available",
                    safety_comparison="equivalent",
                    confidence=0.95,
                )
                generics.append(alternative)

        return generics

    def _find_therapeutic_alternatives(
        self,
        item: PrescriptionItem
    ) -> List[DrugAlternative]:
        """Find therapeutic alternatives in same drug class."""
        alternatives = []

        # Get drug class
        drug_class = self._get_drug_class(item.drug_name)

        if not drug_class:
            return alternatives

        # Get alternatives in same class
        class_members = self._get_class_members(drug_class)

        for member in class_members:
            if member.lower() == item.drug_name.lower():
                continue

            # Get pricing
            original_price = self._get_drug_price(item.drug_name, item.strength, item.quantity)
            alt_price = self._get_drug_price(member, item.strength, item.quantity)

            if alt_price and original_price and alt_price < original_price:
                savings = original_price - alt_price

                alternative = DrugAlternative(
                    original_drug=item.drug_name,
                    alternative_drug=member,
                    alternative_generic_name=self._get_generic_name(member) or member,
                    strength=item.strength,
                    therapeutic_equivalence="similar",
                    reason_for_suggestion="cheaper",
                    original_price=original_price,
                    alternative_price=alt_price,
                    savings_per_month=savings,
                    safety_comparison=self._compare_safety(item.drug_name, member),
                    confidence=0.8,
                )
                alternatives.append(alternative)

        return alternatives

    def _find_formulary_alternatives(
        self,
        item: PrescriptionItem
    ) -> List[DrugAlternative]:
        """Find alternatives in insurance formulary."""
        # Stub - would integrate with insurance formulary database
        return []

    def _get_generic_name(self, drug_name: str) -> Optional[str]:
        """Get generic name for a drug."""
        # Common brand to generic mappings (stub data)
        brand_to_generic = {
            'crocin': 'paracetamol',
            'dolo': 'paracetamol',
            'brufen': 'ibuprofen',
            'combiflam': 'ibuprofen+paracetamol',
            'augmentin': 'amoxicillin+clavulanic acid',
            'azithral': 'azithromycin',
            'pan': 'pantoprazole',
            'lipaglyn': 'saroglitazar',
        }

        return brand_to_generic.get(drug_name.lower())

    def _get_drug_price(
        self,
        drug_name: str,
        strength: str,
        quantity: int
    ) -> Optional[Decimal]:
        """Get drug price from pricing database."""
        # Stub pricing data (Indian Rupees)
        prices = {
            'metformin_500mg': Decimal('2.00'),    # per tablet
            'metformin_1000mg': Decimal('3.50'),
            'glimepiride_2mg': Decimal('3.00'),
            'amlodipine_5mg': Decimal('1.50'),
            'atorvastatin_10mg': Decimal('5.00'),
            'atorvastatin_20mg': Decimal('8.00'),
            'paracetamol_500mg': Decimal('0.50'),
            'crocin_500mg': Decimal('2.00'),       # Brand - more expensive
            'ibuprofen_400mg': Decimal('1.50'),
            'brufen_400mg': Decimal('5.00'),       # Brand - more expensive
        }

        # Normalize key
        key = f"{drug_name.lower()}_{strength.lower().replace(' ', '')}"

        price_per_unit = prices.get(key)

        if price_per_unit:
            return price_per_unit * quantity

        # If not found, try drug database
        if self.pricing_db:
            try:
                return self.pricing_db.get_price(drug_name, strength, quantity)
            except Exception:
                pass

        return None

    def _get_drug_class(self, drug_name: str) -> Optional[str]:
        """Get therapeutic class of drug."""
        # Drug classifications (stub data)
        drug_classes = {
            'metformin': 'biguanide',
            'glimepiride': 'sulfonylurea',
            'gliclazide': 'sulfonylurea',
            'glipizide': 'sulfonylurea',
            'pioglitazone': 'thiazolidinedione',
            'amlodipine': 'calcium_channel_blocker',
            'nifedipine': 'calcium_channel_blocker',
            'diltiazem': 'calcium_channel_blocker',
            'atorvastatin': 'statin',
            'simvastatin': 'statin',
            'rosuvastatin': 'statin',
            'lisinopril': 'ace_inhibitor',
            'ramipril': 'ace_inhibitor',
            'enalapril': 'ace_inhibitor',
        }

        return drug_classes.get(drug_name.lower())

    def _get_class_members(self, drug_class: str) -> List[str]:
        """Get all drugs in a therapeutic class."""
        # Reverse mapping from class to members
        class_members = {
            'sulfonylurea': ['Glimepiride', 'Gliclazide', 'Glipizide'],
            'calcium_channel_blocker': ['Amlodipine', 'Nifedipine', 'Diltiazem'],
            'statin': ['Atorvastatin', 'Simvastatin', 'Rosuvastatin'],
            'ace_inhibitor': ['Lisinopril', 'Ramipril', 'Enalapril'],
        }

        return class_members.get(drug_class, [])

    def _compare_safety(self, drug1: str, drug2: str) -> str:
        """Compare safety profiles of two drugs."""
        # Stub - would use real safety data
        return "comparable"

    def _deduplicate_alternatives(
        self,
        alternatives: List[DrugAlternative]
    ) -> List[DrugAlternative]:
        """Remove duplicate suggestions."""
        seen = set()
        unique = []

        for alt in alternatives:
            key = f"{alt.alternative_drug}_{alt.strength}"
            if key not in seen:
                seen.add(key)
                unique.append(alt)

        return unique

    def _rank_alternatives(
        self,
        alternatives: List[DrugAlternative]
    ) -> List[DrugAlternative]:
        """
        Rank alternatives by priority.

        Priority factors:
        1. Cost savings (high weight)
        2. Therapeutic equivalence (prefer identical)
        3. Safety (prefer better safety)
        4. Availability (prefer widely available)
        5. Confidence score
        """
        def rank_score(alt: DrugAlternative) -> float:
            score = 0.0

            # Cost savings (0-50 points)
            if alt.savings_per_month:
                # ₹100 savings = 10 points, capped at 50
                score += min(float(alt.savings_per_month) / 10, 50)

            # Therapeutic equivalence (0-30 points)
            if alt.therapeutic_equivalence == "identical":
                score += 30
            elif alt.therapeutic_equivalence == "similar":
                score += 20
            else:
                score += 10

            # Safety (0-10 points)
            if alt.safety_comparison == "better":
                score += 10
            elif alt.safety_comparison == "equivalent":
                score += 5

            # Availability (0-5 points)
            if alt.available_in_formulary:
                score += 5

            # Confidence (0-5 points)
            score += alt.confidence * 5

            return score

        # Sort by score (descending)
        return sorted(alternatives, key=rank_score, reverse=True)

    def _get_default_pricing(self):
        """Get default pricing database stub."""
        return None


class CostComparisonReport:
    """Generate cost comparison reports."""

    @staticmethod
    def compare_prescription_costs(
        original_items: List[PrescriptionItem],
        alternative_items: List[PrescriptionItem],
        pricing_db=None
    ) -> Dict[str, Any]:
        """
        Compare total costs of two prescriptions.

        Args:
            original_items: Original prescription items
            alternative_items: Alternative prescription items
            pricing_db: Pricing database

        Returns:
            Cost comparison report
        """
        suggester = AlternativesSuggester(pricing_database=pricing_db)

        original_total = Decimal('0')
        alternative_total = Decimal('0')

        for item in original_items:
            price = suggester._get_drug_price(item.drug_name, item.strength, item.quantity)
            if price:
                original_total += price

        for item in alternative_items:
            price = suggester._get_drug_price(item.drug_name, item.strength, item.quantity)
            if price:
                alternative_total += price

        savings = original_total - alternative_total
        savings_percent = (savings / original_total * 100) if original_total > 0 else 0

        return {
            'original_cost': float(original_total),
            'alternative_cost': float(alternative_total),
            'savings': float(savings),
            'savings_percent': float(savings_percent),
            'currency': 'INR',
        }


# Example usage
if __name__ == "__main__":
    from .models import (
        PrescriptionItem, Dosage, DosageForm, Frequency, RouteOfAdministration
    )

    # Test item - expensive brand
    item = PrescriptionItem(
        drug_name="Crocin",  # Brand paracetamol
        strength="500mg",
        dosage_form=DosageForm.TABLET,
        dosage=Dosage(
            dose="1 tablet",
            frequency=Frequency.TDS,
            duration_days=5,
            route=RouteOfAdministration.ORAL,
        ),
        quantity=15,
        quantity_unit="tablets",
        item_sequence=1,
    )

    # Find alternatives
    suggester = AlternativesSuggester()
    alternatives = suggester.suggest_alternatives(item)

    print(f"Alternatives for {item.drug_name} {item.strength}:")
    for alt in alternatives:
        print(f"\n  Alternative: {alt.alternative_drug}")
        print(f"  Reason: {alt.reason_for_suggestion}")
        print(f"  Original price: ₹{alt.original_price}")
        print(f"  Alternative price: ₹{alt.alternative_price}")
        print(f"  Monthly savings: ₹{alt.savings_per_month}")
        print(f"  Equivalence: {alt.therapeutic_equivalence}")
        print(f"  Confidence: {alt.confidence}")
