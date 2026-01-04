"""
Protocol Storage

Data persistence layer for protocols using SQLite.
"""

import sqlite3
import json
from pathlib import Path
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
    ProtocolStatus,
    ProtocolCategory,
    AccessLevel,
    ChecklistStatus,
    ChecklistItem,
)


class ProtocolStorage:
    """SQLite storage for protocols."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize storage."""
        if db_path is None:
            db_path = str(Path.home() / ".dora" / "protocols.db")

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS protocols (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    content TEXT,
                    structured_data TEXT,  -- JSON
                    current_version_id TEXT,
                    version_number TEXT,
                    created_by TEXT NOT NULL,
                    organization_id TEXT,
                    clinic_id TEXT,
                    status TEXT NOT NULL,
                    is_template INTEGER DEFAULT 0,
                    is_clinic_wide INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    published_at TEXT,
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    next_review_date TEXT,
                    evidence_grade TEXT,
                    references TEXT  -- JSON array
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS protocol_versions (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT NOT NULL,
                    version_number TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    structured_data TEXT,  -- JSON
                    change_summary TEXT,
                    changed_sections TEXT,  -- JSON array
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS quick_references (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    is_printable INTEGER DEFAULT 1,
                    layout TEXT DEFAULT 'card',
                    created_by TEXT NOT NULL,
                    organization_id TEXT,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS checklists (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    items TEXT NOT NULL,  -- JSON array
                    created_by TEXT NOT NULL,
                    organization_id TEXT,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    completion_rate REAL DEFAULT 0.0,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS checklist_executions (
                    id TEXT PRIMARY KEY,
                    checklist_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    patient_id TEXT,
                    encounter_id TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    items_status TEXT,  -- JSON
                    items_notes TEXT,  -- JSON
                    is_completed INTEGER DEFAULT 0,
                    completion_percentage REAL DEFAULT 0.0,
                    FOREIGN KEY (checklist_id) REFERENCES checklists (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS flowcharts (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    mermaid_diagram TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    organization_id TEXT,
                    created_at TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_annotations (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT NOT NULL,
                    version_id TEXT,
                    content TEXT NOT NULL,
                    section TEXT,
                    line_number INTEGER,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    parent_id TEXT,
                    is_resolved INTEGER DEFAULT 0,
                    resolved_by TEXT,
                    resolved_at TEXT,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id),
                    FOREIGN KEY (version_id) REFERENCES protocol_versions (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS protocol_shares (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT NOT NULL,
                    user_id TEXT,
                    team_id TEXT,
                    organization_id TEXT,
                    access_level TEXT NOT NULL,
                    shared_by TEXT NOT NULL,
                    shared_at TEXT NOT NULL,
                    expires_at TEXT,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS protocol_compliance (
                    id TEXT PRIMARY KEY,
                    protocol_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    patient_id TEXT,
                    encounter_id TEXT,
                    followed INTEGER DEFAULT 1,
                    deviation_reason TEXT,
                    deviation_sections TEXT,  -- JSON array
                    outcome_notes TEXT,
                    used_at TEXT NOT NULL,
                    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
                )
            """)

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_protocols_category ON protocols(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_protocols_status ON protocols(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_protocols_org ON protocols(organization_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_protocols_created_by ON protocols(created_by)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_protocol ON protocol_versions(protocol_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_annotations_protocol ON team_annotations(protocol_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_shares_protocol ON protocol_shares(protocol_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_compliance_protocol ON protocol_compliance(protocol_id)")

            conn.commit()

    # Protocol CRUD
    def create_protocol(self, protocol: Protocol) -> None:
        """Create a new protocol."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO protocols VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                protocol.id,
                protocol.title,
                protocol.description,
                protocol.category.value,
                json.dumps(protocol.tags),
                protocol.content,
                json.dumps(protocol.structured_data) if protocol.structured_data else None,
                protocol.current_version_id,
                protocol.version_number,
                protocol.created_by,
                protocol.organization_id,
                protocol.clinic_id,
                protocol.status.value,
                1 if protocol.is_template else 0,
                1 if protocol.is_clinic_wide else 0,
                protocol.usage_count,
                protocol.last_used_at.isoformat() if protocol.last_used_at else None,
                protocol.created_at.isoformat(),
                protocol.updated_at.isoformat(),
                protocol.published_at.isoformat() if protocol.published_at else None,
                protocol.reviewed_by,
                protocol.reviewed_at.isoformat() if protocol.reviewed_at else None,
                protocol.next_review_date.isoformat() if protocol.next_review_date else None,
                protocol.evidence_grade,
                json.dumps(protocol.references),
            ))
            conn.commit()

    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Get protocol by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM protocols WHERE id = ?", (protocol_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_protocol(row)

    def update_protocol(self, protocol: Protocol) -> None:
        """Update protocol."""
        protocol.updated_at = datetime.utcnow()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE protocols SET
                    title = ?, description = ?, category = ?, tags = ?,
                    content = ?, structured_data = ?, current_version_id = ?,
                    version_number = ?, status = ?, is_template = ?,
                    is_clinic_wide = ?, usage_count = ?, last_used_at = ?,
                    updated_at = ?, published_at = ?, reviewed_by = ?,
                    reviewed_at = ?, next_review_date = ?, evidence_grade = ?,
                    references = ?
                WHERE id = ?
            """, (
                protocol.title,
                protocol.description,
                protocol.category.value,
                json.dumps(protocol.tags),
                protocol.content,
                json.dumps(protocol.structured_data) if protocol.structured_data else None,
                protocol.current_version_id,
                protocol.version_number,
                protocol.status.value,
                1 if protocol.is_template else 0,
                1 if protocol.is_clinic_wide else 0,
                protocol.usage_count,
                protocol.last_used_at.isoformat() if protocol.last_used_at else None,
                protocol.updated_at.isoformat(),
                protocol.published_at.isoformat() if protocol.published_at else None,
                protocol.reviewed_by,
                protocol.reviewed_at.isoformat() if protocol.reviewed_at else None,
                protocol.next_review_date.isoformat() if protocol.next_review_date else None,
                protocol.evidence_grade,
                json.dumps(protocol.references),
                protocol.id,
            ))
            conn.commit()

    def delete_protocol(self, protocol_id: str) -> bool:
        """Delete protocol."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM protocols WHERE id = ?", (protocol_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_protocols(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        category: Optional[ProtocolCategory] = None,
        status: Optional[ProtocolStatus] = None,
        is_template: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Protocol]:
        """List protocols with filters."""
        query = "SELECT * FROM protocols WHERE 1=1"
        params = []

        if user_id:
            query += " AND created_by = ?"
            params.append(user_id)

        if organization_id:
            query += " AND organization_id = ?"
            params.append(organization_id)

        if category:
            query += " AND category = ?"
            params.append(category.value)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if is_template is not None:
            query += " AND is_template = ?"
            params.append(1 if is_template else 0)

        if search:
            query += " AND (title LIKE ? OR description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_protocol(row) for row in cursor.fetchall()]

    # Version CRUD
    def create_version(self, version: ProtocolVersion) -> None:
        """Create protocol version."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO protocol_versions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                version.id,
                version.protocol_id,
                version.version_number,
                version.title,
                version.content,
                json.dumps(version.structured_data) if version.structured_data else None,
                version.change_summary,
                json.dumps(version.changed_sections),
                version.created_by,
                version.created_at.isoformat(),
                version.status.value,
                version.approved_by,
                version.approved_at.isoformat() if version.approved_at else None,
            ))
            conn.commit()

    def get_protocol_versions(self, protocol_id: str) -> List[ProtocolVersion]:
        """Get all versions of a protocol."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM protocol_versions WHERE protocol_id = ? ORDER BY created_at DESC",
                (protocol_id,)
            )
            return [self._row_to_version(row) for row in cursor.fetchall()]

    # Quick Reference CRUD
    def create_quick_reference(self, ref: QuickReference) -> None:
        """Create quick reference."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO quick_references VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ref.id,
                ref.protocol_id,
                ref.title,
                ref.content,
                ref.card_type,
                1 if ref.is_printable else 0,
                ref.layout,
                ref.created_by,
                ref.organization_id,
                ref.created_at.isoformat(),
                ref.usage_count,
            ))
            conn.commit()

    def get_quick_references(
        self,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[QuickReference]:
        """Get quick references."""
        query = "SELECT * FROM quick_references WHERE 1=1"
        params = []

        if protocol_id:
            query += " AND protocol_id = ?"
            params.append(protocol_id)

        if organization_id:
            query += " AND organization_id = ?"
            params.append(organization_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_quick_reference(row) for row in cursor.fetchall()]

    # Checklist CRUD
    def create_checklist(self, checklist: Checklist) -> None:
        """Create checklist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO checklists VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                checklist.id,
                checklist.protocol_id,
                checklist.title,
                checklist.description,
                json.dumps([
                    {
                        "id": item.id,
                        "text": item.text,
                        "required": item.required,
                        "order": item.order,
                        "section": item.section,
                        "notes": item.notes,
                    }
                    for item in checklist.items
                ]),
                checklist.created_by,
                checklist.organization_id,
                checklist.created_at.isoformat(),
                checklist.usage_count,
                checklist.completion_rate,
            ))
            conn.commit()

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        """Get checklist by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM checklists WHERE id = ?", (checklist_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_checklist(row)

    def list_checklists(
        self,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[Checklist]:
        """List checklists."""
        query = "SELECT * FROM checklists WHERE 1=1"
        params = []

        if protocol_id:
            query += " AND protocol_id = ?"
            params.append(protocol_id)

        if organization_id:
            query += " AND organization_id = ?"
            params.append(organization_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_checklist(row) for row in cursor.fetchall()]

    # Checklist Execution CRUD
    def create_execution(self, execution: ChecklistExecution) -> None:
        """Create checklist execution."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO checklist_executions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                execution.id,
                execution.checklist_id,
                execution.user_id,
                execution.patient_id,
                execution.encounter_id,
                execution.started_at.isoformat(),
                execution.completed_at.isoformat() if execution.completed_at else None,
                json.dumps({k: v.value for k, v in execution.items_status.items()}),
                json.dumps(execution.items_notes),
                1 if execution.is_completed else 0,
                execution.completion_percentage,
            ))
            conn.commit()

    def update_execution(self, execution: ChecklistExecution) -> None:
        """Update checklist execution."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE checklist_executions SET
                    completed_at = ?, items_status = ?, items_notes = ?,
                    is_completed = ?, completion_percentage = ?
                WHERE id = ?
            """, (
                execution.completed_at.isoformat() if execution.completed_at else None,
                json.dumps({k: v.value for k, v in execution.items_status.items()}),
                json.dumps(execution.items_notes),
                1 if execution.is_completed else 0,
                execution.completion_percentage,
                execution.id,
            ))
            conn.commit()

    # Annotations
    def create_annotation(self, annotation: TeamAnnotation) -> None:
        """Create team annotation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO team_annotations VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                annotation.id,
                annotation.protocol_id,
                annotation.version_id,
                annotation.content,
                annotation.section,
                annotation.line_number,
                annotation.user_id,
                annotation.user_name,
                annotation.created_at.isoformat(),
                annotation.updated_at.isoformat(),
                annotation.parent_id,
                1 if annotation.is_resolved else 0,
                annotation.resolved_by,
                annotation.resolved_at.isoformat() if annotation.resolved_at else None,
            ))
            conn.commit()

    def get_annotations(self, protocol_id: str) -> List[TeamAnnotation]:
        """Get all annotations for protocol."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM team_annotations WHERE protocol_id = ? ORDER BY created_at ASC",
                (protocol_id,)
            )
            return [self._row_to_annotation(row) for row in cursor.fetchall()]

    # Shares
    def create_share(self, share: ProtocolShare) -> None:
        """Create protocol share."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO protocol_shares VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                share.id,
                share.protocol_id,
                share.user_id,
                share.team_id,
                share.organization_id,
                share.access_level.value,
                share.shared_by,
                share.shared_at.isoformat(),
                share.expires_at.isoformat() if share.expires_at else None,
            ))
            conn.commit()

    def get_shares(self, protocol_id: str) -> List[ProtocolShare]:
        """Get all shares for protocol."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM protocol_shares WHERE protocol_id = ?",
                (protocol_id,)
            )
            return [self._row_to_share(row) for row in cursor.fetchall()]

    # Compliance
    def create_compliance_record(self, record: ProtocolCompliance) -> None:
        """Create compliance record."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO protocol_compliance VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                record.id,
                record.protocol_id,
                record.user_id,
                record.patient_id,
                record.encounter_id,
                1 if record.followed else 0,
                record.deviation_reason,
                json.dumps(record.deviation_sections),
                record.outcome_notes,
                record.used_at.isoformat(),
            ))
            conn.commit()

    def get_compliance_records(
        self,
        protocol_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ProtocolCompliance]:
        """Get compliance records with filters."""
        query = "SELECT * FROM protocol_compliance WHERE 1=1"
        params = []

        if protocol_id:
            query += " AND protocol_id = ?"
            params.append(protocol_id)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if start_date:
            query += " AND used_at >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND used_at <= ?"
            params.append(end_date.isoformat())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_compliance(row) for row in cursor.fetchall()]

    # Helper methods to convert rows to objects
    def _row_to_protocol(self, row: sqlite3.Row) -> Protocol:
        """Convert database row to Protocol."""
        return Protocol(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            category=ProtocolCategory(row["category"]),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            content=row["content"] or "",
            structured_data=json.loads(row["structured_data"]) if row["structured_data"] else None,
            current_version_id=row["current_version_id"],
            version_number=row["version_number"],
            created_by=row["created_by"],
            organization_id=row["organization_id"],
            clinic_id=row["clinic_id"],
            status=ProtocolStatus(row["status"]),
            is_template=bool(row["is_template"]),
            is_clinic_wide=bool(row["is_clinic_wide"]),
            usage_count=row["usage_count"],
            last_used_at=datetime.fromisoformat(row["last_used_at"]) if row["last_used_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
            reviewed_by=row["reviewed_by"],
            reviewed_at=datetime.fromisoformat(row["reviewed_at"]) if row["reviewed_at"] else None,
            next_review_date=datetime.fromisoformat(row["next_review_date"]) if row["next_review_date"] else None,
            evidence_grade=row["evidence_grade"],
            references=json.loads(row["references"]) if row["references"] else [],
        )

    def _row_to_version(self, row: sqlite3.Row) -> ProtocolVersion:
        """Convert database row to ProtocolVersion."""
        return ProtocolVersion(
            id=row["id"],
            protocol_id=row["protocol_id"],
            version_number=row["version_number"],
            title=row["title"],
            content=row["content"] or "",
            structured_data=json.loads(row["structured_data"]) if row["structured_data"] else None,
            change_summary=row["change_summary"] or "",
            changed_sections=json.loads(row["changed_sections"]) if row["changed_sections"] else [],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=ProtocolStatus(row["status"]),
            approved_by=row["approved_by"],
            approved_at=datetime.fromisoformat(row["approved_at"]) if row["approved_at"] else None,
        )

    def _row_to_quick_reference(self, row: sqlite3.Row) -> QuickReference:
        """Convert database row to QuickReference."""
        return QuickReference(
            id=row["id"],
            protocol_id=row["protocol_id"],
            title=row["title"],
            content=row["content"],
            card_type=row["card_type"],
            is_printable=bool(row["is_printable"]),
            layout=row["layout"],
            created_by=row["created_by"],
            organization_id=row["organization_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            usage_count=row["usage_count"],
        )

    def _row_to_checklist(self, row: sqlite3.Row) -> Checklist:
        """Convert database row to Checklist."""
        items_data = json.loads(row["items"]) if row["items"] else []
        items = [
            ChecklistItem(
                id=item["id"],
                text=item["text"],
                required=item["required"],
                order=item["order"],
                section=item.get("section"),
                notes=item.get("notes"),
            )
            for item in items_data
        ]

        return Checklist(
            id=row["id"],
            protocol_id=row["protocol_id"],
            title=row["title"],
            description=row["description"] or "",
            items=items,
            created_by=row["created_by"],
            organization_id=row["organization_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            usage_count=row["usage_count"],
            completion_rate=row["completion_rate"],
        )

    def _row_to_annotation(self, row: sqlite3.Row) -> TeamAnnotation:
        """Convert database row to TeamAnnotation."""
        return TeamAnnotation(
            id=row["id"],
            protocol_id=row["protocol_id"],
            version_id=row["version_id"],
            content=row["content"],
            section=row["section"],
            line_number=row["line_number"],
            user_id=row["user_id"],
            user_name=row["user_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            parent_id=row["parent_id"],
            is_resolved=bool(row["is_resolved"]),
            resolved_by=row["resolved_by"],
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
        )

    def _row_to_share(self, row: sqlite3.Row) -> ProtocolShare:
        """Convert database row to ProtocolShare."""
        return ProtocolShare(
            id=row["id"],
            protocol_id=row["protocol_id"],
            user_id=row["user_id"],
            team_id=row["team_id"],
            organization_id=row["organization_id"],
            access_level=AccessLevel(row["access_level"]),
            shared_by=row["shared_by"],
            shared_at=datetime.fromisoformat(row["shared_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        )

    def _row_to_compliance(self, row: sqlite3.Row) -> ProtocolCompliance:
        """Convert database row to ProtocolCompliance."""
        return ProtocolCompliance(
            id=row["id"],
            protocol_id=row["protocol_id"],
            user_id=row["user_id"],
            patient_id=row["patient_id"],
            encounter_id=row["encounter_id"],
            followed=bool(row["followed"]),
            deviation_reason=row["deviation_reason"],
            deviation_sections=json.loads(row["deviation_sections"]) if row["deviation_sections"] else [],
            outcome_notes=row["outcome_notes"],
            used_at=datetime.fromisoformat(row["used_at"]),
        )


# Default instance
_storage: Optional[ProtocolStorage] = None


def get_protocol_storage() -> ProtocolStorage:
    """Get default protocol storage instance."""
    global _storage
    if _storage is None:
        _storage = ProtocolStorage()
    return _storage
