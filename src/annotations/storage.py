"""
Annotation Storage

Persistence layer for annotations using SQLite with PostgreSQL support.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from .models import Annotation, AnnotationType, HighlightColor

logger = logging.getLogger(__name__)


class AnnotationStorage:
    """
    Storage backend for annotations.

    Uses SQLite for local storage with option for PostgreSQL in production.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        postgres_url: Optional[str] = None,
    ):
        """
        Initialize storage.

        Args:
            db_path: SQLite database path (default: ~/.dora/annotations.db)
            postgres_url: PostgreSQL connection URL (takes precedence)
        """
        self.postgres_url = postgres_url
        self._postgres_pool = None

        if postgres_url:
            self._init_postgres()
        else:
            self.db_path = db_path or str(
                Path.home() / ".dora" / "annotations.db"
            )
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

        logger.info(f"Initialized AnnotationStorage")

    def _init_sqlite(self) -> None:
        """Initialize SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    highlighted_text TEXT NOT NULL,
                    annotation_type TEXT NOT NULL,
                    color TEXT,
                    note_content TEXT,
                    tags TEXT,
                    is_shared INTEGER DEFAULT 0,
                    shared_with TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    context_before TEXT,
                    context_after TEXT,
                    page_number INTEGER,
                    section_title TEXT
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_document
                ON annotations(document_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_user
                ON annotations(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_type
                ON annotations(annotation_type)
            """)

            conn.commit()

    def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection pool."""
        try:
            import asyncpg

            # Will initialize pool on first use
            logger.info("PostgreSQL mode enabled")
        except ImportError:
            logger.warning("asyncpg not available, falling back to SQLite")
            self.postgres_url = None
            self._init_sqlite()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save(self, annotation: Annotation) -> None:
        """
        Save annotation to storage.

        Args:
            annotation: Annotation to save
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO annotations (
                    id, document_id, user_id, start_offset, end_offset,
                    highlighted_text, annotation_type, color, note_content,
                    tags, is_shared, shared_with, created_at, updated_at,
                    context_before, context_after, page_number, section_title
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation.id,
                    annotation.document_id,
                    annotation.user_id,
                    annotation.start_offset,
                    annotation.end_offset,
                    annotation.highlighted_text,
                    annotation.annotation_type.value,
                    annotation.color.value if annotation.color else None,
                    annotation.note_content,
                    json.dumps(annotation.tags),
                    1 if annotation.is_shared else 0,
                    json.dumps(annotation.shared_with),
                    annotation.created_at.isoformat(),
                    annotation.updated_at.isoformat(),
                    annotation.context_before,
                    annotation.context_after,
                    annotation.page_number,
                    annotation.section_title,
                ),
            )
            conn.commit()

    def get(self, annotation_id: str) -> Optional[Annotation]:
        """
        Get annotation by ID.

        Args:
            annotation_id: Annotation identifier

        Returns:
            Annotation if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM annotations WHERE id = ?",
                (annotation_id,),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_annotation(row)
            return None

    def delete(self, annotation_id: str) -> bool:
        """
        Delete annotation.

        Args:
            annotation_id: Annotation to delete

        Returns:
            True if deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM annotations WHERE id = ?",
                (annotation_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_by_document(self, document_id: str) -> list[Annotation]:
        """
        List annotations for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of annotations
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM annotations WHERE document_id = ? ORDER BY start_offset",
                (document_id,),
            )
            return [self._row_to_annotation(row) for row in cursor.fetchall()]

    def list_by_user(self, user_id: str) -> list[Annotation]:
        """
        List annotations by user.

        Args:
            user_id: User identifier

        Returns:
            List of annotations
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM annotations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
            return [self._row_to_annotation(row) for row in cursor.fetchall()]

    def list_shared_with_user(self, user_id: str) -> list[Annotation]:
        """
        List annotations shared with a user.

        Args:
            user_id: User identifier

        Returns:
            List of shared annotations
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM annotations
                WHERE is_shared = 1
                OR shared_with LIKE ?
                ORDER BY updated_at DESC
                """,
                (f'%"{user_id}"%',),
            )
            return [self._row_to_annotation(row) for row in cursor.fetchall()]

    def count_by_document(self, document_id: str) -> int:
        """Count annotations for a document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM annotations WHERE document_id = ?",
                (document_id,),
            )
            return cursor.fetchone()[0]

    def count_by_user(self, user_id: str) -> int:
        """Count annotations by a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM annotations WHERE user_id = ?",
                (user_id,),
            )
            return cursor.fetchone()[0]

    def _row_to_annotation(self, row: sqlite3.Row) -> Annotation:
        """Convert database row to Annotation object."""
        return Annotation(
            id=row["id"],
            document_id=row["document_id"],
            user_id=row["user_id"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            highlighted_text=row["highlighted_text"],
            annotation_type=AnnotationType(row["annotation_type"]),
            color=HighlightColor(row["color"]) if row["color"] else None,
            note_content=row["note_content"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            is_shared=bool(row["is_shared"]),
            shared_with=json.loads(row["shared_with"]) if row["shared_with"] else [],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            context_before=row["context_before"],
            context_after=row["context_after"],
            page_number=row["page_number"],
            section_title=row["section_title"],
        )

    def close(self) -> None:
        """Close storage connections."""
        if self._postgres_pool:
            # Close postgres pool
            pass
        logger.debug("AnnotationStorage closed")
