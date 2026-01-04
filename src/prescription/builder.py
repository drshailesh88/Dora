"""
Prescription builder for Dora.

Builds complete prescription documents from items, patient data, and doctor data.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .models import (
    Prescription,
    EPrescription,
    PrescriptionItem,
    PatientInfo,
    DoctorInfo,
    PrescriptionStatus,
    DigitalSignature,
)


class PrescriptionBuilder:
    """Builder pattern for creating prescriptions."""

    def __init__(self):
        """Initialize builder with empty prescription."""
        self.reset()

    def reset(self):
        """Reset builder to create new prescription."""
        self._prescription_id = f"RX-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        self._items: List[PrescriptionItem] = []
        self._patient: Optional[PatientInfo] = None
        self._doctor: Optional[DoctorInfo] = None
        self._diagnosis: Optional[str] = None
        self._advice: Optional[str] = None
        self._follow_up_date: Optional[date] = None
        self._warnings: List[str] = []
        self._precautions: List[str] = []
        self._source: str = "manual"
        self._source_reference: Optional[str] = None
        self._ai_confidence: Optional[float] = None
        self._encounter_id: Optional[str] = None
        self._notes: Optional[str] = None
        self._language: str = "en"
        self._created_by: str = "system"

    def with_id(self, prescription_id: str) -> 'PrescriptionBuilder':
        """Set custom prescription ID."""
        self._prescription_id = prescription_id
        return self

    def with_patient(self, patient: PatientInfo) -> 'PrescriptionBuilder':
        """Set patient information."""
        self._patient = patient
        return self

    def with_doctor(self, doctor: DoctorInfo) -> 'PrescriptionBuilder':
        """Set doctor information."""
        self._doctor = doctor
        return self

    def add_item(self, item: PrescriptionItem) -> 'PrescriptionBuilder':
        """Add prescription item."""
        self._items.append(item)
        return self

    def add_items(self, items: List[PrescriptionItem]) -> 'PrescriptionBuilder':
        """Add multiple prescription items."""
        self._items.extend(items)
        return self

    def with_diagnosis(self, diagnosis: str) -> 'PrescriptionBuilder':
        """Set diagnosis."""
        self._diagnosis = diagnosis
        return self

    def with_advice(self, advice: str) -> 'PrescriptionBuilder':
        """Set patient advice."""
        self._advice = advice
        return self

    def with_follow_up(self, follow_up_date: date) -> 'PrescriptionBuilder':
        """Set follow-up date."""
        self._follow_up_date = follow_up_date
        return self

    def add_warning(self, warning: str) -> 'PrescriptionBuilder':
        """Add a warning."""
        self._warnings.append(warning)
        return self

    def add_warnings(self, warnings: List[str]) -> 'PrescriptionBuilder':
        """Add multiple warnings."""
        self._warnings.extend(warnings)
        return self

    def add_precaution(self, precaution: str) -> 'PrescriptionBuilder':
        """Add a precaution."""
        self._precautions.append(precaution)
        return self

    def with_source(
        self,
        source: str,
        reference: Optional[str] = None,
        ai_confidence: Optional[float] = None
    ) -> 'PrescriptionBuilder':
        """Set source of prescription (manual/dora_ai/template/emr)."""
        self._source = source
        self._source_reference = reference
        self._ai_confidence = ai_confidence
        return self

    def with_encounter(self, encounter_id: str) -> 'PrescriptionBuilder':
        """Link to EMR encounter."""
        self._encounter_id = encounter_id
        return self

    def with_notes(self, notes: str) -> 'PrescriptionBuilder':
        """Add internal notes."""
        self._notes = notes
        return self

    def with_language(self, language: str) -> 'PrescriptionBuilder':
        """Set prescription language."""
        self._language = language
        return self

    def with_created_by(self, created_by: str) -> 'PrescriptionBuilder':
        """Set who created the prescription."""
        self._created_by = created_by
        return self

    def build(self) -> Prescription:
        """
        Build and return the prescription.

        Returns:
            Complete Prescription object

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not self._patient:
            raise ValueError("Patient information is required")
        if not self._doctor:
            raise ValueError("Doctor information is required")
        if not self._items:
            raise ValueError("At least one prescription item is required")

        # Resequence items
        for idx, item in enumerate(self._items, 1):
            item.item_sequence = idx

        # Build prescription
        prescription = Prescription(
            prescription_id=self._prescription_id,
            encounter_id=self._encounter_id,
            patient=self._patient,
            doctor=self._doctor,
            items=self._items,
            diagnosis=self._diagnosis,
            advice=self._advice,
            follow_up_date=self._follow_up_date,
            warnings=self._warnings,
            precautions=self._precautions,
            source=self._source,
            source_reference=self._source_reference,
            ai_confidence=self._ai_confidence,
            created_by=self._created_by,
            notes=self._notes,
            language=self._language,
            status=PrescriptionStatus.DRAFT,
        )

        return prescription

    def build_eprescription(self, signature: DigitalSignature) -> EPrescription:
        """
        Build and return an e-prescription.

        Args:
            signature: Digital signature (required for e-prescription)

        Returns:
            Complete EPrescription object

        Raises:
            ValueError: If signature is not verified
        """
        if not signature.verified:
            raise ValueError("E-prescription requires verified digital signature")

        # Build base prescription
        base = self.build()

        # Generate e-prescription ID
        e_rx_id = f"ERX-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:12].upper()}"

        # Generate QR code data
        qr_data = self._generate_qr_code_data(base, e_rx_id)

        # Create e-prescription
        e_prescription = EPrescription(
            **base.dict(exclude={'prescription_id'}),
            prescription_id=base.prescription_id,
            e_prescription_id=e_rx_id,
            qr_code=qr_data,
            signature=signature,
            status=PrescriptionStatus.SIGNED,
        )

        return e_prescription

    def _generate_qr_code_data(self, prescription: Prescription, e_rx_id: str) -> str:
        """
        Generate QR code data for e-prescription verification.

        QR contains: E-Rx ID, Patient ID, Doctor Reg No, Date, Verification URL
        """
        qr_data = f"{e_rx_id}|{prescription.patient.patient_id}|{prescription.doctor.registration_number}|{prescription.date_prescribed.isoformat()}"
        return qr_data


