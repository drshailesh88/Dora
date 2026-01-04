"""
WhatsApp Service

Main service that coordinates all WhatsApp functionality.
"""

import logging
from typing import Optional
import os

from src.core.pipeline import MedicalQueryPipeline
from src.drugs import DrugInteractionChecker
from src.voice import SpeechToText, TextToSpeech

from .client import WhatsAppClient
from .webhook import WebhookHandler
from .conversation import ConversationManager
from .handlers import (
    TextQueryHandler,
    VoiceNoteHandler,
    DrugCheckHandler,
    CalculatorHandler,
    HelpHandler,
    OnboardingHandler,
    ImageHandler,
    ButtonHandler,
)
from .templates import MessageTemplates
from .media import MediaHandler
from .sharing import AnswerSharing
from .groups import GroupManager
from .models import WhatsAppMessage, MessageType, ConversationIntent

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Main WhatsApp service.

    Coordinates all WhatsApp functionality:
    - Message handling
    - Conversation management
    - Media processing
    - Answer sharing
    - Group management
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        business_account_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        verify_token: Optional[str] = None,
        storage_dir: Optional[str] = None,
        query_pipeline: Optional[MedicalQueryPipeline] = None,
        drug_checker: Optional[DrugInteractionChecker] = None,
    ):
        """
        Initialize WhatsApp service.

        Args:
            access_token: Meta WhatsApp access token
            phone_number_id: WhatsApp Business phone number ID
            business_account_id: WhatsApp Business account ID
            app_secret: Meta app secret for webhook verification
            verify_token: Webhook verification token
            storage_dir: Directory for data storage
            query_pipeline: Medical query pipeline (optional)
            drug_checker: Drug interaction checker (optional)
        """
        # Load from environment if not provided
        self.access_token = access_token or os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = phone_number_id or os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        self.business_account_id = business_account_id or os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
        self.app_secret = app_secret or os.environ.get("WHATSAPP_APP_SECRET", "")
        self.verify_token = verify_token or os.environ.get("WHATSAPP_VERIFY_TOKEN", "")

        # Initialize components
        self.client = WhatsAppClient(
            access_token=self.access_token,
            phone_number_id=self.phone_number_id,
            business_account_id=self.business_account_id,
        )

        self.webhook_handler = WebhookHandler(
            app_secret=self.app_secret,
            verify_token=self.verify_token,
        )

        self.conversation_manager = ConversationManager(
            storage_dir=storage_dir or "./data/whatsapp",
        )

        self.templates = MessageTemplates()

        self.media_handler = MediaHandler(
            whatsapp_client=self.client,
            storage_dir=storage_dir or "./data/whatsapp/media",
        )

        self.sharing = AnswerSharing(
            whatsapp_client=self.client,
            media_handler=self.media_handler,
            templates=self.templates,
        )

        self.group_manager = GroupManager(
            whatsapp_client=self.client,
        )

        # Initialize pipelines
        self.query_pipeline = query_pipeline
        self.drug_checker = drug_checker

        # Initialize handlers
        self._init_handlers()

        logger.info("WhatsApp service initialized")

    def _init_handlers(self):
        """Initialize message handlers"""
        # Text query handler
        if self.query_pipeline:
            self.text_handler = TextQueryHandler(
                conversation_manager=self.conversation_manager,
                whatsapp_client=self.client,
                templates=self.templates,
                query_pipeline=self.query_pipeline,
            )
        else:
            self.text_handler = None
            logger.warning("Query pipeline not available")

        # Voice note handler
        if self.query_pipeline:
            self.voice_handler = VoiceNoteHandler(
                conversation_manager=self.conversation_manager,
                whatsapp_client=self.client,
                templates=self.templates,
                query_pipeline=self.query_pipeline,
                stt=SpeechToText(),
                tts=None,  # TTS is optional
            )
        else:
            self.voice_handler = None

        # Drug check handler
        if self.drug_checker:
            self.drug_handler = DrugCheckHandler(
                conversation_manager=self.conversation_manager,
                whatsapp_client=self.client,
                templates=self.templates,
                drug_checker=self.drug_checker,
            )
        else:
            self.drug_handler = None
            logger.warning("Drug checker not available")

        # Other handlers
        self.calculator_handler = CalculatorHandler(
            conversation_manager=self.conversation_manager,
            whatsapp_client=self.client,
            templates=self.templates,
        )

        self.help_handler = HelpHandler(
            conversation_manager=self.conversation_manager,
            whatsapp_client=self.client,
            templates=self.templates,
        )

        self.onboarding_handler = OnboardingHandler(
            conversation_manager=self.conversation_manager,
            whatsapp_client=self.client,
            templates=self.templates,
        )

        self.image_handler = ImageHandler(
            conversation_manager=self.conversation_manager,
            whatsapp_client=self.client,
            templates=self.templates,
        )

        # Button handler
        self.button_handler = ButtonHandler(
            conversation_manager=self.conversation_manager,
            whatsapp_client=self.client,
            templates=self.templates,
            other_handlers={
                "calculator": self.calculator_handler,
                "help": self.help_handler,
            },
        )

    async def process_message(self, message: WhatsAppMessage) -> bool:
        """
        Process an incoming WhatsApp message.

        Args:
            message: Parsed WhatsApp message

        Returns:
            True if processed successfully
        """
        try:
            whatsapp_id = message.from_number

            # Mark message as read
            if message.message_id:
                await self.client.mark_as_read(message.message_id)

            # Get or create user
            user = self.conversation_manager.get_or_create_user(whatsapp_id)
            user.message_count += 1

            # Get conversation
            conversation = self.conversation_manager.get_or_create_conversation(whatsapp_id)

            # Check if new user - show onboarding
            if self.conversation_manager.should_show_onboarding(whatsapp_id):
                await self.onboarding_handler.handle(message)
                return True

            # Route by message type
            if message.message_type == MessageType.TEXT:
                await self._handle_text_message(message, conversation)

            elif message.message_type in [MessageType.VOICE, MessageType.AUDIO]:
                if self.voice_handler:
                    await self.voice_handler.handle(message)
                else:
                    await self.client.send_text(
                        to=whatsapp_id,
                        text="Voice messages are not currently supported.",
                    )

            elif message.message_type == MessageType.IMAGE:
                await self.image_handler.handle(message)

            elif message.message_type == MessageType.INTERACTIVE:
                await self.button_handler.handle(message)

            elif message.message_type == MessageType.BUTTON:
                await self.button_handler.handle(message)

            else:
                logger.warning(f"Unsupported message type: {message.message_type}")
                await self.client.send_text(
                    to=whatsapp_id,
                    text="Sorry, I don't support that message type yet.",
                )

            return True

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Send error message to user
            try:
                await self.client.send_text(
                    to=message.from_number,
                    text=self.templates.get_error_message(),
                )
            except Exception:
                pass
            return False

    async def _handle_text_message(
        self,
        message: WhatsAppMessage,
        conversation,
    ):
        """Handle text message based on intent"""
        text = (message.text or "").lower().strip()

        # Check for commands
        if text in ["help", "/help", "?", "menu"]:
            await self.help_handler.handle(message)

        elif text in ["link", "/link", "connect"]:
            # Generate link code
            code = self.conversation_manager.generate_link_code(message.from_number)
            await self.client.send_text(
                to=message.from_number,
                text=self.templates.get_linking_instructions(code),
            )

        elif text.startswith("check") and ("interaction" in text or "and" in text):
            # Drug interaction check
            if self.drug_handler:
                await self.drug_handler.handle(message)
            else:
                await self.client.send_text(
                    to=message.from_number,
                    text="Drug interaction checker is not available.",
                )

        elif text in ["calculator", "calc", "calculate"]:
            # Medical calculator
            await self.calculator_handler.handle(message)

        else:
            # Medical query
            if self.text_handler:
                await self.text_handler.handle(message)
            else:
                await self.client.send_text(
                    to=message.from_number,
                    text="Medical query service is not available.",
                )

    async def send_notification(
        self,
        to: str,
        notification_type: str,
        data: dict,
    ) -> bool:
        """
        Send notification to user.

        Args:
            to: WhatsApp ID
            notification_type: Type of notification
            data: Notification data

        Returns:
            True if sent successfully
        """
        try:
            # Check if user has notifications enabled
            user = self.conversation_manager.get_user(to)
            if user and not user.notifications_enabled:
                logger.info(f"Notifications disabled for {to}")
                return False

            # Format notification
            message = self.templates.format_notification(notification_type, data)

            # Send
            await self.client.send_text(to=to, text=message)

            logger.info(f"Sent {notification_type} notification to {to}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def broadcast_message(
        self,
        recipients: list[str],
        message: str,
    ) -> int:
        """
        Broadcast message to multiple users.

        Args:
            recipients: List of WhatsApp IDs
            message: Message text

        Returns:
            Number of messages sent successfully
        """
        sent_count = 0

        for recipient in recipients:
            try:
                await self.client.send_text(to=recipient, text=message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {recipient}: {e}")

        logger.info(f"Broadcast sent to {sent_count}/{len(recipients)} users")
        return sent_count

    def get_stats(self) -> dict:
        """Get service statistics"""
        conv_stats = self.conversation_manager.get_stats()

        return {
            "whatsapp": {
                "phone_number_id": self.phone_number_id,
                "business_account_id": self.business_account_id,
            },
            "users": conv_stats,
            "handlers": {
                "text_query": self.text_handler is not None,
                "voice": self.voice_handler is not None,
                "drug_check": self.drug_handler is not None,
                "calculator": True,
                "image": True,
            },
        }

    def link_user_account(
        self,
        whatsapp_id: str,
        user_id: str,
    ) -> bool:
        """
        Link WhatsApp to Dora user account.

        Args:
            whatsapp_id: WhatsApp phone number
            user_id: Dora user ID

        Returns:
            True if linked successfully
        """
        try:
            self.conversation_manager.link_user(whatsapp_id, user_id)

            # Send confirmation
            import asyncio
            asyncio.create_task(
                self.client.send_text(
                    to=whatsapp_id,
                    text=self.templates.get_linked_confirmation(),
                )
            )

            logger.info(f"Linked WhatsApp {whatsapp_id} to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error linking user: {e}")
            return False

    def verify_link_code(self, code: str) -> Optional[str]:
        """
        Verify link code and return WhatsApp ID.

        Args:
            code: 6-digit link code

        Returns:
            WhatsApp ID if valid
        """
        return self.conversation_manager.verify_link_code(code)
