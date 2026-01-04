"""
Decision tree and clinical algorithm rendering.

This module provides utilities for creating and visualizing clinical decision
algorithms, treatment pathways, and diagnostic flowcharts.
"""

from typing import List, Dict, Optional
from .models import DecisionTree, DecisionNode, EvidenceBadge


class AlgorithmBuilder:
    """Build clinical decision trees and algorithms."""

    def __init__(self, title: str, description: Optional[str] = None):
        """Initialize algorithm builder."""
        self.title = title
        self.description = description
        self.nodes: Dict[str, DecisionNode] = {}
        self.start_node: Optional[str] = None

    def add_decision(
        self,
        node_id: str,
        question: str,
        yes_next: Optional[str] = None,
        no_next: Optional[str] = None,
        evidence: Optional[EvidenceBadge] = None,
    ) -> "AlgorithmBuilder":
        """
        Add a decision node (yes/no question).

        Args:
            node_id: Unique node identifier
            question: Decision question text
            yes_next: Node ID to go to if yes
            no_next: Node ID to go to if no
            evidence: Evidence supporting this decision point

        Returns:
            Self for method chaining
        """
        node = DecisionNode(
            id=node_id,
            type="decision",
            text=question,
            yes_next=yes_next,
            no_next=no_next,
            evidence=evidence,
        )
        self.nodes[node_id] = node

        if self.start_node is None:
            self.start_node = node_id

        return self

    def add_action(
        self,
        node_id: str,
        action: str,
        next_node: Optional[str] = None,
        evidence: Optional[EvidenceBadge] = None,
    ) -> "AlgorithmBuilder":
        """
        Add an action node (what to do).

        Args:
            node_id: Unique node identifier
            action: Action description
            next_node: Optional next node
            evidence: Evidence supporting this action

        Returns:
            Self for method chaining
        """
        node = DecisionNode(
            id=node_id,
            type="action",
            text=action,
            action=action,
            children=[next_node] if next_node else None,
            evidence=evidence,
        )
        self.nodes[node_id] = node
        return self

    def add_outcome(
        self,
        node_id: str,
        outcome: str,
        evidence: Optional[EvidenceBadge] = None,
    ) -> "AlgorithmBuilder":
        """
        Add an outcome node (terminal state).

        Args:
            node_id: Unique node identifier
            outcome: Outcome description
            evidence: Evidence for this outcome

        Returns:
            Self for method chaining
        """
        node = DecisionNode(
            id=node_id, type="outcome", text=outcome, action=outcome, evidence=evidence
        )
        self.nodes[node_id] = node
        return self

    def set_start(self, node_id: str) -> "AlgorithmBuilder":
        """
        Set the starting node.

        Args:
            node_id: ID of starting node

        Returns:
            Self for method chaining
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        self.start_node = node_id
        return self

    def build(self) -> DecisionTree:
        """
        Build the decision tree.

        Returns:
            Complete DecisionTree object

        Raises:
            ValueError: If start node not set or tree invalid
        """
        if not self.start_node:
            raise ValueError("Start node must be set")

        if self.start_node not in self.nodes:
            raise ValueError(f"Start node {self.start_node} not in nodes")

        tree = DecisionTree(
            id=f"algorithm_{self.title.lower().replace(' ', '_')}",
            title=self.title,
            description=self.description,
            start_node=self.start_node,
            nodes=self.nodes,
        )

        # Generate Mermaid diagram
        tree.mermaid_diagram = tree.to_mermaid()

        return tree


def create_chest_pain_algorithm() -> DecisionTree:
    """Example: Chest pain evaluation algorithm."""
    builder = AlgorithmBuilder(
        title="Acute Chest Pain Evaluation",
        description="Emergency evaluation of chest pain",
    )

    (
        builder.add_decision("start", "Hemodynamically unstable?", yes_next="resuscitate", no_next="stemi_check")
        .add_action("resuscitate", "ACLS protocol, emergent cardiology consult")
        .add_decision(
            "stemi_check",
            "STEMI on ECG?",
            yes_next="activate_cath_lab",
            no_next="acs_check",
        )
        .add_action("activate_cath_lab", "Activate cath lab, ASA, heparin, dual antiplatelet")
        .add_decision(
            "acs_check",
            "Troponin elevated OR dynamic ECG changes?",
            yes_next="nstemi",
            no_next="risk_stratify",
        )
        .add_action("nstemi", "NSTEMI protocol: ASA, heparin, cardiology consult")
        .add_decision(
            "risk_stratify",
            "High risk features (HEART score >3)?",
            yes_next="admit_observation",
            no_next="alternative_dx",
        )
        .add_action("admit_observation", "Admit for serial troponins, stress test")
        .add_decision(
            "alternative_dx",
            "Evidence of PE, aortic dissection, pneumothorax?",
            yes_next="treat_alternative",
            no_next="discharge",
        )
        .add_action("treat_alternative", "Treat underlying condition")
        .add_outcome("discharge", "Consider discharge with cardiology follow-up")
    )

    return builder.build()


def create_sepsis_algorithm() -> DecisionTree:
    """Example: Sepsis management algorithm."""
    builder = AlgorithmBuilder(
        title="Sepsis Management",
        description="Sepsis-3 criteria and management",
    )

    (
        builder.add_decision(
            "start",
            "SIRS criteria + suspected infection?",
            yes_next="qsofa_check",
            no_next="monitor",
        )
        .add_decision(
            "qsofa_check",
            "qSOFA ≥2 OR lactate >2?",
            yes_next="sepsis_bundle",
            no_next="sepsis_watch",
        )
        .add_action(
            "sepsis_bundle",
            "Sepsis bundle: cultures, antibiotics <1hr, IVF 30ml/kg, lactate recheck",
        )
        .add_decision(
            "septic_shock_check",
            "Hypotension despite 30ml/kg IVF?",
            yes_next="vasopressors",
            no_next="monitor_response",
        )
        .add_action("vasopressors", "Start norepinephrine, target MAP ≥65, ICU admission")
        .add_action("sepsis_watch", "Close monitoring, repeat vitals q2h, consider antibiotics")
        .add_action("monitor", "Standard monitoring")
        .add_outcome("monitor_response", "Continue antibiotics, source control, supportive care")
    )

    return builder.build()


def create_stroke_algorithm() -> DecisionTree:
    """Example: Acute stroke evaluation algorithm."""
    builder = AlgorithmBuilder(
        title="Acute Stroke Evaluation",
        description="Stroke code activation and tPA decision-making",
    )

    (
        builder.add_decision(
            "start",
            "Symptom onset <4.5 hours AND no contraindications?",
            yes_next="imaging",
            no_next="thrombectomy_window",
        )
        .add_action("imaging", "STAT non-contrast head CT, activate stroke team")
        .add_decision(
            "hemorrhage_check",
            "ICH on CT?",
            yes_next="ich_protocol",
            no_next="tpa_eligible",
        )
        .add_action("ich_protocol", "Neurosurgery consult, reverse anticoagulation, BP control")
        .add_decision(
            "tpa_eligible",
            "NIHSS ≥4 AND no contraindications?",
            yes_next="give_tpa",
            no_next="thrombectomy_eval",
        )
        .add_action("give_tpa", "Administer tPA 0.9mg/kg (max 90mg), 10% bolus then infusion")
        .add_decision(
            "thrombectomy_window",
            "Symptom onset <24 hours AND large vessel occlusion?",
            yes_next="thrombectomy_eval",
            no_next="supportive_care",
        )
        .add_action("thrombectomy_eval", "CTA/CTP, interventional neurology consult for thrombectomy")
        .add_outcome("supportive_care", "ASA 325mg, statin, stroke unit admission, DVT prophylaxis")
    )

    return builder.build()


def create_anaphylaxis_algorithm() -> DecisionTree:
    """Example: Anaphylaxis management algorithm."""
    builder = AlgorithmBuilder(
        title="Anaphylaxis Management",
        description="Emergency treatment of anaphylaxis",
    )

    (
        builder.add_decision(
            "start",
            "Anaphylaxis criteria met?",
            yes_next="epinephrine",
            no_next="allergic_reaction",
        )
        .add_action(
            "epinephrine",
            "Epinephrine 0.3-0.5mg IM (1:1000) anterolateral thigh, repeat q5-15min PRN",
        )
        .add_action("supportive", "Supine position, O2, IV access, monitor vitals")
        .add_decision(
            "refractory_check",
            "Persistent hypotension OR respiratory distress?",
            yes_next="refractory",
            no_next="adjuncts",
        )
        .add_action(
            "refractory",
            "IV epinephrine infusion, IVF bolus, consider glucagon if on beta-blocker",
        )
        .add_action(
            "adjuncts",
            "H1 blocker (diphenhydramine 25-50mg), H2 blocker (famotidine 20mg), steroids (methylpred 125mg)",
        )
        .add_action("allergic_reaction", "H1 blocker, monitor, consider steroids if severe urticaria")
        .add_outcome("observe", "Observe 4-6 hours, discharge with EpiPen prescription and allergy referral")
    )

    return builder.build()


def parse_text_to_algorithm(text: str, title: str) -> DecisionTree:
    """
    Parse plain text algorithm description into DecisionTree.

    This is a simple parser for text like:
    1. Check vital signs
    2. If unstable -> resuscitate
    3. If stable -> continue evaluation

    Args:
        text: Algorithm text
        title: Algorithm title

    Returns:
        DecisionTree object
    """
    builder = AlgorithmBuilder(title)

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        node_id = f"step_{i + 1}"

        # Simple heuristic: if line contains "?", it's a decision
        if "?" in line:
            # Extract yes/no paths if present
            parts = line.split("->")
            question = parts[0].strip("0123456789. ")

            yes_next = None
            no_next = None

            if len(parts) > 1:
                # Try to find next step references
                # This is a simplified parser
                pass

            builder.add_decision(node_id, question, yes_next, no_next)
        elif "->" in line or "If" in line or "then" in line:
            # Decision point
            builder.add_decision(node_id, line.strip("0123456789. "))
        else:
            # Action or outcome
            action = line.strip("0123456789. ")
            builder.add_action(node_id, action)

    try:
        return builder.build()
    except ValueError:
        # Fallback: create simple linear algorithm
        builder = AlgorithmBuilder(title)
        builder.add_action("step_1", text)
        return builder.build()
