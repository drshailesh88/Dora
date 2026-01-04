"""
Medication Guide Generator

Generates patient-friendly medication guides with dosage instructions,
side effects, interactions, and safety information.
"""

import re
from typing import Optional, List, Dict, Any

from ..llm.synthesizer import Synthesizer
from .models import (
    MedicationGuide,
    DosageInstruction,
    SideEffect,
    WarningSign,
    SeverityLevel,
    ReadingLevel,
)


class MedicationGuideGenerator:
    """Generates comprehensive medication guides for patients."""

    def __init__(self, llm_synthesizer: Optional[Synthesizer] = None):
        """
        Initialize medication guide generator.

        Args:
            llm_synthesizer: LLM for generating content
        """
        self.llm = llm_synthesizer

        # Common medication classes and their purposes (simple terms)
        self.medication_classes = {
            "antihypertensive": "controls high blood pressure",
            "antidiabetic": "controls blood sugar",
            "antibiotic": "fights bacterial infections",
            "analgesic": "relieves pain",
            "antipyretic": "reduces fever",
            "anticoagulant": "prevents blood clots",
            "statin": "lowers cholesterol",
            "proton pump inhibitor": "reduces stomach acid",
            "beta blocker": "slows heart rate and lowers blood pressure",
            "ace inhibitor": "lowers blood pressure",
            "diuretic": "removes excess water from body",
            "nsaid": "reduces pain and inflammation",
            "corticosteroid": "reduces inflammation",
            "antidepressant": "treats depression",
            "anxiolytic": "reduces anxiety",
            "bronchodilator": "opens airways",
            "antihistamine": "treats allergies",
            "antacid": "neutralizes stomach acid",
        }

        # Common side effects by category
        self.common_side_effects = {
            "gastrointestinal": [
                SideEffect(
                    name="nausea",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="feeling sick to your stomach"
                ),
                SideEffect(
                    name="diarrhea",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="loose or watery stools"
                ),
                SideEffect(
                    name="constipation",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="difficulty passing stools"
                ),
                SideEffect(
                    name="stomach upset",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="discomfort in stomach"
                ),
            ],
            "neurological": [
                SideEffect(
                    name="dizziness",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="feeling lightheaded"
                ),
                SideEffect(
                    name="headache",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="head pain"
                ),
                SideEffect(
                    name="drowsiness",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="feeling sleepy"
                ),
            ],
            "general": [
                SideEffect(
                    name="fatigue",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="feeling tired"
                ),
                SideEffect(
                    name="dry mouth",
                    severity=SeverityLevel.MILD,
                    frequency="common",
                    description="lack of saliva"
                ),
            ],
        }

    def generate_from_drug_name(
        self,
        generic_name: str,
        brand_names: Optional[List[str]] = None,
        indication: Optional[str] = None,
        dosage: Optional[str] = None,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> MedicationGuide:
        """
        Generate medication guide from drug name.

        Args:
            generic_name: Generic medication name
            brand_names: Brand names
            indication: What it's prescribed for
            dosage: Dosage instruction
            reading_level: Target reading level
            language: Language code

        Returns:
            Complete medication guide
        """
        # Parse dosage instruction
        dosage_info = self._parse_dosage(dosage) if dosage else None

        if not dosage_info:
            dosage_info = DosageInstruction(
                dose="As prescribed by doctor",
                frequency="As directed",
            )

        # Determine purpose from indication or drug class
        purpose = indication or self._determine_purpose(generic_name)

        # Build medication guide
        guide = MedicationGuide(
            generic_name=generic_name,
            brand_names=brand_names or [],
            purpose=purpose,
            condition_treated=indication,
            dosage=dosage_info,
            reading_level=reading_level,
            language=language,
        )

        # Add common instructions
        guide.instructions = self._generate_instructions(generic_name, dosage_info)

        # Add common side effects
        guide.common_side_effects = self._get_common_side_effects(generic_name)

        # Add serious side effects
        guide.serious_side_effects = self._get_serious_side_effects(generic_name)

        # Add warning signs
        guide.warning_signs = self._generate_warning_signs(generic_name)

        # Add food/drug interactions
        guide.food_interactions = self._get_food_interactions(generic_name)
        guide.drug_interactions = self._get_drug_interactions(generic_name)

        # Add missed dose instructions
        guide.missed_dose_instructions = self._generate_missed_dose_instructions(
            dosage_info
        )

        return guide

    def generate_from_text(
        self,
        text: str,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> MedicationGuide:
        """
        Generate medication guide from free text.

        Args:
            text: Text about medication
            reading_level: Target reading level
            language: Language code

        Returns:
            Medication guide
        """
        # Extract drug name from text
        generic_name = self._extract_drug_name(text)

        # Extract dosage
        dosage = self._extract_dosage(text)

        # Extract indication
        indication = self._extract_indication(text)

        return self.generate_from_drug_name(
            generic_name=generic_name,
            indication=indication,
            dosage=dosage,
            reading_level=reading_level,
            language=language,
        )

    def _parse_dosage(self, dosage_str: str) -> DosageInstruction:
        """Parse dosage string into structured format."""
        # Extract dose amount
        dose_pattern = r"(\d+\s*(?:mg|g|ml|mcg|units?))"
        dose_match = re.search(dose_pattern, dosage_str, re.IGNORECASE)
        dose = dose_match.group(1) if dose_match else "As prescribed"

        # Extract frequency
        frequency_patterns = {
            r"once\s+(?:a\s+)?day|daily|qd|od": "once daily",
            r"twice\s+(?:a\s+)?day|bid|bd": "twice daily",
            r"three\s+times\s+(?:a\s+)?day|tid|tds": "three times daily",
            r"four\s+times\s+(?:a\s+)?day|qid|qds": "four times daily",
            r"every\s+(\d+)\s+hours": lambda m: f"every {m.group(1)} hours",
            r"at\s+bedtime|hs|qhs": "at bedtime",
            r"in\s+the\s+morning|qam": "in the morning",
        }

        frequency = "as directed"
        for pattern, replacement in frequency_patterns.items():
            match = re.search(pattern, dosage_str, re.IGNORECASE)
            if match:
                if callable(replacement):
                    frequency = replacement(match)
                else:
                    frequency = replacement
                break

        # Extract timing
        timing = None
        if "with food" in dosage_str.lower():
            timing = "with food"
        elif "before food" in dosage_str.lower() or "on empty stomach" in dosage_str.lower():
            timing = "on empty stomach"
        elif "after food" in dosage_str.lower():
            timing = "after meals"
        elif "at bedtime" in dosage_str.lower():
            timing = "at bedtime"

        return DosageInstruction(
            dose=dose,
            frequency=frequency,
            timing=timing,
        )

    def _determine_purpose(self, generic_name: str) -> str:
        """Determine medication purpose from name or class."""
        name_lower = generic_name.lower()

        # Common medications and their purposes
        purposes = {
            "metformin": "controls blood sugar in diabetes",
            "amlodipine": "lowers blood pressure",
            "atorvastatin": "lowers cholesterol",
            "omeprazole": "reduces stomach acid",
            "aspirin": "prevents blood clots and relieves pain",
            "paracetamol": "reduces pain and fever",
            "ibuprofen": "reduces pain and inflammation",
            "amoxicillin": "treats bacterial infections",
            "azithromycin": "treats bacterial infections",
            "levothyroxine": "treats low thyroid hormone",
            "losartan": "lowers blood pressure",
            "lisinopril": "lowers blood pressure",
            "simvastatin": "lowers cholesterol",
            "pantoprazole": "reduces stomach acid",
            "insulin": "controls blood sugar in diabetes",
        }

        # Check for direct match
        for drug, purpose in purposes.items():
            if drug in name_lower:
                return purpose

        # Check by suffix (drug class)
        if name_lower.endswith("pril"):
            return "lowers blood pressure (ACE inhibitor)"
        elif name_lower.endswith("sartan"):
            return "lowers blood pressure (ARB)"
        elif name_lower.endswith("statin"):
            return "lowers cholesterol"
        elif name_lower.endswith("olol"):
            return "lowers blood pressure and slows heart rate"
        elif name_lower.endswith("cillin"):
            return "treats bacterial infections (antibiotic)"
        elif name_lower.endswith("mycin"):
            return "treats bacterial infections (antibiotic)"
        elif name_lower.endswith("azole"):
            return "treats fungal infections"

        return "treats your condition as prescribed by your doctor"

    def _generate_instructions(
        self, generic_name: str, dosage: DosageInstruction
    ) -> List[str]:
        """Generate how-to-take instructions."""
        instructions = []

        # Based on timing
        if dosage.timing == "with food":
            instructions.append("Take with meals to reduce stomach upset")
        elif dosage.timing == "on empty stomach":
            instructions.append("Take on empty stomach (1 hour before or 2 hours after meals)")
        elif dosage.timing == "at bedtime":
            instructions.append("Take at bedtime")

        # General instructions
        instructions.extend([
            "Swallow tablet whole with water",
            "Take at the same time(s) each day",
            "Do not skip doses",
            "Complete the full course even if you feel better",
        ])

        return instructions[:5]  # Limit to 5 key instructions

    def _get_common_side_effects(self, generic_name: str) -> List[SideEffect]:
        """Get common side effects for medication."""
        # Return general mild side effects
        # In production, this would query a drug database
        return self.common_side_effects["gastrointestinal"][:2] + \
               self.common_side_effects["neurological"][:2]

    def _get_serious_side_effects(self, generic_name: str) -> List[SideEffect]:
        """Get serious side effects requiring medical attention."""
        # Generic serious side effects
        serious = [
            SideEffect(
                name="severe allergic reaction",
                severity=SeverityLevel.EMERGENCY,
                frequency="rare",
                description="rash, itching, swelling, severe dizziness, trouble breathing"
            ),
            SideEffect(
                name="chest pain",
                severity=SeverityLevel.SEVERE,
                frequency="rare",
                description="pain or pressure in chest"
            ),
        ]

        return serious

    def _generate_warning_signs(self, generic_name: str) -> List[WarningSign]:
        """Generate when-to-call-doctor warning signs."""
        warnings = [
            WarningSign(
                symptom="Difficulty breathing or swallowing",
                action="Call emergency services immediately",
                urgency=SeverityLevel.EMERGENCY,
            ),
            WarningSign(
                symptom="Severe rash or hives",
                action="Call your doctor immediately",
                urgency=SeverityLevel.SEVERE,
            ),
            WarningSign(
                symptom="Side effects that don't go away or get worse",
                action="Contact your doctor",
                urgency=SeverityLevel.MODERATE,
            ),
        ]

        return warnings

    def _get_food_interactions(self, generic_name: str) -> List[str]:
        """Get food interactions."""
        name_lower = generic_name.lower()

        interactions = {
            "warfarin": ["Avoid large amounts of vitamin K-rich foods (spinach, broccoli)"],
            "metronidazole": ["Avoid alcohol during treatment and 3 days after"],
            "tetracycline": ["Avoid dairy products (milk, yogurt, cheese)"],
            "statins": ["Avoid grapefruit juice"],
            "mao inhibitors": ["Avoid aged cheeses, cured meats, fermented foods"],
        }

        for drug, foods in interactions.items():
            if drug in name_lower:
                return foods

        return []

    def _get_drug_interactions(self, generic_name: str) -> List[str]:
        """Get common drug interactions."""
        # Generic warning
        return [
            "Tell your doctor about all medications you are taking",
            "This includes over-the-counter medicines and supplements",
        ]

    def _generate_missed_dose_instructions(
        self, dosage: DosageInstruction
    ) -> str:
        """Generate missed dose instructions."""
        if "bedtime" in dosage.timing.lower():
            return "Skip the missed dose and take your next dose at the usual time. Do not double the dose."
        else:
            return "Take the missed dose as soon as you remember. If it's almost time for your next dose, skip the missed dose. Do not double the dose."

    def _extract_drug_name(self, text: str) -> str:
        """Extract drug name from text."""
        # Look for capitalized drug names or medication mentioned
        # This is simplified; in production, use NER or drug database
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["medication", "drug", "medicine"]:
                if i > 0:
                    return words[i - 1].strip(".,;:")

        # Return first capitalized word as fallback
        for word in words:
            if word[0].isupper() and len(word) > 3:
                return word.strip(".,;:")

        return "Medication"

    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage from text."""
        # Look for dosage patterns
        pattern = r"(\d+\s*(?:mg|g|ml|mcg|units?)\s+(?:once|twice|three times|four times)?\s*(?:a\s+)?(?:day|daily|bid|tid|qid)?)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1)

        return None

    def _extract_indication(self, text: str) -> Optional[str]:
        """Extract indication/purpose from text."""
        # Look for "for", "to treat", etc.
        patterns = [
            r"for\s+(.+?)(?:\.|,|\n|$)",
            r"to\s+treat\s+(.+?)(?:\.|,|\n|$)",
            r"used\s+for\s+(.+?)(?:\.|,|\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None


class PillIdentifier:
    """Visual pill identification helper."""

    def __init__(self):
        """Initialize pill identifier."""
        pass

    def generate_description(
        self,
        color: Optional[str] = None,
        shape: Optional[str] = None,
        imprint: Optional[str] = None,
        size: Optional[str] = None,
    ) -> str:
        """
        Generate pill description.

        Args:
            color: Pill color
            shape: Pill shape
            imprint: Imprint/marking on pill
            size: Pill size

        Returns:
            Description string
        """
        parts = []

        if size:
            parts.append(size)
        if color:
            parts.append(color)
        if shape:
            parts.append(shape + " pill")
        else:
            parts.append("pill")

        if imprint:
            parts.append(f"with '{imprint}' imprint")

        return " ".join(parts)

    def get_common_shapes(self) -> List[str]:
        """Get list of common pill shapes."""
        return [
            "round",
            "oval",
            "capsule",
            "rectangular",
            "square",
            "diamond",
            "triangular",
        ]

    def get_common_colors(self) -> List[str]:
        """Get list of common pill colors."""
        return [
            "white",
            "blue",
            "pink",
            "yellow",
            "orange",
            "green",
            "red",
            "purple",
            "brown",
            "gray",
            "multicolored",
        ]
