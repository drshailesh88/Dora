"""
SMS Providers

Supports:
- Twilio (international)
- MSG91 (India-optimized)
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# Try to import clients
try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False


@dataclass
class SMSResult:
    """Result of SMS send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class SMSProvider(ABC):
    """Base class for SMS providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def send(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> SMSResult:
        """Send an SMS message."""
        pass

    @abstractmethod
    async def get_status(self, message_id: str) -> Optional[str]:
        """Get delivery status of a message."""
        pass


class TwilioSMS(SMSProvider):
    """Twilio SMS provider."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER", "")

        if HAS_TWILIO and self.account_sid and self.auth_token:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "twilio"

    async def send(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> SMSResult:
        """Send SMS via Twilio."""
        from_number = sender_id or self.from_number

        if not from_number:
            return SMSResult(success=False, error="No sender number configured")

        try:
            if self._client:
                # Use Twilio SDK
                msg = self._client.messages.create(
                    to=to,
                    from_=from_number,
                    body=message,
                )
                return SMSResult(success=True, message_id=msg.sid)
            else:
                # Use HTTP API
                return await self._send_via_http(to, from_number, message)
        except Exception as e:
            return SMSResult(success=False, error=str(e))

    async def _send_via_http(
        self,
        to: str,
        from_number: str,
        message: str,
    ) -> SMSResult:
        """Send SMS via Twilio HTTP API."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

        data = {
            "To": to,
            "From": from_number,
            "Body": message,
        }

        if HAS_HTTPX:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                )
                if response.status_code == 201:
                    result = response.json()
                    return SMSResult(success=True, message_id=result.get("sid"))
                else:
                    return SMSResult(success=False, error=response.text)
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
                    return SMSResult(success=True, message_id=result.get("sid"))
            except Exception as e:
                return SMSResult(success=False, error=str(e))

    async def get_status(self, message_id: str) -> Optional[str]:
        """Get message delivery status."""
        if self._client:
            try:
                msg = self._client.messages(message_id).fetch()
                return msg.status
            except Exception:
                return None
        return None


class MSG91SMS(SMSProvider):
    """
    MSG91 SMS provider.

    Optimized for India with:
    - DLT registration support
    - Template-based messaging
    - Regional language support
    """

    API_URL = "https://api.msg91.com/api/v5/flow/"

    def __init__(
        self,
        auth_key: Optional[str] = None,
        sender_id: Optional[str] = None,
        dlt_template_id: Optional[str] = None,
    ):
        self.auth_key = auth_key or os.environ.get("MSG91_AUTH_KEY", "")
        self.sender_id = sender_id or os.environ.get("MSG91_SENDER_ID", "DORA")
        self.dlt_template_id = dlt_template_id or os.environ.get("MSG91_DLT_TEMPLATE_ID")

    @property
    def name(self) -> str:
        return "msg91"

    async def send(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None,
        template_id: Optional[str] = None,
        variables: Optional[dict] = None,
    ) -> SMSResult:
        """
        Send SMS via MSG91.

        For India, transactional SMS requires DLT registration.
        """
        # Format phone number for India
        phone = to.lstrip("+")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json",
        }

        # Use flow API for template-based sending
        data = {
            "flow_id": template_id or self.dlt_template_id,
            "sender": sender_id or self.sender_id,
            "mobiles": phone,
        }

        if variables:
            data.update(variables)

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        json=data,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("type") == "success":
                            return SMSResult(
                                success=True,
                                message_id=result.get("request_id"),
                            )
                        else:
                            return SMSResult(
                                success=False,
                                error=result.get("message", "Unknown error"),
                            )
                    else:
                        return SMSResult(success=False, error=response.text)
            else:
                req = urllib.request.Request(
                    self.API_URL,
                    data=json.dumps(data).encode(),
                    headers=headers,
                    method="POST",
                )

                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read())
                    if result.get("type") == "success":
                        return SMSResult(
                            success=True,
                            message_id=result.get("request_id"),
                        )
                    else:
                        return SMSResult(
                            success=False,
                            error=result.get("message", "Unknown error"),
                        )
        except Exception as e:
            return SMSResult(success=False, error=str(e))

    async def get_status(self, message_id: str) -> Optional[str]:
        """Get message delivery status."""
        url = f"https://api.msg91.com/api/v5/report?request_id={message_id}"

        headers = {"authkey": self.auth_key}

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("data", [{}])[0].get("status")
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as resp:
                    result = json.loads(resp.read())
                    return result.get("data", [{}])[0].get("status")
        except Exception:
            pass
        return None

    async def send_otp(
        self,
        phone: str,
        otp: str,
        expiry_minutes: int = 10,
    ) -> SMSResult:
        """Send OTP via MSG91 OTP API."""
        # Format phone number
        phone = phone.lstrip("+")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone

        url = "https://api.msg91.com/api/v5/otp"
        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json",
        }

        data = {
            "mobile": phone,
            "otp": otp,
            "sender": self.sender_id,
            "otp_expiry": expiry_minutes,
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=data, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        return SMSResult(
                            success=result.get("type") == "success",
                            message_id=result.get("request_id"),
                            error=result.get("message") if result.get("type") != "success" else None,
                        )
                    return SMSResult(success=False, error=response.text)
        except Exception as e:
            return SMSResult(success=False, error=str(e))

        return SMSResult(success=False, error="HTTP client not available")
