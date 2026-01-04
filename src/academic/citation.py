"""
Citation Manager

Manages citations in various academic styles for medical writing.
Supports AMA, Vancouver, APA, IEEE, and Harvard styles.
"""

from typing import Optional

from .models import Citation, CitationStyle, Manuscript, Paper


class CitationManager:
    """
    Manages citations and bibliography for manuscripts.

    Features:
    - Multiple citation styles
    - Automatic numbering
    - Duplicate detection
    - In-text citation generation
    - Bibliography formatting
    """

    def __init__(self, style: CitationStyle = CitationStyle.AMA):
        """
        Initialize citation manager.

        Args:
            style: Default citation style
        """
        self.style = style
        self.citations: dict[str, Citation] = {}
        self.next_number = 1

    def add_paper(
        self,
        paper: Paper,
        context: Optional[str] = None,
    ) -> Citation:
        """
        Add a paper as a citation.

        Args:
            paper: Paper to cite
            context: Context where cited

        Returns:
            Citation object with assigned number
        """
        # Check if already cited (by PMID or DOI)
        citation_key = self._get_citation_key(paper)

        if citation_key in self.citations:
            existing = self.citations[citation_key]
            # Update context if provided
            if context and existing.context:
                existing.context += f"; {context}"
            elif context:
                existing.context = context
            return existing

        # Create new citation
        citation = Citation(
            paper=paper,
            citation_number=self.next_number,
            context=context,
        )

        self.citations[citation_key] = citation
        self.next_number += 1

        return citation

    def _get_citation_key(self, paper: Paper) -> str:
        """Get unique key for a paper."""
        if paper.pmid:
            return f"pmid:{paper.pmid}"
        elif paper.doi:
            return f"doi:{paper.doi}"
        else:
            # Fallback to title hash
            return f"title:{hash(paper.title)}"

    def get_inline_citation(
        self,
        paper: Paper,
        style: Optional[CitationStyle] = None,
    ) -> str:
        """
        Get inline citation marker for a paper.

        Args:
            paper: Paper being cited
            style: Citation style (uses default if not specified)

        Returns:
            Inline citation string (e.g., "[1]" or "(Smith, 2023)")
        """
        citation_key = self._get_citation_key(paper)
        citation = self.citations.get(citation_key)

        if not citation:
            # Auto-add if not already cited
            citation = self.add_paper(paper)

        use_style = style or self.style
        return citation.inline(use_style)

    def get_bibliography(
        self,
        style: Optional[CitationStyle] = None,
    ) -> list[str]:
        """
        Get formatted bibliography.

        Args:
            style: Citation style (uses default if not specified)

        Returns:
            List of formatted references
        """
        use_style = style or self.style

        # Sort citations by number
        sorted_citations = sorted(
            self.citations.values(),
            key=lambda c: c.citation_number or 0,
        )

        bibliography = []
        for citation in sorted_citations:
            formatted = citation.format(use_style)

            if use_style in [CitationStyle.AMA, CitationStyle.VANCOUVER, CitationStyle.IEEE]:
                # Numbered styles
                bibliography.append(f"{citation.citation_number}. {formatted}")
            else:
                # Author-year styles
                bibliography.append(formatted)

        return bibliography

    def format_bibliography(
        self,
        style: Optional[CitationStyle] = None,
        indent: int = 0,
    ) -> str:
        """
        Get formatted bibliography as a single string.

        Args:
            style: Citation style
            indent: Indentation spaces for hanging indent

        Returns:
            Formatted bibliography string
        """
        bibliography = self.get_bibliography(style)

        if indent > 0:
            # Apply hanging indent
            formatted = []
            for ref in bibliography:
                lines = ref.split('\n')
                first_line = lines[0]
                rest = [' ' * indent + line for line in lines[1:]]
                formatted.append('\n'.join([first_line] + rest))
            return '\n\n'.join(formatted)
        else:
            return '\n\n'.join(bibliography)

    def renumber(self, order: Optional[list[str]] = None) -> None:
        """
        Renumber citations.

        Args:
            order: Optional list of citation keys in desired order
        """
        if order:
            # Use specified order
            for i, key in enumerate(order, 1):
                if key in self.citations:
                    self.citations[key].citation_number = i
        else:
            # Renumber in current order
            sorted_citations = sorted(
                self.citations.values(),
                key=lambda c: c.citation_number or 0,
            )
            for i, citation in enumerate(sorted_citations, 1):
                citation.citation_number = i

        self.next_number = len(self.citations) + 1

    def remove_citation(self, paper: Paper) -> bool:
        """
        Remove a citation.

        Args:
            paper: Paper to remove

        Returns:
            True if removed, False if not found
        """
        citation_key = self._get_citation_key(paper)

        if citation_key in self.citations:
            del self.citations[citation_key]
            # Renumber remaining
            self.renumber()
            return True

        return False

    def get_citation_count(self) -> int:
        """Get total number of citations."""
        return len(self.citations)

    def get_citation_by_number(self, number: int) -> Optional[Citation]:
        """
        Get citation by its number.

        Args:
            number: Citation number

        Returns:
            Citation object or None
        """
        for citation in self.citations.values():
            if citation.citation_number == number:
                return citation
        return None

    def export_to_manuscript(self, manuscript: Manuscript) -> None:
        """
        Export citations to a manuscript.

        Args:
            manuscript: Manuscript to update
        """
        manuscript.citations = list(self.citations.values())
        manuscript.citation_style = self.style

    def import_from_manuscript(self, manuscript: Manuscript) -> None:
        """
        Import citations from a manuscript.

        Args:
            manuscript: Manuscript to import from
        """
        self.style = manuscript.citation_style
        self.citations = {}
        self.next_number = 1

        for citation in manuscript.citations:
            key = self._get_citation_key(citation.paper)
            self.citations[key] = citation
            if citation.citation_number and citation.citation_number >= self.next_number:
                self.next_number = citation.citation_number + 1


