"""
Education Content Translator

Translates patient education materials to multiple Indian languages.
Wraps the main i18n translator with medical education-specific functionality.
"""

from typing import Dict, Any, Optional, List

from ..i18n.translator import Translator, get_translator
from ..i18n.medical_terms import MEDICAL_TERMS_TRANSLATIONS
from .models import (
    PatientHandout,
    MedicationGuide,
    ConditionExplainer,
    ProcedurePrep,
    PostCareGuide,
    DietPlan,
    LifestyleGuide,
)


class EducationTranslator:
    """Translates patient education content to multiple languages."""

    SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "bn", "mr"]

    def __init__(self, target_language: str = "en"):
        """
        Initialize education translator.

        Args:
            target_language: Target language code
        """
        self.target_language = target_language
        self.translator = get_translator(target_language)

        # Common education phrases
        self.education_phrases = {
            "en": {
                "what_is": "What is",
                "how_to_take": "How to take",
                "side_effects": "Side effects",
                "when_to_call_doctor": "When to call your doctor",
                "warning_signs": "Warning signs",
                "dos": "Do's",
                "donts": "Don'ts",
                "symptoms": "Symptoms",
                "treatment": "Treatment",
                "causes": "Causes",
                "prevention": "Prevention",
                "follow_up": "Follow-up",
                "contact_doctor_if": "Contact your doctor if",
                "emergency": "Emergency",
                "immediately": "immediately",
                "as_needed": "as needed",
                "daily": "daily",
                "twice_daily": "twice daily",
                "with_food": "with food",
                "before_food": "before food",
                "at_bedtime": "at bedtime",
            },
            "hi": {
                "what_is": "क्या है",
                "how_to_take": "कैसे लें",
                "side_effects": "दुष्प्रभाव",
                "when_to_call_doctor": "डॉक्टर को कब बुलाएं",
                "warning_signs": "चेतावनी के संकेत",
                "dos": "क्या करें",
                "donts": "क्या न करें",
                "symptoms": "लक्षण",
                "treatment": "उपचार",
                "causes": "कारण",
                "prevention": "रोकथाम",
                "follow_up": "फॉलो-अप",
                "contact_doctor_if": "डॉक्टर से संपर्क करें अगर",
                "emergency": "आपातकाल",
                "immediately": "तुरंत",
                "as_needed": "जरूरत के अनुसार",
                "daily": "रोज",
                "twice_daily": "दिन में दो बार",
                "with_food": "खाने के साथ",
                "before_food": "खाने से पहले",
                "at_bedtime": "सोते समय",
            },
            # Add more languages as needed
        }

    def translate_handout(self, handout: PatientHandout) -> PatientHandout:
        """
        Translate patient handout to target language.

        Args:
            handout: Handout to translate

        Returns:
            Translated handout
        """
        if self.target_language == "en":
            return handout

        # Create a copy
        translated = handout.model_copy(deep=True)
        translated.language = self.target_language

        # Translate title
        translated.title = self._translate_text(handout.title)

        # Translate based on content type
        if translated.medication_guide:
            translated.medication_guide = self.translate_medication_guide(
                translated.medication_guide
            )
        elif translated.condition_explainer:
            translated.condition_explainer = self.translate_condition_explainer(
                translated.condition_explainer
            )
        elif translated.procedure_prep:
            translated.procedure_prep = self.translate_procedure_prep(
                translated.procedure_prep
            )
        elif translated.post_care_guide:
            translated.post_care_guide = self.translate_post_care_guide(
                translated.post_care_guide
            )

        # Translate custom sections
        if translated.custom_sections:
            translated.custom_sections = [
                {
                    "title": self._translate_text(section.get("title", "")),
                    "content": self._translate_text(section.get("content", "")),
                }
                for section in translated.custom_sections
            ]

        return translated

    def translate_medication_guide(
        self, guide: MedicationGuide
    ) -> MedicationGuide:
        """Translate medication guide."""
        if self.target_language == "en":
            return guide

        translated = guide.model_copy(deep=True)
        translated.language = self.target_language

        # Don't translate medication names, but translate purpose
        translated.purpose = self._translate_text(guide.purpose)

        # Translate instructions
        translated.instructions = [
            self._translate_text(instruction)
            for instruction in guide.instructions
        ]

        # Translate side effects descriptions
        for side_effect in translated.common_side_effects:
            side_effect.name = self._translate_medical_term(side_effect.name)
            if side_effect.description:
                side_effect.description = self._translate_text(side_effect.description)

        for side_effect in translated.serious_side_effects:
            side_effect.name = self._translate_medical_term(side_effect.name)
            if side_effect.description:
                side_effect.description = self._translate_text(side_effect.description)

        # Translate interactions
        translated.food_interactions = [
            self._translate_text(interaction)
            for interaction in guide.food_interactions
        ]
        translated.drug_interactions = [
            self._translate_text(interaction)
            for interaction in guide.drug_interactions
        ]

        # Translate storage and missed dose
        translated.storage_instructions = self._translate_text(
            guide.storage_instructions
        )
        translated.missed_dose_instructions = self._translate_text(
            guide.missed_dose_instructions
        )

        # Translate warning signs
        for warning in translated.warning_signs:
            warning.symptom = self._translate_text(warning.symptom)
            warning.action = self._translate_text(warning.action)

        return translated

    def translate_condition_explainer(
        self, explainer: ConditionExplainer
    ) -> ConditionExplainer:
        """Translate condition explainer."""
        if self.target_language == "en":
            return explainer

        translated = explainer.model_copy(deep=True)
        translated.language = self.target_language

        # Translate explanation
        translated.simple_explanation = self._translate_text(
            explainer.simple_explanation
        )

        # Translate lists
        translated.causes = [self._translate_text(c) for c in explainer.causes]
        translated.risk_factors = [
            self._translate_text(rf) for rf in explainer.risk_factors
        ]
        translated.common_symptoms = [
            self._translate_medical_term(s) for s in explainer.common_symptoms
        ]
        translated.how_diagnosed = [
            self._translate_text(d) for d in explainer.how_diagnosed
        ]
        translated.treatment_options = [
            self._translate_text(t) for t in explainer.treatment_options
        ]
        translated.lifestyle_changes = [
            self._translate_text(lc) for lc in explainer.lifestyle_changes
        ]
        translated.self_care = [self._translate_text(sc) for sc in explainer.self_care]

        # Translate warning signs
        for warning in translated.warning_signs:
            warning.symptom = self._translate_text(warning.symptom)
            warning.action = self._translate_text(warning.action)

        # Translate FAQs
        translated.frequently_asked_questions = [
            {
                "question": self._translate_text(faq.get("question", "")),
                "answer": self._translate_text(faq.get("answer", "")),
            }
            for faq in explainer.frequently_asked_questions
        ]

        return translated

    def translate_procedure_prep(self, prep: ProcedurePrep) -> ProcedurePrep:
        """Translate procedure prep guide."""
        if self.target_language == "en":
            return prep

        translated = prep.model_copy(deep=True)
        translated.language = self.target_language

        # Translate instructions
        for day_instr in translated.days_before_instructions:
            day_instr["day"] = self._translate_text(day_instr.get("day", ""))
            day_instr["instructions"] = [
                self._translate_text(instr)
                for instr in day_instr.get("instructions", [])
            ]

        if translated.fasting_instructions:
            translated.fasting_instructions = self._translate_text(
                prep.fasting_instructions
            )

        translated.what_to_bring = [
            self._translate_text(item) for item in prep.what_to_bring
        ]
        translated.medication_adjustments = [
            self._translate_text(adj) for adj in prep.medication_adjustments
        ]
        translated.what_happens_during = [
            self._translate_text(item) for item in prep.what_happens_during
        ]

        return translated

    def translate_post_care_guide(self, guide: PostCareGuide) -> PostCareGuide:
        """Translate post-care guide."""
        if self.target_language == "en":
            return guide

        translated = guide.model_copy(deep=True)
        translated.language = self.target_language

        # Translate title
        translated.title = self._translate_text(guide.title)

        # Translate timeline
        translated.recovery_timeline = [
            {
                "period": self._translate_text(item.get("period", "")),
                "expect": self._translate_text(item.get("expect", "")),
            }
            for item in guide.recovery_timeline
        ]

        # Translate instructions
        translated.wound_care_instructions = [
            self._translate_text(instr) for instr in guide.wound_care_instructions
        ]
        translated.activity_restrictions = [
            self._translate_text(restr) for restr in guide.activity_restrictions
        ]
        translated.diet_instructions = [
            self._translate_text(diet) for diet in guide.diet_instructions
        ]
        translated.pain_management = [
            self._translate_text(pm) for pm in guide.pain_management
        ]
        translated.when_to_call_doctor = [
            self._translate_text(when) for when in guide.when_to_call_doctor
        ]
        translated.emergency_signs = [
            self._translate_text(sign) for sign in guide.emergency_signs
        ]

        # Translate warning signs
        for warning in translated.warning_signs:
            warning.symptom = self._translate_text(warning.symptom)
            warning.action = self._translate_text(warning.action)

        return translated

    def _translate_text(self, text: str) -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or self.target_language == "en":
            return text

        # For now, we'll mark that translation is needed
        # In production, this would call a translation API or use pre-translated content
        # For Indian languages, we'd use Google Translate API, Microsoft Translator, or
        # a specialized medical translation service

        # Check for common phrases first
        phrases = self.education_phrases.get(self.target_language, {})
        for en_phrase, translated_phrase in self.education_phrases["en"].items():
            if translated_phrase.lower() in text.lower():
                target_phrase = phrases.get(en_phrase, translated_phrase)
                text = text.replace(translated_phrase, target_phrase)

        return text

    def _translate_medical_term(self, term: str) -> str:
        """
        Translate medical term using medical terminology dictionary.

        Args:
            term: Medical term

        Returns:
            Translated term
        """
        if not term or self.target_language == "en":
            return term

        # Use medical terms translator
        return self.translator.translate_medical_term(
            term, locale=self.target_language
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES

    def format_text_for_language(self, text: str, language: str) -> str:
        """
        Format text appropriately for language (RTL, etc.).

        Args:
            text: Text to format
            language: Language code

        Returns:
            Formatted text
        """
        # Check if RTL language
        if self.translator.is_rtl(language):
            # Add RTL markers if needed
            return f"\u202B{text}\u202C"

        return text


class WhatsAppFormatter:
    """Formats education content for WhatsApp delivery."""

    @staticmethod
    def format_medication_guide(guide: MedicationGuide) -> str:
        """
        Format medication guide for WhatsApp.

        Args:
            guide: Medication guide

        Returns:
            WhatsApp-formatted message
        """
        lines = [
            f"💊 *{guide.generic_name.upper()}*",
            f"({', '.join(guide.brand_names)})" if guide.brand_names else "",
            "",
            f"*यह दवा किसके लिए है:*",
            guide.purpose,
            "",
            f"*कैसे लें:*",
            f"• {guide.dosage.dose}",
            f"• {guide.dosage.frequency}",
        ]

        if guide.dosage.timing:
            lines.append(f"• {guide.dosage.timing}")

        if guide.common_side_effects:
            lines.extend([
                "",
                "*सामान्य दुष्प्रभाव:*",
            ])
            for se in guide.common_side_effects[:3]:
                lines.append(f"• {se.name}")

        if guide.warning_signs:
            lines.extend([
                "",
                "⚠️ *डॉक्टर को तुरंत बताएं अगर:*",
            ])
            for ws in guide.warning_signs[:3]:
                lines.append(f"• {ws.symptom}")

        # Remove empty lines
        return "\n".join([line for line in lines if line])

    @staticmethod
    def format_condition_explainer(explainer: ConditionExplainer) -> str:
        """Format condition explainer for WhatsApp."""
        lines = [
            f"🩺 *{explainer.condition_name.upper()}*",
            "",
            "*यह क्या है?*",
            explainer.simple_explanation,
            "",
        ]

        if explainer.common_symptoms:
            lines.append("*लक्षण:*")
            for symptom in explainer.common_symptoms[:5]:
                lines.append(f"• {symptom}")
            lines.append("")

        if explainer.lifestyle_changes:
            lines.append("*जीवनशैली में बदलाव:*")
            for change in explainer.lifestyle_changes[:5]:
                lines.append(f"✅ {change}")
            lines.append("")

        if explainer.warning_signs:
            lines.append("⚠️ *चेतावनी के संकेत:*")
            for ws in explainer.warning_signs[:3]:
                lines.append(f"• {ws.symptom}")

        return "\n".join(lines)


class SMSFormatter:
    """Formats education content for SMS delivery (160 characters)."""

    @staticmethod
    def format_medication_reminder(
        drug_name: str, dosage: str, frequency: str
    ) -> str:
        """
        Format medication reminder for SMS.

        Args:
            drug_name: Medication name
            dosage: Dosage amount
            frequency: How often

        Returns:
            SMS message (max 160 chars)
        """
        message = f"{drug_name} {dosage} {frequency}"
        return message[:160]

    @staticmethod
    def format_appointment_reminder(
        procedure: str, date: str, instructions: str
    ) -> str:
        """Format appointment reminder for SMS."""
        message = f"{procedure} on {date}. {instructions}"
        return message[:160]
