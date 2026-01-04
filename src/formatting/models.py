"""
Rich answer formatting models for medical knowledge display.

This module defines all data models for formatted medical content including
sections, tables, decision trees, callouts, and evidence badges.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EvidenceLevel(str, Enum):
    """Evidence level classification for medical recommendations."""

    A = "A"  # Multiple RCTs or meta-analyses
    B = "B"  # Single RCT or large observational
    C = "C"  # Expert consensus or small studies
    D = "D"  # Expert opinion only
    E = "E"  # Insufficient evidence
    UNKNOWN = "Unknown"


class RecommendationStrength(str, Enum):
    """Strength of clinical recommendation."""

    STRONG = "Strong"
    WEAK = "Weak"
    CONDITIONAL = "Conditional"
    INSUFFICIENT = "Insufficient"


class CalloutType(str, Enum):
    """Types of callout boxes for different alerts."""

    WARNING = "warning"  # Black box warnings, contraindications
    CAUTION = "caution"  # Drug interactions, side effects
    INFO = "info"  # Additional context
    TIP = "tip"  # Clinical pearls
    EVIDENCE = "evidence"  # Supporting studies
    ACTION = "action"  # What to do next


class SourceType(str, Enum):
    """Types of evidence sources."""

    GUIDELINE = "guideline"
    RCT = "rct"
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    OBSERVATIONAL = "observational"
    EXPERT_OPINION = "expert_opinion"
    TEXTBOOK = "textbook"
    DRUG_DATABASE = "drug_database"


class Citation(BaseModel):
    """Formatted reference citation."""

    id: str = Field(..., description="Unique citation identifier")
    title: str = Field(..., description="Article/source title")
    authors: Optional[List[str]] = Field(None, description="List of authors")
    journal: Optional[str] = Field(None, description="Journal name")
    year: Optional[int] = Field(None, description="Publication year")
    doi: Optional[str] = Field(None, description="DOI identifier")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    url: Optional[str] = Field(None, description="Full URL")
    source_type: SourceType = Field(default=SourceType.TEXTBOOK, description="Type of source")
    evidence_level: Optional[EvidenceLevel] = Field(None, description="Evidence level")
    snippet: Optional[str] = Field(None, description="Relevant excerpt")

    def format_apa(self) -> str:
        """Format citation in APA style."""
        parts = []

        if self.authors:
            if len(self.authors) > 6:
                author_str = f"{', '.join(self.authors[:6])}, et al."
            else:
                author_str = ', '.join(self.authors)
            parts.append(author_str)

        if self.year:
            parts.append(f"({self.year})")

        parts.append(self.title)

        if self.journal:
            parts.append(f"{self.journal}.")

        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")
        elif self.url:
            parts.append(self.url)

        return '. '.join(parts)


class EvidenceBadge(BaseModel):
    """Visual indicator of evidence quality."""

    level: EvidenceLevel = Field(..., description="Evidence level A-E")
    strength: Optional[RecommendationStrength] = Field(None, description="Recommendation strength")
    source_count: int = Field(default=0, description="Number of supporting sources")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence 0-1")
    last_updated: Optional[datetime] = Field(None, description="Last evidence review date")

    def get_color(self) -> str:
        """Get badge color based on evidence level."""
        colors = {
            EvidenceLevel.A: "#10b981",  # green
            EvidenceLevel.B: "#3b82f6",  # blue
            EvidenceLevel.C: "#f59e0b",  # amber
            EvidenceLevel.D: "#ef4444",  # red
            EvidenceLevel.E: "#6b7280",  # gray
            EvidenceLevel.UNKNOWN: "#6b7280",
        }
        return colors.get(self.level, "#6b7280")

    def get_description(self) -> str:
        """Get human-readable description."""
        descriptions = {
            EvidenceLevel.A: "Multiple RCTs or meta-analyses",
            EvidenceLevel.B: "Single RCT or large observational study",
            EvidenceLevel.C: "Expert consensus or small studies",
            EvidenceLevel.D: "Expert opinion only",
            EvidenceLevel.E: "Insufficient evidence",
            EvidenceLevel.UNKNOWN: "Evidence level not assessed",
        }
        return descriptions.get(self.level, "Unknown evidence level")


class TableCell(BaseModel):
    """Individual table cell."""

    value: str = Field(..., description="Cell content")
    alignment: Literal["left", "center", "right"] = Field(default="left", description="Text alignment")
    emphasis: bool = Field(default=False, description="Bold/highlight cell")
    color: Optional[str] = Field(None, description="Cell background color")
    tooltip: Optional[str] = Field(None, description="Hover tooltip")


class TableRow(BaseModel):
    """Table row with cells."""

    cells: List[TableCell] = Field(..., description="Row cells")
    is_header: bool = Field(default=False, description="Header row")


class Table(BaseModel):
    """Comparison/dosing table."""

    id: str = Field(..., description="Table identifier")
    title: Optional[str] = Field(None, description="Table title")
    caption: Optional[str] = Field(None, description="Table caption")
    headers: List[str] = Field(..., description="Column headers")
    rows: List[TableRow] = Field(..., description="Table rows")
    sortable: bool = Field(default=True, description="Enable sorting")
    filterable: bool = Field(default=False, description="Enable filtering")
    footer: Optional[str] = Field(None, description="Table footer notes")

    def to_markdown(self) -> str:
        """Convert table to markdown format."""
        lines = []

        if self.title:
            lines.append(f"### {self.title}\n")

        # Headers
        lines.append("| " + " | ".join(self.headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")

        # Rows
        for row in self.rows:
            values = [cell.value for cell in row.cells]
            lines.append("| " + " | ".join(values) + " |")

        if self.footer:
            lines.append(f"\n*{self.footer}*")

        return "\n".join(lines)


class DecisionNode(BaseModel):
    """Node in a clinical decision tree."""

    id: str = Field(..., description="Node identifier")
    type: Literal["decision", "action", "outcome"] = Field(..., description="Node type")
    text: str = Field(..., description="Node text/question")
    yes_next: Optional[str] = Field(None, description="Next node if yes")
    no_next: Optional[str] = Field(None, description="Next node if no")
    children: Optional[List[str]] = Field(None, description="Child node IDs")
    action: Optional[str] = Field(None, description="Recommended action")
    evidence: Optional[EvidenceBadge] = Field(None, description="Evidence for action")


class DecisionTree(BaseModel):
    """Clinical algorithm visualization."""

    id: str = Field(..., description="Tree identifier")
    title: str = Field(..., description="Algorithm title")
    description: Optional[str] = Field(None, description="Algorithm description")
    start_node: str = Field(..., description="Starting node ID")
    nodes: Dict[str, DecisionNode] = Field(..., description="All nodes by ID")
    mermaid_diagram: Optional[str] = Field(None, description="Mermaid format diagram")

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax."""
        if self.mermaid_diagram:
            return self.mermaid_diagram

        lines = ["flowchart TD"]

        for node_id, node in self.nodes.items():
            # Node shape based on type
            if node.type == "decision":
                lines.append(f"    {node_id}{{{node.text}}}")
            elif node.type == "action":
                lines.append(f"    {node_id}[{node.text}]")
            else:  # outcome
                lines.append(f"    {node_id}([{node.text}])")

            # Connections
            if node.yes_next:
                lines.append(f"    {node_id} -->|Yes| {node.yes_next}")
            if node.no_next:
                lines.append(f"    {node_id} -->|No| {node.no_next}")
            if node.children:
                for child in node.children:
                    lines.append(f"    {node_id} --> {child}")

        return "\n".join(lines)


