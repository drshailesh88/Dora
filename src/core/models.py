"""Core data models for Dora."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for medical answers."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    """A citation to a source document."""

    source: str = Field(..., description="Source name (e.g., 'Harrison's Principles')")
    title: str = Field(..., description="Document or section title")
    section: Optional[str] = Field(None, description="Specific section")
    page: Optional[int] = Field(None, description="Page number if available")
    url: Optional[str] = Field(None, description="URL if available")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")

    def __str__(self) -> str:
        parts = [self.source]
        if self.title:
            parts.append(f'"{self.title}"')
        if self.section:
            parts.append(f"Section: {self.section}")
        if self.page:
            parts.append(f"p. {self.page}")
        return ", ".join(parts)


class Chunk(BaseModel):
    """A chunk of text from a document."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(..., description="The chunk text content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[list[float]] = Field(None, description="Vector embedding")

    @property
    def source(self) -> str:
        return self.metadata.get("source", "Unknown")

    @property
    def page(self) -> Optional[int]:
        return self.metadata.get("page")


class RetrievalResult(BaseModel):
    """Result from retrieval operation."""

    chunk: Chunk
    score: float = Field(..., description="Relevance score")
    retriever: str = Field(..., description="Which retriever found this (dense/sparse/graph)")


class Document(BaseModel):
    """A document in the knowledge base."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    doc_type: str = Field(..., description="textbook, guideline, paper, clinical_note")
    source: str = Field(..., description="Publisher or origin")
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    chunk_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class PatientContext(BaseModel):
    """Patient context for personalized queries."""

    patient_id: int
    name: str
    age: int
    gender: str
    active_diagnoses: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    recent_investigations: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""

    def to_context_string(self) -> str:
        """Convert to string for LLM context."""
        parts = [
            f"Patient: {self.name}, {self.age}y {self.gender}",
        ]
        if self.active_diagnoses:
            parts.append(f"Diagnoses: {', '.join(self.active_diagnoses)}")
        if self.current_medications:
            parts.append(f"Medications: {', '.join(self.current_medications)}")
        if self.allergies:
            parts.append(f"Allergies: {', '.join(self.allergies)}")
        return "\n".join(parts)


class MedicalAnswer(BaseModel):
    """Response from the medical query pipeline."""

    question: str
    answer: str
    confidence: ConfidenceLevel
    citations: list[Citation] = Field(default_factory=list)
    related_queries: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list, description="Drug interactions, etc.")
    patient_context_used: bool = False
    model_used: str = Field(..., description="Which LLM generated this")
    latency_ms: int = Field(..., description="Total response time")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_display_string(self) -> str:
        """Format for display to user."""
        lines = [
            self.answer,
            "",
            "---",
            f"Confidence: {self.confidence.value.upper()}",
        ]

        if self.citations:
            lines.append("")
            lines.append("Sources:")
            for i, cite in enumerate(self.citations[:5], 1):
                lines.append(f"  [{i}] {cite}")

        if self.warnings:
            lines.append("")
            lines.append("⚠️ Warnings:")
            for warning in self.warnings:
                lines.append(f"  • {warning}")

        if self.related_queries:
            lines.append("")
            lines.append("Related questions:")
            for q in self.related_queries[:3]:
                lines.append(f"  • {q}")

        return "\n".join(lines)
