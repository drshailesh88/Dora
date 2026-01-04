"""
Academic Writing Module - Data Models

Models for academic papers, citations, references, and manuscripts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CitationStyle(str, Enum):
    """Supported citation styles."""

    AMA = "ama"  # American Medical Association
    VANCOUVER = "vancouver"  # Vancouver (ICMJE)
    APA = "apa"  # American Psychological Association
    IEEE = "ieee"  # IEEE
    HARVARD = "harvard"  # Harvard
    ICMJE = "icmje"  # International Committee of Medical Journal Editors


class ArticleType(str, Enum):
    """PubMed article types."""

    JOURNAL_ARTICLE = "journal_article"
    REVIEW = "review"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    CLINICAL_TRIAL = "clinical_trial"
    CASE_REPORT = "case_report"
    LETTER = "letter"
    EDITORIAL = "editorial"
    GUIDELINE = "guideline"
    BOOK_CHAPTER = "book_chapter"


class StudyType(str, Enum):
    """Types of medical research studies."""

    RCT = "randomized_controlled_trial"
    COHORT = "cohort_study"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    CASE_SERIES = "case_series"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    QUALITATIVE = "qualitative"
    MIXED_METHODS = "mixed_methods"


class ManuscriptSection(str, Enum):
    """Sections of a research manuscript."""

    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    ACKNOWLEDGMENTS = "acknowledgments"


@dataclass
class Author:
    """Author information."""

    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    initials: Optional[str] = None
    affiliation: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None

    def __str__(self) -> str:
        """Format author name."""
        if self.last_name and self.initials:
            return f"{self.last_name} {self.initials}"
        elif self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name[0]}"
        return self.name

    def to_apa(self) -> str:
        """Format for APA style."""
        if self.last_name and self.first_name:
            return f"{self.last_name}, {self.first_name[0]}."
        return self.name

    def to_vancouver(self) -> str:
        """Format for Vancouver style."""
        if self.last_name and self.initials:
            return f"{self.last_name} {self.initials}"
        elif self.last_name and self.first_name:
            first_initial = "".join([n[0].upper() for n in self.first_name.split()])
            return f"{self.last_name} {first_initial}"
        return self.name


class Paper(BaseModel):
    """A published medical paper."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    pmid: Optional[str] = Field(None, description="PubMed ID")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    pmc_id: Optional[str] = Field(None, description="PubMed Central ID")

    # Bibliographic info
    title: str
    authors: list[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None

    # Content
    abstract: Optional[str] = None
    full_text: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list, description="Medical Subject Headings")

    # Metadata
    article_type: Optional[ArticleType] = None
    publication_date: Optional[datetime] = None
    epub_date: Optional[datetime] = None
    language: str = "eng"

    # Metrics
    citation_count: int = 0

    # Local metadata
    added_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

    def short_citation(self, style: CitationStyle = CitationStyle.AMA) -> str:
        """Generate short citation."""
        if style == CitationStyle.AMA:
            return self._short_ama()
        elif style == CitationStyle.VANCOUVER:
            return self._short_vancouver()
        elif style == CitationStyle.APA:
            return self._short_apa()
        return self._short_ama()

    def _short_ama(self) -> str:
        """Short AMA citation."""
        authors_str = self._format_authors_ama(short=True)
        year_str = str(self.year) if self.year else "n.d."
        journal_str = self.journal or "Unknown"

        parts = [authors_str, self.title, journal_str]
        if self.year:
            parts.append(year_str)
        if self.volume:
            parts.append(f"{self.volume}")
        if self.pages:
            parts.append(f"{self.pages}")

        return ". ".join(filter(None, parts)) + "."

    def _short_vancouver(self) -> str:
        """Short Vancouver citation."""
        authors_str = self._format_authors_vancouver(short=True)
        journal_str = self.journal or "Unknown"

        parts = [authors_str, self.title, journal_str]
        if self.year:
            parts.append(f"{self.year}")
        if self.volume:
            vol_str = f"{self.volume}"
            if self.issue:
                vol_str += f"({self.issue})"
            parts.append(vol_str)
        if self.pages:
            parts.append(f":{self.pages}")

        return ". ".join(filter(None, parts)) + "."

    def _short_apa(self) -> str:
        """Short APA citation."""
        authors_str = self._format_authors_apa()
        year_str = f"({self.year})" if self.year else "(n.d.)"
        journal_str = self.journal or "Unknown"

        citation = f"{authors_str} {year_str}. {self.title}. {journal_str}"
        if self.volume:
            citation += f", {self.volume}"
        if self.pages:
            citation += f", {self.pages}"
        if self.doi:
            citation += f". https://doi.org/{self.doi}"

        return citation + "."

    def _format_authors_ama(self, short: bool = False) -> str:
        """Format authors for AMA."""
        if not self.authors:
            return "Anonymous"

        if short and len(self.authors) > 6:
            return f"{self.authors[0]} et al"
        elif len(self.authors) > 6:
            return ", ".join(self.authors[:6]) + ", et al"
        elif len(self.authors) == 1:
            return self.authors[0]
        elif len(self.authors) == 2:
            return f"{self.authors[0]}, {self.authors[1]}"
        else:
            return ", ".join(self.authors[:-1]) + ", " + self.authors[-1]

    def _format_authors_vancouver(self, short: bool = False) -> str:
        """Format authors for Vancouver."""
        if not self.authors:
            return "Anonymous"

        if short and len(self.authors) > 6:
            return f"{self.authors[0]}, et al"
        elif len(self.authors) > 6:
            return ", ".join(self.authors[:6]) + ", et al"
        else:
            return ", ".join(self.authors)

    def _format_authors_apa(self) -> str:
        """Format authors for APA."""
        if not self.authors:
            return "Anonymous"

        if len(self.authors) == 1:
            return self.authors[0]
        elif len(self.authors) == 2:
            return f"{self.authors[0]}, & {self.authors[1]}"
        elif len(self.authors) <= 20:
            return ", ".join(self.authors[:-1]) + f", & {self.authors[-1]}"
        else:
            # For >20 authors, list first 19 then ... then last
            return ", ".join(self.authors[:19]) + f", ... {self.authors[-1]}"


