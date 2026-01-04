"""
Message Handlers

Handlers for different types of WhatsApp messages.
"""

import logging
from typing import Optional, Any
from pathlib import Path

from src.core.models import MedicalAnswer, PatientContext
from src.core.pipeline import MedicalQueryPipeline
from src.drugs import DrugInteractionChecker
from src.voice import SpeechToText, TextToSpeech
from src.calculators import get_calculator

from .models import (
    WhatsAppMessage,
    WhatsAppResponse,
    MessageType,
    ConversationIntent,
    QuickReply,
)
from .conversation import ConversationManager
from .templates import MessageTemplates
from .client import WhatsAppClient

logger = logging.getLogger(__name__)


class MessageHandler:
    """Base message handler"""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        whatsapp_client: WhatsAppClient,
        templates: MessageTemplates,
    ):
        self.conversation_manager = conversation_manager
        self.whatsapp_client = whatsapp_client
        self.templates = templates

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """Handle a message (to be implemented by subclasses)"""
        raise NotImplementedError


class TextQueryHandler(MessageHandler):
    """Handle text queries"""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        whatsapp_client: WhatsAppClient,
        templates: MessageTemplates,
        query_pipeline: MedicalQueryPipeline,
    ):
        super().__init__(conversation_manager, whatsapp_client, templates)
        self.query_pipeline = query_pipeline

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """
        Handle text query.

        Process medical question and return answer.
        """
        if not message.text:
            return None

        question = message.text.strip()
        whatsapp_id = message.from_number

        # Update conversation
        self.conversation_manager.set_conversation_intent(
            whatsapp_id,
            ConversationIntent.QUERY,
        )

        # Get user preferences
        user = self.conversation_manager.get_or_create_user(whatsapp_id)

        # Increment query count
        user.query_count += 1

        try:
            # Query the medical knowledge base
            answer: MedicalAnswer = await self.query_pipeline.query(
                question=question,
                patient_context=None,  # TODO: Get from EMR if linked
                top_k=10,
            )

            # Format response based on user preference
            response_text = self.templates.format_query_response(
                answer=answer,
                format_type=user.preferred_format,
            )

            # Store answer ID in conversation context
            self.conversation_manager.set_context(
                whatsapp_id,
                "last_answer",
                answer,
            )

            # Create quick reply buttons
            buttons = [
                QuickReply(id="drug_check", title="Check Drug Interaction"),
                QuickReply(id="calculator", title="Medical Calculator"),
                QuickReply(id="share", title="Share with Patient"),
            ]

            # Send response with buttons
            response = await self.whatsapp_client.send_interactive_buttons(
                to=whatsapp_id,
                body=response_text,
                buttons=buttons,
                footer="Powered by Dora",
                context_message_id=message.message_id,
            )

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}")

            # Send error message
            error_text = self.templates.get_error_message()
            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=error_text,
                context_message_id=message.message_id,
            )


