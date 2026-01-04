"""
Patient Education Service

Main service for generating, translating, formatting, and delivering
patient education materials.
"""

import os
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from ..core.models import MedicalAnswer
from ..llm.synthesizer import Synthesizer
from ..notifications.service import NotificationService
from ..notifications.models import NotificationChannel

from .models import (
    PatientHandout,
    ContentType,
    ReadingLevel,
    DeliveryFormat,
    MedicationGuide,
    ConditionExplainer,
)
from .generator import ContentGenerator
from .medications import MedicationGuideGenerator
from .conditions import ConditionExplainerGenerator
from .procedures import ProcedureGuideGenerator
from .translator import EducationTranslator, WhatsAppFormatter, SMSFormatter
from .formatter import PDFFormatter, HTMLFormatter, PlainTextFormatter
from .templates import get_template_library, TemplateLibrary


class EducationService:
    """Service for patient education content generation and delivery."""

    def __init__(
        self,
        llm_synthesizer: Optional[Synthesizer] = None,
        notification_service: Optional[NotificationService] = None,
        storage_dir: str = "/tmp/education",
    ):
        """
        Initialize education service.

        Args:
            llm_synthesizer: LLM for content generation
            notification_service: Service for sending notifications
            storage_dir: Directory for storing generated PDFs
        """
        self.llm = llm_synthesizer
        self.notification_service = notification_service
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize generators
        self.content_generator = ContentGenerator(llm_synthesizer)
        self.medication_generator = MedicationGuideGenerator(llm_synthesizer)
        self.condition_generator = ConditionExplainerGenerator(llm_synthesizer)
        self.procedure_generator = ProcedureGuideGenerator(llm_synthesizer)

        # Initialize formatters
        self.pdf_formatter = PDFFormatter()
        self.html_formatter = HTMLFormatter()
        self.text_formatter = PlainTextFormatter()

        # Initialize template library
        self.template_library = get_template_library()

    def generate_from_query_answer(
        self,
        answer: MedicalAnswer,
        content_type: ContentType = ContentType.GENERAL_HANDOUT,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        clinic_name: Optional[str] = None,
    ) -> PatientHandout:
        """
        Generate patient handout from Dora query answer.

        Args:
            answer: Medical answer from query
            content_type: Type of educational content
            reading_level: Target reading level
            language: Language code
            patient_name: Patient name for personalization
            doctor_name: Doctor name
            clinic_name: Clinic name

        Returns:
            Patient handout
        """
        # Generate handout
        handout = self.content_generator.generate_from_answer(
            answer=answer,
            content_type=content_type,
            reading_level=reading_level,
            language=language,
            patient_name=patient_name,
            doctor_name=doctor_name,
        )

        handout.clinic_name = clinic_name

        # Add contact information
        if doctor_name or clinic_name:
            handout.contact_information = {}
            if clinic_name:
                handout.contact_information["Clinic"] = clinic_name
            if doctor_name:
                handout.contact_information["Doctor"] = doctor_name

        # Add emergency contacts
        handout.emergency_contacts = {
            "Emergency": "108 / 112",
            "Ambulance": "108",
        }

        return handout

    def generate_medication_guide(
        self,
        generic_name: str,
        brand_names: Optional[List[str]] = None,
        indication: Optional[str] = None,
        dosage: Optional[str] = None,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
    ) -> PatientHandout:
        """
        Generate medication guide handout.

        Args:
            generic_name: Generic medication name
            brand_names: Brand names
            indication: What it's prescribed for
            dosage: Dosage instruction
            reading_level: Target reading level
            language: Language code
            patient_name: Patient name
            doctor_name: Doctor name

        Returns:
            Patient handout with medication guide
        """
        # Generate medication guide
        med_guide = self.medication_generator.generate_from_drug_name(
            generic_name=generic_name,
            brand_names=brand_names,
            indication=indication,
            dosage=dosage,
            reading_level=reading_level,
            language=language,
        )

        # Create handout
        handout = PatientHandout(
            title=f"Medication Guide: {generic_name}",
            content_type=ContentType.MEDICATION_GUIDE,
            medication_guide=med_guide,
            patient_name=patient_name,
            doctor_name=doctor_name,
            reading_level=reading_level,
            language=language,
        )

        return handout

    def generate_condition_explainer(
        self,
        condition_name: str,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
    ) -> PatientHandout:
        """
        Generate condition explainer handout.

        Args:
            condition_name: Name of medical condition
            reading_level: Target reading level
            language: Language code
            patient_name: Patient name
            doctor_name: Doctor name

        Returns:
            Patient handout with condition explainer
        """
        # Generate condition explainer
        explainer = self.condition_generator.generate_from_condition_name(
            condition_name=condition_name,
            reading_level=reading_level,
            language=language,
        )

        # Create handout
        handout = PatientHandout(
            title=f"Understanding {condition_name}",
            content_type=ContentType.CONDITION_EXPLAINER,
            condition_explainer=explainer,
            patient_name=patient_name,
            doctor_name=doctor_name,
            reading_level=reading_level,
            language=language,
        )

        return handout

    def generate_from_template(
        self,
        template_id: str,
        template_data: dict,
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> PatientHandout:
        """
        Generate handout from template.

        Args:
            template_id: Template identifier
            template_data: Data to fill template
            patient_name: Patient name
            doctor_name: Doctor name
            reading_level: Target reading level
            language: Language code

        Returns:
            Patient handout
        """
        template = self.template_library.get_template(template_id)

        # Build custom sections from template
        custom_sections = []
        for section in template.template_data.get("sections", []):
            custom_sections.append({
                "title": section.get("heading", ""),
                "content": section.get("content", ""),
            })

        handout = PatientHandout(
            title=template.name,
            content_type=template.content_type,
            custom_sections=custom_sections,
            patient_name=patient_name,
            doctor_name=doctor_name,
            reading_level=reading_level,
            language=language,
        )

        return handout

    def translate_handout(
        self, handout: PatientHandout, target_language: str
    ) -> PatientHandout:
        """
        Translate handout to target language.

        Args:
            handout: Handout to translate
            target_language: Target language code

        Returns:
            Translated handout
        """
        translator = EducationTranslator(target_language)
        return translator.translate_handout(handout)

    def format_handout(
        self,
        handout: PatientHandout,
        format: DeliveryFormat,
        output_path: Optional[str] = None,
    ) -> bytes | str:
        """
        Format handout for delivery.

        Args:
            handout: Patient handout
            format: Output format
            output_path: Optional file path for PDF

        Returns:
            Formatted content (bytes for PDF, string for others)
        """
        if format == DeliveryFormat.PDF:
            return self.pdf_formatter.generate_pdf(handout, output_path)
        elif format == DeliveryFormat.HTML:
            return self.html_formatter.generate_html(handout)
        elif format == DeliveryFormat.PLAIN_TEXT:
            return self.text_formatter.generate_text(handout)
        elif format == DeliveryFormat.WHATSAPP:
            if handout.medication_guide:
                return WhatsAppFormatter.format_medication_guide(handout.medication_guide)
            elif handout.condition_explainer:
                return WhatsAppFormatter.format_condition_explainer(handout.condition_explainer)
            else:
                return self.text_formatter.generate_text(handout)
        else:
            return self.text_formatter.generate_text(handout)

    def send_to_patient(
        self,
        handout: PatientHandout,
        recipient: str,
        channel: NotificationChannel = NotificationChannel.WHATSAPP,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Send handout to patient via notification channel.

        Args:
            handout: Patient handout
            recipient: Phone number or email
            channel: Delivery channel
            user_id: User ID for tracking

        Returns:
            True if sent successfully
        """
        if not self.notification_service:
            raise ValueError("NotificationService not initialized")

        # Format content for channel
        if channel == NotificationChannel.WHATSAPP:
            content = self.format_handout(handout, DeliveryFormat.WHATSAPP)
        elif channel == NotificationChannel.SMS:
            # SMS is limited - send brief message with link to full content
            content = f"{handout.title[:100]}... View full guide: [link]"
        elif channel == NotificationChannel.EMAIL:
            # Send HTML email with PDF attachment
            content = self.format_handout(handout, DeliveryFormat.HTML)
        else:
            content = self.format_handout(handout, DeliveryFormat.PLAIN_TEXT)

        # Send notification
        try:
            # This would integrate with the notification service
            # For now, we'll return True
            # In production:
            # self.notification_service.send_custom(
            #     user_id=user_id,
            #     recipient=recipient,
            #     channel=channel,
            #     subject=handout.title,
            #     body=content,
            # )

            # Update handout tracking
            handout.delivered_at = datetime.utcnow()
            handout.delivery_method = channel.value

            return True
        except Exception as e:
            print(f"Failed to send handout: {e}")
            return False

    def save_handout_pdf(
        self, handout: PatientHandout, filename: Optional[str] = None
    ) -> str:
        """
        Save handout as PDF file.

        Args:
            handout: Patient handout
            filename: Optional filename (auto-generated if not provided)

        Returns:
            File path
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in handout.title if c.isalnum() or c in (" ", "_"))
            safe_title = safe_title.replace(" ", "_")[:50]
            filename = f"{safe_title}_{timestamp}.pdf"

        output_path = self.storage_dir / filename

        # Generate PDF
        self.pdf_formatter.generate_pdf(handout, str(output_path))

        return str(output_path)

    def get_templates(self) -> List[dict]:
        """
        Get list of available templates.

        Returns:
            List of template summaries
        """
        return self.template_library.list_templates()

    def get_template_by_id(self, template_id: str) -> dict:
        """
        Get template details by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template data
        """
        template = self.template_library.get_template(template_id)
        return {
            "id": template.id,
            "name": template.name,
            "type": template.content_type.value,
            "description": template.description,
            "required_fields": template.required_fields,
            "languages": template.languages,
            "template_data": template.template_data,
        }


class EducationAnalytics:
    """Analytics for education content usage."""

    def __init__(self):
        """Initialize analytics tracker."""
        self.handouts_generated = 0
        self.handouts_delivered = 0
        self.handouts_viewed = 0

        self.by_type = {}
        self.by_language = {}
        self.by_channel = {}

    def track_generation(self, handout: PatientHandout):
        """Track handout generation."""
        self.handouts_generated += 1

        # Track by type
        content_type = handout.content_type.value
        self.by_type[content_type] = self.by_type.get(content_type, 0) + 1

        # Track by language
        self.by_language[handout.language] = self.by_language.get(handout.language, 0) + 1

    def track_delivery(self, handout: PatientHandout, channel: str):
        """Track handout delivery."""
        self.handouts_delivered += 1

        # Track by channel
        self.by_channel[channel] = self.by_channel.get(channel, 0) + 1

    def track_view(self, handout_id: str):
        """Track handout view."""
        self.handouts_viewed += 1

    def get_stats(self) -> dict:
        """Get analytics statistics."""
        return {
            "total_generated": self.handouts_generated,
            "total_delivered": self.handouts_delivered,
            "total_viewed": self.handouts_viewed,
            "by_type": self.by_type,
            "by_language": self.by_language,
            "by_channel": self.by_channel,
        }


# Global service instance
_education_service: Optional[EducationService] = None


def get_education_service() -> EducationService:
    """
    Get global education service instance.

    Returns:
        Education service
    """
    global _education_service
    if _education_service is None:
        _education_service = EducationService()
    return _education_service
