"""
Offline-First Architecture Module for Dora Medical Knowledge Platform

This module provides comprehensive offline support for rural India use cases.

Features:
- Local SQLite storage with encryption
- Intelligent caching strategies
- Priority-based action queue
- Data synchronization with conflict resolution
- Network state monitoring
- Storage quota management

Usage:
    from src.offline import OfflineStorage, CacheManager, SyncEngine

    # Initialize storage
    storage = OfflineStorage()

    # Setup cache manager
    cache = CacheManager(storage, user_specialty="cardiology")

    # Cache a document
    success, error = cache.cache_document(document)

    # Setup sync
    sync_engine = SyncEngine(storage, action_queue)
    await sync_engine.start_background_sync()
"""

from .models import (
    # Enums
    SyncStatus,
    ActionType,
    Priority,
    ConflictResolution,

    # Data Models
    OfflineQuery,
    CachedDocument,
    OfflineAction,
    SyncMetadata,
    ContentPack,
    DrugDatabase,
    OfflineCalculator,
    NetworkStatus,
    SyncStats,
    StorageQuota,
    ConflictRecord,
    SyncBatch,
)

from .storage import (
    OfflineStorage,
    EncryptionManager,
)

from .cache import (
    CacheManager,
    CacheStrategy,
    LRUStrategy,
    SpecialtyPriorityStrategy,
    ContentPackManager,
)

from .queue import (
    ActionQueue,
    QueryQueue,
)

from .sync import (
    SyncEngine,
    NetworkMonitor,
)

from .conflict import (
    ConflictResolver,
)

__all__ = [
    # Enums
    "SyncStatus",
    "ActionType",
    "Priority",
    "ConflictResolution",

    # Models
    "OfflineQuery",
    "CachedDocument",
    "OfflineAction",
    "SyncMetadata",
    "ContentPack",
    "DrugDatabase",
    "OfflineCalculator",
    "NetworkStatus",
    "SyncStats",
    "StorageQuota",
    "ConflictRecord",
    "SyncBatch",

    # Storage
    "OfflineStorage",
    "EncryptionManager",

    # Cache
    "CacheManager",
    "CacheStrategy",
    "LRUStrategy",
    "SpecialtyPriorityStrategy",
    "ContentPackManager",

    # Queue
    "ActionQueue",
    "QueryQueue",

    # Sync
    "SyncEngine",
    "NetworkMonitor",

    # Conflict
    "ConflictResolver",
]

__version__ = "1.0.0"
