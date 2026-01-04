"""
Prescription formatter for Dora.

Formats prescriptions for:
- Print (text)
- PDF
- EMR integration
- E-prescription standard formats
"""

from typing import Optional
from datetime import datetime
import io

from .models import Prescription, EPrescription, PrescriptionItem


class PrescriptionFormatter:
    """Format prescriptions for various outputs."""

    @staticmethod
    def format_text(prescription: Prescription) -> str:
        """
        Format prescription as formatted text (for print/display).

        Returns prescription in the beautiful box format shown in requirements.
        """
        lines = []

        # Header box
        lines.append("╔══════════════════════════════════════════════════════════════╗")

        # Clinic/Doctor info
        clinic_name = prescription.doctor.clinic_name or "Medical Clinic"
        lines.append(f"║{clinic_name:^62}║")
        lines.append(f"║{prescription.doctor.name:^62}║")

        quals = prescription.doctor.qualifications
        reg = f"Reg No: {prescription.doctor.registration_number}"
        phone = f"Ph: {prescription.doctor.phone}" if prescription.doctor.phone else ""
        info_line = f"{quals} | {reg}"
        if phone:
            info_line += f" | {phone}"
        lines.append(f"║{info_line:^62}║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Patient info and date
        patient_info = f"Patient: {prescription.patient.name} ({prescription.patient.gender}, {prescription.patient.age}y)"
        date_str = f"Date: {prescription.date_prescribed.strftime('%d-%b-%Y')}"

        lines.append(f"║ {patient_info:<44} {date_str:>15} ║")

        if prescription.patient.mrn:
            lines.append(f"║ MRN: {prescription.patient.mrn:<55}║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Diagnosis (if present)
        if prescription.diagnosis:
            lines.append(f"║ Diagnosis: {prescription.diagnosis:<49}║")
            lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Prescription header
        lines.append("║ Rx{:>59}║".format(""))
        lines.append("║{:>62}║".format(""))

        # Items
        for idx, item in enumerate(prescription.items, 1):
            # Drug name and strength
            drug_line = f"{idx}. Tab. {item.drug_name} {item.strength}"
            lines.append(f"║ {drug_line:<60}║")

            # Dosage
            dosage = PrescriptionFormatter._format_dosage(item)
            lines.append(f"║    {dosage:<58}║")

            # Quantity
            qty_line = f"Qty: {item.quantity} {item.quantity_unit}"
            lines.append(f"║    {qty_line:<58}║")

            # Instructions (if present)
            if item.instructions:
                # Wrap long instructions
                instructions = PrescriptionFormatter._wrap_text(item.instructions, 58)
                for inst_line in instructions:
                    lines.append(f"║    {inst_line:<58}║")

            lines.append("║{:>62}║".format(""))

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Advice
        if prescription.advice:
            lines.append("║ Advice:{:>54}║".format(""))
            advice_lines = PrescriptionFormatter._wrap_text(prescription.advice, 60)
            for advice_line in advice_lines:
                lines.append(f"║ {advice_line:<60}║")
            lines.append("║{:>62}║".format(""))

        # Warnings
        if prescription.warnings:
            warning_text = " Avoid: " + ", ".join(prescription.warnings[:3])  # First 3 warnings
            lines.append(f"║ ⚠️  {warning_text:<58}║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Signature
        lines.append("║{:>62}║".format(""))
        lines.append("║{:^62}║".format("[Digital Signature]"))
        lines.append("║{:^62}║".format(prescription.doctor.name))

        lines.append("╚══════════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    @staticmethod
    def _format_dosage(item: PrescriptionItem) -> str:
        """Format dosage instructions."""
        parts = []

        # Frequency detail or frequency name
        if item.dosage.frequency_detail:
            parts.append(item.dosage.frequency_detail)
        else:
            parts.append(item.dosage.frequency.replace('_', ' '))

        # Duration
        parts.append(f"× {item.dosage.duration_days} days")

        # Timing
        if item.dosage.timing:
            parts.append(f"({item.dosage.timing})")

        return " ".join(parts)

    @staticmethod
    def _wrap_text(text: str, width: int) -> list:
        """Wrap text to specified width."""
        # Simple word wrapping
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + (1 if current_line else 0)  # +1 for space

            if current_length + word_length <= width:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        # Handle bullet points
        formatted_lines = []
        for line in lines:
            if line.startswith("•"):
                formatted_lines.append(line)
            elif formatted_lines and formatted_lines[-1].startswith("•"):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return formatted_lines

    @staticmethod
    def format_json(prescription: Prescription) -> dict:
        """Format prescription as JSON (for API/EMR)."""
        return prescription.dict()

    @staticmethod
    def format_pdf(prescription: Prescription) -> bytes:
        """
        Generate PDF prescription.

        In production, use reportlab or weasyprint for proper PDF generation.
        This is a stub that returns PDF-like content.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, Frame

            # Create PDF in memory
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # Header
            y = height - 1 * inch
            c.setFont("Helvetica-Bold", 16)
            clinic_name = prescription.doctor.clinic_name or "Medical Clinic"
            c.drawCentredString(width / 2, y, clinic_name)

            y -= 0.3 * inch
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width / 2, y, prescription.doctor.name)

            y -= 0.25 * inch
            c.setFont("Helvetica", 10)
            info = f"{prescription.doctor.qualifications} | Reg: {prescription.doctor.registration_number}"
            c.drawCentredString(width / 2, y, info)

            # Line
            y -= 0.3 * inch
            c.line(1 * inch, y, width - 1 * inch, y)

            # Patient info
            y -= 0.3 * inch
            c.setFont("Helvetica", 11)
            patient_info = f"Patient: {prescription.patient.name} ({prescription.patient.gender}, {prescription.patient.age}y)"
            c.drawString(1 * inch, y, patient_info)

            date_str = prescription.date_prescribed.strftime('%d-%b-%Y')
            c.drawRightString(width - 1 * inch, y, f"Date: {date_str}")

            if prescription.patient.mrn:
                y -= 0.2 * inch
                c.drawString(1 * inch, y, f"MRN: {prescription.patient.mrn}")

            # Diagnosis
            if prescription.diagnosis:
                y -= 0.25 * inch
                c.drawString(1 * inch, y, f"Diagnosis: {prescription.diagnosis}")

            # Rx header
            y -= 0.4 * inch
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1 * inch, y, "Rx")

            # Items
            y -= 0.3 * inch
            c.setFont("Helvetica", 10)

            for idx, item in enumerate(prescription.items, 1):
                # Drug name
                y -= 0.2 * inch
                drug_text = f"{idx}. Tab. {item.drug_name} {item.strength}"
                c.drawString(1.2 * inch, y, drug_text)

                # Dosage
                y -= 0.18 * inch
                dosage = PrescriptionFormatter._format_dosage(item)
                c.drawString(1.4 * inch, y, dosage)

                # Quantity
                y -= 0.18 * inch
                c.drawString(1.4 * inch, y, f"Qty: {item.quantity} {item.quantity_unit}")

                y -= 0.1 * inch

            # Advice
            if prescription.advice:
                y -= 0.3 * inch
                c.setFont("Helvetica-Bold", 11)
                c.drawString(1 * inch, y, "Advice:")

                y -= 0.2 * inch
                c.setFont("Helvetica", 9)

                # Wrap advice
                advice_lines = PrescriptionFormatter._wrap_text(prescription.advice, 80)
                for line in advice_lines[:5]:  # Max 5 lines
                    c.drawString(1.2 * inch, y, line)
                    y -= 0.15 * inch

            # Signature
            y -= 0.5 * inch
            c.setFont("Helvetica-Italic", 10)
            c.drawCentredString(width / 2, y, "[Digital Signature]")

            y -= 0.2 * inch
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(width / 2, y, prescription.doctor.name)

            # Footer
            c.setFont("Helvetica", 8)
            c.drawCentredString(width / 2, 0.5 * inch, f"Prescription ID: {prescription.prescription_id}")

            # Save PDF
            c.showPage()
            c.save()

            return buffer.getvalue()

        except ImportError:
            # Fallback if reportlab not installed
            # Return text version as "PDF"
            text = PrescriptionFormatter.format_text(prescription)
            return text.encode('utf-8')

    @staticmethod
    def format_emr(prescription: Prescription) -> dict:
        """
        Format prescription for EMR integration.

        Returns structured data compatible with EMR systems.
        """
        return {
            'prescription': {
                'id': prescription.prescription_id,
                'encounter_id': prescription.encounter_id,
                'date': prescription.date_prescribed.isoformat(),
                'status': prescription.status,
            },
            'patient': {
                'id': prescription.patient.patient_id,
                'mrn': prescription.patient.mrn,
                'name': prescription.patient.name,
                'age': prescription.patient.age,
                'gender': prescription.patient.gender,
            },
            'prescriber': {
                'id': prescription.doctor.doctor_id,
                'name': prescription.doctor.name,
                'registration': prescription.doctor.registration_number,
            },
            'medications': [
                {
                    'sequence': item.item_sequence,
                    'drug_name': item.drug_name,
                    'generic_name': item.generic_name,
                    'strength': item.strength,
                    'dosage_form': item.dosage_form,
                    'dose': item.dosage.dose,
                    'frequency': item.dosage.frequency,
                    'duration_days': item.dosage.duration_days,
                    'route': item.dosage.route,
                    'quantity': item.quantity,
                    'instructions': item.instructions,
                }
                for item in prescription.items
            ],
            'diagnosis': prescription.diagnosis,
            'advice': prescription.advice,
            'warnings': prescription.warnings,
        }

    @staticmethod
    def format_whatsapp(prescription: Prescription) -> str:
        """
        Format prescription for WhatsApp sharing.

        Simple text format optimized for mobile viewing.
        """
        lines = []

        lines.append("🏥 *PRESCRIPTION*")
        lines.append("")
        lines.append(f"*{prescription.doctor.clinic_name or 'Medical Clinic'}*")
        lines.append(f"Dr. {prescription.doctor.name}")
        lines.append(f"Reg: {prescription.doctor.registration_number}")
        lines.append("")
        lines.append(f"👤 Patient: {prescription.patient.name}")
        lines.append(f"📅 Date: {prescription.date_prescribed.strftime('%d %b %Y')}")

        if prescription.diagnosis:
            lines.append(f"🩺 Diagnosis: {prescription.diagnosis}")

        lines.append("")
        lines.append("💊 *MEDICATIONS*")
        lines.append("")

        for idx, item in enumerate(prescription.items, 1):
            lines.append(f"{idx}. *{item.drug_name} {item.strength}*")

            dosage = PrescriptionFormatter._format_dosage(item)
            lines.append(f"   {dosage}")
            lines.append(f"   Qty: {item.quantity} {item.quantity_unit}")

            if item.instructions:
                lines.append(f"   ℹ️  {item.instructions}")

            lines.append("")

        if prescription.advice:
            lines.append("📋 *ADVICE*")
            advice_lines = prescription.advice.split('\n')
            for line in advice_lines:
                lines.append(line.strip())
            lines.append("")

        if prescription.warnings:
            lines.append("⚠️  *IMPORTANT*")
            for warning in prescription.warnings[:3]:
                lines.append(f"• {warning}")

        lines.append("")
        lines.append(f"_Prescription ID: {prescription.prescription_id}_")

        return "\n".join(lines)


class ValidationFormatter:
    """Format validation results for display."""

    @staticmethod
    def format_validation_alerts(validation_result) -> list:
        """
        Format validation result as user-friendly alerts.

        Returns list of formatted alert strings.
        """
        alerts = []

        # Errors (blocking)
        for error in validation_result.errors:
            alerts.append(f"❌ ERROR: {error}")

        # Warnings
        for warning in validation_result.warnings:
            alerts.append(f"⚠️  {warning}")

        # Interactions
        for interaction in validation_result.interactions:
            if interaction['severity'] == 'major':
                alerts.append(
                    f"⚠️  INTERACTION: {interaction['drug1']} + {interaction['drug2']} "
                    f"- {interaction['description']}"
                )

        # Dosing issues
        for issue in validation_result.dosing_issues:
            if issue['severity'] == 'error':
                alerts.append(f"❌ DOSING: {issue['description']}")
            else:
                alerts.append(f"✅ DOSING: {issue['drug']} - {issue['description']}")

        # Savings opportunities
        if hasattr(validation_result, 'cost_savings') and validation_result.cost_savings:
            for saving in validation_result.cost_savings:
                alerts.append(
                    f"💰 SAVINGS: {saving['alternative']} saves ₹{saving['amount']}/month "
                    f"vs {saving['original']}"
                )

        return alerts


# Example usage
if __name__ == "__main__":
    from .models import (
        Prescription, PrescriptionItem, PatientInfo, DoctorInfo,
        Dosage, DosageForm, Frequency, RouteOfAdministration
    )
    from datetime import datetime

    # Create sample prescription
    patient = PatientInfo(
        patient_id="PAT-2024-1234",
        mrn="MRN-2024-1234",
        name="Rahul Sharma",
        age=45,
        gender="M",
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Shailesh Kumar",
        qualifications="MD, MBBS",
        specialization="General Medicine",
        registration_number="MCI-12345",
        phone="+91-9876543210",
        clinic_name="DocAssist Clinic",
    )

    items = [
        PrescriptionItem(
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
        ),
        PrescriptionItem(
            drug_name="Amlodipine",
            strength="5mg",
            dosage_form=DosageForm.TABLET,
            dosage=Dosage(
                dose="1 tablet",
                frequency=Frequency.OD,
                frequency_detail="0-0-1",
                duration_days=30,
                route=RouteOfAdministration.ORAL,
                timing="at bedtime",
            ),
            quantity=30,
            quantity_unit="tablets",
            item_sequence=2,
        ),
    ]

    prescription = Prescription(
        prescription_id=f"RX-{datetime.utcnow().strftime('%Y%m%d')}-12345678",
        patient=patient,
        doctor=doctor,
        items=items,
        diagnosis="Type 2 Diabetes Mellitus with Hypertension",
        advice="""• Check blood sugar fasting weekly
• Low salt, low sugar diet
• Walk 30 minutes daily
• Follow up after 1 month with HbA1c""",
        warnings=["Alcohol", "Grapefruit juice"],
        created_by="doctor",
    )

    # Format as text
    print(PrescriptionFormatter.format_text(prescription))
    print("\n" + "="*62 + "\n")

    # Format for WhatsApp
    print(PrescriptionFormatter.format_whatsapp(prescription))
