"""
Protocol Versioning

Version control system for protocols with approval workflows.
"""

from typing import Optional, List, Tuple
from datetime import datetime
import difflib

from .models import Protocol, ProtocolVersion, ProtocolStatus
from .storage import ProtocolStorage, get_protocol_storage


class VersionManager:
    """
    Protocol version control manager.

    Handles version creation, comparison, approval workflows, and rollback.
    """

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    def create_version(
        self,
        protocol_id: str,
        user_id: str,
        change_summary: str,
        changed_sections: Optional[List[str]] = None,
    ) -> Optional[ProtocolVersion]:
        """Create a new version of a protocol."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        # Get current version number and increment
        current_version = protocol.version_number
        major, minor = map(int, current_version.split('.'))

        # Major version for published changes, minor for drafts
        if protocol.status == ProtocolStatus.PUBLISHED:
            new_version = f"{major + 1}.0"
        else:
            new_version = f"{major}.{minor + 1}"

        # Create version snapshot
        version = ProtocolVersion(
            protocol_id=protocol_id,
            version_number=new_version,
            title=protocol.title,
            content=protocol.content,
            structured_data=protocol.structured_data,
            change_summary=change_summary,
            changed_sections=changed_sections or [],
            created_by=user_id,
            status=protocol.status,
        )

        self.storage.create_version(version)

        # Update protocol's current version
        protocol.current_version_id = version.id
        protocol.version_number = new_version
        self.storage.update_protocol(protocol)

        return version

    def get_version_history(self, protocol_id: str) -> List[ProtocolVersion]:
        """Get all versions of a protocol."""
        return self.storage.get_protocol_versions(protocol_id)

    def get_version(self, version_id: str) -> Optional[ProtocolVersion]:
        """Get a specific version by ID."""
        # In real implementation, would have dedicated get_version method
        # For now, iterate through versions
        return None

    def compare_versions(
        self,
        version1_id: str,
        version2_id: str,
    ) -> Optional[dict]:
        """
        Compare two versions and return differences.

        Returns dict with added, removed, and modified content.
        """
        # In real implementation, would load both versions
        # For now, return placeholder
        return {
            "version1": version1_id,
            "version2": version2_id,
            "diff": [],
            "summary": "",
        }

    def generate_diff(
        self,
        old_content: str,
        new_content: str,
    ) -> List[str]:
        """Generate a unified diff between two content strings."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='old',
            tofile='new',
            lineterm='',
        )

        return list(diff)

    def approve_version(
        self,
        version_id: str,
        user_id: str,
    ) -> Optional[ProtocolVersion]:
        """Approve a version for publication."""
        versions = []  # Would load from storage
        version = None

        for v in versions:
            if v.id == version_id:
                version = v
                break

        if not version:
            return None

        version.approved_by = user_id
        version.approved_at = datetime.utcnow()
        version.status = ProtocolStatus.PUBLISHED

        # Would update in storage
        return version

    def rollback_to_version(
        self,
        protocol_id: str,
        version_id: str,
        user_id: str,
    ) -> Optional[Protocol]:
        """Rollback protocol to a previous version."""
        protocol = self.storage.get_protocol(protocol_id)
        if not protocol:
            return None

        versions = self.storage.get_protocol_versions(protocol_id)
        target_version = None

        for v in versions:
            if v.id == version_id:
                target_version = v
                break

        if not target_version:
            return None

        # Create a new version from the rollback
        rollback_version = ProtocolVersion(
            protocol_id=protocol_id,
            version_number=self._increment_version(protocol.version_number),
            title=target_version.title,
            content=target_version.content,
            structured_data=target_version.structured_data,
            change_summary=f"Rolled back to version {target_version.version_number}",
            changed_sections=[],
            created_by=user_id,
            status=ProtocolStatus.DRAFT,
        )

        self.storage.create_version(rollback_version)

        # Update protocol
        protocol.content = target_version.content
        protocol.structured_data = target_version.structured_data
        protocol.version_number = rollback_version.version_number
        protocol.current_version_id = rollback_version.id
        protocol.status = ProtocolStatus.DRAFT

        self.storage.update_protocol(protocol)

        return protocol

    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        major, minor = map(int, version.split('.'))
        return f"{major}.{minor + 1}"

    def get_version_diff_summary(
        self,
        old_version: ProtocolVersion,
        new_version: ProtocolVersion,
    ) -> dict:
        """
        Get a summary of changes between versions.

        Returns statistics about additions, deletions, and modifications.
        """
        diff = self.generate_diff(old_version.content, new_version.content)

        additions = sum(1 for line in diff if line.startswith('+'))
        deletions = sum(1 for line in diff if line.startswith('-'))

        return {
            "additions": additions,
            "deletions": deletions,
            "total_changes": additions + deletions,
            "change_summary": new_version.change_summary,
            "changed_sections": new_version.changed_sections,
        }

    def get_change_log(
        self,
        protocol_id: str,
        limit: int = 10,
    ) -> List[dict]:
        """Get a change log for a protocol."""
        versions = self.storage.get_protocol_versions(protocol_id)

        changelog = []
        for i, version in enumerate(versions[:limit]):
            entry = {
                "version": version.version_number,
                "date": version.created_at,
                "author": version.created_by,
                "summary": version.change_summary,
                "status": version.status.value,
            }

            # Calculate diff if not the first version
            if i < len(versions) - 1:
                prev_version = versions[i + 1]
                diff_summary = self.get_version_diff_summary(prev_version, version)
                entry["changes"] = diff_summary

            changelog.append(entry)

        return changelog


# Default instance
_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """Get default version manager."""
    global _manager
    if _manager is None:
        _manager = VersionManager()
    return _manager
