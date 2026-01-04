#!/usr/bin/env python3
"""
Academic Writing Module Demo

Demonstrates the key features of the academic writing module.
"""

import asyncio
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.academic import (
    get_academic_service,
    CitationStyle,
    StudyType,
)


async def demo_literature_search():
    """Demo: Search PubMed for literature."""
    print("\n" + "="*60)
    print("1. LITERATURE SEARCH DEMO")
    print("="*60)

    service = get_academic_service()

    # Search for papers
    print("\nSearching PubMed for 'diabetes treatment'...")
    papers = await service.search_literature(
        query="diabetes treatment",
        max_results=5,
        date_from="2023",
    )

    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}...")
        print(f"   Journal: {paper.journal} ({paper.year})")
        print(f"   PMID: {paper.pmid}")
        if paper.doi:
            print(f"   DOI: {paper.doi}")

    return papers


async def demo_citations(papers):
    """Demo: Generate citations in different styles."""
    print("\n" + "="*60)
    print("2. CITATION GENERATION DEMO")
    print("="*60)

    if not papers:
        print("No papers available for citation demo")
        return

    paper = papers[0]
    print(f"\nGenerating citations for:\n{paper.title}\n")

    for style in [CitationStyle.AMA, CitationStyle.VANCOUVER, CitationStyle.APA]:
        print(f"\n{style.value.upper()} Style:")
        print(f"{paper.short_citation(style)}")


async def demo_bibliography(papers):
    """Demo: Generate bibliography."""
    print("\n" + "="*60)
    print("3. BIBLIOGRAPHY GENERATION DEMO")
    print("="*60)

    service = get_academic_service(citation_style=CitationStyle.VANCOUVER)

    # Add citations
    for paper in papers[:3]:
        service.add_citation(paper)

    # Generate bibliography
    bibliography = service.generate_bibliography()

    print("\nGenerated Bibliography (Vancouver style):\n")
    print(bibliography)

    # Export as BibTeX
    print("\n\nBibTeX Export:")
    print("-" * 60)
    bibtex = service.export_bibliography(papers[:2], format="bibtex")
    print(bibtex[:500] + "..." if len(bibtex) > 500 else bibtex)


async def demo_ai_writing():
    """Demo: AI-assisted writing."""
    print("\n" + "="*60)
    print("4. AI WRITING ASSISTANCE DEMO")
    print("="*60)

    service = get_academic_service()

    # Generate structured abstract
    print("\nGenerating structured abstract...")

    context = {
        "objective": "To evaluate the efficacy of a new diabetes medication in reducing HbA1c levels",
        "design": "Randomized, double-blind, placebo-controlled trial",
        "setting": "Multi-center study across 50 hospitals",
        "participants": "500 adults with type 2 diabetes (HbA1c >7%)",
        "intervention": "New medication vs placebo for 12 weeks",
        "results": "Mean HbA1c reduction of 1.5% in treatment group vs 0.2% in placebo (p<0.001)",
        "conclusion": "The medication significantly reduces HbA1c and is well-tolerated",
    }

    abstract = await service.generate_abstract(
        title="Efficacy of Novel GLP-1 Agonist in Type 2 Diabetes",
        study_type=StudyType.RCT,
        context=context,
        max_words=250,
        structured=True,
    )

    print("\nGenerated Abstract:")
    print("-" * 60)
    print(abstract)
    print("-" * 60)
    print(f"Word count: {len(abstract.split())} words")


async def demo_manuscript_workflow():
    """Demo: Complete manuscript workflow."""
    print("\n" + "="*60)
    print("5. COMPLETE MANUSCRIPT WORKFLOW")
    print("="*60)

    service = get_academic_service(citation_style=CitationStyle.AMA)

    # 1. Search for relevant papers
    print("\n1. Searching for background literature...")
    papers = await service.search_literature(
        query="hypertension treatment guidelines",
        max_results=3,
    )
    print(f"   Found {len(papers)} papers")

    # 2. Create manuscript
    print("\n2. Creating manuscript...")
    manuscript = service.create_manuscript(
        title="Treatment Outcomes in Hypertensive Patients",
        study_type=StudyType.COHORT,
        citation_style=CitationStyle.AMA,
    )
    print(f"   Manuscript created: {manuscript.title}")

    # 3. Add citations
    print("\n3. Adding citations...")
    for paper in papers:
        citation = manuscript.add_citation(paper)
        print(f"   Added: {citation.inline(CitationStyle.AMA)} {paper.title[:50]}...")

    # 4. Generate bibliography
    print("\n4. Generating bibliography...")
    bibliography = service.generate_bibliography(
        citations=manuscript.citations,
        style=CitationStyle.AMA,
    )
    print(f"   Bibliography contains {len(manuscript.citations)} references")

    # 5. Display sample
    print("\n5. Sample Bibliography Entries:")
    print("-" * 60)
    for line in bibliography.split('\n')[:5]:  # Show first 5 lines
        print(line)
    print("...")

    return manuscript


async def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("ACADEMIC WRITING MODULE DEMONSTRATION")
    print("="*60)

    try:
        # Demo 1: Literature Search
        papers = await demo_literature_search()

        # Demo 2: Citations
        await demo_citations(papers)

        # Demo 3: Bibliography
        await demo_bibliography(papers)

        # Demo 4: AI Writing (requires LLM)
        # Uncomment if you have API keys configured
        # await demo_ai_writing()

        # Demo 5: Complete Workflow
        await demo_manuscript_workflow()

        print("\n" + "="*60)
        print("DEMO COMPLETE!")
        print("="*60)
        print("\nAll features demonstrated successfully.")
        print("See ACADEMIC_MODULE_SUMMARY.md for full documentation.")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        print("\nNote: Some demos require:")
        print("  - NCBI_API_KEY and NCBI_EMAIL in .env")
        print("  - ANTHROPIC_API_KEY or OPENAI_API_KEY for AI writing")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
