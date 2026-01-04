"""
Media Handling

Handle WhatsApp media (voice notes, images, documents).
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from src.voice import SpeechToText, TextToSpeech

from .client import WhatsAppClient
from .models import MediaMessage, MessageType

logger = logging.getLogger(__name__)


class MediaHandler:
    """Handle WhatsApp media operations"""

    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        storage_dir: Optional[str] = None,
    ):
        """
        Initialize media handler.

        Args:
            whatsapp_client: WhatsApp client for download/upload
            storage_dir: Directory to store media files
        """
        self.whatsapp_client = whatsapp_client
        self.storage_dir = Path(storage_dir or "./data/whatsapp/media")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize STT/TTS lazily
        self._stt: Optional[SpeechToText] = None
        self._tts: Optional[TextToSpeech] = None

    @property
    def stt(self) -> SpeechToText:
        """Lazy load STT"""
        if self._stt is None:
            self._stt = SpeechToText()
        return self._stt

    @property
    def tts(self) -> Optional[TextToSpeech]:
        """Lazy load TTS"""
        if self._tts is None:
            try:
                self._tts = TextToSpeech()
            except Exception as e:
                logger.warning(f"TTS not available: {e}")
                self._tts = None
        return self._tts

    async def download_media(
        self,
        media_id: str,
        media_type: MessageType,
        save_to_disk: bool = True,
    ) -> Optional[MediaMessage]:
        """
        Download media from WhatsApp.

        Args:
            media_id: WhatsApp media ID
            media_type: Type of media
            save_to_disk: Whether to save to disk (vs temp)

        Returns:
            MediaMessage with local path
        """
        try:
            # Download media bytes
            media_bytes = await self.whatsapp_client.download_media(media_id)
            if not media_bytes:
                logger.error(f"Failed to download media {media_id}")
                return None

            # Determine file extension
            extension_map = {
                MessageType.IMAGE: ".jpg",
                MessageType.AUDIO: ".ogg",
                MessageType.VOICE: ".ogg",
                MessageType.VIDEO: ".mp4",
                MessageType.DOCUMENT: ".pdf",
            }
            ext = extension_map.get(media_type, ".bin")

            # Save file
            if save_to_disk:
                file_path = self.storage_dir / f"{media_id}{ext}"
            else:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=ext,
                    dir=str(self.storage_dir),
                )
                file_path = Path(temp_file.name)
                temp_file.close()

            with open(file_path, "wb") as f:
                f.write(media_bytes)

            logger.info(f"Downloaded media {media_id} to {file_path}")

            return MediaMessage(
                media_id=media_id,
                local_path=str(file_path),
                media_type=media_type,
                file_size=len(media_bytes),
                downloaded=True,
            )

        except Exception as e:
            logger.error(f"Error downloading media {media_id}: {e}")
            return None

    async def transcribe_voice_note(
        self,
        media_id: str,
        language: str = "en",
    ) -> Optional[str]:
        """
        Download and transcribe a voice note.

        Args:
            media_id: WhatsApp media ID
            language: Language code for transcription

        Returns:
            Transcribed text
        """
        try:
            # Download audio
            media = await self.download_media(
                media_id,
                MessageType.VOICE,
                save_to_disk=False,
            )

            if not media or not media.local_path:
                return None

            # Transcribe
            result = self.stt.transcribe(media.local_path, language=language)
            transcription = result["text"]

            # Update media object
            media.transcribed = True
            media.transcription = transcription

            logger.info(f"Transcribed voice note {media_id}: {transcription}")

            # Clean up temp file
            Path(media.local_path).unlink()

            return transcription

        except Exception as e:
            logger.error(f"Error transcribing voice note {media_id}: {e}")
            return None

    async def generate_audio_response(
        self,
        text: str,
        output_format: str = "ogg",
    ) -> Optional[str]:
        """
        Generate audio response from text.

        Args:
            text: Text to convert to speech
            output_format: Audio format (ogg, mp3, wav)

        Returns:
            Path to generated audio file
        """
        if not self.tts:
            logger.warning("TTS not available")
            return None

        try:
            # Generate audio
            output_path = self.storage_dir / f"response_{hash(text)}.{output_format}"

            self.tts.synthesize(text, str(output_path))

            logger.info(f"Generated audio response: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating audio response: {e}")
            return None

    async def upload_and_send_audio(
        self,
        to: str,
        text: str,
    ) -> Optional[str]:
        """
        Generate audio, upload to WhatsApp, and send.

        Args:
            to: Recipient phone number
            text: Text to convert to speech

        Returns:
            WhatsApp message ID
        """
        try:
            # Generate audio
            audio_path = await self.generate_audio_response(text)
            if not audio_path:
                return None

            # Upload to WhatsApp
            media_id = await self.whatsapp_client.upload_media(
                audio_path,
                "audio/ogg",
            )

            if not media_id:
                logger.error("Failed to upload audio")
                return None

            # Send audio
            response = await self.whatsapp_client.send_audio(
                to=to,
                audio_id=media_id,
            )

            # Clean up
            Path(audio_path).unlink()

            return response.message_id

        except Exception as e:
            logger.error(f"Error uploading and sending audio: {e}")
            return None

    async def process_image(
        self,
        media_id: str,
    ) -> Optional[dict]:
        """
        Download and process an image.

        Could be used for:
        - Dermatology analysis
        - X-ray interpretation
        - Lab report OCR

        Args:
            media_id: WhatsApp media ID

        Returns:
            Analysis results
        """
        try:
            # Download image
            media = await self.download_media(
                media_id,
                MessageType.IMAGE,
                save_to_disk=True,
            )

            if not media or not media.local_path:
                return None

            # TODO: Implement image analysis
            # This would use a vision model or OCR

            logger.info(f"Image downloaded: {media.local_path}")

            return {
                "media_id": media_id,
                "path": media.local_path,
                "size": media.file_size,
                "analysis": "Image analysis not yet implemented",
            }

        except Exception as e:
            logger.error(f"Error processing image {media_id}: {e}")
            return None

    async def generate_pdf_handout(
        self,
        content: str,
        title: str,
    ) -> Optional[str]:
        """
        Generate a PDF handout from content.

        Args:
            content: Content text
            title: Document title

        Returns:
            Path to generated PDF
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            # Create PDF
            output_path = self.storage_dir / f"handout_{hash(content)}.pdf"

            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )

            # Content
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Content
            for line in content.split("\n"):
                if line.strip():
                    story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))

            # Footer
            footer_text = "Generated by Dora - DocAssist Medical Knowledge Platform"
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(footer_text, styles['Italic']))

            doc.build(story)

            logger.info(f"Generated PDF: {output_path}")

            return str(output_path)

        except ImportError:
            logger.error("reportlab not installed. Cannot generate PDF.")
            return None
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None

    def cleanup_old_media(self, days: int = 7):
        """
        Clean up media files older than N days.

        Args:
            days: Delete files older than this many days
        """
        import time

        cutoff = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.storage_dir.glob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old media files")
