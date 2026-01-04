"""
Protocol Service

Unified service layer for all protocol operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    Protocol,
    ProtocolVersion,
    QuickReference,
    Checklist,
    ChecklistExecution,
    Flowchart,
    TeamAnnotation,
    ProtocolShare,
    ProtocolCompliance,
    ComplianceReport,
    ProtocolCategory,
    ProtocolStatus,
    AccessLevel,
    ChecklistStatus,
    ChecklistItem,
)
from .storage import ProtocolStorage, get_protocol_storage
from .library import ProtocolLibrary, get_protocol_library
from .templates import create_from_template, list_templates
from .references import QuickReferenceManager, get_reference_manager
from .checklists import ChecklistManager, get_checklist_manager
from .flowcharts import FlowchartManager, get_flowchart_manager
from .versioning import VersionManager, get_version_manager
from .sharing import SharingManager, get_sharing_manager
from .compliance import ComplianceTracker, get_compliance_tracker


class ProtocolService:
    """
    Unified protocol service.

    Central service for all protocol-related operations.
    Orchestrates library, versioning, sharing, compliance, and collaboration features.
    """

    def __init__(
        self,
        storage: Optional[ProtocolStorage] = None,
        library: Optional[ProtocolLibrary] = None,
        references: Optional[QuickReferenceManager] = None,
        checklists: Optional[ChecklistManager] = None,
        flowcharts: Optional[FlowchartManager] = None,
        versioning: Optional[VersionManager] = None,
        sharing: Optional[SharingManager] = None,
        compliance: Optional[ComplianceTracker] = None,
    ):
        self.storage = storage or get_protocol_storage()
        self.library = library or get_protocol_library()
        self.references = references or get_reference_manager()
        self.checklists = checklists or get_checklist_manager()
        self.flowcharts = flowcharts or get_flowchart_manager()
        self.versioning = versioning or get_version_manager()
        self.sharing = sharing or get_sharing_manager()
        self.compliance = compliance or get_compliance_tracker()

    # Protocol CRUD (delegated to library)
    def create_protocol(self, *args, **kwargs) -> Protocol:
        """Create a new protocol."""
        return self.library.create_protocol(*args, **kwargs)

    def get_protocol(self, protocol_id: str, user_id: Optional[str] = None) -> Optional[Protocol]:
        """
        Get a protocol by ID.

        Checks access permissions if user_id provided.
        """
        protocol = self.library.get_protocol(protocol_id)

        if protocol and user_id:
            # Check if user has access
            if not self.sharing.check_access(protocol_id, user_id):
                return None

        return protocol

    def update_protocol(self, *args, **kwargs) -> Optional[Protocol]:
        """Update a protocol."""
        return self.library.update_protocol(*args, **kwargs)

    def delete_protocol(self, protocol_id: str) -> bool:
        """Delete a protocol."""
        return self.library.delete_protocol(protocol_id)

    def search_protocols(self, *args, **kwargs) -> List[Protocol]:
        """Search protocols."""
        return self.library.search_protocols(*args, **kwargs)

    # Template operations
    def create_from_template(self, template_id: str, user_id: str, **kwargs) -> Optional[Protocol]:
        """Create protocol from template."""
        return self.library.create_from_template(template_id, user_id, **kwargs)

    def get_templates(self, category: Optional[ProtocolCategory] = None) -> List[Protocol]:
        """Get available templates."""
        return self.library.get_templates(category)

    # Quick References
    def create_quick_reference(self, *args, **kwargs) -> QuickReference:
        """Create a quick reference card."""
        return self.references.create_reference(*args, **kwargs)

    def get_quick_references(self, **kwargs) -> List[QuickReference]:
        """Get quick references."""
        return self.references.get_references(**kwargs)

    def get_default_references(self) -> List[Dict[str, str]]:
        """Get default pre-built reference cards."""
        return self.references.get_default_references()

    # Checklists
    def create_checklist(self, *args, **kwargs) -> Checklist:
        """Create a checklist."""
        return self.checklists.create_checklist(*args, **kwargs)

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        """Get a checklist."""
        return self.checklists.get_checklist(checklist_id)

    def list_checklists(self, **kwargs) -> List[Checklist]:
        """List checklists."""
        return self.checklists.list_checklists(**kwargs)

    def get_default_checklists(self) -> List[Checklist]:
        """Get pre-built checklist templates."""
        return self.checklists.get_default_checklists()

    def start_checklist_execution(self, *args, **kwargs) -> ChecklistExecution:
        """Start checklist execution."""
        return self.checklists.start_execution(*args, **kwargs)

    def update_checklist_item(self, *args, **kwargs) -> Optional[ChecklistExecution]:
        """Update checklist item status."""
        return self.checklists.update_item_status(*args, **kwargs)

    # Flowcharts
    def create_flowchart(self, *args, **kwargs) -> Flowchart:
        """Create a flowchart."""
        return self.flowcharts.create_flowchart(*args, **kwargs)

    def get_default_flowcharts(self) -> List[dict]:
        """Get pre-built flowcharts."""
        return self.flowcharts.get_default_flowcharts()

    # Versioning
    def create_version(self, *args, **kwargs) -> Optional[ProtocolVersion]:
        """Create a new protocol version."""
        return self.versioning.create_version(*args, **kwargs)

    def get_version_history(self, protocol_id: str) -> List[ProtocolVersion]:
        """Get version history."""
        return self.versioning.get_version_history(protocol_id)

    def compare_versions(self, version1_id: str, version2_id: str) -> Optional[dict]:
        """Compare two versions."""
        return self.versioning.compare_versions(version1_id, version2_id)

    def approve_version(self, version_id: str, user_id: str) -> Optional[ProtocolVersion]:
        """Approve a version."""
        return self.versioning.approve_version(version_id, user_id)

    def rollback_protocol(self, protocol_id: str, version_id: str, user_id: str) -> Optional[Protocol]:
        """Rollback to a previous version."""
        return self.versioning.rollback_to_version(protocol_id, version_id, user_id)

    # Sharing & Collaboration
    def share_protocol(self, *args, **kwargs) -> ProtocolShare:
        """Share a protocol."""
        return self.sharing.share_protocol(*args, **kwargs)

    def get_protocol_shares(self, protocol_id: str) -> List[ProtocolShare]:
        """Get protocol shares."""
        return self.sharing.get_protocol_shares(protocol_id)

    def add_annotation(self, *args, **kwargs) -> TeamAnnotation:
        """Add a comment/annotation."""
        return self.sharing.add_annotation(*args, **kwargs)

    def get_annotations(self, protocol_id: str, **kwargs) -> List[TeamAnnotation]:
        """Get protocol annotations."""
        return self.sharing.get_protocol_annotations(protocol_id, **kwargs)

    def resolve_annotation(self, annotation_id: str, user_id: str) -> Optional[TeamAnnotation]:
        """Resolve an annotation."""
        return self.sharing.resolve_annotation(annotation_id, user_id)

    def make_clinic_wide(self, protocol_id: str, organization_id: str) -> Optional[Protocol]:
        """Make protocol clinic-wide."""
        return self.sharing.make_clinic_wide(protocol_id, organization_id)

    # Compliance & Tracking
    def record_usage(self, *args, **kwargs) -> ProtocolCompliance:
        """Record protocol usage."""
        return self.compliance.record_usage(*args, **kwargs)

    def generate_compliance_report(
        self,
        protocol_id: str,
        **kwargs,
    ) -> Optional[ComplianceReport]:
        """Generate compliance report."""
        return self.compliance.generate_protocol_report(protocol_id, **kwargs)

    def generate_organization_report(
        self,
        organization_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate organization-wide report."""
        return self.compliance.generate_organization_report(organization_id, **kwargs)

    def generate_user_report(
        self,
        user_id: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate user compliance report."""
        return self.compliance.generate_user_report(user_id, **kwargs)

    def identify_improvement_opportunities(
        self,
        organization_id: str,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Identify protocols needing improvement."""
        return self.compliance.identify_improvement_opportunities(organization_id, **kwargs)

    # Lifecycle management
    def publish_protocol(self, protocol_id: str, user_id: str) -> Optional[Protocol]:
        """Publish a protocol."""
        protocol = self.library.publish_protocol(protocol_id, user_id)

        if protocol:
            # Create version snapshot
            self.versioning.create_version(
                protocol_id,
                user_id,
                f"Published version {protocol.version_number}",
            )

        return protocol

    def archive_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Archive a protocol."""
        return self.library.archive_protocol(protocol_id)

    # Statistics & Analytics
    def get_dashboard_stats(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get dashboard statistics."""
        # Library stats
        library_stats = self.library.get_usage_stats(
            organization_id=organization_id,
            user_id=user_id,
        )

        # Recent activity
        protocols = self.library.search_protocols(
            organization_id=organization_id,
            user_id=user_id,
            limit=5,
        )

        recent_protocols = [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category.value,
                "updated_at": p.updated_at,
                "status": p.status.value,
            }
            for p in protocols
        ]

        return {
            "library": library_stats,
            "recent_protocols": recent_protocols,
            "total_checklists": len(self.checklists.list_checklists(organization_id=organization_id)),
            "total_references": len(self.references.get_references(organization_id=organization_id)),
        }


# Default instance
_service: Optional[ProtocolService] = None


def get_protocol_service() -> ProtocolService:
    """Get default protocol service instance."""
    global _service
    if _service is None:
        _service = ProtocolService()
    return _service
