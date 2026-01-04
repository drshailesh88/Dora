"""
Procedural Checklists

Interactive checklists for clinical procedures with completion tracking.
"""

from typing import Optional, List, Dict
from datetime import datetime

from .models import (
    Checklist,
    ChecklistItem,
    ChecklistExecution,
    ChecklistStatus,
)
from .storage import ProtocolStorage, get_protocol_storage


# Pre-built checklist templates
SURGICAL_SAFETY_CHECKLIST = Checklist(
    title="WHO Surgical Safety Checklist",
    description="World Health Organization surgical safety checklist",
    items=[
        # SIGN IN (Before Induction of Anesthesia)
        ChecklistItem(
            text="Patient has confirmed identity, site, procedure, consent",
            required=True,
            order=1,
            section="Sign In",
        ),
        ChecklistItem(
            text="Site marked/not applicable",
            required=True,
            order=2,
            section="Sign In",
        ),
        ChecklistItem(
            text="Anesthesia safety check completed",
            required=True,
            order=3,
            section="Sign In",
        ),
        ChecklistItem(
            text="Pulse oximeter on patient and functioning",
            required=True,
            order=4,
            section="Sign In",
        ),
        ChecklistItem(
            text="Known allergy? No / Yes",
            required=True,
            order=5,
            section="Sign In",
        ),
        ChecklistItem(
            text="Difficult airway/aspiration risk? No / Yes, equipment available",
            required=True,
            order=6,
            section="Sign In",
        ),
        ChecklistItem(
            text="Risk of >500mL blood loss? No / Yes, IV access and fluids planned",
            required=True,
            order=7,
            section="Sign In",
        ),
        # TIME OUT (Before Skin Incision)
        ChecklistItem(
            text="All team members introduced by name and role",
            required=True,
            order=8,
            section="Time Out",
        ),
        ChecklistItem(
            text="Surgeon, anesthesia, and nursing confirm patient, site, procedure",
            required=True,
            order=9,
            section="Time Out",
        ),
        ChecklistItem(
            text="Anticipated critical events reviewed",
            required=True,
            order=10,
            section="Time Out",
        ),
        ChecklistItem(
            text="Antibiotic prophylaxis given <60 min? Yes / Not applicable",
            required=True,
            order=11,
            section="Time Out",
        ),
        ChecklistItem(
            text="Essential imaging displayed? Yes / Not applicable",
            required=True,
            order=12,
            section="Time Out",
        ),
        # SIGN OUT (Before Patient Leaves OR)
        ChecklistItem(
            text="Name of procedure recorded",
            required=True,
            order=13,
            section="Sign Out",
        ),
        ChecklistItem(
            text="Instrument, sponge, and needle counts correct",
            required=True,
            order=14,
            section="Sign Out",
        ),
        ChecklistItem(
            text="Specimen labeled (including patient name)",
            required=False,
            order=15,
            section="Sign Out",
        ),
        ChecklistItem(
            text="Any equipment problems addressed",
            required=True,
            order=16,
            section="Sign Out",
        ),
        ChecklistItem(
            text="Key concerns for recovery reviewed",
            required=True,
            order=17,
            section="Sign Out",
        ),
    ],
)

