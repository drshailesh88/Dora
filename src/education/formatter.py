"""
Education Content Formatters

Formats patient education content for various delivery methods:
PDF, HTML, plain text, WhatsApp, SMS, email.
"""

import io
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        Image as RLImage,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import (
    PatientHandout,
    MedicationGuide,
    ConditionExplainer,
    ProcedurePrep,
    PostCareGuide,
    DeliveryFormat,
)


class PDFFormatter:
    """Formats patient education content as PDF."""

    def __init__(self):
        """Initialize PDF formatter."""
        self.page_size = A4
        self.margin = 0.75 * inch

        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            alignment=TA_CENTER,
        ))

        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=6,
            spaceBefore=12,
        ))

        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ))

        # Bullet style
        self.styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=self.styles['BodyText'],
            fontSize=11,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4,
        ))

        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.red,
            leftIndent=10,
            spaceAfter=6,
        ))

        # Large font style for accessibility
        self.styles.add(ParagraphStyle(
            name='LargeBody',
            parent=self.styles['BodyText'],
            fontSize=14,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ))

    def generate_pdf(
        self,
        handout: PatientHandout,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF from patient handout.

        Args:
            handout: Patient handout
            output_path: Optional file path to save PDF

        Returns:
            PDF bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation")

        # Create buffer or file
        if output_path:
            buffer = output_path
        else:
            buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Build content
        story = []

        # Header
        story.extend(self._build_header(handout))
        story.append(Spacer(1, 0.2 * inch))

        # Content based on type
        if handout.medication_guide:
            story.extend(self._build_medication_guide(handout.medication_guide, handout.large_font))
        elif handout.condition_explainer:
            story.extend(self._build_condition_explainer(handout.condition_explainer, handout.large_font))
        elif handout.procedure_prep:
            story.extend(self._build_procedure_prep(handout.procedure_prep, handout.large_font))
        elif handout.post_care_guide:
            story.extend(self._build_post_care_guide(handout.post_care_guide, handout.large_font))
        elif handout.custom_sections:
            story.extend(self._build_custom_sections(handout.custom_sections, handout.large_font))

        # Footer
        story.extend(self._build_footer(handout))

        # Build PDF
        doc.build(story)

        # Return bytes if using BytesIO
        if isinstance(buffer, io.BytesIO):
            return buffer.getvalue()

        return b""

    def _build_header(self, handout: PatientHandout) -> list:
        """Build PDF header."""
        elements = []
        style = self.styles['CustomTitle']

        # Title
        elements.append(Paragraph(handout.title, style))

        # Patient info if available
        if handout.patient_name or handout.doctor_name:
            info_lines = []
            if handout.patient_name:
                info_lines.append(f"Patient: {handout.patient_name}")
            if handout.doctor_name:
                info_lines.append(f"Doctor: {handout.doctor_name}")
            if handout.clinic_name:
                info_lines.append(f"Clinic: {handout.clinic_name}")

            info_text = " | ".join(info_lines)
            elements.append(Paragraph(info_text, self.styles['Normal']))

        # Date
        date_str = handout.generated_at.strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated: {date_str}", self.styles['Normal']))

        return elements

    def _build_medication_guide(self, guide: MedicationGuide, large_font: bool) -> list:
        """Build medication guide content."""
        elements = []
        body_style = self.styles['LargeBody'] if large_font else self.styles['CustomBody']
        heading_style = self.styles['CustomHeading']

        # Medication name
        if guide.brand_names:
            brand_text = f" ({', '.join(guide.brand_names)})"
        else:
            brand_text = ""
        elements.append(Paragraph(f"<b>{guide.generic_name}{brand_text}</b>", body_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Purpose
        elements.append(Paragraph("What is this medication for?", heading_style))
        elements.append(Paragraph(guide.purpose, body_style))
        elements.append(Spacer(1, 0.1 * inch))

        # How to take
        elements.append(Paragraph("How to take", heading_style))
        elements.append(Paragraph(
            f"<b>Dose:</b> {guide.dosage.dose}<br/>"
            f"<b>Frequency:</b> {guide.dosage.frequency}<br/>"
            f"{f'<b>Timing:</b> {guide.dosage.timing}<br/>' if guide.dosage.timing else ''}",
            body_style
        ))

        if guide.instructions:
            for instr in guide.instructions:
                elements.append(Paragraph(f"• {instr}", body_style))

        elements.append(Spacer(1, 0.1 * inch))

        # Side effects
        if guide.common_side_effects:
            elements.append(Paragraph("Common Side Effects", heading_style))
            for se in guide.common_side_effects:
                desc = f" - {se.description}" if se.description else ""
                elements.append(Paragraph(f"• {se.name}{desc}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Warning signs
        if guide.warning_signs:
            elements.append(Paragraph("⚠️ When to Call Your Doctor", heading_style))
            for ws in guide.warning_signs:
                elements.append(Paragraph(
                    f"• <b>{ws.symptom}:</b> {ws.action}",
                    self.styles['Warning']
                ))
            elements.append(Spacer(1, 0.1 * inch))

        # Storage
        elements.append(Paragraph("Storage", heading_style))
        elements.append(Paragraph(guide.storage_instructions, body_style))

        return elements

    def _build_condition_explainer(self, explainer: ConditionExplainer, large_font: bool) -> list:
        """Build condition explainer content."""
        elements = []
        body_style = self.styles['LargeBody'] if large_font else self.styles['CustomBody']
        heading_style = self.styles['CustomHeading']

        # What is it?
        elements.append(Paragraph("What is it?", heading_style))
        elements.append(Paragraph(explainer.simple_explanation, body_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Symptoms
        if explainer.common_symptoms:
            elements.append(Paragraph("Common Symptoms", heading_style))
            for symptom in explainer.common_symptoms:
                elements.append(Paragraph(f"• {symptom}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Causes
        if explainer.causes:
            elements.append(Paragraph("Causes", heading_style))
            for cause in explainer.causes:
                elements.append(Paragraph(f"• {cause}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Treatment
        if explainer.treatment_options:
            elements.append(Paragraph("Treatment Options", heading_style))
            for treatment in explainer.treatment_options:
                elements.append(Paragraph(f"• {treatment}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Lifestyle changes
        if explainer.lifestyle_changes:
            elements.append(Paragraph("Lifestyle Changes", heading_style))
            for change in explainer.lifestyle_changes:
                elements.append(Paragraph(f"✓ {change}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Do's and Don'ts
        if explainer.dos_donts:
            elements.append(Paragraph("Do's and Don'ts", heading_style))

            # Create table for dos and donts
            dos_list = "<br/>".join([f"✓ {do}" for do in explainer.dos_donts.dos])
            donts_list = "<br/>".join([f"✗ {dont}" for dont in explainer.dos_donts.donts])

            table_data = [
                [Paragraph("<b>DO</b>", body_style), Paragraph("<b>DON'T</b>", body_style)],
                [Paragraph(dos_list, body_style), Paragraph(donts_list, body_style)],
            ]

            table = Table(table_data, colWidths=[3 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0fe')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _build_procedure_prep(self, prep: ProcedurePrep, large_font: bool) -> list:
        """Build procedure prep content."""
        elements = []
        body_style = self.styles['LargeBody'] if large_font else self.styles['CustomBody']
        heading_style = self.styles['CustomHeading']

        # Preparation timeline
        if prep.days_before_instructions:
            elements.append(Paragraph("Preparation Instructions", heading_style))
            for day_instr in prep.days_before_instructions:
                elements.append(Paragraph(f"<b>{day_instr['day']}</b>", body_style))
                for instr in day_instr.get('instructions', []):
                    elements.append(Paragraph(f"• {instr}", body_style))
                elements.append(Spacer(1, 0.05 * inch))

        # What to bring
        if prep.what_to_bring:
            elements.append(Paragraph("What to Bring", heading_style))
            for item in prep.what_to_bring:
                elements.append(Paragraph(f"• {item}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _build_post_care_guide(self, guide: PostCareGuide, large_font: bool) -> list:
        """Build post-care guide content."""
        elements = []
        body_style = self.styles['LargeBody'] if large_font else self.styles['CustomBody']
        heading_style = self.styles['CustomHeading']

        # Recovery timeline
        if guide.recovery_timeline:
            elements.append(Paragraph("Recovery Timeline", heading_style))
            for timeline in guide.recovery_timeline:
                elements.append(Paragraph(
                    f"<b>{timeline['period']}:</b> {timeline['expect']}",
                    body_style
                ))
            elements.append(Spacer(1, 0.1 * inch))

        # Activity restrictions
        if guide.activity_restrictions:
            elements.append(Paragraph("Activity Restrictions", heading_style))
            for restriction in guide.activity_restrictions:
                elements.append(Paragraph(f"• {restriction}", body_style))
            elements.append(Spacer(1, 0.1 * inch))

        # Warning signs
        if guide.warning_signs:
            elements.append(Paragraph("⚠️ When to Call Your Doctor", heading_style))
            for ws in guide.warning_signs:
                elements.append(Paragraph(
                    f"• <b>{ws.symptom}:</b> {ws.action}",
                    self.styles['Warning']
                ))

        return elements

    def _build_custom_sections(self, sections: list, large_font: bool) -> list:
        """Build custom sections."""
        elements = []
        body_style = self.styles['LargeBody'] if large_font else self.styles['CustomBody']
        heading_style = self.styles['CustomHeading']

        for section in sections:
            elements.append(Paragraph(section.get('title', ''), heading_style))
            elements.append(Paragraph(section.get('content', ''), body_style))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _build_footer(self, handout: PatientHandout) -> list:
        """Build PDF footer."""
        elements = []

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("_" * 80, self.styles['Normal']))

        # Contact information
        if handout.contact_information:
            contact_lines = []
            for key, value in handout.contact_information.items():
                contact_lines.append(f"{key}: {value}")
            contact_text = " | ".join(contact_lines)
            elements.append(Paragraph(contact_text, self.styles['Normal']))

        # Emergency contacts
        if handout.emergency_contacts:
            elements.append(Paragraph("<b>Emergency Contacts:</b>", self.styles['Normal']))
            for key, value in handout.emergency_contacts.items():
                elements.append(Paragraph(f"{key}: {value}", self.styles['Normal']))

        # Disclaimer
        elements.append(Spacer(1, 0.1 * inch))
        disclaimer = (
            "<i>This information is for educational purposes only and does not replace "
            "professional medical advice. Always consult your healthcare provider.</i>"
        )
        elements.append(Paragraph(disclaimer, self.styles['Normal']))

        return elements


class HTMLFormatter:
    """Formats patient education content as HTML."""

    def generate_html(self, handout: PatientHandout) -> str:
        """
        Generate HTML from patient handout.

        Args:
            handout: Patient handout

        Returns:
            HTML string
        """
        html_parts = [
            self._get_html_header(handout),
            self._get_html_body(handout),
            self._get_html_footer(handout),
        ]

        return "\n".join(html_parts)

    def _get_html_header(self, handout: PatientHandout) -> str:
        """Get HTML header."""
        font_size = "16px" if handout.large_font else "14px"

        return f"""<!DOCTYPE html>
<html lang="{handout.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{handout.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-size: {font_size};
        }}
        h1 {{ color: #1a73e8; text-align: center; }}
        h2 {{ color: #1a73e8; margin-top: 20px; }}
        .warning {{ color: #d32f2f; font-weight: bold; }}
        .dos-donts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .do {{ background: #e8f5e9; padding: 15px; border-radius: 5px; }}
        .dont {{ background: #ffebee; padding: 15px; border-radius: 5px; }}
        ul {{ padding-left: 20px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #e0e0e0; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>{handout.title}</h1>
"""

    def _get_html_body(self, handout: PatientHandout) -> str:
        """Get HTML body content."""
        if handout.medication_guide:
            return self._format_medication_guide_html(handout.medication_guide)
        elif handout.condition_explainer:
            return self._format_condition_explainer_html(handout.condition_explainer)
        elif handout.custom_sections:
            return self._format_custom_sections_html(handout.custom_sections)
        return ""

    def _format_medication_guide_html(self, guide: MedicationGuide) -> str:
        """Format medication guide as HTML."""
        html = f"""
    <h2>What is this medication for?</h2>
    <p>{guide.purpose}</p>

    <h2>How to take</h2>
    <ul>
        <li><strong>Dose:</strong> {guide.dosage.dose}</li>
        <li><strong>Frequency:</strong> {guide.dosage.frequency}</li>
        {f'<li><strong>Timing:</strong> {guide.dosage.timing}</li>' if guide.dosage.timing else ''}
    </ul>
"""

        if guide.common_side_effects:
            html += "\n    <h2>Common Side Effects</h2>\n    <ul>\n"
            for se in guide.common_side_effects:
                html += f"        <li>{se.name}</li>\n"
            html += "    </ul>\n"

        if guide.warning_signs:
            html += '\n    <h2 class="warning">⚠️ When to Call Your Doctor</h2>\n    <ul>\n'
            for ws in guide.warning_signs:
                html += f'        <li class="warning">{ws.symptom}: {ws.action}</li>\n'
            html += "    </ul>\n"

        return html

    def _format_condition_explainer_html(self, explainer: ConditionExplainer) -> str:
        """Format condition explainer as HTML."""
        html = f"""
    <h2>What is it?</h2>
    <p>{explainer.simple_explanation}</p>
"""

        if explainer.common_symptoms:
            html += "\n    <h2>Symptoms</h2>\n    <ul>\n"
            for symptom in explainer.common_symptoms:
                html += f"        <li>{symptom}</li>\n"
            html += "    </ul>\n"

        if explainer.dos_donts:
            html += '\n    <h2>Do\'s and Don\'ts</h2>\n    <div class="dos-donts">\n'
            html += '        <div class="do">\n            <h3>DO</h3>\n            <ul>\n'
            for do in explainer.dos_donts.dos:
                html += f"                <li>{do}</li>\n"
            html += '            </ul>\n        </div>\n'

            html += '        <div class="dont">\n            <h3>DON\'T</h3>\n            <ul>\n'
            for dont in explainer.dos_donts.donts:
                html += f"                <li>{dont}</li>\n"
            html += '            </ul>\n        </div>\n    </div>\n'

        return html

    def _format_custom_sections_html(self, sections: list) -> str:
        """Format custom sections as HTML."""
        html = ""
        for section in sections:
            html += f"""
    <h2>{section.get('title', '')}</h2>
    <p>{section.get('content', '')}</p>
"""
        return html

    def _get_html_footer(self, handout: PatientHandout) -> str:
        """Get HTML footer."""
        footer = '\n    <div class="footer">\n'

        if handout.contact_information:
            footer += "        <p><strong>Contact:</strong> "
            footer += " | ".join([f"{k}: {v}" for k, v in handout.contact_information.items()])
            footer += "</p>\n"

        footer += """        <p><em>This information is for educational purposes only and does not replace professional medical advice.</em></p>
    </div>
</body>
</html>"""

        return footer


class PlainTextFormatter:
    """Formats patient education content as plain text."""

    def generate_text(self, handout: PatientHandout) -> str:
        """
        Generate plain text from patient handout.

        Args:
            handout: Patient handout

        Returns:
            Plain text string
        """
        lines = [
            "=" * 60,
            handout.title.upper().center(60),
            "=" * 60,
            "",
        ]

        # Patient info
        if handout.patient_name:
            lines.append(f"Patient: {handout.patient_name}")
        if handout.doctor_name:
            lines.append(f"Doctor: {handout.doctor_name}")
        lines.append(f"Date: {handout.generated_at.strftime('%B %d, %Y')}")
        lines.append("")

        # Content
        if handout.medication_guide:
            lines.extend(self._format_medication_guide_text(handout.medication_guide))
        elif handout.condition_explainer:
            lines.extend(self._format_condition_explainer_text(handout.condition_explainer))

        # Footer
        lines.extend([
            "",
            "-" * 60,
            "This information is for educational purposes only.",
            "Always consult your healthcare provider.",
            "-" * 60,
        ])

        return "\n".join(lines)

    def _format_medication_guide_text(self, guide: MedicationGuide) -> list:
        """Format medication guide as plain text."""
        lines = [
            f"MEDICATION: {guide.generic_name}",
            "",
            "What is this for?",
            guide.purpose,
            "",
            "How to take:",
            f"  - Dose: {guide.dosage.dose}",
            f"  - Frequency: {guide.dosage.frequency}",
        ]

        if guide.dosage.timing:
            lines.append(f"  - Timing: {guide.dosage.timing}")

        lines.append("")

        if guide.common_side_effects:
            lines.append("Common side effects:")
            for se in guide.common_side_effects:
                lines.append(f"  • {se.name}")
            lines.append("")

        return lines

    def _format_condition_explainer_text(self, explainer: ConditionExplainer) -> list:
        """Format condition explainer as plain text."""
        lines = [
            f"CONDITION: {explainer.condition_name}",
            "",
            "What is it?",
            explainer.simple_explanation,
            "",
        ]

        if explainer.common_symptoms:
            lines.append("Symptoms:")
            for symptom in explainer.common_symptoms:
                lines.append(f"  • {symptom}")
            lines.append("")

        return lines