class Callout(BaseModel):
    """Warning/info/tip callout box."""

    type: CalloutType = Field(..., description="Callout type")
    title: str = Field(..., description="Callout title")
    content: str = Field(..., description="Callout content")
    icon: Optional[str] = Field(None, description="Icon/emoji")
    severity: Literal["low", "medium", "high", "critical"] = Field(default="medium", description="Severity level")
    citations: Optional[List[Citation]] = Field(None, description="Supporting references")

    def get_icon(self) -> str:
        """Get default icon for callout type."""
        if self.icon:
            return self.icon

        icons = {
            CalloutType.WARNING: "⚠️",
            CalloutType.CAUTION: "⚡",
            CalloutType.INFO: "ℹ️",
            CalloutType.TIP: "💡",
            CalloutType.EVIDENCE: "📊",
            CalloutType.ACTION: "✅",
        }
        return icons.get(self.type, "ℹ️")

    def get_color(self) -> str:
        """Get background color for callout type."""
        colors = {
            CalloutType.WARNING: "#fef2f2",  # red-50
            CalloutType.CAUTION: "#fff7ed",  # orange-50
            CalloutType.INFO: "#eff6ff",  # blue-50
            CalloutType.TIP: "#f0fdf4",  # green-50
            CalloutType.EVIDENCE: "#f5f3ff",  # purple-50
            CalloutType.ACTION: "#ecfdf5",  # emerald-50
        }
        return colors.get(self.type, "#f9fafb")