CENTRAL_LINE_CHECKLIST = Checklist(
    title="Central Line Insertion Checklist",
    description="Checklist for central venous catheter insertion",
    items=[
        ChecklistItem(
            text="Indication documented (justification for central line)",
            required=True,
            order=1,
            section="Pre-procedure",
        ),
        ChecklistItem(
            text="Informed consent obtained",
            required=True,
            order=2,
            section="Pre-procedure",
        ),
        ChecklistItem(
            text="Coagulation studies reviewed (INR, platelets)",
            required=True,
            order=3,
            section="Pre-procedure",
        ),
        ChecklistItem(
            text="Ultrasound machine available",
            required=True,
            order=4,
            section="Pre-procedure",
        ),
        ChecklistItem(
            text="Hand hygiene performed",
            required=True,
            order=5,
            section="Sterile Technique",
        ),
        ChecklistItem(
            text="Cap and mask worn",
            required=True,
            order=6,
            section="Sterile Technique",
        ),
        ChecklistItem(
            text="Sterile gown and gloves worn",
            required=True,
            order=7,
            section="Sterile Technique",
        ),
        ChecklistItem(
            text="Full barrier drapes used (large sterile drape)",
            required=True,
            order=8,
            section="Sterile Technique",
        ),
        ChecklistItem(
            text="Chlorhexidine skin prep performed (>30 seconds scrub)",
            required=True,
            order=9,
            section="Sterile Technique",
        ),
        ChecklistItem(
            text="Sterile ultrasound probe cover used",
            required=True,
            order=10,
            section="Procedure",
        ),
        ChecklistItem(
            text="Local anesthetic administered",
            required=True,
            order=11,
            section="Procedure",
        ),
        ChecklistItem(
            text="Ultrasound guidance used for venipuncture",
            required=True,
            order=12,
            section="Procedure",
        ),
        ChecklistItem(
            text="Guidewire position confirmed",
            required=True,
            order=13,
            section="Procedure",
        ),
        ChecklistItem(
            text="Catheter flushed and secured",
            required=True,
            order=14,
            section="Post-procedure",
        ),
        ChecklistItem(
            text="Sterile dressing applied",
            required=True,
            order=15,
            section="Post-procedure",
        ),
        ChecklistItem(
            text="Chest X-ray ordered for line placement confirmation",
            required=True,
            order=16,
            section="Post-procedure",
        ),
        ChecklistItem(
            text="Procedure documented (site, attempts, complications)",
            required=True,
            order=17,
            section="Post-procedure",
        ),
    ],
)

INTUBATION_CHECKLIST = Checklist(
    title="Rapid Sequence Intubation Checklist",
    description="Pre-intubation safety checklist",
    items=[
        ChecklistItem(
            text="Team roles assigned (airway, medications, monitoring)",
            required=True,
            order=1,
            section="Team Preparation",
        ),
        ChecklistItem(
            text="Suction equipment ready and tested",
            required=True,
            order=2,
            section="Equipment",
        ),
        ChecklistItem(
            text="Oxygen source connected and functioning",
            required=True,
            order=3,
            section="Equipment",
        ),
        ChecklistItem(
            text="Bag-valve mask available and tested",
            required=True,
            order=4,
            section="Equipment",
        ),
        ChecklistItem(
            text="Laryngoscope tested (light working)",
            required=True,
            order=5,
            section="Equipment",
        ),
        ChecklistItem(
            text="ETT size selected and cuff tested",
            required=True,
            order=6,
            section="Equipment",
        ),
        ChecklistItem(
            text="ETT one size smaller available",
            required=True,
            order=7,
            section="Equipment",
        ),
        ChecklistItem(
            text="Stylet prepared",
            required=True,
            order=8,
            section="Equipment",
        ),
        ChecklistItem(
            text="End-tidal CO2 detector ready",
            required=True,
            order=9,
            section="Equipment",
        ),
        ChecklistItem(
            text="Backup airway plan discussed (LMA, surgical airway)",
            required=True,
            order=10,
            section="Planning",
        ),
        ChecklistItem(
            text="Medications drawn and labeled",
            required=True,
            order=11,
            section="Medications",
        ),
        ChecklistItem(
            text="Pre-oxygenation completed (3-5 min, SpO2 100%)",
            required=True,
            order=12,
            section="Pre-procedure",
        ),
        ChecklistItem(
            text="Hemodynamically stable (or pressors ready)",
            required=True,
            order=13,
            section="Patient Assessment",
        ),
        ChecklistItem(
            text="Difficult airway assessment done (LEMON)",
            required=True,
            order=14,
            section="Patient Assessment",
        ),
    ],
)