class VoiceNoteHandler(MessageHandler):
    """Handle voice notes"""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        whatsapp_client: WhatsAppClient,
        templates: MessageTemplates,
        query_pipeline: MedicalQueryPipeline,
        stt: SpeechToText,
        tts: Optional[TextToSpeech] = None,
    ):
        super().__init__(conversation_manager, whatsapp_client, templates)
        self.query_pipeline = query_pipeline
        self.stt = stt
        self.tts = tts

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """
        Handle voice note.

        1. Download audio
        2. Transcribe to text
        3. Process query
        4. Send text response (and optional audio)
        """
        whatsapp_id = message.from_number

        # Update conversation intent
        self.conversation_manager.set_conversation_intent(
            whatsapp_id,
            ConversationIntent.VOICE_NOTE,
        )

        try:
            # Download audio
            if not message.media_id:
                return None

            audio_bytes = await self.whatsapp_client.download_media(message.media_id)
            if not audio_bytes:
                return await self.whatsapp_client.send_text(
                    to=whatsapp_id,
                    text="Sorry, I couldn't download the voice note. Please try again.",
                    context_message_id=message.message_id,
                )

            # Save temporarily
            temp_dir = Path("./data/temp/whatsapp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            audio_path = temp_dir / f"{message.message_id}.ogg"

            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

            # Transcribe
            result = self.stt.transcribe(str(audio_path))
            transcribed_text = result["text"]

            logger.info(f"Transcribed voice note: {transcribed_text}")

            # Clean up
            audio_path.unlink()

            # Send transcription confirmation
            await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=f'I heard: "{transcribed_text}"\n\nLet me find the answer...',
                context_message_id=message.message_id,
            )

            # Process as text query
            answer: MedicalAnswer = await self.query_pipeline.query(
                question=transcribed_text,
                patient_context=None,
                top_k=10,
            )

            # Get user preferences
            user = self.conversation_manager.get_or_create_user(whatsapp_id)
            user.query_count += 1

            # Format response
            response_text = self.templates.format_query_response(
                answer=answer,
                format_type=user.preferred_format,
            )

            # Send text response
            await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=response_text,
            )

            # Send audio response if enabled and available
            if user.voice_responses and self.tts:
                try:
                    # Generate audio
                    audio_output = temp_dir / f"response_{message.message_id}.ogg"
                    self.tts.synthesize(answer.answer, str(audio_output))

                    # Upload and send
                    media_id = await self.whatsapp_client.upload_media(
                        str(audio_output),
                        "audio/ogg",
                    )

                    if media_id:
                        await self.whatsapp_client.send_audio(
                            to=whatsapp_id,
                            audio_id=media_id,
                        )

                    # Clean up
                    audio_output.unlink()

                except Exception as e:
                    logger.error(f"Failed to send audio response: {e}")

            return None  # Already sent responses

        except Exception as e:
            logger.error(f"Error processing voice note: {e}")

            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Sorry, I couldn't process your voice note. Please try sending a text message instead.",
                context_message_id=message.message_id,
            )


class DrugCheckHandler(MessageHandler):
    """Handle drug interaction checks"""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        whatsapp_client: WhatsAppClient,
        templates: MessageTemplates,
        drug_checker: DrugInteractionChecker,
    ):
        super().__init__(conversation_manager, whatsapp_client, templates)
        self.drug_checker = drug_checker

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """
        Handle drug interaction check.

        Expects: "Check clopidogrel and omeprazole"
        """
        if not message.text:
            return None

        whatsapp_id = message.from_number

        # Update conversation intent
        self.conversation_manager.set_conversation_intent(
            whatsapp_id,
            ConversationIntent.DRUG_CHECK,
        )

        try:
            # Parse drug names (simple split on "and" or comma)
            text = message.text.lower()
            text = text.replace("check interaction", "").replace("check", "").strip()

            # Split on common delimiters
            drugs = []
            for delimiter in [" and ", ",", ";"]:
                if delimiter in text:
                    drugs = [d.strip() for d in text.split(delimiter)]
                    break

            if not drugs or len(drugs) < 2:
                return await self.whatsapp_client.send_text(
                    to=whatsapp_id,
                    text="Please provide at least 2 drugs to check interactions.\n\nExample: Check clopidogrel and omeprazole",
                    context_message_id=message.message_id,
                )

            # Check interactions
            interactions = self.drug_checker.check_multiple(drugs)

            # Format response
            response_text = self.templates.format_drug_interaction_response(
                drugs=drugs,
                interactions=interactions,
            )

            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=response_text,
                context_message_id=message.message_id,
            )

        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")

            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Sorry, I couldn't check the drug interactions. Please try again.",
                context_message_id=message.message_id,
            )


