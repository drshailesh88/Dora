"""
Message Storage

Persistent storage for WhatsApp messages with status tracking and history.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import WhatsAppMessage, WhatsAppResponse, MessageStatus

logger = logging.getLogger(__name__)


class MessageStore:
    """
    Persistent storage for WhatsApp messages.

    Stores sent and received messages with status tracking for:
    - Message history retrieval
    - Status updates (delivered, read)
    - Compliance and audit logging
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize message store.

        Args:
            storage_dir: Directory to store message data
        """
        self.storage_dir = Path(storage_dir or "./data/whatsapp/messages")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Message indices for fast lookup
        self._message_index_file = self.storage_dir / "message_index.json"
        self._message_index: dict[str, str] = {}  # message_id -> file_path

        # Load index
        self._load_index()

    def _load_index(self):
        """Load message index from disk"""
        if self._message_index_file.exists():
            try:
                with open(self._message_index_file) as f:
                    self._message_index = json.load(f)
                logger.info(f"Loaded message index with {len(self._message_index)} entries")
            except Exception as e:
                logger.error(f"Failed to load message index: {e}")
                self._message_index = {}

    def _save_index(self):
        """Save message index to disk"""
        try:
            with open(self._message_index_file, "w") as f:
                json.dump(self._message_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save message index: {e}")

    def _get_message_dir(self, whatsapp_id: str) -> Path:
        """Get directory for a user's messages"""
        # Use hash of whatsapp_id to avoid filesystem issues
        import hashlib
        user_hash = hashlib.md5(whatsapp_id.encode()).hexdigest()[:8]
        return self.storage_dir / user_hash

    def save_incoming_message(self, message: WhatsAppMessage) -> bool:
        """
        Save incoming WhatsApp message.

        Args:
            message: WhatsApp message to save

        Returns:
            True if saved successfully
        """
        try:
            user_dir = self._get_message_dir(message.from_number)
            user_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = message.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"in_{timestamp}_{message.message_id}.json"
            file_path = user_dir / filename

            # Save message
            message_data = message.to_dict()
            message_data["direction"] = "incoming"
            message_data["saved_at"] = datetime.utcnow().isoformat()

            with open(file_path, "w") as f:
                json.dump(message_data, f, indent=2)

            # Update index
            self._message_index[message.message_id] = str(file_path)
            self._save_index()

            logger.info(f"Saved incoming message {message.message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save incoming message: {e}")
            return False

    def save_outgoing_message(self, response: WhatsAppResponse) -> bool:
        """
        Save outgoing WhatsApp message.

        Args:
            response: WhatsApp response to save

        Returns:
            True if saved successfully
        """
        try:
            user_dir = self._get_message_dir(response.to_number)
            user_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = response.sent_at.strftime("%Y%m%d_%H%M%S")
            message_id = response.message_id or response.id
            filename = f"out_{timestamp}_{message_id}.json"
            file_path = user_dir / filename

            # Save message
            message_data = response.to_dict()
            message_data["direction"] = "outgoing"
            message_data["saved_at"] = datetime.utcnow().isoformat()

            with open(file_path, "w") as f:
                json.dump(message_data, f, indent=2)

            # Update index
            if response.message_id:
                self._message_index[response.message_id] = str(file_path)
                self._save_index()

            logger.info(f"Saved outgoing message {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save outgoing message: {e}")
            return False

    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Update message delivery status.

        Args:
            message_id: WhatsApp message ID
            status: New status
            timestamp: Status timestamp

        Returns:
            True if updated successfully
        """
        try:
            # Find message file
            file_path = self._message_index.get(message_id)
            if not file_path or not Path(file_path).exists():
                logger.warning(f"Message {message_id} not found for status update")
                return False

            # Load message
            with open(file_path) as f:
                message_data = json.load(f)

            # Update status
            message_data["status"] = status.value
            message_data["status_updated_at"] = (
                timestamp or datetime.utcnow()
            ).isoformat()

            # Update specific timestamp fields
            if status == MessageStatus.DELIVERED:
                message_data["delivered_at"] = (
                    timestamp or datetime.utcnow()
                ).isoformat()
            elif status == MessageStatus.READ:
                message_data["read_at"] = (timestamp or datetime.utcnow()).isoformat()

            # Save updated message
            with open(file_path, "w") as f:
                json.dump(message_data, f, indent=2)

            logger.info(f"Updated message {message_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            return False

    def get_message_history(
        self,
        whatsapp_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        Get message history for a WhatsApp user.

        Args:
            whatsapp_id: WhatsApp phone number
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of message dictionaries
        """
        try:
            user_dir = self._get_message_dir(whatsapp_id)
            if not user_dir.exists():
                return []

            # Get all message files sorted by modification time (newest first)
            message_files = sorted(
                user_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Apply pagination
            paginated_files = message_files[offset : offset + limit]

            # Load messages
            messages = []
            for file_path in paginated_files:
                try:
                    with open(file_path) as f:
                        message_data = json.load(f)
                        messages.append(message_data)
                except Exception as e:
                    logger.error(f"Failed to load message from {file_path}: {e}")

            return messages

        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []

    def get_message_count(self, whatsapp_id: str) -> int:
        """
        Get total message count for a user.

        Args:
            whatsapp_id: WhatsApp phone number

        Returns:
            Total number of messages
        """
        try:
            user_dir = self._get_message_dir(whatsapp_id)
            if not user_dir.exists():
                return 0

            return len(list(user_dir.glob("*.json")))

        except Exception as e:
            logger.error(f"Failed to get message count: {e}")
            return 0

    def search_messages(
        self,
        whatsapp_id: str,
        query: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Search messages by text content.

        Args:
            whatsapp_id: WhatsApp phone number
            query: Search query
            limit: Maximum results

        Returns:
            List of matching messages
        """
        try:
            user_dir = self._get_message_dir(whatsapp_id)
            if not user_dir.exists():
                return []

            query_lower = query.lower()
            matching_messages = []

            # Search through all messages
            for file_path in user_dir.glob("*.json"):
                try:
                    with open(file_path) as f:
                        message_data = json.load(f)

                        # Search in text content
                        text = message_data.get("text", "")
                        if text and query_lower in text.lower():
                            matching_messages.append(message_data)

                            if len(matching_messages) >= limit:
                                break

                except Exception as e:
                    logger.error(f"Failed to search message {file_path}: {e}")

            # Sort by timestamp (newest first)
            matching_messages.sort(
                key=lambda m: m.get("timestamp", ""),
                reverse=True,
            )

            return matching_messages[:limit]

        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []

    def cleanup_old_messages(self, days: int = 90):
        """
        Clean up messages older than N days.

        Args:
            days: Delete messages older than this many days
        """
        import time

        cutoff = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        try:
            for user_dir in self.storage_dir.iterdir():
                if not user_dir.is_dir():
                    continue

                for file_path in user_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff:
                        try:
                            # Remove from index
                            for msg_id, path in list(self._message_index.items()):
                                if path == str(file_path):
                                    del self._message_index[msg_id]

                            # Delete file
                            file_path.unlink()
                            deleted_count += 1

                        except Exception as e:
                            logger.error(f"Error deleting {file_path}: {e}")

            # Save updated index
            self._save_index()

            logger.info(f"Cleaned up {deleted_count} old messages")

        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")

    def get_stats(self) -> dict:
        """Get message storage statistics"""
        total_messages = len(self._message_index)
        total_users = len(list(self.storage_dir.glob("*")))

        return {
            "total_messages": total_messages,
            "total_users": total_users,
            "storage_dir": str(self.storage_dir),
        }
