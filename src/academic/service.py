"""
Academic Writing Service

Main orchestration service for academic writing features.
Integrates PubMed search, citation management, and AI writing assistance.
"""

import os
from typing import Optional

from .bibliography import BibliographyGenerator, merge_bibliographies
from .citation import CitationManager
from .models import (
    Citation,
    CitationStyle,
    Manuscript,
    ManuscriptSection,
    Paper,
    StudyType,
)
from .pubmed import PubMedClient, get_pubmed_client
from .writing import AcademicWritingAssistant, get_writing_assistant


class AcademicService:
    """
    Main service for academic writing functionality.

    Features:
    - Literature search via PubMed
    - Citation and bibliography management
    - AI-assisted writing
    - Manuscript management
    """

    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        pubmed_email: Optional[str] = None,
        default_citation_style: CitationStyle = CitationStyle.AMA,
        prefer_local_llm: bool = False,
    ):
        """
        Initialize academic service.

        Args:
            pubmed_api_key: NCBI API key
            pubmed_email: Contact email for NCBI
            default_citation_style: Default citation style
            prefer_local_llm: Prefer local LLM for writing assistance
        """
        # Get API key and email from environment if not provided
        self.pubmed_api_key = pubmed_api_key or os.getenv("NCBI_API_KEY")
        self.pubmed_email = pubmed_email or os.getenv("NCBI_EMAIL")

        # Initialize components
        self.pubmed = PubMedClient(
            api_key=self.pubmed_api_key,
            email=self.pubmed_email,
        )

        self.citation_style = default_citation_style
        self.prefer_local_llm = prefer_local_llm

        # Component instances (created per-manuscript or per-request)
        self.citation_manager: Optional[CitationManager] = None
        self.bibliography_generator: Optional[BibliographyGenerator] = None
        self.writing_assistant: Optional[AcademicWritingAssistant] = None

    def get_citation_manager(
        self,
        style: Optional[CitationStyle] = None,
    ) -> CitationManager:
        """Get or create citation manager."""
        use_style = style or self.citation_style

        if self.citation_manager is None or self.citation_manager.style != use_style:
            self.citation_manager = CitationManager(style=use_style)

        return self.citation_manager

    def get_bibliography_generator(
        self,
        style: Optional[CitationStyle] = None,
    ) -> BibliographyGenerator:
        """Get or create bibliography generator."""
        use_style = style or self.citation_style

        if self.bibliography_generator is None or self.bibliography_generator.style != use_style:
            self.bibliography_generator = BibliographyGenerator(style=use_style)

        return self.bibliography_generator

    def get_writing_assistant(self) -> AcademicWritingAssistant:
        """Get or create writing assistant."""
        if self.writing_assistant is None:
            self.writing_assistant = AcademicWritingAssistant(
                prefer_local=self.prefer_local_llm
            )

        return self.writing_assistant

    # PubMed Search Operations

    async def search_literature(
        self,
        query: str,
        max_results: int = 20,
        **kwargs,
    ) -> list[Paper]:
        """
        Search PubMed for literature.

        Args:
            query: Search query
            max_results: Maximum results
            **kwargs: Additional search parameters

        Returns:
            List of papers
        """
        pmids = await self.pubmed.search(query, max_results=max_results, **kwargs)
        papers = await self.pubmed.get_articles(pmids)
        return papers

    async def get_paper_by_pmid(self, pmid: str) -> Optional[Paper]:
        """
        Get paper details by PMID.

        Args:
            pmid: PubMed ID

        Returns:
            Paper object
        """
        return await self.pubmed.get_article(pmid)

    async def get_related_papers(
        self,
        pmid: str,
        max_results: int = 10,
    ) -> list[Paper]:
        """
        Get papers related to a given PMID.

        Args:
            pmid: PubMed ID
            max_results: Maximum results

        Returns:
            List of related papers
        """
        related_pmids = await self.pubmed.get_related(pmid, max_results=max_results)
        papers = await self.pubmed.get_articles(related_pmids)
        return papers

    # Citation Management

    def add_citation(
        self,
        paper: Paper,
        context: Optional[str] = None,
        style: Optional[CitationStyle] = None,
    ) -> Citation:
        """
        Add a paper as a citation.

        Args:
            paper: Paper to cite
            context: Context where cited
            style: Citation style

        Returns:
            Citation object
        """
        manager = self.get_citation_manager(style)
        return manager.add_paper(paper, context=context)

    def get_inline_citation(
        self,
        paper: Paper,
        style: Optional[CitationStyle] = None,
    ) -> str:
        """
        Get inline citation for a paper.

        Args:
            paper: Paper being cited
            style: Citation style

        Returns:
            Inline citation string
        """
        manager = self.get_citation_manager(style)
        return manager.get_inline_citation(paper, style=style)

    def generate_bibliography(
        self,
        citations: Optional[list[Citation]] = None,
        style: Optional[CitationStyle] = None,
    ) -> str:
        """
        Generate formatted bibliography.

        Args:
            citations: List of citations (uses manager's if not provided)
            style: Citation style

        Returns:
            Formatted bibliography text
        """
        generator = self.get_bibliography_generator(style)

        if citations is None:
            manager = self.get_citation_manager(style)
            citations = list(manager.citations.values())

        return generator.generate(citations, style=style)

    def export_bibliography(
        self,
        papers: list[Paper],
        format: str = "ris",
    ) -> str:
        """
        Export bibliography in specified format.

        Args:
            papers: List of papers
            format: Export format (ris, bibtex, endnote)

        Returns:
            Formatted export string
        """
        generator = self.get_bibliography_generator()

        if format == "ris":
            return generator.export_ris(papers)
        elif format == "bibtex":
            return generator.export_bibtex(papers)
        elif format == "endnote":
            return generator.export_endnote(papers)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # Writing Assistance

    async def generate_abstract(
        self,
        title: str,
        study_type: StudyType,
        context: dict,
        max_words: int = 250,
        structured: bool = True,
    ) -> str:
        """
        Generate abstract for a paper.

        Args:
            title: Paper title
            study_type: Type of study
            context: Context with findings, methods, etc.
            max_words: Maximum words
            structured: Use structured format

        Returns:
            Generated abstract text
        """
        assistant = self.get_writing_assistant()
        result = await assistant.generate_abstract(
            title, study_type, context, max_words, structured
        )
        return result.content

    async def generate_methods(
        self,
        study_type: StudyType,
        context: dict,
        max_words: Optional[int] = None,
    ) -> str:
        """
        Generate methods section.

        Args:
            study_type: Type of study
            context: Study details
            max_words: Maximum words

        Returns:
            Generated methods text
        """
        assistant = self.get_writing_assistant()
        result = await assistant.generate_methods(study_type, context, max_words)
        return result.content

    async def generate_results(
        self,
        context: dict,
        max_words: Optional[int] = None,
    ) -> str:
        """
        Generate results section.

        Args:
            context: Study results
            max_words: Maximum words

        Returns:
            Generated results text
        """
        assistant = self.get_writing_assistant()
        result = await assistant.generate_results(context, max_words)
        return result.content

    async def generate_discussion(
        self,
        context: dict,
        max_words: Optional[int] = None,
    ) -> str:
        """
        Generate discussion section.

        Args:
            context: Results and implications
            max_words: Maximum words

        Returns:
            Generated discussion text
        """
        assistant = self.get_writing_assistant()
        result = await assistant.generate_discussion(context, max_words)
        return result.content

    async def improve_text(
        self,
        section: ManuscriptSection,
        text: str,
        improvement_type: str = "clarity",
    ) -> str:
        """
        Improve existing text.

        Args:
            section: Section type
            text: Current text
            improvement_type: Type of improvement

        Returns:
            Improved text
        """
        assistant = self.get_writing_assistant()
        result = await assistant.improve_section(section, text, improvement_type)
        return result.content

    # Manuscript Management

    def create_manuscript(
        self,
        title: str,
        study_type: Optional[StudyType] = None,
        citation_style: Optional[CitationStyle] = None,
    ) -> Manuscript:
        """
        Create a new manuscript.

        Args:
            title: Manuscript title
            study_type: Type of study
            citation_style: Citation style

        Returns:
            New manuscript object
        """
        use_style = citation_style or self.citation_style

        manuscript = Manuscript(
            title=title,
            study_type=study_type,
            citation_style=use_style,
        )

        return manuscript

    def save_manuscript(self, manuscript: Manuscript, filepath: str) -> None:
        """
        Save manuscript to file.

        Args:
            manuscript: Manuscript to save
            filepath: Output file path
        """
        import json

        with open(filepath, 'w') as f:
            # Convert to dict and save as JSON
            data = manuscript.model_dump()
            json.dump(data, f, indent=2, default=str)

    def load_manuscript(self, filepath: str) -> Manuscript:
        """
        Load manuscript from file.

        Args:
            filepath: Input file path

        Returns:
            Loaded manuscript
        """
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)
            return Manuscript(**data)

    # Integration with Dora's RAG system

    async def search_with_rag(
        self,
        query: str,
        include_pubmed: bool = True,
        max_pubmed_results: int = 5,
    ) -> dict:
        """
        Search using both Dora's RAG and PubMed.

        Args:
            query: Search query
            include_pubmed: Whether to include PubMed results
            max_pubmed_results: Max PubMed results

        Returns:
            Combined results from RAG and PubMed
        """
        results = {
            "rag_results": [],
            "pubmed_results": [],
        }

        # PubMed search
        if include_pubmed:
            papers = await self.search_literature(query, max_results=max_pubmed_results)
            results["pubmed_results"] = papers

        # TODO: Integrate with Dora's RAG pipeline
        # from src.core.pipeline import MedicalQueryPipeline
        # pipeline = MedicalQueryPipeline()
        # answer = await pipeline.query(query)
        # results["rag_results"] = answer

        return results

    # Notification integration

    async def notify_new_papers(
        self,
        user_id: str,
        topic: str,
        papers: list[Paper],
    ) -> None:
        """
        Notify user about new papers matching their interests.

        Args:
            user_id: User ID
            topic: Topic of interest
            papers: New papers found
        """
        # TODO: Integrate with notification service
        # from src.notifications import get_notification_service
        # notification_service = get_notification_service()
        # await notification_service.send_new_papers_alert(user_id, topic, papers)
        pass

    async def close(self) -> None:
        """Close all clients."""
        await self.pubmed.close()


# Singleton instance
_academic_service: Optional[AcademicService] = None


def get_academic_service(
    pubmed_api_key: Optional[str] = None,
    pubmed_email: Optional[str] = None,
    citation_style: CitationStyle = CitationStyle.AMA,
    prefer_local_llm: bool = False,
) -> AcademicService:
    """Get the default academic service instance."""
    global _academic_service
    if _academic_service is None:
        _academic_service = AcademicService(
            pubmed_api_key=pubmed_api_key,
            pubmed_email=pubmed_email,
            default_citation_style=citation_style,
            prefer_local_llm=prefer_local_llm,
        )
    return _academic_service
