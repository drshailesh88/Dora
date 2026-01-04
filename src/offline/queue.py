"""
Offline Action Queue Management

This module manages queued actions when offline:
- Query queue
- Search queue
- User actions (bookmarks, annotations)
- Priority-based processing
- Retry logic with exponential backoff
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from collections import defaultdict
import asyncio

from .models import (
    OfflineAction, ActionType, Priority, SyncStatus,
    OfflineQuery, SyncBatch
)
from .storage import OfflineStorage

logger = logging.getLogger(__name__)


class ActionQueue:
    """
    Manages offline actions with priority-based processing

    Features:
    - Priority queue (CRITICAL -> HIGH -> MEDIUM -> LOW)
    - Retry logic with exponential backoff
    - Batch processing
    - Action deduplication
    """

    def __init__(
        self,
        storage: OfflineStorage,
        max_retry_attempts: int = 3,
        base_retry_delay_seconds: int = 5
    ):
        self.storage = storage
        self.max_retry_attempts = max_retry_attempts
        self.base_retry_delay = base_retry_delay_seconds

        # Action handlers
        self.handlers: Dict[ActionType, Callable] = {}

    def register_handler(
        self,
        action_type: ActionType,
        handler: Callable
    ):
        """Register a handler for specific action type"""
        self.handlers[action_type] = handler
        logger.info(f"Registered handler for {action_type.value}")

    def enqueue(
        self,
        action: OfflineAction,
        deduplicate: bool = True
    ) -> bool:
        """
        Add action to queue

        Args:
            action: Action to enqueue
            deduplicate: Check for duplicate actions

        Returns:
            True if enqueued, False if duplicate or error
        """
        try:
            # Check for duplicates if requested
            if deduplicate:
                existing = self._find_duplicate(action)
                if existing:
                    logger.info(
                        f"Duplicate action found: {action.id}, skipping"
                    )
                    return False

            # Save to storage
            success = self.storage.save_action(action)

            if success:
                logger.info(
                    f"Enqueued action: {action.action_type.value} "
                    f"(priority: {action.priority.value})"
                )

            return success

        except Exception as e:
            logger.error(f"Error enqueueing action: {e}")
            return False

    def _find_duplicate(self, action: OfflineAction) -> Optional[OfflineAction]:
        """Find duplicate action in queue"""
        # Get pending actions of same type
        pending = self.storage.get_pending_actions()

        for existing in pending:
            if (existing.action_type == action.action_type and
                    existing.payload == action.payload and
                    existing.user_id == action.user_id):
                return existing

        return None

    def get_next_batch(
        self,
        batch_size: int = 10,
        priority_filter: Optional[Priority] = None
    ) -> Optional[SyncBatch]:
        """
        Get next batch of actions to process

        Args:
            batch_size: Maximum actions in batch
            priority_filter: Only get actions of this priority

        Returns:
            SyncBatch or None if queue empty
        """
        actions = self.storage.get_pending_actions(
            priority=priority_filter,
            limit=batch_size
        )

        if not actions:
            return None

        # Group by priority (highest first)
        priority_order = [
            Priority.CRITICAL,
            Priority.HIGH,
            Priority.MEDIUM,
            Priority.LOW
        ]

        # Take top priority actions
        for priority in priority_order:
            priority_actions = [
                a for a in actions if a.priority == priority
            ]
            if priority_actions:
                batch = SyncBatch(
                    priority=priority,
                    items=priority_actions[:batch_size]
                )
                return batch

        return None

    async def process_batch(
        self,
        batch: SyncBatch,
        online: bool = False
    ) -> Dict[str, Any]:
        """
        Process a batch of actions

        Args:
            batch: Batch to process
            online: Whether system is online

        Returns:
            Processing results
        """
        batch.status = SyncStatus.SYNCING
        batch.started_at = datetime.utcnow()

        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        for action in batch.items:
            try:
                # Update action status
                action.sync_status = SyncStatus.SYNCING
                self.storage.save_action(action)

                # Get handler for action type
                handler = self.handlers.get(action.action_type)

                if not handler:
                    logger.warning(
                        f"No handler for action type: {action.action_type.value}"
                    )
                    results["skipped"] += 1
                    continue

                # Process action
                if asyncio.iscoroutinefunction(handler):
                    success = await handler(action, online)
                else:
                    success = handler(action, online)

                if success:
                    action.sync_status = SyncStatus.SYNCED
                    results["succeeded"] += 1
                else:
                    self._handle_failure(action)
                    results["failed"] += 1

                # Save updated action
                self.storage.save_action(action)
                results["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing action {action.id}: {e}")
                results["errors"].append({
                    "action_id": action.id,
                    "error": str(e)
                })
                self._handle_failure(action)
                results["failed"] += 1

        batch.status = SyncStatus.SYNCED if results["failed"] == 0 else SyncStatus.FAILED
        batch.completed_at = datetime.utcnow()

        return results

    def _handle_failure(self, action: OfflineAction):
        """Handle failed action with retry logic"""
        action.retry_count += 1

        if action.retry_count >= action.max_retries:
            action.sync_status = SyncStatus.FAILED
            action.error_message = f"Max retries ({action.max_retries}) exceeded"
            logger.error(
                f"Action {action.id} failed after {action.max_retries} attempts"
            )
        else:
            # Schedule retry with exponential backoff
            delay_seconds = self.base_retry_delay * (2 ** (action.retry_count - 1))
            action.scheduled_sync_time = datetime.utcnow() + timedelta(
                seconds=delay_seconds
            )
            action.sync_status = SyncStatus.PENDING

            logger.info(
                f"Scheduled retry for action {action.id} in {delay_seconds}s "
                f"(attempt {action.retry_count}/{action.max_retries})"
            )

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.storage.get_connection() as conn:
            cursor = conn.cursor()

            # Total by status
            cursor.execute("""
                SELECT sync_status, COUNT(*) as count
                FROM offline_actions
                GROUP BY sync_status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Total by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count
                FROM offline_actions
                WHERE sync_status = ?
                GROUP BY priority
            """, (SyncStatus.PENDING.value,))
            priority_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Total by action type
            cursor.execute("""
                SELECT action_type, COUNT(*) as count
                FROM offline_actions
                WHERE sync_status = ?
                GROUP BY action_type
            """, (SyncStatus.PENDING.value,))
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Failed actions
            cursor.execute("""
                SELECT COUNT(*) FROM offline_actions
                WHERE sync_status = ?
            """, (SyncStatus.FAILED.value,))
            failed_count = cursor.fetchone()[0]

        return {
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "type_breakdown": type_counts,
            "total_pending": status_counts.get(SyncStatus.PENDING.value, 0),
            "total_failed": failed_count,
            "next_scheduled": self._get_next_scheduled_time()
        }

    def _get_next_scheduled_time(self) -> Optional[datetime]:
        """Get next scheduled retry time"""
        with self.storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MIN(scheduled_sync_time)
                FROM offline_actions
                WHERE sync_status = ? AND scheduled_sync_time IS NOT NULL
            """, (SyncStatus.PENDING.value,))

            result = cursor.fetchone()[0]
            if result:
                return datetime.fromisoformat(result)

        return None

    def clear_failed_actions(self) -> int:
        """Remove all failed actions from queue"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM offline_actions
                    WHERE sync_status = ?
                """, (SyncStatus.FAILED.value,))
                deleted = cursor.rowcount

            logger.info(f"Cleared {deleted} failed actions")
            return deleted

        except Exception as e:
            logger.error(f"Error clearing failed actions: {e}")
            return 0

    def retry_failed_actions(self) -> int:
        """Reset failed actions to pending for retry"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE offline_actions
                    SET sync_status = ?,
                        retry_count = 0,
                        error_message = NULL
                    WHERE sync_status = ?
                """, (SyncStatus.PENDING.value, SyncStatus.FAILED.value))
                updated = cursor.rowcount

            logger.info(f"Reset {updated} failed actions for retry")
            return updated

        except Exception as e:
            logger.error(f"Error retrying failed actions: {e}")
            return 0