DISCHARGE_CHECKLIST = Checklist(
    title="Hospital Discharge Checklist",
    description="Safe discharge planning checklist",
    items=[
        ChecklistItem(
            text="Discharge diagnosis documented",
            required=True,
            order=1,
            section="Documentation",
        ),
        ChecklistItem(
            text="Discharge summary completed",
            required=True,
            order=2,
            section="Documentation",
        ),
        ChecklistItem(
            text="Medication reconciliation performed",
            required=True,
            order=3,
            section="Medications",
        ),
        ChecklistItem(
            text="Discharge prescriptions written",
            required=True,
            order=4,
            section="Medications",
        ),
        ChecklistItem(
            text="Patient counseled on medication changes",
            required=True,
            order=5,
            section="Patient Education",
        ),
        ChecklistItem(
            text="Follow-up appointments scheduled",
            required=True,
            order=6,
            section="Follow-up",
        ),
        ChecklistItem(
            text="Red flag symptoms explained to patient",
            required=True,
            order=7,
            section="Patient Education",
        ),
        ChecklistItem(
            text="Contact number provided for questions",
            required=True,
            order=8,
            section="Patient Education",
        ),
        ChecklistItem(
            text="Home services arranged if needed (PT, nursing)",
            required=False,
            order=9,
            section="Coordination",
        ),
        ChecklistItem(
            text="Medical equipment ordered (oxygen, walker, etc.)",
            required=False,
            order=10,
            section="Coordination",
        ),
        ChecklistItem(
            text="Primary care physician notified",
            required=True,
            order=11,
            section="Communication",
        ),
    ],
)


class ChecklistManager:
    """Manager for procedural checklists."""

    def __init__(self, storage: Optional[ProtocolStorage] = None):
        self.storage = storage or get_protocol_storage()

    def create_checklist(
        self,
        title: str,
        description: str,
        items: List[ChecklistItem],
        user_id: str,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Checklist:
        """Create a new checklist."""
        checklist = Checklist(
            protocol_id=protocol_id,
            title=title,
            description=description,
            items=items,
            created_by=user_id,
            organization_id=organization_id,
        )

        self.storage.create_checklist(checklist)
        return checklist

    def get_checklist(self, checklist_id: str) -> Optional[Checklist]:
        """Get checklist by ID."""
        return self.storage.get_checklist(checklist_id)

    def list_checklists(
        self,
        protocol_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[Checklist]:
        """List checklists."""
        return self.storage.list_checklists(
            protocol_id=protocol_id,
            organization_id=organization_id,
        )

    def get_default_checklists(self) -> List[Checklist]:
        """Get pre-built checklist templates."""
        return [
            SURGICAL_SAFETY_CHECKLIST,
            CENTRAL_LINE_CHECKLIST,
            INTUBATION_CHECKLIST,
            DISCHARGE_CHECKLIST,
        ]

    # Execution tracking
    def start_execution(
        self,
        checklist_id: str,
        user_id: str,
        patient_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
    ) -> ChecklistExecution:
        """Start a new checklist execution."""
        execution = ChecklistExecution(
            checklist_id=checklist_id,
            user_id=user_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
        )

        self.storage.create_execution(execution)
        return execution

    def update_item_status(
        self,
        execution_id: str,
        item_id: str,
        status: ChecklistStatus,
        notes: Optional[str] = None,
    ) -> Optional[ChecklistExecution]:
        """Update the status of a checklist item."""
        # This would typically load from storage, but for simplicity:
        execution = ChecklistExecution(id=execution_id)
        # In real implementation, load from storage first

        execution.items_status[item_id] = status

        if notes:
            execution.items_notes[item_id] = notes

        # Calculate completion percentage
        checklist = self.storage.get_checklist(execution.checklist_id)
        if checklist:
            total_items = len(checklist.items)
            completed_items = sum(
                1 for s in execution.items_status.values()
                if s == ChecklistStatus.COMPLETED
            )
            execution.completion_percentage = (completed_items / total_items) * 100

            # Check if all required items completed
            required_items = [item for item in checklist.items if item.required]
            all_required_completed = all(
                execution.items_status.get(item.id) == ChecklistStatus.COMPLETED
                for item in required_items
            )

            if all_required_completed:
                execution.is_completed = True
                execution.completed_at = datetime.utcnow()

        self.storage.update_execution(execution)
        return execution

    def get_completion_stats(
        self,
        checklist_id: str,
        organization_id: Optional[str] = None,
    ) -> Dict:
        """Get completion statistics for a checklist."""
        # In real implementation, would query executions from storage
        return {
            "total_executions": 0,
            "completed": 0,
            "average_completion_time": None,
            "common_skipped_items": [],
        }


# Default instance
_manager: Optional[ChecklistManager] = None


def get_checklist_manager() -> ChecklistManager:
    """Get default checklist manager."""
    global _manager
    if _manager is None:
        _manager = ChecklistManager()
    return _manager
