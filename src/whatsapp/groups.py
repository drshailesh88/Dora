"""
WhatsApp Group Features

Handle clinic/team group communications.
"""

import logging
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from .client import WhatsAppClient
from .models import QuickReply

logger = logging.getLogger(__name__)


@dataclass
class WhatsAppGroup:
    """WhatsApp group"""
    id: str
    name: str
    description: Optional[str] = None

    # Members
    members: List[str] = field(default_factory=list)  # WhatsApp IDs
    admins: List[str] = field(default_factory=list)

    # Settings
    allow_queries: bool = True
    allow_broadcasts: bool = True
    require_approval: bool = True

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Stats
    message_count: int = 0
    query_count: int = 0


class GroupManager:
    """Manage WhatsApp groups for clinics/teams"""

    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
    ):
        """
        Initialize group manager.

        Args:
            whatsapp_client: WhatsApp client
        """
        self.whatsapp_client = whatsapp_client
        self._groups: dict[str, WhatsAppGroup] = {}

    def create_group(
        self,
        group_id: str,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> WhatsAppGroup:
        """
        Create a new group.

        Note: WhatsApp Cloud API doesn't support creating groups via API.
        This is for internal tracking only.

        Args:
            group_id: WhatsApp group ID
            name: Group name
            description: Group description
            created_by: Creator's WhatsApp ID

        Returns:
            WhatsAppGroup
        """
        group = WhatsAppGroup(
            id=group_id,
            name=name,
            description=description,
            created_by=created_by,
        )

        self._groups[group_id] = group
        logger.info(f"Registered group: {name} ({group_id})")

        return group

    def get_group(self, group_id: str) -> Optional[WhatsAppGroup]:
        """Get group by ID"""
        return self._groups.get(group_id)

    def add_member(
        self,
        group_id: str,
        member_id: str,
        is_admin: bool = False,
    ) -> bool:
        """
        Add member to group.

        Args:
            group_id: Group ID
            member_id: Member's WhatsApp ID
            is_admin: Whether member is admin

        Returns:
            True if successful
        """
        group = self.get_group(group_id)
        if not group:
            return False

        if member_id not in group.members:
            group.members.append(member_id)

        if is_admin and member_id not in group.admins:
            group.admins.append(member_id)

        logger.info(f"Added member {member_id} to group {group_id}")
        return True

    def remove_member(
        self,
        group_id: str,
        member_id: str,
    ) -> bool:
        """Remove member from group"""
        group = self.get_group(group_id)
        if not group:
            return False

        if member_id in group.members:
            group.members.remove(member_id)

        if member_id in group.admins:
            group.admins.remove(member_id)

        logger.info(f"Removed member {member_id} from group {group_id}")
        return True

    def is_member(self, group_id: str, member_id: str) -> bool:
        """Check if user is group member"""
        group = self.get_group(group_id)
        if not group:
            return False

        return member_id in group.members

    def is_admin(self, group_id: str, member_id: str) -> bool:
        """Check if user is group admin"""
        group = self.get_group(group_id)
        if not group:
            return False

        return member_id in group.admins

    async def broadcast_to_group(
        self,
        group_id: str,
        message: str,
        sender_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast message to all group members.

        Note: WhatsApp Cloud API doesn't support group messages.
        This sends individual messages to all members.

        Args:
            group_id: Group ID
            message: Message text
            sender_id: Sender's WhatsApp ID (must be admin)

        Returns:
            Number of messages sent
        """
        group = self.get_group(group_id)
        if not group:
            logger.error(f"Group {group_id} not found")
            return 0

        # Check permissions
        if not group.allow_broadcasts:
            logger.warning(f"Broadcasts not allowed in group {group_id}")
            return 0

        if sender_id and not self.is_admin(group_id, sender_id):
            logger.warning(f"User {sender_id} is not admin of group {group_id}")
            return 0

        # Send to all members
        sent_count = 0
        for member_id in group.members:
            if member_id == sender_id:
                continue  # Don't send to sender

            try:
                await self.whatsapp_client.send_text(
                    to=member_id,
                    text=f"📢 *Group Broadcast: {group.name}*\n\n{message}",
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {member_id}: {e}")

        logger.info(f"Broadcast sent to {sent_count} members of {group_id}")
        return sent_count

    async def send_query_to_team(
        self,
        group_id: str,
        query: str,
        answer: str,
        sender_id: str,
    ) -> int:
        """
        Share query and answer with team.

        Args:
            group_id: Group ID
            query: Original query
            answer: Answer text
            sender_id: Doctor who made the query

        Returns:
            Number of team members notified
        """
        group = self.get_group(group_id)
        if not group:
            return 0

        if not group.allow_queries:
            return 0

        # Format message
        message = f"""💡 *Team Query*

Query: {query}

Answer: {answer}

_Shared by team member_"""

        # Send to all members except sender
        sent_count = 0
        for member_id in group.members:
            if member_id == sender_id:
                continue

            try:
                await self.whatsapp_client.send_text(
                    to=member_id,
                    text=message,
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send query to {member_id}: {e}")

        group.query_count += 1
        logger.info(f"Shared query with {sent_count} team members")

        return sent_count

    async def send_daily_summary(
        self,
        group_id: str,
        summary: dict,
    ) -> int:
        """
        Send daily summary to group.

        Args:
            group_id: Group ID
            summary: Summary data

        Returns:
            Number of members notified
        """
        group = self.get_group(group_id)
        if not group:
            return 0

        # Format summary
        message = f"""📊 *Daily Summary - {group.name}*

• Queries: {summary.get('queries', 0)}
• Active users: {summary.get('active_users', 0)}
• Messages: {summary.get('messages', 0)}

{summary.get('notes', '')}"""

        # Send to admins
        sent_count = 0
        for admin_id in group.admins:
            try:
                await self.whatsapp_client.send_text(
                    to=admin_id,
                    text=message,
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send summary to {admin_id}: {e}")

        logger.info(f"Sent daily summary to {sent_count} admins")
        return sent_count

    def get_group_stats(self, group_id: str) -> Optional[dict]:
        """Get group statistics"""
        group = self.get_group(group_id)
        if not group:
            return None

        return {
            "group_id": group.id,
            "name": group.name,
            "member_count": len(group.members),
            "admin_count": len(group.admins),
            "message_count": group.message_count,
            "query_count": group.query_count,
            "created_at": group.created_at.isoformat(),
        }
