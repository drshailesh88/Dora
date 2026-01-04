"""
Decision Flowcharts

Visual decision trees for clinical pathways using Mermaid diagrams.
"""

from typing import Optional, List
from .models import Flowchart
from .storage import ProtocolStorage, get_protocol_storage


# Pre-built flowchart templates
CHEST_PAIN_FLOWCHART = """
graph TD
    A[Chest Pain Patient] --> B{Vital Signs Stable?}
    B -->|No| C[RESUSCITATION]
    C --> D[Activate Crash Cart]
    B -->|Yes| E[12-lead ECG < 10 min]
    E --> F{STEMI on ECG?}
    F -->|Yes| G[ACTIVATE CATH LAB]
    G --> H[Aspirin 325mg]
    H --> I[Heparin Bolus]
    I --> J[PCI/Thrombolysis]
    F -->|No| K{Dynamic Changes?}
    K -->|Yes| L[ACS Protocol]
    L --> M[Admit Telemetry]
    K -->|No| N[Troponin × 2]
    N --> O{Troponin Elevated?}
    O -->|Yes| L
    O -->|No| P{HEART Score ≥ 4?}
    P -->|Yes| L
    P -->|No| Q[Low Risk]
    Q --> R[Discharge with Stress Test]
"""

SEPSIS_FLOWCHART = """
graph TD
    A[Suspected Infection] --> B{qSOFA ≥ 2?}
    B -->|Yes| C[HIGH RISK SEPSIS]
    B -->|No| D{SIRS ≥ 2?}
    D -->|Yes| E[Possible Sepsis]
    D -->|No| F[Monitor]
    C --> G[HOUR-1 BUNDLE]
    E --> G
    G --> H[1. Measure Lactate]
    H --> I[2. Blood Cultures]
    I --> J[3. Broad Antibiotics]
    J --> K[4. Fluid Bolus 30 mL/kg]
    K --> L{Hypotensive?}
    L -->|Yes| M[5. Start Vasopressors]
    M --> N{MAP ≥ 65?}
    L -->|No| O{Lactate > 2?}
    O -->|Yes| P[Repeat Lactate]
    O -->|No| Q[Continue Monitoring]
    N -->|No| R[Escalate Pressors]
    N -->|Yes| S[ICU Admission]
"""

STROKE_FLOWCHART = """
graph TD
    A[Suspected Stroke] --> B[Activate Stroke Team]
    B --> C[ABC Assessment]
    C --> D[Check Glucose]
    D --> E{Symptom Onset Time?}
    E -->|Unknown| F[Last Known Well Time]
    E -->|< 4.5 hours| G[STAT CT Head]
    F --> G
    G --> H{Hemorrhage on CT?}
    H -->|Yes| I[Hemorrhagic Stroke Protocol]
    I --> J[Neurosurgery Consult]
    H -->|No| K{tPA Eligible?}
    K -->|No| L{Thrombectomy Candidate?}
    K -->|Yes| M[Lower BP < 185/110]
    M --> N[Give tPA]
    N --> O{Large Vessel Occlusion?}
    O -->|Yes| P[tPA + Thrombectomy]
    O -->|No| Q[Monitor Post-tPA]
    L -->|Yes| R[Thrombectomy Only]
    L -->|No| S[Supportive Care]
    S --> T[Admit Stroke Unit]
"""

DKA_FLOWCHART = """
graph TD
    A[Hyperglycemia + Acidosis] --> B{DKA Criteria Met?}
    B -->|Yes| C[Check Potassium]
    B -->|No| D[Alternative Diagnosis]
    C --> E{K+ < 3.3?}
    E -->|Yes| F[HOLD Insulin]
    F --> G[Give K+ 20-30 mEq/hr]
    G --> H[Recheck K+ in 2h]
    E -->|No| I[Start Insulin 0.1 U/kg/hr]
    I --> J[Fluid Resuscitation]
    J --> K[K+ Replacement in Fluids]
    K --> L{Glucose < 250?}
    L -->|No| M[Continue Current Rate]
    L -->|Yes| N[Reduce Insulin to 0.05 U/kg/hr]
    N --> O[Add D5 to Fluids]
    O --> P{DKA Resolved?}
    P -->|No| Q[Continue Protocol]
    P -->|Yes| R[Transition to SQ Insulin]
    R --> S[Overlap IV × 2 hours]
"""

