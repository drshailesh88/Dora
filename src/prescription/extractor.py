"""
Prescription extractor from Dora AI answers.

Extracts structured prescription data from natural language medical recommendations.
Uses LLM + regex + medical NLP for robust extraction.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from .models import (
    PrescriptionItem,
    Dosage,
    RouteOfAdministration,
    Frequency,
    DosageForm,
    DrugSchedule,
    Refill,
    Substitution,
)


class PrescriptionExtractor:
    """Extract prescription items from Dora AI answers."""

    # Common drug name patterns
    DRUG_PATTERNS = [
        r'Tab\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)',
        r'Cap\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)',
        r'Syp\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g)/(\d+)?\s*(ml)',
        r'Inj\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml)',
    ]

    # Frequency patterns
    FREQUENCY_PATTERNS = {
        r'\b1-0-1\b|\bbd\b|\bbid\b|\btwice\s+daily\b': Frequency.BD,
        r'\b1-1-1\b|\btds\b|\btid\b|\bthree\s+times\s+daily\b': Frequency.TDS,
        r'\b1-1-1-1\b|\bqid\b|\bfour\s+times\s+daily\b': Frequency.QID,
        r'\b0-0-1\b|\b1-0-0\b|\bod\b|\bonce\s+daily\b': Frequency.OD,
        r'\bqhs\b|\bat\s+bedtime\b|\bat\s+night\b': Frequency.QHS,
        r'\bprn\b|\bas\s+needed\b|\bwhen\s+required\b': Frequency.PRN,
        r'\bstat\b|\bimmediately\b': Frequency.STAT,
        r'\bweekly\b|\bonce\s+a\s+week\b': Frequency.WEEKLY,
        r'\balternate\s+days\b|\bqod\b': Frequency.QOD,
    }

    # Duration patterns
    DURATION_PATTERNS = [
        r'(?:for|x|×)\s*(\d+)\s*(?:days?|d)',
        r'(?:for|x|×)\s*(\d+)\s*(?:weeks?|w)',
        r'(?:for|x|×)\s*(\d+)\s*(?:months?|m)',
    ]

    # Route patterns
    ROUTE_PATTERNS = {
        r'\boral(?:ly)?\b|\bp\.?o\.?\b|\bby\s+mouth\b': RouteOfAdministration.ORAL,
        r'\biv\b|\bintravenous(?:ly)?\b': RouteOfAdministration.IV,
        r'\bim\b|\bintramuscular(?:ly)?\b': RouteOfAdministration.IM,
        r'\bsc\b|\bsubcutaneous(?:ly)?\b': RouteOfAdministration.SC,
        r'\btopical(?:ly)?\b': RouteOfAdministration.TOPICAL,
        r'\binhaled?\b|\binhalation\b': RouteOfAdministration.INHALED,
        r'\bsublingual(?:ly)?\b|\bs\.?l\.?\b': RouteOfAdministration.SUBLINGUAL,
    }

    # Dosage form patterns
    FORM_PATTERNS = {
        r'\btab(?:let)?s?\b': DosageForm.TABLET,
        r'\bcap(?:sule)?s?\b': DosageForm.CAPSULE,
        r'\bsyrup\b|\bsyp\b': DosageForm.SYRUP,
        r'\bsusp(?:ension)?\b': DosageForm.SUSPENSION,
        r'\binj(?:ection)?\b': DosageForm.INJECTION,
        r'\bcream\b': DosageForm.CREAM,
        r'\bointment\b': DosageForm.OINTMENT,
        r'\bdrops?\b': DosageForm.DROPS,
        r'\binhaler\b': DosageForm.INHALER,
    }

    def __init__(self, llm_client=None):
        """
        Initialize extractor.

        Args:
            llm_client: Optional LLM client for enhanced extraction
        """
        self.llm_client = llm_client

    def extract_from_answer(
        self,
        answer_text: str,
        use_llm: bool = True,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Extract prescription items from Dora answer text.

        Args:
            answer_text: The Dora AI answer containing recommendations
            use_llm: Whether to use LLM for extraction (more accurate)
            min_confidence: Minimum confidence threshold

        Returns:
            List of extracted prescription items with metadata
        """
        if use_llm and self.llm_client:
            return self._extract_with_llm(answer_text, min_confidence)
        else:
            return self._extract_with_regex(answer_text, min_confidence)

    def _extract_with_llm(
        self,
        answer_text: str,
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Extract prescriptions using LLM with structured output.

        More accurate than regex, especially for complex/varied formats.
        """
        prompt = f"""Extract prescription information from the following medical recommendation.

Return a JSON array of medications with this structure:
{{
  "medications": [
    {{
      "drug_name": "string",
      "generic_name": "string (if different)",
      "strength": "string with unit (e.g., 500mg)",
      "dosage_form": "tablet|capsule|syrup|injection|etc",
      "dose": "string (e.g., 1 tablet, 5ml)",
      "frequency": "once_daily|twice_daily|three_times_daily|etc",
      "frequency_detail": "string like 1-0-1 if mentioned",
      "duration_days": integer,
      "route": "oral|iv|im|topical|etc",
      "timing": "string (e.g., after food, before breakfast)",
      "instructions": "string (patient instructions)",
      "confidence": float (0-1)
    }}
  ]
}}

Medical text:
{answer_text}

Extract only medications that are explicitly recommended. Do not infer.
Return valid JSON only."""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,  # Low temperature for factual extraction
                max_tokens=2000
            )

            # Parse LLM response
            result = self._parse_llm_response(response)

            # Filter by confidence
            return [
                item for item in result
                if item.get('confidence', 0) >= min_confidence
            ]

        except Exception as e:
            print(f"LLM extraction failed: {e}. Falling back to regex.")
            return self._extract_with_regex(answer_text, min_confidence)

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM JSON response into prescription items."""
        # Extract JSON from response (LLM might add explanation)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            return []

        try:
            data = json.loads(json_match.group())
            return data.get('medications', [])
        except json.JSONDecodeError:
            return []

    def _extract_with_regex(
        self,
        answer_text: str,
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Extract prescriptions using regex patterns.

        Less accurate but works without LLM. Good for structured text.
        """
        items = []

        # Split into lines for line-by-line extraction
        lines = answer_text.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip empty lines or headers
            if not line.strip() or len(line.strip()) < 5:
                continue

            # Try to extract drug information
            drug_info = self._extract_drug_from_line(line)

            if drug_info:
                drug_info['line_number'] = line_num
                drug_info['extracted_from_text'] = line.strip()

                # Calculate confidence based on completeness
                drug_info['confidence'] = self._calculate_confidence(drug_info)

                if drug_info['confidence'] >= min_confidence:
                    items.append(drug_info)

        return items

    def _extract_drug_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract drug information from a single line."""
        # Try drug patterns
        drug_name = None
        strength = None
        strength_unit = None
        dosage_form = None

        for pattern in self.DRUG_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                drug_name = groups[0].strip()
                strength = groups[1]
                strength_unit = groups[2]

                # Infer dosage form from pattern
                if 'Tab' in match.group():
                    dosage_form = DosageForm.TABLET
                elif 'Cap' in match.group():
                    dosage_form = DosageForm.CAPSULE
                elif 'Syp' in match.group():
                    dosage_form = DosageForm.SYRUP
                elif 'Inj' in match.group():
                    dosage_form = DosageForm.INJECTION

                break

        if not drug_name:
            return None

        # Extract frequency
        frequency = self._extract_frequency(line)

        # Extract duration
        duration_days = self._extract_duration(line)

        # Extract route
        route = self._extract_route(line)

        # Extract timing/instructions
        timing = self._extract_timing(line)

        # Build result
        return {
            'drug_name': drug_name,
            'strength': f"{strength}{strength_unit}",
            'dosage_form': dosage_form,
            'frequency': frequency,
            'frequency_detail': self._extract_frequency_detail(line),
            'duration_days': duration_days,
            'route': route,
            'timing': timing,
            'instructions': None,  # Need more context for this
        }

    def _extract_frequency(self, text: str) -> str:
        """Extract frequency from text."""
        for pattern, freq in self.FREQUENCY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return freq.value

        return Frequency.CUSTOM.value

    def _extract_frequency_detail(self, text: str) -> Optional[str]:
        """Extract detailed frequency like 1-0-1."""
        match = re.search(r'\b(\d-\d(?:-\d)?(?:-\d)?)\b', text)
        if match:
            return match.group(1)
        return None

    def _extract_duration(self, text: str) -> int:
        """Extract duration in days."""
        for pattern in self.DURATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))

                # Convert to days
                if 'week' in pattern or 'w' in pattern:
                    return value * 7
                elif 'month' in pattern or 'm' in pattern:
                    return value * 30
                else:
                    return value

        # Default duration
        return 30

    def _extract_route(self, text: str) -> str:
        """Extract route of administration."""
        for pattern, route in self.ROUTE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return route.value

        return RouteOfAdministration.ORAL.value

    def _extract_timing(self, text: str) -> Optional[str]:
        """Extract timing instructions."""
        timing_patterns = [
            r'(after (?:food|meals|breakfast|lunch|dinner))',
            r'(before (?:food|meals|breakfast|lunch|dinner))',
            r'(with (?:food|meals))',
            r'(on empty stomach)',
            r'(at bedtime)',
            r'(in the morning)',
        ]

        for pattern in timing_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _calculate_confidence(self, drug_info: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on completeness of extraction.

        Higher confidence = more fields successfully extracted.
        """
        required_fields = ['drug_name', 'strength', 'frequency', 'duration_days']
        optional_fields = ['dosage_form', 'route', 'timing', 'frequency_detail']

        # Check required fields
        required_score = sum(
            1 for field in required_fields
            if drug_info.get(field) is not None
        ) / len(required_fields)

        # Check optional fields
        optional_score = sum(
            1 for field in optional_fields
            if drug_info.get(field) is not None
        ) / len(optional_fields)

        # Weighted average (required = 70%, optional = 30%)
        confidence = (required_score * 0.7) + (optional_score * 0.3)

        return round(confidence, 2)

    def build_prescription_items(
        self,
        extracted_data: List[Dict[str, Any]],
        require_confirmation: bool = True
    ) -> List[PrescriptionItem]:
        """
        Convert extracted data to PrescriptionItem models.

        Args:
            extracted_data: List of extracted drug dictionaries
            require_confirmation: Mark items as needing confirmation

        Returns:
            List of PrescriptionItem objects
        """
        items = []

        for idx, data in enumerate(extracted_data, 1):
            try:
                # Build dosage
                dosage = Dosage(
                    dose=data.get('dose', f"1 {data.get('dosage_form', 'tablet')}"),
                    frequency=Frequency(data.get('frequency', Frequency.CUSTOM.value)),
                    frequency_detail=data.get('frequency_detail'),
                    duration_days=data.get('duration_days', 30),
                    route=RouteOfAdministration(
                        data.get('route', RouteOfAdministration.ORAL.value)
                    ),
                    timing=data.get('timing'),
                )

                # Calculate quantity
                quantity = self._calculate_quantity(
                    dosage.frequency,
                    dosage.duration_days,
                    dosage.frequency_detail
                )

                # Build prescription item
                item = PrescriptionItem(
                    drug_name=data['drug_name'],
                    generic_name=data.get('generic_name'),
                    strength=data['strength'],
                    dosage_form=DosageForm(
                        data.get('dosage_form', DosageForm.TABLET.value)
                    ),
                    dosage=dosage,
                    quantity=quantity,
                    quantity_unit=self._get_quantity_unit(dosage.dosage_form),
                    item_sequence=idx,
                    instructions=data.get('instructions'),
                    extracted_from_text=data.get('extracted_from_text'),
                    confidence_score=data.get('confidence'),
                    needs_confirmation=require_confirmation,
                )

                items.append(item)

            except Exception as e:
                print(f"Failed to build item {idx}: {e}")
                continue

        return items

    def _calculate_quantity(
        self,
        frequency: Frequency,
        duration_days: int,
        frequency_detail: Optional[str]
    ) -> int:
        """Calculate total quantity needed."""
        # Parse frequency detail if available (e.g., "1-0-1" = 2 doses/day)
        if frequency_detail:
            doses_per_day = sum(int(d) for d in frequency_detail.split('-'))
        else:
            # Default doses per day by frequency
            doses_map = {
                Frequency.OD: 1,
                Frequency.BD: 2,
                Frequency.TDS: 3,
                Frequency.QID: 4,
                Frequency.QHS: 1,
                Frequency.WEEKLY: 1/7,
                Frequency.QOD: 0.5,
            }
            doses_per_day = doses_map.get(frequency, 2)  # Default to BD

        total_quantity = int(doses_per_day * duration_days)

        # Round up to nearest 10 for convenience
        return ((total_quantity + 9) // 10) * 10

    def _get_quantity_unit(self, dosage_form: DosageForm) -> str:
        """Get quantity unit based on dosage form."""
        unit_map = {
            DosageForm.TABLET: "tablets",
            DosageForm.CAPSULE: "capsules",
            DosageForm.SYRUP: "ml",
            DosageForm.SUSPENSION: "ml",
            DosageForm.INJECTION: "vials",
            DosageForm.CREAM: "gm",
            DosageForm.OINTMENT: "gm",
            DosageForm.DROPS: "ml",
            DosageForm.INHALER: "puffs",
        }
        return unit_map.get(dosage_form, "units")


# Example usage
if __name__ == "__main__":
    # Test extraction
    sample_answer = """
    For your type 2 diabetes, I recommend:

    1. Tab. Metformin 500mg - 1-0-1 x 30 days (after food)
    2. Tab. Glimepiride 2mg - 1-0-0 x 30 days (before breakfast)
    3. Tab. Amlodipine 5mg - 0-0-1 x 30 days (at bedtime)

    Also maintain diet and exercise.
    """

    extractor = PrescriptionExtractor(llm_client=None)
    extracted = extractor.extract_from_answer(sample_answer, use_llm=False)

    print("Extracted medications:")
    for item in extracted:
        print(f"  - {item['drug_name']} {item['strength']}")
        print(f"    Frequency: {item['frequency']}")
        print(f"    Duration: {item['duration_days']} days")
        print(f"    Confidence: {item['confidence']}")
        print()

    # Build prescription items
    items = extractor.build_prescription_items(extracted)
    print(f"\nCreated {len(items)} prescription items")
