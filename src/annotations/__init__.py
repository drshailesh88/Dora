"""
Annotations Module for Dora Medical Knowledge Platform

Provides document highlighting and annotation capabilities:
- Text highlighting with colors
- Inline notes and comments
- Tags and categorization
- Export to markdown/PDF
"""

from .models import (
    Annotation,
    AnnotationType,
    HighlightColor,
    AnnotationExport,
    AnnotationStats,
)
from .service import AnnotationService
from .storage import AnnotationStorage

__all__ = [
    # Models
    "Annotation",
    "AnnotationType",
    "HighlightColor",
    "AnnotationExport",
    "AnnotationStats",
    # Service
    "AnnotationService",
    # Storage
    "AnnotationStorage",
]
