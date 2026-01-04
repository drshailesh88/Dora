"""
CME Certificate Generator

Generates professional PDF certificates for CME credits with QR code verification.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import logging
import io
import qrcode

from .models import (
    CMECertificate,
    CMECredit,
    CMECategory,
    AccreditationBody,
)

logger = logging.getLogger(__name__)


class CertificateGenerator:
    """Generates CME certificates"""

    def __init__(self, output_dir: str = "data/certificates"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_certificate(
        self,
        user_id: str,
        doctor_name: str,
        credits: list[CMECredit],
        registration_number: Optional[str] = None,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
        certificate_title: Optional[str] = None,
    ) -> CMECertificate:
        """
        Generate a CME certificate

        Args:
            user_id: User ID
            doctor_name: Doctor's name
            credits: List of CME credits to include
            registration_number: Medical registration number
            specialty: Specialty
            institution: Institution
            certificate_title: Custom certificate title

        Returns:
            CMECertificate
        """
        if not credits:
            raise ValueError("No credits provided for certificate")

        # Calculate total credits
        total_credits = sum(c.credits for c in credits)

        # Determine category (use highest category)
        category_priority = {
            CMECategory.CATEGORY_1: 3,
            CMECategory.CATEGORY_2: 2,
            CMECategory.CATEGORY_3: 1,
        }
        category = max(
            set(c.category for c in credits),
            key=lambda x: category_priority.get(x, 0)
        )

        # Determine accreditation body
        accreditation_body = credits[0].accreditation_body
        if any(c.accreditation_body == AccreditationBody.MCI for c in credits):
            accreditation_body = AccreditationBody.MCI

        # Collect topics
        all_topics = []
        for credit in credits:
            all_topics.extend(credit.topics)
        topics_covered = list(set(all_topics))  # Unique topics

        # Generate title if not provided
        if not certificate_title:
            if specialty:
                certificate_title = f"Continuing Medical Education in {specialty}"
            else:
                certificate_title = "Continuing Medical Education"

        # Generate description
        description = self._generate_description(credits, total_credits)

        # Create certificate
        certificate = CMECertificate(
            user_id=user_id,
            doctor_name=doctor_name,
            registration_number=registration_number,
            specialty=specialty,
            institution=institution,
            title=certificate_title,
            description=description,
            total_credits=total_credits,
            category=category,
            accreditation_body=accreditation_body,
            topics_covered=topics_covered[:10],  # Limit to top 10
            activities_completed=len(credits),
            issued_date=date.today(),
            valid_until=date.today() + timedelta(days=365 * 5),  # 5 years
            qr_code_data=f"https://docassist.dora/verify/{certificate.certificate_number}",
            verification_url=f"https://docassist.dora/verify/{certificate.certificate_number}",
        )

        # Update verification URL with actual certificate number
        certificate.qr_code_data = f"https://docassist.dora/verify/{certificate.certificate_number}"
        certificate.verification_url = f"https://docassist.dora/verify/{certificate.certificate_number}"

        # Generate PDF
        pdf_path = self._generate_pdf(certificate)
        certificate.pdf_path = str(pdf_path)

        # Add metadata
        certificate.metadata["credit_ids"] = [c.id for c in credits]
        certificate.metadata["generated_at"] = date.today().isoformat()

        logger.info(
            f"Generated certificate {certificate.certificate_number} "
            f"for {doctor_name} with {total_credits} credits"
        )

        return certificate

    def generate_annual_certificate(
        self,
        user_id: str,
        doctor_name: str,
        year: int,
        credits: list[CMECredit],
        registration_number: Optional[str] = None,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
    ) -> CMECertificate:
        """
        Generate annual CME certificate

        Args:
            user_id: User ID
            doctor_name: Doctor's name
            year: Year
            credits: Credits for the year
            registration_number: Registration number
            specialty: Specialty
            institution: Institution

        Returns:
            CMECertificate
        """
        title = f"Annual CME Certificate - {year}"

        return self.generate_certificate(
            user_id=user_id,
            doctor_name=doctor_name,
            credits=credits,
            registration_number=registration_number,
            specialty=specialty,
            institution=institution,
            certificate_title=title,
        )

    def generate_path_certificate(
        self,
        user_id: str,
        doctor_name: str,
        path_title: str,
        credits: list[CMECredit],
        registration_number: Optional[str] = None,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
    ) -> CMECertificate:
        """
        Generate certificate for completing a learning path

        Args:
            user_id: User ID
            doctor_name: Doctor's name
            path_title: Learning path title
            credits: Credits earned in path
            registration_number: Registration number
            specialty: Specialty
            institution: Institution

        Returns:
            CMECertificate
        """
        title = f"Certificate of Completion - {path_title}"

        return self.generate_certificate(
            user_id=user_id,
            doctor_name=doctor_name,
            credits=credits,
            registration_number=registration_number,
            specialty=specialty,
            institution=institution,
            certificate_title=title,
        )

    def _generate_description(self, credits: list[CMECredit], total_credits: float) -> str:
        """
        Generate certificate description

        Args:
            credits: Credits
            total_credits: Total credits

        Returns:
            Description text
        """
        activity_types = set(c.activity_type for c in credits)

        description_parts = [
            f"This certifies that the above-named physician has successfully completed "
            f"{total_credits:.1f} hours of Continuing Medical Education."
        ]

        if len(activity_types) > 1:
            description_parts.append(
                f"The learning activities included {len(credits)} different educational experiences "
                f"covering various aspects of medical knowledge and clinical practice."
            )
        else:
            description_parts.append(
                f"The learning was achieved through {len(credits)} educational activities."
            )

        description_parts.append(
            "This certificate demonstrates the physician's commitment to lifelong learning "
            "and staying current with medical advances."
        )

        return " ".join(description_parts)

    def _generate_pdf(self, certificate: CMECertificate) -> Path:
        """
        Generate PDF certificate

        Args:
            certificate: Certificate data

        Returns:
            Path to PDF file
        """
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.pdfgen import canvas
        except ImportError:
            logger.warning("reportlab not installed, creating text-based certificate")
            return self._generate_text_certificate(certificate)

        # Output file
        filename = f"{certificate.certificate_number}.pdf"
        filepath = self.output_dir / filename

        # Create PDF
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(A4),
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )

        # Container for elements
        elements = []

        # Styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=32,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica',
        )

        name_style = ParagraphStyle(
            'CustomName',
            parent=styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#2b6cb0'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica',
        )

        # Header
        elements.append(Spacer(1, 0.5*inch))

        # Title
        elements.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
        elements.append(Paragraph("Continuing Medical Education", subtitle_style))

        elements.append(Spacer(1, 0.3*inch))

        # This certifies that
        elements.append(Paragraph("This is to certify that", body_style))

        elements.append(Spacer(1, 0.2*inch))

        # Doctor name
        elements.append(Paragraph(f"<b>{certificate.doctor_name}</b>", name_style))

        if certificate.registration_number:
            elements.append(
                Paragraph(
                    f"Registration No: {certificate.registration_number}",
                    body_style
                )
            )

        if certificate.institution:
            elements.append(Paragraph(f"{certificate.institution}", body_style))

        elements.append(Spacer(1, 0.3*inch))

        # Description
        elements.append(Paragraph(certificate.description, body_style))

        elements.append(Spacer(1, 0.2*inch))

        # Credits table
        credit_data = [
            ["CME Credits", f"{certificate.total_credits:.1f} hours"],
            ["Category", certificate.category.value.replace("_", " ").title()],
            ["Activities", str(certificate.activities_completed)],
            ["Valid Until", certificate.valid_until.strftime("%B %d, %Y")],
        ]

        if certificate.specialty:
            credit_data.insert(1, ["Specialty", certificate.specialty])

        credit_table = Table(credit_data, colWidths=[2.5*inch, 2.5*inch])
        credit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ]))

        elements.append(credit_table)

        elements.append(Spacer(1, 0.3*inch))

        # QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(certificate.qr_code_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save QR code to bytes
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Add QR code image
        qr_image = Image(qr_buffer, width=1*inch, height=1*inch)
        elements.append(qr_image)

        elements.append(Spacer(1, 0.1*inch))

        # Certificate number and verification
        elements.append(
            Paragraph(
                f"Certificate No: <b>{certificate.certificate_number}</b>",
                body_style
            )
        )
        elements.append(
            Paragraph(
                f"Issued: {certificate.issued_date.strftime('%B %d, %Y')}",
                body_style
            )
        )
        elements.append(
            Paragraph(
                f"Verify at: {certificate.verification_url}",
                body_style
            )
        )

        # Build PDF
        doc.build(elements)

        logger.info(f"Generated PDF certificate: {filepath}")
        return filepath

    def _generate_text_certificate(self, certificate: CMECertificate) -> Path:
        """
        Generate text-based certificate (fallback if reportlab not available)

        Args:
            certificate: Certificate data

        Returns:
            Path to text file
        """
        filename = f"{certificate.certificate_number}.txt"
        filepath = self.output_dir / filename

        content = f"""
{'='*80}
                    CERTIFICATE OF COMPLETION
                   Continuing Medical Education
{'='*80}

