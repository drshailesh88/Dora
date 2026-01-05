"""
Annotation Service

Business logic for document annotations including CRUD operations,
sharing, and export functionality.
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Optional

from .models import (
    Annotation,
    AnnotationExport,
    AnnotationStats,
    AnnotationType,
    HighlightColor,
)
from .storage import AnnotationStorage

logger = logging.getLogger(__name__)


class AnnotationService:
    """
    Service for managing document annotations.

    Provides:
    - CRUD operations for annotations
    - Sharing and collaboration
    - Statistics and analytics
    - Export functionality
    """

    def __init__(self, storage: Optional[AnnotationStorage] = None):
        """
        Initialize annotation service.

        Args:
            storage: Storage backend for annotations
        """
        self.storage = storage or AnnotationStorage()
        logger.info("Initialized AnnotationService")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_annotation(
        self,
        document_id: str,
        user_id: str,
        start_offset: int,
        end_offset: int,
        highlighted_text: str,
        annotation_type: AnnotationType = AnnotationType.HIGHLIGHT,
        color: Optional[HighlightColor] = HighlightColor.YELLOW,
        note_content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
    ) -> Annotation:
        """
        Create a new annotation.

        Args:
            document_id: Document being annotated
            user_id: User creating annotation
            start_offset: Character start position
            end_offset: Character end position
            highlighted_text: Selected text
            annotation_type: Type of annotation
            color: Highlight color
            note_content: Optional note text
            tags: Optional tags
            page_number: Optional page reference
            section_title: Optional section reference

        Returns:
            Created annotation
        """
        annotation = Annotation(
            document_id=document_id,
            user_id=user_id,
            start_offset=start_offset,
            end_offset=end_offset,
            highlighted_text=highlighted_text,
            annotation_type=annotation_type,
            color=color,
            note_content=note_content,
            tags=tags or [],
            page_number=page_number,
            section_title=section_title,
        )

        self.storage.save(annotation)
        logger.info(
            f"Created annotation {annotation.id} for document {document_id} by user {user_id}"
        )

        return annotation

    def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """
        Get annotation by ID.

        Args:
            annotation_id: Annotation identifier

        Returns:
            Annotation if found, None otherwise
        """
        return self.storage.get(annotation_id)

    def update_annotation(
        self,
        annotation_id: str,
        user_id: str,
        note_content: Optional[str] = None,
        color: Optional[HighlightColor] = None,
        tags: Optional[list[str]] = None,
    ) -> Optional[Annotation]:
        """
        Update an existing annotation.

        Args:
            annotation_id: Annotation to update
            user_id: User making update (must own annotation)
            note_content: New note content
            color: New color
            tags: New tags

        Returns:
            Updated annotation or None if not found/unauthorized
        """
        annotation = self.storage.get(annotation_id)

        if not annotation:
            logger.warning(f"Annotation not found: {annotation_id}")
            return None

        if annotation.user_id != user_id:
            logger.warning(
                f"User {user_id} not authorized to update annotation {annotation_id}"
            )
            return None

        # Update fields
        if note_content is not None:
            annotation.note_content = note_content
        if color is not None:
            annotation.color = color
        if tags is not None:
            annotation.tags = tags

        annotation.updated_at = datetime.utcnow()

        self.storage.save(annotation)
        logger.info(f"Updated annotation {annotation_id}")

        return annotation

    def delete_annotation(self, annotation_id: str, user_id: str) -> bool:
        """
        Delete an annotation.

        Args:
            annotation_id: Annotation to delete
            user_id: User deleting (must own annotation)

        Returns:
            True if deleted, False otherwise
        """
        annotation = self.storage.get(annotation_id)

        if not annotation:
            return False

        if annotation.user_id != user_id:
            logger.warning(
                f"User {user_id} not authorized to delete annotation {annotation_id}"
            )
            return False

        self.storage.delete(annotation_id)
        logger.info(f"Deleted annotation {annotation_id}")

        return True

    # =========================================================================
    # List and Query
    # =========================================================================

    def list_annotations(
        self,
        document_id: str,
        user_id: str,
        include_shared: bool = True,
        annotation_type: Optional[AnnotationType] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Annotation]:
        """
        List annotations for a document.

        Args:
            document_id: Document to get annotations for
            user_id: User requesting annotations
            include_shared: Include annotations shared with user
            annotation_type: Filter by type
            tags: Filter by tags

        Returns:
            List of annotations
        """
        annotations = self.storage.list_by_document(document_id)

        # Filter by ownership and sharing
        result = []
        for ann in annotations:
            if ann.user_id == user_id:
                result.append(ann)
            elif include_shared and (ann.is_shared or user_id in ann.shared_with):
                result.append(ann)

        # Filter by type
        if annotation_type:
            result = [a for a in result if a.annotation_type == annotation_type]

        # Filter by tags
        if tags:
            result = [a for a in result if any(t in a.tags for t in tags)]

        # Sort by position
        result.sort(key=lambda a: a.start_offset)

        return result

    def list_user_annotations(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Annotation]:
        """
        List all annotations by a user.

        Args:
            user_id: User identifier
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of user's annotations
        """
        annotations = self.storage.list_by_user(user_id)

        # Sort by most recent
        annotations.sort(key=lambda a: a.updated_at, reverse=True)

        return annotations[offset : offset + limit]

    def search_annotations(
        self,
        user_id: str,
        query: str,
        document_id: Optional[str] = None,
    ) -> list[Annotation]:
        """
        Search annotations by text content.

        Args:
            user_id: User identifier
            query: Search query
            document_id: Optional document filter

        Returns:
            Matching annotations
        """
        if document_id:
            annotations = self.list_annotations(document_id, user_id)
        else:
            annotations = self.list_user_annotations(user_id, limit=1000)

        query_lower = query.lower()
        results = []

        for ann in annotations:
            if (
                query_lower in ann.highlighted_text.lower()
                or (ann.note_content and query_lower in ann.note_content.lower())
                or any(query_lower in tag.lower() for tag in ann.tags)
            ):
                results.append(ann)

        return results

    # =========================================================================
    # Sharing
    # =========================================================================

    def share_annotation(
        self,
        annotation_id: str,
        owner_id: str,
        share_with: list[str],
        public: bool = False,
    ) -> Optional[Annotation]:
        """
        Share annotation with other users.

        Args:
            annotation_id: Annotation to share
            owner_id: Owner user ID
            share_with: List of user IDs to share with
            public: Make publicly visible

        Returns:
            Updated annotation or None
        """
        annotation = self.storage.get(annotation_id)

        if not annotation or annotation.user_id != owner_id:
            return None

        annotation.shared_with = list(set(annotation.shared_with + share_with))
        annotation.is_shared = public or len(annotation.shared_with) > 0
        annotation.updated_at = datetime.utcnow()

        self.storage.save(annotation)
        logger.info(f"Shared annotation {annotation_id} with {len(share_with)} users")

        return annotation

    def unshare_annotation(
        self,
        annotation_id: str,
        owner_id: str,
        unshare_from: Optional[list[str]] = None,
    ) -> Optional[Annotation]:
        """
        Remove sharing from annotation.

        Args:
            annotation_id: Annotation to unshare
            owner_id: Owner user ID
            unshare_from: Specific users to unshare (None = all)

        Returns:
            Updated annotation or None
        """
        annotation = self.storage.get(annotation_id)

        if not annotation or annotation.user_id != owner_id:
            return None

        if unshare_from:
            annotation.shared_with = [
                u for u in annotation.shared_with if u not in unshare_from
            ]
        else:
            annotation.shared_with = []
            annotation.is_shared = False

        annotation.updated_at = datetime.utcnow()
        self.storage.save(annotation)

        return annotation

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_user_stats(self, user_id: str) -> AnnotationStats:
        """
        Get annotation statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Annotation statistics
        """
        annotations = self.storage.list_by_user(user_id)

        stats = AnnotationStats()
        stats.total_annotations = len(annotations)

        # Count by type
        for ann in annotations:
            if ann.annotation_type == AnnotationType.HIGHLIGHT:
                stats.total_highlights += 1
            elif ann.annotation_type == AnnotationType.NOTE:
                stats.total_notes += 1
            elif ann.annotation_type == AnnotationType.BOOKMARK:
                stats.total_bookmarks += 1

        # Count by color
        color_counts = Counter(
            ann.color.value
            for ann in annotations
            if ann.color and ann.annotation_type == AnnotationType.HIGHLIGHT
        )
        stats.highlights_by_color = dict(color_counts)

        # Top tags
        all_tags = [tag for ann in annotations for tag in ann.tags]
        tag_counts = Counter(all_tags)
        stats.top_tags = tag_counts.most_common(10)

        # Documents annotated
        doc_ids = set(ann.document_id for ann in annotations)
        stats.documents_annotated = len(doc_ids)

        # Most annotated documents
        doc_counts = Counter(ann.document_id for ann in annotations)
        stats.most_annotated_documents = [
            {"document_id": doc_id, "count": count}
            for doc_id, count in doc_counts.most_common(5)
        ]

        # Shared
        stats.shared_annotations = sum(
            1 for ann in annotations if ann.is_shared or ann.shared_with
        )

        return stats

    # =========================================================================
    # Export
    # =========================================================================

    def export_annotations(
        self,
        document_id: str,
        user_id: str,
        document_title: str,
        user_name: str,
        format: str = "markdown",
    ) -> str:
        """
        Export annotations for a document.

        Args:
            document_id: Document to export
            user_id: User exporting
            document_title: Title for export
            user_name: User name for export
            format: Export format (markdown, json)

        Returns:
            Exported content string
        """
        annotations = self.list_annotations(document_id, user_id)

        export = AnnotationExport(
            document_title=document_title,
            document_id=document_id,
            user_name=user_name,
            exported_at=datetime.utcnow(),
            annotations=annotations,
        )

        if format == "markdown":
            return export.to_markdown()
        elif format == "json":
            import json

            return json.dumps(export.to_dict(), indent=2)
        else:
            return export.to_markdown()

    def bulk_add_tags(
        self,
        annotation_ids: list[str],
        user_id: str,
        tags: list[str],
    ) -> int:
        """
        Add tags to multiple annotations.

        Args:
            annotation_ids: Annotations to update
            user_id: User making update
            tags: Tags to add

        Returns:
            Number of annotations updated
        """
        count = 0

        for ann_id in annotation_ids:
            annotation = self.storage.get(ann_id)
            if annotation and annotation.user_id == user_id:
                annotation.tags = list(set(annotation.tags + tags))
                annotation.updated_at = datetime.utcnow()
                self.storage.save(annotation)
                count += 1

        logger.info(f"Added tags {tags} to {count} annotations")
        return count

    def delete_all_for_document(self, document_id: str, user_id: str) -> int:
        """
        Delete all user's annotations for a document.

        Args:
            document_id: Document to clear
            user_id: User's annotations to delete

        Returns:
            Number deleted
        """
        annotations = self.list_annotations(
            document_id, user_id, include_shared=False
        )

        count = 0
        for ann in annotations:
            if ann.user_id == user_id:
                self.storage.delete(ann.id)
                count += 1

        logger.info(f"Deleted {count} annotations for document {document_id}")
        return count
