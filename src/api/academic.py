"""
Academic Writing API Endpoints

REST API for academic writing, literature search, and citation management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user
from src.academic import (
    AcademicService,
    CitationStyle,
    ManuscriptSection,
    Paper,
    StudyType,
    get_academic_service,
)

router = APIRouter(prefix="/api/v1/academic", tags=["academic"])


# Request/Response models
class SearchRequest(BaseModel):
    """Request for PubMed search."""

    query: str = Field(..., min_length=2, description="Search query")
    max_results: int = Field(20, ge=1, le=100, description="Maximum results")
    sort: str = Field("relevance", description="Sort order")
    date_from: Optional[str] = Field(None, description="Start date (YYYY or YYYY/MM/DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY or YYYY/MM/DD)")
    article_type: Optional[str] = Field(None, description="Article type filter")


class SearchResponse(BaseModel):
    """Response with search results."""

    success: bool
    papers: list[dict] = Field(default_factory=list)
    count: int = 0
    query: str


class ArticleRequest(BaseModel):
    """Request for article details."""

    pmid: str = Field(..., description="PubMed ID")


class ArticleResponse(BaseModel):
    """Response with article details."""

    success: bool
    paper: Optional[dict] = None
    error: Optional[str] = None


class CitationRequest(BaseModel):
    """Request to generate citation."""

    pmid: Optional[str] = None
    paper: Optional[dict] = None
    style: CitationStyle = CitationStyle.AMA
    inline: bool = Field(False, description="Generate inline citation marker")


class CitationResponse(BaseModel):
    """Response with formatted citation."""

    success: bool
    citation: Optional[str] = None
    inline_marker: Optional[str] = None
    citation_number: Optional[int] = None
    error: Optional[str] = None


class BibliographyRequest(BaseModel):
    """Request to generate bibliography."""

    pmids: list[str] = Field(default_factory=list)
    papers: list[dict] = Field(default_factory=list)
    style: CitationStyle = CitationStyle.AMA
    format: str = Field("text", description="Output format (text, ris, bibtex)")


class BibliographyResponse(BaseModel):
    """Response with formatted bibliography."""

    success: bool
    bibliography: Optional[str] = None
    format: str
    count: int = 0
    error: Optional[str] = None


class WritingAssistRequest(BaseModel):
    """Request for AI writing assistance."""

    section: ManuscriptSection
    title: Optional[str] = None
    study_type: Optional[StudyType] = None
    context: dict = Field(default_factory=dict)
    max_words: Optional[int] = None
    structured: bool = Field(True, description="Use structured format (for abstracts)")


class WritingAssistResponse(BaseModel):
    """Response with AI-generated text."""

    success: bool
    section: str
    content: Optional[str] = None
    word_count: int = 0
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class ImproveTextRequest(BaseModel):
    """Request to improve existing text."""

    section: ManuscriptSection
    text: str = Field(..., min_length=10)
    improvement_type: str = Field("clarity", description="clarity, conciseness, or grammar")


class RelatedPapersRequest(BaseModel):
    """Request for related papers."""

    pmid: str
    max_results: int = Field(10, ge=1, le=50)


# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search_pubmed(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Search PubMed for medical literature.

    Args:
        request: Search parameters

    Returns:
        List of papers matching the search query
    """
    service = get_academic_service()

    try:
        papers = await service.search_literature(
            query=request.query,
            max_results=request.max_results,
            sort=request.sort,
            date_from=request.date_from,
            date_to=request.date_to,
            article_type=request.article_type,
        )

        # Convert papers to dict
        papers_dict = [p.model_dump() for p in papers]

        return SearchResponse(
            success=True,
            papers=papers_dict,
            count=len(papers),
            query=request.query,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/article/{pmid}", response_model=ArticleResponse)
async def get_article(
    pmid: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed article information by PMID.

    Args:
        pmid: PubMed ID

    Returns:
        Article details including abstract, authors, citations, etc.
    """
    service = get_academic_service()

    try:
        paper = await service.get_paper_by_pmid(pmid)

        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Article {pmid} not found",
            )

        return ArticleResponse(
            success=True,
            paper=paper.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        return ArticleResponse(
            success=False,
            error=str(e),
        )


@router.post("/article/{pmid}/related", response_model=SearchResponse)
async def get_related_papers(
    pmid: str,
    max_results: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    Get papers related to a given PMID.

    Args:
        pmid: PubMed ID
        max_results: Maximum results

    Returns:
        List of related papers
    """
    service = get_academic_service()

    try:
        papers = await service.get_related_papers(pmid, max_results=max_results)

        papers_dict = [p.model_dump() for p in papers]

        return SearchResponse(
            success=True,
            papers=papers_dict,
            count=len(papers),
            query=f"related:{pmid}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get related papers: {str(e)}",
        )


@router.post("/cite", response_model=CitationResponse)
async def generate_citation(
    request: CitationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a formatted citation.

    Args:
        request: Citation request with PMID or paper data

    Returns:
        Formatted citation in specified style
    """
    service = get_academic_service()

    try:
        # Get paper
        if request.pmid:
            paper = await service.get_paper_by_pmid(request.pmid)
            if not paper:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Article {request.pmid} not found",
                )
        elif request.paper:
            paper = Paper(**request.paper)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either pmid or paper data must be provided",
            )

        # Add citation
        citation = service.add_citation(paper, style=request.style)

        # Format citation
        formatted = citation.format(request.style)

        # Generate inline marker if requested
        inline_marker = None
        if request.inline:
            inline_marker = citation.inline(request.style)

        return CitationResponse(
            success=True,
            citation=formatted,
            inline_marker=inline_marker,
            citation_number=citation.citation_number,
        )

    except HTTPException:
        raise
    except Exception as e:
        return CitationResponse(
            success=False,
            error=str(e),
        )


@router.post("/bibliography", response_model=BibliographyResponse)
async def generate_bibliography(
    request: BibliographyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a formatted bibliography.

    Args:
        request: Bibliography request with papers and style

    Returns:
        Formatted bibliography in specified format
    """
    service = get_academic_service()

    try:
        # Get papers
        papers = []

        if request.pmids:
            for pmid in request.pmids:
                paper = await service.get_paper_by_pmid(pmid)
                if paper:
                    papers.append(paper)

        if request.papers:
            for paper_dict in request.papers:
                papers.append(Paper(**paper_dict))

        if not papers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No papers provided",
            )

        # Generate bibliography
        if request.format == "text":
            # Add citations and generate bibliography
            for paper in papers:
                service.add_citation(paper, style=request.style)

            bibliography = service.generate_bibliography(style=request.style)

        elif request.format == "ris":
            bibliography = service.export_bibliography(papers, format="ris")

        elif request.format == "bibtex":
            bibliography = service.export_bibliography(papers, format="bibtex")

        elif request.format == "endnote":
            bibliography = service.export_bibliography(papers, format="endnote")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {request.format}",
            )

        return BibliographyResponse(
            success=True,
            bibliography=bibliography,
            format=request.format,
            count=len(papers),
        )

    except HTTPException:
        raise
    except Exception as e:
        return BibliographyResponse(
            success=False,
            format=request.format,
            error=str(e),
        )


@router.post("/assist", response_model=WritingAssistResponse)
async def writing_assistance(
    request: WritingAssistRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Get AI assistance for academic writing.

    Args:
        request: Writing assistance request

    Returns:
        AI-generated text for the specified section
    """
    service = get_academic_service()

    try:
        # Generate content based on section
        if request.section == ManuscriptSection.ABSTRACT:
            if not request.title or not request.study_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title and study_type required for abstract generation",
                )

            content = await service.generate_abstract(
                title=request.title,
                study_type=request.study_type,
                context=request.context,
                max_words=request.max_words or 250,
                structured=request.structured,
            )

        elif request.section == ManuscriptSection.METHODS:
            if not request.study_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="study_type required for methods generation",
                )

            content = await service.generate_methods(
                study_type=request.study_type,
                context=request.context,
                max_words=request.max_words,
            )

        elif request.section == ManuscriptSection.RESULTS:
            content = await service.generate_results(
                context=request.context,
                max_words=request.max_words,
            )

        elif request.section == ManuscriptSection.DISCUSSION:
            content = await service.generate_discussion(
                context=request.context,
                max_words=request.max_words,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Writing assistance not available for section: {request.section}",
            )

        word_count = len(content.split())

        return WritingAssistResponse(
            success=True,
            section=request.section.value,
            content=content,
            word_count=word_count,
            suggestions=[
                "Review for accuracy and completeness",
                "Add specific citations where appropriate",
                "Adjust tone for target journal",
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        return WritingAssistResponse(
            success=False,
            section=request.section.value,
            error=str(e),
        )


@router.post("/improve", response_model=WritingAssistResponse)
async def improve_text(
    request: ImproveTextRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Improve existing text for clarity, conciseness, or grammar.

    Args:
        request: Text improvement request

    Returns:
        Improved version of the text
    """
    service = get_academic_service()

    try:
        if request.improvement_type not in ["clarity", "conciseness", "grammar"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="improvement_type must be clarity, conciseness, or grammar",
            )

        improved_text = await service.improve_text(
            section=request.section,
            text=request.text,
            improvement_type=request.improvement_type,
        )

        word_count = len(improved_text.split())

        return WritingAssistResponse(
            success=True,
            section=request.section.value,
            content=improved_text,
            word_count=word_count,
            suggestions=[
                f"Text improved for {request.improvement_type}",
                "Compare with original to ensure meaning preserved",
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        return WritingAssistResponse(
            success=False,
            section=request.section.value,
            error=str(e),
        )


@router.get("/styles")
async def get_citation_styles():
    """
    Get list of available citation styles.

    Returns:
        List of supported citation styles
    """
    styles = [
        {
            "id": style.value,
            "name": style.value.upper(),
            "description": _get_style_description(style),
        }
        for style in CitationStyle
    ]

    return {
        "styles": styles,
        "default": CitationStyle.AMA.value,
    }


@router.get("/study-types")
async def get_study_types():
    """
    Get list of available study types.

    Returns:
        List of supported study types
    """
    types = [
        {
            "id": study_type.value,
            "name": study_type.value.replace("_", " ").title(),
        }
        for study_type in StudyType
    ]

    return {"study_types": types}


# Helper functions
def _get_style_description(style: CitationStyle) -> str:
    """Get description for citation style."""
    descriptions = {
        CitationStyle.AMA: "American Medical Association (numbered, widely used in medicine)",
        CitationStyle.VANCOUVER: "Vancouver/ICMJE style (numbered, common in medical journals)",
        CitationStyle.APA: "American Psychological Association (author-year)",
        CitationStyle.IEEE: "IEEE style (numbered, common in engineering)",
        CitationStyle.HARVARD: "Harvard style (author-year)",
        CitationStyle.ICMJE: "International Committee of Medical Journal Editors",
    }
    return descriptions.get(style, "")
