"""
PubMed API Client

Integrates with NCBI E-utilities for literature search and retrieval.
Implements rate limiting (3 requests/second for public API).

API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx

from .models import ArticleType, Author, Paper


class PubMedClient:
    """
    Client for PubMed/NCBI E-utilities API.

    Features:
    - Search by keywords, authors, MeSH terms
    - Fetch article details
    - Download PMC full-text
    - Rate limiting (3 req/sec public, 10 req/sec with API key)
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        tool: str = "Dora",
    ):
        """
        Initialize PubMed client.

        Args:
            api_key: NCBI API key (increases rate limit to 10/sec)
            email: Contact email (required by NCBI guidelines)
            tool: Tool name for NCBI logs
        """
        self.api_key = api_key
        self.email = email
        self.tool = tool

        # Rate limiting: 3 req/sec without key, 10/sec with key
        self.rate_limit = 10 if api_key else 3
        self.min_delay = 1.0 / self.rate_limit
        self.last_request_time = 0.0

        self.client = httpx.AsyncClient(timeout=30.0)

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_delay:
            await asyncio.sleep(self.min_delay - time_since_last)

        self.last_request_time = asyncio.get_event_loop().time()

    def _build_params(self, **kwargs) -> dict:
        """Build common query parameters."""
        params = {
            "tool": self.tool,
        }

        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        params.update(kwargs)
        return params

    async def search(
        self,
        query: str,
        max_results: int = 20,
        sort: str = "relevance",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        article_type: Optional[str] = None,
    ) -> list[str]:
        """
        Search PubMed for articles.

        Args:
            query: Search query (can use PubMed syntax)
            max_results: Maximum number of results
            sort: Sort order (relevance, date, or pub_date)
            date_from: Start date (YYYY/MM/DD or YYYY)
            date_to: End date (YYYY/MM/DD or YYYY)
            article_type: Filter by article type

        Returns:
            List of PMIDs

        Examples:
            >>> await client.search("diabetes treatment")
            >>> await client.search("cancer[Title] AND 2023[PDAT]")
            >>> await client.search("Smith J[Author]")
        """
        await self._rate_limit()

        # Build query
        full_query = query

        # Add date range if specified
        if date_from or date_to:
            date_range = f"{date_from or '1900'}:{date_to or '3000'}[PDAT]"
            full_query += f" AND {date_range}"

        # Add article type filter
        if article_type:
            full_query += f" AND {article_type}[Publication Type]"

        params = self._build_params(
            db="pubmed",
            term=full_query,
            retmax=max_results,
            sort=sort,
            retmode="xml",
        )

        url = f"{self.BASE_URL}/esearch.fcgi"
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.text)
        pmids = [id_elem.text for id_elem in root.findall(".//Id")]

        return pmids

    async def search_by_author(
        self,
        author: str,
        max_results: int = 20,
    ) -> list[str]:
        """
        Search by author name.

        Args:
            author: Author name (e.g., "Smith J" or "Smith John")
            max_results: Maximum results

        Returns:
            List of PMIDs
        """
        query = f"{author}[Author]"
        return await self.search(query, max_results=max_results)

    async def search_by_mesh(
        self,
        mesh_term: str,
        max_results: int = 20,
    ) -> list[str]:
        """
        Search by MeSH (Medical Subject Heading) term.

        Args:
            mesh_term: MeSH term
            max_results: Maximum results

        Returns:
            List of PMIDs
        """
        query = f"{mesh_term}[MeSH Terms]"
        return await self.search(query, max_results=max_results)

    async def get_article(self, pmid: str) -> Optional[Paper]:
        """
        Get detailed article information.

        Args:
            pmid: PubMed ID

        Returns:
            Paper object with full metadata
        """
        await self._rate_limit()

        params = self._build_params(
            db="pubmed",
            id=pmid,
            retmode="xml",
        )

        url = f"{self.BASE_URL}/efetch.fcgi"
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        # Parse XML
        try:
            root = ET.fromstring(response.text)
            article = root.find(".//PubmedArticle")
            if not article:
                return None

            return self._parse_article(article, pmid)

        except Exception as e:
            print(f"Error parsing article {pmid}: {e}")
            return None

    def _parse_article(self, article_elem: ET.Element, pmid: str) -> Paper:
        """Parse article XML into Paper object."""
        # Basic info
        article = article_elem.find(".//Article")
        if not article:
            return Paper(pmid=pmid, title="Unknown")

        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "Unknown"

        # Abstract
        abstract_elem = article.find(".//AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else None

        # Handle structured abstracts
        if abstract is None:
            abstract_parts = []
            for abs_elem in article.findall(".//AbstractText"):
                label = abs_elem.get("Label", "")
                text = abs_elem.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            if abstract_parts:
                abstract = "\n".join(abstract_parts)

        # Authors
        authors = []
        for author_elem in article.findall(".//Author"):
            last_name_elem = author_elem.find("LastName")
            first_name_elem = author_elem.find("ForeName")
            initials_elem = author_elem.find("Initials")

            if last_name_elem is not None:
                last_name = last_name_elem.text
                initials = initials_elem.text if initials_elem is not None else ""
                authors.append(f"{last_name} {initials}".strip())

        # Journal info
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else None

        # Publication date
        pub_date_elem = article.find(".//PubDate")
        year = None
        pub_date = None
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find("Year")
            month_elem = pub_date_elem.find("Month")
            day_elem = pub_date_elem.find("Day")

            if year_elem is not None:
                year = int(year_elem.text)

                try:
                    month = month_elem.text if month_elem is not None else "1"
                    day = day_elem.text if day_elem is not None else "1"

                    # Convert month name to number if needed
                    month_map = {
                        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
                        "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
                        "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
                    }
                    if month in month_map:
                        month = month_map[month]

                    pub_date = datetime(year, int(month), int(day))
                except (ValueError, TypeError):
                    pub_date = datetime(year, 1, 1)

        # Volume, Issue, Pages
        volume_elem = article.find(".//Volume")
        volume = volume_elem.text if volume_elem is not None else None

        issue_elem = article.find(".//Issue")
        issue = issue_elem.text if issue_elem is not None else None

        pages_elem = article.find(".//MedlinePgn")
        pages = pages_elem.text if pages_elem is not None else None

        # DOI
        doi = None
        for article_id in article_elem.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi":
                doi = article_id.text
                break

        # PMC ID
        pmc_id = None
        for article_id in article_elem.findall(".//ArticleId"):
            if article_id.get("IdType") == "pmc":
                pmc_id = article_id.text
                break

        # MeSH terms
        mesh_terms = []
        for mesh_elem in article_elem.findall(".//MeshHeading/DescriptorName"):
            if mesh_elem.text:
                mesh_terms.append(mesh_elem.text)

        # Keywords
        keywords = []
        for kw_elem in article.findall(".//Keyword"):
            if kw_elem.text:
                keywords.append(kw_elem.text)

        # Article type
        article_type = None
        pub_type_elem = article.find(".//PublicationType")
        if pub_type_elem is not None:
            pub_type = pub_type_elem.text.lower()
            if "review" in pub_type:
                if "systematic" in pub_type:
                    article_type = ArticleType.SYSTEMATIC_REVIEW
                else:
                    article_type = ArticleType.REVIEW
            elif "clinical trial" in pub_type:
                article_type = ArticleType.CLINICAL_TRIAL
            elif "meta-analysis" in pub_type:
                article_type = ArticleType.META_ANALYSIS
            elif "case report" in pub_type:
                article_type = ArticleType.CASE_REPORT

        return Paper(
            pmid=pmid,
            doi=doi,
            pmc_id=pmc_id,
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            volume=volume,
            issue=issue,
            pages=pages,
            abstract=abstract,
            keywords=keywords,
            mesh_terms=mesh_terms,
            article_type=article_type,
            publication_date=pub_date,
        )

    async def get_articles(self, pmids: list[str]) -> list[Paper]:
        """
        Get multiple articles in batch.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of Paper objects
        """
        papers = []
        for pmid in pmids:
            paper = await self.get_article(pmid)
            if paper:
                papers.append(paper)
        return papers

    async def get_full_text(self, pmc_id: str) -> Optional[str]:
        """
        Get full text from PubMed Central.

        Args:
            pmc_id: PMC ID (without 'PMC' prefix)

        Returns:
            Full text or None if not available
        """
        await self._rate_limit()

        # Clean PMC ID
        pmc_id = pmc_id.replace("PMC", "")

        params = self._build_params(
            db="pmc",
            id=pmc_id,
            retmode="xml",
        )

        url = f"{self.BASE_URL}/efetch.fcgi"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            # Parse XML and extract text
            root = ET.fromstring(response.text)

            # Extract all text from body
            body = root.find(".//body")
            if body is not None:
                return self._extract_text(body)

            return None

        except Exception as e:
            print(f"Error fetching full text for PMC{pmc_id}: {e}")
            return None

    def _extract_text(self, elem: ET.Element) -> str:
        """Recursively extract text from XML element."""
        text_parts = []

        if elem.text:
            text_parts.append(elem.text.strip())

        for child in elem:
            child_text = self._extract_text(child)
            if child_text:
                text_parts.append(child_text)

            if child.tail:
                text_parts.append(child.tail.strip())

        return " ".join(filter(None, text_parts))

    async def export_citation(
        self,
        pmid: str,
        format: str = "ris",
    ) -> str:
        """
        Export citation in various formats.

        Args:
            pmid: PubMed ID
            format: Export format (ris, bibtex, medline)

        Returns:
            Formatted citation string
        """
        await self._rate_limit()

        format_map = {
            "ris": "ris",
            "bibtex": "bibtex",
            "medline": "medline",
        }

        params = self._build_params(
            db="pubmed",
            id=pmid,
            rettype=format_map.get(format, "ris"),
            retmode="text",
        )

        url = f"{self.BASE_URL}/efetch.fcgi"
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        return response.text

    async def get_related(
        self,
        pmid: str,
        max_results: int = 10,
    ) -> list[str]:
        """
        Get related articles.

        Args:
            pmid: PubMed ID
            max_results: Maximum results

        Returns:
            List of related PMIDs
        """
        await self._rate_limit()

        params = self._build_params(
            dbfrom="pubmed",
            db="pubmed",
            id=pmid,
            retmax=max_results,
        )

        url = f"{self.BASE_URL}/elink.fcgi"
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.text)
        pmids = [id_elem.text for id_elem in root.findall(".//Link/Id")]

        return pmids

    async def get_citations(self, pmid: str) -> int:
        """
        Get citation count (from PMC).

        Args:
            pmid: PubMed ID

        Returns:
            Number of citations
        """
        await self._rate_limit()

        params = self._build_params(
            dbfrom="pubmed",
            db="pmc",
            id=pmid,
            linkname="pubmed_pmc_refs",
        )

        url = f"{self.BASE_URL}/elink.fcgi"
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.text)
        citations = root.findall(".//Link/Id")

        return len(citations)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_pubmed_client: Optional[PubMedClient] = None


def get_pubmed_client(
    api_key: Optional[str] = None,
    email: Optional[str] = None,
) -> PubMedClient:
    """Get the default PubMed client instance."""
    global _pubmed_client
    if _pubmed_client is None:
        _pubmed_client = PubMedClient(api_key=api_key, email=email)
    return _pubmed_client
