"""
Secure Messaging

HIPAA-compliant messaging for consultations with encryption,
file attachments, and read receipts.
"""

from datetime import datetime
from typing import Optional

from src.peers.models import (
    ConsultMessage,
    MessageThread,
    MessageType,
)


class SecureMessaging:
    """Manages secure messaging for consultations."""

    def __init__(self):
        """Initialize messaging system."""
        # In production, use database with encryption
        self.messages: dict[str, ConsultMessage] = {}
        self.threads: dict[str, MessageThread] = {}

    def create_thread(
        self,
        consult_request_id: str,
        participants: list[str],
    ) -> MessageThread:
        """
        Create a message thread for consultation.

        Args:
            consult_request_id: Consultation request ID
            participants: List of user IDs in thread

        Returns:
            MessageThread object
        """
        thread = MessageThread(
            consult_request_id=consult_request_id,
            participants=participants,
            unread_count={p: 0 for p in participants},
        )

        self.threads[thread.id] = thread
        return thread

    def get_thread(
        self,
        consult_request_id: str,
    ) -> Optional[MessageThread]:
        """
        Get thread for consultation request.

        Args:
            consult_request_id: Consultation request ID

        Returns:
            MessageThread or None
        """
        for thread in self.threads.values():
            if thread.consult_request_id == consult_request_id:
                return thread
        return None

    def get_or_create_thread(
        self,
        consult_request_id: str,
        participants: list[str],
    ) -> MessageThread:
        """
        Get existing thread or create new one.

        Args:
            consult_request_id: Consultation request ID
            participants: List of user IDs

        Returns:
            MessageThread object
        """
        thread = self.get_thread(consult_request_id)
        if not thread:
            thread = self.create_thread(consult_request_id, participants)
        return thread

    def send_message(
        self,
        consult_request_id: str,
        sender_id: str,
        receiver_id: str,
        message_text: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT,
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> ConsultMessage:
        """
        Send a message in consultation thread.

        Args:
            consult_request_id: Consultation request ID
            sender_id: Sender user ID
            receiver_id: Receiver user ID
            message_text: Message text
            message_type: Type of message
            attachment_url: URL to attachment (encrypted)
            attachment_name: Attachment filename
            duration_seconds: Duration for voice/video

        Returns:
            ConsultMessage object
        """
        # Get or create thread
        thread = self.get_or_create_thread(
            consult_request_id=consult_request_id,
            participants=[sender_id, receiver_id],
        )

        # Create message
        message = ConsultMessage(
            consult_request_id=consult_request_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            message_text=message_text,
            attachment_url=attachment_url,
            attachment_name=attachment_name,
            duration_seconds=duration_seconds,
            thread_id=thread.id,
        )

        self.messages[message.id] = message

        # Update thread
        thread.last_message_at = datetime.utcnow()
        thread.last_message_preview = self._create_message_preview(message)

        # Increment unread count for receiver
        if receiver_id in thread.unread_count:
            thread.unread_count[receiver_id] += 1

        return message

    def get_messages(
        self,
        consult_request_id: str,
        limit: int = 100,
    ) -> list[ConsultMessage]:
        """
        Get messages for consultation.

        Args:
            consult_request_id: Consultation request ID
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        messages = [
            m for m in self.messages.values()
            if m.consult_request_id == consult_request_id
        ]

        # Sort by creation time
        messages.sort(key=lambda m: m.created_at)

        return messages[-limit:]  # Return most recent

    def mark_as_read(
        self,
        message_id: str,
        user_id: str,
    ) -> bool:
        """
        Mark message as read.

        Args:
            message_id: Message ID
            user_id: User who read the message

        Returns:
            Success status
        """
        message = self.messages.get(message_id)
        if not message or message.receiver_id != user_id:
            return False

        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()

            # Update thread unread count
            if message.thread_id:
                thread = self.threads.get(message.thread_id)
                if thread and user_id in thread.unread_count:
                    thread.unread_count[user_id] = max(
                        0, thread.unread_count[user_id] - 1
                    )

        return True

    def mark_all_read(
        self,
        consult_request_id: str,
        user_id: str,
    ) -> int:
        """
        Mark all messages in consultation as read.

        Args:
            consult_request_id: Consultation request ID
            user_id: User who read messages

        Returns:
            Number of messages marked as read
        """
        count = 0
        messages = [
            m for m in self.messages.values()
            if m.consult_request_id == consult_request_id
            and m.receiver_id == user_id
            and not m.is_read
        ]

        for message in messages:
            message.is_read = True
            message.read_at = datetime.utcnow()
            count += 1

        # Reset thread unread count
        thread = self.get_thread(consult_request_id)
        if thread and user_id in thread.unread_count:
            thread.unread_count[user_id] = 0

        return count

    def get_unread_count(
        self,
        consult_request_id: str,
        user_id: str,
    ) -> int:
        """
        Get unread message count for user.

        Args:
            consult_request_id: Consultation request ID
            user_id: User ID

        Returns:
            Unread message count
        """
        thread = self.get_thread(consult_request_id)
        if thread and user_id in thread.unread_count:
            return thread.unread_count[user_id]
        return 0

    def get_user_threads(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> list[MessageThread]:
        """
        Get all threads for a user.

        Args:
            user_id: User ID
            active_only: Only active threads

        Returns:
            List of threads
        """
        threads = [
            t for t in self.threads.values()
            if user_id in t.participants
        ]

        if active_only:
            threads = [t for t in threads if t.is_active]

        # Sort by last message time (most recent first)
        threads.sort(key=lambda t: t.last_message_at, reverse=True)

        return threads

    def archive_thread(
        self,
        thread_id: str,
    ) -> bool:
        """
        Archive (deactivate) a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Success status
        """
        thread = self.threads.get(thread_id)
        if not thread:
            return False

        thread.is_active = False
        return True

    def delete_message(
        self,
        message_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete a message (soft delete).

        Args:
            message_id: Message ID
            user_id: User ID (must be sender)

        Returns:
            Success status
        """
        message = self.messages.get(message_id)
        if not message or message.sender_id != user_id:
            return False

        # In production, implement soft delete
        # For now, just remove from store
        del self.messages[message_id]
        return True

    def search_messages(
        self,
        consult_request_id: str,
        query: str,
    ) -> list[ConsultMessage]:
        """
        Search messages in consultation.

        Args:
            consult_request_id: Consultation request ID
            query: Search query

        Returns:
            List of matching messages
        """
        messages = self.get_messages(consult_request_id, limit=1000)

        query_lower = query.lower()
        matching = [
            m for m in messages
            if m.message_type == MessageType.TEXT
            and m.message_text
            and query_lower in m.message_text.lower()
        ]

        return matching

    def _create_message_preview(self, message: ConsultMessage) -> str:
        """
        Create preview text for message.

        Args:
            message: Message object

        Returns:
            Preview text
        """
        if message.message_type == MessageType.TEXT and message.message_text:
            return message.message_text[:100]
        elif message.message_type == MessageType.IMAGE:
            return "Sent an image"
        elif message.message_type == MessageType.PDF:
            return f"Sent a document: {message.attachment_name or 'file.pdf'}"
        elif message.message_type == MessageType.VOICE:
            duration = message.duration_seconds or 0
            return f"Sent a voice message ({duration}s)"
        elif message.message_type == MessageType.VIDEO:
            return "Sent a video"
        else:
            return "Sent a message"

    def encrypt_attachment(self, file_path: str) -> str:
        """
        Encrypt and upload attachment.

        Args:
            file_path: Path to file

        Returns:
            Encrypted file URL
        """
        # In production, implement encryption and upload to secure storage
        # For now, return placeholder
        return f"encrypted://{file_path}"

    def decrypt_attachment(self, encrypted_url: str) -> str:
        """
        Decrypt attachment URL.

        Args:
            encrypted_url: Encrypted URL

        Returns:
            Decrypted file path/URL
        """
        # In production, implement decryption
        # For now, return placeholder
        return encrypted_url.replace("encrypted://", "")

    def get_messaging_stats(
        self,
        consult_request_id: str,
    ) -> dict[str, int]:
        """
        Get messaging statistics for consultation.

        Args:
            consult_request_id: Consultation request ID

        Returns:
            Statistics dictionary
        """
        messages = self.get_messages(consult_request_id, limit=10000)

        stats = {
            "total_messages": len(messages),
            "text_messages": len([m for m in messages if m.message_type == MessageType.TEXT]),
            "attachments": len([m for m in messages if m.message_type != MessageType.TEXT]),
            "unread_messages": len([m for m in messages if not m.is_read]),
        }

        return stats
