"""
Bibliography Generator

Generates formatted bibliographies in various citation styles.
Supports export to RIS, BibTeX, and formatted text.
"""

from typing import Optional

from .models import Citation, CitationStyle, Manuscript, Paper


class BibliographyGenerator:
    """
    Generates formatted bibliographies from citations.

    Features:
    - Multiple output formats (text, RIS, BibTeX)
    - Style-specific formatting
    - Sorting and grouping options
    """

    def __init__(self, style: CitationStyle = CitationStyle.AMA):
        """
        Initialize bibliography generator.

        Args:
            style: Citation style
        """
        self.style = style

    def generate(
        self,
        citations: list[Citation],
        style: Optional[CitationStyle] = None,
        sort_by: str = "number",
    ) -> str:
        """
        Generate formatted bibliography.

        Args:
            citations: List of citations
            style: Citation style (uses default if not specified)
            sort_by: Sort order (number, author, year, title)

        Returns:
            Formatted bibliography text
        """
        use_style = style or self.style

        # Sort citations
        sorted_citations = self._sort_citations(citations, sort_by)

        # Format each citation
        formatted = []
        for citation in sorted_citations:
            entry = citation.format(use_style)

            if use_style in [CitationStyle.AMA, CitationStyle.VANCOUVER, CitationStyle.IEEE]:
                # Numbered styles
                formatted.append(f"{citation.citation_number}. {entry}")
            else:
                # Author-year styles (no numbers)
                formatted.append(entry)

        return "\n\n".join(formatted)

    def generate_from_manuscript(
        self,
        manuscript: Manuscript,
        style: Optional[CitationStyle] = None,
    ) -> str:
        """
        Generate bibliography from manuscript.

        Args:
            manuscript: Manuscript with citations
            style: Citation style (uses manuscript's style if not specified)

        Returns:
            Formatted bibliography
        """
        use_style = style or manuscript.citation_style
        return self.generate(manuscript.citations, style=use_style, sort_by="number")

    def _sort_citations(
        self,
        citations: list[Citation],
        sort_by: str,
    ) -> list[Citation]:
        """Sort citations by specified criteria."""
        if sort_by == "number":
            return sorted(citations, key=lambda c: c.citation_number or 0)
        elif sort_by == "author":
            return sorted(
                citations,
                key=lambda c: c.paper.authors[0] if c.paper.authors else "zzz",
            )
        elif sort_by == "year":
            return sorted(
                citations,
                key=lambda c: c.paper.year or 0,
                reverse=True,
            )
        elif sort_by == "title":
            return sorted(citations, key=lambda c: c.paper.title)
        else:
            return citations

    def export_ris(self, papers: list[Paper]) -> str:
        """
        Export papers as RIS format.

        RIS is a standardized format for bibliographic data.

        Args:
            papers: List of papers

        Returns:
            RIS formatted string
        """
        ris_entries = []

        for paper in papers:
            entry = []

            # Article type
            article_type = "JOUR"  # Journal article (default)
            if paper.article_type:
                type_map = {
                    "review": "JOUR",
                    "book_chapter": "CHAP",
                    "clinical_trial": "JOUR",
                }
                article_type = type_map.get(paper.article_type.value, "JOUR")

            entry.append(f"TY  - {article_type}")

            # Title
            entry.append(f"TI  - {paper.title}")

            # Authors
            for author in paper.authors:
                entry.append(f"AU  - {author}")

            # Journal
            if paper.journal:
                entry.append(f"JO  - {paper.journal}")
                entry.append(f"T2  - {paper.journal}")

            # Year
            if paper.year:
                entry.append(f"PY  - {paper.year}")

            # Volume
            if paper.volume:
                entry.append(f"VL  - {paper.volume}")

            # Issue
            if paper.issue:
                entry.append(f"IS  - {paper.issue}")

            # Pages
            if paper.pages:
                entry.append(f"SP  - {paper.pages.split('-')[0]}")
                if '-' in paper.pages:
                    entry.append(f"EP  - {paper.pages.split('-')[1]}")

            # Abstract
            if paper.abstract:
                entry.append(f"AB  - {paper.abstract}")

            # Keywords
            for keyword in paper.keywords:
                entry.append(f"KW  - {keyword}")

            # DOI
            if paper.doi:
                entry.append(f"DO  - {paper.doi}")

            # PMID
            if paper.pmid:
                entry.append(f"AN  - {paper.pmid}")

            # Language
            entry.append(f"LA  - {paper.language}")

            # End of record
            entry.append("ER  - ")

            ris_entries.append("\n".join(entry))

        return "\n\n".join(ris_entries)

    def export_bibtex(self, papers: list[Paper]) -> str:
        """
        Export papers as BibTeX format.

        Args:
            papers: List of papers

        Returns:
            BibTeX formatted string
        """
        bibtex_entries = []

        for i, paper in enumerate(papers, 1):
            # Generate citation key
            author_key = ""
            if paper.authors:
                # Extract last name from first author
                first_author = paper.authors[0].split()[0]
                author_key = first_author.lower()

            year_key = str(paper.year) if paper.year else "nodate"
            cite_key = f"{author_key}{year_key}" if author_key else f"paper{i}"

            # Article type
            entry_type = "article"  # Default

            entry = [f"@{entry_type}{{{cite_key},"]

            # Title
            entry.append(f'  title = {{{paper.title}}},')

            # Authors
            if paper.authors:
                authors_str = " and ".join(paper.authors)
                entry.append(f'  author = {{{authors_str}}},')

            # Journal
            if paper.journal:
                entry.append(f'  journal = {{{paper.journal}}},')

            # Year
            if paper.year:
                entry.append(f'  year = {{{paper.year}}},')

            # Volume
            if paper.volume:
                entry.append(f'  volume = {{{paper.volume}}},')

            # Number (issue)
            if paper.issue:
                entry.append(f'  number = {{{paper.issue}}},')

            # Pages
            if paper.pages:
                entry.append(f'  pages = {{{paper.pages}}},')

            # DOI
            if paper.doi:
                entry.append(f'  doi = {{{paper.doi}}},')

            # PMID
            if paper.pmid:
                entry.append(f'  pmid = {{{paper.pmid}}},')

            # Abstract
            if paper.abstract:
                # Escape special characters
                abstract = paper.abstract.replace("{", "\\{").replace("}", "\\}")
                entry.append(f'  abstract = {{{abstract}}},')

            # Keywords
            if paper.keywords:
                keywords_str = ", ".join(paper.keywords)
                entry.append(f'  keywords = {{{keywords_str}}},')

            entry.append("}")

            bibtex_entries.append("\n".join(entry))

        return "\n\n".join(bibtex_entries)

    def export_endnote(self, papers: list[Paper]) -> str:
        """
        Export papers as EndNote format (similar to RIS).

        Args:
            papers: List of papers

        Returns:
            EndNote formatted string
        """
        # EndNote uses RIS-like format
        return self.export_ris(papers)

    def generate_summary(self, citations: list[Citation]) -> dict:
        """
        Generate summary statistics about citations.

        Args:
            citations: List of citations

        Returns:
            Dictionary with summary statistics
        """
        total = len(citations)

        if total == 0:
            return {
                "total": 0,
                "journals": {},
                "years": {},
                "authors": {},
                "article_types": {},
            }

        # Count journals
        journals = {}
        for cit in citations:
            journal = cit.paper.journal or "Unknown"
            journals[journal] = journals.get(journal, 0) + 1

        # Count years
        years = {}
        for cit in citations:
            year = str(cit.paper.year) if cit.paper.year else "Unknown"
            years[year] = years.get(year, 0) + 1

        # Count authors
        authors = {}
        for cit in citations:
            for author in cit.paper.authors:
                authors[author] = authors.get(author, 0) + 1

        # Count article types
        article_types = {}
        for cit in citations:
            atype = cit.paper.article_type.value if cit.paper.article_type else "unknown"
            article_types[atype] = article_types.get(atype, 0) + 1

        return {
            "total": total,
            "journals": journals,
            "years": years,
            "authors": authors,
            "article_types": article_types,
            "top_journals": sorted(journals.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_authors": sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def check_duplicates(self, citations: list[Citation]) -> list[tuple[Citation, Citation]]:
        """
        Check for duplicate citations.

        Args:
            citations: List of citations

        Returns:
            List of duplicate pairs
        """
        duplicates = []

        for i, cit1 in enumerate(citations):
            for cit2 in citations[i + 1:]:
                # Check PMID
                if cit1.paper.pmid and cit1.paper.pmid == cit2.paper.pmid:
                    duplicates.append((cit1, cit2))
                    continue

                # Check DOI
                if cit1.paper.doi and cit1.paper.doi == cit2.paper.doi:
                    duplicates.append((cit1, cit2))
                    continue

                # Check title similarity (exact match for now)
                if cit1.paper.title.lower().strip() == cit2.paper.title.lower().strip():
                    duplicates.append((cit1, cit2))

        return duplicates

    def validate_citations(self, citations: list[Citation]) -> list[dict]:
        """
        Validate citations for completeness.

        Args:
            citations: List of citations

        Returns:
            List of validation warnings
        """
        warnings = []

        for cit in citations:
            paper = cit.paper
            issues = []

            # Check required fields
            if not paper.title or paper.title == "Unknown":
                issues.append("Missing title")

            if not paper.authors:
                issues.append("Missing authors")

            if not paper.year:
                issues.append("Missing publication year")

            if not paper.journal:
                issues.append("Missing journal name")

            # Check for incomplete data
            if not paper.volume and paper.pages:
                issues.append("Has pages but missing volume")

            if not paper.doi and not paper.pmid:
                issues.append("Missing both DOI and PMID (recommended to have at least one)")

            if issues:
                warnings.append({
                    "citation_number": cit.citation_number,
                    "title": paper.title,
                    "issues": issues,
                })

        return warnings


def merge_bibliographies(
    bib1: list[Citation],
    bib2: list[Citation],
    remove_duplicates: bool = True,
) -> list[Citation]:
    """
    Merge two bibliographies.

    Args:
        bib1: First bibliography
        bib2: Second bibliography
        remove_duplicates: Whether to remove duplicates

    Returns:
        Merged bibliography
    """
    merged = list(bib1)

    if not remove_duplicates:
        merged.extend(bib2)
        return merged

    # Add citations from bib2 that aren't duplicates
    for cit2 in bib2:
        is_duplicate = False

        for cit1 in bib1:
            # Check PMID
            if cit2.paper.pmid and cit2.paper.pmid == cit1.paper.pmid:
                is_duplicate = True
                break

            # Check DOI
            if cit2.paper.doi and cit2.paper.doi == cit1.paper.doi:
                is_duplicate = True
                break

            # Check title
            if cit2.paper.title.lower().strip() == cit1.paper.title.lower().strip():
                is_duplicate = True
                break

        if not is_duplicate:
            merged.append(cit2)

    return merged
