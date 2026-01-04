"""Template Manager for Clinical Documentation.

Manages customizable templates for different document types and specialties.
"""

from enum import Enum
from typing import Any, Optional


class Specialty(str, Enum):
    """Medical specialties."""

    GENERAL_MEDICINE = "general_medicine"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"
    SURGERY = "surgery"
    OBSTETRICS = "obstetrics"
    PSYCHIATRY = "psychiatry"
    DERMATOLOGY = "dermatology"
    ENT = "ent"
    OPHTHALMOLOGY = "ophthalmology"
    EMERGENCY = "emergency"


class DocumentTemplate:
    """Base class for document templates."""

    def __init__(
        self,
        template_id: str,
        name: str,
        specialty: Specialty,
        sections: dict[str, Any],
        boilerplate: Optional[dict[str, str]] = None,
    ):
        """Initialize template.

        Args:
            template_id: Unique template ID
            name: Template name
            specialty: Medical specialty
            sections: Template sections configuration
            boilerplate: Boilerplate text for sections
        """
        self.template_id = template_id
        self.name = name
        self.specialty = specialty
        self.sections = sections
        self.boilerplate = boilerplate or {}

    def get_boilerplate(self, section: str) -> str:
        """Get boilerplate text for a section.

        Args:
            section: Section name

        Returns:
            Boilerplate text
        """
        return self.boilerplate.get(section, "")

    def render(self, data: dict[str, Any]) -> str:
        """Render template with data.

        Args:
            data: Data to fill template

        Returns:
            Rendered template
        """
        raise NotImplementedError("Subclasses must implement render()")


class SOAPTemplate(DocumentTemplate):
    """SOAP note template."""

    def __init__(
        self,
        template_id: str,
        name: str,
        specialty: Specialty,
        ros_sections: Optional[list[str]] = None,
        exam_sections: Optional[list[str]] = None,
        boilerplate: Optional[dict[str, str]] = None,
    ):
        """Initialize SOAP template.

        Args:
            template_id: Template ID
            name: Template name
            specialty: Specialty
            ros_sections: Review of systems sections to include
            exam_sections: Physical exam sections to include
            boilerplate: Boilerplate text
        """
        sections = {
            "ros_sections": ros_sections or self._default_ros_sections(),
            "exam_sections": exam_sections or self._default_exam_sections(),
        }
        super().__init__(template_id, name, specialty, sections, boilerplate)

    def _default_ros_sections(self) -> list[str]:
        """Get default ROS sections."""
        return [
            "Constitutional",
            "Cardiovascular",
            "Respiratory",
            "Gastrointestinal",
            "Genitourinary",
            "Musculoskeletal",
            "Neurological",
            "Psychiatric",
            "Skin",
            "Endocrine",
        ]

    def _default_exam_sections(self) -> list[str]:
        """Get default exam sections."""
        return [
            "General",
            "Cardiovascular",
            "Respiratory",
            "Abdomen",
            "Extremities",
            "Neurological",
        ]

    def render(self, data: dict[str, Any]) -> str:
        """Render SOAP note."""
        # This would be implemented based on specific formatting needs
        return "SOAP Note Template"


