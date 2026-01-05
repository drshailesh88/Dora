"""Information Extractor for Clinical Documentation.

Extracts structured medical information from unstructured text using NER and LLM.
"""

import re
from datetime import datetime
from typing import Any, Optional

from ..llm.client import get_llm_client
from .models import Diagnosis, Investigation, Medication, Patient, Provider, Vitals


class MedicalInformationExtractor:
    """Extract structured medical information from text."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize extractor.

        Args:
            model: LLM model to use for extraction
        """
        self.llm = get_llm_client()
        self.model = model

    async def extract_from_text(self, text: str) -> dict[str, Any]:
        """Extract all medical entities from text.

        Args:
            text: Clinical text (transcript, note, etc.)

        Returns:
            Dictionary with extracted entities
        """
        prompt = f"""You are a medical NER (Named Entity Recognition) system. Extract all medical entities from the text.

TEXT:
{text}

Extract in JSON format:
{{
    "patient": {{
        "name": "Patient name if mentioned",
        "age": age_number,
        "gender": "Male/Female",
        "mrn": "Medical record number if mentioned"
    }},
    "provider": {{
        "name": "Provider name if mentioned",
        "qualification": "Qualifications if mentioned"
    }},
    "chief_complaint": "Main complaint",
    "diagnoses": [
        {{
            "description": "Diagnosis name",
            "icd10_code": "ICD-10 code if mentioned",
            "is_primary": true/false
        }}
    ],
    "medications": [
        {{
            "name": "Drug name",
            "dosage": "Dose with unit",
            "route": "PO/IV/IM/SC",
            "frequency": "Once daily/BID/TID/QID",
            "duration": "Duration if mentioned"
        }}
    ],
    "vitals": {{
        "bp_systolic": systolic_bp,
        "bp_diastolic": diastolic_bp,
        "heart_rate": hr,
        "respiratory_rate": rr,
        "temperature": temp,
        "spo2": oxygen_sat,
        "weight": weight_kg,
        "height": height_cm
    }},
    "investigations": [
        {{
            "name": "Test name",
            "result": "Result description",
            "value": "Numeric value",
            "unit": "Unit",
            "flag": "H/L/N for high/low/normal"
        }}
    ],
    "allergies": ["Allergy1", "Allergy2"],
    "procedures": ["Procedure1", "Procedure2"],
    "dates": {{
        "admission": "YYYY-MM-DD if mentioned",
        "discharge": "YYYY-MM-DD if mentioned",
        "followup": "YYYY-MM-DD if mentioned"
    }}
}}

IMPORTANT:
- Extract only what is explicitly mentioned
- Use null for missing information
- Normalize drug names to generic names
- Use standard medical abbreviations
- For ICD-10, only include if explicitly mentioned
"""

        response = await self.llm.generate(
            prompt=prompt,
            model=self.model,
            temperature=0.1,
            response_format="json",
        )

        import json

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    async def extract_medications(self, text: str) -> list[Medication]:
        """Extract medications from text.

        Args:
            text: Text containing medication information

        Returns:
            List of Medication objects
        """
        extracted = await self.extract_from_text(text)
        med_data = extracted.get("medications", [])
        return [Medication(**med) for med in med_data]

    async def extract_diagnoses(self, text: str) -> list[Diagnosis]:
        """Extract diagnoses from text.

        Args:
            text: Text containing diagnosis information

        Returns:
            List of Diagnosis objects
        """
        extracted = await self.extract_from_text(text)
        diag_data = extracted.get("diagnoses", [])
        return [Diagnosis(**diag) for diag in diag_data]

    async def extract_vitals(self, text: str) -> Optional[Vitals]:
        """Extract vital signs from text.

        Args:
            text: Text containing vital signs

        Returns:
            Vitals object or None
        """
        extracted = await self.extract_from_text(text)
        vitals_data = extracted.get("vitals", {})

        if not vitals_data or all(v is None for v in vitals_data.values()):
            return None

        return Vitals(**vitals_data)

    async def extract_patient(self, text: str) -> Optional[Patient]:
        """Extract patient information from text.

        Args:
            text: Text containing patient information

        Returns:
            Patient object or None
        """
        extracted = await self.extract_from_text(text)
        patient_data = extracted.get("patient", {})

        if not patient_data or not patient_data.get("name"):
            return None

        return Patient(**patient_data)

    async def extract_provider(self, text: str) -> Optional[Provider]:
        """Extract provider information from text.

        Args:
            text: Text containing provider information

        Returns:
            Provider object or None
        """
        extracted = await self.extract_from_text(text)
        provider_data = extracted.get("provider", {})

        if not provider_data or not provider_data.get("name"):
            return None

        return Provider(**provider_data)

    def extract_icd10_codes(self, text: str) -> list[str]:
        """Extract ICD-10 codes from text using regex.

        Args:
            text: Text containing ICD-10 codes

        Returns:
            List of ICD-10 codes
        """
        # ICD-10 format: Letter followed by 2-3 digits, optional decimal and 1-2 more digits
        # Examples: A01, A01.0, A01.00, Z99.89
        pattern = r"\b[A-TV-Z][0-9]{2}(?:\.[0-9]{1,2})?\b"
        codes = re.findall(pattern, text.upper())
        return list(set(codes))  # Remove duplicates

    def extract_drug_names(self, text: str) -> list[str]:
        """Extract potential drug names from text.

        Uses simple heuristics - for production, use a medical NER model.

        Args:
            text: Text containing drug names

        Returns:
            List of potential drug names
        """
        # Common drug suffixes
        suffixes = [
            "mycin",
            "cillin",
            "azole",
            "pril",
            "olol",
            "statin",
            "zepam",
            "pine",
            "done",
            "ine",
            "mab",
            "nib",
        ]

        words = text.split()
        drug_names = []

        for word in words:
            word_clean = re.sub(r"[^a-zA-Z]", "", word).lower()
            # Check if word ends with common drug suffix
            if any(word_clean.endswith(suffix) for suffix in suffixes):
                drug_names.append(word_clean.capitalize())

        return drug_names

    async def extract_from_voice_transcript(
        self, transcript: str
    ) -> dict[str, Any]:
        """Extract structured data from voice transcript.

        Voice transcripts may have filler words, corrections, and informal language.

        Args:
            transcript: Voice transcript

        Returns:
            Extracted structured data
        """
        # Clean up transcript first
        cleaned = self._clean_transcript(transcript)

        # Extract using standard method
        return await self.extract_from_text(cleaned)

    def _clean_transcript(self, transcript: str) -> str:
        """Clean voice transcript for better extraction.

        Args:
            transcript: Raw voice transcript

        Returns:
            Cleaned transcript
        """
        # Remove common filler words
        fillers = [
            "um",
            "uh",
            "like",
            "you know",
            "so",
            "basically",
            "actually",
            "literally",
        ]
        cleaned = transcript.lower()

        for filler in fillers:
            cleaned = re.sub(rf"\b{filler}\b", "", cleaned)

        # Remove multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip()

    async def extract_from_emr_data(self, emr_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and normalize data from EMR.

        Args:
            emr_data: Raw EMR data (from DocAssist EMR models)

        Returns:
            Normalized data for documentation
        """
        from ..emr.models import (
            Patient as EMRPatient,
            Medication as EMRMedication,
            Diagnosis as EMRDiagnosis,
            VitalSigns as EMRVitals,
            LabResult,
            PatientSummary,
        )

        # If it's a PatientSummary, extract comprehensive data
        if isinstance(emr_data, PatientSummary):
            normalized = {
                "patient": {
                    "name": emr_data.patient.name,
                    "age": emr_data.patient.age,
                    "gender": emr_data.patient.gender.value,
                    "mrn": emr_data.patient.mrn,
                    "contact": emr_data.patient.phone,
                    "address": emr_data.patient.address,
                },
                "medications": [
                    {
                        "name": med.drug_name,
                        "dosage": med.dosage,
                        "route": med.route,
                        "frequency": med.frequency,
                        "duration": med.duration,
                        "indication": med.indication,
                    }
                    for med in emr_data.current_medications
                ],
                "allergies": [
                    allergy.allergen
                    for allergy in emr_data.allergies
                ],
                "diagnoses": [
                    {
                        "description": dx.diagnosis_name,
                        "icd10_code": dx.diagnosis_code,
                        "is_primary": dx.diagnosis_type == "primary",
                        "status": "chronic" if dx.is_chronic else "active",
                    }
                    for dx in emr_data.active_diagnoses
                ],
                "vitals": None,
                "investigations": [],
            }

            # Add vitals if available
            if emr_data.recent_vitals:
                v = emr_data.recent_vitals
                normalized["vitals"] = {
                    "bp_systolic": v.blood_pressure_systolic,
                    "bp_diastolic": v.blood_pressure_diastolic,
                    "heart_rate": v.heart_rate,
                    "respiratory_rate": v.respiratory_rate,
                    "temperature": v.temperature_c,
                    "spo2": v.spo2,
                    "weight": v.weight_kg,
                    "height": v.height_cm,
                    "bmi": v.bmi,
                }

            # Add lab results
            normalized["investigations"] = [
                {
                    "name": lab.test_name,
                    "result": lab.result,
                    "unit": lab.unit,
                    "normal_range": lab.reference_range,
                    "flag": lab.abnormal_flag,
                    "date": lab.test_date.isoformat() if lab.test_date else None,
                }
                for lab in emr_data.recent_labs
            ]

            return normalized

        # If it's a raw dict, try to map known fields
        elif isinstance(emr_data, dict):
            normalized = {}

            # Map patient data
            if "patient" in emr_data:
                p = emr_data["patient"]
                normalized["patient"] = {
                    "name": p.get("name"),
                    "age": p.get("age"),
                    "gender": p.get("gender"),
                    "mrn": p.get("mrn") or p.get("uhid"),
                    "contact": p.get("phone") or p.get("contact"),
                    "address": p.get("address"),
                }

            # Map medications
            if "medications" in emr_data:
                normalized["medications"] = [
                    {
                        "name": m.get("drug_name") or m.get("name"),
                        "dosage": m.get("dosage"),
                        "route": m.get("route", "PO"),
                        "frequency": m.get("frequency"),
                        "duration": m.get("duration"),
                    }
                    for m in emr_data["medications"]
                ]

            # Map diagnoses
            if "diagnoses" in emr_data:
                normalized["diagnoses"] = [
                    {
                        "description": d.get("diagnosis_name") or d.get("description"),
                        "icd10_code": d.get("diagnosis_code") or d.get("icd10_code"),
                        "is_primary": d.get("diagnosis_type") == "primary",
                    }
                    for d in emr_data["diagnoses"]
                ]

            # Map allergies
            if "allergies" in emr_data:
                normalized["allergies"] = [
                    a.get("allergen") if isinstance(a, dict) else a
                    for a in emr_data["allergies"]
                ]

            return normalized

        # Fallback: return as-is
        return emr_data

    def extract_vital_signs_regex(self, text: str) -> Optional[Vitals]:
        """Extract vital signs using regex patterns (backup method).

        Args:
            text: Text containing vital signs

        Returns:
            Vitals object or None
        """
        vitals_data = {}

        # Blood pressure: "BP 120/80" or "120/80 mmHg"
        bp_pattern = r"BP\s*:?\s*(\d{2,3})\s*/\s*(\d{2,3})|(\d{2,3})\s*/\s*(\d{2,3})\s*mmHg"
        bp_match = re.search(bp_pattern, text, re.IGNORECASE)
        if bp_match:
            sys = bp_match.group(1) or bp_match.group(3)
            dia = bp_match.group(2) or bp_match.group(4)
            vitals_data["bp_systolic"] = int(sys)
            vitals_data["bp_diastolic"] = int(dia)

        # Heart rate: "HR 72" or "Pulse 72"
        hr_pattern = r"(?:HR|Heart Rate|Pulse)\s*:?\s*(\d{2,3})"
        hr_match = re.search(hr_pattern, text, re.IGNORECASE)
        if hr_match:
            vitals_data["heart_rate"] = int(hr_match.group(1))

        # Respiratory rate: "RR 16"
        rr_pattern = r"(?:RR|Respiratory Rate)\s*:?\s*(\d{1,2})"
        rr_match = re.search(rr_pattern, text, re.IGNORECASE)
        if rr_match:
            vitals_data["respiratory_rate"] = int(rr_match.group(1))

        # Temperature: "Temp 98.6" or "98.6°F"
        temp_pattern = r"(?:Temp|Temperature)\s*:?\s*(\d{2,3}(?:\.\d)?)\s*°?[FC]?"
        temp_match = re.search(temp_pattern, text, re.IGNORECASE)
        if temp_match:
            vitals_data["temperature"] = float(temp_match.group(1))

        # SpO2: "SpO2 98%" or "O2 sat 98%"
        spo2_pattern = r"(?:SpO2|O2 Sat|Oxygen)\s*:?\s*(\d{2,3})\s*%?"
        spo2_match = re.search(spo2_pattern, text, re.IGNORECASE)
        if spo2_match:
            vitals_data["spo2"] = int(spo2_match.group(1))

        if not vitals_data:
            return None

        return Vitals(**vitals_data)


async def extract_medical_entities(text: str) -> dict[str, Any]:
    """Convenience function to extract medical entities.

    Args:
        text: Clinical text

    Returns:
        Dictionary with extracted entities
    """
    extractor = MedicalInformationExtractor()
    return await extractor.extract_from_text(text)
