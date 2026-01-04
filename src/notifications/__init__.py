"""
Dora Notifications Module

Provides multi-channel notification support:
- SMS (via Twilio, MSG91)
- WhatsApp (via Twilio, Gupshup)
- Email (via SendGrid, SES)
- Push Notifications (via Firebase)
"""

from .service import NotificationService
from .sms import SMSProvider, TwilioSMS, MSG91SMS
from .whatsapp import WhatsAppProvider, TwilioWhatsApp, GupshupWhatsApp
from .email import EmailProvider, SendGridEmail
from .push import PushProvider, FirebasePush
from .models import (
    Notification,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
    NotificationTemplate,
)

__all__ = [
    "NotificationService",
    "SMSProvider",
    "TwilioSMS",
    "MSG91SMS",
    "WhatsAppProvider",
    "TwilioWhatsApp",
    "GupshupWhatsApp",
    "EmailProvider",
    "SendGridEmail",
    "PushProvider",
    "FirebasePush",
    "Notification",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationTemplate",
]
