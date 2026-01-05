"""
Annotation Data Models

Models for document highlighting, notes, and annotations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


class AnnotationType(str, Enum):
    """Types of annotations"""
    HIGHLIGHT = "highlight"
    NOTE = "note"
    BOOKMARK = "bookmark"


class HighlightColor(str, Enum):
    """Available highlight colors"""
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PINK = "pink"
    PURPLE = "purple"
    ORANGE = "orange"
    RED = "red"


@dataclass
class Annotation:
    """
    Document annotation model.

    Supports:
    - Text highlighting with colors
    - Inline notes attached to highlights
    - Bookmarks for quick navigation
    - Tags for categorization
    - Sharing with colleagues
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Document reference
    document_id: str = ""
    user_id: str = ""

    # Text selection
    start_offset: int = 0  # Character position start
    end_offset: int = 0    # Character position end
    highlighted_text: str = ""  # Actual text content

    # Annotation details
    annotation_type: AnnotationType = AnnotationType.HIGHLIGHT
    color: Optional[HighlightColor] = HighlightColor.YELLOW

    # Optional note content
    note_content: Optional[str] = None

    # Tags for categorization
    tags: List[str] = field(default_factory=list)

    # Sharing
    is_shared: bool = False
    shared_with: List[str] = field(default_factory=list)  # User IDs

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Context (optional - paragraph or section containing the highlight)
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    # Page/section reference (if document has structure)
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "highlighted_text": self.highlighted_text,
            "annotation_type": self.annotation_type.value,
            "color": self.color.value if self.color else None,
            "note_content": self.note_content,
            "tags": self.tags,
            "is_shared": self.is_shared,
            "shared_with": self.shared_with,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context_before": self.context_before,
            "context_after": self.context_after,
            "page_number": self.page_number,
            "section_title": self.section_title,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            document_id=data.get("document_id", ""),
            user_id=data.get("user_id", ""),
            start_offset=data.get("start_offset", 0),
            end_offset=data.get("end_offset", 0),
            highlighted_text=data.get("highlighted_text", ""),
            annotation_type=AnnotationType(data.get("annotation_type", "highlight")),
            color=HighlightColor(data["color"]) if data.get("color") else None,
            note_content=data.get("note_content"),
            tags=data.get("tags", []),
            is_shared=data.get("is_shared", False),
            shared_with=data.get("shared_with", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            context_before=data.get("context_before"),
            context_after=data.get("context_after"),
            page_number=data.get("page_number"),
            section_title=data.get("section_title"),
        )


@dataclass
class AnnotationExport:
    """
    Export format for annotations.

    Used when exporting annotations to markdown, PDF, etc.
    """
    document_title: str
    document_id: str
    user_name: str
    exported_at: datetime
    annotations: List[Annotation]

    def to_markdown(self) -> str:
        """Export annotations to markdown format"""
        lines = [
            f"# Annotations for: {self.document_title}",
            f"",
            f"**Exported by:** {self.user_name}",
            f"**Date:** {self.exported_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Total Annotations:** {len(self.annotations)}",
            f"",
            "---",
            f"",
        ]

        # Group by type
        highlights = [a for a in self.annotations if a.annotation_type == AnnotationType.HIGHLIGHT]
        notes = [a for a in self.annotations if a.annotation_type == AnnotationType.NOTE]
        bookmarks = [a for a in self.annotations if a.annotation_type == AnnotationType.BOOKMARK]

        if highlights:
            lines.append("## Highlights\n")
            for ann in highlights:
                lines.append(f"### {ann.color.value.title() if ann.color else 'Highlight'}")
                lines.append(f"> {ann.highlighted_text}\n")
                if ann.note_content:
                    lines.append(f"**Note:** {ann.note_content}\n")
                if ann.tags:
                    lines.append(f"**Tags:** {', '.join(ann.tags)}\n")
                if ann.section_title:
                    lines.append(f"**Section:** {ann.section_title}\n")
                lines.append("")

        if notes:
            lines.append("## Notes\n")
            for ann in notes:
                if ann.section_title:
                    lines.append(f"### {ann.section_title}")
                if ann.highlighted_text:
                    lines.append(f"> {ann.highlighted_text}\n")
                lines.append(f"{ann.note_content}\n")
                if ann.tags:
                    lines.append(f"**Tags:** {', '.join(ann.tags)}\n")
                lines.append("")

        if bookmarks:
            lines.append("## Bookmarks\n")
            for ann in bookmarks:
                title = ann.section_title or f"Page {ann.page_number}" or "Bookmark"
                lines.append(f"- {title}")
                if ann.highlighted_text:
                    lines.append(f"  > {ann.highlighted_text[:100]}...")
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "document_title": self.document_title,
            "document_id": self.document_id,
            "user_name": self.user_name,
            "exported_at": self.exported_at.isoformat(),
            "annotations": [a.to_dict() for a in self.annotations],
        }


@dataclass
class AnnotationStats:
    """Statistics about user's annotations"""
    total_annotations: int = 0
    total_highlights: int = 0
    total_notes: int = 0
    total_bookmarks: int = 0

    # By color
    highlights_by_color: dict = field(default_factory=dict)

    # Most used tags
    top_tags: List[tuple] = field(default_factory=list)  # (tag, count)

    # By document
    documents_annotated: int = 0
    most_annotated_documents: List[dict] = field(default_factory=list)

    # Sharing
    shared_annotations: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total_annotations": self.total_annotations,
            "total_highlights": self.total_highlights,
            "total_notes": self.total_notes,
            "total_bookmarks": self.total_bookmarks,
            "highlights_by_color": self.highlights_by_color,
            "top_tags": self.top_tags,
            "documents_annotated": self.documents_annotated,
            "most_annotated_documents": self.most_annotated_documents,
            "shared_annotations": self.shared_annotations,
        }
