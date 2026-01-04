"""Discharge Summary Generator for Dora.

Generates comprehensive hospital discharge summaries following medical standards.
"""

from datetime import datetime
from typing import Any, Optional

from ..llm.client import get_llm_client
from .models import Diagnosis, DischargeSummary, Medication, Patient, Provider


class DischargeSummaryGenerator:
    """Generate hospital discharge summaries using LLM."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize discharge summary generator.

        Args:
            model: LLM model to use for generation
        """
        self.llm = get_llm_client()
        self.model = model

    async def generate_from_admission(
        self,
        patient: Patient,
        provider: Provider,
        admission_data: dict[str, Any],
    ) -> DischargeSummary:
        """Generate discharge summary from admission data.

        Args:
            patient: Patient information
            provider: Discharging provider
            admission_data: Dictionary with admission details, hospital course, etc.

        Returns:
            Discharge summary in draft status
        """
        # Extract basic information
        admission_date = self._parse_date(admission_data.get("admission_date"))
        discharge_date = self._parse_date(
            admission_data.get("discharge_date", datetime.now())
        )

        # Calculate length of stay
        los = (discharge_date - admission_date).days if admission_date else None

        # Build discharge summary
        return DischargeSummary(
            patient=patient,
            provider=provider,
            admission_date=admission_date or datetime.now(),
            discharge_date=discharge_date,
            length_of_stay=los,
            admission_department=admission_data.get("admission_department", "Unknown"),
            discharge_department=admission_data.get("discharge_department", "Unknown"),
            chief_complaint=admission_data.get("chief_complaint", ""),
            admitting_diagnosis=admission_data.get("admitting_diagnosis", ""),
            final_diagnosis=self._extract_diagnoses(
                admission_data.get("final_diagnosis", [])
            ),
            hospital_course=admission_data.get("hospital_course", ""),
            procedures_performed=admission_data.get("procedures_performed", []),
            consultations=admission_data.get("consultations", []),
            condition_at_discharge=admission_data.get(
                "condition_at_discharge", "Stable"
            ),
            discharge_medications=self._extract_medications(
                admission_data.get("discharge_medications", [])
            ),
            discharge_instructions=admission_data.get("discharge_instructions", ""),
            diet_restrictions=admission_data.get("diet_restrictions"),
            activity_restrictions=admission_data.get("activity_restrictions"),
            followup_instructions=admission_data.get(
                "followup_instructions",
                "Follow up with primary care physician in 1 week",
            ),
            followup_date=self._parse_date(admission_data.get("followup_date")),
            followup_provider=admission_data.get("followup_provider"),
            warning_signs=admission_data.get("warning_signs", []),
        )

    async def generate_from_text(
        self,
        text: str,
        patient: Patient,
        provider: Provider,
    ) -> DischargeSummary:
        """Generate discharge summary from free-text hospital course.

        Args:
            text: Free-text description of hospital stay
            patient: Patient information
            provider: Provider information

        Returns:
            Generated discharge summary
        """
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(text)

        # Call LLM to extract structured data
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

        # Build discharge summary from extracted data
        return await self.generate_from_admission(patient, provider, extracted)

    async def enhance_with_ai(
        self, discharge_summary: DischargeSummary
    ) -> DischargeSummary:
        """Enhance discharge summary with AI-generated instructions and warnings.

        Args:
            discharge_summary: Existing discharge summary

        Returns:
            Enhanced discharge summary
        """
        # Build prompt for enhancement
        prompt = f"""You are a medical documentation assistant. Review this discharge summary and provide:
1. Clear, patient-friendly discharge instructions
2. Warning signs the patient should watch for
3. Diet and activity recommendations

DISCHARGE SUMMARY:
Diagnosis: {[d.description for d in discharge_summary.final_diagnosis]}
Medications: {[m.name for m in discharge_summary.discharge_medications]}
Procedures: {discharge_summary.procedures_performed}
Condition: {discharge_summary.condition_at_discharge}

Provide response in JSON:
{{
    "discharge_instructions": "Clear instructions for patient",
    "warning_signs": ["Sign 1", "Sign 2"],
    "diet_restrictions": "Diet advice",
    "activity_restrictions": "Activity advice"
}}
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.model, temperature=0.3, response_format="json"
        )

        import json

        try:
            enhanced = json.loads(response)
            discharge_summary.discharge_instructions = enhanced.get(
                "discharge_instructions", discharge_summary.discharge_instructions
            )
            discharge_summary.warning_signs = enhanced.get(
                "warning_signs", discharge_summary.warning_signs
            )
            discharge_summary.diet_restrictions = enhanced.get(
                "diet_restrictions", discharge_summary.diet_restrictions
            )
            discharge_summary.activity_restrictions = enhanced.get(
                "activity_restrictions", discharge_summary.activity_restrictions
            )
        except json.JSONDecodeError:
            pass  # Keep original if parsing fails

        return discharge_summary

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for extracting discharge summary components.

        Args:
            text: Hospital course text

        Returns:
            Prompt for LLM
        """
        return f"""You are a medical documentation assistant. Extract discharge summary components from the following hospital course.

HOSPITAL COURSE:
{text}

Extract the following in JSON format:
{{
    "admission_date": "YYYY-MM-DD",
    "discharge_date": "YYYY-MM-DD",
    "admission_department": "Department",
    "discharge_department": "Department",
    "chief_complaint": "Why patient was admitted",
    "admitting_diagnosis": "Initial diagnosis",
    "final_diagnosis": [
        {{
            "description": "Final diagnosis",
            "icd10_code": "Code if known",
            "is_primary": true
        }}
    ],
    "hospital_course": "Detailed narrative of hospital stay",
    "procedures_performed": ["Procedure 1", "Procedure 2"],
    "consultations": ["Cardiology", "Nephrology"],
    "condition_at_discharge": "Improved/Stable/Critical",
    "discharge_medications": [
        {{
            "name": "Drug name",
            "dosage": "Dose",
            "route": "PO/IV",
            "frequency": "BID/TID",
            "duration": "7 days",
            "instructions": "Special instructions"
        }}
    ],
    "discharge_instructions": "What patient should do at home",
    "diet_restrictions": "Diet advice",
    "activity_restrictions": "Activity limitations",
    "followup_instructions": "When and where to follow up",
    "followup_date": "YYYY-MM-DD",
    "followup_provider": "Provider name",
    "warning_signs": ["Sign to watch for 1", "Sign 2"]
}}

IMPORTANT:
- Extract only explicitly mentioned information
- Use null for missing data
- Dates in YYYY-MM-DD format
- Be thorough with hospital course narrative
"""

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats.

        Args:
            date_value: Date value (string, datetime, or None)

        Returns:
            datetime object or None
        """
        if not date_value:
            return None
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                return None
        return None

    def _extract_diagnoses(self, data: list[dict[str, Any]]) -> list[Diagnosis]:
        """Extract diagnoses from data."""
        diagnoses = []
        for diag in data:
            if "onset_date" in diag and isinstance(diag["onset_date"], str):
                diag["onset_date"] = datetime.fromisoformat(diag["onset_date"])
            diagnoses.append(Diagnosis(**diag))
        return diagnoses

    def _extract_medications(self, data: list[dict[str, Any]]) -> list[Medication]:
        """Extract medications from data."""
        return [Medication(**med) for med in data]


async def generate_discharge_summary(
    patient: Patient,
    provider: Provider,
    admission_data: dict[str, Any],
    enhance: bool = True,
    model: str = "claude-3-5-sonnet-20241022",
) -> DischargeSummary:
    """Convenience function to generate discharge summary.

    Args:
        patient: Patient information
        provider: Provider information
        admission_data: Admission and hospital course data
        enhance: Whether to enhance with AI-generated instructions
        model: LLM model to use

    Returns:
        Discharge summary
    """
    generator = DischargeSummaryGenerator(model=model)
    summary = await generator.generate_from_admission(patient, provider, admission_data)

    if enhance:
        summary = await generator.enhance_with_ai(summary)

    return summary
