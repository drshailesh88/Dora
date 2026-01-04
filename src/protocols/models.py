"""
Protocol Data Models

Clinical protocol management models for team-based best practices.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class ProtocolStatus(str, Enum):
    """Protocol version status."""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProtocolCategory(str, Enum):
    """Protocol categories."""
    EMERGENCY = "emergency"
    CHRONIC_CARE = "chronic_care"
    PROCEDURES = "procedures"
    MEDICATIONS = "medications"
    DIAGNOSTICS = "diagnostics"
    POST_OP = "post_op"
    PEDIATRICS = "pediatrics"
    OB_GYN = "ob_gyn"
    INFECTIOUS_DISEASE = "infectious_disease"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    RESPIRATORY = "respiratory"
    GENERAL = "general"


class AccessLevel(str, Enum):
    """Access levels for protocol sharing."""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    APPROVE = "approve"
    OWNER = "owner"


class ChecklistStatus(str, Enum):
    """Checklist item status."""
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Protocol:
    """Clinical protocol document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Metadata
    title: str = ""
    description: str = ""
    category: ProtocolCategory = ProtocolCategory.GENERAL
    tags: List[str] = field(default_factory=list)

    # Content
    content: str = ""  # Markdown content
    structured_data: Optional[Dict[str, Any]] = None  # JSON for structured sections

    # Version
    current_version_id: Optional[str] = None
    version_number: str = "1.0"

    # Ownership
    created_by: str = ""  # User ID
    organization_id: Optional[str] = None
    clinic_id: Optional[str] = None

    # Status
    status: ProtocolStatus = ProtocolStatus.DRAFT
    is_template: bool = False
    is_clinic_wide: bool = False

    # Usage tracking
    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Review
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None

    # Evidence
    evidence_grade: Optional[str] = None  # A, B, C, D
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "tags": self.tags,
            "content": self.content,
            "structured_data": self.structured_data,
            "version_number": self.version_number,
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "clinic_id": self.clinic_id,
            "status": self.status.value,
            "is_template": self.is_template,
            "is_clinic_wide": self.is_clinic_wide,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "evidence_grade": self.evidence_grade,
            "references": self.references,
        }


@dataclass
class ProtocolVersion:
    """Protocol version history."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str = ""

    # Version info
    version_number: str = "1.0"
    title: str = ""
    content: str = ""
    structured_data: Optional[Dict[str, Any]] = None

    # Changes
    change_summary: str = ""
    changed_sections: List[str] = field(default_factory=list)

    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ProtocolStatus = ProtocolStatus.DRAFT

    # Review
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "version_number": self.version_number,
            "title": self.title,
            "content": self.content,
            "structured_data": self.structured_data,
            "change_summary": self.change_summary,
            "changed_sections": self.changed_sections,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


@dataclass
class QuickReference:
    """Quick reference card/pocket guide."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: Optional[str] = None

    # Content
    title: str = ""
    content: str = ""  # Markdown or structured text
    card_type: str = "dosing"  # dosing, lab_values, scoring, algorithm

    # Display
    is_printable: bool = True
    layout: str = "card"  # card, table, flowchart

    # Metadata
    created_by: str = ""
    organization_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Usage
    usage_count: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "title": self.title,
            "content": self.content,
            "card_type": self.card_type,
            "is_printable": self.is_printable,
            "layout": self.layout,
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
        }


@dataclass
class ChecklistItem:
    """Individual checklist item."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    required: bool = True
    order: int = 0
    section: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Checklist:
    """Procedural checklist."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: Optional[str] = None

    # Content
    title: str = ""
    description: str = ""
    items: List[ChecklistItem] = field(default_factory=list)

    # Metadata
    created_by: str = ""
    organization_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Usage
    usage_count: int = 0
    completion_rate: float = 0.0  # Average completion rate

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "title": self.title,
            "description": self.description,
            "items": [
                {
                    "id": item.id,
                    "text": item.text,
                    "required": item.required,
                    "order": item.order,
                    "section": item.section,
                    "notes": item.notes,
                }
                for item in self.items
            ],
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
            "completion_rate": self.completion_rate,
        }


@dataclass
class ChecklistExecution:
    """Checklist execution instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    checklist_id: str = ""

    # Context
    user_id: str = ""
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None

    # Status
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Items status
    items_status: Dict[str, ChecklistStatus] = field(default_factory=dict)
    items_notes: Dict[str, str] = field(default_factory=dict)

    # Completion
    is_completed: bool = False
    completion_percentage: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "checklist_id": self.checklist_id,
            "user_id": self.user_id,
            "patient_id": self.patient_id,
            "encounter_id": self.encounter_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items_status": {k: v.value for k, v in self.items_status.items()},
            "items_notes": self.items_notes,
            "is_completed": self.is_completed,
            "completion_percentage": self.completion_percentage,
        }


@dataclass
class Flowchart:
    """Decision flowchart."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: Optional[str] = None

    # Content
    title: str = ""
    description: str = ""
    mermaid_diagram: str = ""  # Mermaid syntax

    # Metadata
    created_by: str = ""
    organization_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Usage
    usage_count: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "title": self.title,
            "description": self.description,
            "mermaid_diagram": self.mermaid_diagram,
            "created_by": self.created_by,
            "organization_id": self.organization_id,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
        }


@dataclass
class TeamAnnotation:
    """Team comment/annotation on protocol."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str = ""
    version_id: Optional[str] = None

    # Content
    content: str = ""
    section: Optional[str] = None  # Which section this refers to
    line_number: Optional[int] = None

    # Metadata
    user_id: str = ""
    user_name: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Thread
    parent_id: Optional[str] = None  # For replies
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "version_id": self.version_id,
            "content": self.content,
            "section": self.section,
            "line_number": self.line_number,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parent_id": self.parent_id,
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class ProtocolShare:
    """Protocol sharing configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str = ""

    # Recipient
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    organization_id: Optional[str] = None

    # Access
    access_level: AccessLevel = AccessLevel.VIEW

    # Metadata
    shared_by: str = ""
    shared_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "organization_id": self.organization_id,
            "access_level": self.access_level.value,
            "shared_by": self.shared_by,
            "shared_at": self.shared_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class ProtocolCompliance:
    """Protocol compliance tracking."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str = ""

    # Context
    user_id: str = ""
    patient_id: Optional[str] = None
    encounter_id: Optional[str] = None

    # Compliance
    followed: bool = True
    deviation_reason: Optional[str] = None
    deviation_sections: List[str] = field(default_factory=list)

    # Outcome
    outcome_notes: Optional[str] = None

    # Timestamps
    used_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocol_id": self.protocol_id,
            "user_id": self.user_id,
            "patient_id": self.patient_id,
            "encounter_id": self.encounter_id,
            "followed": self.followed,
            "deviation_reason": self.deviation_reason,
            "deviation_sections": self.deviation_sections,
            "outcome_notes": self.outcome_notes,
            "used_at": self.used_at.isoformat(),
        }


@dataclass
class ComplianceReport:
    """Compliance metrics report."""
    protocol_id: str
    protocol_title: str

    # Metrics
    total_uses: int = 0
    compliant_uses: int = 0
    compliance_rate: float = 0.0

    # Deviations
    deviation_count: int = 0
    common_deviations: List[Dict[str, Any]] = field(default_factory=list)

    # Time period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "protocol_id": self.protocol_id,
            "protocol_title": self.protocol_title,
            "total_uses": self.total_uses,
            "compliant_uses": self.compliant_uses,
            "compliance_rate": self.compliance_rate,
            "deviation_count": self.deviation_count,
            "common_deviations": self.common_deviations,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }
