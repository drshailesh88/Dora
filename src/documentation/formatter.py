"""Document Formatters for Clinical Documentation.

Export documentation to various formats: text, JSON, PDF, EMR-compatible formats.
"""

import json
from datetime import datetime
from io import BytesIO
from typing import Any, Union

from .models import (
    DischargeSummary,
    MedicalCertificate,
    OperativeNote,
    ReferralLetter,
    SOAPNote,
)


class TextFormatter:
    """Format documents as plain text."""

    def format_soap_note(self, soap: SOAPNote) -> str:
        """Format SOAP note as text.

        Args:
            soap: SOAP note

        Returns:
            Formatted text
        """
        lines = [
            "=" * 70,
            "CLINICAL NOTE - SOAP FORMAT".center(70),
            "=" * 70,
            "",
        ]

        # Header
        lines.append(
            f"Patient: {soap.patient.name} ({soap.patient.gender[0]}, {soap.patient.age}y)"
        )
        if soap.patient.mrn:
            lines.append(f"MRN: {soap.patient.mrn}")
        lines.append(f"Date: {soap.date.strftime('%d-%b-%Y')}")
        lines.append(f"Provider: {soap.provider.name}")
        lines.append("")

        # Subjective
        lines.append("-" * 70)
        lines.append("SUBJECTIVE:")
        lines.append("-" * 70)
        lines.append(f"Chief Complaint: {soap.chief_complaint}")
        lines.append("")

        lines.append("History of Present Illness:")
        lines.append(soap.history_present_illness)
        lines.append("")

        if soap.past_medical_history:
            lines.append(f"Past Medical History: {soap.past_medical_history}")
            lines.append("")

        if soap.medications:
            lines.append("Current Medications:")
            for med in soap.medications:
                lines.append(
                    f"  - {med.name} {med.dosage} {med.route} {med.frequency}"
                )
            lines.append("")

        if soap.allergies:
            lines.append(f"Allergies: {', '.join(soap.allergies)}")
            lines.append("")

        if soap.social_history:
            lines.append(f"Social History: {soap.social_history}")

        if soap.review_of_systems:
            lines.append("")
            lines.append("Review of Systems:")
            lines.append(soap.review_of_systems)

        # Objective
        lines.append("")
        lines.append("-" * 70)
        lines.append("OBJECTIVE:")
        lines.append("-" * 70)

        if soap.vitals:
            lines.append(f"Vitals: {soap.vitals}")
            lines.append("")

        if soap.general_exam:
            lines.append(f"General: {soap.general_exam}")

        for system, findings in soap.system_exams.items():
            lines.append(f"{system.capitalize()}: {findings}")

        if soap.investigations:
            lines.append("")
            lines.append("Investigations:")
            for inv in soap.investigations:
                if inv.value and inv.unit:
                    result = f"{inv.value} {inv.unit}"
                    if inv.flag:
                        result += f" ({inv.flag})"
                    lines.append(f"  - {inv.name}: {result}")
                elif inv.result:
                    lines.append(f"  - {inv.name}: {inv.result}")

        # Assessment
        lines.append("")
        lines.append("-" * 70)
        lines.append("ASSESSMENT:")
        lines.append("-" * 70)
        for i, diag in enumerate(soap.diagnoses, 1):
            if diag.icd10_code:
                lines.append(f"{i}. {diag.description} ({diag.icd10_code})")
            else:
                lines.append(f"{i}. {diag.description}")

        if soap.differential_diagnoses:
            lines.append("")
            lines.append("Differential Diagnoses:")
            for ddx in soap.differential_diagnoses:
                lines.append(f"  - {ddx}")

        # Plan
        lines.append("")
        lines.append("-" * 70)
        lines.append("PLAN:")
        lines.append("-" * 70)

        if soap.plan_medications:
            lines.append("Medications:")
            for med in soap.plan_medications:
                lines.append(
                    f"  - {med.name} {med.dosage} {med.route} {med.frequency}"
                )
                if med.duration:
                    lines.append(f"    Duration: {med.duration}")
            lines.append("")

        if soap.plan_investigations:
            lines.append("Investigations to order:")
            for inv in soap.plan_investigations:
                lines.append(f"  - {inv}")
            lines.append("")

        if soap.plan_procedures:
            lines.append("Procedures:")
            for proc in soap.plan_procedures:
                lines.append(f"  - {proc}")
            lines.append("")

        if soap.plan_referrals:
            lines.append("Referrals:")
            for ref in soap.plan_referrals:
                lines.append(f"  - {ref}")
            lines.append("")

        if soap.plan_followup:
            lines.append(f"Follow-up: {soap.plan_followup}")

        if soap.plan_patient_education:
            lines.append("")
            lines.append("Patient Education:")
            lines.append(soap.plan_patient_education)

        # Footer
        lines.append("")
        lines.append("-" * 70)
        if soap.signed_at:
            lines.append(f"Signed: {soap.provider.name}")
            lines.append(f"Time: {soap.signed_at.strftime('%d-%b-%Y %H:%M')}")
        else:
            lines.append("[DRAFT - NOT SIGNED]")
        lines.append("=" * 70)

        return "\n".join(lines)

    def format_discharge_summary(self, discharge: DischargeSummary) -> str:
        """Format discharge summary as text."""
        lines = ["DISCHARGE SUMMARY", "=" * 70, ""]

        lines.append(
            f"Patient: {discharge.patient.name} ({discharge.patient.age}/{discharge.patient.gender[0]})"
        )
        if discharge.patient.mrn:
            lines.append(f"MRN: {discharge.patient.mrn}")
        lines.append(
            f"Admission: {discharge.admission_date.strftime('%d-%b-%Y')} | Discharge: {discharge.discharge_date.strftime('%d-%b-%Y')}"
        )
        if discharge.length_of_stay:
            lines.append(f"Length of Stay: {discharge.length_of_stay} days")
        lines.append(f"Provider: {discharge.provider.name}")
        lines.append("")

        lines.append(f"Chief Complaint: {discharge.chief_complaint}")
        lines.append(f"Admitting Diagnosis: {discharge.admitting_diagnosis}")
        lines.append("")

        lines.append("Final Diagnosis:")
        for diag in discharge.final_diagnosis:
            if diag.icd10_code:
                lines.append(f"  - {diag.description} ({diag.icd10_code})")
            else:
                lines.append(f"  - {diag.description}")
        lines.append("")

        lines.append("Hospital Course:")
        lines.append(discharge.hospital_course)
        lines.append("")

        if discharge.procedures_performed:
            lines.append("Procedures Performed:")
            for proc in discharge.procedures_performed:
                lines.append(f"  - {proc}")
            lines.append("")

        lines.append(f"Condition at Discharge: {discharge.condition_at_discharge}")
        lines.append("")

        if discharge.discharge_medications:
            lines.append("Discharge Medications:")
            for med in discharge.discharge_medications:
                lines.append(
                    f"  - {med.name} {med.dosage} {med.route} {med.frequency}"
                )
            lines.append("")

        lines.append("Discharge Instructions:")
        lines.append(discharge.discharge_instructions)
        lines.append("")

        if discharge.warning_signs:
            lines.append("Warning Signs (Return if you experience):")
            for sign in discharge.warning_signs:
                lines.append(f"  - {sign}")
            lines.append("")

        lines.append("Follow-up:")
        lines.append(discharge.followup_instructions)

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


