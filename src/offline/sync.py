"""
Data Synchronization Logic for Offline-First Architecture

This module handles bidirectional sync between local and server:
- Priority-based sync (critical data first)
- Delta sync (only changes)
- Background sync when online
- Network state detection
- Bandwidth-aware sync
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
import hashlib
import json

from .models import (
    SyncStatus, Priority, SyncStats, NetworkStatus,
    OfflineAction, SyncMetadata, ConflictRecord,
    ConflictResolution
)
from .storage import OfflineStorage
from .queue import ActionQueue
from .conflict import ConflictResolver

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Monitors network connectivity and bandwidth"""

    def __init__(self):
        self.status = NetworkStatus(
            is_online=False,
            sync_enabled=True
        )
        self._callbacks: List[Callable] = []

    def register_callback(self, callback: Callable):
        """Register callback for network state changes"""
        self._callbacks.append(callback)

    async def check_connectivity(self) -> bool:
        """Check if online"""
        try:
            # Try to reach a reliable endpoint
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.google.com',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_online = response.status == 200

                    old_status = self.status.is_online
                    self.status.is_online = is_online

                    if old_status != is_online:
                        self.status.last_online = datetime.utcnow()
                        await self._notify_callbacks()

                    return is_online

        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            self.status.is_online = False
            return False

    async def estimate_bandwidth(self) -> Optional[float]:
        """Estimate connection bandwidth in Mbps"""
        # Simple bandwidth estimation
        # In production, use more sophisticated methods
        try:
            if not self.status.is_online:
                return None

            import time
            import aiohttp

            # Download small test file and measure time
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.google.com',
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    content = await response.read()
                    elapsed = time.time() - start

                    # Calculate bandwidth (very rough estimate)
                    bytes_downloaded = len(content)
                    mbps = (bytes_downloaded * 8) / (elapsed * 1_000_000)

                    self.status.bandwidth_estimate = mbps
                    return mbps

        except Exception as e:
            logger.debug(f"Bandwidth estimation failed: {e}")
            return None

    async def _notify_callbacks(self):
        """Notify registered callbacks of status change"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.status)
                else:
                    callback(self.status)
            except Exception as e:
                logger.error(f"Error in network callback: {e}")


class SyncEngine:
    """
    Main synchronization engine

    Features:
    - Priority-based sync (CRITICAL -> HIGH -> MEDIUM -> LOW)
    - Delta sync (only changes since last sync)
    - Conflict detection and resolution
    - Background sync
    - Bandwidth-aware sync
    """

    def __init__(
        self,
        storage: OfflineStorage,
        action_queue: ActionQueue,
        api_client: Optional[Any] = None
    ):
        self.storage = storage
        self.action_queue = action_queue
        self.api_client = api_client

        self.network_monitor = NetworkMonitor()
        self.conflict_resolver = ConflictResolver(storage)

        self.is_syncing = False
        self.last_sync_time: Optional[datetime] = None
        self.sync_stats = SyncStats()

        # Sync settings
        self.auto_sync_enabled = True
        self.auto_sync_interval_minutes = 15
        self.max_batch_size = 50
        self.low_bandwidth_threshold_mbps = 1.0

        # Background sync task
        self._sync_task: Optional[asyncio.Task] = None

    async def start_background_sync(self):
        """Start background sync loop"""
        if self._sync_task and not self._sync_task.done():
            logger.warning("Background sync already running")
            return

        self._sync_task = asyncio.create_task(self._background_sync_loop())
        logger.info("Background sync started")

    async def stop_background_sync(self):
        """Stop background sync loop"""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            logger.info("Background sync stopped")

    async def _background_sync_loop(self):
        """Background sync loop"""
        while True:
            try:
                # Check connectivity
                is_online = await self.network_monitor.check_connectivity()

                if is_online and self.auto_sync_enabled and not self.is_syncing:
                    # Perform sync
                    await self.sync()

                # Wait for next interval
                await asyncio.sleep(self.auto_sync_interval_minutes * 60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retry

    async def sync(
        self,
        priority_filter: Optional[Priority] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Perform synchronization

        Args:
            priority_filter: Only sync actions of this priority
            force: Force sync even if offline

        Returns:
            Sync results
        """
        if self.is_syncing and not force:
            return {"error": "Sync already in progress"}

        self.is_syncing = True
        sync_start = datetime.utcnow()

        results = {
            "started_at": sync_start.isoformat(),
            "push_results": None,
            "pull_results": None,
            "conflicts": [],
            "errors": []
        }

        try:
            # Check if online
            is_online = await self.network_monitor.check_connectivity()

            if not is_online and not force:
                results["error"] = "Offline - sync skipped"
                return results

            # Check bandwidth
            bandwidth = await self.network_monitor.estimate_bandwidth()
            use_delta_sync = (
                bandwidth and
                bandwidth < self.low_bandwidth_threshold_mbps
            )

            # Push local changes
            logger.info("Starting push phase...")
            push_results = await self._push_changes(
                priority_filter=priority_filter,
                delta_only=use_delta_sync
            )
            results["push_results"] = push_results

            # Pull server updates
            logger.info("Starting pull phase...")
            pull_results = await self._pull_updates(delta_only=use_delta_sync)
            results["pull_results"] = pull_results

            # Handle conflicts
            if pull_results.get("conflicts"):
                logger.info(f"Resolving {len(pull_results['conflicts'])} conflicts...")
                for conflict_data in pull_results["conflicts"]:
                    conflict = await self.conflict_resolver.resolve_conflict(
                        conflict_data
                    )
                    results["conflicts"].append(conflict.dict())

            # Update sync stats
            self.sync_stats.last_successful_sync = datetime.utcnow()
            self.sync_stats.total_pending = results["push_results"].get("remaining", 0)
            self.sync_stats.sync_duration_seconds = (
                datetime.utcnow() - sync_start
            ).total_seconds()

            self.last_sync_time = datetime.utcnow()

        except Exception as e:
            logger.error(f"Sync error: {e}")
            results["errors"].append(str(e))

        finally:
            self.is_syncing = False

        results["completed_at"] = datetime.utcnow().isoformat()
        results["duration_seconds"] = (
            datetime.utcnow() - sync_start
        ).total_seconds()

        logger.info(f"Sync completed in {results['duration_seconds']:.2f}s")
        return results

    async def _push_changes(
        self,
        priority_filter: Optional[Priority] = None,
        delta_only: bool = False
    ) -> Dict[str, Any]:
        """Push local changes to server"""
        results = {
            "total_pushed": 0,
            "succeeded": 0,
            "failed": 0,
            "remaining": 0,
            "data_uploaded_mb": 0.0
        }

        # Process by priority order
        priority_order = [
            Priority.CRITICAL,
            Priority.HIGH,
            Priority.MEDIUM,
            Priority.LOW
        ]

        for priority in priority_order:
            if priority_filter and priority != priority_filter:
                continue

            # Get batch of pending actions
            batch = self.action_queue.get_next_batch(
                batch_size=self.max_batch_size,
                priority_filter=priority
            )

            if not batch:
                continue

            # Process batch
            batch_results = await self.action_queue.process_batch(
                batch,
                online=True
            )

            results["total_pushed"] += batch_results["processed"]
            results["succeeded"] += batch_results["succeeded"]
            results["failed"] += batch_results["failed"]

            # If low priority and low bandwidth, stop here
            if delta_only and priority == Priority.LOW:
                break

        # Get remaining pending count
        queue_stats = self.action_queue.get_queue_stats()
        results["remaining"] = queue_stats["total_pending"]

        self.sync_stats.total_synced += results["succeeded"]
        self.sync_stats.total_failed += results["failed"]

        return results

    async def _pull_updates(
        self,
        delta_only: bool = False
    ) -> Dict[str, Any]:
        """Pull updates from server"""
        results = {
            "total_pulled": 0,
            "documents_updated": 0,
            "conflicts": [],
            "data_downloaded_mb": 0.0
        }

        if not self.api_client:
            logger.warning("No API client configured, skipping pull")
            return results

        try:
            # Get last sync timestamp for delta sync
            since = None
            if delta_only and self.last_sync_time:
                since = self.last_sync_time.isoformat()

            # Call server API to get updates
            # This is a placeholder - implement actual API call
            updates = await self._fetch_server_updates(since=since)

            for update in updates:
                # Check for conflicts
                conflict = await self._check_conflict(update)

                if conflict:
                    results["conflicts"].append(conflict)
                else:
                    # Apply update
                    await self._apply_update(update)
                    results["total_pulled"] += 1

        except Exception as e:
            logger.error(f"Error pulling updates: {e}")
            raise

        return results

    async def _fetch_server_updates(
        self,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch updates from server"""
        # Placeholder - implement actual API call
        # This would call something like:
        # return await self.api_client.get_updates(since=since)
        return []

    async def _check_conflict(
        self,
        server_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if server update conflicts with local data"""
        entity_id = server_data.get("id")
        entity_type = server_data.get("type")

        # Get sync metadata
        with self.storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sync_metadata WHERE entity_id = ?",
                (entity_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None  # No local version

            # Check versions
            local_version = row["local_version"]
            server_version = server_data.get("version", 0)

            # Check checksums
            server_checksum = server_data.get("checksum")
            local_checksum = row["local_checksum"]

            if server_version > local_version:
                # Check if local has been modified
                if local_checksum != row["server_checksum"]:
                    # Conflict detected
                    return {
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "local_version": local_version,
                        "server_version": server_version,
                        "server_data": server_data
                    }

        return None

    async def _apply_update(self, update: Dict[str, Any]):
        """Apply server update to local storage"""
        # Placeholder - implement based on entity type
        entity_type = update.get("type")

        if entity_type == "document":
            # Update cached document
            pass
        elif entity_type == "query":
            # Update query result
            pass

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        queue_stats = self.action_queue.get_queue_stats()

        return {
            "is_syncing": self.is_syncing,
            "is_online": self.network_monitor.status.is_online,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "auto_sync_enabled": self.auto_sync_enabled,
            "queue_stats": queue_stats,
            "sync_stats": self.sync_stats.dict(),
            "network_status": self.network_monitor.status.dict()
        }

    def calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)

        return hashlib.sha256(content.encode()).hexdigest()

    async def force_full_sync(self) -> Dict[str, Any]:
        """Force a full sync (not delta)"""
        self.last_sync_time = None
        return await self.sync(force=True)
