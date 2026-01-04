"""
Academic Writing Module

Comprehensive academic writing support for medical research.
Integrates literature search, citation management, and AI-assisted writing.

Usage:
    from src.academic import AcademicService, CitationStyle

    service = AcademicService()
    papers = await service.search_literature("diabetes treatment")
    citation = service.add_citation(papers[0])
    bibliography = service.generate_bibliography()
"""

# Models
from .models import (
    ArticleType,
    Author,
    Citation,
    CitationStyle,
    Manuscript,
    ManuscriptSection,
    Paper,
    Reference,
    StudyType,
    WritingPrompt,
    WritingResult,
)

# PubMed client
from .pubmed import PubMedClient, get_pubmed_client

# Citation management
from .citation import CitationManager, CitationStyleFormatter, detect_citation_style_from_text

# Bibliography
from .bibliography import BibliographyGenerator, merge_bibliographies

# Writing assistance
from .writing import AcademicWritingAssistant, get_writing_assistant

# Main service
from .service import AcademicService, get_academic_service

__all__ = [
    # Models
    "ArticleType",
    "Author",
    "Citation",
    "CitationStyle",
    "Manuscript",
    "ManuscriptSection",
    "Paper",
    "Reference",
    "StudyType",
    "WritingPrompt",
    "WritingResult",
    # PubMed
    "PubMedClient",
    "get_pubmed_client",
    # Citation
    "CitationManager",
    "CitationStyleFormatter",
    "detect_citation_style_from_text",
    # Bibliography
    "BibliographyGenerator",
    "merge_bibliographies",
    # Writing
    "AcademicWritingAssistant",
    "get_writing_assistant",
    # Service
    "AcademicService",
    "get_academic_service",
]