ANAPHYLAXIS_FLOWCHART = """
graph TD
    A[Suspected Anaphylaxis] --> B{ABC Compromised?}
    B -->|Yes| C[CALL CODE]
    C --> D[Epinephrine 1mg IV]
    B -->|No| E{Skin/Mucosal + Respiratory OR Cardiovascular?}
    E -->|Yes| F[EPINEPHRINE 0.3-0.5mg IM]
    E -->|No| G[Monitor Closely]
    F --> H[High Flow O2]
    H --> I[IV Access × 2]
    I --> J[Fluid Bolus 1-2L]
    J --> K[H1 Blocker: Diphenhydramine]
    K --> L[H2 Blocker: Ranitidine]
    L --> M[Corticosteroids]
    M --> N{Improved in 5-15 min?}
    N -->|No| O[Repeat Epi IM]
    O --> P{Still Not Improving?}
    P -->|Yes| Q[Epinephrine Infusion]
    Q --> R[ICU Admission]
    N -->|Yes| S[Observe 4-6 Hours]
    P -->|No| S
    S --> T{Stable for Discharge?}
    T -->|Yes| U[Prescribe EpiPen]
    T -->|No| V[Admit for Monitoring]
"""


class FlowchartManager:
    """Manager for clinical decision flowcharts."""

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    def create_flowchart(
        self,
        title: str,
        description: str,
        mermaid_diagram: str,
        user_id: str,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Flowchart:
        """Create a new flowchart."""
        flowchart = Flowchart(
            protocol_id=protocol_id,
            title=title,
            description=description,
            mermaid_diagram=mermaid_diagram,
            created_by=user_id,
            organization_id=organization_id,
        )

        # In real implementation, would save to storage
        # self.storage.create_flowchart(flowchart)
        return flowchart

    def get_default_flowcharts(self) -> List[dict]:
        """Get pre-built flowchart templates."""
        return [
            {
                "id": "chest_pain",
                "title": "Chest Pain Decision Tree",
                "description": "Acute chest pain evaluation pathway",
                "mermaid_diagram": CHEST_PAIN_FLOWCHART,
            },
            {
                "id": "sepsis",
                "title": "Sepsis Management Algorithm",
                "description": "Sepsis recognition and early management",
                "mermaid_diagram": SEPSIS_FLOWCHART,
            },
            {
                "id": "stroke",
                "title": "Acute Stroke Pathway",
                "description": "Stroke evaluation and tPA decision tree",
                "mermaid_diagram": STROKE_FLOWCHART,
            },
            {
                "id": "dka",
                "title": "DKA Management Algorithm",
                "description": "Diabetic ketoacidosis treatment pathway",
                "mermaid_diagram": DKA_FLOWCHART,
            },
            {
                "id": "anaphylaxis",
                "title": "Anaphylaxis Treatment Algorithm",
                "description": "Immediate management of anaphylactic reactions",
                "mermaid_diagram": ANAPHYLAXIS_FLOWCHART,
            },
        ]

    def render_flowchart(self, flowchart_id: str) -> Optional[str]:
        """
        Render flowchart to SVG or PNG.

        In production, would use mermaid-cli or similar.
        For now, returns the Mermaid syntax.
        """
        flowcharts = self.get_default_flowcharts()
        for fc in flowcharts:
            if fc["id"] == flowchart_id:
                return fc["mermaid_diagram"]
        return None


# Default instance
_manager: Optional[FlowchartManager] = None


def get_flowchart_manager() -> FlowchartManager:
    """Get default flowchart manager."""
    global _manager
    if _manager is None:
        _manager = FlowchartManager()
    return _manager
