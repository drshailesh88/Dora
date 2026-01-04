"""
Copy-to-clipboard functionality for clinical notes and EMR integration.

This module provides utilities for generating formatted text that can be
easily copied and pasted into clinical notes and EMR systems.
"""

from typing import Optional, List
from .models import RichAnswer, Section, DrugCard, CalculatorResult, Table, Citation


class ClipboardFormatter:
    """Format content for clipboard copy."""

    @staticmethod
    def format_for_emr(
        answer: RichAnswer,
        include_citations: bool = False,
        include_evidence: bool = False,
    ) -> str:
        """
        Format rich answer for EMR paste.

        Generates clean, professional text suitable for medical records.

        Args:
            answer: Rich answer to format
            include_citations: Include reference numbers
            include_evidence: Include evidence level indicators

        Returns:
            EMR-formatted text
        """
        lines = []

        # Summary
        lines.append(answer.summary)
        lines.append("")

        # Main sections (only expanded ones)
        for section in answer.sections:
            if not section.collapsed:
                lines.append(section.title.upper())
                lines.append("-" * len(section.title))
                lines.append(ClipboardFormatter._clean_markdown(section.content))
                lines.append("")

        # Drug information
        for drug in answer.drug_cards:
            lines.append(f"MEDICATION: {drug.name}")
            if drug.dosing:
                lines.append(f"Dosing: {drug.dosing}")
            if drug.warnings:
                lines.append(f"Warnings: {', '.join(drug.warnings)}")
            lines.append("")

        # Calculator results
        for calc in answer.calculator_results:
            lines.append(f"{calc.calculator_name}: {calc.result_value}")
            lines.append(f"Interpretation: {calc.interpretation}")
            if calc.recommendations:
                lines.append("Recommendations:")
                for rec in calc.recommendations:
                    lines.append(f"  - {rec}")
            lines.append("")

        # Citations
        if include_citations and answer.citations:
            lines.append("REFERENCES")
            lines.append("-" * 10)
            for i, citation in enumerate(answer.citations[:5], 1):  # Limit to top 5
                lines.append(f"[{i}] {citation.format_apa()}")
            lines.append("")

        # Evidence level
        if include_evidence and answer.overall_evidence:
            lines.append(
                f"Evidence Level: {answer.overall_evidence.level.value} ({answer.overall_evidence.get_description()})"
            )

        return "\n".join(lines)

    @staticmethod
    def format_drug_for_prescription(drug: DrugCard) -> str:
        """
        Format drug information for prescription writing.

        Args:
            drug: Drug card

        Returns:
            Prescription-formatted text
        """
        lines = []

        # Drug name
        lines.append(drug.name.upper())
        if drug.generic_name:
            lines.append(f"({drug.generic_name})")
        lines.append("")

        # Dosing
        if drug.dosing:
            lines.append(f"Sig: {drug.dosing}")
            lines.append("")

        # Indications
        if drug.indications:
            lines.append(f"Indication: {drug.indications[0]}")
            lines.append("")

        # Special instructions
        if drug.monitoring:
            lines.append(f"Special Instructions: {drug.monitoring}")
            lines.append("")

        # Warnings
        if drug.warnings:
            lines.append("WARNINGS:")
            for warning in drug.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)

    @staticmethod
    def format_calculator_for_note(calc: CalculatorResult) -> str:
        """
        Format calculator result for progress note.

        Args:
            calc: Calculator result

        Returns:
            Note-formatted text
        """
        lines = []

        lines.append(f"{calc.calculator_name}: {calc.result_value}")
        lines.append(f"  {calc.interpretation}")

        if calc.risk_category:
            lines.append(f"  Risk Category: {calc.risk_category}")

        if calc.recommendations:
            lines.append("  Plan:")
            for rec in calc.recommendations:
                lines.append(f"    - {rec}")

        return "\n".join(lines)

    @staticmethod
    def format_table_as_text(table: Table) -> str:
        """
        Format table as aligned text.

        Args:
            table: Table to format

        Returns:
            Text-formatted table
        """
        lines = []

        if table.title:
            lines.append(table.title)
            lines.append("")

        # Calculate column widths
        col_widths = [len(header) for header in table.headers]

        for row in table.rows:
            for i, cell in enumerate(row.cells):
                col_widths[i] = max(col_widths[i], len(cell.value))

        # Header
        header_line = "  ".join(
            header.ljust(col_widths[i]) for i, header in enumerate(table.headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in table.rows:
            row_line = "  ".join(
                cell.value.ljust(col_widths[i]) for i, cell in enumerate(row.cells)
            )
            lines.append(row_line)

        if table.footer:
            lines.append("")
            lines.append(f"Note: {table.footer}")

        return "\n".join(lines)

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """
        Remove markdown formatting for plain text.

        Args:
            text: Markdown text

        Returns:
            Plain text
        """
        # Remove bold
        text = text.replace("**", "")

        # Remove italic
        text = text.replace("*", "")

        # Remove headers
        text = text.replace("#", "")

        # Remove inline code
        text = text.replace("`", "")

        return text.strip()


def create_soap_note_format(
    subjective: str,
    objective: str,
    assessment: str,
    plan: str,
    citations: Optional[List[Citation]] = None,
) -> str:
    """
    Create SOAP note format.

    Args:
        subjective: Subjective information
        objective: Objective findings
        assessment: Assessment
        plan: Treatment plan
        citations: Optional references

    Returns:
        SOAP note formatted text
    """
    lines = []

    lines.append("SUBJECTIVE")
    lines.append("-" * 20)
    lines.append(subjective)
    lines.append("")

    lines.append("OBJECTIVE")
    lines.append("-" * 20)
    lines.append(objective)
    lines.append("")

    lines.append("ASSESSMENT")
    lines.append("-" * 20)
    lines.append(assessment)
    lines.append("")

    lines.append("PLAN")
    lines.append("-" * 20)
    lines.append(plan)
    lines.append("")

    if citations:
        lines.append("REFERENCES")
        lines.append("-" * 20)
        for i, citation in enumerate(citations, 1):
            lines.append(f"{i}. {citation.format_apa()}")

    return "\n".join(lines)


def create_procedure_note_format(
    procedure: str,
    indication: str,
    consent: str,
    technique: str,
    findings: str,
    complications: str,
    plan: str,
) -> str:
    """
    Create procedure note format.

    Args:
        procedure: Procedure name
        indication: Indication for procedure
        consent: Consent details
        technique: Technique used
        findings: Findings
        complications: Complications if any
        plan: Post-procedure plan

    Returns:
        Procedure note formatted text
    """
    lines = []

    lines.append(f"PROCEDURE: {procedure}")
    lines.append("")

    lines.append(f"INDICATION: {indication}")
    lines.append("")

    lines.append(f"CONSENT: {consent}")
    lines.append("")

    lines.append("TECHNIQUE:")
    lines.append(technique)
    lines.append("")

    lines.append("FINDINGS:")
    lines.append(findings)
    lines.append("")

    lines.append("COMPLICATIONS:")
    lines.append(complications if complications else "None")
    lines.append("")

    lines.append("POST-PROCEDURE PLAN:")
    lines.append(plan)

    return "\n".join(lines)


def create_discharge_summary_format(
    diagnosis: str,
    hospital_course: str,
    discharge_condition: str,
    medications: List[str],
    follow_up: str,
) -> str:
    """
    Create discharge summary format.

    Args:
        diagnosis: Primary/secondary diagnoses
        hospital_course: Hospital course summary
        discharge_condition: Condition at discharge
        medications: Discharge medications
        follow_up: Follow-up instructions

    Returns:
        Discharge summary formatted text
    """
    lines = []

    lines.append("DISCHARGE SUMMARY")
    lines.append("=" * 40)
    lines.append("")

    lines.append("DIAGNOSIS:")
    lines.append(diagnosis)
    lines.append("")

    lines.append("HOSPITAL COURSE:")
    lines.append(hospital_course)
    lines.append("")

    lines.append("CONDITION AT DISCHARGE:")
    lines.append(discharge_condition)
    lines.append("")

    lines.append("DISCHARGE MEDICATIONS:")
    for i, med in enumerate(medications, 1):
        lines.append(f"{i}. {med}")
    lines.append("")

    lines.append("FOLLOW-UP INSTRUCTIONS:")
    lines.append(follow_up)

    return "\n".join(lines)


def create_prescription_pad_format(
    patient_name: str,
    drug: DrugCard,
    quantity: str,
    refills: int,
) -> str:
    """
    Create prescription pad format.

    Args:
        patient_name: Patient name
        drug: Drug information
        quantity: Quantity to dispense
        refills: Number of refills

    Returns:
        Prescription formatted text
    """
    lines = []

    lines.append(f"Patient: {patient_name}")
    lines.append("")

    lines.append(f"Rx: {drug.name}")
    if drug.generic_name:
        lines.append(f"    ({drug.generic_name})")
    lines.append("")

    if drug.dosing:
        lines.append(f"Sig: {drug.dosing}")
    lines.append("")

    lines.append(f"Quantity: {quantity}")
    lines.append(f"Refills: {refills}")
    lines.append("")

    if drug.warnings:
        lines.append("WARNINGS:")
        for warning in drug.warnings:
            lines.append(f"  - {warning}")

    return "\n".join(lines)