class CalculatorHandler(MessageHandler):
    """Handle medical calculator requests"""

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """
        Handle calculator request.

        Shows available calculators or processes input.
        """
        whatsapp_id = message.from_number

        # Update conversation intent
        self.conversation_manager.set_conversation_intent(
            whatsapp_id,
            ConversationIntent.CALCULATOR,
        )

        # Check if calculator already selected
        selected_calc = self.conversation_manager.get_context(
            whatsapp_id,
            "selected_calculator",
        )

        if not selected_calc:
            # Show calculator list
            calculators = [
                ("egfr", "eGFR (Kidney Function)"),
                ("chads2", "CHA2DS2-VASc Score"),
                ("wells", "Wells' DVT Score"),
                ("bmi", "BMI Calculator"),
            ]

            response_text = "📊 *Medical Calculators*\n\n"
            response_text += "Select a calculator:\n\n"

            for code, name in calculators:
                response_text += f"• {name}\n"

            response_text += "\nReply with the calculator name."

            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=response_text,
                context_message_id=message.message_id,
            )

        else:
            # Process calculator input
            # This would need more sophisticated parsing
            # For now, just acknowledge
            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Calculator processing not yet implemented. Coming soon!",
                context_message_id=message.message_id,
            )


class HelpHandler(MessageHandler):
    """Handle help requests"""

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """Send help message"""
        whatsapp_id = message.from_number

        help_text = self.templates.get_help_message()

        return await self.whatsapp_client.send_text(
            to=whatsapp_id,
            text=help_text,
            context_message_id=message.message_id,
        )


class OnboardingHandler(MessageHandler):
    """Handle new user onboarding"""

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """Send welcome message"""
        whatsapp_id = message.from_number

        welcome_text = self.templates.get_welcome_message()

        buttons = [
            QuickReply(id="link_account", title="Link My Account"),
            QuickReply(id="start_query", title="Ask a Question"),
            QuickReply(id="help", title="Help"),
        ]

        return await self.whatsapp_client.send_interactive_buttons(
            to=whatsapp_id,
            body=welcome_text,
            buttons=buttons,
        )


class ImageHandler(MessageHandler):
    """Handle image uploads (for analysis)"""

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """
        Handle image upload.

        Could be used for:
        - Dermatology image analysis
        - X-ray interpretation
        - Lab report OCR
        """
        whatsapp_id = message.from_number

        # Update conversation intent
        self.conversation_manager.set_conversation_intent(
            whatsapp_id,
            ConversationIntent.IMAGE_ANALYSIS,
        )

        # For now, just acknowledge
        return await self.whatsapp_client.send_text(
            to=whatsapp_id,
            text="📸 Image analysis is coming soon!\n\nFor now, please describe your medical question in text.",
            context_message_id=message.message_id,
        )


class ButtonHandler(MessageHandler):
    """Handle button clicks"""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        whatsapp_client: WhatsAppClient,
        templates: MessageTemplates,
        other_handlers: dict[str, MessageHandler],
    ):
        super().__init__(conversation_manager, whatsapp_client, templates)
        self.other_handlers = other_handlers

    async def handle(self, message: WhatsAppMessage) -> Optional[WhatsAppResponse]:
        """Route button clicks to appropriate handlers"""
        if not message.button_payload:
            return None

        payload = message.button_payload
        whatsapp_id = message.from_number

        # Route to appropriate handler
        if payload == "drug_check":
            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Please send the drugs you want to check for interactions.\n\nExample: clopidogrel and omeprazole",
            )

        elif payload == "calculator":
            handler = self.other_handlers.get("calculator")
            if handler:
                return await handler.handle(message)

        elif payload == "share":
            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Answer sharing feature coming soon!",
            )

        elif payload == "link_account":
            # Generate link code
            code = self.conversation_manager.generate_link_code(whatsapp_id)

            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text=f"🔗 *Link Your Account*\n\nYour link code is: *{code}*\n\nThis code expires in 15 minutes.\n\n1. Open Dora web app or mobile app\n2. Go to Settings → WhatsApp\n3. Enter this code\n\nOnce linked, you'll have access to all premium features!",
            )

        elif payload == "start_query":
            return await self.whatsapp_client.send_text(
                to=whatsapp_id,
                text="Ask me any medical question!\n\nYou can:\n• Send a text message\n• Send a voice note\n• Check drug interactions\n• Use medical calculators",
            )

        elif payload == "help":
            handler = self.other_handlers.get("help")
            if handler:
                return await handler.handle(message)

        return None
