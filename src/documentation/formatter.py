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
        from ..emr.models import ClinicalNote as EMRClinicalNote

        # Map documentation models to EMR schema
        if isinstance(document, SOAPNote):
            return {
                "patient_id": int(document.patient.id) if document.patient.id.isdigit() else None,
                "note_type": "soap",
                "note_date": document.date.isoformat(),
                "subjective": self._build_subjective_text(document),
                "objective": self._build_objective_text(document),
                "assessment": self._build_assessment_text(document),
                "plan": self._build_plan_text(document),
                "full_note": TextFormatter().format_soap_note(document),
                "author": document.provider.name,
                "signed": document.status.value == "signed",
                "signed_at": document.signed_at.isoformat() if document.signed_at else None,
            }
        elif isinstance(document, DischargeSummary):
            return {
                "patient_id": int(document.patient.id) if document.patient.id.isdigit() else None,
                "note_type": "discharge",
                "note_date": document.discharge_date.isoformat(),
                "full_note": TextFormatter().format_discharge_summary(document),
                "author": document.provider.name,
                "signed": document.status.value == "signed",
                "signed_at": document.signed_at.isoformat() if document.signed_at else None,
            }
        else:
            # Generic mapping
            return document.model_dump()

    def _build_subjective_text(self, soap: SOAPNote) -> str:
        """Build subjective section for EMR."""
        parts = [f"CC: {soap.chief_complaint}", f"\nHPI: {soap.history_present_illness}"]
        if soap.past_medical_history:
            parts.append(f"\nPMH: {soap.past_medical_history}")
        if soap.medications:
            meds = ", ".join([f"{m.name} {m.dosage}" for m in soap.medications])
            parts.append(f"\nMedications: {meds}")
        if soap.allergies:
            parts.append(f"\nAllergies: {', '.join(soap.allergies)}")
        return "".join(parts)

    def _build_objective_text(self, soap: SOAPNote) -> str:
        """Build objective section for EMR."""
        parts = []
        if soap.vitals:
            parts.append(f"Vitals: {str(soap.vitals)}")
        if soap.general_exam:
            parts.append(f"\nGeneral: {soap.general_exam}")
        for system, findings in soap.system_exams.items():
            parts.append(f"\n{system.title()}: {findings}")
        return "".join(parts)

    def _build_assessment_text(self, soap: SOAPNote) -> str:
        """Build assessment section for EMR."""
        diagnoses = []
        for i, dx in enumerate(soap.diagnoses, 1):
            if dx.icd10_code:
                diagnoses.append(f"{i}. {dx.description} ({dx.icd10_code})")
            else:
                diagnoses.append(f"{i}. {dx.description}")
        return "\n".join(diagnoses)

    def _build_plan_text(self, soap: SOAPNote) -> str:
        """Build plan section for EMR."""
        parts = []
        if soap.plan_medications:
            parts.append("Medications:")
            for med in soap.plan_medications:
                parts.append(f"  - {med.name} {med.dosage} {med.route} {med.frequency}")
        if soap.plan_investigations:
            parts.append("\nInvestigations: " + ", ".join(soap.plan_investigations))
        if soap.plan_followup:
            parts.append(f"\nFollow-up: {soap.plan_followup}")
        return "\n".join(parts)

    def format_as_hl7(self, document: Any) -> str:
        """Format document as HL7 v2.x message.

        Args:
            document: Clinical document

        Returns:
            HL7 message string (ORU^R01 for clinical observations)
        """
        from datetime import datetime

        if isinstance(document, SOAPNote):
            # ORU^R01 - Unsolicited Observation Message
            now = datetime.now().strftime("%Y%m%d%H%M%S")

            # MSH - Message Header
            msh = f"MSH|^~\\&|DORA|DocAssist|EMR|Hospital|{now}||ORU^R01|{document.id}|P|2.5"

            # PID - Patient Identification
            pid = (
                f"PID|1||{document.patient.mrn or document.patient.id}||"
                f"{document.patient.name}||{self._calculate_dob(document.patient.age)}|"
                f"{document.patient.gender[0]}|||{document.patient.address or ''}||"
                f"{document.patient.contact or ''}"
            )

            # PV1 - Patient Visit
            pv1 = f"PV1|1|O|||||{document.provider.name}^{document.provider.qualification or ''}"

            # OBR - Observation Request
            obr = f"OBR|1||{document.id}|SOAP^SOAP Note^LN||{document.date.strftime('%Y%m%d%H%M%S')}"

            # OBX - Observation Results (SOAP sections)
            obx_segments = []
            obx_count = 1

            # Subjective
            obx_segments.append(
                f"OBX|{obx_count}|TX|SUBJ^Subjective^LN||{document.chief_complaint}||||||F"
            )
            obx_count += 1

            # Objective (Vitals)
            if document.vitals:
                if document.vitals.bp_systolic and document.vitals.bp_diastolic:
                    obx_segments.append(
                        f"OBX|{obx_count}|NM|BP^Blood Pressure^LN||"
                        f"{document.vitals.bp_systolic}/{document.vitals.bp_diastolic}|mmHg|||||F"
                    )
                    obx_count += 1
                if document.vitals.heart_rate:
                    obx_segments.append(
                        f"OBX|{obx_count}|NM|HR^Heart Rate^LN||{document.vitals.heart_rate}|bpm|||||F"
                    )
                    obx_count += 1

            # Assessment
            if document.diagnoses:
                dx_text = "; ".join([d.description for d in document.diagnoses])
                obx_segments.append(
                    f"OBX|{obx_count}|TX|ASSESS^Assessment^LN||{dx_text}||||||F"
                )
                obx_count += 1

            # Combine all segments
            return "\r".join([msh, pid, pv1, obr] + obx_segments)
        else:
            raise NotImplementedError(f"HL7 formatting not implemented for {type(document)}")

    def _calculate_dob(self, age: int) -> str:
        """Calculate approximate DOB from age for HL7."""
        from datetime import datetime
        year = datetime.now().year - age
        return f"{year}0101"

    def format_as_fhir(self, document: Any) -> dict[str, Any]:
        """Format document as FHIR R4 resource.

        Args:
            document: Clinical document

        Returns:
            FHIR DiagnosticReport or DocumentReference resource dictionary
        """
        if isinstance(document, SOAPNote):
            # FHIR DiagnosticReport resource for SOAP note
            fhir_resource = {
                "resourceType": "DiagnosticReport",
                "id": document.id,
                "status": "final" if document.status.value == "signed" else "preliminary",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "SOAP",
                        "display": "SOAP Note"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "34117-2",
                        "display": "History and physical note"
                    }],
                    "text": "SOAP Clinical Note"
                },
                "subject": {
                    "reference": f"Patient/{document.patient.id}",
                    "display": document.patient.name
                },
                "effectiveDateTime": document.date.isoformat(),
                "issued": document.created_at.isoformat(),
                "performer": [{
                    "reference": f"Practitioner/{document.provider.name}",
                    "display": document.provider.name
                }],
                "conclusion": self._build_assessment_text(document),
                "presentedForm": [{
                    "contentType": "text/plain",
                    "data": TextFormatter().format_soap_note(document),
                    "title": "SOAP Note"
                }]
            }

            # Add observations for vitals
            if document.vitals:
                observations = []
                if document.vitals.bp_systolic and document.vitals.bp_diastolic:
                    observations.append({
                        "reference": f"Observation/bp-{document.id}",
                        "display": f"Blood Pressure: {document.vitals.bp_systolic}/{document.vitals.bp_diastolic}"
                    })
                if document.vitals.heart_rate:
                    observations.append({
                        "reference": f"Observation/hr-{document.id}",
                        "display": f"Heart Rate: {document.vitals.heart_rate} bpm"
                    })
                if observations:
                    fhir_resource["result"] = observations

            return fhir_resource

        elif isinstance(document, DischargeSummary):
            # FHIR DocumentReference for discharge summary
            return {
                "resourceType": "DocumentReference",
                "id": document.id,
                "status": "current",
                "type": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "18842-5",
                        "display": "Discharge summary"
                    }]
                },
                "subject": {
                    "reference": f"Patient/{document.patient.id}",
                    "display": document.patient.name
                },
                "date": document.discharge_date.isoformat(),
                "author": [{
                    "reference": f"Practitioner/{document.provider.name}",
                    "display": document.provider.name
                }],
                "content": [{
                    "attachment": {
                        "contentType": "text/plain",
                        "data": TextFormatter().format_discharge_summary(document),
                        "title": "Discharge Summary"
                    }
                }],
                "context": {
                    "period": {
                        "start": document.admission_date.isoformat(),
                        "end": document.discharge_date.isoformat()
                    }
                }
            }
        else:
            raise NotImplementedError(f"FHIR formatting not implemented for {type(document)}")


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
