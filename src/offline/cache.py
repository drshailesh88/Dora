"""
Intelligent Caching Strategies for Offline-First Architecture

This module implements advanced caching strategies optimized for medical content:
- LRU (Least Recently Used) for general content
- Specialty-based caching (prioritize user's specialty)
- Pinned content (always keep)
- Smart prefetching based on usage patterns
- Compression for large documents
"""

import logging
import zlib
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
import json

from .models import CachedDocument, StorageQuota, Priority
from .storage import OfflineStorage

logger = logging.getLogger(__name__)


class CacheStrategy:
    """Base class for cache strategies"""

    def should_cache(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Determine if document should be cached"""
        raise NotImplementedError

    def should_evict(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Determine if document should be evicted"""
        raise NotImplementedError


class LRUStrategy(CacheStrategy):
    """Least Recently Used eviction strategy"""

    def should_cache(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Cache if space available or can evict LRU items"""
        if document.is_pinned:
            return True

        if not quota.is_critical:
            return True

        return False

    def should_evict(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Evict if not pinned and least recently used"""
        if document.is_pinned:
            return False

        if quota.is_critical:
            # Evict documents not accessed in last 7 days
            cutoff = datetime.utcnow() - timedelta(days=7)
            return document.last_accessed < cutoff

        if quota.is_warning:
            # Evict documents not accessed in last 14 days
            cutoff = datetime.utcnow() - timedelta(days=14)
            return document.last_accessed < cutoff

        return False


class SpecialtyPriorityStrategy(CacheStrategy):
    """Prioritize caching based on user's specialty"""

    def __init__(self, user_specialty: str):
        self.user_specialty = user_specialty

    def should_cache(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Prioritize specialty-relevant content"""
        if document.is_pinned:
            return True

        # Always cache user's specialty
        if document.specialty == self.user_specialty:
            return True

        # Cache others if space available
        return not quota.is_warning

    def should_evict(
        self,
        document: CachedDocument,
        quota: StorageQuota
    ) -> bool:
        """Don't evict specialty content unless critical"""
        if document.is_pinned:
            return False

        if document.specialty == self.user_specialty:
            return quota.is_critical and document.access_count < 2

        # Evict non-specialty content more aggressively
        if quota.is_warning:
            cutoff = datetime.utcnow() - timedelta(days=7)
            return document.last_accessed < cutoff

        return False


class CacheManager:
    """
    Intelligent cache manager for offline medical content

    Features:
    - Multiple caching strategies
    - Automatic compression
    - Smart prefetching
    - Usage pattern analysis
    - Storage quota management
    """

    def __init__(
        self,
        storage: OfflineStorage,
        user_specialty: Optional[str] = None,
        compression_threshold_kb: int = 100
    ):
        self.storage = storage
        self.compression_threshold = compression_threshold_kb * 1024
        self.user_specialty = user_specialty

        # Initialize strategies
        self.strategies = [
            LRUStrategy(),
        ]
        if user_specialty:
            self.strategies.append(SpecialtyPriorityStrategy(user_specialty))

        # Usage tracking
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.prefetch_candidates: List[str] = []

    def cache_document(
        self,
        document: CachedDocument,
        force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Cache a document with intelligent decision making

        Args:
            document: Document to cache
            force: Force caching regardless of quota

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check storage quota
            quota = self.storage.get_storage_quota()

            # Check if we should cache
            if not force:
                should_cache = any(
                    strategy.should_cache(document, quota)
                    for strategy in self.strategies
                )

                if not should_cache:
                    return False, "Cache strategies declined to cache document"

            # Compress if needed
            if document.size_bytes > self.compression_threshold:
                document = self._compress_document(document)

            # Free space if needed
            if quota.is_warning:
                self._evict_candidates(required_mb=document.size_bytes / (1024 * 1024))

            # Save to storage
            success = self.storage.save_document(document)

            if success:
                logger.info(f"Cached document: {document.doc_id}")
                return True, None
            else:
                return False, "Failed to save document to storage"

        except Exception as e:
            logger.error(f"Error caching document: {e}")
            return False, str(e)

    def get_cached_document(
        self,
        doc_id: str,
        decompress: bool = True
    ) -> Optional[CachedDocument]:
        """
        Retrieve cached document and update access patterns

        Args:
            doc_id: Document ID
            decompress: Whether to decompress if compressed

        Returns:
            CachedDocument or None
        """
        document = self.storage.get_document(doc_id)

        if document:
            # Track access pattern
            self.access_patterns[doc_id].append(datetime.utcnow())

            # Decompress if needed
            if decompress and document.metadata.get('compressed'):
                document = self._decompress_document(document)

            # Update prefetch candidates
            self._update_prefetch_candidates()

            return document

        return None

    def _compress_document(self, document: CachedDocument) -> CachedDocument:
        """Compress document content"""
        try:
            compressed = zlib.compress(document.content.encode())
            original_size = document.size_bytes
            compressed_size = len(compressed)

            # Only use compression if significant savings
            if compressed_size < original_size * 0.8:
                document.content = compressed.hex()
                document.size_bytes = compressed_size
                document.metadata['compressed'] = True
                document.metadata['original_size'] = original_size

                logger.info(
                    f"Compressed document {document.doc_id}: "
                    f"{original_size} -> {compressed_size} bytes "
                    f"({100 * (1 - compressed_size/original_size):.1f}% reduction)"
                )

        except Exception as e:
            logger.error(f"Compression error: {e}")

        return document

    def _decompress_document(self, document: CachedDocument) -> CachedDocument:
        """Decompress document content"""
        try:
            if document.metadata.get('compressed'):
                compressed_bytes = bytes.fromhex(document.content)
                decompressed = zlib.decompress(compressed_bytes)
                document.content = decompressed.decode()
                document.metadata['compressed'] = False

        except Exception as e:
            logger.error(f"Decompression error: {e}")

        return document

    def _evict_candidates(self, required_mb: float = 0) -> int:
        """
        Evict documents to free space

        Args:
            required_mb: Minimum MB to free

        Returns:
            Number of documents evicted
        """
        quota = self.storage.get_storage_quota()
        documents = self.storage.search_documents(limit=1000)

        evicted_count = 0
        freed_mb = 0.0

        # Sort by eviction priority
        candidates = []
        for doc in documents:
            should_evict = any(
                strategy.should_evict(doc, quota)
                for strategy in self.strategies
            )
            if should_evict:
                candidates.append(doc)

        # Sort by access count and last accessed
        candidates.sort(
            key=lambda d: (d.access_count, d.last_accessed)
        )

        # Evict until we free enough space or run out of candidates
        for doc in candidates:
            if required_mb > 0 and freed_mb >= required_mb:
                break

            # Delete from storage
            try:
                with self.storage.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM cached_documents WHERE doc_id = ?",
                        (doc.doc_id,)
                    )

                freed_mb += doc.size_bytes / (1024 * 1024)
                evicted_count += 1

            except Exception as e:
                logger.error(f"Error evicting document {doc.doc_id}: {e}")

        if evicted_count > 0:
            logger.info(
                f"Evicted {evicted_count} documents, "
                f"freed {freed_mb:.2f} MB"
            )

        return evicted_count

    def _update_prefetch_candidates(self):
        """Update list of documents to prefetch based on access patterns"""
        # Analyze access patterns to predict next documents
        # Simple heuristic: documents accessed together frequently

        # This is a placeholder for more sophisticated ML-based prediction
        # For now, just track frequently accessed documents

        frequent_docs = []
        for doc_id, accesses in self.access_patterns.items():
            # Accessed more than 3 times in last 7 days
            recent_accesses = [
                a for a in accesses
                if a > datetime.utcnow() - timedelta(days=7)
            ]
            if len(recent_accesses) >= 3:
                frequent_docs.append(doc_id)

        self.prefetch_candidates = frequent_docs[:20]  # Top 20

    def get_prefetch_candidates(self) -> List[str]:
        """Get list of document IDs recommended for prefetching"""
        return self.prefetch_candidates

    def pin_document(self, doc_id: str) -> bool:
        """Pin document to prevent eviction"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cached_documents SET is_pinned = 1 WHERE doc_id = ?",
                    (doc_id,)
                )
            return True
        except Exception as e:
            logger.error(f"Error pinning document: {e}")
            return False

    def unpin_document(self, doc_id: str) -> bool:
        """Unpin document"""
        try:
            with self.storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE cached_documents SET is_pinned = 0 WHERE doc_id = ?",
                    (doc_id,)
                )
            return True
        except Exception as e:
            logger.error(f"Error unpinning document: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        quota = self.storage.get_storage_quota()
        documents = self.storage.search_documents(limit=10000)

        specialty_breakdown = defaultdict(int)
        category_breakdown = defaultdict(int)
        pinned_count = 0

        for doc in documents:
            if doc.specialty:
                specialty_breakdown[doc.specialty] += 1
            category_breakdown[doc.category] += 1
            if doc.is_pinned:
                pinned_count += 1

        return {
            "total_documents": len(documents),
            "pinned_documents": pinned_count,
            "storage_quota": quota.dict(),
            "specialty_breakdown": dict(specialty_breakdown),
            "category_breakdown": dict(category_breakdown),
            "prefetch_candidates": len(self.prefetch_candidates),
            "compression_threshold_kb": self.compression_threshold / 1024
        }

    def optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize cache by:
        1. Removing old unused documents
        2. Compressing large documents
        3. Vacuuming database
        """
        results = {
            "old_docs_removed": 0,
            "docs_compressed": 0,
            "space_freed_mb": 0.0
        }

        # Remove old documents
        quota_before = self.storage.get_storage_quota()
        results["old_docs_removed"] = self.storage.cleanup_old_cache(days=30)

        # Compress large uncompressed documents
        documents = self.storage.search_documents(limit=10000)
        for doc in documents:
            if (doc.size_bytes > self.compression_threshold and
                    not doc.metadata.get('compressed')):
                compressed = self._compress_document(doc)
                self.storage.save_document(compressed)
                results["docs_compressed"] += 1

        # Vacuum database
        self.storage.vacuum_database()

        quota_after = self.storage.get_storage_quota()
        results["space_freed_mb"] = quota_before.used_mb - quota_after.used_mb

        logger.info(f"Cache optimization complete: {results}")
        return results


class ContentPackManager:
    """Manages downloadable content packs for offline use"""

    def __init__(self, storage: OfflineStorage):
        self.storage = storage

    def get_available_packs(self) -> List[Dict[str, Any]]:
        """Get list of available content packs"""
        # This would typically fetch from server
        # For now, return static list
        return [
            {
                "id": "cardiology-essentials",
                "name": "Cardiology Essentials",
                "specialty": "cardiology",
                "size_mb": 450,
                "description": "Core cardiology guidelines and references",
                "required": True
            },
            {
                "id": "emergency-medicine",
                "name": "Emergency Medicine Protocols",
                "specialty": "emergency",
                "size_mb": 320,
                "description": "Emergency protocols and drug dosing",
                "required": True
            },
            {
                "id": "drug-interactions",
                "name": "Drug Interactions Database",
                "specialty": "all",
                "size_mb": 180,
                "description": "Comprehensive drug interactions",
                "required": True
            }
        ]

    def estimate_download_size(
        self,
        pack_ids: List[str]
    ) -> Dict[str, Any]:
        """Estimate total download size for selected packs"""
        packs = self.get_available_packs()
        total_mb = sum(
            p["size_mb"] for p in packs
            if p["id"] in pack_ids
        )

        quota = self.storage.get_storage_quota()

        return {
            "total_mb": total_mb,
            "available_mb": quota.available_mb,
            "sufficient_space": total_mb <= quota.available_mb,
            "packs_count": len(pack_ids)
        }
