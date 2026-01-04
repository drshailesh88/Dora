"""
Collapsible section management for organized content display.

This module provides utilities for creating hierarchical, collapsible
sections to organize medical information effectively.
"""

from typing import List, Optional
from .models import Section, QuickAction, EvidenceBadge


class SectionBuilder:
    """Build hierarchical content sections."""

    def __init__(self, section_id: str, title: str, level: int = 1):
        """
        Initialize section builder.

        Args:
            section_id: Unique section identifier
            title: Section title
            level: Heading level (1-6)
        """
        self.section_id = section_id
        self.title = title
        self.level = level
        self.content_parts: List[str] = []
        self.subsections: List[Section] = []
        self.quick_actions: List[QuickAction] = []
        self.collapsed = False
        self.evidence: Optional[EvidenceBadge] = None

    def add_content(self, content: str) -> "SectionBuilder":
        """
        Add content to section.

        Args:
            content: Markdown content to add

        Returns:
            Self for method chaining
        """
        self.content_parts.append(content)
        return self

    def add_paragraph(self, text: str) -> "SectionBuilder":
        """
        Add paragraph to section.

        Args:
            text: Paragraph text

        Returns:
            Self for method chaining
        """
        self.content_parts.append(text)
        return self

    def add_list(self, items: List[str], ordered: bool = False) -> "SectionBuilder":
        """
        Add list to section.

        Args:
            items: List items
            ordered: Use ordered list if True

        Returns:
            Self for method chaining
        """
        if ordered:
            list_items = [f"{i+1}. {item}" for i, item in enumerate(items)]
        else:
            list_items = [f"- {item}" for item in items]

        self.content_parts.append("\n".join(list_items))
        return self

    def add_subsection(self, subsection: Section) -> "SectionBuilder":
        """
        Add subsection.

        Args:
            subsection: Subsection to add

        Returns:
            Self for method chaining
        """
        self.subsections.append(subsection)
        return self

    def add_action(self, action: QuickAction) -> "SectionBuilder":
        """
        Add quick action button.

        Args:
            action: Quick action to add

        Returns:
            Self for method chaining
        """
        self.quick_actions.append(action)
        return self

    def set_collapsed(self, collapsed: bool = True) -> "SectionBuilder":
        """
        Set initial collapsed state.

        Args:
            collapsed: Collapsed state

        Returns:
            Self for method chaining
        """
        self.collapsed = collapsed
        return self

    def set_evidence(self, evidence: EvidenceBadge) -> "SectionBuilder":
        """
        Set evidence quality badge.

        Args:
            evidence: Evidence badge

        Returns:
            Self for method chaining
        """
        self.evidence = evidence
        return self

    def build(self) -> Section:
        """
        Build the section.

        Returns:
            Complete Section object
        """
        content = "\n\n".join(self.content_parts)

        return Section(
            id=self.section_id,
            title=self.title,
            content=content,
            collapsed=self.collapsed,
            level=self.level,
            subsections=self.subsections,
            quick_actions=self.quick_actions,
            evidence=self.evidence,
        )


def create_overview_section(summary: str, evidence: Optional[EvidenceBadge] = None) -> Section:
    """
    Create overview section (always expanded).

    Args:
        summary: Brief overview text
        evidence: Overall evidence quality

    Returns:
        Overview section
    """
    return (
        SectionBuilder("overview", "Overview", level=2)
        .add_content(summary)
        .set_collapsed(False)
        .set_evidence(evidence)
        .build()
    )


def create_mechanism_section(mechanism: str) -> Section:
    """
    Create mechanism of action section (collapsed by default).

    Args:
        mechanism: Mechanism description

    Returns:
        Mechanism section
    """
    return (
        SectionBuilder("mechanism", "Mechanism of Action", level=2)
        .add_content(mechanism)
        .set_collapsed(True)
        .build()
    )


def create_dosing_section(dosing_info: str, special_populations: Optional[List[str]] = None) -> Section:
    """
    Create dosing section (expanded by default).

    Args:
        dosing_info: Standard dosing information
        special_populations: Special population considerations

    Returns:
        Dosing section
    """
    builder = SectionBuilder("dosing", "Dosing", level=2).add_content(dosing_info).set_collapsed(False)

    if special_populations:
        builder.add_content("\n**Special Populations:**").add_list(special_populations)

    # Add copy action
    copy_action = QuickAction(label="Copy Dosing", action_type="copy", data={"text": dosing_info})
    builder.add_action(copy_action)

    return builder.build()


def create_side_effects_section(
    common: List[str], serious: List[str], monitoring: Optional[str] = None
) -> Section:
    """
    Create side effects section (collapsed by default).

    Args:
        common: Common side effects
        serious: Serious/rare side effects
        monitoring: Monitoring requirements

    Returns:
        Side effects section
    """
    builder = (
        SectionBuilder("side_effects", "Side Effects", level=2)
        .add_content("**Common:**")
        .add_list(common)
        .add_content("\n**Serious/Rare:**")
        .add_list(serious)
        .set_collapsed(True)
    )

    if monitoring:
        builder.add_content(f"\n**Monitoring:** {monitoring}")

    return builder.build()


