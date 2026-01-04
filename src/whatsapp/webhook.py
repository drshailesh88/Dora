"""
WhatsApp Webhook Handler

Processes incoming WhatsApp webhooks from Meta Cloud API.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional, Any
from datetime import datetime

from .models import (
    WhatsAppMessage,
    MessageType,
    MediaMessage,
)

logger = logging.getLogger(__name__)


class WebhookVerifier:
    """Verify webhook signatures from Meta"""

    def __init__(self, app_secret: str):
        """
        Initialize verifier.

        Args:
            app_secret: Meta app secret for signature verification
        """
        self.app_secret = app_secret

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid
        """
        if not signature.startswith("sha256="):
            return False

        # Extract signature
        expected_signature = signature[7:]  # Remove 'sha256=' prefix

        # Compute HMAC
        mac = hmac.new(
            self.app_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256,
        )
        computed_signature = mac.hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(computed_signature, expected_signature)


class WebhookParser:
    """Parse WhatsApp webhook payloads"""

    @staticmethod
    def parse_message(webhook_data: dict) -> Optional[WhatsAppMessage]:
        """
        Parse incoming message from webhook.

        Args:
            webhook_data: Webhook JSON payload

        Returns:
            WhatsAppMessage or None
        """
        try:
            # Extract entry
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})

            # Get metadata
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")
            display_phone = metadata.get("display_phone_number")

            # Get messages
            messages = value.get("messages", [])
            if not messages:
                # No messages (could be status update)
                return None

            msg = messages[0]

            # Parse message
            message_id = msg.get("id")
            from_number = msg.get("from")
            timestamp = datetime.fromtimestamp(int(msg.get("timestamp", 0)))
            msg_type = msg.get("type")

            # Create base message
            whatsapp_msg = WhatsAppMessage(
                message_id=message_id,
                from_number=from_number,
                to_number=display_phone or "",
                timestamp=timestamp,
            )

            # Parse by type
            if msg_type == "text":
                whatsapp_msg.message_type = MessageType.TEXT
                whatsapp_msg.text = msg.get("text", {}).get("body", "")

            elif msg_type == "image":
                whatsapp_msg.message_type = MessageType.IMAGE
                image_data = msg.get("image", {})
                whatsapp_msg.media_id = image_data.get("id")
                whatsapp_msg.mime_type = image_data.get("mime_type")
                whatsapp_msg.caption = image_data.get("caption")

            elif msg_type == "audio":
                whatsapp_msg.message_type = MessageType.AUDIO
                audio_data = msg.get("audio", {})
                whatsapp_msg.media_id = audio_data.get("id")
                whatsapp_msg.mime_type = audio_data.get("mime_type")

            elif msg_type == "voice":
                whatsapp_msg.message_type = MessageType.VOICE
                voice_data = msg.get("voice", {})
                whatsapp_msg.media_id = voice_data.get("id")
                whatsapp_msg.mime_type = voice_data.get("mime_type")

            elif msg_type == "video":
                whatsapp_msg.message_type = MessageType.VIDEO
                video_data = msg.get("video", {})
                whatsapp_msg.media_id = video_data.get("id")
                whatsapp_msg.mime_type = video_data.get("mime_type")
                whatsapp_msg.caption = video_data.get("caption")

            elif msg_type == "document":
                whatsapp_msg.message_type = MessageType.DOCUMENT
                doc_data = msg.get("document", {})
                whatsapp_msg.media_id = doc_data.get("id")
                whatsapp_msg.mime_type = doc_data.get("mime_type")
                whatsapp_msg.caption = doc_data.get("caption")

            elif msg_type == "interactive":
                whatsapp_msg.message_type = MessageType.INTERACTIVE
                interactive_data = msg.get("interactive", {})

                # Button reply
                if interactive_data.get("type") == "button_reply":
                    button_reply = interactive_data.get("button_reply", {})
                    whatsapp_msg.button_payload = button_reply.get("id")
                    whatsapp_msg.text = button_reply.get("title")

                # List reply
                elif interactive_data.get("type") == "list_reply":
                    list_reply = interactive_data.get("list_reply", {})
                    whatsapp_msg.list_reply_id = list_reply.get("id")
                    whatsapp_msg.text = list_reply.get("title")

            elif msg_type == "button":
                whatsapp_msg.message_type = MessageType.BUTTON
                button_data = msg.get("button", {})
                whatsapp_msg.button_payload = button_data.get("payload")
                whatsapp_msg.text = button_data.get("text")

            else:
                logger.warning(f"Unsupported message type: {msg_type}")
                return None

            # Check for context (reply to message)
            context = msg.get("context")
            if context:
                whatsapp_msg.context_message_id = context.get("id")

            return whatsapp_msg

        except Exception as e:
            logger.error(f"Failed to parse webhook message: {e}")
            logger.debug(f"Webhook data: {json.dumps(webhook_data, indent=2)}")
            return None

    @staticmethod
    def parse_status(webhook_data: dict) -> Optional[dict]:
        """
        Parse status update from webhook.

        Args:
            webhook_data: Webhook JSON payload

        Returns:
            Status dict with message_id, status, timestamp
        """
        try:
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})

            statuses = value.get("statuses", [])
            if not statuses:
                return None

            status = statuses[0]

            return {
                "message_id": status.get("id"),
                "status": status.get("status"),  # sent, delivered, read, failed
                "timestamp": datetime.fromtimestamp(int(status.get("timestamp", 0))),
                "recipient_id": status.get("recipient_id"),
                "errors": status.get("errors", []),
            }

        except Exception as e:
            logger.error(f"Failed to parse status update: {e}")
            return None

    @staticmethod
    def is_message_webhook(webhook_data: dict) -> bool:
        """Check if webhook contains a message"""
        try:
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            return bool(value.get("messages"))
        except (IndexError, KeyError):
            return False

    @staticmethod
    def is_status_webhook(webhook_data: dict) -> bool:
        """Check if webhook contains a status update"""
        try:
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            return bool(value.get("statuses"))
        except (IndexError, KeyError):
            return False