class JSONFormatter:
    """Format documents as JSON."""

    def format_any(
        self,
        document: Union[SOAPNote, DischargeSummary, ReferralLetter, MedicalCertificate, OperativeNote],
    ) -> str:
        """Format any document as JSON.

        Args:
            document: Document to format

        Returns:
            JSON string
        """
        return document.model_dump_json(indent=2, exclude_none=True)


class PDFFormatter:
    """Format documents as PDF."""

    def __init__(self):
        """Initialize PDF formatter."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            self.reportlab_available = True
            self._reportlab_imports = {
                "colors": colors,
                "letter": letter,
                "getSampleStyleSheet": getSampleStyleSheet,
                "ParagraphStyle": ParagraphStyle,
                "inch": inch,
                "SimpleDocTemplate": SimpleDocTemplate,
                "Paragraph": Paragraph,
                "Spacer": Spacer,
                "Table": Table,
                "TableStyle": TableStyle,
                "PageBreak": PageBreak,
            }
        except ImportError:
            self.reportlab_available = False
            self._reportlab_imports = None

    def format_soap_note(self, soap: SOAPNote) -> bytes:
        """Format SOAP note as PDF.

        Args:
            soap: SOAP note

        Returns:
            PDF bytes
        """
        if not self.reportlab_available:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")

        buffer = BytesIO()
        doc = self._reportlab_imports["SimpleDocTemplate"](buffer, pagesize=self._reportlab_imports["letter"])
        styles = self._reportlab_imports["getSampleStyleSheet"]()

        # Build PDF content
        story = []

        # Title
        title_style = self._reportlab_imports["ParagraphStyle"](
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=self._reportlab_imports["colors"].HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        story.append(self._reportlab_imports["Paragraph"]("CLINICAL NOTE - SOAP FORMAT", title_style))

        # Patient info
        story.append(
            self._reportlab_imports["Paragraph"](
                f"<b>Patient:</b> {soap.patient.name} ({soap.patient.gender[0]}, {soap.patient.age}y)",
                styles["Normal"],
            )
        )
        story.append(
            self._reportlab_imports["Paragraph"](f"<b>Date:</b> {soap.date.strftime('%d-%b-%Y')}", styles["Normal"])
        )
        story.append(self._reportlab_imports["Paragraph"](f"<b>Provider:</b> {soap.provider.name}", styles["Normal"]))
        story.append(self._reportlab_imports["Spacer"](1, 0.2 * self._reportlab_imports["inch"]))

        # SOAP sections
        sections = [
            ("SUBJECTIVE", self._build_soap_subjective_text(soap)),
            ("OBJECTIVE", self._build_soap_objective_text(soap)),
            ("ASSESSMENT", self._build_soap_assessment_text(soap)),
            ("PLAN", self._build_soap_plan_text(soap)),
        ]

        for section_title, section_text in sections:
            story.append(self._reportlab_imports["Paragraph"](f"<b>{section_title}</b>", styles["Heading2"]))
            story.append(self._reportlab_imports["Paragraph"](section_text, styles["Normal"]))
            story.append(self._reportlab_imports["Spacer"](1, 0.2 * self._reportlab_imports["inch"]))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_soap_subjective_text(self, soap: SOAPNote) -> str:
        """Build subjective section text for PDF."""
        parts = [f"<b>Chief Complaint:</b> {soap.chief_complaint}<br/>"]
        parts.append(f"<b>HPI:</b> {soap.history_present_illness}<br/>")

        if soap.medications:
            meds = ", ".join([m.name for m in soap.medications])
            parts.append(f"<b>Medications:</b> {meds}<br/>")

        if soap.allergies:
            parts.append(f"<b>Allergies:</b> {', '.join(soap.allergies)}<br/>")

        return "".join(parts)

    def _build_soap_objective_text(self, soap: SOAPNote) -> str:
        """Build objective section text for PDF."""
        parts = []

        if soap.vitals:
            parts.append(f"<b>Vitals:</b> {soap.vitals}<br/>")

        if soap.general_exam:
            parts.append(f"<b>General:</b> {soap.general_exam}<br/>")

        return "".join(parts)

    def _build_soap_assessment_text(self, soap: SOAPNote) -> str:
        """Build assessment section text for PDF."""
        diagnoses = []
        for i, diag in enumerate(soap.diagnoses, 1):
            if diag.icd10_code:
                diagnoses.append(f"{i}. {diag.description} ({diag.icd10_code})")
            else:
                diagnoses.append(f"{i}. {diag.description}")

        return "<br/>".join(diagnoses)

    def _build_soap_plan_text(self, soap: SOAPNote) -> str:
        """Build plan section text for PDF."""
        parts = []

        if soap.plan_medications:
            parts.append("<b>Medications:</b><br/>")
            for med in soap.plan_medications:
                parts.append(f"  - {med.name} {med.dosage} {med.frequency}<br/>")

        if soap.plan_followup:
            parts.append(f"<br/><b>Follow-up:</b> {soap.plan_followup}")

        return "".join(parts)


class EMRFormatter:
    """Format documents for EMR integration."""

    def format_for_docassist_emr(self, document: Any) -> dict[str, Any]:
        """Format document for DocAssist EMR.

        Args:
            document: Clinical document

        Returns:
            EMR-compatible dictionary
        """
        # TODO: Map to DocAssist EMR schema
        return document.model_dump()

    def format_as_hl7(self, document: Any) -> str:
        """Format document as HL7 message.

        Args:
            document: Clinical document

        Returns:
            HL7 message string
        """
        # TODO: Implement HL7 formatting
        raise NotImplementedError("HL7 formatting not yet implemented")

    def format_as_fhir(self, document: Any) -> dict[str, Any]:
        """Format document as FHIR resource.

        Args:
            document: Clinical document

        Returns:
            FHIR resource dictionary
        """
        # TODO: Implement FHIR formatting
        raise NotImplementedError("FHIR formatting not yet implemented")


# Convenience functions
def to_text(document: Any) -> str:
    """Convert document to text."""
    formatter = TextFormatter()

    if isinstance(document, SOAPNote):
        return formatter.format_soap_note(document)
    elif isinstance(document, DischargeSummary):
        return formatter.format_discharge_summary(document)
    else:
        return str(document)


def to_json(document: Any) -> str:
    """Convert document to JSON."""
    formatter = JSONFormatter()
    return formatter.format_any(document)


def to_pdf(document: Any) -> bytes:
    """Convert document to PDF."""
    formatter = PDFFormatter()

    if isinstance(document, SOAPNote):
        return formatter.format_soap_note(document)
    else:
        raise NotImplementedError(f"PDF formatting not implemented for {type(document)}")
