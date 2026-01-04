"""SOAP Note Generator for Dora.

Generates SOAP (Subjective, Objective, Assessment, Plan) format clinical notes
from voice transcription, structured input, or EMR data.
"""

from datetime import datetime
from typing import Any, Optional

from ..llm.client import get_llm_client
from .models import (
    Diagnosis,
    Investigation,
    Medication,
    Patient,
    Provider,
    SOAPNote,
    Vitals,
)


class SOAPNoteGenerator:
    """Generate SOAP format clinical notes using LLM."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize SOAP note generator.

        Args:
            model: LLM model to use for generation
        """
        self.llm = get_llm_client()
        self.model = model

    async def generate_from_text(
        self,
        text: str,
        patient: Optional[Patient] = None,
        provider: Optional[Provider] = None,
    ) -> SOAPNote:
        """Generate SOAP note from free-text input (e.g., voice transcription).

        Args:
            text: Free-text clinical encounter description
            patient: Patient information (if available)
            provider: Provider information

        Returns:
            Generated SOAP note in draft status
        """
        # Build prompt for LLM
        prompt = self._build_extraction_prompt(text)

        # Call LLM to extract structured data
        response = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.1,  # Low temperature for structured extraction
            response_format="json",
        )

        # Parse response into structured format
        extracted = self._parse_llm_response(response)

        # Build SOAP note
        soap_note = self._build_soap_note(
            extracted=extracted, patient=patient, provider=provider
        )

        return soap_note

    async def generate_from_structured(
        self,
        data: dict[str, Any],
        patient: Optional[Patient] = None,
        provider: Optional[Provider] = None,
    ) -> SOAPNote:
        """Generate SOAP note from structured input data.

        Args:
            data: Dictionary with SOAP sections
            patient: Patient information
            provider: Provider information

        Returns:
            SOAP note
        """
        return SOAPNote(
            patient=patient or self._extract_patient(data),
            provider=provider or self._extract_provider(data),
            chief_complaint=data.get("chief_complaint", ""),
            history_present_illness=data.get("history_present_illness", ""),
            past_medical_history=data.get("past_medical_history"),
            medications=self._extract_medications(data.get("medications", [])),
            allergies=data.get("allergies", []),
            social_history=data.get("social_history"),
            family_history=data.get("family_history"),
            review_of_systems=data.get("review_of_systems"),
            vitals=self._extract_vitals(data.get("vitals", {})),
            general_exam=data.get("general_exam"),
            system_exams=data.get("system_exams", {}),
            investigations=self._extract_investigations(data.get("investigations", [])),
            diagnoses=self._extract_diagnoses(data.get("diagnoses", [])),
            differential_diagnoses=data.get("differential_diagnoses", []),
            plan_medications=self._extract_medications(
                data.get("plan_medications", [])
            ),
            plan_investigations=data.get("plan_investigations", []),
            plan_procedures=data.get("plan_procedures", []),
            plan_referrals=data.get("plan_referrals", []),
            plan_followup=data.get("plan_followup"),
            plan_patient_education=data.get("plan_patient_education"),
        )

    async def generate_from_emr(
        self, patient_id: str, encounter_id: str, provider: Provider
    ) -> SOAPNote:
        """Generate SOAP note from EMR data.

        Args:
            patient_id: Patient ID in EMR
            encounter_id: Encounter ID in EMR
            provider: Provider information

        Returns:
            SOAP note pre-filled with EMR data
        """
        # TODO: Integrate with DocAssist EMR
        # For now, return a template
        raise NotImplementedError("EMR integration pending")

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for extracting SOAP components from text.

        Args:
            text: Clinical encounter text

        Returns:
            Prompt for LLM
        """
        return f"""You are a medical documentation assistant. Extract SOAP note components from the following clinical encounter.

ENCOUNTER TEXT:
{text}

Extract the following in JSON format:
{{
    "subjective": {{
        "chief_complaint": "Main reason for visit",
        "history_present_illness": "Detailed HPI",
        "past_medical_history": "Relevant PMH",
        "medications": ["Current medications"],
        "allergies": ["Known allergies"],
        "social_history": "Social history",
        "family_history": "Family history",
        "review_of_systems": "ROS findings"
    }},
    "objective": {{
        "vitals": {{
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature": 98.6,
            "spo2": 98
        }},
        "general_exam": "General examination findings",
        "system_exams": {{
            "cardiovascular": "CV exam",
            "respiratory": "Resp exam",
            "abdomen": "Abd exam"
        }},
        "investigations": [
            {{
                "name": "Test name",
                "result": "Result",
                "value": "Value",
                "flag": "H/L/N"
            }}
        ]
    }},
    "assessment": {{
        "diagnoses": [
            {{
                "description": "Diagnosis",
                "icd10_code": "Code if mentioned",
                "is_primary": true
            }}
        ],
        "differential_diagnoses": ["DDx1", "DDx2"]
    }},
    "plan": {{
        "medications": [
            {{
                "name": "Drug name",
                "dosage": "Dose",
                "route": "Route",
                "frequency": "Frequency",
                "duration": "Duration"
            }}
        ],
        "investigations": ["Tests to order"],
        "procedures": ["Procedures"],
        "referrals": ["Referrals"],
        "followup": "Follow-up plan",
        "patient_education": "Patient instructions"
    }}
}}