class QueryQueue:
    """
    Specialized queue for offline queries

    Features:
    - Query deduplication
    - Local query answering when possible
    - Query caching
    """

    def __init__(self, storage: OfflineStorage):
        self.storage = storage
        self.query_cache: Dict[str, Any] = {}

    def enqueue_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OfflineQuery:
        """Enqueue a query for processing"""
        # Check cache first
        cache_key = self._get_cache_key(query_text)
        if cache_key in self.query_cache:
            logger.info(f"Query cache hit: {query_text[:50]}...")
            cached_result = self.query_cache[cache_key]

            query = OfflineQuery(
                query_text=query_text,
                priority=priority,
                sync_status=SyncStatus.SYNCED,
                result=cached_result,
                user_id=user_id,
                metadata=metadata or {}
            )
            self.storage.save_query(query)
            return query

        # Create new query
        query = OfflineQuery(
            query_text=query_text,
            action_type=ActionType.QUERY,
            priority=priority,
            sync_status=SyncStatus.PENDING,
            user_id=user_id,
            metadata=metadata or {}
        )

        self.storage.save_query(query)
        logger.info(f"Enqueued query: {query_text[:50]}...")

        return query

    def _get_cache_key(self, query_text: str) -> str:
        """Generate cache key for query"""
        # Normalize query text
        normalized = query_text.lower().strip()
        # Use hash for key
        import hashlib
        return hashlib.md5(normalized.encode()).hexdigest()

    def get_pending_queries(
        self,
        limit: Optional[int] = None
    ) -> List[OfflineQuery]:
        """Get pending queries"""
        return self.storage.get_pending_queries(limit=limit)

    def update_query_result(
        self,
        query_id: str,
        result: Dict[str, Any],
        cache: bool = True
    ) -> bool:
        """Update query with result"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()

                # Get the query
                cursor.execute(
                    "SELECT * FROM offline_queries WHERE id = ?",
                    (query_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return False

                # Update query
                cursor.execute("""
                    UPDATE offline_queries
                    SET result = ?,
                        sync_status = ?,
                        error = NULL
                    WHERE id = ?
                """, (
                    self.storage._serialize(result),
                    SyncStatus.SYNCED.value,
                    query_id
                ))

                # Cache result if requested
                if cache:
                    cache_key = self._get_cache_key(row['query_text'])
                    self.query_cache[cache_key] = result

            return True

        except Exception as e:
            logger.error(f"Error updating query result: {e}")
            return False

    def get_query_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[OfflineQuery]:
        """Get query history"""
        with self.storage.get_connection() as conn:
            cursor = conn.cursor()

            if user_id:
                cursor.execute("""
                    SELECT * FROM offline_queries
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM offline_queries
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            return [self.storage._row_to_query(row) for row in rows]