def create_interactions_section(interactions: List[str]) -> Section:
    """
    Create drug interactions section (collapsed by default).

    Args:
        interactions: List of key interactions

    Returns:
        Interactions section
    """
    return (
        SectionBuilder("interactions", "Drug Interactions", level=2)
        .add_content("**Key Interactions:**")
        .add_list(interactions)
        .set_collapsed(True)
        .build()
    )


def create_references_section(citations: List[str]) -> Section:
    """
    Create references section (collapsed by default).

    Args:
        citations: List of formatted citations

    Returns:
        References section
    """
    builder = SectionBuilder("references", "References", level=2).set_collapsed(True)

    for i, citation in enumerate(citations, 1):
        builder.add_content(f"{i}. {citation}")

    return builder.build()


def create_clinical_pearls_section(pearls: List[str]) -> Section:
    """
    Create clinical pearls section (expanded).

    Args:
        pearls: List of clinical pearls

    Returns:
        Clinical pearls section
    """
    return (
        SectionBuilder("pearls", "Clinical Pearls", level=2)
        .add_content("💡 **Key Points to Remember:**")
        .add_list(pearls)
        .set_collapsed(False)
        .build()
    )


def create_diagnostic_approach_section(
    history: str, physical: str, testing: str, differential: Optional[str] = None
) -> Section:
    """
    Create diagnostic approach section with subsections.

    Args:
        history: History taking points
        physical: Physical exam findings
        testing: Diagnostic testing
        differential: Differential diagnosis considerations

    Returns:
        Diagnostic approach section with subsections
    """
    builder = SectionBuilder("diagnostic_approach", "Diagnostic Approach", level=2).set_collapsed(False)

    # History subsection
    history_section = (
        SectionBuilder("history", "History", level=3).add_content(history).set_collapsed(False).build()
    )
    builder.add_subsection(history_section)

    # Physical exam subsection
    physical_section = (
        SectionBuilder("physical", "Physical Examination", level=3)
        .add_content(physical)
        .set_collapsed(False)
        .build()
    )
    builder.add_subsection(physical_section)

    # Testing subsection
    testing_section = (
        SectionBuilder("testing", "Diagnostic Testing", level=3)
        .add_content(testing)
        .set_collapsed(False)
        .build()
    )
    builder.add_subsection(testing_section)

    if differential:
        diff_section = (
            SectionBuilder("differential", "Differential Diagnosis", level=3)
            .add_content(differential)
            .set_collapsed(True)
            .build()
        )
        builder.add_subsection(diff_section)

    return builder.build()


def create_treatment_section(
    acute_management: str,
    chronic_management: Optional[str] = None,
    follow_up: Optional[str] = None,
) -> Section:
    """
    Create treatment section with subsections.

    Args:
        acute_management: Acute/initial treatment
        chronic_management: Long-term management
        follow_up: Follow-up recommendations

    Returns:
        Treatment section with subsections
    """
    builder = SectionBuilder("treatment", "Treatment", level=2).set_collapsed(False)

    # Acute management
    acute_section = (
        SectionBuilder("acute", "Acute Management", level=3)
        .add_content(acute_management)
        .set_collapsed(False)
        .build()
    )
    builder.add_subsection(acute_section)

    if chronic_management:
        chronic_section = (
            SectionBuilder("chronic", "Chronic Management", level=3)
            .add_content(chronic_management)
            .set_collapsed(True)
            .build()
        )
        builder.add_subsection(chronic_section)

    if follow_up:
        followup_section = (
            SectionBuilder("followup", "Follow-up", level=3)
            .add_content(follow_up)
            .set_collapsed(True)
            .build()
        )
        builder.add_subsection(followup_section)

    return builder.build()


def organize_content_into_sections(content: str, section_structure: Optional[List[str]] = None) -> List[Section]:
    """
    Automatically organize markdown content into logical sections.

    Args:
        content: Raw markdown content
        section_structure: Optional list of section names to look for

    Returns:
        List of organized sections
    """
    if section_structure is None:
        section_structure = [
            "Overview",
            "Mechanism",
            "Indications",
            "Dosing",
            "Side Effects",
            "Contraindications",
            "Interactions",
            "Monitoring",
            "References",
        ]

    sections = []
    lines = content.split("\n")

    current_section = None
    current_content = []

    for line in lines:
        # Check if line is a header
        if line.startswith("#"):
            # Save previous section
            if current_section:
                sections.append(
                    SectionBuilder(
                        current_section.lower().replace(" ", "_"),
                        current_section,
                        level=2,
                    )
                    .add_content("\n".join(current_content))
                    .build()
                )
                current_content = []

            # Extract title
            title = line.lstrip("#").strip()
            current_section = title
        else:
            current_content.append(line)

    # Add last section
    if current_section:
        sections.append(
            SectionBuilder(
                current_section.lower().replace(" ", "_"),
                current_section,
                level=2,
            )
            .add_content("\n".join(current_content))
            .build()
        )

    return sections


def collapse_sections_by_priority(sections: List[Section], keep_expanded: List[str]) -> List[Section]:
    """
    Collapse sections except priority ones.

    Args:
        sections: List of sections
        keep_expanded: List of section IDs to keep expanded

    Returns:
        Modified sections list
    """
    for section in sections:
        if section.id not in keep_expanded:
            section.collapsed = True
        else:
            section.collapsed = False

    return sections
