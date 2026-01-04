"""
Condition Explainer Generator

Generates patient-friendly explanations of medical conditions including
causes, symptoms, diagnosis, treatment, and prognosis.
"""

from typing import Optional, List, Dict

from ..llm.synthesizer import Synthesizer
from .models import (
    ConditionExplainer,
    WarningSign,
    SeverityLevel,
    DosDonts,
    ReadingLevel,
)


class ConditionExplainerGenerator:
    """Generates patient-friendly condition explanations."""

    def __init__(self, llm_synthesizer: Optional[Synthesizer] = None):
        """
        Initialize condition explainer generator.

        Args:
            llm_synthesizer: LLM for generating content
        """
        self.llm = llm_synthesizer

        # Common conditions with simple explanations
        self.condition_library = {
            "diabetes": {
                "simple_explanation": "Diabetes means your blood sugar (glucose) is too high. Your body either doesn't make enough insulin or can't use it properly. Insulin helps sugar get into your cells for energy.",
                "alternate_names": ["Diabetes Mellitus", "Sugar Disease"],
                "common_symptoms": [
                    "Feeling very thirsty",
                    "Urinating more than usual",
                    "Feeling very hungry",
                    "Feeling tired",
                    "Blurry vision",
                    "Slow healing of cuts",
                    "Tingling in hands or feet",
                ],
                "causes": [
                    "Type 1: Body's immune system attacks insulin-producing cells",
                    "Type 2: Body becomes resistant to insulin or doesn't produce enough",
                ],
                "risk_factors": [
                    "Family history of diabetes",
                    "Being overweight",
                    "Lack of physical activity",
                    "Age over 45",
                    "High blood pressure",
                ],
            },
            "hypertension": {
                "simple_explanation": "Hypertension (high blood pressure) means the force of blood against your artery walls is too high. This makes your heart work harder and can damage your blood vessels over time.",
                "alternate_names": ["High Blood Pressure", "HTN"],
                "common_symptoms": [
                    "Often no symptoms (silent disease)",
                    "Headaches",
                    "Shortness of breath",
                    "Nosebleeds (rare)",
                ],
                "causes": [
                    "Often no single cause (primary hypertension)",
                    "Kidney disease",
                    "Thyroid problems",
                    "Sleep apnea",
                ],
                "risk_factors": [
                    "Age",
                    "Family history",
                    "Being overweight",
                    "Too much salt in diet",
                    "Lack of exercise",
                    "Smoking",
                    "Stress",
                ],
            },
            "asthma": {
                "simple_explanation": "Asthma is a condition where your airways (breathing tubes) become narrow and swollen. This makes it hard to breathe. It can come and go.",
                "alternate_names": ["Bronchial Asthma"],
                "common_symptoms": [
                    "Wheezing (whistling sound when breathing)",
                    "Shortness of breath",
                    "Chest tightness",
                    "Coughing, especially at night",
                ],
                "causes": [
                    "Genetic factors",
                    "Environmental triggers",
                    "Allergens (dust, pollen, pets)",
                    "Respiratory infections",
                ],
                "risk_factors": [
                    "Family history of asthma or allergies",
                    "Having allergies",
                    "Smoking or exposure to secondhand smoke",
                    "Air pollution",
                    "Obesity",
                ],
            },
            "copd": {
                "simple_explanation": "COPD (Chronic Obstructive Pulmonary Disease) is lung damage that makes it hard to breathe. It gets worse over time. The most common types are emphysema and chronic bronchitis.",
                "alternate_names": ["Chronic Obstructive Pulmonary Disease", "Emphysema", "Chronic Bronchitis"],
                "common_symptoms": [
                    "Chronic cough",
                    "Shortness of breath during daily activities",
                    "Wheezing",
                    "Chest tightness",
                    "Mucus production",
                    "Frequent respiratory infections",
                ],
                "causes": [
                    "Smoking (most common cause)",
                    "Long-term exposure to lung irritants",
                    "Air pollution",
                    "Workplace dust and chemicals",
                ],
                "risk_factors": [
                    "Smoking",
                    "Age (usually develops after age 40)",
                    "Genetics (rare)",
                    "Exposure to secondhand smoke",
                ],
            },
        }

    def generate_from_condition_name(
        self,
        condition_name: str,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> ConditionExplainer:
        """
        Generate condition explainer from condition name.

        Args:
            condition_name: Name of medical condition
            reading_level: Target reading level
            language: Language code

        Returns:
            Complete condition explainer
        """
        # Normalize condition name
        condition_key = condition_name.lower().strip()

        # Get from library if available
        if condition_key in self.condition_library:
            template = self.condition_library[condition_key]

            explainer = ConditionExplainer(
                condition_name=condition_name.title(),
                simple_explanation=template["simple_explanation"],
                alternate_names=template.get("alternate_names", []),
                common_symptoms=template.get("common_symptoms", []),
                causes=template.get("causes", []),
                risk_factors=template.get("risk_factors", []),
                reading_level=reading_level,
                language=language,
            )

            # Add standard sections
            explainer.how_diagnosed = self._generate_diagnostic_info(condition_name)
            explainer.treatment_options = self._generate_treatment_options(condition_name)
            explainer.lifestyle_changes = self._generate_lifestyle_changes(condition_name)
            explainer.warning_signs = self._generate_warning_signs(condition_name)
            explainer.self_care = self._generate_self_care(condition_name)
            explainer.dos_donts = self._generate_dos_donts(condition_name)
            explainer.frequently_asked_questions = self._generate_faqs(condition_name)

        else:
            # Generate generic explainer
            explainer = self._generate_generic_explainer(
                condition_name, reading_level, language
            )

        return explainer

    def generate_from_text(
        self,
        text: str,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> ConditionExplainer:
        """
        Generate condition explainer from free text.

        Args:
            text: Text about condition
            reading_level: Target reading level
            language: Language code

        Returns:
            Condition explainer
        """
        # Extract condition name from text
        # This is simplified; in production, use NER
        condition_name = self._extract_condition_name(text)

        # Try to generate from library first
        explainer = self.generate_from_condition_name(
            condition_name, reading_level, language
        )

        # Override with text-extracted information if available
        if "causes" in text.lower():
            causes = self._extract_list_from_text(text, "causes")
            if causes:
                explainer.causes = causes

        if "symptom" in text.lower():
            symptoms = self._extract_list_from_text(text, "symptom")
            if symptoms:
                explainer.common_symptoms = symptoms

        if "treatment" in text.lower():
            treatments = self._extract_list_from_text(text, "treatment")
            if treatments:
                explainer.treatment_options = treatments

        return explainer

    def _generate_diagnostic_info(self, condition_name: str) -> List[str]:
        """Generate how-it's-diagnosed information."""
        condition_lower = condition_name.lower()

        diagnostics = {
            "diabetes": [
                "Fasting blood sugar test",
                "HbA1c (average blood sugar over 3 months)",
                "Random blood sugar test",
                "Oral glucose tolerance test",
            ],
            "hypertension": [
                "Blood pressure measurement",
                "Multiple readings over time",
                "24-hour blood pressure monitoring (sometimes)",
                "Blood tests to check for causes",
            ],
            "asthma": [
                "Breathing tests (spirometry)",
                "Peak flow meter",
                "Chest X-ray",
                "Allergy testing",
            ],
            "copd": [
                "Breathing tests (spirometry)",
                "Chest X-ray",
                "CT scan",
                "Blood oxygen level test",
            ],
        }

        for key, tests in diagnostics.items():
            if key in condition_lower:
                return tests

        return [
            "Physical examination",
            "Medical history review",
            "Lab tests as needed",
            "Imaging studies if required",
        ]

    def _generate_treatment_options(self, condition_name: str) -> List[str]:
        """Generate treatment options."""
        condition_lower = condition_name.lower()

        treatments = {
            "diabetes": [
                "Lifestyle changes (diet and exercise)",
                "Blood sugar monitoring",
                "Oral medications (pills)",
                "Insulin injections (for some patients)",
                "Regular check-ups",
            ],
            "hypertension": [
                "Lifestyle changes (diet, exercise, weight loss)",
                "Reduce salt intake",
                "Blood pressure medications",
                "Regular blood pressure monitoring",
                "Stress management",
            ],
            "asthma": [
                "Quick-relief inhaler for symptoms",
                "Long-term control medications",
                "Avoiding triggers",
                "Allergy medications if needed",
                "Action plan for flare-ups",
            ],
            "copd": [
                "Stop smoking (most important)",
                "Bronchodilator medications",
                "Inhaled steroids",
                "Pulmonary rehabilitation",
                "Oxygen therapy (for severe cases)",
            ],
        }

        for key, options in treatments.items():
            if key in condition_lower:
                return options

        return [
            "Medications as prescribed",
            "Lifestyle modifications",
            "Regular monitoring",
            "Follow-up appointments",
        ]

    def _generate_lifestyle_changes(self, condition_name: str) -> List[str]:
        """Generate lifestyle change recommendations."""
        condition_lower = condition_name.lower()

        changes = {
            "diabetes": [
                "Eat healthy foods (vegetables, whole grains, lean protein)",
                "Limit sugar and refined carbohydrates",
                "Exercise regularly (30 minutes most days)",
                "Maintain healthy weight",
                "Monitor blood sugar as directed",
                "Take medications as prescribed",
            ],
            "hypertension": [
                "Reduce salt in diet",
                "Eat more fruits and vegetables",
                "Exercise regularly",
                "Lose weight if overweight",
                "Limit alcohol",
                "Quit smoking",
                "Manage stress",
            ],
            "asthma": [
                "Identify and avoid triggers",
                "Don't smoke and avoid secondhand smoke",
                "Exercise regularly (with proper warm-up)",
                "Get vaccinated (flu, pneumonia)",
                "Keep home clean and dust-free",
            ],
            "copd": [
                "Quit smoking immediately",
                "Avoid air pollution and irritants",
                "Exercise as tolerated",
                "Eat nutritious foods",
                "Practice breathing exercises",
                "Get vaccinated",
            ],
        }

        for key, recommendations in changes.items():
            if key in condition_lower:
                return recommendations

        return [
            "Follow a healthy diet",
            "Stay physically active",
            "Get adequate sleep",
            "Manage stress",
            "Avoid harmful substances",
        ]

    def _generate_warning_signs(self, condition_name: str) -> List[WarningSign]:
        """Generate when-to-seek-help warning signs."""
        condition_lower = condition_name.lower()

        warnings = {
            "diabetes": [
                WarningSign(
                    symptom="Blood sugar very high (over 300 mg/dL) or very low (under 70 mg/dL)",
                    action="Call your doctor or go to emergency room",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Confusion, excessive drowsiness",
                    action="Go to emergency room immediately",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Fruity-smelling breath, rapid breathing",
                    action="Go to emergency room immediately",
                    urgency=SeverityLevel.EMERGENCY,
                ),
            ],
            "hypertension": [
                WarningSign(
                    symptom="Severe headache",
                    action="Seek immediate medical attention",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Chest pain",
                    action="Call emergency services",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Difficulty speaking or moving",
                    action="Call emergency services",
                    urgency=SeverityLevel.EMERGENCY,
                ),
            ],
            "asthma": [
                WarningSign(
                    symptom="Severe difficulty breathing",
                    action="Use quick-relief inhaler and call emergency services",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Blue lips or fingernails",
                    action="Call emergency services immediately",
                    urgency=SeverityLevel.EMERGENCY,
                ),
                WarningSign(
                    symptom="Quick-relief inhaler not helping",
                    action="Seek immediate medical attention",
                    urgency=SeverityLevel.EMERGENCY,
                ),
            ],
        }

        for key, signs in warnings.items():
            if key in condition_lower:
                return signs

        return [
            WarningSign(
                symptom="Symptoms getting worse despite treatment",
                action="Contact your doctor",
                urgency=SeverityLevel.MODERATE,
            ),
            WarningSign(
                symptom="New or unusual symptoms",
                action="Contact your doctor",
                urgency=SeverityLevel.MODERATE,
            ),
        ]

    def _generate_self_care(self, condition_name: str) -> List[str]:
        """Generate self-care recommendations."""
        return [
            "Take medications exactly as prescribed",
            "Keep all follow-up appointments",
            "Monitor your symptoms",
            "Keep a health diary",
            "Learn about your condition",
            "Join a support group if helpful",
        ]

    def _generate_dos_donts(self, condition_name: str) -> DosDonts:
        """Generate do's and don'ts."""
        condition_lower = condition_name.lower()

        dos_donts_map = {
            "diabetes": DosDonts(
                dos=[
                    "Check your blood sugar as directed",
                    "Take medications on time",
                    "Eat regular, balanced meals",
                    "Exercise regularly",
                    "Check your feet daily for cuts or sores",
                ],
                donts=[
                    "Skip medications",
                    "Ignore low blood sugar symptoms",
                    "Eat large amounts of sweets",
                    "Skip meals",
                    "Ignore foot problems",
                ],
            ),
            "hypertension": DosDonts(
                dos=[
                    "Take blood pressure medications daily",
                    "Check blood pressure at home if advised",
                    "Reduce salt in your diet",
                    "Stay active",
                    "Manage stress",
                ],
                donts=[
                    "Stop medications without consulting doctor",
                    "Eat processed or salty foods",
                    "Smoke",
                    "Drink excessive alcohol",
                    "Ignore symptoms",
                ],
            ),
        }

        for key, dos_donts in dos_donts_map.items():
            if key in condition_lower:
                return dos_donts

        return DosDonts(
            dos=[
                "Follow your treatment plan",
                "Stay in touch with your healthcare team",
                "Make healthy lifestyle choices",
            ],
            donts=[
                "Ignore symptoms",
                "Skip medications",
                "Avoid doctor appointments",
            ],
        )

    def _generate_faqs(self, condition_name: str) -> List[Dict[str, str]]:
        """Generate frequently asked questions."""
        condition_lower = condition_name.lower()

        faqs = {
            "diabetes": [
                {
                    "question": "Can diabetes be cured?",
                    "answer": "Type 1 diabetes cannot be cured but can be managed well. Type 2 diabetes can sometimes be reversed with significant lifestyle changes and weight loss, but most people need ongoing management.",
                },
                {
                    "question": "How often should I check my blood sugar?",
                    "answer": "This depends on your treatment plan. Your doctor will tell you how often to check. It may be several times a day if you use insulin, or less often if you take pills only.",
                },
                {
                    "question": "Can I eat sugar if I have diabetes?",
                    "answer": "You can have small amounts of sugar occasionally as part of a balanced meal plan. The key is moderation and counting it as part of your carbohydrates.",
                },
            ],
            "hypertension": [
                {
                    "question": "Will I always need blood pressure medication?",
                    "answer": "Many people need lifelong treatment. However, significant lifestyle changes (weight loss, exercise, diet) may allow some people to reduce or stop medication under doctor supervision.",
                },
                {
                    "question": "Can stress cause high blood pressure?",
                    "answer": "Stress can temporarily raise blood pressure. Long-term stress may contribute to high blood pressure along with other factors.",
                },
            ],
        }

        for key, questions in faqs.items():
            if key in condition_lower:
                return questions

        return [
            {
                "question": "Is this condition serious?",
                "answer": "Any medical condition should be taken seriously. With proper treatment and management, most conditions can be controlled effectively.",
            },
            {
                "question": "When will I feel better?",
                "answer": "This varies by condition and treatment. Some people feel better within days, while others may take weeks or months. Talk to your doctor about what to expect.",
            },
        ]

    def _generate_generic_explainer(
        self, condition_name: str, reading_level: ReadingLevel, language: str
    ) -> ConditionExplainer:
        """Generate generic explainer for unknown condition."""
        return ConditionExplainer(
            condition_name=condition_name,
            simple_explanation=f"{condition_name} is a medical condition. Your doctor can explain more about what this means for you.",
            reading_level=reading_level,
            language=language,
            how_diagnosed=[
                "Medical examination",
                "Tests as recommended by your doctor",
            ],
            treatment_options=[
                "Treatment as prescribed by your doctor",
                "Regular follow-up appointments",
            ],
            lifestyle_changes=[
                "Follow your doctor's recommendations",
                "Maintain a healthy lifestyle",
            ],
        )

    def _extract_condition_name(self, text: str) -> str:
        """Extract condition name from text."""
        # Look for capitalized medical terms
        # This is simplified; in production, use medical NER
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in self.condition_library:
                return word

        # Fallback to first meaningful capitalized phrase
        return text.split(".")[0].strip()[:50]

    def _extract_list_from_text(self, text: str, keyword: str) -> List[str]:
        """Extract bullet points or lists from text."""
        # Simple extraction looking for list patterns
        # In production, use proper NLP
        items = []

        # Look for bullets or numbered lists
        lines = text.split("\n")
        in_list = False

        for line in lines:
            if keyword.lower() in line.lower():
                in_list = True
                continue

            if in_list:
                # Check for list markers
                line = line.strip()
                if line.startswith(("•", "-", "*", "·")) or (line and line[0].isdigit() and line[1] in ".):"):
                    # Remove marker
                    item = line.lstrip("•-*·0123456789.): ").strip()
                    if item:
                        items.append(item)
                elif not line:
                    # Empty line might end list
                    if items:
                        break
                else:
                    # No marker but might be continuation
                    if items:
                        break

        return items