class QuickPrescriptionBuilder:
    """
    Simplified builder for common use cases.

    Provides convenience methods for rapid prescription creation.
    """

    @staticmethod
    def from_template(
        template_items: List[PrescriptionItem],
        patient: PatientInfo,
        doctor: DoctorInfo,
        diagnosis: Optional[str] = None
    ) -> Prescription:
        """
        Create prescription from template.

        Args:
            template_items: Pre-configured prescription items
            patient: Patient information
            doctor: Doctor information
            diagnosis: Optional diagnosis

        Returns:
            Complete prescription
        """
        builder = PrescriptionBuilder()
        return (
            builder
            .with_patient(patient)
            .with_doctor(doctor)
            .add_items(template_items)
            .with_diagnosis(diagnosis)
            .with_source("template")
            .build()
        )

    @staticmethod
    def from_dora_answer(
        extracted_items: List[PrescriptionItem],
        dora_answer_id: str,
        patient: PatientInfo,
        doctor: DoctorInfo,
        diagnosis: Optional[str] = None,
        advice: Optional[str] = None,
        ai_confidence: Optional[float] = None
    ) -> Prescription:
        """
        Create prescription from Dora AI answer.

        Args:
            extracted_items: Items extracted from Dora answer
            dora_answer_id: ID of the Dora answer
            patient: Patient information
            doctor: Doctor information
            diagnosis: Diagnosis from Dora
            advice: Advice from Dora
            ai_confidence: AI confidence score

        Returns:
            Draft prescription requiring physician confirmation
        """
        builder = PrescriptionBuilder()

        prescription = (
            builder
            .with_patient(patient)
            .with_doctor(doctor)
            .add_items(extracted_items)
            .with_diagnosis(diagnosis)
            .with_advice(advice)
            .with_source("dora_ai", dora_answer_id, ai_confidence)
            .build()
        )

        # Mark all items as needing confirmation
        for item in prescription.items:
            item.needs_confirmation = True

        return prescription

    @staticmethod
    def from_emr(
        items: List[PrescriptionItem],
        encounter_id: str,
        patient: PatientInfo,
        doctor: DoctorInfo,
        diagnosis: Optional[str] = None
    ) -> Prescription:
        """
        Create prescription from EMR encounter.

        Args:
            items: Prescription items
            encounter_id: EMR encounter ID
            patient: Patient information
            doctor: Doctor information
            diagnosis: Diagnosis

        Returns:
            Complete prescription linked to EMR
        """
        builder = PrescriptionBuilder()
        return (
            builder
            .with_patient(patient)
            .with_doctor(doctor)
            .with_encounter(encounter_id)
            .add_items(items)
            .with_diagnosis(diagnosis)
            .with_source("emr", encounter_id)
            .build()
        )

    @staticmethod
    def create_simple(
        drug_name: str,
        strength: str,
        frequency: str,
        duration_days: int,
        patient: PatientInfo,
        doctor: DoctorInfo
    ) -> Prescription:
        """
        Create simple single-drug prescription.

        Args:
            drug_name: Drug name
            strength: Drug strength (e.g., "500mg")
            frequency: Frequency (e.g., "twice_daily")
            duration_days: Duration in days
            patient: Patient information
            doctor: Doctor information

        Returns:
            Simple prescription with one item
        """
        from .models import Dosage, DosageForm, Frequency, RouteOfAdministration

        # Create simple dosage
        dosage = Dosage(
            dose="1 tablet",
            frequency=Frequency(frequency),
            duration_days=duration_days,
            route=RouteOfAdministration.ORAL,
        )

        # Calculate quantity
        doses_per_day = {
            "once_daily": 1,
            "twice_daily": 2,
            "three_times_daily": 3,
            "four_times_daily": 4,
        }.get(frequency, 2)

        quantity = doses_per_day * duration_days

        # Create item
        item = PrescriptionItem(
            drug_name=drug_name,
            strength=strength,
            dosage_form=DosageForm.TABLET,
            dosage=dosage,
            quantity=quantity,
            quantity_unit="tablets",
            item_sequence=1,
        )

        # Build prescription
        builder = PrescriptionBuilder()
        return (
            builder
            .with_patient(patient)
            .with_doctor(doctor)
            .add_item(item)
            .build()
        )