class Citation(BaseModel):
    """A citation/reference in a manuscript."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    paper: Paper
    citation_number: Optional[int] = None
    page_cited: Optional[str] = None
    context: Optional[str] = Field(None, description="Where/why this was cited")

    def format(self, style: CitationStyle = CitationStyle.AMA) -> str:
        """Format citation in specified style."""
        if style == CitationStyle.AMA:
            return self._format_ama()
        elif style == CitationStyle.VANCOUVER:
            return self._format_vancouver()
        elif style == CitationStyle.APA:
            return self._format_apa()
        elif style == CitationStyle.IEEE:
            return self._format_ieee()
        elif style == CitationStyle.HARVARD:
            return self._format_harvard()
        return self._format_ama()

    def _format_ama(self) -> str:
        """Format as AMA."""
        return self.paper.short_citation(CitationStyle.AMA)

    def _format_vancouver(self) -> str:
        """Format as Vancouver."""
        return self.paper.short_citation(CitationStyle.VANCOUVER)

    def _format_apa(self) -> str:
        """Format as APA."""
        return self.paper.short_citation(CitationStyle.APA)

    def _format_ieee(self) -> str:
        """Format as IEEE."""
        authors = ", ".join(self.paper.authors[:3]) if self.paper.authors else "Anonymous"
        if len(self.paper.authors) > 3:
            authors += " et al."

        citation = f"{authors}, \"{self.paper.title},\" {self.paper.journal or 'Unknown'}"
        if self.paper.volume:
            citation += f", vol. {self.paper.volume}"
        if self.paper.issue:
            citation += f", no. {self.paper.issue}"
        if self.paper.pages:
            citation += f", pp. {self.paper.pages}"
        if self.paper.year:
            citation += f", {self.paper.year}"

        return citation + "."

    def _format_harvard(self) -> str:
        """Format as Harvard."""
        authors = self.paper.authors[0] if self.paper.authors else "Anonymous"
        if len(self.paper.authors) > 1:
            authors += " et al."

        year = self.paper.year or "n.d."
        citation = f"{authors} ({year}) '{self.paper.title}', {self.paper.journal or 'Unknown'}"
        if self.paper.volume:
            citation += f", {self.paper.volume}"
        if self.paper.issue:
            citation += f"({self.paper.issue})"
        if self.paper.pages:
            citation += f", pp. {self.paper.pages}"

        return citation + "."

    def inline(self, style: CitationStyle = CitationStyle.AMA) -> str:
        """Get inline citation marker."""
        if style in [CitationStyle.AMA, CitationStyle.VANCOUVER, CitationStyle.IEEE]:
            # Numbered citation
            return f"[{self.citation_number}]" if self.citation_number else "[?]"
        elif style in [CitationStyle.APA, CitationStyle.HARVARD]:
            # Author-year citation
            author = self.paper.authors[0] if self.paper.authors else "Anonymous"
            # Extract last name if format is "Last FM"
            author_parts = author.split()
            last_name = author_parts[0] if author_parts else author
            year = self.paper.year or "n.d."
            return f"({last_name}, {year})"
        return f"[{self.citation_number}]"


class Reference(BaseModel):
    """A reference entry in bibliography."""

    citation: Citation
    style: CitationStyle = CitationStyle.AMA

    def __str__(self) -> str:
        """Format reference."""
        formatted = self.citation.format(self.style)
        if self.citation.citation_number:
            return f"{self.citation.citation_number}. {formatted}"
        return formatted


class Manuscript(BaseModel):
    """A manuscript being written."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    authors: list[Author] = Field(default_factory=list)

    # Sections
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None
    acknowledgments: Optional[str] = None

    # References
    citations: list[Citation] = Field(default_factory=list)
    citation_style: CitationStyle = CitationStyle.AMA

    # Metadata
    study_type: Optional[StudyType] = None
    keywords: list[str] = Field(default_factory=list)
    target_journal: Optional[str] = None
    word_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

    def add_citation(self, paper: Paper, context: Optional[str] = None) -> Citation:
        """Add a citation to the manuscript."""
        # Check if already cited
        for cit in self.citations:
            if cit.paper.pmid and cit.paper.pmid == paper.pmid:
                return cit
            if cit.paper.doi and cit.paper.doi == paper.doi:
                return cit

        # Create new citation
        citation = Citation(
            paper=paper,
            citation_number=len(self.citations) + 1,
            context=context,
        )
        self.citations.append(citation)
        return citation

    def get_bibliography(self) -> list[Reference]:
        """Get formatted bibliography."""
        return [
            Reference(citation=cit, style=self.citation_style)
            for cit in sorted(self.citations, key=lambda x: x.citation_number or 0)
        ]

    def get_word_count(self) -> int:
        """Calculate total word count."""
        sections = [
            self.abstract,
            self.introduction,
            self.methods,
            self.results,
            self.discussion,
            self.conclusion,
        ]

        total = 0
        for section in sections:
            if section:
                total += len(section.split())

        return total

    def update_word_count(self) -> None:
        """Update the word count."""
        self.word_count = self.get_word_count()
        self.updated_at = datetime.utcnow()


class WritingPrompt(BaseModel):
    """Prompt for AI writing assistance."""

    section: ManuscriptSection
    context: dict = Field(default_factory=dict)
    style: str = "academic"
    max_words: Optional[int] = None

    class Config:
        use_enum_values = True


class WritingResult(BaseModel):
    """Result from AI writing assistance."""

    section: ManuscriptSection
    content: str
    word_count: int
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
