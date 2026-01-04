"""
Local Storage Implementation for Offline-First Architecture

This module handles SQLite database operations for offline data persistence.
Includes encryption for sensitive medical data and efficient indexing.
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Type, TypeVar
from contextlib import contextmanager
import logging
from cryptography.fernet import Fernet
import os

from .models import (
    OfflineQuery, CachedDocument, OfflineAction, SyncMetadata,
    ContentPack, DrugDatabase, ConflictRecord, SyncBatch,
    SyncStatus, ActionType, Priority, StorageQuota
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EncryptionManager:
    """Handles encryption/decryption of sensitive data"""

    def __init__(self, key_path: Optional[str] = None):
        self.key_path = key_path or os.path.join(
            Path.home(), ".dora", "encryption.key"
        )
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        """Load existing key or create new one"""
        key_file = Path(self.key_path)
        key_file.parent.mkdir(parents=True, exist_ok=True)

        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            # Secure file permissions (owner only)
            key_file.chmod(0o600)
            return key

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class OfflineStorage:
    """
    Local SQLite storage manager for offline-first architecture

    Features:
    - Encrypted storage for sensitive medical data
    - Efficient indexing for fast queries
    - Transaction support
    - Connection pooling
    - Storage quota management
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        encrypt_sensitive: bool = True
    ):
        self.db_path = db_path or os.path.join(
            Path.home(), ".dora", "offline.db"
        )
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.encrypt_sensitive = encrypt_sensitive
        self.encryption = EncryptionManager() if encrypt_sensitive else None

        self._initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Offline Queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_queries (
                    id TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    sync_status TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    user_id TEXT,
                    metadata TEXT
                )
            """)

            # Cached Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_documents (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    specialty TEXT,
                    category TEXT NOT NULL,
                    embedding BLOB,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0,
                    sync_status TEXT NOT NULL
                )
            """)

            # Offline Actions queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offline_actions (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sync_status TEXT NOT NULL,
                    scheduled_sync_time TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_message TEXT,
                    user_id TEXT
                )
            """)

            # Sync Metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    local_version INTEGER DEFAULT 1,
                    server_version INTEGER,
                    last_sync_time TEXT,
                    local_checksum TEXT,
                    server_checksum TEXT,
                    conflict_detected INTEGER DEFAULT 0,
                    conflict_resolution TEXT
                )
            """)

            # Content Packs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_packs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    specialty TEXT NOT NULL,
                    version TEXT NOT NULL,
                    size_mb REAL NOT NULL,
                    document_count INTEGER NOT NULL,
                    last_updated TEXT NOT NULL,
                    required INTEGER DEFAULT 0,
                    downloaded INTEGER DEFAULT 0,
                    download_progress REAL DEFAULT 0,
                    file_path TEXT,
                    checksum TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Drug Database table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_database (
                    drug_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    generic_name TEXT,
                    brand_names TEXT,
                    category TEXT NOT NULL,
                    interactions TEXT,
                    contraindications TEXT,
                    dosage_info TEXT,
                    side_effects TEXT,
                    pregnancy_category TEXT,
                    metadata TEXT,
                    last_updated TEXT NOT NULL
                )
            """)

            # Conflict Records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflict_records (
                    id TEXT PRIMARY KEY,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    local_data TEXT NOT NULL,
                    server_data TEXT NOT NULL,
                    conflict_detected_at TEXT NOT NULL,
                    resolution_strategy TEXT,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    resolved_data TEXT
                )
            """)

            # Sync Batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_batches (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    items TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_sync_status
                ON offline_queries(sync_status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queries_priority
                ON offline_queries(priority, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_specialty
                ON cached_documents(specialty)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_category
                ON cached_documents(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_pinned
                ON cached_documents(is_pinned)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_actions_sync_status
                ON offline_actions(sync_status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_actions_priority
                ON offline_actions(priority, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_drugs_name
                ON drug_database(name)
            """)

            conn.commit()

    def _serialize(self, obj: Any) -> str:
        """Serialize object to JSON"""
        if isinstance(obj, list):
            return json.dumps(obj)
        return json.dumps(obj) if obj else None

    def _deserialize(self, data: str, type_hint: Type[T] = None) -> Any:
        """Deserialize JSON to object"""
        if not data:
            return None
        return json.loads(data)

    def _encrypt_if_needed(self, data: str) -> str:
        """Encrypt data if encryption is enabled"""
        if self.encrypt_sensitive and self.encryption and data:
            return self.encryption.encrypt(data)
        return data

    def _decrypt_if_needed(self, data: str) -> str:
        """Decrypt data if encryption is enabled"""
        if self.encrypt_sensitive and self.encryption and data:
            try:
                return self.encryption.decrypt(data)
            except Exception as e:
                logger.error(f"Decryption error: {e}")
                return data
        return data

    # ===== OFFLINE QUERIES =====

    def save_query(self, query: OfflineQuery) -> bool:
        """Save an offline query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO offline_queries VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    query.id,
                    query.query_text,
                    query.timestamp.isoformat(),
                    query.action_type.value,
                    query.priority.value,
                    query.sync_status.value,
                    self._serialize(query.result),
                    query.error,
                    query.retry_count,
                    query.max_retries,
                    query.user_id,
                    self._serialize(query.metadata)
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving query: {e}")
            return False

    def get_pending_queries(
        self,
        limit: Optional[int] = None
    ) -> List[OfflineQuery]:
        """Get pending queries for sync"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM offline_queries
                WHERE sync_status = ?
                ORDER BY priority DESC, timestamp ASC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (SyncStatus.PENDING.value,))
            rows = cursor.fetchall()

            return [self._row_to_query(row) for row in rows]

    def _row_to_query(self, row: sqlite3.Row) -> OfflineQuery:
        """Convert database row to OfflineQuery"""
        return OfflineQuery(
            id=row['id'],
            query_text=row['query_text'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            action_type=ActionType(row['action_type']),
            priority=Priority(row['priority']),
            sync_status=SyncStatus(row['sync_status']),
            result=self._deserialize(row['result']),
            error=row['error'],
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            user_id=row['user_id'],
            metadata=self._deserialize(row['metadata']) or {}
        )

    # ===== CACHED DOCUMENTS =====

    def save_document(self, document: CachedDocument) -> bool:
        """Save a cached document"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Encrypt content if sensitive
                content = self._encrypt_if_needed(document.content)

                cursor.execute("""
                    INSERT OR REPLACE INTO cached_documents VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    document.id,
                    document.doc_id,
                    document.title,
                    content,
                    document.specialty,
                    document.category,
                    self._serialize(document.embedding) if document.embedding else None,
                    self._serialize(document.metadata),
                    document.created_at.isoformat(),
                    document.updated_at.isoformat(),
                    document.last_accessed.isoformat(),
                    document.access_count,
                    document.size_bytes,
                    1 if document.is_pinned else 0,
                    document.sync_status.value
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False

    def get_document(self, doc_id: str) -> Optional[CachedDocument]:
        """Get a cached document by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cached_documents WHERE doc_id = ?",
                (doc_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update access count and timestamp
                cursor.execute("""
                    UPDATE cached_documents
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE doc_id = ?
                """, (datetime.utcnow().isoformat(), doc_id))

                return self._row_to_document(row)
            return None

    def search_documents(
        self,
        query: str = None,
        specialty: str = None,
        category: str = None,
        pinned_only: bool = False,
        limit: int = 50
    ) -> List[CachedDocument]:
        """Search cached documents"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if query:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if specialty:
                conditions.append("specialty = ?")
                params.append(specialty)

            if category:
                conditions.append("category = ?")
                params.append(category)

            if pinned_only:
                conditions.append("is_pinned = 1")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query_sql = f"""
                SELECT * FROM cached_documents
                WHERE {where_clause}
                ORDER BY access_count DESC, last_accessed DESC
                LIMIT {limit}
            """

            cursor.execute(query_sql, params)
            rows = cursor.fetchall()

            return [self._row_to_document(row) for row in rows]

    def _row_to_document(self, row: sqlite3.Row) -> CachedDocument:
        """Convert database row to CachedDocument"""
        content = self._decrypt_if_needed(row['content'])

        return CachedDocument(
            id=row['id'],
            doc_id=row['doc_id'],
            title=row['title'],
            content=content,
            specialty=row['specialty'],
            category=row['category'],
            embedding=self._deserialize(row['embedding']),
            metadata=self._deserialize(row['metadata']) or {},
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            last_accessed=datetime.fromisoformat(row['last_accessed']),
            access_count=row['access_count'],
            size_bytes=row['size_bytes'],
            is_pinned=bool(row['is_pinned']),
            sync_status=SyncStatus(row['sync_status'])
        )

    # ===== OFFLINE ACTIONS =====

    def save_action(self, action: OfflineAction) -> bool:
        """Save an offline action to queue"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO offline_actions VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    action.id,
                    action.action_type.value,
                    action.priority.value,
                    self._serialize(action.payload),
                    action.timestamp.isoformat(),
                    action.sync_status.value,
                    action.scheduled_sync_time.isoformat() if action.scheduled_sync_time else None,
                    action.retry_count,
                    action.max_retries,
                    action.error_message,
                    action.user_id
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving action: {e}")
            return False

    def get_pending_actions(
        self,
        priority: Optional[Priority] = None,
        limit: Optional[int] = None
    ) -> List[OfflineAction]:
        """Get pending actions from queue"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM offline_actions
                WHERE sync_status = ?
            """
            params = [SyncStatus.PENDING.value]

            if priority:
                query += " AND priority = ?"
                params.append(priority.value)

            query += " ORDER BY priority DESC, timestamp ASC"

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_action(row) for row in rows]

    def _row_to_action(self, row: sqlite3.Row) -> OfflineAction:
        """Convert database row to OfflineAction"""
        return OfflineAction(
            id=row['id'],
            action_type=ActionType(row['action_type']),
            priority=Priority(row['priority']),
            payload=self._deserialize(row['payload']) or {},
            timestamp=datetime.fromisoformat(row['timestamp']),
            sync_status=SyncStatus(row['sync_status']),
            scheduled_sync_time=datetime.fromisoformat(row['scheduled_sync_time']) if row['scheduled_sync_time'] else None,
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            error_message=row['error_message'],
            user_id=row['user_id']
        )

    # ===== STORAGE MANAGEMENT =====

    def get_storage_quota(self) -> StorageQuota:
        """Get current storage quota information"""
        db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM cached_documents")
            doc_count = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(size_bytes) FROM cached_documents")
            cache_size = (cursor.fetchone()[0] or 0) / (1024 * 1024)

            cursor.execute("""
                SELECT SUM(size_mb) FROM content_packs WHERE downloaded = 1
            """)
            packs_size = cursor.fetchone()[0] or 0

        total_mb = 10240  # 10GB default quota
        used_mb = db_size + cache_size + packs_size

        return StorageQuota(
            total_mb=total_mb,
            used_mb=used_mb,
            available_mb=total_mb - used_mb,
            documents_count=doc_count,
            cache_size_mb=cache_size,
            database_size_mb=db_size,
            content_packs_mb=packs_size
        )

    def cleanup_old_cache(self, days: int = 30) -> int:
        """Remove documents not accessed in specified days"""
        cutoff_date = datetime.utcnow().replace(
            day=datetime.utcnow().day - days
        ).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM cached_documents
                WHERE last_accessed < ? AND is_pinned = 0
            """, (cutoff_date,))
            deleted = cursor.rowcount

        logger.info(f"Cleaned up {deleted} old cached documents")
        return deleted

    def vacuum_database(self):
        """Optimize database (reclaim space)"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed successfully")