class WebhookHandler:
    """Handle incoming WhatsApp webhooks"""

    def __init__(
        self,
        app_secret: str,
        verify_token: str,
    ):
        """
        Initialize webhook handler.

        Args:
            app_secret: Meta app secret
            verify_token: Webhook verification token
        """
        self.verifier = WebhookVerifier(app_secret)
        self.verify_token = verify_token
        self.parser = WebhookParser()

    def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
    ) -> Optional[str]:
        """
        Verify webhook subscription.

        Meta sends this during webhook setup.

        Args:
            mode: Should be "subscribe"
            token: Verification token
            challenge: Challenge string to echo back

        Returns:
            Challenge string if verification succeeds
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verification successful")
            return challenge
        else:
            logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
            return None

    def handle_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> dict:
        """
        Handle incoming webhook.

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header

        Returns:
            Dict with processed messages and statuses
        """
        # Verify signature
        if not self.verifier.verify_signature(payload, signature):
            logger.error("Invalid webhook signature")
            raise ValueError("Invalid webhook signature")

        # Parse JSON
        try:
            webhook_data = json.loads(payload.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid webhook JSON: {e}")
            raise ValueError("Invalid JSON")

        result = {
            "messages": [],
            "statuses": [],
        }

        # Parse messages
        if self.parser.is_message_webhook(webhook_data):
            msg = self.parser.parse_message(webhook_data)
            if msg:
                result["messages"].append(msg)

        # Parse status updates
        if self.parser.is_status_webhook(webhook_data):
            status = self.parser.parse_status(webhook_data)
            if status:
                result["statuses"].append(status)

        return result

    async def process_message(
        self,
        message: WhatsAppMessage,
        handler_func,
    ) -> Any:
        """
        Process a message with custom handler.

        Args:
            message: Parsed WhatsApp message
            handler_func: Async function to handle message

        Returns:
            Handler function result
        """
        try:
            return await handler_func(message)
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            raise
