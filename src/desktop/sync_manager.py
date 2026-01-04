"""
Desktop Sync Manager

Coordinates synchronization for the desktop application.
Provides UI-friendly sync operations and status reporting.

Features:
- Manual and automatic sync
- Progress tracking
- Conflict resolution UI support
- Sync scheduling
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import asyncio

from ..offline import (
    SyncEngine, OfflineStorage, ActionQueue,
    Priority, SyncStatus, ConflictResolver
)

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Desktop synchronization manager

    Provides high-level sync operations optimized for desktop UI.
    """

    def __init__(
        self,
        storage: OfflineStorage,
        action_queue: ActionQueue,
        sync_engine: SyncEngine
    ):
        self.storage = storage
        self.action_queue = action_queue
        self.sync_engine = sync_engine
        self.conflict_resolver = ConflictResolver(storage)

        # Sync state
        self._sync_in_progress = False
        self._last_sync_result: Optional[Dict[str, Any]] = None

        # Progress callbacks
        self._progress_callbacks: list[Callable] = []

        # Scheduled sync
        self._scheduled_sync_task: Optional[asyncio.Task] = None

    # ===== SYNC OPERATIONS =====

    async def sync(
        self,
        priority_filter: Optional[Priority] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Perform synchronization with progress reporting

        Args:
            priority_filter: Only sync specific priority
            show_progress: Report progress to callbacks

        Returns:
            Sync results
        """
        if self._sync_in_progress:
            return {
                'success': False,
                'error': 'Sync already in progress'
            }

        self._sync_in_progress = True

        try:
            # Report start
            if show_progress:
                await self._report_progress({
                    'stage': 'started',
                    'progress': 0,
                    'message': 'Starting synchronization...'
                })

            # Check network
            is_online = await self.sync_engine.network_monitor.check_connectivity()

            if not is_online:
                return {
                    'success': False,
                    'error': 'No internet connection',
                    'offline': True
                }

            # Push phase
            if show_progress:
                await self._report_progress({
                    'stage': 'push',
                    'progress': 25,
                    'message': 'Uploading local changes...'
                })

            # Perform sync
            results = await self.sync_engine.sync(priority_filter=priority_filter)

            # Pull phase
            if show_progress:
                await self._report_progress({
                    'stage': 'pull',
                    'progress': 75,
                    'message': 'Downloading updates...'
                })

            # Complete
            if show_progress:
                await self._report_progress({
                    'stage': 'completed',
                    'progress': 100,
                    'message': 'Sync completed successfully'
                })

            self._last_sync_result = results
            return {
                'success': True,
                'results': results
            }

        except Exception as e:
            logger.error(f"Sync error: {e}")

            if show_progress:
                await self._report_progress({
                    'stage': 'error',
                    'progress': 0,
                    'message': f'Sync failed: {str(e)}'
                })

            return {
                'success': False,
                'error': str(e)
            }

        finally:
            self._sync_in_progress = False

    async def quick_sync(self) -> Dict[str, Any]:
        """Quick sync - only critical and high priority items"""
        return await self.sync(priority_filter=Priority.CRITICAL)

    async def force_full_sync(self) -> Dict[str, Any]:
        """Force complete synchronization"""
        return await self.sync_engine.force_full_sync()

    # ===== PROGRESS REPORTING =====

    def register_progress_callback(self, callback: Callable):
        """Register callback for progress updates"""
        self._progress_callbacks.append(callback)

    async def _report_progress(self, progress: Dict[str, Any]):
        """Report progress to all callbacks"""
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    # ===== SCHEDULED SYNC =====

    async def schedule_sync(
        self,
        interval_minutes: int = 15,
        auto_start: bool = True
    ):
        """
        Schedule automatic sync

        Args:
            interval_minutes: Sync interval
            auto_start: Start immediately
        """
        # Cancel existing task
        if self._scheduled_sync_task:
            self._scheduled_sync_task.cancel()

        # Create new task
        self._scheduled_sync_task = asyncio.create_task(
            self._scheduled_sync_loop(interval_minutes)
        )

        logger.info(f"Scheduled sync every {interval_minutes} minutes")

    async def _scheduled_sync_loop(self, interval_minutes: int):
        """Background sync loop"""
        while True:
            try:
                # Wait for interval
                await asyncio.sleep(interval_minutes * 60)

                # Check if online
                is_online = await self.sync_engine.network_monitor.check_connectivity()

                if is_online and not self._sync_in_progress:
                    logger.info("Running scheduled sync")
                    await self.sync(show_progress=False)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduled sync error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    def cancel_scheduled_sync(self):
        """Cancel scheduled sync"""
        if self._scheduled_sync_task:
            self._scheduled_sync_task.cancel()
            logger.info("Scheduled sync cancelled")

    # ===== CONFLICT MANAGEMENT =====

    async def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get all pending conflicts"""
        conflicts = self.conflict_resolver.get_pending_conflicts()
        return [c.dict() for c in conflicts]

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,  # 'local', 'server', 'custom'
        custom_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Resolve conflict with user choice"""
        return await self.conflict_resolver.resolve_manual_conflict(
            conflict_id=conflict_id,
            chosen_version=resolution,
            custom_data=custom_data
        )

    async def auto_resolve_conflicts(self) -> int:
        """Auto-resolve conflicts using default strategy"""
        conflicts = self.conflict_resolver.get_pending_conflicts()

        resolved = 0
        for conflict in conflicts:
            try:
                await self.conflict_resolver.resolve_conflict(
                    {'entity_id': conflict.entity_id, 'entity_type': conflict.entity_type}
                )
                resolved += 1
            except Exception as e:
                logger.error(f"Error auto-resolving conflict: {e}")

        return resolved

    # ===== STATUS AND STATS =====

    async def get_status(self) -> Dict[str, Any]:
        """Get detailed sync status"""
        status = self.sync_engine.get_sync_status()

        # Add conflict info
        conflicts = await self.get_conflicts()

        # Add last result
        last_result = self._last_sync_result

        return {
            **status,
            'conflicts': conflicts,
            'conflicts_count': len(conflicts),
            'last_result': last_result,
            'sync_in_progress': self._sync_in_progress
        }

    async def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        stats = self.action_queue.get_queue_stats()

        return {
            'pending': stats['total_pending'],
            'failed': stats['total_failed'],
            'by_priority': stats['priority_breakdown'],
            'by_type': stats['type_breakdown'],
            'next_scheduled': stats['next_scheduled']
        }

    # ===== UTILITY METHODS =====

    async def retry_failed(self) -> int:
        """Retry all failed actions"""
        return self.action_queue.retry_failed_actions()

    async def clear_failed(self) -> int:
        """Clear all failed actions"""
        return self.action_queue.clear_failed_actions()

    async def estimate_sync_time(self) -> Dict[str, Any]:
        """Estimate time required for next sync"""
        stats = self.action_queue.get_queue_stats()
        pending = stats['total_pending']

        # Rough estimate: 100 items per minute
        estimated_minutes = max(1, pending // 100)

        # Check bandwidth
        bandwidth = self.sync_engine.network_monitor.status.bandwidth_estimate

        if bandwidth and bandwidth < 1:
            # Slow connection, multiply time
            estimated_minutes *= 2

        return {
            'pending_items': pending,
            'estimated_minutes': estimated_minutes,
            'estimated_human': self._format_duration(estimated_minutes)
        }

    def _format_duration(self, minutes: int) -> str:
        """Format duration in human-readable form"""
        if minutes < 1:
            return 'Less than a minute'
        elif minutes == 1:
            return '1 minute'
        elif minutes < 60:
            return f'{minutes} minutes'
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f'{hours} hour{"s" if hours > 1 else ""}'
            else:
                return f'{hours}h {mins}m'

    # ===== ADVANCED FEATURES =====

    async def sync_with_verification(self) -> Dict[str, Any]:
        """
        Sync with post-sync verification

        Verifies that all pending items were synced successfully.
        """
        # Get pending count before
        before_stats = self.action_queue.get_queue_stats()
        before_pending = before_stats['total_pending']

        # Perform sync
        result = await self.sync()

        # Verify after
        after_stats = self.action_queue.get_queue_stats()
        after_pending = after_stats['total_pending']

        synced_count = before_pending - after_pending

        return {
            **result,
            'verification': {
                'before_pending': before_pending,
                'after_pending': after_pending,
                'synced_count': synced_count,
                'verified': synced_count == before_pending
            }
        }

    async def selective_sync(
        self,
        entity_types: list[str],
        priority: Optional[Priority] = None
    ) -> Dict[str, Any]:
        """
        Selective sync - only specific entity types

        Args:
            entity_types: List of entity types to sync
            priority: Optional priority filter
        """
        # This would filter actions by entity type before syncing
        # Placeholder implementation

        logger.info(f"Selective sync: {entity_types}")
        return await self.sync(priority_filter=priority)
