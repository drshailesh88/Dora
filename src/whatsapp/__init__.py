"""
WhatsApp Integration Module

Complete WhatsApp Business API integration for Dora.

Supports:
- Text and voice message queries
- Drug interaction checks
- Medical calculators
- Answer sharing with patients
- Group/team features
- Account linking
"""

from .client import WhatsAppClient, RateLimiter
from .models import (
    WhatsAppUser,
    WhatsAppMessage,
    WhatsAppResponse,
    MediaMessage,
    QuickReply,
    ConversationState,
    MessageType,
    MessageStatus,
    ConversationStatus,
    ConversationIntent,
)
from .webhook import WebhookHandler, WebhookParser, WebhookVerifier
from .conversation import ConversationManager
from .templates import MessageTemplates
from .media import MediaHandler
from .sharing import AnswerSharing
from .groups import GroupManager, WhatsAppGroup
from .service import WhatsAppService
from .storage import MessageStore

__all__ = [
    # Client
    "WhatsAppClient",
    "RateLimiter",
    # Models
    "WhatsAppUser",
    "WhatsAppMessage",
    "WhatsAppResponse",
    "MediaMessage",
    "QuickReply",
    "ConversationState",
    "MessageType",
    "MessageStatus",
    "ConversationStatus",
    "ConversationIntent",
    # Webhook
    "WebhookHandler",
    "WebhookParser",
    "WebhookVerifier",
    # Conversation
    "ConversationManager",
    # Templates
    "MessageTemplates",
    # Media
    "MediaHandler",
    # Sharing
    "AnswerSharing",
    # Groups
    "GroupManager",
    "WhatsAppGroup",
    # Service
    "WhatsAppService",
    # Storage
    "MessageStore",
]
