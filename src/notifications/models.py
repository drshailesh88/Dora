"""
Notification Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(str, Enum):
    """Types of notifications."""
    # Auth
    VERIFICATION_CODE = "verification_code"
    PASSWORD_RESET = "password_reset"
    LOGIN_ALERT = "login_alert"

    # Subscription
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    TRIAL_ENDING = "trial_ending"

    # Medical
    DRUG_INTERACTION_ALERT = "drug_interaction_alert"
    QUERY_RESPONSE = "query_response"

    # System
    WELCOME = "welcome"
    SYSTEM_UPDATE = "system_update"
    MAINTENANCE = "maintenance"

    # Reminders
    APPOINTMENT_REMINDER = "appointment_reminder"
    FOLLOW_UP_REMINDER = "follow_up_reminder"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationPriority(str, Enum):
    """Notification priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationTemplate:
    """Template for notifications."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    notification_type: NotificationType = NotificationType.WELCOME
    channel: NotificationChannel = NotificationChannel.SMS

    # Content
    subject: Optional[str] = None  # For email
    body: str = ""  # Message body with {{placeholders}}
    html_body: Optional[str] = None  # HTML version for email

    # WhatsApp specific
    whatsapp_template_id: Optional[str] = None
    whatsapp_template_namespace: Optional[str] = None

    # SMS specific
    sms_sender_id: Optional[str] = None

    # Metadata
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def render(self, context: dict[str, Any]) -> str:
        """Render template with context."""
        content = self.body
        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content

    def render_html(self, context: dict[str, Any]) -> Optional[str]:
        """Render HTML template with context."""
        if not self.html_body:
            return None
        content = self.html_body
        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content


@dataclass
class Notification:
    """Notification record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Type and channel
    notification_type: NotificationType = NotificationType.WELCOME
    channel: NotificationChannel = NotificationChannel.SMS
    priority: NotificationPriority = NotificationPriority.NORMAL

    # Recipient
    recipient: str = ""  # Phone, email, device token

    # Content
    subject: Optional[str] = None
    body: str = ""
    html_body: Optional[str] = None

    # Context data
    context: dict[str, Any] = field(default_factory=dict)

    # Status
    status: NotificationStatus = NotificationStatus.PENDING

    # Provider details
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Error
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Retry
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None

    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.retry_count < self.max_retries

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type.value,
            "channel": self.channel.value,
            "priority": self.priority.value,
            "recipient": self.recipient[:4] + "***" if self.recipient else None,
            "subject": self.subject,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }


@dataclass
class UserNotificationPreferences:
    """User notification preferences."""
    user_id: str = ""

    # Channel preferences
    sms_enabled: bool = True
    whatsapp_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True

    # Phone numbers
    phone: Optional[str] = None
    whatsapp_phone: Optional[str] = None  # If different from phone

    # Email
    email: Optional[str] = None

    # Device tokens for push
    device_tokens: list[str] = field(default_factory=list)

    # Type preferences (which types to receive on which channel)
    preferred_channel: NotificationChannel = NotificationChannel.WHATSAPP

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_start: Optional[str] = None  # "22:00"
    quiet_end: Optional[str] = None  # "07:00"

    # Language
    language: str = "en"

    def get_recipient(self, channel: NotificationChannel) -> Optional[str]:
        """Get recipient for channel."""
        if channel == NotificationChannel.SMS:
            return self.phone if self.sms_enabled else None
        elif channel == NotificationChannel.WHATSAPP:
            return (self.whatsapp_phone or self.phone) if self.whatsapp_enabled else None
        elif channel == NotificationChannel.EMAIL:
            return self.email if self.email_enabled else None
        elif channel == NotificationChannel.PUSH:
            return self.device_tokens[0] if self.device_tokens and self.push_enabled else None
        return None


# Default templates
DEFAULT_TEMPLATES = [
    NotificationTemplate(
        id="verification_code_sms",
        name="Verification Code SMS",
        notification_type=NotificationType.VERIFICATION_CODE,
        channel=NotificationChannel.SMS,
        body="Your Dora verification code is {{code}}. Valid for 10 minutes. Do not share this code.",
    ),
    NotificationTemplate(
        id="verification_code_whatsapp",
        name="Verification Code WhatsApp",
        notification_type=NotificationType.VERIFICATION_CODE,
        channel=NotificationChannel.WHATSAPP,
        body="Your Dora verification code is *{{code}}*. Valid for 10 minutes.\n\nDo not share this code with anyone.",
    ),
    NotificationTemplate(
        id="welcome_email",
        name="Welcome Email",
        notification_type=NotificationType.WELCOME,
        channel=NotificationChannel.EMAIL,
        subject="Welcome to Dora - Your Medical Knowledge Partner",
        body="""Hi {{name}},

Welcome to Dora! We're excited to have you on board.

Dora is your AI-powered medical knowledge assistant, helping you access evidence-based medical information instantly.

Getting Started:
1. Download our mobile app for iOS and Android
2. Ask your first medical question
3. Explore drug interaction checker

If you have any questions, our support team is here to help.

Best regards,
The DocAssist Team""",
    ),
    NotificationTemplate(
        id="payment_received_sms",
        name="Payment Received SMS",
        notification_type=NotificationType.PAYMENT_RECEIVED,
        channel=NotificationChannel.SMS,
        body="Payment of Rs.{{amount}} received for Dora {{plan}} subscription. Invoice: {{invoice_number}}. Thank you!",
    ),
    NotificationTemplate(
        id="trial_ending_sms",
        name="Trial Ending SMS",
        notification_type=NotificationType.TRIAL_ENDING,
        channel=NotificationChannel.SMS,
        body="Your Dora trial ends in {{days}} days. Upgrade now to continue enjoying premium features. Visit app to upgrade.",
    ),
    NotificationTemplate(
        id="drug_interaction_alert",
        name="Drug Interaction Alert",
        notification_type=NotificationType.DRUG_INTERACTION_ALERT,
        channel=NotificationChannel.WHATSAPP,
        body="""⚠️ *Drug Interaction Alert*

A potential interaction was detected between:
- {{drug1}}
- {{drug2}}

Severity: *{{severity}}*

{{description}}

Please review the patient's medication list.""",
    ),
]
