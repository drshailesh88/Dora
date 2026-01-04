"""
Answer Sharing

Share medical answers with patients via WhatsApp.
"""

import logging
from typing import Optional
import qrcode
from io import BytesIO

from src.core.models import MedicalAnswer

from .client import WhatsAppClient
from .media import MediaHandler
from .templates import MessageTemplates

logger = logging.getLogger(__name__)


class AnswerSharing:
    """Share answers with patients"""

    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        media_handler: MediaHandler,
        templates: MessageTemplates,
        app_download_url: str = "https://docassist.in/download",
    ):
        """
        Initialize answer sharing.

        Args:
            whatsapp_client: WhatsApp client
            media_handler: Media handler for PDF generation
            templates: Message templates
            app_download_url: URL for app download
        """
        self.whatsapp_client = whatsapp_client
        self.media_handler = media_handler
        self.templates = templates
        self.app_download_url = app_download_url

    async def share_text_answer(
        self,
        to: str,
        answer: MedicalAnswer,
        include_sources: bool = False,
    ) -> bool:
        """
        Share answer as text message.

        Args:
            to: Patient phone number
            answer: Medical answer to share
            include_sources: Include citations

        Returns:
            True if sent successfully
        """
        try:
            # Format for patient (simplified)
            text = self._format_for_patient(answer, include_sources)

            # Send
            await self.whatsapp_client.send_text(
                to=to,
                text=text,
            )

            logger.info(f"Shared answer with patient {to}")
            return True

        except Exception as e:
            logger.error(f"Error sharing answer: {e}")
            return False

    async def share_pdf_answer(
        self,
        to: str,
        answer: MedicalAnswer,
        doctor_name: Optional[str] = None,
    ) -> bool:
        """
        Share answer as PDF document.

        Args:
            to: Patient phone number
            answer: Medical answer
            doctor_name: Doctor's name for attribution

        Returns:
            True if sent successfully
        """
        try:
            # Generate PDF content
            content = self._format_for_pdf(answer, doctor_name)
            title = f"Medical Information - {answer.question[:50]}"

            # Generate PDF
            pdf_path = await self.media_handler.generate_pdf_handout(
                content=content,
                title=title,
            )

            if not pdf_path:
                logger.error("Failed to generate PDF")
                return False

            # Upload to WhatsApp
            media_id = await self.whatsapp_client.upload_media(
                pdf_path,
                "application/pdf",
            )

            if not media_id:
                logger.error("Failed to upload PDF")
                return False

            # Send document
            await self.whatsapp_client.send_document(
                to=to,
                document_id=media_id,
                filename=f"{title}.pdf",
                caption="Medical information from your doctor",
            )

            logger.info(f"Shared PDF answer with patient {to}")

            # Clean up
            from pathlib import Path
            Path(pdf_path).unlink()

            return True

        except Exception as e:
            logger.error(f"Error sharing PDF: {e}")
            return False

    async def share_with_qr_code(
        self,
        to: str,
        answer: MedicalAnswer,
    ) -> bool:
        """
        Share answer with QR code for app download.

        Args:
            to: Patient phone number
            answer: Medical answer

        Returns:
            True if sent successfully
        """
        try:
            # Generate QR code for app download
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(self.app_download_url)
            qr.make(fit=True)

            # Save QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = self.media_handler.storage_dir / f"qr_{hash(to)}.png"

            img.save(str(qr_path))

            # Upload QR code
            media_id = await self.whatsapp_client.upload_media(
                str(qr_path),
                "image/png",
            )

            if not media_id:
                logger.error("Failed to upload QR code")
                return False

            # Send answer text
            text = self._format_for_patient(answer, include_sources=False)
            await self.whatsapp_client.send_text(to=to, text=text)

            # Send QR code with caption
            await self.whatsapp_client.send_image(
                to=to,
                image_id=media_id,
                caption="📱 Scan to download DocAssist app for more medical information",
            )

            # Clean up
            qr_path.unlink()

            logger.info(f"Shared answer with QR code to {to}")
            return True

        except Exception as e:
            logger.error(f"Error sharing with QR code: {e}")
            return False

    def _format_for_patient(
        self,
        answer: MedicalAnswer,
        include_sources: bool = False,
    ) -> str:
        """
        Format answer for patient (simplified language).

        Args:
            answer: Medical answer
            include_sources: Include citations

        Returns:
            Formatted text
        """
        lines = []

        lines.append("📋 *Medical Information*")
        lines.append("")

        # Simplify answer (ideally would use LLM)
        # For now, just use the answer as-is
        lines.append(answer.answer)
        lines.append("")

        # Important warnings
        if answer.warnings:
            lines.append("⚠️ *Important:*")
            for warning in answer.warnings:
                lines.append(f"• {warning}")
            lines.append("")

        # Sources (if requested)
        if include_sources and answer.citations:
            lines.append("📚 *Sources:*")
            for cite in answer.citations[:3]:
                lines.append(f"• {cite.source}")
            lines.append("")

        # Disclaimer
        lines.append("_This information is for educational purposes._")
        lines.append("_Always follow your doctor's specific advice._")
        lines.append("")
        lines.append("🩺 Shared by your healthcare provider")

        return "\n".join(lines)

    def _format_for_pdf(
        self,
        answer: MedicalAnswer,
        doctor_name: Optional[str] = None,
    ) -> str:
        """Format answer for PDF handout"""
        lines = []

        # Header
        if doctor_name:
            lines.append(f"From: Dr. {doctor_name}")
            lines.append("")

        lines.append(f"Question: {answer.question}")
        lines.append("")

        # Answer
        lines.append("Answer:")
        lines.append(answer.answer)
        lines.append("")

        # Warnings
        if answer.warnings:
            lines.append("Important Notes:")
            for warning in answer.warnings:
                lines.append(f"• {warning}")
            lines.append("")

        # Sources
        if answer.citations:
            lines.append("Medical References:")
            for i, cite in enumerate(answer.citations[:5], 1):
                lines.append(f"{i}. {cite.source}")
                if cite.title:
                    lines.append(f"   {cite.title}")
            lines.append("")

        # Disclaimer
        lines.append("Disclaimer:")
        lines.append("This information is for educational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for diagnosis and treatment.")

        return "\n".join(lines)

    async def send_app_invitation(
        self,
        to: str,
        doctor_name: Optional[str] = None,
    ) -> bool:
        """
        Send app download invitation to patient.

        Args:
            to: Patient phone number
            doctor_name: Doctor's name

        Returns:
            True if sent successfully
        """
        try:
            invitation = f"""👋 Hello!

{"Dr. " + doctor_name if doctor_name else "Your doctor"} uses *DocAssist* for medical information.

Download the DocAssist patient app to:
• View your medical information
• Get appointment reminders
• Access prescriptions
• Ask health questions

📱 Download now: {self.app_download_url}

It's free and secure!"""

            await self.whatsapp_client.send_text(to=to, text=invitation)

            logger.info(f"Sent app invitation to {to}")
            return True

        except Exception as e:
            logger.error(f"Error sending app invitation: {e}")
            return False