class TemplateManager:
    """Manage document templates."""

    def __init__(self):
        """Initialize template manager."""
        self.templates: dict[str, DocumentTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default templates for common specialties."""
        # General Medicine SOAP
        self.templates["general_soap"] = SOAPTemplate(
            template_id="general_soap",
            name="General Medicine SOAP Note",
            specialty=Specialty.GENERAL_MEDICINE,
            boilerplate={
                "social_history": "Non-smoker, social drinker",
                "family_history": "Non-contributory",
            },
        )

        # Cardiology SOAP
        self.templates["cardio_soap"] = SOAPTemplate(
            template_id="cardio_soap",
            name="Cardiology SOAP Note",
            specialty=Specialty.CARDIOLOGY,
            ros_sections=[
                "Cardiovascular",
                "Respiratory",
                "Constitutional",
            ],
            exam_sections=[
                "Cardiovascular",
                "Respiratory",
                "Extremities",
            ],
            boilerplate={
                "review_of_systems": "Cardiovascular: Chest pain, palpitations, SOB, orthopnea, PND, edema",
            },
        )

        # Pediatrics SOAP
        self.templates["peds_soap"] = SOAPTemplate(
            template_id="peds_soap",
            name="Pediatrics SOAP Note",
            specialty=Specialty.PEDIATRICS,
            exam_sections=[
                "General",
                "HEENT",
                "Cardiovascular",
                "Respiratory",
                "Abdomen",
                "Skin",
                "Neurological",
                "Development",
            ],
            boilerplate={
                "social_history": "Immunizations up to date. Attends school/daycare.",
            },
        )

        # Emergency SOAP
        self.templates["emergency_soap"] = SOAPTemplate(
            template_id="emergency_soap",
            name="Emergency Medicine SOAP Note",
            specialty=Specialty.EMERGENCY,
            boilerplate={
                "disposition": "Patient discharged in stable condition with appropriate follow-up instructions.",
            },
        )

    def get_template(self, template_id: str) -> Optional[DocumentTemplate]:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template or None
        """
        return self.templates.get(template_id)

    def get_templates_by_specialty(
        self, specialty: Specialty
    ) -> list[DocumentTemplate]:
        """Get all templates for a specialty.

        Args:
            specialty: Medical specialty

        Returns:
            List of templates
        """
        return [
            template
            for template in self.templates.values()
            if template.specialty == specialty
        ]

    def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates.

        Returns:
            List of template metadata
        """
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "specialty": template.specialty.value,
            }
            for template in self.templates.values()
        ]

    def add_custom_template(self, template: DocumentTemplate):
        """Add a custom template.

        Args:
            template: Document template
        """
        self.templates[template.template_id] = template

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted, False if not found
        """
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False


# Boilerplate text library
BOILERPLATE_LIBRARY = {
    # Review of Systems
    "ros_negative": {
        "constitutional": "No fever, chills, night sweats, or unintentional weight loss.",
        "cardiovascular": "No chest pain, palpitations, orthopnea, PND, or lower extremity edema.",
        "respiratory": "No cough, shortness of breath, wheezing, or hemoptysis.",
        "gastrointestinal": "No nausea, vomiting, diarrhea, constipation, or abdominal pain.",
        "genitourinary": "No dysuria, hematuria, frequency, or urgency.",
        "musculoskeletal": "No joint pain, swelling, or muscle weakness.",
        "neurological": "No headache, dizziness, syncope, or focal weakness.",
        "psychiatric": "No depression, anxiety, or sleep disturbances.",
        "skin": "No rash, lesions, or pruritus.",
        "endocrine": "No polyuria, polydipsia, or heat/cold intolerance.",
    },
    # Physical Exam
    "exam_normal": {
        "general": "Alert, oriented, no acute distress.",
        "cardiovascular": "Regular rate and rhythm, S1S2 normal, no murmurs, rubs, or gallops.",
        "respiratory": "Clear to auscultation bilaterally, no wheezes, rales, or rhonchi.",
        "abdomen": "Soft, non-tender, non-distended, normal bowel sounds, no organomegaly.",
        "extremities": "No clubbing, cyanosis, or edema. Pulses 2+ bilaterally.",
        "neurological": "Alert and oriented x3. Cranial nerves II-XII intact. Motor strength 5/5 throughout. Sensation intact.",
        "skin": "Warm, dry, no rashes or lesions.",
    },
    # Social History
    "social": {
        "non_smoker": "Non-smoker",
        "former_smoker": "Former smoker, quit [date]",
        "current_smoker": "Current smoker, [X] pack-years",
        "alcohol_none": "No alcohol use",
        "alcohol_social": "Social drinker",
        "alcohol_moderate": "Moderate alcohol use",
        "drugs_none": "No illicit drug use",
    },
    # Family History
    "family": {
        "non_contributory": "Family history non-contributory for the present illness.",
        "cardiac": "Family history significant for cardiac disease.",
        "diabetes": "Family history significant for diabetes mellitus.",
        "cancer": "Family history significant for cancer.",
    },
    # Discharge Instructions
    "discharge": {
        "follow_up": "Follow up with primary care physician in 1 week or as directed.",
        "return_if": "Return to emergency department if symptoms worsen or new concerning symptoms develop.",
        "activity": "Resume normal activities as tolerated.",
        "diet": "Resume regular diet.",
    },
}


def get_boilerplate(category: str, key: str) -> str:
    """Get boilerplate text.

    Args:
        category: Category (ros_negative, exam_normal, etc.)
        key: Specific key

    Returns:
        Boilerplate text or empty string
    """
    return BOILERPLATE_LIBRARY.get(category, {}).get(key, "")