class DrugCard(BaseModel):
    """Compact drug information card."""

    name: str = Field(..., description="Drug name")
    generic_name: Optional[str] = Field(None, description="Generic name")
    class_name: Optional[str] = Field(None, description="Drug class")
    mechanism: Optional[str] = Field(None, description="Mechanism of action")
    indications: List[str] = Field(default_factory=list, description="Primary indications")
    dosing: Optional[str] = Field(None, description="Standard dosing")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    warnings: List[str] = Field(default_factory=list, description="Black box warnings")
    interactions: List[str] = Field(default_factory=list, description="Key interactions")
    side_effects: List[str] = Field(default_factory=list, description="Common side effects")
    monitoring: Optional[str] = Field(None, description="Required monitoring")
    evidence: Optional[EvidenceBadge] = Field(None, description="Evidence quality")


class CalculatorResult(BaseModel):
    """Formatted clinical calculator result."""

    calculator_name: str = Field(..., description="Calculator name")
    result_value: str = Field(..., description="Calculated value")
    interpretation: str = Field(..., description="Result interpretation")
    risk_category: Optional[str] = Field(None, description="Risk category")
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    inputs: Dict[str, Any] = Field(..., description="Input parameters used")
    evidence: Optional[EvidenceBadge] = Field(None, description="Calculator validation evidence")
    citations: Optional[List[Citation]] = Field(None, description="References")


class QuickAction(BaseModel):
    """Actionable button/link."""

    label: str = Field(..., description="Button label")
    action_type: Literal["copy", "calculate", "prescribe", "order", "navigate"] = Field(..., description="Action type")
    data: Optional[Dict[str, Any]] = Field(None, description="Action payload")
    icon: Optional[str] = Field(None, description="Button icon")
    primary: bool = Field(default=False, description="Primary action styling")


class Section(BaseModel):
    """Collapsible content section."""

    id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content (markdown)")
    collapsed: bool = Field(default=False, description="Initially collapsed")
    level: int = Field(default=1, ge=1, le=6, description="Heading level")
    subsections: List["Section"] = Field(default_factory=list, description="Nested sections")
    quick_actions: List[QuickAction] = Field(default_factory=list, description="Section actions")
    evidence: Optional[EvidenceBadge] = Field(None, description="Section evidence quality")


class RichAnswer(BaseModel):
    """Complete formatted answer container."""

    query: str = Field(..., description="Original query")
    summary: str = Field(..., description="Brief answer summary")
    sections: List[Section] = Field(..., description="Content sections")
    tables: List[Table] = Field(default_factory=list, description="Comparison tables")
    decision_trees: List[DecisionTree] = Field(default_factory=list, description="Clinical algorithms")
    callouts: List[Callout] = Field(default_factory=list, description="Important alerts")
    drug_cards: List[DrugCard] = Field(default_factory=list, description="Drug information")
    calculator_results: List[CalculatorResult] = Field(default_factory=list, description="Calculator outputs")
    citations: List[Citation] = Field(..., description="All references")
    overall_evidence: Optional[EvidenceBadge] = Field(None, description="Overall evidence quality")
    quick_actions: List[QuickAction] = Field(default_factory=list, description="Top-level actions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")

    def get_plain_text(self) -> str:
        """Convert to plain text for EMR paste."""
        lines = [f"Query: {self.query}", "", self.summary, ""]

        for section in self.sections:
            lines.append(f"\n{'#' * section.level} {section.title}")
            lines.append(section.content)

        if self.citations:
            lines.append("\n## References")
            for i, citation in enumerate(self.citations, 1):
                lines.append(f"{i}. {citation.format_apa()}")

        return "\n".join(lines)

    def get_copyable_text(self, include_citations: bool = True) -> str:
        """Get formatted text for clipboard copy."""
        lines = [self.summary, ""]

        for section in self.sections:
            if not section.collapsed:
                lines.append(f"{section.title}:")
                lines.append(section.content)
                lines.append("")

        if include_citations and self.citations:
            lines.append("References:")
            for i, citation in enumerate(self.citations, 1):
                lines.append(f"[{i}] {citation.format_apa()}")

        return "\n".join(lines)


# Update forward references
Section.model_rebuild()
