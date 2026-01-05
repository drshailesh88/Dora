"""Data models for document comparison."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of change detected in document comparison."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class DocumentMetadata(BaseModel):
    """Metadata for a document in comparison."""

    id: str
    title: str
    doc_type: str = Field(..., description="textbook, guideline, paper, clinical_note")
    version: Optional[str] = None
    source: Optional[str] = None
    last_modified: Optional[datetime] = None
    file_path: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineRange(BaseModel):
    """Range of lines in a document."""

    start: int = Field(..., ge=1, description="Starting line number (1-indexed)")
    end: int = Field(..., ge=1, description="Ending line number (1-indexed)")

    def __str__(self) -> str:
        if self.start == self.end:
            return f"Line {self.start}"
        return f"Lines {self.start}-{self.end}"


class DocumentChange(BaseModel):
    """A single change detected between documents."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ChangeType
    left_text: Optional[str] = Field(None, description="Text from left/original document")
    right_text: Optional[str] = Field(None, description="Text from right/new document")
    left_lines: Optional[LineRange] = Field(None, description="Line range in left document")
    right_lines: Optional[LineRange] = Field(None, description="Line range in right document")
    context_before: Optional[str] = Field(None, description="Context before the change")
    context_after: Optional[str] = Field(None, description="Context after the change")

    # Semantic information
    semantic_category: Optional[str] = Field(
        None, description="Category of semantic change (e.g., 'dosage_change', 'contraindication_added')"
    )
    clinical_significance: Optional[str] = Field(
        None, description="Assessment of clinical importance (high/medium/low)"
    )

    class Config:
        use_enum_values = True


class SemanticChangeGroup(BaseModel):
    """Group of related changes with semantic meaning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    category: str = Field(..., description="Category of changes (e.g., 'Treatment Protocol')")
    changes: list[DocumentChange] = Field(default_factory=list)
    summary: str = Field(..., description="Summary of this group of changes")
    clinical_impact: Optional[str] = Field(None, description="Clinical impact assessment")


class ComparisonSummary(BaseModel):
    """AI-generated summary of document comparison."""

    overall_summary: str = Field(..., description="High-level summary of all changes")
    key_changes: list[str] = Field(default_factory=list, description="List of key changes")
    clinical_implications: list[str] = Field(
        default_factory=list,
        description="Clinical implications of the changes"
    )
    risk_level: str = Field(..., description="Overall risk level (high/medium/low/none)")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations based on changes"
    )
    model_used: str = Field(..., description="LLM model used for summary")


class ComparisonResult(BaseModel):
    """Complete result of document comparison."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    left_document: DocumentMetadata = Field(..., description="Original/left document")
    right_document: DocumentMetadata = Field(..., description="New/right document")

    # Changes
    changes: list[DocumentChange] = Field(default_factory=list)
    semantic_groups: list[SemanticChangeGroup] = Field(default_factory=list)

    # Summary
    summary: Optional[ComparisonSummary] = None

    # Statistics
    total_changes: int = 0
    additions: int = 0
    deletions: int = 0
    modifications: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    comparison_time_ms: int = Field(..., description="Time taken for comparison")

    def update_statistics(self) -> None:
        """Update statistics based on changes."""
        self.total_changes = len(self.changes)
        self.additions = sum(1 for c in self.changes if c.type == ChangeType.ADDED)
        self.deletions = sum(1 for c in self.changes if c.type == ChangeType.REMOVED)
        self.modifications = sum(1 for c in self.changes if c.type == ChangeType.MODIFIED)


class ComparisonRequest(BaseModel):
    """Request to compare two documents."""

    doc1_id: str = Field(..., description="ID of first document (left/original)")
    doc2_id: Optional[str] = Field(None, description="ID of second document (right/new)")
    doc1_text: Optional[str] = Field(None, description="Text of first document (if not from DB)")
    doc2_text: Optional[str] = Field(None, description="Text of second document (if not from DB)")

    # Options
    include_semantic_analysis: bool = Field(True, description="Include AI semantic analysis")
    include_summary: bool = Field(True, description="Include AI summary")
    context_lines: int = Field(3, ge=0, description="Number of context lines around changes")

    class Config:
        json_schema_extra = {
            "example": {
                "doc1_id": "guideline-diabetes-2023",
                "doc2_id": "guideline-diabetes-2024",
                "include_semantic_analysis": True,
                "include_summary": True,
                "context_lines": 3
            }
        }


class SummarizeRequest(BaseModel):
    """Request to summarize an existing comparison."""

    comparison_id: str = Field(..., description="ID of comparison to summarize")
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Specific areas to focus on (e.g., ['dosage', 'contraindications'])"
    )
