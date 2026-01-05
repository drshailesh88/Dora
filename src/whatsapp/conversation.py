"""
Conversation Manager

Manages multi-turn conversations with context tracking.
"""

import json
import logging
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

from .models import (
    WhatsAppUser,
    ConversationState,
    ConversationStatus,
    ConversationIntent,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages WhatsApp conversations.

    Tracks conversation state, user context, and session timeouts.
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        session_timeout_minutes: int = 30,
    ):
        """
        Initialize conversation manager.

        Args:
            storage_dir: Directory to store conversation state
            session_timeout_minutes: Minutes of inactivity before timeout
        """
        self.storage_dir = Path(storage_dir or "./data/whatsapp")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.session_timeout_minutes = session_timeout_minutes

        # In-memory cache
        self._users: dict[str, WhatsAppUser] = {}
        self._conversations: dict[str, ConversationState] = {}

        # Load from disk
        self._load_all()

    # User Management

    def get_or_create_user(self, whatsapp_id: str, name: Optional[str] = None) -> WhatsAppUser:
        """
        Get or create a WhatsApp user.

        Args:
            whatsapp_id: WhatsApp phone number
            name: User name (optional)

        Returns:
            WhatsAppUser
        """
        if whatsapp_id in self._users:
            user = self._users[whatsapp_id]
            # Update last active
            user.last_active = datetime.utcnow()
            self._save_user(user)
            return user

        # Create new user
        user = WhatsAppUser(
            whatsapp_id=whatsapp_id,
            name=name,
        )
        self._users[whatsapp_id] = user
        self._save_user(user)

        logger.info(f"Created new WhatsApp user: {whatsapp_id}")
        return user

    def get_user(self, whatsapp_id: str) -> Optional[WhatsAppUser]:
        """Get user by WhatsApp ID"""
        return self._users.get(whatsapp_id)

    def get_user_by_dora_id(self, user_id: str) -> Optional[WhatsAppUser]:
        """
        Get WhatsApp user by Dora user ID (reverse lookup).

        Args:
            user_id: Dora user ID

        Returns:
            WhatsAppUser if found, None otherwise
        """
        for user in self._users.values():
            if user.user_id == user_id and user.is_linked:
                return user
        return None

    def get_whatsapp_id_by_user_id(self, user_id: str) -> Optional[str]:
        """
        Get WhatsApp ID by Dora user ID (reverse lookup).

        Args:
            user_id: Dora user ID

        Returns:
            WhatsApp ID if found, None otherwise
        """
        user = self.get_user_by_dora_id(user_id)
        return user.whatsapp_id if user else None

    def link_user(
        self,
        whatsapp_id: str,
        user_id: str,
    ) -> WhatsAppUser:
        """
        Link WhatsApp account to Dora user.

        Args:
            whatsapp_id: WhatsApp phone number
            user_id: Dora user ID

        Returns:
            Updated WhatsAppUser
        """
        user = self.get_or_create_user(whatsapp_id)
        user.user_id = user_id
        user.is_linked = True
        user.linked_at = datetime.utcnow()
        user.link_code = None  # Clear link code
        user.link_code_expires = None

        self._save_user(user)
        logger.info(f"Linked WhatsApp {whatsapp_id} to user {user_id}")

        return user

    def unlink_user(self, whatsapp_id: str) -> WhatsAppUser:
        """Unlink WhatsApp account"""
        user = self.get_or_create_user(whatsapp_id)
        user.user_id = None
        user.is_linked = False
        user.linked_at = None

        self._save_user(user)
        logger.info(f"Unlinked WhatsApp {whatsapp_id}")

        return user

    def generate_link_code(self, whatsapp_id: str) -> str:
        """
        Generate a 6-digit link code.

        Args:
            whatsapp_id: WhatsApp phone number

        Returns:
            6-digit code
        """
        user = self.get_or_create_user(whatsapp_id)

        # Generate random 6-digit code
        code = "".join(random.choices(string.digits, k=6))

        # Set code with 15-minute expiry
        user.link_code = code
        user.link_code_expires = datetime.utcnow() + timedelta(minutes=15)

        self._save_user(user)
        logger.info(f"Generated link code for {whatsapp_id}")

        return code

    def verify_link_code(self, code: str) -> Optional[str]:
        """
        Verify a link code and return WhatsApp ID.

        Args:
            code: 6-digit code

        Returns:
            WhatsApp ID if valid, None otherwise
        """
        for user in self._users.values():
            if user.link_code == code:
                # Check expiry
                if user.link_code_expires and datetime.utcnow() < user.link_code_expires:
                    return user.whatsapp_id
                else:
                    logger.warning(f"Expired link code: {code}")
                    return None

        return None

    # Conversation Management

    def get_or_create_conversation(self, whatsapp_id: str) -> ConversationState:
        """
        Get or create active conversation.

        Args:
            whatsapp_id: WhatsApp phone number

        Returns:
            ConversationState
        """
        # Check if active conversation exists
        if whatsapp_id in self._conversations:
            conv = self._conversations[whatsapp_id]

            # Check timeout
            if conv.should_timeout(self.session_timeout_minutes):
                logger.info(f"Conversation timed out for {whatsapp_id}")
                conv.status = ConversationStatus.TIMEOUT
                conv.ended_at = datetime.utcnow()
                self._save_conversation(conv)

                # Create new conversation
                conv = self._create_new_conversation(whatsapp_id)
            else:
                # Update last message time
                conv.last_message_at = datetime.utcnow()
                self._save_conversation(conv)

            return conv

        # Create new conversation
        return self._create_new_conversation(whatsapp_id)

    def _create_new_conversation(self, whatsapp_id: str) -> ConversationState:
        """Create a new conversation"""
        # Get user
        user = self.get_or_create_user(whatsapp_id)

        conv = ConversationState(
            whatsapp_id=whatsapp_id,
            user_id=user.user_id,
        )

        self._conversations[whatsapp_id] = conv
        self._save_conversation(conv)

        logger.info(f"Created new conversation for {whatsapp_id}")
        return conv

    def get_conversation(self, whatsapp_id: str) -> Optional[ConversationState]:
        """Get active conversation"""
        return self._conversations.get(whatsapp_id)

    def update_conversation(
        self,
        whatsapp_id: str,
        **kwargs: Any,
    ) -> ConversationState:
        """
        Update conversation state.

        Args:
            whatsapp_id: WhatsApp phone number
            **kwargs: Fields to update

        Returns:
            Updated conversation
        """
        conv = self.get_or_create_conversation(whatsapp_id)

        for key, value in kwargs.items():
            if hasattr(conv, key):
                setattr(conv, key, value)

        conv.last_message_at = datetime.utcnow()
        conv.message_count += 1

        self._save_conversation(conv)
        return conv

    def set_conversation_intent(
        self,
        whatsapp_id: str,
        intent: ConversationIntent,
    ) -> ConversationState:
        """Set conversation intent"""
        return self.update_conversation(whatsapp_id, intent=intent)

    def set_context(
        self,
        whatsapp_id: str,
        key: str,
        value: Any,
    ) -> ConversationState:
        """
        Set context value.

        Args:
            whatsapp_id: WhatsApp phone number
            key: Context key
            value: Context value

        Returns:
            Updated conversation
        """
        conv = self.get_or_create_conversation(whatsapp_id)
        conv.context[key] = value
        self._save_conversation(conv)
        return conv

    def get_context(
        self,
        whatsapp_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get context value"""
        conv = self.get_conversation(whatsapp_id)
        if not conv:
            return default
        return conv.context.get(key, default)

    def clear_context(self, whatsapp_id: str) -> ConversationState:
        """Clear conversation context"""
        return self.update_conversation(whatsapp_id, context={})

    def end_conversation(self, whatsapp_id: str) -> ConversationState:
        """End active conversation"""
        conv = self.get_or_create_conversation(whatsapp_id)
        conv.status = ConversationStatus.ENDED
        conv.ended_at = datetime.utcnow()
        self._save_conversation(conv)

        # Remove from active conversations
        if whatsapp_id in self._conversations:
            del self._conversations[whatsapp_id]

        logger.info(f"Ended conversation for {whatsapp_id}")
        return conv

    # Onboarding

    def is_new_user(self, whatsapp_id: str) -> bool:
        """Check if user needs onboarding"""
        user = self.get_user(whatsapp_id)
        if not user:
            return True

        # New if no messages sent yet
        return user.message_count == 0

    def should_show_onboarding(self, whatsapp_id: str) -> bool:
        """Check if onboarding should be shown"""
        return self.is_new_user(whatsapp_id)

    # Storage

    def _save_user(self, user: WhatsAppUser):
        """Save user to disk"""
        user_file = self.storage_dir / f"user_{user.whatsapp_id}.json"
        with open(user_file, "w") as f:
            json.dump(user.to_dict(), f, indent=2)

    def _save_conversation(self, conv: ConversationState):
        """Save conversation to disk"""
        conv_file = self.storage_dir / f"conv_{conv.whatsapp_id}.json"
        with open(conv_file, "w") as f:
            json.dump(conv.to_dict(), f, indent=2)

    def _load_all(self):
        """Load all users and conversations from disk"""
        # Load users
        for user_file in self.storage_dir.glob("user_*.json"):
            try:
                with open(user_file) as f:
                    data = json.load(f)
                    user = WhatsAppUser.from_dict(data)
                    self._users[user.whatsapp_id] = user
            except Exception as e:
                logger.error(f"Failed to load user from {user_file}: {e}")

        # Load conversations (only active ones)
        for conv_file in self.storage_dir.glob("conv_*.json"):
            try:
                with open(conv_file) as f:
                    data = json.load(f)
                    conv = ConversationState.from_dict(data)

                    # Only load active conversations
                    if conv.is_active():
                        # Check if timed out
                        if conv.should_timeout(self.session_timeout_minutes):
                            conv.status = ConversationStatus.TIMEOUT
                            conv.ended_at = datetime.utcnow()
                            self._save_conversation(conv)
                        else:
                            self._conversations[conv.whatsapp_id] = conv

            except Exception as e:
                logger.error(f"Failed to load conversation from {conv_file}: {e}")

        logger.info(f"Loaded {len(self._users)} users and {len(self._conversations)} conversations")

    def get_stats(self) -> dict:
        """Get conversation statistics"""
        active_count = sum(1 for c in self._conversations.values() if c.is_active())

        return {
            "total_users": len(self._users),
            "linked_users": sum(1 for u in self._users.values() if u.is_linked),
            "active_conversations": active_count,
            "total_messages": sum(u.message_count for u in self._users.values()),
            "total_queries": sum(u.query_count for u in self._users.values()),
        }
