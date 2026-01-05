"""Documentation Service for Dora.

Main service interface for clinical documentation functionality.
"""

from datetime import datetime
from typing import Any, Optional, Union

from .certificate import MedicalCertificateGenerator
from .discharge import DischargeSummaryGenerator
from .extractor import MedicalInformationExtractor
from .formatter import EMRFormatter, JSONFormatter, PDFFormatter, TextFormatter
from .models import (
    CertificateType,
    DischargeSummary,
    DocumentStatus,
    MedicalCertificate,
    OperativeNote,
    Patient,
    Provider,
    ReferralLetter,
    SOAPNote,
    UrgencyLevel,
)
from .operative import OperativeNoteGenerator
from .referral import ReferralLetterGenerator
from .soap import SOAPNoteGenerator
from .templates import TemplateManager
from .validator import DocumentValidator, ValidationResult


class DocumentationService:
    """Main service for clinical documentation."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize documentation service.

        Args:
            model: LLM model to use for generation
        """
        self.model = model

        # Initialize generators
        self.soap_generator = SOAPNoteGenerator(model=model)
        self.discharge_generator = DischargeSummaryGenerator(model=model)
        self.referral_generator = ReferralLetterGenerator(model=model)
        self.operative_generator = OperativeNoteGenerator(model=model)
        self.certificate_generator = MedicalCertificateGenerator()

        # Initialize utilities
        self.extractor = MedicalInformationExtractor(model=model)
        self.validator = DocumentValidator()
        self.template_manager = TemplateManager()

        # Initialize formatters
        self.text_formatter = TextFormatter()
        self.json_formatter = JSONFormatter()
        self.pdf_formatter = PDFFormatter()
        self.emr_formatter = EMRFormatter()

    # SOAP Note Generation
    async def generate_soap_from_text(
        self,
        text: str,
        patient: Optional[Patient] = None,
        provider: Optional[Provider] = None,
    ) -> SOAPNote:
        """Generate SOAP note from text (voice transcript, etc.).

        Args:
            text: Clinical encounter text
            patient: Patient information
            provider: Provider information

        Returns:
            SOAP note in draft status
        """
        return await self.soap_generator.generate_from_text(text, patient, provider)

    async def generate_soap_from_voice(
        self,
        transcript: str,
        patient: Optional[Patient] = None,
        provider: Optional[Provider] = None,
    ) -> SOAPNote:
        """Generate SOAP note from voice transcript.

        Args:
            transcript: Voice transcript
            patient: Patient information
            provider: Provider information

        Returns:
            SOAP note
        """
        # Extract structured data from voice transcript
        extracted = await self.extractor.extract_from_voice_transcript(transcript)

        # Generate SOAP note
        return await self.soap_generator.generate_from_structured(
            extracted, patient, provider
        )

    # Discharge Summary
    async def generate_discharge_summary(
        self,
        patient: Patient,
        provider: Provider,
        admission_data: dict[str, Any],
        enhance: bool = True,
    ) -> DischargeSummary:
        """Generate discharge summary.

        Args:
            patient: Patient information
            provider: Provider
            admission_data: Admission and hospital course data
            enhance: Whether to enhance with AI-generated instructions

        Returns:
            Discharge summary
        """
        summary = await self.discharge_generator.generate_from_admission(
            patient, provider, admission_data
        )

        if enhance:
            summary = await self.discharge_generator.enhance_with_ai(summary)

        return summary

    # Referral Letters
    async def generate_referral(
        self,
        patient: Patient,
        referring_provider: Provider,
        specialty: str,
        reason: str,
        urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
        **kwargs,
    ) -> ReferralLetter:
        """Generate referral letter.

        Args:
            patient: Patient information
            referring_provider: Referring doctor
            specialty: Specialty to refer to
            reason: Reason for referral
            urgency: Urgency level
            **kwargs: Additional referral data

        Returns:
            Referral letter
        """
        return await self.referral_generator.generate(
            patient=patient,
            referring_provider=referring_provider,
            specialty=specialty,
            reason=reason,
            urgency=urgency,
            **kwargs,
        )

    async def generate_referral_from_soap(
        self,
        soap_note: SOAPNote,
        specialty: str,
        reason: str,
        urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
    ) -> ReferralLetter:
        """Generate referral from existing SOAP note.

        Args:
            soap_note: SOAP note
            specialty: Specialty to refer to
            reason: Reason for referral
            urgency: Urgency level

        Returns:
            Referral letter
        """
        return await self.referral_generator.generate_from_soap(
            soap_note, specialty, reason, urgency=urgency
        )

    # Medical Certificates
    def generate_sick_leave(
        self,
        patient: Patient,
        provider: Provider,
        diagnosis: str,
        days: int = 3,
    ) -> MedicalCertificate:
        """Generate sick leave certificate.

        Args:
            patient: Patient
            provider: Provider
            diagnosis: Diagnosis
            days: Days of rest

        Returns:
            Sick leave certificate
        """
        return self.certificate_generator.generate_sick_leave_certificate(
            patient=patient,
            provider=provider,
            diagnosis=diagnosis,
            from_date=datetime.now(),
            days_of_rest=days,
        )

    def generate_fitness_certificate(
        self,
        patient: Patient,
        provider: Provider,
        purpose: str,
        fit_for: str = "normal duties",
        restrictions: Optional[str] = None,
    ) -> MedicalCertificate:
        """Generate fitness certificate.

        Args:
            patient: Patient
            provider: Provider
            purpose: Purpose of certificate
            fit_for: What patient is fit for
            restrictions: Any restrictions

        Returns:
            Fitness certificate
        """
        return self.certificate_generator.generate_fitness_certificate(
            patient=patient,
            provider=provider,
            purpose=purpose,
            fitness_statement=f"Fit for {fit_for}",
            restrictions=restrictions,
        )

    # Operative Notes
    async def generate_operative_note(
        self,
        patient: Patient,
        surgeon: Provider,
        operative_data: dict[str, Any],
        assistants: Optional[list[Provider]] = None,
    ) -> OperativeNote:
        """Generate operative note.

        Args:
            patient: Patient
            surgeon: Primary surgeon
            operative_data: Operative details
            assistants: Assistant surgeons

        Returns:
            Operative note
        """
        return await self.operative_generator.generate(
            patient, surgeon, operative_data, assistants
        )

    async def generate_operative_from_dictation(
        self,
        dictation: str,
        patient: Patient,
        surgeon: Provider,
        assistants: Optional[list[Provider]] = None,
    ) -> OperativeNote:
        """Generate operative note from surgeon's dictation.

        Args:
            dictation: Surgeon's dictation
            patient: Patient
            surgeon: Surgeon
            assistants: Assistants

        Returns:
            Operative note
        """
        return await self.operative_generator.generate_from_dictation(
            dictation, patient, surgeon, assistants
        )

    # Extraction
    async def extract_from_text(self, text: str) -> dict[str, Any]:
        """Extract medical entities from text.

        Args:
            text: Clinical text

        Returns:
            Extracted entities
        """
        return await self.extractor.extract_from_text(text)

    async def extract_from_voice(self, transcript: str) -> dict[str, Any]:
        """Extract from voice transcript.

        Args:
            transcript: Voice transcript

        Returns:
            Extracted entities
        """
        return await self.extractor.extract_from_voice_transcript(transcript)

    # Validation
    def validate(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
    ) -> ValidationResult:
        """Validate a document.

        Args:
            document: Document to validate

        Returns:
            Validation result
        """
        return self.validator.validate_document(document)

    # Formatting
    def to_text(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
    ) -> str:
        """Format document as text.

        Args:
            document: Document to format

        Returns:
            Formatted text
        """
        if isinstance(document, SOAPNote):
            return self.text_formatter.format_soap_note(document)
        elif isinstance(document, DischargeSummary):
            return self.text_formatter.format_discharge_summary(document)
        else:
            return str(document)

    def to_json(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
    ) -> str:
        """Format document as JSON.

        Args:
            document: Document to format

        Returns:
            JSON string
        """
        return self.json_formatter.format_any(document)

    def to_pdf(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
    ) -> bytes:
        """Format document as PDF.

        Args:
            document: Document to format

        Returns:
            PDF bytes
        """
        if isinstance(document, SOAPNote):
            return self.pdf_formatter.format_soap_note(document)
        else:
            raise NotImplementedError(f"PDF formatting not implemented for {type(document)}")

    # Signing
    def sign_document(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
    ) -> bool:
        """Sign a document.

        Args:
            document: Document to sign

        Returns:
            True if successful
        """
        # Validate first
        validation = self.validate(document)

        if not validation.is_valid:
            raise ValueError(
                f"Cannot sign document with errors. Issues:\n{validation.get_summary()}"
            )

        # Sign
        document.status = DocumentStatus.SIGNED
        document.signed_at = datetime.now()

        return True

    # EMR Integration
    async def push_to_emr(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, OperativeNote, MedicalCertificate],
        emr_system: str = "docassist",
    ) -> dict[str, Any]:
        """Push document to EMR.

        Args:
            document: Document to push
            emr_system: EMR system identifier

        Returns:
            EMR response
        """
        from ..emr.client import EMRClient, EMRConfig
        from ..emr.models import ClinicalNote as EMRClinicalNote

        # Format for EMR
        emr_data = self.emr_formatter.format_for_docassist_emr(document)

        try:
            # Initialize EMR client
            emr_client = EMRClient(config=EMRConfig())

            async with emr_client:
                # Create clinical note in EMR
                if emr_data.get("patient_id"):
                    # Create EMR clinical note object
                    clinical_note = EMRClinicalNote(
                        patient_id=emr_data["patient_id"],
                        note_type=emr_data.get("note_type", "progress"),
                        note_date=emr_data.get("note_date"),
                        subjective=emr_data.get("subjective"),
                        objective=emr_data.get("objective"),
                        assessment=emr_data.get("assessment"),
                        plan=emr_data.get("plan"),
                        full_note=emr_data.get("full_note"),
                        author=emr_data.get("author"),
                        signed=emr_data.get("signed", False),
                        signed_at=emr_data.get("signed_at"),
                    )

                    # Push to EMR via API
                    response = await emr_client._request(
                        "POST",
                        f"/patients/{emr_data['patient_id']}/notes",
                        json=clinical_note.model_dump(exclude_none=True),
                    )

                    return {
                        "success": True,
                        "emr_system": emr_system,
                        "data": response,
                        "message": "Document successfully pushed to EMR",
                    }
                else:
                    return {
                        "success": False,
                        "emr_system": emr_system,
                        "error": "No patient_id in document",
                        "message": "Cannot push to EMR without patient identifier",
                    }

        except Exception as e:
            # Fallback to returning formatted data if API fails
            return {
                "success": False,
                "emr_system": emr_system,
                "data": emr_data,
                "error": str(e),
                "message": f"EMR API call failed: {str(e)}. Data formatted but not pushed.",
            }

    # Templates
    def list_templates(self, specialty: Optional[str] = None) -> list[dict[str, Any]]:
        """List available templates.

        Args:
            specialty: Filter by specialty

        Returns:
            List of templates
        """
        if specialty:
            from .templates import Specialty

            specialty_enum = Specialty(specialty)
            templates = self.template_manager.get_templates_by_specialty(specialty_enum)
            return [
                {
                    "template_id": t.template_id,
                    "name": t.name,
                    "specialty": t.specialty.value,
                }
                for t in templates
            ]
        else:
            return self.template_manager.list_templates()


# Singleton instance
_service: Optional[DocumentationService] = None


def get_documentation_service(model: str = "claude-3-5-sonnet-20241022") -> DocumentationService:
    """Get documentation service singleton.

    Args:
        model: LLM model to use

    Returns:
        Documentation service
    """
    global _service
    if _service is None:
        _service = DocumentationService(model=model)
    return _service
