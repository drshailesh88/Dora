"""Operative Note Generator for Dora.

Generates detailed operative/surgical notes.
"""

from datetime import datetime
from typing import Any, Optional

from ..llm.client import get_llm_client
from .models import OperativeNote, Patient, Provider


class OperativeNoteGenerator:
    """Generate operative/surgical notes using LLM."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize operative note generator.

        Args:
            model: LLM model to use for generation
        """
        self.llm = get_llm_client()
        self.model = model

    async def generate(
        self,
        patient: Patient,
        surgeon: Provider,
        operative_data: dict[str, Any],
        assistants: Optional[list[Provider]] = None,
    ) -> OperativeNote:
        """Generate operative note.

        Args:
            patient: Patient information
            surgeon: Primary surgeon
            operative_data: Dictionary with operative details
            assistants: Assistant surgeons

        Returns:
            Operative note in draft status
        """
        return OperativeNote(
            patient=patient,
            surgeon=surgeon,
            assistants=assistants or [],
            date=self._parse_date(operative_data.get("date", datetime.now())),
            preop_diagnosis=operative_data.get("preop_diagnosis", ""),
            indication_for_surgery=operative_data.get("indication_for_surgery", ""),
            procedure_performed=operative_data.get("procedure_performed", ""),
            procedure_type=operative_data.get("procedure_type", "Elective"),
            anesthesia_type=operative_data.get("anesthesia_type", "General"),
            anesthesiologist=operative_data.get("anesthesiologist"),
            operative_findings=operative_data.get("operative_findings", ""),
            technique=operative_data.get("technique", ""),
            estimated_blood_loss=operative_data.get("estimated_blood_loss"),
            specimens_sent=operative_data.get("specimens_sent", []),
            complications=operative_data.get("complications"),
            implants_used=operative_data.get("implants_used", []),
            postop_diagnosis=operative_data.get("postop_diagnosis", ""),
            postop_condition=operative_data.get("postop_condition", "Stable"),
            postop_destination=operative_data.get("postop_destination", "Recovery room"),
            postop_instructions=operative_data.get("postop_instructions", ""),
        )

    async def generate_from_dictation(
        self,
        dictation: str,
        patient: Patient,
        surgeon: Provider,
        assistants: Optional[list[Provider]] = None,
    ) -> OperativeNote:
        """Generate operative note from surgeon's dictation.

        Args:
            dictation: Surgeon's dictated operative note
            patient: Patient information
            surgeon: Surgeon
            assistants: Assistant surgeons

        Returns:
            Structured operative note
        """
        # Build extraction prompt
        prompt = self._build_extraction_prompt(dictation)

        # Call LLM to structure the dictation
        response = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.1,
            response_format="json",
        )

        # Parse response
        import json

        try:
            extracted = json.loads(response)
        except json.JSONDecodeError:
            extracted = {}

        # Generate operative note
        return await self.generate(patient, surgeon, extracted, assistants)

    def _build_extraction_prompt(self, dictation: str) -> str:
        """Build prompt for extracting operative note components.

        Args:
            dictation: Surgeon's dictation

        Returns:
            Prompt for LLM
        """
        return f"""You are a medical documentation assistant. Structure this surgical dictation into a formal operative note.

SURGICAL DICTATION:
{dictation}

Extract the following in JSON format:
{{
    "date": "YYYY-MM-DD",
    "preop_diagnosis": "Pre-operative diagnosis",
    "indication_for_surgery": "Why surgery was indicated",
    "procedure_performed": "Full name of procedure",
    "procedure_type": "Elective/Emergency",
    "anesthesia_type": "General/Spinal/Local/Regional",
    "anesthesiologist": "Anesthesiologist name if mentioned",
    "operative_findings": "What was found during surgery",
    "technique": "Detailed surgical technique - step by step",
    "estimated_blood_loss": "EBL if mentioned",
    "specimens_sent": ["Specimens sent to pathology"],
    "complications": "Complications if any",
    "implants_used": ["Implants/prosthetics used"],
    "postop_diagnosis": "Post-operative diagnosis",
    "postop_condition": "Patient condition after surgery",
    "postop_destination": "Where patient went (Recovery/ICU/Ward)",
    "postop_instructions": "Post-operative instructions"
}}

IMPORTANT:
- Be thorough with surgical technique
- Preserve medical terminology
- Extract only what is mentioned
- Use null for missing information
"""

    def _parse_date(self, date_value: Any) -> datetime:
        """Parse date from various formats."""
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                return datetime.now()
        return datetime.now()

    def format_operative_note(self, op_note: OperativeNote) -> str:
        """Format operative note for printing.

        Args:
            op_note: Operative note

        Returns:
            Formatted operative note
        """
        lines = ["OPERATIVE NOTE", "=" * 70, ""]

        # Patient and surgeon details
        lines.append(
            f"Patient: {op_note.patient.name} ({op_note.patient.age}/{op_note.patient.gender[0]})"
        )
        if op_note.patient.mrn:
            lines.append(f"MRN: {op_note.patient.mrn}")
        lines.append(f"Date of Surgery: {op_note.date.strftime('%d-%b-%Y')}")
        lines.append("")

        lines.append(f"Surgeon: {op_note.surgeon.name}")
        if op_note.assistants:
            assistant_names = ", ".join([a.name for a in op_note.assistants])
            lines.append(f"Assistants: {assistant_names}")
        if op_note.anesthesiologist:
            lines.append(f"Anesthesiologist: {op_note.anesthesiologist}")
        lines.append(f"Anesthesia: {op_note.anesthesia_type}")
        lines.append("")

        # Pre-operative
        lines.append("-" * 70)
        lines.append("PRE-OPERATIVE DIAGNOSIS:")
        lines.append(op_note.preop_diagnosis)
        lines.append("")

        lines.append("INDICATION FOR SURGERY:")
        lines.append(op_note.indication_for_surgery)
        lines.append("")

        # Procedure
        lines.append("-" * 70)
        lines.append("PROCEDURE PERFORMED:")
        lines.append(op_note.procedure_performed)
        lines.append(f"Type: {op_note.procedure_type}")
        lines.append("")

        # Operative details
        lines.append("-" * 70)
        lines.append("OPERATIVE FINDINGS:")
        lines.append(op_note.operative_findings)
        lines.append("")

        lines.append("SURGICAL TECHNIQUE:")
        lines.append(op_note.technique)
        lines.append("")

        if op_note.estimated_blood_loss:
            lines.append(f"Estimated Blood Loss: {op_note.estimated_blood_loss}")
            lines.append("")

        if op_note.specimens_sent:
            lines.append("SPECIMENS SENT TO PATHOLOGY:")
            for specimen in op_note.specimens_sent:
                lines.append(f"  - {specimen}")
            lines.append("")

        if op_note.implants_used:
            lines.append("IMPLANTS/PROSTHETICS USED:")
            for implant in op_note.implants_used:
                lines.append(f"  - {implant}")
            lines.append("")

        if op_note.complications:
            lines.append("COMPLICATIONS:")
            lines.append(op_note.complications)
            lines.append("")

        # Post-operative
        lines.append("-" * 70)
        lines.append("POST-OPERATIVE DIAGNOSIS:")
        lines.append(op_note.postop_diagnosis)
        lines.append("")

        lines.append(f"Patient Condition: {op_note.postop_condition}")
        lines.append(f"Transferred to: {op_note.postop_destination}")
        lines.append("")

        lines.append("POST-OPERATIVE INSTRUCTIONS:")
        lines.append(op_note.postop_instructions)
        lines.append("")

        # Signature
        lines.append("-" * 70)
        lines.append("_" * 30)
        lines.append(f"{op_note.surgeon.name}")
        if op_note.surgeon.qualification:
            lines.append(op_note.surgeon.qualification)
        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


async def generate_operative_note(
    patient: Patient,
    surgeon: Provider,
    operative_data: dict[str, Any],
    assistants: Optional[list[Provider]] = None,
    model: str = "claude-3-5-sonnet-20241022",
) -> OperativeNote:
    """Convenience function to generate operative note.

    Args:
        patient: Patient information
        surgeon: Primary surgeon
        operative_data: Operative details
        assistants: Assistant surgeons
        model: LLM model to use

    Returns:
        Operative note
    """
    generator = OperativeNoteGenerator(model=model)
    return await generator.generate(patient, surgeon, operative_data, assistants)
