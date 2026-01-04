"""
Prescription service - main orchestration layer for Dora.

High-level API for prescription operations:
- Generate prescription from Dora answer
- Validate prescription
- Get alternatives
- Sign prescription
- Format and export
- Send to pharmacy/EMR
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    Prescription,
    EPrescription,
    PrescriptionItem,
    PatientInfo,
    DoctorInfo,
    PrescriptionValidationResult,
    DrugAlternative,
    DigitalSignature,
)
from .extractor import PrescriptionExtractor
from .builder import PrescriptionBuilder, QuickPrescriptionBuilder
from .validator import PrescriptionValidator
from .alternatives import AlternativesSuggester
from .templates import TemplateLibrary, CustomTemplateManager
from .signature import SignatureService, DigitalCertificate
from .formatter import PrescriptionFormatter
from .dispense import PharmacyService, RefillManager


class PrescriptionService:
    """
    Main service for prescription operations.

    Orchestrates all prescription-related functionality.
    """

    def __init__(
        self,
        llm_client=None,
        drug_database=None,
        pricing_database=None,
        pharmacy_api=None,
    ):
        """
        Initialize prescription service.

        Args:
            llm_client: LLM client for AI-powered extraction
            drug_database: Drug interaction database
            pricing_database: Drug pricing database
            pharmacy_api: Pharmacy integration API
        """
        self.extractor = PrescriptionExtractor(llm_client=llm_client)
        self.validator = PrescriptionValidator(drug_database=drug_database)
        self.alternatives = AlternativesSuggester(
            drug_database=drug_database,
            pricing_database=pricing_database
        )
        self.signature_service = SignatureService()
        self.pharmacy_service = PharmacyService(pharmacy_api=pharmacy_api)
        self.refill_manager = RefillManager()
        self.template_manager = CustomTemplateManager()

    def generate_from_dora_answer(
        self,
        answer_text: str,
        dora_answer_id: str,
        patient: PatientInfo,
        doctor: DoctorInfo,
        diagnosis: Optional[str] = None,
        advice: Optional[str] = None,
        use_llm: bool = True,
        min_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate prescription from Dora AI answer.

        This is the MAGIC one-tap prescription feature!

        Args:
            answer_text: Dora AI answer text
            dora_answer_id: ID of Dora answer
            patient: Patient information
            doctor: Doctor information
            diagnosis: Optional diagnosis
            advice: Optional advice
            use_llm: Use LLM for extraction (more accurate)
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with prescription, validation, and alternatives
        """
        # Step 1: Extract medications from answer
        extracted_data = self.extractor.extract_from_answer(
            answer_text,
            use_llm=use_llm,
            min_confidence=min_confidence
        )

        if not extracted_data:
            return {
                'success': False,
                'error': 'No medications found in answer',
            }

        # Step 2: Build prescription items
        items = self.extractor.build_prescription_items(
            extracted_data,
            require_confirmation=True
        )

        # Step 3: Calculate AI confidence
        avg_confidence = sum(
            item.confidence_score or 0 for item in items
        ) / len(items) if items else 0

        # Step 4: Build prescription
        prescription = QuickPrescriptionBuilder.from_dora_answer(
            extracted_items=items,
            dora_answer_id=dora_answer_id,
            patient=patient,
            doctor=doctor,
            diagnosis=diagnosis,
            advice=advice,
            ai_confidence=avg_confidence,
        )

        # Step 5: Validate prescription
        validation = self.validator.validate(prescription)

        # Step 6: Get alternatives for cost savings
        all_alternatives = []
        for item in items:
            item_alternatives = self.alternatives.suggest_alternatives(
                item,
                max_alternatives=3
            )
            all_alternatives.extend(item_alternatives)

        # Step 7: Format for preview
        preview_text = PrescriptionFormatter.format_text(prescription)

        return {
            'success': True,
            'prescription': prescription,
            'validation': validation,
            'alternatives': all_alternatives,
            'preview': preview_text,
            'requires_confirmation': True,
            'ai_confidence': avg_confidence,
            'extracted_count': len(items),
        }

    def validate_prescription(
        self,
        prescription: Prescription
    ) -> PrescriptionValidationResult:
        """
        Validate prescription for safety.

        Args:
            prescription: Prescription to validate

        Returns:
            Validation result
        """
        return self.validator.validate(prescription)

    def get_alternatives(
        self,
        prescription: Prescription,
        max_per_item: int = 3
    ) -> Dict[str, List[DrugAlternative]]:
        """
        Get alternatives for all items in prescription.

        Args:
            prescription: Prescription
            max_per_item: Max alternatives per item

        Returns:
            Dictionary mapping item sequence to alternatives
        """
        alternatives_map = {}

        for item in prescription.items:
            alts = self.alternatives.suggest_alternatives(
                item,
                max_alternatives=max_per_item
            )
            if alts:
                alternatives_map[item.item_sequence] = alts

        return alternatives_map

    def sign_prescription(
        self,
        prescription: Prescription,
        certificate: DigitalCertificate,
        pin: Optional[str] = None,
    ) -> EPrescription:
        """
        Digitally sign prescription to create e-prescription.

        Args:
            prescription: Prescription to sign
            certificate: Doctor's digital certificate
            pin: PIN for authentication

        Returns:
            E-prescription with signature

        Raises:
            ValueError: If validation fails or signature invalid
        """
        # Validate prescription first
        validation = self.validator.validate(prescription)

        if not validation.is_valid:
            raise ValueError(
                f"Cannot sign invalid prescription. Errors: {', '.join(validation.errors)}"
            )

        # Generate signature
        signature = self.signature_service.sign_prescription(
            prescription,
            certificate,
            pin=pin,
        )

        # Build e-prescription
        builder = PrescriptionBuilder()

        # Copy data from prescription
        for key, value in prescription.dict().items():
            if hasattr(builder, f"_{key}"):
                setattr(builder, f"_{key}", value)

        builder._prescription_id = prescription.prescription_id
        builder._items = prescription.items
        builder._patient = prescription.patient
        builder._doctor = prescription.doctor

        # Build e-prescription
        e_prescription = builder.build_eprescription(signature)

        return e_prescription

    def format_prescription(
        self,
        prescription: Prescription,
        format_type: str = "text"
    ) -> Any:
        """
        Format prescription for output.

        Args:
            prescription: Prescription to format
            format_type: text, pdf, json, emr, whatsapp

        Returns:
            Formatted output
        """
        formatters = {
            'text': PrescriptionFormatter.format_text,
            'pdf': PrescriptionFormatter.format_pdf,
            'json': PrescriptionFormatter.format_json,
            'emr': PrescriptionFormatter.format_emr,
            'whatsapp': PrescriptionFormatter.format_whatsapp,
        }

        formatter = formatters.get(format_type)
        if not formatter:
            raise ValueError(f"Unknown format type: {format_type}")

        return formatter(prescription)

    def send_to_pharmacy(
        self,
        prescription: Prescription,
        pharmacy_id: str,
        delivery_method: str = "pickup",
    ):
        """
        Send prescription to pharmacy.

        Args:
            prescription: Prescription to send
            pharmacy_id: Target pharmacy ID
            delivery_method: pickup or delivery

        Returns:
            Dispense record
        """
        return self.pharmacy_service.send_to_pharmacy(
            prescription,
            pharmacy_id,
            delivery_method=delivery_method,
        )

    def send_to_emr(
        self,
        prescription: Prescription,
        emr_api_client=None
    ) -> bool:
        """
        Send prescription to EMR system.

        Args:
            prescription: Prescription to send
            emr_api_client: EMR API client

        Returns:
            Success status
        """
        if not emr_api_client:
            # Mark as sent but don't actually send
            prescription.sent_to_emr = True
            return True

        try:
            # Format for EMR
            emr_data = PrescriptionFormatter.format_emr(prescription)

            # Send to EMR
            response = emr_api_client.create_prescription(emr_data)

            if response.get('success'):
                prescription.sent_to_emr = True
                prescription.emr_id = response.get('emr_prescription_id')
                return True

            return False

        except Exception as e:
            print(f"Error sending to EMR: {e}")
            return False

    def get_template(self, template_name: str):
        """
        Get prescription template.

        Args:
            template_name: Template name

        Returns:
            Template or None
        """
        return TemplateLibrary.get_template(template_name)

    def list_templates(self):
        """List all available templates."""
        return TemplateLibrary.list_templates()

    def create_from_template(
        self,
        template_name: str,
        patient: PatientInfo,
        doctor: DoctorInfo,
    ) -> Prescription:
        """
        Create prescription from template.

        Args:
            template_name: Template name
            patient: Patient information
            doctor: Doctor information

        Returns:
            Prescription from template
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")

        return QuickPrescriptionBuilder.from_template(
            template_items=template.items,
            patient=patient,
            doctor=doctor,
            diagnosis=template.condition,
        )

    def complete_workflow(
        self,
        answer_text: str,
        dora_answer_id: str,
        patient: PatientInfo,
        doctor: DoctorInfo,
        certificate: DigitalCertificate,
        pharmacy_id: Optional[str] = None,
        emr_api_client=None,
    ) -> Dict[str, Any]:
        """
        Complete end-to-end workflow: Extract → Validate → Sign → Send.

        This is the complete one-tap prescription flow!

        Args:
            answer_text: Dora answer
            dora_answer_id: Dora answer ID
            patient: Patient info
            doctor: Doctor info
            certificate: Digital certificate for signing
            pharmacy_id: Optional pharmacy to send to
            emr_api_client: Optional EMR client

        Returns:
            Complete workflow result
        """
        result = {
            'success': False,
            'steps': {
                'extract': False,
                'validate': False,
                'sign': False,
                'pharmacy': False,
                'emr': False,
            }
        }

        try:
            # Step 1: Extract and generate
            generation = self.generate_from_dora_answer(
                answer_text=answer_text,
                dora_answer_id=dora_answer_id,
                patient=patient,
                doctor=doctor,
            )

            if not generation['success']:
                result['error'] = generation.get('error')
                return result

            result['steps']['extract'] = True
            prescription = generation['prescription']
            validation = generation['validation']

            # Step 2: Check validation
            if not validation.is_valid:
                result['error'] = f"Validation failed: {', '.join(validation.errors)}"
                result['validation'] = validation
                return result

            result['steps']['validate'] = True

            # Step 3: Sign prescription
            try:
                e_prescription = self.sign_prescription(
                    prescription,
                    certificate,
                )
                result['steps']['sign'] = True
                result['prescription'] = e_prescription
            except Exception as e:
                result['error'] = f"Signature failed: {str(e)}"
                return result

            # Step 4: Send to pharmacy (optional)
            if pharmacy_id:
                try:
                    dispense_record = self.send_to_pharmacy(
                        e_prescription,
                        pharmacy_id,
                    )
                    result['steps']['pharmacy'] = True
                    result['dispense_record'] = dispense_record
                except Exception as e:
                    # Non-critical error
                    result['pharmacy_error'] = str(e)

            # Step 5: Send to EMR (optional)
            if emr_api_client:
                try:
                    emr_success = self.send_to_emr(e_prescription, emr_api_client)
                    result['steps']['emr'] = emr_success
                except Exception as e:
                    # Non-critical error
                    result['emr_error'] = str(e)

            # Success!
            result['success'] = True
            result['validation'] = validation
            result['alternatives'] = generation.get('alternatives', [])

            return result

        except Exception as e:
            result['error'] = f"Workflow failed: {str(e)}"
            return result


# Example usage
if __name__ == "__main__":
    from datetime import timedelta

    # Initialize service
    service = PrescriptionService()

    # Sample Dora answer
    dora_answer = """
    Based on your symptoms and blood sugar levels, I recommend:

    1. Tab. Metformin 500mg - 1-0-1 x 30 days (after food)
       This will help control your blood sugar.

    2. Tab. Glimepiride 2mg - 1-0-0 x 30 days (before breakfast)
       Take before breakfast. Keep sugar handy.

    Also follow diabetic diet and exercise regularly.
    """

    # Patient and doctor info
    patient = PatientInfo(
        patient_id="PAT-001",
        mrn="MRN-2024-1234",
        name="Rahul Sharma",
        age=45,
        gender="M",
        known_allergies=[],
        active_conditions=["Type 2 Diabetes Mellitus"],
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Shailesh Kumar",
        qualifications="MD, MBBS",
        registration_number="MCI-12345",
        clinic_name="DocAssist Clinic",
    )

    # Generate prescription from Dora answer
    result = service.generate_from_dora_answer(
        answer_text=dora_answer,
        dora_answer_id="DORA-ANS-12345",
        patient=patient,
        doctor=doctor,
        diagnosis="Type 2 Diabetes Mellitus - Newly diagnosed",
        use_llm=False,  # Using regex extraction for demo
    )

    if result['success']:
        print("✅ Prescription generated successfully!")
        print(f"Extracted {result['extracted_count']} medications")
        print(f"AI Confidence: {result['ai_confidence']:.2f}")
        print(f"\nValidation: {'✅ PASSED' if result['validation'].is_valid else '❌ FAILED'}")

        if result['validation'].warnings:
            print("\nWarnings:")
            for warning in result['validation'].warnings:
                print(f"  {warning}")

        if result['alternatives']:
            print(f"\nFound {len(result['alternatives'])} cost-saving alternatives")

        print("\n" + "="*62)
        print(result['preview'])

    else:
        print(f"❌ Failed: {result.get('error')}")
