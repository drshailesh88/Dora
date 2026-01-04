"""
Pre-built Patient Education Templates

Common templates for frequently needed educational materials.
"""

from typing import Dict, List
from .models import (
    EducationTemplate,
    ContentType,
    MedicationGuide,
    ConditionExplainer,
    DietPlan,
    LifestyleGuide,
    DosDonts,
    SideEffect,
    WarningSign,
    SeverityLevel,
    DosageInstruction,
)


class TemplateLibrary:
    """Library of pre-built education templates."""

    def __init__(self):
        """Initialize template library."""
        self.templates: Dict[str, EducationTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all templates."""
        # Diabetes templates
        self.templates["diabetes_management"] = self._create_diabetes_management_template()
        self.templates["diabetes_diet"] = self._create_diabetes_diet_template()

        # Hypertension templates
        self.templates["hypertension_management"] = self._create_hypertension_management_template()
        self.templates["hypertension_diet"] = self._create_hypertension_diet_template()

        # Medication adherence
        self.templates["medication_adherence"] = self._create_medication_adherence_template()

        # Post-surgery care
        self.templates["post_surgery_care"] = self._create_post_surgery_care_template()

        # Pregnancy care
        self.templates["pregnancy_first_trimester"] = self._create_pregnancy_first_trimester_template()

        # Child vaccination
        self.templates["child_vaccination"] = self._create_child_vaccination_template()

        # Diet plans
        self.templates["cardiac_diet"] = self._create_cardiac_diet_template()
        self.templates["renal_diet"] = self._create_renal_diet_template()

    def _create_diabetes_management_template(self) -> EducationTemplate:
        """Create diabetes management template."""
        template_data = {
            "title": "Living with Diabetes",
            "sections": [
                {
                    "heading": "Understanding Diabetes",
                    "content": "Diabetes means your blood sugar is too high. Managing it well helps prevent complications.",
                },
                {
                    "heading": "Daily Care",
                    "items": [
                        "Check blood sugar as directed",
                        "Take medications on time",
                        "Eat healthy, balanced meals",
                        "Exercise regularly",
                        "Check feet daily",
                    ],
                },
                {
                    "heading": "Target Blood Sugar",
                    "content": "Before meals: 80-130 mg/dL\nAfter meals: Less than 180 mg/dL\nHbA1c: Less than 7%",
                },
                {
                    "heading": "Warning Signs",
                    "items": [
                        "Very high blood sugar (over 300)",
                        "Very low blood sugar (under 70)",
                        "Confusion or dizziness",
                        "Unusual sweating",
                    ],
                },
            ],
            "dos": [
                "Eat regular meals",
                "Stay active",
                "Monitor blood sugar",
                "Take care of feet",
                "Attend follow-up appointments",
            ],
            "donts": [
                "Skip medications",
                "Ignore symptoms",
                "Eat excessive sweets",
                "Skip meals",
                "Go barefoot",
            ],
        }

        return EducationTemplate(
            id="diabetes_management",
            name="Diabetes Management Guide",
            content_type=ContentType.LIFESTYLE_GUIDE,
            description="Comprehensive diabetes self-care guide",
            template_data=template_data,
            required_fields=["patient_name"],
            languages=["en", "hi", "ta", "te"],
        )

    def _create_diabetes_diet_template(self) -> EducationTemplate:
        """Create diabetes diet plan template."""
        template_data = {
            "title": "Diabetic Diet Plan",
            "foods_to_eat": [
                "Vegetables (spinach, broccoli, carrots)",
                "Whole grains (brown rice, whole wheat)",
                "Lean proteins (chicken, fish, beans)",
                "Low-fat dairy",
                "Nuts and seeds (in moderation)",
            ],
            "foods_to_limit": [
                "White rice and white bread",
                "Sugary drinks",
                "Fried foods",
                "Processed snacks",
            ],
            "foods_to_avoid": [
                "Sugar-sweetened beverages",
                "Candy and sweets",
                "High-sugar desserts",
                "Excessive fruit juices",
            ],
            "meal_plan": {
                "Breakfast": ["Oats with vegetables", "Egg white omelet", "Low-fat milk"],
                "Mid-morning": ["Apple or orange", "Handful of nuts"],
                "Lunch": ["2 rotis with dal", "Vegetable curry", "Salad"],
                "Evening": ["Tea without sugar", "Roasted chickpeas"],
                "Dinner": ["1 roti with vegetable", "Grilled fish/chicken", "Soup"],
            },
        }

        return EducationTemplate(
            id="diabetes_diet",
            name="Diabetic Diet Plan",
            content_type=ContentType.DIET_PLAN,
            description="Meal plan for diabetes management",
            template_data=template_data,
            required_fields=[],
            languages=["en", "hi"],
        )

    def _create_hypertension_management_template(self) -> EducationTemplate:
        """Create hypertension management template."""
        template_data = {
            "title": "Managing High Blood Pressure",
            "target_bp": "Less than 140/90 mmHg (or as advised by doctor)",
            "lifestyle_changes": [
                "Reduce salt intake (less than 5g per day)",
                "Exercise 30 minutes daily",
                "Lose weight if overweight",
                "Limit alcohol",
                "Quit smoking",
                "Manage stress",
                "Get adequate sleep",
            ],
            "dos": [
                "Take medications daily",
                "Check BP regularly",
                "Eat more fruits and vegetables",
                "Stay active",
                "Reduce stress",
            ],
            "donts": [
                "Add extra salt to food",
                "Skip blood pressure medications",
                "Smoke",
                "Drink excessive alcohol",
                "Ignore symptoms",
            ],
            "when_to_seek_help": [
                "BP over 180/120",
                "Severe headache",
                "Chest pain",
                "Difficulty breathing",
                "Visual changes",
            ],
        }

        return EducationTemplate(
            id="hypertension_management",
            name="Hypertension Management",
            content_type=ContentType.LIFESTYLE_GUIDE,
            description="Blood pressure control guide",
            template_data=template_data,
            required_fields=[],
        )

    def _create_hypertension_diet_template(self) -> EducationTemplate:
        """Create hypertension diet template (DASH diet)."""
        template_data = {
            "title": "DASH Diet for High Blood Pressure",
            "description": "Dietary Approaches to Stop Hypertension",
            "foods_to_eat": [
                "Vegetables and fruits",
                "Whole grains",
                "Low-fat dairy",
                "Lean meats, fish, poultry",
                "Nuts, seeds, legumes",
            ],
            "foods_to_limit": [
                "Salt and sodium",
                "Red meat",
                "Sweets and sugary drinks",
            ],
            "foods_to_avoid": [
                "Processed foods",
                "Pickles and papad",
                "Chips and namkeen",
                "Canned soups",
                "Fast food",
            ],
            "tips": [
                "Read food labels for sodium content",
                "Cook without added salt",
                "Use herbs and spices for flavor",
                "Avoid table salt",
                "Rinse canned foods before eating",
            ],
        }

        return EducationTemplate(
            id="hypertension_diet",
            name="DASH Diet Plan",
            content_type=ContentType.DIET_PLAN,
            description="Heart-healthy low-sodium diet",
            template_data=template_data,
            required_fields=[],
        )

    def _create_medication_adherence_template(self) -> EducationTemplate:
        """Create medication adherence template."""
        template_data = {
            "title": "Taking Your Medications Correctly",
            "why_important": "Taking medications as prescribed helps them work properly and prevents complications.",
            "tips": [
                "Set daily alarms as reminders",
                "Use a pill organizer",
                "Keep medications visible",
                "Link taking meds to daily routine (e.g., brushing teeth)",
                "Keep a medication diary",
                "Get refills before running out",
            ],
            "barriers": {
                "Forgetting": "Use alarms, pill organizers, or mobile apps",
                "Side effects": "Talk to doctor about alternatives",
                "Cost": "Ask about generic options or assistance programs",
                "Too many pills": "Ask doctor about combination medications",
            },
            "dos": [
                "Take medications at same time daily",
                "Store medications properly",
                "Tell doctor about all medications",
                "Bring medication list to appointments",
            ],
            "donts": [
                "Stop medications without consulting doctor",
                "Share medications with others",
                "Take expired medications",
                "Double dose if you forget one",
            ],
        }

        return EducationTemplate(
            id="medication_adherence",
            name="Medication Adherence Guide",
            content_type=ContentType.GENERAL_HANDOUT,
            description="Tips for taking medications correctly",
            template_data=template_data,
            required_fields=[],
        )

    def _create_post_surgery_care_template(self) -> EducationTemplate:
        """Create post-surgery care template."""
        template_data = {
            "title": "After Your Surgery - Care Instructions",
            "wound_care": [
                "Keep wound clean and dry",
                "Change dressing as instructed",
                "Wash hands before touching wound",
                "Watch for infection signs",
            ],
            "pain_management": [
                "Take pain medications as prescribed",
                "Don't wait for pain to become severe",
                "Use ice packs if advised",
                "Rest and elevate affected area",
            ],
            "activity": [
                "No heavy lifting for 2 weeks",
                "Walk short distances regularly",
                "Avoid strenuous activity",
                "Resume activities gradually",
            ],
            "diet": [
                "Start with light, easy-to-digest foods",
                "Drink plenty of fluids",
                "Avoid spicy and fatty foods initially",
            ],
            "warning_signs": [
                "Fever over 101°F",
                "Increasing pain or swelling",
                "Redness or warmth at incision",
                "Pus or bad-smelling drainage",
                "Bleeding that won't stop",
            ],
            "follow_up": "See your doctor in 1-2 weeks for wound check",
        }

        return EducationTemplate(
            id="post_surgery_care",
            name="Post-Surgery Care Instructions",
            content_type=ContentType.POST_CARE_GUIDE,
            description="General post-operative care guide",
            template_data=template_data,
            required_fields=["procedure_name", "surgery_date"],
        )

    def _create_pregnancy_first_trimester_template(self) -> EducationTemplate:
        """Create first trimester pregnancy care template."""
        template_data = {
            "title": "First Trimester Care (Weeks 1-12)",
            "what_to_expect": [
                "Morning sickness",
                "Fatigue",
                "Breast tenderness",
                "Frequent urination",
                "Mood changes",
            ],
            "dos": [
                "Take prenatal vitamins daily",
                "Eat small, frequent meals",
                "Stay hydrated",
                "Get adequate rest",
                "Attend all prenatal appointments",
                "Exercise moderately (walking, swimming)",
            ],
            "donts": [
                "Smoke or drink alcohol",
                "Take unprescribed medications",
                "Eat raw or undercooked meat",
                "Change cat litter",
                "Consume excessive caffeine",
                "Use hot tubs or saunas",
            ],
            "nutrition": [
                "Folic acid rich foods (leafy greens, legumes)",
                "Iron-rich foods (lean meat, beans)",
                "Calcium sources (milk, yogurt)",
                "Avoid raw fish and unpasteurized cheese",
            ],
            "when_to_call_doctor": [
                "Vaginal bleeding",
                "Severe abdominal pain",
                "Severe vomiting",
                "Fever",
                "Severe headache",
            ],
        }

        return EducationTemplate(
            id="pregnancy_first_trimester",
            name="First Trimester Pregnancy Care",
            content_type=ContentType.GENERAL_HANDOUT,
            description="Care guide for first 12 weeks of pregnancy",
            template_data=template_data,
            required_fields=["patient_name", "due_date"],
        )

    def _create_child_vaccination_template(self) -> EducationTemplate:
        """Create child vaccination information template."""
        template_data = {
            "title": "Child Vaccination Schedule",
            "why_important": "Vaccines protect your child from serious diseases. Following the schedule ensures best protection.",
            "schedule": {
                "Birth": "BCG, Hepatitis B (1st dose), OPV (0 dose)",
                "6 weeks": "DPT 1, Hib 1, IPV 1, Hep B 2, Rota 1, PCV 1",
                "10 weeks": "DPT 2, Hib 2, IPV 2, Rota 2, PCV 2",
                "14 weeks": "DPT 3, Hib 3, IPV 3, Rota 3, PCV 3",
                "9 months": "Measles 1",
                "12 months": "Hepatitis A 1",
                "15 months": "MMR 1, PCV Booster",
                "16-18 months": "DPT Booster 1, Hib Booster, IPV Booster",
            },
            "after_vaccination": [
                "Child may have mild fever",
                "Give paracetamol if needed",
                "Keep injection site clean",
                "Watch for allergic reactions (rare)",
            ],
            "when_to_seek_help": [
                "High fever (over 103°F)",
                "Difficulty breathing",
                "Severe swelling",
                "Excessive crying for hours",
            ],
        }

        return EducationTemplate(
            id="child_vaccination",
            name="Child Vaccination Schedule",
            content_type=ContentType.GENERAL_HANDOUT,
            description="Vaccination schedule and information for parents",
            template_data=template_data,
            required_fields=["child_name", "date_of_birth"],
        )

    def _create_cardiac_diet_template(self) -> EducationTemplate:
        """Create cardiac/heart-healthy diet template."""
        template_data = {
            "title": "Heart-Healthy Diet Plan",
            "goals": [
                "Lower cholesterol",
                "Reduce blood pressure",
                "Maintain healthy weight",
                "Improve heart health",
            ],
            "foods_to_eat": [
                "Whole grains (oats, brown rice)",
                "Fruits and vegetables",
                "Fish rich in omega-3 (salmon, mackerel)",
                "Nuts and seeds",
                "Olive oil",
                "Low-fat dairy",
            ],
            "foods_to_limit": [
                "Salt and sodium",
                "Saturated fats",
                "Red meat",
                "Full-fat dairy",
            ],
            "foods_to_avoid": [
                "Trans fats",
                "Fried foods",
                "Processed meats",
                "Sugary drinks",
                "Excessive sweets",
            ],
            "cooking_tips": [
                "Grill, bake, or steam instead of frying",
                "Use herbs instead of salt",
                "Choose lean cuts of meat",
                "Remove skin from poultry",
                "Use healthy oils (olive, canola)",
            ],
        }

        return EducationTemplate(
            id="cardiac_diet",
            name="Heart-Healthy Diet",
            content_type=ContentType.DIET_PLAN,
            description="Diet plan for heart health",
            template_data=template_data,
            required_fields=[],
        )

    def _create_renal_diet_template(self) -> EducationTemplate:
        """Create kidney-friendly diet template."""
        template_data = {
            "title": "Kidney-Friendly Diet Plan",
            "goals": [
                "Control protein intake",
                "Limit sodium",
                "Control potassium and phosphorus",
                "Maintain proper fluid balance",
            ],
            "protein": {
                "recommendation": "As per doctor's advice (usually 0.6-0.8 g/kg)",
                "good_sources": "Egg whites, fish, chicken breast",
            },
            "sodium": {
                "limit": "Less than 2000 mg per day",
                "avoid": "Processed foods, pickles, papad, canned soups",
            },
            "potassium": {
                "limit": "As per doctor's advice",
                "high_foods_to_limit": "Bananas, oranges, tomatoes, potatoes",
                "lower_alternatives": "Apples, grapes, cabbage, cauliflower",
            },
            "phosphorus": {
                "limit": "As per doctor's advice",
                "high_foods_to_limit": "Dairy, nuts, beans, cola drinks",
            },
            "fluids": "Monitor fluid intake as advised by doctor",
            "tips": [
                "Read food labels carefully",
                "Boil and drain vegetables to reduce potassium",
                "Avoid salt substitutes (contain potassium)",
                "Work with a dietitian",
            ],
        }

        return EducationTemplate(
            id="renal_diet",
            name="Kidney-Friendly Diet",
            content_type=ContentType.DIET_PLAN,
            description="Diet plan for kidney disease",
            template_data=template_data,
            required_fields=[],
        )

    def get_template(self, template_id: str) -> EducationTemplate:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Education template

        Raises:
            KeyError: If template not found
        """
        return self.templates[template_id]

    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available templates.

        Returns:
            List of template summaries
        """
        return [
            {
                "id": template.id,
                "name": template.name,
                "type": template.content_type.value,
                "description": template.description,
            }
            for template in self.templates.values()
        ]

    def get_templates_by_type(self, content_type: ContentType) -> List[EducationTemplate]:
        """
        Get all templates of a specific type.

        Args:
            content_type: Type of content

        Returns:
            List of matching templates
        """
        return [
            template
            for template in self.templates.values()
            if template.content_type == content_type
        ]


# Global template library instance
_template_library: TemplateLibrary = None


def get_template_library() -> TemplateLibrary:
    """
    Get global template library instance.

    Returns:
        Template library
    """
    global _template_library
    if _template_library is None:
        _template_library = TemplateLibrary()
    return _template_library
