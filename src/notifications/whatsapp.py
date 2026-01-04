"""
WhatsApp Providers

Supports:
- Twilio WhatsApp
- Gupshup (popular in India)
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False

try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False


@dataclass
class WhatsAppResult:
    """Result of WhatsApp send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class WhatsAppProvider(ABC):
    """Base class for WhatsApp providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def send_template(
        self,
        to: str,
        template_name: str,
        template_namespace: str,
        variables: list[str],
        language: str = "en",
    ) -> WhatsAppResult:
        """Send a template message."""
        pass

    @abstractmethod
    async def send_text(
        self,
        to: str,
        message: str,
    ) -> WhatsAppResult:
        """Send a text message (within 24h window)."""
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> Optional[str]:
        """Get message delivery status."""
        pass


class TwilioWhatsApp(WhatsAppProvider):
    """Twilio WhatsApp provider."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

        if HAS_TWILIO and self.account_sid and self.auth_token:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "twilio_whatsapp"

    def _format_number(self, number: str) -> str:
        """Format number for WhatsApp."""
        number = number.lstrip("+")
        return f"whatsapp:+{number}"

    async def send_template(
        self,
        to: str,
        template_name: str,
        template_namespace: str,
        variables: list[str],
        language: str = "en",
    ) -> WhatsAppResult:
        """Send a template message via Twilio Content API."""
        to = self._format_number(to)
        from_number = self._format_number(self.from_number)

        # Twilio uses Content SID for templates
        content_variables = {str(i + 1): v for i, v in enumerate(variables)}

        try:
            if self._client:
                msg = self._client.messages.create(
                    to=to,
                    from_=from_number,
                    content_sid=template_name,  # Content SID
                    content_variables=json.dumps(content_variables),
                )
                return WhatsAppResult(success=True, message_id=msg.sid)
            else:
                return await self._send_via_http(to, from_number, None, template_name, content_variables)
        except Exception as e:
            return WhatsAppResult(success=False, error=str(e))

    async def send_text(
        self,
        to: str,
        message: str,
    ) -> WhatsAppResult:
        """Send a text message."""
        to = self._format_number(to)
        from_number = self._format_number(self.from_number)

        try:
            if self._client:
                msg = self._client.messages.create(
                    to=to,
                    from_=from_number,
                    body=message,
                )
                return WhatsAppResult(success=True, message_id=msg.sid)
            else:
                return await self._send_via_http(to, from_number, message, None, None)
        except Exception as e:
            return WhatsAppResult(success=False, error=str(e))

    async def _send_via_http(
        self,
        to: str,
        from_number: str,
        message: Optional[str],
        content_sid: Optional[str],
        content_variables: Optional[dict],
    ) -> WhatsAppResult:
        """Send via Twilio HTTP API."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        data = {
            "To": to,
            "From": from_number,
        }

        if message:
            data["Body"] = message
        if content_sid:
            data["ContentSid"] = content_sid
            if content_variables:
                data["ContentVariables"] = json.dumps(content_variables)

        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                )
                if response.status_code == 201:
                    result = response.json()
                    return WhatsAppResult(success=True, message_id=result.get("sid"))
                else:
                    return WhatsAppResult(success=False, error=response.text)
        else:
            import base64
            from urllib.parse import urlencode

            credentials = base64.b64encode(
                f"{self.account_sid}:{self.auth_token}".encode()
            ).decode()

            req = urllib.request.Request(
                url,
                data=urlencode(data).encode(),
                headers={"Authorization": f"Basic {credentials}"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read())
                    return WhatsAppResult(success=True, message_id=result.get("sid"))
            except Exception as e:
                return WhatsAppResult(success=False, error=str(e))

    async def get_status(self, message_id: str) -> Optional[str]:
        """Get message status."""
        if self._client:
            try:
                msg = self._client.messages(message_id).fetch()
                return msg.status
            except Exception:
                pass
        return None


class GupshupWhatsApp(WhatsAppProvider):
    """
    Gupshup WhatsApp provider.

    Popular in India for WhatsApp Business API.
    """

    API_URL = "https://api.gupshup.io/sm/api/v1/msg"

    def __init__(
        self,
        api_key: Optional[str] = None,
        app_name: Optional[str] = None,
        source_number: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("GUPSHUP_API_KEY", "")
        self.app_name = app_name or os.environ.get("GUPSHUP_APP_NAME", "")
        self.source_number = source_number or os.environ.get("GUPSHUP_SOURCE_NUMBER", "")

    @property
    def name(self) -> str:
        return "gupshup"

    def _format_number(self, number: str) -> str:
        """Format number for Gupshup (without + prefix)."""
        return number.lstrip("+")

    async def send_template(
        self,
        to: str,
        template_name: str,
        template_namespace: str,
        variables: list[str],
        language: str = "en",
    ) -> WhatsAppResult:
        """Send a template message via Gupshup."""
        to = self._format_number(to)
        source = self._format_number(self.source_number)

        # Build template payload
        template_payload = {
            "id": template_namespace,
            "params": variables,
        }

        message = {
            "type": "template",
            "template": template_payload,
        }

        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "channel": "whatsapp",
            "source": source,
            "destination": to,
            "message": json.dumps(message),
            "src.name": self.app_name,
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        data=data,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "submitted":
                            return WhatsAppResult(
                                success=True,
                                message_id=result.get("messageId"),
                            )
                        else:
                            return WhatsAppResult(
                                success=False,
                                error=result.get("message", "Unknown error"),
                            )
                    else:
                        return WhatsAppResult(success=False, error=response.text)
            else:
                from urllib.parse import urlencode

                req = urllib.request.Request(
                    self.API_URL,
                    data=urlencode(data).encode(),
                    headers=headers,
                    method="POST",
                )

                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read())
                    if result.get("status") == "submitted":
                        return WhatsAppResult(
                            success=True,
                            message_id=result.get("messageId"),
                        )
                    else:
                        return WhatsAppResult(
                            success=False,
                            error=result.get("message"),
                        )
        except Exception as e:
            return WhatsAppResult(success=False, error=str(e))

    async def send_text(
        self,
        to: str,
        message: str,
    ) -> WhatsAppResult:
        """Send a text message via Gupshup."""
        to = self._format_number(to)
        source = self._format_number(self.source_number)

        msg_payload = {
            "type": "text",
            "text": message,
        }

        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "channel": "whatsapp",
            "source": source,
            "destination": to,
            "message": json.dumps(msg_payload),
            "src.name": self.app_name,
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        data=data,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "submitted":
                            return WhatsAppResult(
                                success=True,
                                message_id=result.get("messageId"),
                            )
                        else:
                            return WhatsAppResult(
                                success=False,
                                error=result.get("message"),
                            )
                    else:
                        return WhatsAppResult(success=False, error=response.text)
        except Exception as e:
            return WhatsAppResult(success=False, error=str(e))

        return WhatsAppResult(success=False, error="HTTP client not available")

    async def get_status(self, message_id: str) -> Optional[str]:
        """Get message status - Gupshup uses webhooks for status."""
        # Gupshup provides status via webhooks, not API polling
        return None

    async def send_media(
        self,
        to: str,
        media_type: str,  # image, video, audio, file
        media_url: str,
        caption: Optional[str] = None,
    ) -> WhatsAppResult:
        """Send a media message via Gupshup."""
        to = self._format_number(to)
        source = self._format_number(self.source_number)

        msg_payload = {
            "type": media_type,
            "originalUrl": media_url,
            "previewUrl": media_url,
        }

        if caption:
            msg_payload["caption"] = caption

        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "channel": "whatsapp",
            "source": source,
            "destination": to,
            "message": json.dumps(msg_payload),
            "src.name": self.app_name,
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        data=data,
                        headers=headers,
                    )
                    result = response.json()
                    if result.get("status") == "submitted":
                        return WhatsAppResult(
                            success=True,
                            message_id=result.get("messageId"),
                        )
                    else:
                        return WhatsAppResult(
                            success=False,
                            error=result.get("message"),
                        )
        except Exception as e:
            return WhatsAppResult(success=False, error=str(e))

        return WhatsAppResult(success=False, error="HTTP client not available")
