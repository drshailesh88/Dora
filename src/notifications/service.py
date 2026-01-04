"""
Notification Service

Central service for sending notifications across all channels.
"""

import os
from datetime import datetime
from typing import Optional, Any

from .models import (
    Notification, NotificationType, NotificationChannel,
    NotificationStatus, NotificationPriority,
    NotificationTemplate, UserNotificationPreferences,
    DEFAULT_TEMPLATES,
)
from .sms import SMSProvider, TwilioSMS, MSG91SMS
from .whatsapp import WhatsAppProvider, TwilioWhatsApp, GupshupWhatsApp
from .email import EmailProvider, SendGridEmail
from .push import PushProvider, FirebasePush


class NotificationService:
    """
    Central notification service.

    Features:
    - Multi-channel support (SMS, WhatsApp, Email, Push)
    - Template-based notifications
    - User preferences
    - Retry logic
    - Delivery tracking
    """

    def __init__(
        self,
        sms_provider: Optional[SMSProvider] = None,
        whatsapp_provider: Optional[WhatsAppProvider] = None,
        email_provider: Optional[EmailProvider] = None,
        push_provider: Optional[PushProvider] = None,
    ):
        # Initialize providers
        self.sms = sms_provider or self._init_sms_provider()
        self.whatsapp = whatsapp_provider or self._init_whatsapp_provider()
        self.email = email_provider or self._init_email_provider()
        self.push = push_provider or self._init_push_provider()

        # Template storage
        self.templates: dict[str, NotificationTemplate] = {
            t.id: t for t in DEFAULT_TEMPLATES
        }

    def _init_sms_provider(self) -> Optional[SMSProvider]:
        """Initialize SMS provider based on environment."""
        # Prefer MSG91 for India
        if os.environ.get("MSG91_AUTH_KEY"):
            return MSG91SMS()
        elif os.environ.get("TWILIO_ACCOUNT_SID"):
            return TwilioSMS()
        return None

    def _init_whatsapp_provider(self) -> Optional[WhatsAppProvider]:
        """Initialize WhatsApp provider based on environment."""
        # Prefer Gupshup for India
        if os.environ.get("GUPSHUP_API_KEY"):
            return GupshupWhatsApp()
        elif os.environ.get("TWILIO_WHATSAPP_NUMBER"):
            return TwilioWhatsApp()
        return None

    def _init_email_provider(self) -> Optional[EmailProvider]:
        """Initialize email provider based on environment."""
        if os.environ.get("SENDGRID_API_KEY"):
            return SendGridEmail()
        return None

    def _init_push_provider(self) -> Optional[PushProvider]:
        """Initialize push provider based on environment."""
        if os.environ.get("FIREBASE_CREDENTIALS_PATH"):
            return FirebasePush()
        return None

    # Template management
    def register_template(self, template: NotificationTemplate) -> None:
        """Register a notification template."""
        self.templates[template.id] = template

    def get_template(
        self,
        notification_type: NotificationType,
        channel: NotificationChannel,
    ) -> Optional[NotificationTemplate]:
        """Get template for type and channel."""
        for template in self.templates.values():
            if (
                template.notification_type == notification_type
                and template.channel == channel
                and template.is_active
            ):
                return template
        return None

    # Send notifications
    async def send(
        self,
        user_id: str,
        notification_type: NotificationType,
        channel: NotificationChannel,
        recipient: str,
        context: dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_id: Optional[str] = None,
    ) -> Notification:
        """
        Send a notification.

        Args:
            user_id: User ID
            notification_type: Type of notification
            channel: Delivery channel
            recipient: Phone, email, or device token
            context: Template variables
            priority: Priority level
            template_id: Optional specific template ID

        Returns:
            Notification record with status
        """
        # Get template
        template = None
        if template_id:
            template = self.templates.get(template_id)
        else:
            template = self.get_template(notification_type, channel)

        if not template:
            return Notification(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                context=context,
                status=NotificationStatus.FAILED,
                error_message="No template found",
            )

        # Render template
        body = template.render(context)
        html_body = template.render_html(context) if template.html_body else None
        subject = template.subject
        if subject:
            for key, value in context.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))

        # Create notification record
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            recipient=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
            context=context,
            status=NotificationStatus.PENDING,
        )

        # Send based on channel
        try:
            if channel == NotificationChannel.SMS:
                result = await self._send_sms(recipient, body, template)
            elif channel == NotificationChannel.WHATSAPP:
                result = await self._send_whatsapp(recipient, body, template, context)
            elif channel == NotificationChannel.EMAIL:
                result = await self._send_email(recipient, subject or "", body, html_body)
            elif channel == NotificationChannel.PUSH:
                result = await self._send_push(recipient, subject or "Dora", body, context)
            else:
                result = (False, None, "Unsupported channel")

            success, message_id, error = result

            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                notification.provider_message_id = message_id
                notification.provider = self._get_provider_name(channel)
            else:
                notification.status = NotificationStatus.FAILED
                notification.failed_at = datetime.utcnow()
                notification.error_message = error

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.error_message = str(e)

        return notification

    async def _send_sms(
        self,
        recipient: str,
        body: str,
        template: NotificationTemplate,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send SMS."""
        if not self.sms:
            return False, None, "SMS provider not configured"

        result = await self.sms.send(
            to=recipient,
            message=body,
            sender_id=template.sms_sender_id,
        )
        return result.success, result.message_id, result.error

    async def _send_whatsapp(
        self,
        recipient: str,
        body: str,
        template: NotificationTemplate,
        context: dict[str, Any],
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send WhatsApp message."""
        if not self.whatsapp:
            return False, None, "WhatsApp provider not configured"

        # Use template if configured
        if template.whatsapp_template_id:
            result = await self.whatsapp.send_template(
                to=recipient,
                template_name=template.whatsapp_template_id,
                template_namespace=template.whatsapp_template_namespace or "",
                variables=list(context.values()),
            )
        else:
            result = await self.whatsapp.send_text(
                to=recipient,
                message=body,
            )
        return result.success, result.message_id, result.error

    async def _send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str],
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send email."""
        if not self.email:
            return False, None, "Email provider not configured"

        result = await self.email.send(
            to=recipient,
            subject=subject,
            body=body,
            html_body=html_body,
        )
        return result.success, result.message_id, result.error

    async def _send_push(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send push notification."""
        if not self.push:
            return False, None, "Push provider not configured"

        # Convert data values to strings for FCM
        str_data = {k: str(v) for k, v in data.items()}

        result = await self.push.send(
            token=token,
            title=title,
            body=body,
            data=str_data,
        )
        return result.success, result.message_id, result.error

    def _get_provider_name(self, channel: NotificationChannel) -> Optional[str]:
        """Get provider name for channel."""
        if channel == NotificationChannel.SMS and self.sms:
            return self.sms.name
        elif channel == NotificationChannel.WHATSAPP and self.whatsapp:
            return self.whatsapp.name
        elif channel == NotificationChannel.EMAIL and self.email:
            return self.email.name
        elif channel == NotificationChannel.PUSH and self.push:
            return self.push.name
        return None

    # Convenience methods for common notifications
    async def send_verification_code(
        self,
        user_id: str,
        phone: str,
        code: str,
        channel: NotificationChannel = NotificationChannel.SMS,
    ) -> Notification:
        """Send verification code."""
        return await self.send(
            user_id=user_id,
            notification_type=NotificationType.VERIFICATION_CODE,
            channel=channel,
            recipient=phone,
            context={"code": code},
            priority=NotificationPriority.HIGH,
        )

    async def send_welcome(
        self,
        user_id: str,
        email: str,
        name: str,
    ) -> Notification:
        """Send welcome email."""
        return await self.send(
            user_id=user_id,
            notification_type=NotificationType.WELCOME,
            channel=NotificationChannel.EMAIL,
            recipient=email,
            context={"name": name},
        )

    async def send_payment_confirmation(
        self,
        user_id: str,
        phone: str,
        amount: int,
        plan: str,
        invoice_number: str,
    ) -> Notification:
        """Send payment confirmation."""
        return await self.send(
            user_id=user_id,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            channel=NotificationChannel.SMS,
            recipient=phone,
            context={
                "amount": amount / 100,  # Convert paise to rupees
                "plan": plan,
                "invoice_number": invoice_number,
            },
        )

    async def send_drug_interaction_alert(
        self,
        user_id: str,
        phone: str,
        drug1: str,
        drug2: str,
        severity: str,
        description: str,
    ) -> Notification:
        """Send drug interaction alert via WhatsApp."""
        return await self.send(
            user_id=user_id,
            notification_type=NotificationType.DRUG_INTERACTION_ALERT,
            channel=NotificationChannel.WHATSAPP,
            recipient=phone,
            context={
                "drug1": drug1,
                "drug2": drug2,
                "severity": severity,
                "description": description,
            },
            priority=NotificationPriority.URGENT,
        )

    async def send_trial_ending(
        self,
        user_id: str,
        phone: str,
        days_remaining: int,
    ) -> Notification:
        """Send trial ending reminder."""
        return await self.send(
            user_id=user_id,
            notification_type=NotificationType.TRIAL_ENDING,
            channel=NotificationChannel.SMS,
            recipient=phone,
            context={"days": days_remaining},
        )

    # Multi-channel sending
    async def send_to_user(
        self,
        user_id: str,
        notification_type: NotificationType,
        preferences: UserNotificationPreferences,
        context: dict[str, Any],
        channels: Optional[list[NotificationChannel]] = None,
    ) -> list[Notification]:
        """
        Send notification to user based on preferences.

        Sends to all enabled channels or specified channels.
        """
        results = []

        if channels is None:
            # Use preferred channel
            channels = [preferences.preferred_channel]

        for channel in channels:
            recipient = preferences.get_recipient(channel)
            if not recipient:
                continue

            notification = await self.send(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                context=context,
            )
            results.append(notification)

        return results

    # Status check
    async def check_status(
        self,
        notification: Notification,
    ) -> Optional[str]:
        """Check delivery status of a notification."""
        if not notification.provider_message_id:
            return None

        if notification.channel == NotificationChannel.SMS and self.sms:
            return await self.sms.get_status(notification.provider_message_id)
        elif notification.channel == NotificationChannel.WHATSAPP and self.whatsapp:
            return await self.whatsapp.get_status(notification.provider_message_id)

        return None


# Default instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the default notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
