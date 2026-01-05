"""
Document Comparison Module for Dora Medical Knowledge Platform

Provides document comparison capabilities:
- Text-based diffing
- Semantic change detection
- AI-powered change summarization
"""

from .models import (
    ChangeType,
    DocumentChange,
    DocumentMetadata,
    LineRange,
    SemanticChangeGroup,
    ComparisonResult,
    ComparisonRequest,
    ComparisonSummary,
    SummarizeRequest,
)
from .differ import DocumentDiffer
from .semantic_diff import SemanticDiffEngine
from .change_summarizer import ChangeSummarizer

__all__ = [
    # Models
    "ChangeType",
    "DocumentChange",
    "DocumentMetadata",
    "LineRange",
    "SemanticChangeGroup",
    "ComparisonResult",
    "ComparisonRequest",
    "ComparisonSummary",
    "SummarizeRequest",
    # Engines
    "DocumentDiffer",
    "SemanticDiffEngine",
    "ChangeSummarizer",
]
