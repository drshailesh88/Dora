"""
Format renderer for converting rich answers to various output formats.

This module provides renderers for HTML, Markdown, JSON, and React components.
"""

from typing import Dict, Any, Optional
import json
from .models import (
    RichAnswer,
    Section,
    Table,
    DecisionTree,
    Callout,
    DrugCard,
    CalculatorResult,
    EvidenceBadge,
)


class MarkdownRenderer:
    """Render rich answers as Markdown."""

    @staticmethod
    def render(answer: RichAnswer) -> str:
        """
        Render complete answer as Markdown.

        Args:
            answer: Rich answer to render

        Returns:
            Markdown string
        """
        lines = []

        # Title
        lines.append(f"# {answer.query}")
        lines.append("")

        # Evidence badge
        if answer.overall_evidence:
            lines.append(
                f"**Evidence Level:** {answer.overall_evidence.level.value} | "
                f"**Confidence:** {int(answer.overall_evidence.confidence_score * 100)}%"
            )
            lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(answer.summary)
        lines.append("")

        # Callouts
        for callout in answer.callouts:
            lines.append(MarkdownRenderer._render_callout(callout))
            lines.append("")

        # Sections
        for section in answer.sections:
            lines.append(MarkdownRenderer._render_section(section))
            lines.append("")

        # Tables
        for table in answer.tables:
            lines.append(table.to_markdown())
            lines.append("")

        # Drug cards
        for drug in answer.drug_cards:
            lines.append(MarkdownRenderer._render_drug_card(drug))
            lines.append("")

        # Calculator results
        for calc in answer.calculator_results:
            lines.append(MarkdownRenderer._render_calculator(calc))
            lines.append("")

        # Decision trees
        for tree in answer.decision_trees:
            lines.append(f"## {tree.title}")
            lines.append("```mermaid")
            lines.append(tree.to_mermaid())
            lines.append("```")
            lines.append("")

        # References
        if answer.citations:
            lines.append("## References")
            for i, citation in enumerate(answer.citations, 1):
                lines.append(f"{i}. {citation.format_apa()}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _render_section(section: Section, level_offset: int = 0) -> str:
        """Render a section."""
        lines = []

        # Header
        header_level = section.level + level_offset
        lines.append(f"{'#' * header_level} {section.title}")

        # Evidence badge
        if section.evidence:
            lines.append(f"*Evidence Level: {section.evidence.level.value}*")

        lines.append("")
        lines.append(section.content)

        # Subsections
        for subsection in section.subsections:
            lines.append("")
            lines.append(MarkdownRenderer._render_section(subsection, level_offset))

        return "\n".join(lines)

    @staticmethod
    def _render_callout(callout: Callout) -> str:
        """Render a callout."""
        lines = []
        lines.append(f"> {callout.get_icon()} **{callout.title}**")
        lines.append(f"> {callout.content}")
        return "\n".join(lines)

    @staticmethod
    def _render_drug_card(drug: DrugCard) -> str:
        """Render a drug card."""
        lines = []
        lines.append(f"### {drug.name}")

        if drug.generic_name:
            lines.append(f"*{drug.generic_name}*")

        if drug.class_name:
            lines.append(f"**Class:** {drug.class_name}")

        if drug.dosing:
            lines.append(f"**Dosing:** {drug.dosing}")

        if drug.warnings:
            lines.append(f"**⚠️ Warnings:** {', '.join(drug.warnings)}")

        return "\n".join(lines)

    @staticmethod
    def _render_calculator(calc: CalculatorResult) -> str:
        """Render a calculator result."""
        lines = []
        lines.append(f"### {calc.calculator_name}")
        lines.append(f"**Result:** {calc.result_value}")
        lines.append(f"**Interpretation:** {calc.interpretation}")

        if calc.recommendations:
            lines.append("**Recommendations:**")
            for rec in calc.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


class HTMLRenderer:
    """Render rich answers as HTML."""

    @staticmethod
    def render(answer: RichAnswer) -> str:
        """
        Render complete answer as HTML.

        Args:
            answer: Rich answer to render

        Returns:
            HTML string
        """
        html_parts = []

        html_parts.append('<div class="rich-answer">')

        # Header
        html_parts.append(f'<h1>{answer.query}</h1>')

        # Evidence badge
        if answer.overall_evidence:
            html_parts.append(HTMLRenderer._render_evidence_badge(answer.overall_evidence))

        # Summary
        html_parts.append('<div class="summary">')
        html_parts.append(f"<p>{answer.summary}</p>")
        html_parts.append("</div>")

        # Callouts
        for callout in answer.callouts:
            html_parts.append(HTMLRenderer._render_callout(callout))

        # Sections
        for section in answer.sections:
            html_parts.append(HTMLRenderer._render_section(section))

        # Tables
        for table in answer.tables:
            html_parts.append(HTMLRenderer._render_table(table))

        # Drug cards
        for drug in answer.drug_cards:
            html_parts.append(HTMLRenderer._render_drug_card(drug))

        # Calculator results
        for calc in answer.calculator_results:
            html_parts.append(HTMLRenderer._render_calculator(calc))

        html_parts.append("</div>")

        return "\n".join(html_parts)

    @staticmethod
    def _render_evidence_badge(badge: EvidenceBadge) -> str:
        """Render evidence badge."""
        color = badge.get_color()
        return (
            f'<div class="evidence-badge" style="background-color: {color};">'
            f'<span class="level">Level {badge.level.value}</span>'
            f'<span class="confidence">{int(badge.confidence_score * 100)}%</span>'
            f"</div>"
        )

    @staticmethod
    def _render_section(section: Section) -> str:
        """Render section."""
        collapsed_class = "collapsed" if section.collapsed else ""

        html = f'<div class="section {collapsed_class}" id="{section.id}">'
        html += f"<h{section.level}>{section.title}</h{section.level}>"
        html += f'<div class="content">{section.content}</div>'

        for subsection in section.subsections:
            html += HTMLRenderer._render_section(subsection)

        html += "</div>"
        return html

    @staticmethod
    def _render_callout(callout: Callout) -> str:
        """Render callout."""
        color = callout.get_color()
        return (
            f'<div class="callout callout-{callout.type.value}" style="background-color: {color};">'
            f'<div class="callout-header">'
            f'<span class="icon">{callout.get_icon()}</span>'
            f'<span class="title">{callout.title}</span>'
            f"</div>"
            f'<div class="callout-content">{callout.content}</div>'
            f"</div>"
        )

    @staticmethod
    def _render_table(table: Table) -> str:
        """Render table."""
        html = f'<div class="table-container">'
        if table.title:
            html += f"<h3>{table.title}</h3>"

        html += '<table class="medical-table">'

        # Headers
        html += "<thead><tr>"
        for header in table.headers:
            html += f"<th>{header}</th>"
        html += "</tr></thead>"

        # Rows
        html += "<tbody>"
        for row in table.rows:
            html += "<tr>"
            for cell in row.cells:
                style = f' style="background-color: {cell.color}"' if cell.color else ""
                emphasis = " class='emphasis'" if cell.emphasis else ""
                html += f"<td{emphasis}{style}>{cell.value}</td>"
            html += "</tr>"
        html += "</tbody>"

        html += "</table>"

        if table.footer:
            html += f'<div class="table-footer">{table.footer}</div>'

        html += "</div>"
        return html

    @staticmethod
    def _render_drug_card(drug: DrugCard) -> str:
        """Render drug card."""
        html = '<div class="drug-card">'
        html += f"<h3>{drug.name}</h3>"

        if drug.generic_name:
            html += f'<p class="generic-name">{drug.generic_name}</p>'

        if drug.class_name:
            html += f'<p><strong>Class:</strong> {drug.class_name}</p>'

        if drug.dosing:
            html += f'<p><strong>Dosing:</strong> {drug.dosing}</p>'

        if drug.warnings:
            html += '<div class="warnings">'
            html += "<strong>⚠️ Warnings:</strong>"
            html += "<ul>"
            for warning in drug.warnings:
                html += f"<li>{warning}</li>"
            html += "</ul></div>"

        html += "</div>"
        return html

    @staticmethod
    def _render_calculator(calc: CalculatorResult) -> str:
        """Render calculator result."""
        html = '<div class="calculator-result">'
        html += f"<h3>{calc.calculator_name}</h3>"
        html += f'<div class="result-value">{calc.result_value}</div>'
        html += f'<p class="interpretation">{calc.interpretation}</p>'

        if calc.recommendations:
            html += '<div class="recommendations"><strong>Recommendations:</strong><ul>'
            for rec in calc.recommendations:
                html += f"<li>{rec}</li>"
            html += "</ul></div>"

        html += "</div>"
        return html


class JSONRenderer:
    """Render rich answers as JSON."""

    @staticmethod
    def render(answer: RichAnswer) -> str:
        """
        Render complete answer as JSON.

        Args:
            answer: Rich answer to render

        Returns:
            JSON string
        """
        # Pydantic models have json() method
        return answer.model_dump_json(indent=2)

    @staticmethod
    def render_dict(answer: RichAnswer) -> Dict[str, Any]:
        """
        Render complete answer as dictionary.

        Args:
            answer: Rich answer to render

        Returns:
            Dictionary representation
        """
        return answer.model_dump()


class ReactRenderer:
    """Generate React/JSX component code."""

    @staticmethod
    def render(answer: RichAnswer) -> str:
        """
        Generate React component code.

        Args:
            answer: Rich answer to render

        Returns:
            React component code (TypeScript)
        """
        lines = []

        lines.append("import React from 'react';")
        lines.append("import { RichAnswer } from '@/components/answer/RichAnswer';")
        lines.append("")
        lines.append("export default function AnswerComponent() {")
        lines.append("  const data = " + JSONRenderer.render(answer) + ";")
        lines.append("")
        lines.append("  return <RichAnswer data={data} />;")
        lines.append("}")

        return "\n".join(lines)


def render_to_format(answer: RichAnswer, format: str = "markdown") -> str:
    """
    Render answer to specified format.

    Args:
        answer: Rich answer to render
        format: Output format (markdown, html, json, react)

    Returns:
        Rendered output

    Raises:
        ValueError: If format not supported
    """
    renderers = {
        "markdown": MarkdownRenderer,
        "md": MarkdownRenderer,
        "html": HTMLRenderer,
        "json": JSONRenderer,
        "react": ReactRenderer,
        "tsx": ReactRenderer,
    }

    renderer_class = renderers.get(format.lower())
    if not renderer_class:
        raise ValueError(
            f"Unsupported format: {format}. Supported: {', '.join(renderers.keys())}"
        )

    return renderer_class.render(answer)
