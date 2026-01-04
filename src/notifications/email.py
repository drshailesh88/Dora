"""
Email Providers

Supports:
- SendGrid
- AWS SES (future)
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
    HAS_SENDGRID = True
except ImportError:
    HAS_SENDGRID = False


@dataclass
class EmailResult:
    """Result of email send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    """Base class for email providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """Send an email."""
        pass

    @abstractmethod
    async def send_template(
        self,
        to: str,
        template_id: str,
        dynamic_data: dict,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailResult:
        """Send a templated email."""
        pass


class SendGridEmail(EmailProvider):
    """SendGrid email provider."""

    API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("SENDGRID_API_KEY", "")
        self.from_email = from_email or os.environ.get("SENDGRID_FROM_EMAIL", "noreply@docassist.in")
        self.from_name = from_name or os.environ.get("SENDGRID_FROM_NAME", "DocAssist Dora")

        if HAS_SENDGRID and self.api_key:
            self._client = SendGridAPIClient(self.api_key)
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "sendgrid"

    async def send(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """Send an email via SendGrid."""
        sender_email = from_email or self.from_email
        sender_name = from_name or self.from_name

        try:
            if self._client:
                message = Mail(
                    from_email=Email(sender_email, sender_name),
                    to_emails=To(to),
                    subject=subject,
                    plain_text_content=body,
                )

                if html_body:
                    message.add_content(Content("text/html", html_body))

                if reply_to:
                    message.reply_to = Email(reply_to)

                response = self._client.send(message)

                if response.status_code in [200, 201, 202]:
                    message_id = response.headers.get("X-Message-Id")
                    return EmailResult(success=True, message_id=message_id)
                else:
                    return EmailResult(success=False, error=response.body.decode())
            else:
                return await self._send_via_http(
                    to, subject, body, html_body,
                    sender_email, sender_name, reply_to
                )
        except Exception as e:
            return EmailResult(success=False, error=str(e))

    async def _send_via_http(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: Optional[str],
    ) -> EmailResult:
        """Send via SendGrid HTTP API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        content = [{"type": "text/plain", "value": body}]
        if html_body:
            content.append({"type": "text/html", "value": html_body})

        data = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": from_email, "name": from_name},
            "subject": subject,
            "content": content,
        }

        if reply_to:
            data["reply_to"] = {"email": reply_to}

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        json=data,
                        headers=headers,
                    )
                    if response.status_code in [200, 201, 202]:
                        message_id = response.headers.get("X-Message-Id")
                        return EmailResult(success=True, message_id=message_id)
                    else:
                        return EmailResult(success=False, error=response.text)
            else:
                req = urllib.request.Request(
                    self.API_URL,
                    data=json.dumps(data).encode(),
                    headers=headers,
                    method="POST",
                )

                with urllib.request.urlopen(req) as resp:
                    message_id = resp.headers.get("X-Message-Id")
                    return EmailResult(success=True, message_id=message_id)
        except Exception as e:
            return EmailResult(success=False, error=str(e))

    async def send_template(
        self,
        to: str,
        template_id: str,
        dynamic_data: dict,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailResult:
        """Send a templated email via SendGrid Dynamic Templates."""
        sender_email = from_email or self.from_email
        sender_name = from_name or self.from_name

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "personalizations": [{
                "to": [{"email": to}],
                "dynamic_template_data": dynamic_data,
            }],
            "from": {"email": sender_email, "name": sender_name},
            "template_id": template_id,
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.API_URL,
                        json=data,
                        headers=headers,
                    )
                    if response.status_code in [200, 201, 202]:
                        message_id = response.headers.get("X-Message-Id")
                        return EmailResult(success=True, message_id=message_id)
                    else:
                        return EmailResult(success=False, error=response.text)
            else:
                req = urllib.request.Request(
                    self.API_URL,
                    data=json.dumps(data).encode(),
                    headers=headers,
                    method="POST",
                )

                with urllib.request.urlopen(req) as resp:
                    message_id = resp.headers.get("X-Message-Id")
                    return EmailResult(success=True, message_id=message_id)
        except Exception as e:
            return EmailResult(success=False, error=str(e))

        return EmailResult(success=False, error="HTTP client not available")
