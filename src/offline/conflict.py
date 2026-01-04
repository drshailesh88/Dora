"""
Conflict Resolution for Data Synchronization

This module handles conflicts when local and server data diverge:
- Automatic resolution strategies
- Manual conflict resolution UI support
- Merge strategies for different data types
- Conflict logging and auditing
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

from .models import (
    ConflictRecord, ConflictResolution, SyncMetadata
)
from .storage import OfflineStorage

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    Handles conflict resolution between local and server data

    Strategies:
    - SERVER_WINS: Server data overwrites local
    - CLIENT_WINS: Local data overwrites server
    - LATEST_TIMESTAMP: Most recent modification wins
    - MERGE: Intelligent merge of both versions
    - MANUAL: Flag for user resolution
    """

    def __init__(
        self,
        storage: OfflineStorage,
        default_strategy: ConflictResolution = ConflictResolution.LATEST_TIMESTAMP
    ):
        self.storage = storage
        self.default_strategy = default_strategy

        # Strategy handlers
        self.strategy_handlers = {
            ConflictResolution.SERVER_WINS: self._server_wins,
            ConflictResolution.CLIENT_WINS: self._client_wins,
            ConflictResolution.LATEST_TIMESTAMP: self._latest_timestamp,
            ConflictResolution.MERGE: self._merge_data,
            ConflictResolution.MANUAL: self._flag_for_manual
        }

    async def resolve_conflict(
        self,
        conflict_data: Dict[str, Any],
        strategy: Optional[ConflictResolution] = None
    ) -> ConflictRecord:
        """
        Resolve a sync conflict

        Args:
            conflict_data: Conflict information
            strategy: Resolution strategy (uses default if None)

        Returns:
            ConflictRecord with resolution details
        """
        entity_id = conflict_data["entity_id"]
        entity_type = conflict_data["entity_type"]

        # Get local and server data
        local_data = await self._get_local_data(entity_id, entity_type)
        server_data = conflict_data["server_data"]

        # Create conflict record
        conflict = ConflictRecord(
            entity_id=entity_id,
            entity_type=entity_type,
            local_data=local_data,
            server_data=server_data
        )

        # Determine strategy
        resolution_strategy = strategy or self.default_strategy

        # Get handler
        handler = self.strategy_handlers.get(resolution_strategy)
        if not handler:
            logger.error(f"Unknown resolution strategy: {resolution_strategy}")
            handler = self._flag_for_manual
            resolution_strategy = ConflictResolution.MANUAL

        # Resolve conflict
        try:
            resolved_data = await handler(conflict)

            conflict.resolution_strategy = resolution_strategy
            conflict.resolved_data = resolved_data
            conflict.resolved_at = datetime.utcnow()
            conflict.resolved_by = "auto"

            # Save conflict record
            self._save_conflict_record(conflict)

            # Apply resolved data
            if resolved_data and resolution_strategy != ConflictResolution.MANUAL:
                await self._apply_resolution(conflict)

            logger.info(
                f"Resolved conflict for {entity_type} {entity_id} "
                f"using {resolution_strategy.value}"
            )

        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            conflict.resolution_strategy = ConflictResolution.MANUAL
            self._save_conflict_record(conflict)

        return conflict

    async def _get_local_data(
        self,
        entity_id: str,
        entity_type: str
    ) -> Dict[str, Any]:
        """Get local version of entity"""
        if entity_type == "document":
            doc = self.storage.get_document(entity_id)
            if doc:
                return doc.dict()

        elif entity_type == "query":
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM offline_queries WHERE id = ?",
                    (entity_id,)
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)

        return {}

    async def _server_wins(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Server data wins - overwrite local"""
        logger.info(f"Resolution: SERVER_WINS for {conflict.entity_id}")
        return conflict.server_data

    async def _client_wins(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Client data wins - keep local"""
        logger.info(f"Resolution: CLIENT_WINS for {conflict.entity_id}")
        return conflict.local_data

    async def _latest_timestamp(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Most recent modification wins"""
        local_updated = conflict.local_data.get("updated_at")
        server_updated = conflict.server_data.get("updated_at")

        if not local_updated and not server_updated:
            # No timestamps, default to server
            return conflict.server_data

        if not local_updated:
            return conflict.server_data

        if not server_updated:
            return conflict.local_data

        # Parse timestamps
        try:
            local_dt = datetime.fromisoformat(local_updated.replace('Z', '+00:00'))
            server_dt = datetime.fromisoformat(server_updated.replace('Z', '+00:00'))

            if local_dt > server_dt:
                logger.info(
                    f"Resolution: LATEST_TIMESTAMP (local) for {conflict.entity_id}"
                )
                return conflict.local_data
            else:
                logger.info(
                    f"Resolution: LATEST_TIMESTAMP (server) for {conflict.entity_id}"
                )
                return conflict.server_data

        except Exception as e:
            logger.error(f"Error parsing timestamps: {e}")
            return conflict.server_data

    async def _merge_data(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Intelligent merge of local and server data"""
        logger.info(f"Resolution: MERGE for {conflict.entity_id}")

        merged = {}

        # Get all keys from both versions
        all_keys = set(conflict.local_data.keys()) | set(conflict.server_data.keys())

        for key in all_keys:
            local_value = conflict.local_data.get(key)
            server_value = conflict.server_data.get(key)

            # If same, use either
            if local_value == server_value:
                merged[key] = local_value
                continue

            # If only one has value, use that
            if local_value is None:
                merged[key] = server_value
                continue
            if server_value is None:
                merged[key] = local_value
                continue

            # Different values - apply merge strategy based on type
            merged[key] = self._merge_field(
                key,
                local_value,
                server_value,
                conflict.entity_type
            )

        return merged

    def _merge_field(
        self,
        field: str,
        local_value: Any,
        server_value: Any,
        entity_type: str
    ) -> Any:
        """Merge individual field values"""
        # For lists, merge unique items
        if isinstance(local_value, list) and isinstance(server_value, list):
            # Combine and deduplicate
            merged = list(set(local_value + server_value))
            return merged

        # For dicts, recursive merge
        if isinstance(local_value, dict) and isinstance(server_value, dict):
            merged = {}
            all_keys = set(local_value.keys()) | set(server_value.keys())
            for k in all_keys:
                if k in local_value and k in server_value:
                    merged[k] = self._merge_field(
                        k,
                        local_value[k],
                        server_value[k],
                        entity_type
                    )
                elif k in local_value:
                    merged[k] = local_value[k]
                else:
                    merged[k] = server_value[k]
            return merged

        # For numbers, use maximum (assuming increment-only fields)
        if isinstance(local_value, (int, float)) and isinstance(server_value, (int, float)):
            if field in ['access_count', 'version', 'retry_count']:
                return max(local_value, server_value)

        # For strings, prefer longer (more complete)
        if isinstance(local_value, str) and isinstance(server_value, str):
            if field in ['content', 'description', 'result']:
                return local_value if len(local_value) > len(server_value) else server_value

        # Default: prefer server value
        return server_value

    async def _flag_for_manual(self, conflict: ConflictRecord) -> Dict[str, Any]:
        """Flag conflict for manual resolution"""
        logger.info(f"Resolution: MANUAL (flagged) for {conflict.entity_id}")
        # Return None to indicate manual resolution needed
        return None

    async def _apply_resolution(self, conflict: ConflictRecord):
        """Apply resolved data to storage"""
        if not conflict.resolved_data:
            return

        entity_type = conflict.entity_type
        resolved = conflict.resolved_data

        try:
            if entity_type == "document":
                # Update cached document
                from .models import CachedDocument
                doc = CachedDocument(**resolved)
                self.storage.save_document(doc)

            elif entity_type == "query":
                # Update query
                from .models import OfflineQuery
                query = OfflineQuery(**resolved)
                self.storage.save_query(query)

            # Update sync metadata
            self._update_sync_metadata(
                conflict.entity_id,
                entity_type,
                resolved.get("version", 1)
            )

        except Exception as e:
            logger.error(f"Error applying resolution: {e}")

    def _save_conflict_record(self, conflict: ConflictRecord):
        """Save conflict record to database"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO conflict_records VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    conflict.id,
                    conflict.entity_id,
                    conflict.entity_type,
                    json.dumps(conflict.local_data),
                    json.dumps(conflict.server_data),
                    conflict.conflict_detected_at.isoformat(),
                    conflict.resolution_strategy.value if conflict.resolution_strategy else None,
                    conflict.resolved_at.isoformat() if conflict.resolved_at else None,
                    conflict.resolved_by,
                    json.dumps(conflict.resolved_data) if conflict.resolved_data else None
                ))

        except Exception as e:
            logger.error(f"Error saving conflict record: {e}")

    def _update_sync_metadata(
        self,
        entity_id: str,
        entity_type: str,
        version: int
    ):
        """Update sync metadata after resolution"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()

                # Check if exists
                cursor.execute(
                    "SELECT * FROM sync_metadata WHERE entity_id = ?",
                    (entity_id,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    cursor.execute("""
                        UPDATE sync_metadata
                        SET local_version = ?,
                            server_version = ?,
                            last_sync_time = ?,
                            conflict_detected = 0
                        WHERE entity_id = ?
                    """, (
                        version,
                        version,
                        datetime.utcnow().isoformat(),
                        entity_id
                    ))
                else:
                    metadata = SyncMetadata(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        local_version=version,
                        server_version=version,
                        last_sync_time=datetime.utcnow()
                    )

                    cursor.execute("""
                        INSERT INTO sync_metadata VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        metadata.entity_id,
                        metadata.entity_type,
                        metadata.local_version,
                        metadata.server_version,
                        metadata.last_sync_time.isoformat(),
                        metadata.local_checksum,
                        metadata.server_checksum,
                        0,
                        None
                    ))

        except Exception as e:
            logger.error(f"Error updating sync metadata: {e}")

    def get_pending_conflicts(self) -> List[ConflictRecord]:
        """Get conflicts pending manual resolution"""
        conflicts = []

        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM conflict_records
                    WHERE resolution_strategy = ? OR resolved_at IS NULL
                    ORDER BY conflict_detected_at DESC
                """, (ConflictResolution.MANUAL.value,))

                rows = cursor.fetchall()

                for row in rows:
                    conflict = ConflictRecord(
                        id=row["id"],
                        entity_id=row["entity_id"],
                        entity_type=row["entity_type"],
                        local_data=json.loads(row["local_data"]),
                        server_data=json.loads(row["server_data"]),
                        conflict_detected_at=datetime.fromisoformat(row["conflict_detected_at"]),
                        resolution_strategy=ConflictResolution(row["resolution_strategy"]) if row["resolution_strategy"] else None,
                        resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
                        resolved_by=row["resolved_by"],
                        resolved_data=json.loads(row["resolved_data"]) if row["resolved_data"] else None
                    )
                    conflicts.append(conflict)

        except Exception as e:
            logger.error(f"Error getting pending conflicts: {e}")

        return conflicts

    async def resolve_manual_conflict(
        self,
        conflict_id: str,
        chosen_version: str,  # "local" or "server" or "custom"
        custom_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Manually resolve a conflict

        Args:
            conflict_id: Conflict ID
            chosen_version: Which version to use
            custom_data: Custom merged data if chosen_version is "custom"

        Returns:
            Success status
        """
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM conflict_records WHERE id = ?",
                    (conflict_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.error(f"Conflict not found: {conflict_id}")
                    return False

                conflict = ConflictRecord(
                    id=row["id"],
                    entity_id=row["entity_id"],
                    entity_type=row["entity_type"],
                    local_data=json.loads(row["local_data"]),
                    server_data=json.loads(row["server_data"]),
                    conflict_detected_at=datetime.fromisoformat(row["conflict_detected_at"])
                )

                # Determine resolved data
                if chosen_version == "local":
                    resolved_data = conflict.local_data
                    strategy = ConflictResolution.CLIENT_WINS
                elif chosen_version == "server":
                    resolved_data = conflict.server_data
                    strategy = ConflictResolution.SERVER_WINS
                elif chosen_version == "custom" and custom_data:
                    resolved_data = custom_data
                    strategy = ConflictResolution.MERGE
                else:
                    logger.error(f"Invalid chosen_version: {chosen_version}")
                    return False

                # Update conflict record
                conflict.resolution_strategy = strategy
                conflict.resolved_data = resolved_data
                conflict.resolved_at = datetime.utcnow()
                conflict.resolved_by = "manual"

                self._save_conflict_record(conflict)

                # Apply resolution
                await self._apply_resolution(conflict)

                logger.info(f"Manually resolved conflict {conflict_id}")
                return True

        except Exception as e:
            logger.error(f"Error resolving manual conflict: {e}")
            return False

    def get_conflict_stats(self) -> Dict[str, Any]:
        """Get conflict statistics"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT COUNT(*) FROM conflict_records"
                )
                total = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM conflict_records
                    WHERE resolved_at IS NOT NULL
                """)
                resolved = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM conflict_records
                    WHERE resolution_strategy = ?
                """, (ConflictResolution.MANUAL.value,))
                pending_manual = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT resolution_strategy, COUNT(*) as count
                    FROM conflict_records
                    WHERE resolution_strategy IS NOT NULL
                    GROUP BY resolution_strategy
                """)
                strategy_breakdown = {
                    row[0]: row[1] for row in cursor.fetchall()
                }

                return {
                    "total_conflicts": total,
                    "resolved": resolved,
                    "pending_manual": pending_manual,
                    "strategy_breakdown": strategy_breakdown
                }

        except Exception as e:
            logger.error(f"Error getting conflict stats: {e}")
            return {}
