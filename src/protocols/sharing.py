"""
Protocol Sharing

Team collaboration and access control for protocols.
"""

from typing import Optional, List
from datetime import datetime, timedelta

from .models import (
    Protocol,
    ProtocolShare,
    TeamAnnotation,
    AccessLevel,
)
from .storage import ProtocolStorage, get_protocol_storage


class SharingManager:
    """
    Protocol sharing and collaboration manager.

    Handles access control, team sharing, and collaborative features.
    """

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    # Access Control
    def share_protocol(
        self,
        protocol_id: str,
        shared_by: str,
        access_level: AccessLevel = AccessLevel.VIEW,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        expires_days: Optional[int] = None,
    ) -> ProtocolShare:
        """Share a protocol with a user, team, or organization."""
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        share = ProtocolShare(
            protocol_id=protocol_id,
            user_id=user_id,
            team_id=team_id,
            organization_id=organization_id,
            access_level=access_level,
            shared_by=shared_by,
            expires_at=expires_at,
        )

        self.storage.create_share(share)
        return share

    def revoke_share(self, share_id: str) -> bool:
        """Revoke a protocol share."""
        # In real implementation, would have revoke method
        return True

    def get_protocol_shares(self, protocol_id: str) -> List[ProtocolShare]:
        """Get all shares for a protocol."""
        return self.storage.get_shares(protocol_id)

    def check_access(
        self,
        protocol_id: str,
        user_id: str,
        required_level: AccessLevel = AccessLevel.VIEW,
    ) -> bool:
        """
        Check if a user has required access level to a protocol.

        Returns True if user has required access level or higher.
        """
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return False

        # Owner has full access
        if protocol.created_by == user_id:
            return True

        # Clinic-wide protocols are accessible to org members
        if protocol.is_clinic_wide and protocol.organization_id:
            # Would check if user belongs to organization
            pass

        # Check explicit shares
        shares = self.storage.get_shares(protocol_id)
        for share in shares:
            # Check if share has expired
            if share.expires_at and datetime.utcnow() > share.expires_at:
                continue

            # Check if user matches
            if share.user_id == user_id:
                # Check access level hierarchy
                return self._has_sufficient_access(share.access_level, required_level)

        return False

    def _has_sufficient_access(
        self,
        user_level: AccessLevel,
        required_level: AccessLevel,
    ) -> bool:
        """Check if user's access level meets requirement."""
        hierarchy = {
            AccessLevel.VIEW: 1,
            AccessLevel.COMMENT: 2,
            AccessLevel.EDIT: 3,
            AccessLevel.APPROVE: 4,
            AccessLevel.OWNER: 5,
        }

        return hierarchy.get(user_level, 0) >= hierarchy.get(required_level, 0)

    # Collaboration
    def add_annotation(
        self,
        protocol_id: str,
        user_id: str,
        user_name: str,
        content: str,
        section: Optional[str] = None,
        line_number: Optional[int] = None,
        parent_id: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> TeamAnnotation:
        """Add a comment/annotation to a protocol."""
        annotation = TeamAnnotation(
            protocol_id=protocol_id,
            version_id=version_id,
            content=content,
            section=section,
            line_number=line_number,
            user_id=user_id,
            user_name=user_name,
            parent_id=parent_id,
        )

        self.storage.create_annotation(annotation)
        return annotation

    def resolve_annotation(
        self,
        annotation_id: str,
        user_id: str,
    ) -> Optional[TeamAnnotation]:
        """Mark an annotation as resolved."""
        # In real implementation, would update annotation
        annotation = TeamAnnotation(id=annotation_id)
        annotation.is_resolved = True
        annotation.resolved_by = user_id
        annotation.resolved_at = datetime.utcnow()
        return annotation

    def get_protocol_annotations(
        self,
        protocol_id: str,
        include_resolved: bool = False,
    ) -> List[TeamAnnotation]:
        """Get all annotations for a protocol."""
        annotations = self.storage.get_annotations(protocol_id)

        if not include_resolved:
            annotations = [a for a in annotations if not a.is_resolved]

        return annotations

    def get_annotation_threads(
        self,
        protocol_id: str,
    ) -> List[List[TeamAnnotation]]:
        """
        Get annotations organized into threads.

        Returns list of annotation threads (parent + replies).
        """
        annotations = self.storage.get_annotations(protocol_id)

        # Build annotation map
        annotation_map = {a.id: a for a in annotations}

        # Find root annotations (no parent)
        roots = [a for a in annotations if not a.parent_id]

        # Build threads
        threads = []
        for root in roots:
            thread = [root]

            # Find all replies
            replies = [
                a for a in annotations
                if a.parent_id == root.id
            ]
            thread.extend(sorted(replies, key=lambda x: x.created_at))

            threads.append(thread)

        return threads

    # Team Management
    def share_with_team(
        self,
        protocol_id: str,
        team_id: str,
        shared_by: str,
        access_level: AccessLevel = AccessLevel.VIEW,
    ) -> ProtocolShare:
        """Share a protocol with an entire team."""
        return self.share_protocol(
            protocol_id=protocol_id,
            shared_by=shared_by,
            access_level=access_level,
            team_id=team_id,
        )

    def make_clinic_wide(
        self,
        protocol_id: str,
        organization_id: str,
    ) -> Optional[Protocol]:
        """Make a protocol available to entire clinic/organization."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        protocol.is_clinic_wide = True
        protocol.organization_id = organization_id
        self.storage.update_protocol(protocol)

        return protocol

    def get_team_protocols(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> List[Protocol]:
        """Get all protocols shared with user or their organization."""
        # Get protocols where user has explicit share
        # Plus clinic-wide protocols in their org
        protocols = self.storage.list_protocols(
            organization_id=organization_id,
            limit=1000,
        )

        accessible = []
        for protocol in protocols:
            if self.check_access(protocol.id, user_id):
                accessible.append(protocol)

        return accessible

    # Notifications
    def notify_collaborators(
        self,
        protocol_id: str,
        message: str,
        exclude_user_id: Optional[str] = None,
    ) -> List[str]:
        """
        Notify all collaborators about protocol update.

        Returns list of notified user IDs.
        """
        shares = self.storage.get_shares(protocol_id)

        notified = []
        for share in shares:
            if share.user_id and share.user_id != exclude_user_id:
                # In real implementation, would send notification
                # via notification service
                notified.append(share.user_id)

        return notified


# Default instance
_manager: Optional[SharingManager] = None


def get_sharing_manager() -> SharingManager:
    """Get default sharing manager."""
    global _manager
    if _manager is None:
        _manager = SharingManager()
    return _manager