IMPORTANT:
- Extract only information explicitly mentioned
- Do not make up vital signs or lab values
- Use null for missing information
- Use standard medical abbreviations
- Include ICD-10 codes if mentioned
"""

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse LLM JSON response.

        Args:
            response: LLM response (JSON string)

        Returns:
            Parsed dictionary
        """
        import json

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty structure
            return {
                "subjective": {},
                "objective": {},
                "assessment": {},
                "plan": {},
            }

    def _build_soap_note(
        self,
        extracted: dict[str, Any],
        patient: Optional[Patient],
        provider: Optional[Provider],
    ) -> SOAPNote:
        """Build SOAP note from extracted data.

        Args:
            extracted: Extracted data from LLM
            patient: Patient information
            provider: Provider information

        Returns:
            SOAP note
        """
        subj = extracted.get("subjective", {})
        obj = extracted.get("objective", {})
        assess = extracted.get("assessment", {})
        plan = extracted.get("plan", {})

        return SOAPNote(
            patient=patient or Patient(name="Unknown", age=0, gender="Unknown"),
            provider=provider or Provider(name="Unknown"),
            chief_complaint=subj.get("chief_complaint", ""),
            history_present_illness=subj.get("history_present_illness", ""),
            past_medical_history=subj.get("past_medical_history"),
            medications=self._extract_medications(subj.get("medications", [])),
            allergies=subj.get("allergies", []),
            social_history=subj.get("social_history"),
            family_history=subj.get("family_history"),
            review_of_systems=subj.get("review_of_systems"),
            vitals=self._extract_vitals(obj.get("vitals", {})),
            general_exam=obj.get("general_exam"),
            system_exams=obj.get("system_exams", {}),
            investigations=self._extract_investigations(obj.get("investigations", [])),
            diagnoses=self._extract_diagnoses(assess.get("diagnoses", [])),
            differential_diagnoses=assess.get("differential_diagnoses", []),
            plan_medications=self._extract_medications(plan.get("medications", [])),
            plan_investigations=plan.get("investigations", []),
            plan_procedures=plan.get("procedures", []),
            plan_referrals=plan.get("referrals", []),
            plan_followup=plan.get("followup"),
            plan_patient_education=plan.get("patient_education"),
        )

    def _extract_patient(self, data: dict[str, Any]) -> Patient:
        """Extract patient from data."""
        patient_data = data.get("patient", {})
        return Patient(
            name=patient_data.get("name", "Unknown"),
            age=patient_data.get("age", 0),
            gender=patient_data.get("gender", "Unknown"),
            mrn=patient_data.get("mrn"),
            contact=patient_data.get("contact"),
            address=patient_data.get("address"),
        )

    def _extract_provider(self, data: dict[str, Any]) -> Provider:
        """Extract provider from data."""
        provider_data = data.get("provider", {})
        return Provider(
            name=provider_data.get("name", "Unknown"),
            qualification=provider_data.get("qualification"),
            registration_number=provider_data.get("registration_number"),
            specialty=provider_data.get("specialty"),
            contact=provider_data.get("contact"),
        )

    def _extract_vitals(self, data: dict[str, Any]) -> Optional[Vitals]:
        """Extract vitals from data."""
        if not data:
            return None
        return Vitals(**data)

    def _extract_medications(self, data: list[dict[str, Any]]) -> list[Medication]:
        """Extract medications from data."""
        return [Medication(**med) for med in data]

    def _extract_investigations(
        self, data: list[dict[str, Any]]
    ) -> list[Investigation]:
        """Extract investigations from data."""
        investigations = []
        for inv in data:
            if "date" in inv and isinstance(inv["date"], str):
                inv["date"] = datetime.fromisoformat(inv["date"])
            investigations.append(Investigation(**inv))
        return investigations

    def _extract_diagnoses(self, data: list[dict[str, Any]]) -> list[Diagnosis]:
        """Extract diagnoses from data."""
        diagnoses = []
        for diag in data:
            if "onset_date" in diag and isinstance(diag["onset_date"], str):
                diag["onset_date"] = datetime.fromisoformat(diag["onset_date"])
            diagnoses.append(Diagnosis(**diag))
        return diagnoses


async def generate_soap_note(
    text: str,
    patient: Optional[Patient] = None,
    provider: Optional[Provider] = None,
    model: str = "claude-3-5-sonnet-20241022",
) -> SOAPNote:
    """Convenience function to generate SOAP note from text.

    Args:
        text: Clinical encounter text
        patient: Patient information
        provider: Provider information
        model: LLM model to use

    Returns:
        Generated SOAP note
    """
    generator = SOAPNoteGenerator(model=model)
    return await generator.generate_from_text(text, patient, provider)
