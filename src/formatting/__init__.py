"""
Rich answer formatting module for Dora medical knowledge platform.

This module provides comprehensive formatting utilities for transforming plain
RAG outputs into visually rich, scannable medical content with evidence grading,
tables, decision trees, callouts, and more.
"""

# Models
from .models import (
    RichAnswer,
    Section,
    Table,
    TableRow,
    TableCell,
    DecisionTree,
    DecisionNode,
    Callout,
    CalloutType,
    DrugCard,
    CalculatorResult,
    Citation,
    EvidenceBadge,
    EvidenceLevel,
    RecommendationStrength,
    SourceType,
    QuickAction,
)

# Evidence grading
from .evidence import (
    EvidenceGrader,
    create_evidence_badge,
    get_evidence_icon,
    format_evidence_badge_text,
)

# Tables
from .tables import (
    TableGenerator,
    create_quick_comparison,
)

# Algorithms
from .algorithms import (
    AlgorithmBuilder,
    create_chest_pain_algorithm,
    create_sepsis_algorithm,
    create_stroke_algorithm,
    create_anaphylaxis_algorithm,
    parse_text_to_algorithm,
)

# Callouts
from .callouts import (
    CalloutBuilder,
    create_black_box_warning,
    create_drug_interaction_alert,
    create_contraindication_alert,
    create_clinical_pearl,
    create_pregnancy_warning,
    create_renal_dosing_alert,
    create_hepatic_dosing_alert,
    create_monitoring_requirement,
    create_guideline_recommendation,
    extract_callouts_from_text,
)

# Cards
from .cards import (
    CardBuilder,
    create_aspirin_card,
    create_chads2vasc_result,
    create_wells_dvt_result,
    create_gcs_result,
    format_drug_card_markdown,
)

# Sections
from .sections import (
    SectionBuilder,
    create_overview_section,
    create_mechanism_section,
    create_dosing_section,
    create_side_effects_section,
    create_interactions_section,
    create_references_section,
    create_clinical_pearls_section,
    create_diagnostic_approach_section,
    create_treatment_section,
    organize_content_into_sections,
    collapse_sections_by_priority,
)

# Quick copy
from .quick_copy import (
    ClipboardFormatter,
    create_soap_note_format,
    create_procedure_note_format,
    create_discharge_summary_format,
    create_prescription_pad_format,
)

# Renderer
from .renderer import (
    MarkdownRenderer,
    HTMLRenderer,
    JSONRenderer,
    ReactRenderer,
    render_to_format,
)

# Main service
from .service import (
    FormattingService,
    format_query_response,
)

__all__ = [
    # Models
    "RichAnswer",
    "Section",
    "Table",
    "TableRow",
    "TableCell",
    "DecisionTree",
    "DecisionNode",
    "Callout",
    "CalloutType",
    "DrugCard",
    "CalculatorResult",
    "Citation",
    "EvidenceBadge",
    "EvidenceLevel",
    "RecommendationStrength",
    "SourceType",
    "QuickAction",
    # Evidence
    "EvidenceGrader",
    "create_evidence_badge",
    "get_evidence_icon",
    "format_evidence_badge_text",
    # Tables
    "TableGenerator",
    "create_quick_comparison",
    # Algorithms
    "AlgorithmBuilder",
    "create_chest_pain_algorithm",
    "create_sepsis_algorithm",
    "create_stroke_algorithm",
    "create_anaphylaxis_algorithm",
    "parse_text_to_algorithm",
    # Callouts
    "CalloutBuilder",
    "create_black_box_warning",
    "create_drug_interaction_alert",
    "create_contraindication_alert",
    "create_clinical_pearl",
    "create_pregnancy_warning",
    "create_renal_dosing_alert",
    "create_hepatic_dosing_alert",
    "create_monitoring_requirement",
    "create_guideline_recommendation",
    "extract_callouts_from_text",
    # Cards
    "CardBuilder",
    "create_aspirin_card",
    "create_chads2vasc_result",
    "create_wells_dvt_result",
    "create_gcs_result",
    "format_drug_card_markdown",
    # Sections
    "SectionBuilder",
    "create_overview_section",
    "create_mechanism_section",
    "create_dosing_section",
    "create_side_effects_section",
    "create_interactions_section",
    "create_references_section",
    "create_clinical_pearls_section",
    "create_diagnostic_approach_section",
    "create_treatment_section",
    "organize_content_into_sections",
    "collapse_sections_by_priority",
    # Quick copy
    "ClipboardFormatter",
    "create_soap_note_format",
    "create_procedure_note_format",
    "create_discharge_summary_format",
    "create_prescription_pad_format",
    # Renderer
    "MarkdownRenderer",
    "HTMLRenderer",
    "JSONRenderer",
    "ReactRenderer",
    "render_to_format",
    # Service
    "FormattingService",
    "format_query_response",
]

__version__ = "1.0.0"
