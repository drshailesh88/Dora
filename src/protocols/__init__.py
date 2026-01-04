"""
Protocol Management Module

Team protocol library for sharing clinical best practices.
"""

# Models
from .models import (
    Protocol,
    ProtocolVersion,
    ProtocolCategory,
    ProtocolStatus,
    QuickReference,
    Checklist,
    ChecklistItem,
    ChecklistExecution,
    ChecklistStatus,
    Flowchart,
    TeamAnnotation,
    ProtocolShare,
    ProtocolCompliance,
    ComplianceReport,
    AccessLevel,
)

# Storage
from .storage import ProtocolStorage, get_protocol_storage

# Core managers
from .library import ProtocolLibrary, get_protocol_library
from .templates import create_from_template, list_templates, get_template
from .references import QuickReferenceManager, get_reference_manager
from .checklists import ChecklistManager, get_checklist_manager
from .flowcharts import FlowchartManager, get_flowchart_manager
from .versioning import VersionManager, get_version_manager
from .sharing import SharingManager, get_sharing_manager
from .compliance import ComplianceTracker, get_compliance_tracker

# Unified service
from .service import ProtocolService, get_protocol_service


__all__ = [
    # Models
    "Protocol",
    "ProtocolVersion",
    "ProtocolCategory",
    "ProtocolStatus",
    "QuickReference",
    "Checklist",
    "ChecklistItem",
    "ChecklistExecution",
    "ChecklistStatus",
    "Flowchart",
    "TeamAnnotation",
    "ProtocolShare",
    "ProtocolCompliance",
    "ComplianceReport",
    "AccessLevel",
    # Storage
    "ProtocolStorage",
    "get_protocol_storage",
    # Managers
    "ProtocolLibrary",
    "get_protocol_library",
    "QuickReferenceManager",
    "get_reference_manager",
    "ChecklistManager",
    "get_checklist_manager",
    "FlowchartManager",
    "get_flowchart_manager",
    "VersionManager",
    "get_version_manager",
    "SharingManager",
    "get_sharing_manager",
    "ComplianceTracker",
    "get_compliance_tracker",
    # Service
    "ProtocolService",
    "get_protocol_service",
    # Templates
    "create_from_template",
    "list_templates",
    "get_template",
]
