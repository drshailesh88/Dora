"""
Desktop Offline Manager for Dora

Manages offline mode for the Flet desktop application.
Coordinates local storage, caching, and sync operations.

Features:
- Offline mode detection and switching
- Local RAG integration
- Cache management
- Sync coordination
- UI state management
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import asyncio

from ..offline import (
    OfflineStorage, CacheManager, ActionQueue,
    SyncEngine, NetworkMonitor, Priority
)

logger = logging.getLogger(__name__)


class OfflineManager:
    """
    Main offline manager for desktop application

    Coordinates all offline functionality:
    - Network monitoring
    - Cache management
    - Data synchronization
    - Local RAG queries
    - UI notifications
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        specialty: Optional[str] = None
    ):
        self.user_id = user_id
        self.specialty = specialty

        # Initialize components
        self.storage = OfflineStorage()
        self.cache_manager = CacheManager(
            self.storage,
            user_specialty=specialty
        )
        self.action_queue = ActionQueue(self.storage)
        self.sync_engine = SyncEngine(
            self.storage,
            self.action_queue
        )

        # Network monitor
        self.network_monitor = self.sync_engine.network_monitor

        # Local RAG (initialized separately)
        self.local_rag = None

        # UI callbacks
        self._status_callbacks: list[Callable] = []
        self._offline_mode = False

        # Initialize
        self._initialized = False

    async def initialize(self):
        """Initialize offline manager"""
        if self._initialized:
            return

        # Register network callback
        self.network_monitor.register_callback(self._on_network_change)

        # Start background sync
        await self.sync_engine.start_background_sync()

        # Initialize local RAG if available
        try:
            from .local_rag import LocalRAG
            self.local_rag = LocalRAG(self.storage)
            await self.local_rag.initialize()
            logger.info("Local RAG initialized")
        except Exception as e:
            logger.warning(f"Could not initialize local RAG: {e}")

        self._initialized = True
        logger.info("Offline manager initialized")

    async def _on_network_change(self, status):
        """Handle network status changes"""
        was_offline = self._offline_mode
        is_offline = not status.is_online

        if was_offline != is_offline:
            self._offline_mode = is_offline

            if is_offline:
                logger.info("Switched to offline mode")
                await self._notify_status_change({
                    'mode': 'offline',
                    'message': 'You are offline. Limited features available.',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logger.info("Switched to online mode")
                await self._notify_status_change({
                    'mode': 'online',
                    'message': 'Back online. Syncing data...',
                    'timestamp': datetime.utcnow().isoformat()
                })

                # Trigger sync when coming online
                asyncio.create_task(self.sync_engine.sync())

    def register_status_callback(self, callback: Callable):
        """Register callback for status changes"""
        self._status_callbacks.append(callback)

    async def _notify_status_change(self, status: Dict[str, Any]):
        """Notify all registered callbacks"""
        for callback in self._status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(status)
                else:
                    callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")

    # ===== QUERY OPERATIONS =====

    async def handle_query(
        self,
        query_text: str,
        priority: Priority = Priority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Handle user query (online or offline)

        Args:
            query_text: User's question
            priority: Query priority

        Returns:
            Query result dictionary
        """
        is_online = self.network_monitor.status.is_online

        if is_online:
            # Online: Use cloud RAG
            return await self._handle_online_query(query_text, priority)
        else:
            # Offline: Use local RAG
            return await self._handle_offline_query(query_text)

    async def _handle_online_query(
        self,
        query_text: str,
        priority: Priority
    ) -> Dict[str, Any]:
        """Handle query when online"""
        # This would call the cloud RAG API
        # Placeholder implementation

        return {
            'query': query_text,
            'answer': 'Online query result',
            'sources': [],
            'mode': 'online',
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _handle_offline_query(
        self,
        query_text: str
    ) -> Dict[str, Any]:
        """Handle query when offline using local RAG"""
        if not self.local_rag:
            return {
                'query': query_text,
                'error': 'Local RAG not available. Cannot process offline queries.',
                'mode': 'offline',
                'timestamp': datetime.utcnow().isoformat()
            }

        try:
            result = await self.local_rag.query(query_text)
            return {
                'query': query_text,
                'answer': result.get('answer'),
                'sources': result.get('sources', []),
                'confidence': result.get('confidence'),
                'mode': 'offline',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Offline query error: {e}")
            return {
                'query': query_text,
                'error': str(e),
                'mode': 'offline',
                'timestamp': datetime.utcnow().isoformat()
            }

    # ===== CACHE OPERATIONS =====

    async def cache_document(
        self,
        document: Dict[str, Any],
        pin: bool = False
    ) -> bool:
        """Cache document for offline access"""
        from ..offline.models import CachedDocument

        try:
            doc = CachedDocument(**document)
            doc.is_pinned = pin

            success, error = self.cache_manager.cache_document(doc)

            if success:
                logger.info(f"Cached document: {doc.doc_id}")
            else:
                logger.error(f"Failed to cache document: {error}")

            return success

        except Exception as e:
            logger.error(f"Error caching document: {e}")
            return False

    async def get_cached_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached document"""
        doc = self.cache_manager.get_cached_document(doc_id)

        if doc:
            return doc.dict()

        return None

    async def search_cached_documents(
        self,
        query: str = None,
        specialty: str = None,
        category: str = None
    ) -> list[Dict[str, Any]]:
        """Search cached documents"""
        docs = self.storage.search_documents(
            query=query,
            specialty=specialty,
            category=category
        )

        return [doc.dict() for doc in docs]

    # ===== SYNC OPERATIONS =====

    async def sync_now(self, force: bool = False) -> Dict[str, Any]:
        """Trigger immediate sync"""
        return await self.sync_engine.sync(force=force)

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return self.sync_engine.get_sync_status()

    # ===== STORAGE OPERATIONS =====

    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get storage quota information"""
        quota = self.storage.get_storage_quota()
        return quota.dict()

    async def optimize_storage(self) -> Dict[str, Any]:
        """Optimize storage (cleanup old cache, vacuum DB)"""
        results = self.cache_manager.optimize_cache()

        # Vacuum database
        self.storage.vacuum_database()

        return results

    # ===== OFFLINE CAPABILITIES =====

    def get_offline_capabilities(self) -> Dict[str, bool]:
        """Get available offline capabilities"""
        has_local_rag = self.local_rag is not None

        return {
            'drug_interactions': True,  # Always available
            'calculators': True,  # Always available
            'cached_documents': True,  # If documents cached
            'recent_queries': True,  # From local storage
            'local_rag': has_local_rag,
            'real_time_search': False,  # Requires online
            'cloud_sync': self.network_monitor.status.is_online,
        }

    def get_status_message(self) -> str:
        """Get user-friendly status message"""
        is_online = self.network_monitor.status.is_online

        if not is_online:
            capabilities = self.get_offline_capabilities()
            if capabilities['local_rag']:
                return "Offline mode - Local AI available"
            else:
                return "Offline mode - Limited features available"

        quality = self.network_monitor.status.quality

        if quality:
            quality_messages = {
                'excellent': 'Online - Excellent connection',
                'good': 'Online - Good connection',
                'fair': 'Online - Fair connection',
                'poor': 'Online - Poor connection'
            }
            return quality_messages.get(quality.value, 'Online')

        return 'Online'

    # ===== UTILITY METHODS =====

    async def download_content_pack(
        self,
        pack_id: str,
        on_progress: Optional[Callable[[float], None]] = None
    ) -> bool:
        """Download content pack for offline use"""
        # This would download and install a content pack
        # Placeholder implementation

        logger.info(f"Downloading content pack: {pack_id}")

        # Simulate progress
        for progress in range(0, 101, 10):
            if on_progress:
                on_progress(progress)
            await asyncio.sleep(0.5)

        return True

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        sync_status = await self.get_sync_status()
        storage_quota = await self.get_storage_quota()
        cache_stats = self.cache_manager.get_cache_stats()

        return {
            'sync': sync_status,
            'storage': storage_quota,
            'cache': cache_stats,
            'offline_mode': self._offline_mode,
            'capabilities': self.get_offline_capabilities()
        }

    async def shutdown(self):
        """Shutdown offline manager"""
        # Stop background sync
        await self.sync_engine.stop_background_sync()

        # Cleanup
        if self.local_rag:
            await self.local_rag.cleanup()

        logger.info("Offline manager shutdown complete")