class CitationStyleFormatter:
    """
    Advanced citation formatting with style-specific rules.

    Implements detailed formatting rules for each citation style.
    """

    @staticmethod
    def format_authors_ama(
        authors: list[str],
        max_authors: int = 6,
        et_al: bool = True,
    ) -> str:
        """
        Format authors for AMA style.

        Rules:
        - List all authors up to 6
        - If >6, list first 3, then "et al"
        - Format: LastName Initials
        - Separate with commas
        """
        if not authors:
            return "Anonymous"

        if len(authors) <= max_authors:
            return ", ".join(authors)
        else:
            if et_al:
                return ", ".join(authors[:3]) + ", et al"
            else:
                return ", ".join(authors)

    @staticmethod
    def format_authors_vancouver(
        authors: list[str],
        max_authors: int = 6,
    ) -> str:
        """
        Format authors for Vancouver style.

        Rules:
        - List all authors up to 6
        - If >6, list first 6, then "et al"
        - Format: LastName Initials (no periods)
        - Separate with commas
        """
        if not authors:
            return "Anonymous"

        if len(authors) <= max_authors:
            return ", ".join(authors)
        else:
            return ", ".join(authors[:max_authors]) + ", et al"

    @staticmethod
    def format_authors_apa(
        authors: list[str],
        max_authors: int = 20,
    ) -> str:
        """
        Format authors for APA 7th edition.

        Rules:
        - 1-20 authors: List all
        - >20 authors: First 19, then "...", then last
        - Format: LastName, F. M.
        - Use "&" before last author
        """
        if not authors:
            return "Anonymous"

        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} & {authors[1]}"
        elif len(authors) <= max_authors:
            return ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            # >20 authors
            return ", ".join(authors[:19]) + f", ... {authors[-1]}"

    @staticmethod
    def format_journal_ama(
        journal: str,
        abbreviate: bool = True,
    ) -> str:
        """
        Format journal name for AMA.

        Args:
            journal: Full journal name
            abbreviate: Whether to abbreviate (per Index Medicus)

        Returns:
            Formatted journal name
        """
        # Common abbreviations (simplified - real implementation would use NLM catalog)
        abbreviations = {
            "The New England Journal of Medicine": "N Engl J Med",
            "Journal of the American Medical Association": "JAMA",
            "The Lancet": "Lancet",
            "British Medical Journal": "BMJ",
            "Annals of Internal Medicine": "Ann Intern Med",
            "Journal of Clinical Oncology": "J Clin Oncol",
            "Circulation": "Circulation",
            "Nature Medicine": "Nat Med",
            "Science": "Science",
        }

        if abbreviate and journal in abbreviations:
            return abbreviations[journal]

        return journal

    @staticmethod
    def format_title_apa(title: str) -> str:
        """
        Format title for APA style.

        Rules:
        - Sentence case (capitalize first word and proper nouns)
        - Italicize journal titles but not article titles
        """
        # Simple sentence case (real implementation would preserve proper nouns)
        if title:
            return title[0].upper() + title[1:].lower()
        return title


def detect_citation_style_from_text(text: str) -> CitationStyle:
    """
    Detect citation style from text.

    Args:
        text: Text containing citations

    Returns:
        Detected citation style
    """
    # Check for numbered citations [1], [2]
    if "[1]" in text or "[2]" in text:
        # Could be AMA, Vancouver, or IEEE
        # Look for other clues
        if "et al" in text.lower():
            return CitationStyle.VANCOUVER
        return CitationStyle.AMA

    # Check for (Author, Year) citations
    if "(" in text and "," in text and any(str(year) in text for year in range(1900, 2030)):
        return CitationStyle.APA

    # Default to AMA for medical texts
    return CitationStyle.AMA
