"""
Patient Education Content Generator

Converts medical query answers into patient-friendly educational content.
Handles jargon simplification, reading level adjustment, and formatting.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.models import MedicalAnswer
from ..llm.synthesizer import Synthesizer
from .models import (
    PatientHandout,
    ContentType,
    ReadingLevel,
    DosDonts,
    WarningSign,
    SeverityLevel,
)


class ReadingLevelAnalyzer:
    """Analyzes and adjusts reading level of text."""

    def __init__(self):
        """Initialize reading level analyzer."""
        # Medical jargon dictionary for simplification
        self.jargon_map = {
            "myocardial infarction": "heart attack",
            "cerebrovascular accident": "stroke",
            "hypertension": "high blood pressure",
            "diabetes mellitus": "diabetes",
            "hyperlipidemia": "high cholesterol",
            "gastroesophageal reflux": "acid reflux",
            "osteoarthritis": "arthritis",
            "bronchitis": "chest infection",
            "dyspnea": "shortness of breath",
            "syncope": "fainting",
            "edema": "swelling",
            "pruritus": "itching",
            "vertigo": "dizziness",
            "tachycardia": "fast heartbeat",
            "bradycardia": "slow heartbeat",
            "arrhythmia": "irregular heartbeat",
            "ischemia": "reduced blood flow",
            "hemorrhage": "bleeding",
            "laceration": "cut",
            "contusion": "bruise",
            "fracture": "broken bone",
            "analgesic": "pain reliever",
            "antibiotic": "infection medicine",
            "antipyretic": "fever reducer",
            "antacid": "stomach acid reducer",
            "diuretic": "water pill",
            "anticoagulant": "blood thinner",
            "anticonvulsant": "seizure medicine",
            "antidepressant": "depression medicine",
            "anxiolytic": "anxiety medicine",
            "sedative": "sleep medicine",
            "prophylaxis": "prevention",
            "contraindication": "reason not to use",
            "adverse effect": "bad side effect",
            "parenteral": "by injection",
            "topical": "applied to skin",
            "subcutaneous": "under the skin",
            "intramuscular": "into the muscle",
            "intravenous": "into the vein",
        }

    def calculate_flesch_kincaid(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid grade level.

        Returns:
            Grade level (0-18+)
        """
        # Remove special characters and extra spaces
        text = re.sub(r"[^\w\s\.]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Count sentences
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        sentence_count = len(sentences)

        if sentence_count == 0:
            return 0.0

        # Count words
        words = text.split()
        word_count = len(words)

        if word_count == 0:
            return 0.0

        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(word) for word in words)

        # Flesch-Kincaid formula
        grade_level = (
            0.39 * (word_count / sentence_count)
            + 11.8 * (syllable_count / word_count)
            - 15.59
        )

        return max(0, grade_level)

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified algorithm)."""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith("e"):
            syllable_count -= 1

        # Ensure at least one syllable
        return max(1, syllable_count)

    def simplify_jargon(self, text: str) -> str:
        """
        Replace medical jargon with simpler terms.

        Args:
            text: Text containing medical terminology

        Returns:
            Simplified text
        """
        simplified = text

        for jargon, simple in self.jargon_map.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(jargon), re.IGNORECASE)
            simplified = pattern.sub(simple, simplified)

        return simplified

    def adjust_to_reading_level(
        self, text: str, target_level: ReadingLevel
    ) -> str:
        """
        Adjust text to target reading level.

        Args:
            text: Original text
            target_level: Target reading level

        Returns:
            Adjusted text
        """
        # Start with jargon simplification
        adjusted = self.simplify_jargon(text)

        # Calculate current level
        current_grade = self.calculate_flesch_kincaid(adjusted)

        # Target grade levels
        target_grades = {
            ReadingLevel.BASIC: 6.0,
            ReadingLevel.INTERMEDIATE: 10.0,
            ReadingLevel.ADVANCED: 14.0,
        }

        target_grade = target_grades[target_level]

        # If text is already at appropriate level, return it
        if abs(current_grade - target_grade) <= 2.0:
            return adjusted

        # For basic level, apply additional simplifications
        if target_level == ReadingLevel.BASIC and current_grade > 8.0:
            adjusted = self._apply_basic_simplifications(adjusted)

        return adjusted

    def _apply_basic_simplifications(self, text: str) -> str:
        """Apply additional simplifications for basic reading level."""
        # Break long sentences
        sentences = text.split(". ")
        simplified_sentences = []

        for sentence in sentences:
            # If sentence is too long (>20 words), try to break it
            words = sentence.split()
            if len(words) > 20:
                # Simple split at conjunctions
                for conj in [" and ", " but ", " or "]:
                    if conj in sentence:
                        parts = sentence.split(conj, 1)
                        simplified_sentences.append(parts[0].strip())
                        simplified_sentences.append(parts[1].strip())
                        break
                else:
                    simplified_sentences.append(sentence)
            else:
                simplified_sentences.append(sentence)

        return ". ".join(simplified_sentences)


class ContentGenerator:
    """Generates patient education content from medical answers."""

    def __init__(self, llm_synthesizer: Optional[Synthesizer] = None):
        """
        Initialize content generator.

        Args:
            llm_synthesizer: LLM synthesizer for generating content
        """
        self.llm = llm_synthesizer
        self.reading_analyzer = ReadingLevelAnalyzer()

    def generate_from_answer(
        self,
        answer: MedicalAnswer,
        content_type: ContentType,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
    ) -> PatientHandout:
        """
        Generate patient handout from medical query answer.

        Args:
            answer: Medical answer from Dora query
            content_type: Type of educational content
            reading_level: Target reading level
            language: Language code
            patient_name: Patient name for personalization
            doctor_name: Doctor name

        Returns:
            Complete patient handout
        """
        # Extract key information
        simplified_answer = self.reading_analyzer.adjust_to_reading_level(
            answer.answer, reading_level
        )

        # Generate appropriate content based on type
        if content_type == ContentType.MEDICATION_GUIDE:
            from .medications import MedicationGuideGenerator
            generator = MedicationGuideGenerator(self.llm)
            med_guide = generator.generate_from_text(
                simplified_answer, reading_level, language
            )
            content = {"medication_guide": med_guide}
            title = f"Medication Guide: {med_guide.generic_name}"

        elif content_type == ContentType.CONDITION_EXPLAINER:
            from .conditions import ConditionExplainerGenerator
            generator = ConditionExplainerGenerator(self.llm)
            condition = generator.generate_from_text(
                simplified_answer, reading_level, language
            )
            content = {"condition_explainer": condition}
            title = f"Understanding {condition.condition_name}"

        else:
            # General handout
            content = {
                "custom_sections": [
                    {"title": "Information", "content": simplified_answer}
                ]
            }
            title = answer.question

        # Extract warnings and do's/don'ts from answer
        warning_signs = self._extract_warning_signs(answer)
        dos_donts = self._extract_dos_donts(answer)

        # Build handout
        handout = PatientHandout(
            title=title,
            content_type=content_type,
            patient_name=patient_name,
            doctor_name=doctor_name,
            reading_level=reading_level,
            language=language,
            **content,
        )

        return handout

    def _extract_warning_signs(self, answer: MedicalAnswer) -> List[WarningSign]:
        """Extract warning signs from medical answer."""
        warning_signs = []

        # Look for warnings in the answer
        for warning in answer.warnings:
            warning_signs.append(
                WarningSign(
                    symptom=warning,
                    action="Contact your doctor immediately",
                    urgency=SeverityLevel.SEVERE,
                )
            )

        # Parse answer text for warning patterns
        warning_patterns = [
            r"seek immediate (medical )?attention if",
            r"call (your )?doctor (immediately )?if",
            r"emergency (?:room|department) if",
            r"warning signs? (?:include)?:?",
        ]

        answer_lower = answer.answer.lower()
        for pattern in warning_patterns:
            match = re.search(pattern, answer_lower)
            if match:
                # Extract text after pattern (simplified)
                remaining = answer.answer[match.end():match.end() + 200]
                # This is a simplified extraction; in production, use NLP
                break

        return warning_signs

    def _extract_dos_donts(self, answer: MedicalAnswer) -> Optional[DosDonts]:
        """Extract do's and don'ts from medical answer."""
        dos = []
        donts = []

        # Simple pattern matching
        dos_patterns = [
            r"(?:should|must|do) (.+?)(?:\.|;|\n)",
            r"recommended to (.+?)(?:\.|;|\n)",
        ]

        donts_patterns = [
            r"(?:should not|must not|don't|avoid) (.+?)(?:\.|;|\n)",
            r"not recommended to (.+?)(?:\.|;|\n)",
        ]

        answer_lower = answer.answer.lower()

        for pattern in dos_patterns:
            matches = re.findall(pattern, answer_lower)
            dos.extend(matches[:5])  # Limit to 5

        for pattern in donts_patterns:
            matches = re.findall(pattern, answer_lower)
            donts.extend(matches[:5])

        if dos or donts:
            return DosDonts(dos=dos, donts=donts)

        return None

    def add_visuals(
        self, handout: PatientHandout, visual_type: str = "icons"
    ) -> PatientHandout:
        """
        Add visual placeholders to handout.

        Args:
            handout: Patient handout
            visual_type: Type of visuals (icons, diagrams, images)

        Returns:
            Handout with visual placeholders
        """
        # Add visual placeholders based on content type
        # This would integrate with an icon/image library

        # For now, add placeholder markers
        visual_markers = {
            ContentType.MEDICATION_GUIDE: "💊",
            ContentType.CONDITION_EXPLAINER: "🩺",
            ContentType.PROCEDURE_PREP: "🏥",
            ContentType.POST_CARE_GUIDE: "🏠",
            ContentType.DIET_PLAN: "🥗",
            ContentType.LIFESTYLE_GUIDE: "🏃",
        }

        marker = visual_markers.get(handout.content_type, "📋")

        # Add marker to title
        if not handout.title.startswith(marker):
            handout.title = f"{marker} {handout.title}"

        return handout

    def generate_summary(
        self, handout: PatientHandout, max_words: int = 50
    ) -> str:
        """
        Generate brief summary of handout.

        Args:
            handout: Patient handout
            max_words: Maximum words in summary

        Returns:
            Brief summary
        """
        # Extract key content
        if handout.medication_guide:
            content = handout.medication_guide.purpose
        elif handout.condition_explainer:
            content = handout.condition_explainer.simple_explanation
        elif handout.custom_sections:
            content = handout.custom_sections[0].get("content", "")
        else:
            content = handout.title

        # Truncate to max words
        words = content.split()[:max_words]
        summary = " ".join(words)

        if len(content.split()) > max_words:
            summary += "..."

        return summary


class IconProvider:
    """Provides appropriate icons for medical content."""

    EMOJI_MAP = {
        # Symptoms
        "pain": "😣",
        "headache": "🤕",
        "fever": "🤒",
        "cough": "🤧",
        "nausea": "🤢",
        "dizziness": "😵",
        "fatigue": "😴",

        # Medical
        "medication": "💊",
        "pill": "💊",
        "injection": "💉",
        "syringe": "💉",
        "hospital": "🏥",
        "doctor": "👨‍⚕️",
        "stethoscope": "🩺",
        "thermometer": "🌡️",
        "bandage": "🩹",

        # Activities
        "exercise": "🏃",
        "walk": "🚶",
        "sleep": "😴",
        "water": "💧",

        # Food
        "food": "🍽️",
        "vegetable": "🥗",
        "fruit": "🍎",
        "meal": "🍽️",

        # Warnings
        "warning": "⚠️",
        "danger": "🚨",
        "stop": "🛑",
        "caution": "⚠️",

        # Positive
        "check": "✅",
        "yes": "✅",
        "good": "👍",

        # Negative
        "cross": "❌",
        "no": "❌",
        "bad": "👎",

        # Time
        "clock": "🕐",
        "calendar": "📅",

        # Communication
        "phone": "📞",
        "emergency": "🚨",
    }

    @classmethod
    def get_icon(cls, keyword: str) -> str:
        """
        Get emoji icon for keyword.

        Args:
            keyword: Keyword to find icon for

        Returns:
            Emoji or empty string
        """
        keyword_lower = keyword.lower()

        # Direct match
        if keyword_lower in cls.EMOJI_MAP:
            return cls.EMOJI_MAP[keyword_lower]

        # Partial match
        for key, emoji in cls.EMOJI_MAP.items():
            if key in keyword_lower or keyword_lower in key:
                return emoji

        return ""

    @classmethod
    def add_icons_to_list(cls, items: List[str]) -> List[str]:
        """
        Add relevant icons to list items.

        Args:
            items: List of text items

        Returns:
            List with icons prepended
        """
        result = []
        for item in items:
            icon = cls.get_icon(item)
            if icon:
                result.append(f"{icon} {item}")
            else:
                result.append(f"• {item}")

        return result
