"""
Callout and alert box generation for medical warnings and tips.

This module provides utilities for creating formatted callouts for warnings,
cautions, clinical pearls, and actionable recommendations.
"""

from typing import List, Optional
from .models import Callout, CalloutType, Citation


class CalloutBuilder:
    """Build callouts for medical information."""

    @staticmethod
    def warning(
        title: str,
        content: str,
        severity: str = "high",
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create warning callout (contraindications, black box warnings).

        Args:
            title: Warning title
            content: Warning content
            severity: Severity level (low/medium/high/critical)
            citations: Supporting references

        Returns:
            Warning callout
        """
        return Callout(
            type=CalloutType.WARNING,
            title=title,
            content=content,
            icon="⚠️",
            severity=severity,
            citations=citations,
        )

    @staticmethod
    def caution(
        title: str,
        content: str,
        severity: str = "medium",
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create caution callout (drug interactions, side effects).

        Args:
            title: Caution title
            content: Caution content
            severity: Severity level
            citations: Supporting references

        Returns:
            Caution callout
        """
        return Callout(
            type=CalloutType.CAUTION,
            title=title,
            content=content,
            icon="⚡",
            severity=severity,
            citations=citations,
        )

    @staticmethod
    def info(
        title: str,
        content: str,
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create info callout (additional context).

        Args:
            title: Info title
            content: Info content
            citations: Supporting references

        Returns:
            Info callout
        """
        return Callout(
            type=CalloutType.INFO,
            title=title,
            content=content,
            icon="ℹ️",
            severity="low",
            citations=citations,
        )

    @staticmethod
    def tip(
        title: str,
        content: str,
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create tip callout (clinical pearls).

        Args:
            title: Tip title
            content: Tip content
            citations: Supporting references

        Returns:
            Tip callout
        """
        return Callout(
            type=CalloutType.TIP,
            title=title,
            content=content,
            icon="💡",
            severity="low",
            citations=citations,
        )

    @staticmethod
    def evidence(
        title: str,
        content: str,
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create evidence callout (supporting studies).

        Args:
            title: Evidence title
            content: Evidence content
            citations: Supporting references

        Returns:
            Evidence callout
        """
        return Callout(
            type=CalloutType.EVIDENCE,
            title=title,
            content=content,
            icon="📊",
            severity="low",
            citations=citations,
        )

    @staticmethod
    def action(
        title: str,
        content: str,
        severity: str = "medium",
        citations: Optional[List[Citation]] = None,
    ) -> Callout:
        """
        Create action callout (what to do).

        Args:
            title: Action title
            content: Action content
            severity: Urgency level
            citations: Supporting references

        Returns:
            Action callout
        """
        return Callout(
            type=CalloutType.ACTION,
            title=title,
            content=content,
            icon="✅",
            severity=severity,
            citations=citations,
        )


def create_black_box_warning(drug_name: str, warning: str) -> Callout:
    """
    Create FDA black box warning callout.

    Args:
        drug_name: Name of the medication
        warning: Black box warning text

    Returns:
        Critical warning callout
    """
    return CalloutBuilder.warning(
        title=f"⚫ BLACK BOX WARNING - {drug_name}",
        content=warning,
        severity="critical",
    )


def create_drug_interaction_alert(
    drug1: str, drug2: str, interaction: str, management: str
) -> Callout:
    """
    Create drug-drug interaction alert.

    Args:
        drug1: First drug name
        drug2: Second drug name
        interaction: Interaction description
        management: How to manage the interaction

    Returns:
        Drug interaction caution
    """
    content = f"{interaction}\n\nManagement: {management}"

    return CalloutBuilder.caution(
        title=f"DRUG INTERACTION: {drug1} + {drug2}",
        content=content,
        severity="high",
    )


def create_contraindication_alert(drug_name: str, contraindication: str) -> Callout:
    """
    Create contraindication alert.

    Args:
        drug_name: Name of the medication
        contraindication: Contraindication description

    Returns:
        Contraindication warning
    """
    return CalloutBuilder.warning(
        title=f"CONTRAINDICATION - {drug_name}",
        content=contraindication,
        severity="critical",
    )


def create_clinical_pearl(pearl: str, source: Optional[str] = None) -> Callout:
    """
    Create clinical pearl tip.

    Args:
        pearl: Clinical pearl text
        source: Optional source/expert

    Returns:
        Clinical pearl tip
    """
    title = "CLINICAL PEARL"
    if source:
        title += f" ({source})"

    return CalloutBuilder.tip(title=title, content=pearl)


def create_pregnancy_warning(drug_name: str, category: str, details: str) -> Callout:
    """
    Create pregnancy category warning.

    Args:
        drug_name: Name of the medication
        category: Pregnancy category (A/B/C/D/X or descriptor)
        details: Additional details

    Returns:
        Pregnancy warning callout
    """
    severity_map = {
        "A": "low",
        "B": "low",
        "C": "medium",
        "D": "high",
        "X": "critical",
    }

    severity = severity_map.get(category.upper(), "medium")

    content = f"Pregnancy Category: {category}\n\n{details}"

    return CalloutBuilder.warning(
        title=f"PREGNANCY - {drug_name}",
        content=content,
        severity=severity,
    )


def create_renal_dosing_alert(drug_name: str, recommendation: str) -> Callout:
    """
    Create renal dosing adjustment alert.

    Args:
        drug_name: Name of the medication
        recommendation: Dosing recommendation

    Returns:
        Renal dosing caution
    """
    return CalloutBuilder.caution(
        title=f"RENAL DOSING - {drug_name}",
        content=recommendation,
        severity="medium",
    )


def create_hepatic_dosing_alert(drug_name: str, recommendation: str) -> Callout:
    """
    Create hepatic dosing adjustment alert.

    Args:
        drug_name: Name of the medication
        recommendation: Dosing recommendation

    Returns:
        Hepatic dosing caution
    """
    return CalloutBuilder.caution(
        title=f"HEPATIC DOSING - {drug_name}",
        content=recommendation,
        severity="medium",
    )


def create_pediatric_dosing_alert(drug_name: str, recommendation: str) -> Callout:
    """
    Create pediatric dosing alert.

    Args:
        drug_name: Name of the medication
        recommendation: Pediatric dosing information

    Returns:
        Pediatric dosing info
    """
    return CalloutBuilder.info(
        title=f"PEDIATRIC DOSING - {drug_name}",
        content=recommendation,
    )


def create_monitoring_requirement(drug_name: str, monitoring: str) -> Callout:
    """
    Create monitoring requirement action.

    Args:
        drug_name: Name of the medication
        monitoring: Required monitoring

    Returns:
        Monitoring action callout
    """
    return CalloutBuilder.action(
        title=f"REQUIRED MONITORING - {drug_name}",
        content=monitoring,
        severity="medium",
    )


def create_administration_tip(drug_name: str, tip: str) -> Callout:
    """
    Create administration tip.

    Args:
        drug_name: Name of the medication
        tip: Administration tip

    Returns:
        Administration tip callout
    """
    return CalloutBuilder.tip(
        title=f"ADMINISTRATION - {drug_name}",
        content=tip,
    )


def create_food_interaction_alert(drug_name: str, interaction: str) -> Callout:
    """
    Create food-drug interaction alert.

    Args:
        drug_name: Name of the medication
        interaction: Food interaction description

    Returns:
        Food interaction caution
    """
    return CalloutBuilder.caution(
        title=f"FOOD INTERACTION - {drug_name}",
        content=interaction,
        severity="low",
    )


def create_guideline_recommendation(
    title: str, recommendation: str, guideline_source: str, year: Optional[int] = None
) -> Callout:
    """
    Create guideline-based recommendation.

    Args:
        title: Recommendation title
        recommendation: Recommendation text
        guideline_source: Source guideline (e.g., "ACC/AHA", "IDSA")
        year: Guideline year

    Returns:
        Evidence-based recommendation callout
    """
    source_text = guideline_source
    if year:
        source_text += f" {year}"

    content = f"{recommendation}\n\nSource: {source_text}"

    return CalloutBuilder.evidence(title=title, content=content)


def extract_callouts_from_text(text: str, drug_name: Optional[str] = None) -> List[Callout]:
    """
    Extract callouts from free text medical content.

    This function looks for keywords and patterns to automatically
    generate appropriate callouts.

    Args:
        text: Medical text to parse
        drug_name: Optional drug name context

    Returns:
        List of extracted callouts
    """
    callouts = []

    # Keywords to look for
    warning_keywords = [
        "black box",
        "contraindicated",
        "contraindication",
        "do not use",
        "warning",
        "boxed warning",
    ]

    caution_keywords = [
        "interaction",
        "caution",
        "avoid",
        "monitor",
        "side effect",
        "adverse",
    ]

    pearl_keywords = ["pearl", "tip", "remember", "note"]

    lines = text.split("\n")

    for line in lines:
        line_lower = line.lower()

        # Check for warnings
        if any(keyword in line_lower for keyword in warning_keywords):
            if drug_name:
                callouts.append(
                    CalloutBuilder.warning(
                        title=f"Warning - {drug_name}",
                        content=line,
                        severity="high",
                    )
                )
            else:
                callouts.append(
                    CalloutBuilder.warning(title="Warning", content=line, severity="high")
                )

        # Check for cautions
        elif any(keyword in line_lower for keyword in caution_keywords):
            if drug_name:
                callouts.append(
                    CalloutBuilder.caution(
                        title=f"Caution - {drug_name}",
                        content=line,
                        severity="medium",
                    )
                )
            else:
                callouts.append(
                    CalloutBuilder.caution(title="Caution", content=line, severity="medium")
                )

        # Check for clinical pearls
        elif any(keyword in line_lower for keyword in pearl_keywords):
            callouts.append(CalloutBuilder.tip(title="Clinical Pearl", content=line))

    return callouts
