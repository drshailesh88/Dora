"""
WhatsApp Business API Client

Meta WhatsApp Cloud API integration for sending messages.
"""

import asyncio
import json
import os
from typing import Optional, Any
import logging

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.parse
    HAS_HTTPX = False

from .models import (
    MessageType,
    WhatsAppResponse,
    MessageStatus,
    QuickReply,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for WhatsApp API"""

    def __init__(self, messages_per_second: int = 80):
        """
        Initialize rate limiter.

        WhatsApp Cloud API limits:
        - 80 messages/second
        - 1000 messages/second for business accounts
        """
        self.messages_per_second = messages_per_second
        self.interval = 1.0 / messages_per_second
        self.last_send = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire rate limit slot"""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_send

            if time_since_last < self.interval:
                await asyncio.sleep(self.interval - time_since_last)

            self.last_send = asyncio.get_event_loop().time()


class WhatsAppClient:
    """
    WhatsApp Business Cloud API Client.

    Handles sending messages, media, interactive buttons, etc.
    """

    API_VERSION = "v21.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        business_account_id: Optional[str] = None,
    ):
        """
        Initialize WhatsApp client.

        Args:
            access_token: Meta WhatsApp access token
            phone_number_id: WhatsApp Business phone number ID
            business_account_id: WhatsApp Business account ID
        """
        self.access_token = access_token or os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = phone_number_id or os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        self.business_account_id = business_account_id or os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID", "")

        self.rate_limiter = RateLimiter()

        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured")

    def _get_url(self, endpoint: str) -> str:
        """Get full API URL"""
        return f"{self.BASE_URL}/{self.API_VERSION}/{endpoint}"

    def _get_headers(self) -> dict:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> dict:
        """Make HTTP request to WhatsApp API"""
        url = self._get_url(endpoint)
        headers = self._get_headers()

        # Apply rate limiting
        await self.rate_limiter.acquire()

        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()
        else:
            # Fallback to urllib
            req_data = json.dumps(data).encode() if data else None

            request = urllib.request.Request(
                url,
                data=req_data,
                headers=headers,
                method=method,
            )

            try:
                with urllib.request.urlopen(request) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                error_body = e.read().decode()
                logger.error(f"WhatsApp API error: {error_body}")
                raise

    async def send_text(
        self,
        to: str,
        text: str,
        preview_url: bool = True,
        context_message_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """
        Send a text message.

        Args:
            to: Recipient phone number (with country code, no +)
            text: Message text
            preview_url: Enable URL preview
            context_message_id: Message ID to reply to

        Returns:
            WhatsAppResponse with message ID
        """
        to = self._format_number(to)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text,
            },
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.TEXT,
                text=text,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
                context_message_id=context_message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            raise

    async def send_image(
        self,
        to: str,
        image_url: Optional[str] = None,
        image_id: Optional[str] = None,
        caption: Optional[str] = None,
        context_message_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """
        Send an image.

        Args:
            to: Recipient phone number
            image_url: URL of image (or use image_id)
            image_id: WhatsApp media ID (or use image_url)
            caption: Image caption
            context_message_id: Message ID to reply to

        Returns:
            WhatsAppResponse
        """
        to = self._format_number(to)

        if not image_url and not image_id:
            raise ValueError("Either image_url or image_id must be provided")

        image_data = {}
        if image_id:
            image_data["id"] = image_id
        else:
            image_data["link"] = image_url

        if caption:
            image_data["caption"] = caption

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image_data,
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.IMAGE,
                media_url=image_url,
                media_id=image_id,
                caption=caption,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
                context_message_id=context_message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            raise

    async def send_audio(
        self,
        to: str,
        audio_url: Optional[str] = None,
        audio_id: Optional[str] = None,
        context_message_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send an audio file"""
        to = self._format_number(to)

        if not audio_url and not audio_id:
            raise ValueError("Either audio_url or audio_id must be provided")

        audio_data = {}
        if audio_id:
            audio_data["id"] = audio_id
        else:
            audio_data["link"] = audio_url

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": audio_data,
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.AUDIO,
                media_url=audio_url,
                media_id=audio_id,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
                context_message_id=context_message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            raise

    async def send_document(
        self,
        to: str,
        document_url: Optional[str] = None,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        context_message_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Send a document (PDF, etc.)"""
        to = self._format_number(to)

        if not document_url and not document_id:
            raise ValueError("Either document_url or document_id must be provided")

        doc_data = {}
        if document_id:
            doc_data["id"] = document_id
        else:
            doc_data["link"] = document_url

        if filename:
            doc_data["filename"] = filename
        if caption:
            doc_data["caption"] = caption

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": doc_data,
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.DOCUMENT,
                media_url=document_url,
                media_id=document_id,
                caption=caption,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
                context_message_id=context_message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            raise

    async def send_interactive_buttons(
        self,
        to: str,
        body: str,
        buttons: list[QuickReply],
        header: Optional[str] = None,
        footer: Optional[str] = None,
        context_message_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """
        Send interactive message with reply buttons.

        Args:
            to: Recipient phone number
            body: Message body text
            buttons: List of QuickReply buttons (max 3)
            header: Optional header text
            footer: Optional footer text
            context_message_id: Message ID to reply to

        Returns:
            WhatsAppResponse
        """
        to = self._format_number(to)

        if len(buttons) > 3:
            raise ValueError("Maximum 3 buttons allowed")

        button_data = [
            {
                "type": "reply",
                "reply": {"id": btn.id, "title": btn.title[:20]},  # Max 20 chars
            }
            for btn in buttons
        ]

        interactive_data: dict[str, Any] = {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": button_data},
        }

        if header:
            interactive_data["header"] = {"type": "text", "text": header}
        if footer:
            interactive_data["footer"] = {"text": footer}

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_data,
        }

        if context_message_id:
            payload["context"] = {"message_id": context_message_id}

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.INTERACTIVE,
                text=body,
                buttons=[btn.to_dict() for btn in buttons],
                header=header,
                footer=footer,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
                context_message_id=context_message_id,
            )

        except Exception as e:
            logger.error(f"Failed to send interactive buttons: {e}")
            raise

    async def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en",
        components: Optional[list[dict]] = None,
    ) -> WhatsAppResponse:
        """
        Send a message template.

        Args:
            to: Recipient phone number
            template_name: Template name (pre-approved)
            language: Template language code
            components: Template components (header, body, buttons)

        Returns:
            WhatsAppResponse
        """
        to = self._format_number(to)

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }

        if components:
            payload["template"]["components"] = components

        try:
            result = await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )

            return WhatsAppResponse(
                to_number=to,
                message_type=MessageType.TEMPLATE,
                status=MessageStatus.SENT,
                message_id=result["messages"][0]["id"],
            )

        except Exception as e:
            logger.error(f"Failed to send template: {e}")
            raise

    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.

        Args:
            message_id: WhatsApp message ID

        Returns:
            True if successful
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            await self._make_request(
                "POST",
                f"{self.phone_number_id}/messages",
                payload,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False

    async def upload_media(
        self,
        file_path: str,
        mime_type: str,
    ) -> Optional[str]:
        """
        Upload media file and get media ID.

        Args:
            file_path: Path to media file
            mime_type: MIME type of file

        Returns:
            Media ID if successful
        """
        # This requires multipart/form-data upload
        # Implementation depends on whether we have httpx
        if not HAS_HTTPX:
            logger.error("Media upload requires httpx library")
            return None

        url = self._get_url(f"{self.phone_number_id}/media")

        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, "rb") as f:
                    files = {"file": (file_path, f, mime_type)}
                    data = {"messaging_product": "whatsapp"}
                    headers = {"Authorization": f"Bearer {self.access_token}"}

                    response = await client.post(
                        url,
                        files=files,
                        data=data,
                        headers=headers,
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result.get("id")

        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return None

    async def download_media(
        self,
        media_id: str,
    ) -> Optional[bytes]:
        """
        Download media file.

        Args:
            media_id: WhatsApp media ID

        Returns:
            Media file bytes
        """
        try:
            # First, get media URL
            media_info = await self._make_request("GET", media_id)
            media_url = media_info.get("url")

            if not media_url:
                return None

            # Download media
            headers = {"Authorization": f"Bearer {self.access_token}"}

            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.get(media_url, headers=headers)
                    response.raise_for_status()
                    return response.content
            else:
                request = urllib.request.Request(media_url, headers=headers)
                with urllib.request.urlopen(request) as resp:
                    return resp.read()

        except Exception as e:
            logger.error(f"Failed to download media: {e}")
            return None

    def _format_number(self, number: str) -> str:
        """
        Format phone number for WhatsApp.

        WhatsApp Cloud API expects numbers without + prefix.
        E.g., "919876543210" for India
        """
        return number.lstrip("+")

    async def get_business_profile(self) -> Optional[dict]:
        """Get WhatsApp Business profile"""
        try:
            return await self._make_request(
                "GET",
                f"{self.phone_number_id}/whatsapp_business_profile?fields=about,address,description,email,profile_picture_url,websites,vertical",
            )
        except Exception as e:
            logger.error(f"Failed to get business profile: {e}")
            return None
