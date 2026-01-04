"""
WhatsApp Data Models

Models for WhatsApp Business API integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class MessageType(str, Enum):
    """WhatsApp message types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    VOICE = "voice"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    TEMPLATE = "template"


class MessageStatus(str, Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    TIMEOUT = "timeout"


class ConversationIntent(str, Enum):
    """User intent in conversation"""
    QUERY = "query"
    DRUG_CHECK = "drug_check"
    CALCULATOR = "calculator"
    IMAGE_ANALYSIS = "image_analysis"
    VOICE_NOTE = "voice_note"
    HELP = "help"
    ONBOARDING = "onboarding"
    SHARE_ANSWER = "share_answer"
    UNKNOWN = "unknown"


@dataclass
class WhatsAppUser:
    """WhatsApp user linked to Dora account"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    whatsapp_id: str = ""  # WhatsApp ID (phone number)
    user_id: Optional[str] = None  # Linked Dora user ID
    name: Optional[str] = None

    # Link status
    is_linked: bool = False
    link_code: Optional[str] = None  # 6-digit code for linking
    link_code_expires: Optional[datetime] = None

    # Preferences
    language: str = "en"
    preferred_format: str = "concise"  # concise, detailed, patient_friendly
    voice_responses: bool = True
    notifications_enabled: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    linked_at: Optional[datetime] = None
    last_active: Optional[datetime] = None

    # Usage
    message_count: int = 0
    query_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "whatsapp_id": self.whatsapp_id,
            "user_id": self.user_id,
            "name": self.name,
            "is_linked": self.is_linked,
            "link_code": self.link_code,
            "link_code_expires": self.link_code_expires.isoformat() if self.link_code_expires else None,
            "language": self.language,
            "preferred_format": self.preferred_format,
            "voice_responses": self.voice_responses,
            "notifications_enabled": self.notifications_enabled,
            "created_at": self.created_at.isoformat(),
            "linked_at": self.linked_at.isoformat() if self.linked_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "message_count": self.message_count,
            "query_count": self.query_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WhatsAppUser":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            whatsapp_id=data.get("whatsapp_id", ""),
            user_id=data.get("user_id"),
            name=data.get("name"),
            is_linked=data.get("is_linked", False),
            link_code=data.get("link_code"),
            link_code_expires=datetime.fromisoformat(data["link_code_expires"]) if data.get("link_code_expires") else None,
            language=data.get("language", "en"),
            preferred_format=data.get("preferred_format", "concise"),
            voice_responses=data.get("voice_responses", True),
            notifications_enabled=data.get("notifications_enabled", True),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            linked_at=datetime.fromisoformat(data["linked_at"]) if data.get("linked_at") else None,
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None,
            message_count=data.get("message_count", 0),
            query_count=data.get("query_count", 0),
        )


@dataclass
class WhatsAppMessage:
    """Incoming WhatsApp message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = ""  # WhatsApp message ID
    from_number: str = ""
    to_number: str = ""

    # Content
    message_type: MessageType = MessageType.TEXT
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_id: Optional[str] = None
    mime_type: Optional[str] = None
    caption: Optional[str] = None

    # Context
    context_message_id: Optional[str] = None  # Reply to message

    # Interactive
    button_payload: Optional[str] = None
    list_reply_id: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    received_at: datetime = field(default_factory=datetime.utcnow)

    # Processing
    processed: bool = False
    processed_at: Optional[datetime] = None
    conversation_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "message_type": self.message_type.value,
            "text": self.text,
            "media_url": self.media_url,
            "media_id": self.media_id,
            "mime_type": self.mime_type,
            "caption": self.caption,
            "context_message_id": self.context_message_id,
            "button_payload": self.button_payload,
            "list_reply_id": self.list_reply_id,
            "timestamp": self.timestamp.isoformat(),
            "received_at": self.received_at.isoformat(),
            "processed": self.processed,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "conversation_id": self.conversation_id,
        }


@dataclass
class WhatsAppResponse:
    """Outgoing WhatsApp response"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    to_number: str = ""

    # Content
    message_type: MessageType = MessageType.TEXT
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_id: Optional[str] = None
    caption: Optional[str] = None

    # Interactive
    buttons: Optional[list[dict]] = None
    list_sections: Optional[list[dict]] = None
    header: Optional[str] = None
    footer: Optional[str] = None

    # Context
    context_message_id: Optional[str] = None  # Reply to message

    # Status
    status: MessageStatus = MessageStatus.SENT
    message_id: Optional[str] = None  # WhatsApp message ID

    # Timestamps
    sent_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    # Metadata
    conversation_id: Optional[str] = None
    query_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "to_number": self.to_number,
            "message_type": self.message_type.value,
            "text": self.text,
            "media_url": self.media_url,
            "media_id": self.media_id,
            "caption": self.caption,
            "buttons": self.buttons,
            "list_sections": self.list_sections,
            "header": self.header,
            "footer": self.footer,
            "context_message_id": self.context_message_id,
            "status": self.status.value,
            "message_id": self.message_id,
            "sent_at": self.sent_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "conversation_id": self.conversation_id,
            "query_id": self.query_id,
        }


@dataclass
class MediaMessage:
    """Media message (image/audio/document)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    media_id: str = ""  # WhatsApp media ID
    media_url: Optional[str] = None  # Downloaded URL
    local_path: Optional[str] = None  # Local file path

    media_type: MessageType = MessageType.IMAGE
    mime_type: str = ""
    file_size: Optional[int] = None

    # Processing
    downloaded: bool = False
    transcribed: bool = False
    transcription: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuickReply:
    """Quick reply button"""
    id: str
    title: str

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title}


@dataclass
class ConversationState:
    """Conversation state tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    whatsapp_id: str = ""
    user_id: Optional[str] = None

    # State
    status: ConversationStatus = ConversationStatus.ACTIVE
    intent: ConversationIntent = ConversationIntent.UNKNOWN

    # Context
    context: dict[str, Any] = field(default_factory=dict)
    last_query: Optional[str] = None
    last_answer_id: Optional[str] = None
    awaiting_input: Optional[str] = None  # What we're waiting for

    # History
    message_count: int = 0
    last_message_at: datetime = field(default_factory=datetime.utcnow)

    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "whatsapp_id": self.whatsapp_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "intent": self.intent.value,
            "context": self.context,
            "last_query": self.last_query,
            "last_answer_id": self.last_answer_id,
            "awaiting_input": self.awaiting_input,
            "message_count": self.message_count,
            "last_message_at": self.last_message_at.isoformat(),
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationState":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            whatsapp_id=data.get("whatsapp_id", ""),
            user_id=data.get("user_id"),
            status=ConversationStatus(data.get("status", "active")),
            intent=ConversationIntent(data.get("intent", "unknown")),
            context=data.get("context", {}),
            last_query=data.get("last_query"),
            last_answer_id=data.get("last_answer_id"),
            awaiting_input=data.get("awaiting_input"),
            message_count=data.get("message_count", 0),
            last_message_at=datetime.fromisoformat(data["last_message_at"]) if "last_message_at" in data else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if "started_at" in data else datetime.utcnow(),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
            timeout_at=datetime.fromisoformat(data["timeout_at"]) if data.get("timeout_at") else None,
        )

    def is_active(self) -> bool:
        """Check if conversation is still active"""
        return self.status == ConversationStatus.ACTIVE

    def should_timeout(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation should timeout"""
        if not self.is_active():
            return False

        inactive_minutes = (datetime.utcnow() - self.last_message_at).total_seconds() / 60
        return inactive_minutes > timeout_minutes
