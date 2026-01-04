"""Bidirectional EMR sync for patient data and recommendations."""

import asyncio
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from .client import EMRClient
from .models import ClinicalNote, Order, PatientSummary


class SyncDirection(str, Enum):
    """Sync direction."""

    PULL = "pull"  # Pull data from EMR to Dora
    PUSH = "push"  # Push data from Dora to EMR
    BIDIRECTIONAL = "bidirectional"  # Both directions


class SyncStatus(str, Enum):
    """Sync operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncRecord(BaseModel):
    """Record of a sync operation."""

    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    patient_id: int
    sync_type: str = Field(
        description="patient_context, recommendation, note, order"
    )
    direction: SyncDirection
    status: SyncStatus = SyncStatus.PENDING
    data: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    retry_count: int = 0


class ConflictResolution(str, Enum):
    """How to resolve sync conflicts."""

    EMR_WINS = "emr_wins"  # EMR data takes precedence
    DORA_WINS = "dora_wins"  # Dora data takes precedence
    MANUAL = "manual"  # Require manual resolution
    NEWEST = "newest"  # Most recently updated wins


class EMRSyncManager:
    """
    Manages bidirectional synchronization with EMR.

    Features:
    - Pull patient context before queries
    - Push recommendations back to EMR
    - Push clinical notes
    - Push orders (medications, labs, imaging)
    - Conflict resolution
    - Audit trail
    - Offline queue
    """

    def __init__(
        self,
        emr_client: EMRClient,
        offline_queue_path: Optional[Path] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.EMR_WINS,
    ):
        """
        Initialize sync manager.

        Args:
            emr_client: EMR API client
            offline_queue_path: Path to offline queue storage
            conflict_resolution: Default conflict resolution strategy
        """
        self.emr = emr_client
        self.conflict_resolution = conflict_resolution
        self.offline_queue_path = offline_queue_path or Path("./data/sync_queue")
        self.offline_queue_path.mkdir(parents=True, exist_ok=True)

        # In-memory sync records
        self._sync_records: list[SyncRecord] = []
        self._load_offline_queue()

    def _load_offline_queue(self):
        """Load pending syncs from offline queue."""
        queue_file = self.offline_queue_path / "pending_syncs.json"
        if queue_file.exists():
            try:
                with open(queue_file) as f:
                    data = json.load(f)
                    self._sync_records = [
                        SyncRecord(**record) for record in data
                    ]
            except (json.JSONDecodeError, ValueError):
                pass

    def _save_offline_queue(self):
        """Save pending syncs to offline queue."""
        queue_file = self.offline_queue_path / "pending_syncs.json"
        with open(queue_file, "w") as f:
            data = [
                record.model_dump()
                for record in self._sync_records
                if record.status in [SyncStatus.PENDING, SyncStatus.CONFLICT]
            ]
            json.dump(data, f, default=str, indent=2)

    async def pull_patient_context(
        self, patient_id: int
    ) -> Optional[PatientSummary]:
        """
        Pull patient context from EMR.

        Args:
            patient_id: Patient ID

        Returns:
            Patient summary or None if failed
        """
        record = SyncRecord(
            patient_id=patient_id,
            sync_type="patient_context",
            direction=SyncDirection.PULL,
            status=SyncStatus.IN_PROGRESS,
        )
        self._sync_records.append(record)

        try:
            summary = await self.emr.get_patient_summary(patient_id)
            if summary:
                record.status = SyncStatus.COMPLETED
                record.completed_at = datetime.utcnow()
                record.data = {"summary": summary.model_dump()}
                return summary
            else:
                record.status = SyncStatus.FAILED
                record.error_message = "Patient not found"
                return None
        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            self._save_offline_queue()
            raise

    async def push_clinical_note(
        self,
        patient_id: int,
        note: ClinicalNote,
    ) -> bool:
        """
        Push clinical note to EMR.

        Args:
            patient_id: Patient ID
            note: Clinical note to push

        Returns:
            True if successful
        """
        record = SyncRecord(
            patient_id=patient_id,
            sync_type="clinical_note",
            direction=SyncDirection.PUSH,
            status=SyncStatus.PENDING,
            data=note.model_dump(),
        )
        self._sync_records.append(record)

        try:
            # In a real implementation, this would call EMR API
            # For now, just simulate
            record.status = SyncStatus.IN_PROGRESS

            # Simulate API call
            await asyncio.sleep(0.1)

            # TODO: Actual API call
            # await self.emr.create_clinical_note(note)

            record.status = SyncStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            return True

        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            self._save_offline_queue()
            return False

    async def push_order(
        self,
        patient_id: int,
        order: Order,
    ) -> Optional[Order]:
        """
        Push clinical order to EMR.

        Args:
            patient_id: Patient ID
            order: Order to create

        Returns:
            Created order with ID or None if failed
        """
        record = SyncRecord(
            patient_id=patient_id,
            sync_type="order",
            direction=SyncDirection.PUSH,
            status=SyncStatus.PENDING,
            data=order.model_dump(),
        )
        self._sync_records.append(record)

        try:
            record.status = SyncStatus.IN_PROGRESS
            created_order = await self.emr.create_order(order)
            record.status = SyncStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            record.data = created_order.model_dump()
            return created_order

        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            self._save_offline_queue()
            return None

    async def push_recommendation(
        self,
        patient_id: int,
        recommendation: dict[str, Any],
    ) -> bool:
        """
        Push Dora recommendation to EMR.

        Args:
            patient_id: Patient ID
            recommendation: Recommendation data

        Returns:
            True if successful
        """
        record = SyncRecord(
            patient_id=patient_id,
            sync_type="recommendation",
            direction=SyncDirection.PUSH,
            status=SyncStatus.PENDING,
            data=recommendation,
        )
        self._sync_records.append(record)

        try:
            record.status = SyncStatus.IN_PROGRESS

            # Convert recommendation to clinical note
            note = ClinicalNote(
                patient_id=patient_id,
                note_type="progress",
                full_note=f"Dora Recommendation:\n\n{recommendation.get('answer', '')}",
                author="Dora AI",
            )

            # Push as clinical note
            success = await self.push_clinical_note(patient_id, note)

            if success:
                record.status = SyncStatus.COMPLETED
                record.completed_at = datetime.utcnow()
            else:
                record.status = SyncStatus.FAILED

            return success

        except Exception as e:
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            self._save_offline_queue()
            return False

    async def sync_pending_queue(self) -> dict[str, int]:
        """
        Sync all pending items in offline queue.

        Returns:
            Dict with counts of successful/failed syncs
        """
        results = {"successful": 0, "failed": 0, "total": 0}

        pending = [
            r for r in self._sync_records if r.status == SyncStatus.PENDING
        ]
        results["total"] = len(pending)

        for record in pending:
            record.retry_count += 1
            try:
                if record.sync_type == "clinical_note":
                    note = ClinicalNote(**record.data)
                    success = await self.push_clinical_note(
                        record.patient_id, note
                    )
                    if success:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                elif record.sync_type == "order":
                    order = Order(**record.data)
                    created = await self.push_order(record.patient_id, order)
                    if created:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

            except Exception as e:
                record.status = SyncStatus.FAILED
                record.error_message = str(e)
                results["failed"] += 1

        self._save_offline_queue()
        return results

    def get_sync_history(
        self,
        patient_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[SyncRecord]:
        """
        Get sync history.

        Args:
            patient_id: Filter by patient ID
            limit: Max records to return

        Returns:
            List of sync records
        """
        records = self._sync_records
        if patient_id:
            records = [r for r in records if r.patient_id == patient_id]

        return sorted(
            records,
            key=lambda x: x.started_at,
            reverse=True,
        )[:limit]

    def get_sync_stats(self) -> dict[str, Any]:
        """
        Get sync statistics.

        Returns:
            Dict with sync stats
        """
        total = len(self._sync_records)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "success_rate": 0.0,
            }

        completed = sum(
            1 for r in self._sync_records if r.status == SyncStatus.COMPLETED
        )
        failed = sum(
            1 for r in self._sync_records if r.status == SyncStatus.FAILED
        )
        pending = sum(
            1 for r in self._sync_records if r.status == SyncStatus.PENDING
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": (completed / total * 100) if total > 0 else 0.0,
        }

    async def resolve_conflict(
        self,
        record_id: str,
        resolution: ConflictResolution,
    ) -> bool:
        """
        Resolve a sync conflict.

        Args:
            record_id: Sync record ID
            resolution: How to resolve

        Returns:
            True if resolved successfully
        """
        for record in self._sync_records:
            if record.id == record_id and record.status == SyncStatus.CONFLICT:
                if resolution == ConflictResolution.EMR_WINS:
                    # Discard Dora changes, use EMR data
                    record.status = SyncStatus.COMPLETED
                    record.completed_at = datetime.utcnow()
                    return True

                elif resolution == ConflictResolution.DORA_WINS:
                    # Force push Dora data to EMR
                    record.status = SyncStatus.PENDING
                    # Will be retried in next sync
                    return True

                elif resolution == ConflictResolution.MANUAL:
                    # Keep in conflict state for manual review
                    return False

        return False

    def create_audit_trail(
        self,
        patient_id: int,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        Create audit trail entry for EMR access.

        Args:
            patient_id: Patient ID accessed
            action: Action performed
            user_id: User who performed action
            details: Additional details
        """
        audit_file = self.offline_queue_path / "audit_trail.jsonl"
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "patient_id": patient_id,
            "action": action,
            "user_id": user_id,
            "details": details or {},
        }

        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
