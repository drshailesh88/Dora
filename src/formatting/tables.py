"""
Table generator for medical comparisons and dosing information.

This module provides utilities for creating formatted tables for drug comparisons,
dosing schedules, lab values, and differential diagnoses.
"""

from typing import List, Dict, Any, Optional, Literal
from .models import Table, TableRow, TableCell


class TableGenerator:
    """Generate formatted tables for medical information."""

    @staticmethod
    def create_drug_comparison_table(
        drugs: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> Table:
        """
        Create drug comparison table.

        Args:
            drugs: List of drug dictionaries with properties
            columns: Columns to include (defaults to common properties)

        Returns:
            Formatted comparison table
        """
        if not columns:
            columns = [
                "Drug",
                "Class",
                "Mechanism",
                "Dosing",
                "Side Effects",
                "Contraindications",
            ]

        rows = []
        for drug in drugs:
            cells = []
            for col in columns:
                # Map column name to drug property
                col_key = col.lower().replace(" ", "_")
                value = drug.get(col_key, "-")

                # Handle list values
                if isinstance(value, list):
                    value = ", ".join(value) if value else "-"

                # Emphasis on drug name
                emphasis = col == "Drug"

                cells.append(TableCell(value=str(value), emphasis=emphasis))

            rows.append(TableRow(cells=cells))

        return Table(
            id=f"drug_comparison_{len(drugs)}",
            title="Drug Comparison",
            headers=columns,
            rows=rows,
            sortable=True,
            filterable=True,
        )

    @staticmethod
    def create_dosing_table(
        drug_name: str,
        dosing_info: List[Dict[str, str]],
    ) -> Table:
        """
        Create dosing table for a medication.

        Args:
            drug_name: Name of the drug
            dosing_info: List of dosing scenarios with indication, dose, frequency, etc.

        Returns:
            Formatted dosing table
        """
        headers = ["Indication", "Dose", "Frequency", "Route", "Max Dose", "Notes"]
        rows = []

        for info in dosing_info:
            cells = [
                TableCell(value=info.get("indication", "-")),
                TableCell(value=info.get("dose", "-"), emphasis=True),
                TableCell(value=info.get("frequency", "-")),
                TableCell(value=info.get("route", "-")),
                TableCell(value=info.get("max_dose", "-")),
                TableCell(value=info.get("notes", "-")),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id=f"dosing_{drug_name.lower().replace(' ', '_')}",
            title=f"{drug_name} Dosing",
            headers=headers,
            rows=rows,
            sortable=False,
            footer="Always check renal/hepatic dosing adjustments and drug interactions.",
        )

    @staticmethod
    def create_differential_diagnosis_table(
        diagnoses: List[Dict[str, Any]],
    ) -> Table:
        """
        Create differential diagnosis comparison table.

        Args:
            diagnoses: List of diagnoses with features

        Returns:
            Formatted differential table
        """
        headers = ["Diagnosis", "Key Features", "Testing", "Likelihood", "Urgency"]
        rows = []

        for dx in diagnoses:
            likelihood = dx.get("likelihood", "Unknown")
            urgency = dx.get("urgency", "Routine")

            # Color coding by urgency
            urgency_colors = {
                "Emergent": "#fef2f2",  # red
                "Urgent": "#fff7ed",  # orange
                "Routine": "#f0fdf4",  # green
            }

            cells = [
                TableCell(value=dx.get("name", "-"), emphasis=True),
                TableCell(value=dx.get("key_features", "-")),
                TableCell(value=dx.get("testing", "-")),
                TableCell(value=likelihood),
                TableCell(value=urgency, color=urgency_colors.get(urgency)),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id="differential_diagnosis",
            title="Differential Diagnosis",
            headers=headers,
            rows=rows,
            sortable=True,
            filterable=True,
        )

    @staticmethod
    def create_lab_reference_table(
        lab_name: str,
        reference_ranges: List[Dict[str, str]],
    ) -> Table:
        """
        Create lab value reference range table.

        Args:
            lab_name: Name of the lab test
            reference_ranges: List of ranges by age/sex/condition

        Returns:
            Formatted reference table
        """
        headers = ["Population", "Normal Range", "Units", "Critical Values", "Notes"]
        rows = []

        for range_info in reference_ranges:
            cells = [
                TableCell(value=range_info.get("population", "Adult")),
                TableCell(value=range_info.get("normal_range", "-"), emphasis=True),
                TableCell(value=range_info.get("units", "-")),
                TableCell(value=range_info.get("critical_values", "-"), color="#fef2f2"),
                TableCell(value=range_info.get("notes", "-")),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id=f"lab_ref_{lab_name.lower().replace(' ', '_')}",
            title=f"{lab_name} Reference Ranges",
            headers=headers,
            rows=rows,
            sortable=False,
            footer="Reference ranges may vary by laboratory. Always check local standards.",
        )

    @staticmethod
    def create_side_effects_table(
        drug_name: str,
        side_effects: List[Dict[str, str]],
    ) -> Table:
        """
        Create side effects table organized by frequency and severity.

        Args:
            drug_name: Name of the drug
            side_effects: List of side effects with frequency and severity

        Returns:
            Formatted side effects table
        """
        headers = ["Side Effect", "Frequency", "Severity", "Management"]
        rows = []

        # Sort by severity then frequency
        severity_order = {"Severe": 0, "Moderate": 1, "Mild": 2}
        sorted_effects = sorted(
            side_effects,
            key=lambda x: (
                severity_order.get(x.get("severity", "Mild"), 3),
                -self._frequency_to_number(x.get("frequency", "Rare")),
            ),
        )

        for effect in sorted_effects:
            severity = effect.get("severity", "Mild")

            # Color code by severity
            severity_colors = {
                "Severe": "#fef2f2",
                "Moderate": "#fff7ed",
                "Mild": "#f0fdf4",
            }

            cells = [
                TableCell(value=effect.get("name", "-")),
                TableCell(value=effect.get("frequency", "-")),
                TableCell(value=severity, color=severity_colors.get(severity)),
                TableCell(value=effect.get("management", "-")),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id=f"side_effects_{drug_name.lower().replace(' ', '_')}",
            title=f"{drug_name} Side Effects",
            headers=headers,
            rows=rows,
            sortable=True,
            filterable=True,
        )

    @staticmethod
    def _frequency_to_number(frequency: str) -> float:
        """Convert frequency text to number for sorting."""
        freq_map = {
            "Very Common": 0.3,  # >10%
            "Common": 0.05,  # 1-10%
            "Uncommon": 0.005,  # 0.1-1%
            "Rare": 0.0005,  # 0.01-0.1%
            "Very Rare": 0.00005,  # <0.01%
        }
        return freq_map.get(frequency, 0.001)

    @staticmethod
    def create_interaction_table(
        drug_name: str,
        interactions: List[Dict[str, str]],
    ) -> Table:
        """
        Create drug interaction table.

        Args:
            drug_name: Primary drug name
            interactions: List of interacting drugs with effects

        Returns:
            Formatted interaction table
        """
        headers = ["Interacting Drug", "Effect", "Severity", "Management"]
        rows = []

        # Sort by severity
        severity_order = {"Contraindicated": 0, "Major": 1, "Moderate": 2, "Minor": 3}
        sorted_interactions = sorted(
            interactions, key=lambda x: severity_order.get(x.get("severity", "Minor"), 4)
        )

        for interaction in sorted_interactions:
            severity = interaction.get("severity", "Minor")

            # Color code by severity
            severity_colors = {
                "Contraindicated": "#7f1d1d",  # dark red
                "Major": "#fef2f2",  # red
                "Moderate": "#fff7ed",  # orange
                "Minor": "#fffbeb",  # yellow
            }

            cells = [
                TableCell(value=interaction.get("drug", "-"), emphasis=True),
                TableCell(value=interaction.get("effect", "-")),
                TableCell(value=severity, color=severity_colors.get(severity)),
                TableCell(value=interaction.get("management", "-")),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id=f"interactions_{drug_name.lower().replace(' ', '_')}",
            title=f"{drug_name} Drug Interactions",
            headers=headers,
            rows=rows,
            sortable=True,
            filterable=True,
            footer="This list may not be exhaustive. Always check comprehensive drug interaction databases.",
        )

    @staticmethod
    def create_renal_dosing_table(
        drug_name: str,
        dosing_by_function: List[Dict[str, str]],
    ) -> Table:
        """
        Create renal dosing adjustment table.

        Args:
            drug_name: Name of the drug
            dosing_by_function: List of dosing by CrCl/eGFR ranges

        Returns:
            Formatted renal dosing table
        """
        headers = ["CrCl/eGFR", "Dose Adjustment", "Frequency Adjustment", "Notes"]
        rows = []

        for dosing in dosing_by_function:
            cells = [
                TableCell(value=dosing.get("creatinine_clearance", "-")),
                TableCell(value=dosing.get("dose_adjustment", "-"), emphasis=True),
                TableCell(value=dosing.get("frequency_adjustment", "-")),
                TableCell(value=dosing.get("notes", "-")),
            ]
            rows.append(TableRow(cells=cells))

        return Table(
            id=f"renal_dosing_{drug_name.lower().replace(' ', '_')}",
            title=f"{drug_name} Renal Dosing Adjustments",
            headers=headers,
            rows=rows,
            sortable=False,
            footer="Consult clinical pharmacist for complex cases. Consider dialysis timing.",
        )


def create_quick_comparison(
    items: List[str], properties: Dict[str, List[str]], title: str = "Comparison"
) -> Table:
    """
    Quick helper to create simple comparison table.

    Args:
        items: List of item names (rows)
        properties: Dict mapping property name to list of values
        title: Table title

    Returns:
        Formatted table

    Example:
        >>> items = ["Drug A", "Drug B"]
        >>> properties = {
        ...     "Dose": ["10mg", "20mg"],
        ...     "Frequency": ["BID", "TID"]
        ... }
        >>> table = create_quick_comparison(items, properties, "Drug Comparison")
    """
    headers = ["Item"] + list(properties.keys())
    rows = []

    for i, item in enumerate(items):
        cells = [TableCell(value=item, emphasis=True)]

        for prop_values in properties.values():
            if i < len(prop_values):
                cells.append(TableCell(value=prop_values[i]))
            else:
                cells.append(TableCell(value="-"))

        rows.append(TableRow(cells=cells))

    return Table(
        id=f"comparison_{len(items)}",
        title=title,
        headers=headers,
        rows=rows,
        sortable=True,
    )
