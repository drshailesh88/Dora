"""
Formatting service - Main orchestration for rich answer generation.

This module provides the main service for transforming RAG query results
into rich, formatted medical answers.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import (
    RichAnswer,
    Section,
    Table,
    DecisionTree,
    Callout,
    DrugCard,
    CalculatorResult,
    Citation,
    EvidenceBadge,
    QuickAction,
    SourceType,
)
from .evidence import EvidenceGrader, create_evidence_badge
from .sections import (
    SectionBuilder,
    create_overview_section,
    create_mechanism_section,
    create_dosing_section,
    create_side_effects_section,
    create_interactions_section,
    create_references_section,
    organize_content_into_sections,
)
from .tables import TableGenerator
from .callouts import CalloutBuilder, extract_callouts_from_text
from .cards import CardBuilder
from .algorithms import AlgorithmBuilder
from .renderer import render_to_format


class FormattingService:
    """Service for transforming RAG outputs into rich formatted answers."""

    def __init__(self):
        """Initialize formatting service."""
        self.table_generator = TableGenerator()
        self.evidence_grader = EvidenceGrader()

    def format_rag_response(
        self,
        query: str,
        raw_answer: str,
        retrieved_docs: List[Dict[str, Any]],
        confidence_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RichAnswer:
        """
        Transform RAG response into rich formatted answer.

        Args:
            query: Original user query
            raw_answer: Generated answer text
            retrieved_docs: Retrieved documents with metadata
            confidence_score: Model confidence score
            metadata: Additional metadata

        Returns:
            Rich formatted answer
        """
        # Extract citations from retrieved docs
        citations = self._extract_citations(retrieved_docs)

        # Grade overall evidence
        overall_evidence = create_evidence_badge(citations, confidence_score)

        # Extract summary (first paragraph or first 200 chars)
        summary = self._extract_summary(raw_answer)

        # Organize content into sections
        sections = self._organize_sections(raw_answer, citations)

        # Extract callouts from content
        callouts = self._extract_callouts(raw_answer)

        # Extract tables if present
        tables = self._extract_tables(raw_answer)

        # Extract drug information if query is about medication
        drug_cards = self._extract_drug_cards(query, raw_answer)

        # Generate quick actions
        quick_actions = self._generate_quick_actions(query, sections)

        return RichAnswer(
            query=query,
            summary=summary,
            sections=sections,
            tables=tables,
            decision_trees=[],  # Extracted separately if needed
            callouts=callouts,
            drug_cards=drug_cards,
            calculator_results=[],  # Added separately for calculator queries
            citations=citations,
            overall_evidence=overall_evidence,
            quick_actions=quick_actions,
            metadata=metadata or {},
            generated_at=datetime.utcnow(),
        )

    def format_drug_query(
        self,
        drug_name: str,
        raw_answer: str,
        retrieved_docs: List[Dict[str, Any]],
        confidence_score: float = 0.0,
    ) -> RichAnswer:
        """
        Format answer for drug information query.

        Args:
            drug_name: Name of the drug
            raw_answer: Generated answer text
            retrieved_docs: Retrieved documents
            confidence_score: Model confidence

        Returns:
            Rich formatted answer with drug card
        """
        # Extract citations
        citations = self._extract_citations(retrieved_docs)

        # Grade evidence
        evidence = create_evidence_badge(citations, confidence_score)

        # Create drug card
        drug_card = self._create_drug_card_from_text(drug_name, raw_answer, evidence)

        # Create sections
        sections = [
            create_overview_section(self._extract_summary(raw_answer), evidence),
            create_mechanism_section(
                self._extract_section_content(raw_answer, "mechanism")
            ),
            create_dosing_section(self._extract_section_content(raw_answer, "dosing")),
            create_side_effects_section(
                self._extract_list(raw_answer, "common side effects"),
                self._extract_list(raw_answer, "serious side effects"),
            ),
            create_interactions_section(
                self._extract_list(raw_answer, "drug interactions")
            ),
            create_references_section([c.format_apa() for c in citations]),
        ]

        # Extract warnings as callouts
        callouts = []
        if "black box" in raw_answer.lower():
            callouts.append(
                CalloutBuilder.warning(
                    title=f"BLACK BOX WARNING - {drug_name}",
                    content=self._extract_section_content(raw_answer, "black box"),
                    severity="critical",
                )
            )

        return RichAnswer(
            query=f"Information about {drug_name}",
            summary=self._extract_summary(raw_answer),
            sections=sections,
            callouts=callouts,
            drug_cards=[drug_card],
            citations=citations,
            overall_evidence=evidence,
        )

    def format_calculator_result(
        self,
        calculator_name: str,
        result: CalculatorResult,
        context: Optional[str] = None,
    ) -> RichAnswer:
        """
        Format calculator result as rich answer.

        Args:
            calculator_name: Name of the calculator
            result: Calculator result
            context: Optional context/explanation

        Returns:
            Rich formatted answer
        """
        summary = f"{calculator_name}: {result.result_value} - {result.interpretation}"

        sections = [
            create_overview_section(summary, result.evidence),
        ]

        if context:
            sections.append(
                SectionBuilder("explanation", "Explanation", level=2)
                .add_content(context)
                .build()
            )

        # Add recommendations as section
        if result.recommendations:
            rec_section = (
                SectionBuilder("recommendations", "Recommendations", level=2)
                .add_list(result.recommendations)
                .build()
            )
            sections.append(rec_section)

        return RichAnswer(
            query=f"{calculator_name} calculation",
            summary=summary,
            sections=sections,
            calculator_results=[result],
            citations=result.citations or [],
            overall_evidence=result.evidence,
        )

    def add_decision_tree(
        self, answer: RichAnswer, algorithm: DecisionTree
    ) -> RichAnswer:
        """
        Add decision tree to existing answer.

        Args:
            answer: Existing rich answer
            algorithm: Decision tree to add

        Returns:
            Updated answer
        """
        answer.decision_trees.append(algorithm)
        return answer

    def add_comparison_table(
        self,
        answer: RichAnswer,
        items: List[Dict[str, Any]],
        table_type: str = "drug_comparison",
    ) -> RichAnswer:
        """
        Add comparison table to answer.

        Args:
            answer: Existing rich answer
            items: Items to compare
            table_type: Type of table (drug_comparison, differential, etc.)

        Returns:
            Updated answer
        """
        if table_type == "drug_comparison":
            table = self.table_generator.create_drug_comparison_table(items)
        elif table_type == "differential":
            table = self.table_generator.create_differential_diagnosis_table(items)
        else:
            # Generic comparison
            from .tables import create_quick_comparison

            table = create_quick_comparison(
                [item.get("name", f"Item {i}") for i, item in enumerate(items)],
                self._extract_properties_from_items(items),
                title="Comparison",
            )

        answer.tables.append(table)
        return answer

    # Private helper methods

    def _extract_citations(self, retrieved_docs: List[Dict[str, Any]]) -> List[Citation]:
        """Extract citations from retrieved documents."""
        citations = []

        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})

            citation = Citation(
                id=doc.get("id", f"ref_{len(citations) + 1}"),
                title=metadata.get("title", "Unknown Source"),
                authors=metadata.get("authors"),
                journal=metadata.get("journal"),
                year=metadata.get("year"),
                doi=metadata.get("doi"),
                pmid=metadata.get("pmid"),
                url=metadata.get("url"),
                source_type=self._infer_source_type(metadata),
                snippet=doc.get("text", "")[:500],  # First 500 chars
            )

            citations.append(citation)

        return citations

    def _infer_source_type(self, metadata: Dict[str, Any]) -> SourceType:
        """Infer source type from metadata."""
        title = metadata.get("title", "").lower()

        if "meta-analysis" in title or "meta analysis" in title:
            return SourceType.META_ANALYSIS
        elif "systematic review" in title:
            return SourceType.SYSTEMATIC_REVIEW
        elif "randomized" in title or "rct" in title:
            return SourceType.RCT
        elif "guideline" in title:
            return SourceType.GUIDELINE
        elif metadata.get("pmid"):
            return SourceType.OBSERVATIONAL
        else:
            return SourceType.TEXTBOOK

    def _extract_summary(self, text: str, max_length: int = 200) -> str:
        """Extract summary from text."""
        # Get first paragraph
        paragraphs = text.split("\n\n")
        if paragraphs:
            summary = paragraphs[0].strip()
            if len(summary) <= max_length:
                return summary
            else:
                return summary[:max_length] + "..."

        # Fallback: first N chars
        return text[:max_length].strip() + "..."

    def _organize_sections(
        self, text: str, citations: List[Citation]
    ) -> List[Section]:
        """Organize text into logical sections."""
        # Try to auto-detect sections
        sections = organize_content_into_sections(text)

        # If no sections detected, create single overview
        if not sections:
            sections = [create_overview_section(text)]

        # Add references section
        if citations:
            sections.append(
                create_references_section([c.format_apa() for c in citations])
            )

        return sections

    def _extract_callouts(self, text: str) -> List[Callout]:
        """Extract callouts from text."""
        return extract_callouts_from_text(text)

    def _extract_tables(self, text: str) -> List[Table]:
        """Extract tables from markdown text."""
        # Simple markdown table parser
        tables = []
        lines = text.split("\n")

        current_table_lines = []
        in_table = False

        for line in lines:
            if "|" in line:
                in_table = True
                current_table_lines.append(line)
            elif in_table:
                # End of table
                if current_table_lines:
                    table = self._parse_markdown_table(current_table_lines)
                    if table:
                        tables.append(table)
                    current_table_lines = []
                    in_table = False

        return tables

    def _parse_markdown_table(self, lines: List[str]) -> Optional[Table]:
        """Parse markdown table lines into Table object."""
        if len(lines) < 2:
            return None

        # Extract headers
        headers = [h.strip() for h in lines[0].split("|") if h.strip()]

        # Skip separator line
        # Parse rows
        from .models import TableRow, TableCell

        rows = []
        for line in lines[2:]:  # Skip header and separator
            cells_text = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells_text) == len(headers):
                cells = [TableCell(value=text) for text in cells_text]
                rows.append(TableRow(cells=cells))

        return Table(
            id=f"table_{len(rows)}",
            headers=headers,
            rows=rows,
        )

    def _extract_drug_cards(self, query: str, text: str) -> List[DrugCard]:
        """Extract drug cards if query is about medication."""
        # Check if query is about a drug
        drug_keywords = [
            "medication",
            "drug",
            "dosing",
            "prescription",
            "tablet",
            "capsule",
        ]

        if not any(keyword in query.lower() for keyword in drug_keywords):
            return []

        # Try to extract drug name from query
        # This is simplified - in production, use NER
        return []

    def _create_drug_card_from_text(
        self, drug_name: str, text: str, evidence: EvidenceBadge
    ) -> DrugCard:
        """Create drug card from extracted text."""
        return CardBuilder.create_drug_card(
            name=drug_name,
            generic_name=self._extract_section_content(text, "generic"),
            drug_class=self._extract_section_content(text, "class"),
            mechanism=self._extract_section_content(text, "mechanism"),
            indications=self._extract_list(text, "indication"),
            dosing=self._extract_section_content(text, "dosing"),
            evidence=evidence,
        )

    def _extract_section_content(self, text: str, section_keyword: str) -> Optional[str]:
        """Extract content for specific section."""
        # Simple keyword-based extraction
        lines = text.split("\n")

        for i, line in enumerate(lines):
            if section_keyword.lower() in line.lower() and (
                line.startswith("#") or ":" in line
            ):
                # Found section, get content
                content_lines = []
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("#"):
                        break
                    content_lines.append(lines[j])

                return "\n".join(content_lines).strip()

        return None

    def _extract_list(self, text: str, list_keyword: str) -> List[str]:
        """Extract list items from text."""
        items = []
        lines = text.split("\n")

        in_list = False
        for line in lines:
            if list_keyword.lower() in line.lower():
                in_list = True
                continue

            if in_list:
                if line.startswith("- ") or line.startswith("* "):
                    items.append(line.lstrip("-* ").strip())
                elif line.strip() and not line.startswith(" "):
                    break  # End of list

        return items

    def _generate_quick_actions(
        self, query: str, sections: List[Section]
    ) -> List[QuickAction]:
        """Generate contextual quick actions."""
        actions = []

        # Copy to clipboard
        actions.append(
            QuickAction(
                label="Copy to EMR",
                action_type="copy",
                icon="📋",
                primary=True,
            )
        )

        # Navigate to calculator if relevant
        if any(
            keyword in query.lower()
            for keyword in ["calculate", "score", "risk", "creatinine"]
        ):
            actions.append(
                QuickAction(
                    label="Open Calculator",
                    action_type="calculate",
                    icon="🧮",
                )
            )

        return actions

    def _extract_properties_from_items(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Extract common properties from items for comparison table."""
        if not items:
            return {}

        # Get all keys from first item
        keys = list(items[0].keys())
        properties = {}

        for key in keys:
            if key != "name":  # Skip name as it's used for rows
                values = [str(item.get(key, "-")) for item in items]
                properties[key.replace("_", " ").title()] = values

        return properties


# Convenience functions


def format_query_response(
    query: str,
    answer: str,
    retrieved_docs: List[Dict[str, Any]],
    confidence: float = 0.0,
) -> RichAnswer:
    """
    Quick function to format a query response.

    Args:
        query: User query
        answer: Generated answer
        retrieved_docs: Retrieved documents
        confidence: Confidence score

    Returns:
        Rich formatted answer
    """
    service = FormattingService()
    return service.format_rag_response(query, answer, retrieved_docs, confidence)