class PrescriptionEditor:
    """Edit existing prescriptions."""

    def __init__(self, prescription: Prescription):
        """
        Initialize editor with existing prescription.

        Args:
            prescription: Prescription to edit
        """
        self.prescription = prescription

    def add_item(self, item: PrescriptionItem) -> 'PrescriptionEditor':
        """Add new item to prescription."""
        item.item_sequence = len(self.prescription.items) + 1
        self.prescription.items.append(item)
        self._update_timestamp()
        return self

    def remove_item(self, sequence: int) -> 'PrescriptionEditor':
        """Remove item by sequence number."""
        self.prescription.items = [
            item for item in self.prescription.items
            if item.item_sequence != sequence
        ]
        # Resequence
        for idx, item in enumerate(self.prescription.items, 1):
            item.item_sequence = idx
        self._update_timestamp()
        return self

    def update_item(
        self,
        sequence: int,
        updated_item: PrescriptionItem
    ) -> 'PrescriptionEditor':
        """Update specific item."""
        for idx, item in enumerate(self.prescription.items):
            if item.item_sequence == sequence:
                updated_item.item_sequence = sequence
                self.prescription.items[idx] = updated_item
                self._update_timestamp()
                break
        return self

    def set_diagnosis(self, diagnosis: str) -> 'PrescriptionEditor':
        """Update diagnosis."""
        self.prescription.diagnosis = diagnosis
        self._update_timestamp()
        return self

    def set_advice(self, advice: str) -> 'PrescriptionEditor':
        """Update advice."""
        self.prescription.advice = advice
        self._update_timestamp()
        return self

    def add_warning(self, warning: str) -> 'PrescriptionEditor':
        """Add warning."""
        self.prescription.warnings.append(warning)
        self._update_timestamp()
        return self

    def confirm_ai_suggestions(self) -> 'PrescriptionEditor':
        """Confirm all AI-extracted items."""
        self.prescription.physician_confirmed = True
        for item in self.prescription.items:
            item.needs_confirmation = False
        self._update_timestamp()
        return self

    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.prescription.updated_at = datetime.utcnow()

    def get_prescription(self) -> Prescription:
        """Get the edited prescription."""
        return self.prescription


# Example usage
if __name__ == "__main__":
    # Create sample patient and doctor
    patient = PatientInfo(
        patient_id="PAT-001",
        mrn="MRN-2024-1234",
        name="Rahul Sharma",
        age=45,
        gender="M",
        known_allergies=["Sulfa drugs"],
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Shailesh Kumar",
        qualifications="MD, MBBS",
        specialization="General Medicine",
        registration_number="MCI-12345",
        clinic_name="DocAssist Clinic",
    )

    # Build prescription using builder
    builder = PrescriptionBuilder()

    from .models import (
        Dosage, DosageForm, Frequency, RouteOfAdministration,
        PrescriptionItem
    )

    # Create item
    metformin = PrescriptionItem(
        drug_name="Metformin",
        strength="500mg",
        dosage_form=DosageForm.TABLET,
        dosage=Dosage(
            dose="1 tablet",
            frequency=Frequency.BD,
            frequency_detail="1-0-1",
            duration_days=30,
            route=RouteOfAdministration.ORAL,
            timing="after food",
        ),
        quantity=60,
        quantity_unit="tablets",
        item_sequence=1,
        instructions="Take with meals to reduce stomach upset",
    )

    prescription = (
        builder
        .with_patient(patient)
        .with_doctor(doctor)
        .add_item(metformin)
        .with_diagnosis("Type 2 Diabetes Mellitus")
        .with_advice("Check fasting blood sugar weekly")
        .with_follow_up(date.today() + timedelta(days=30))
        .build()
    )

    print(f"Created prescription: {prescription.prescription_id}")
    print(f"Status: {prescription.status}")
    print(f"Items: {len(prescription.items)}")