This is to certify that

                        {certificate.doctor_name}
"""
        if certificate.registration_number:
            content += f"                  Registration No: {certificate.registration_number}\n"

        if certificate.institution:
            content += f"                        {certificate.institution}\n"

        content += f"""
{certificate.description}

{'='*80}
CME Credits:        {certificate.total_credits:.1f} hours
Category:           {certificate.category.value.replace('_', ' ').title()}
"""
        if certificate.specialty:
            content += f"Specialty:          {certificate.specialty}\n"

        content += f"""Activities:         {certificate.activities_completed}
Valid Until:        {certificate.valid_until.strftime('%B %d, %Y')}
{'='*80}

Certificate No:     {certificate.certificate_number}
Issued:             {certificate.issued_date.strftime('%B %d, %Y')}
Verify at:          {certificate.verification_url}

{'='*80}
"""

        filepath.write_text(content)
        logger.info(f"Generated text certificate: {filepath}")
        return filepath

    def verify_certificate(self, certificate_number: str) -> Optional[CMECertificate]:
        """
        Verify a certificate (stub - would query database in production)

        Args:
            certificate_number: Certificate number

        Returns:
            CMECertificate if valid, None otherwise
        """
        # In production, this would query the database
        logger.info(f"Verifying certificate: {certificate_number}")
        return None


# Global certificate generator instance
_certificate_generator = CertificateGenerator()


def get_certificate_generator() -> CertificateGenerator:
    """Get the global certificate generator instance"""
    return _certificate_generator
