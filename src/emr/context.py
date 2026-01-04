"""Patient Context Builder for RAG query enhancement."""

from datetime import datetime, timedelta
from typing import Optional

from .client import EMRClient
from .models import LabResult, Medication, PatientSummary


class PatientContextBuilder:
    """
    Build comprehensive patient context for RAG queries.

    Features:
    - Filter relevant medications based on query
    - Highlight critical allergies
    - Include pertinent lab values
    - Calculate derived values (eGFR, BMI)
    - Format for optimal LLM comprehension
    """

    def __init__(self, emr_client: EMRClient):
        """
        Initialize context builder.

        Args:
            emr_client: EMR client for data retrieval
        """
        self.emr = emr_client

    async def build_context(
        self,
        patient_id: int,
        query: Optional[str] = None,
        include_full_history: bool = False,
    ) -> Optional[str]:
        """
        Build patient context string for RAG.

        Args:
            patient_id: Patient ID
            query: User's query (for filtering relevance)
            include_full_history: Include all history vs. query-relevant only

        Returns:
            Formatted patient context string or None if patient not found
        """
        summary = await self.emr.get_patient_summary(patient_id)
        if not summary:
            return None

        if include_full_history or not query:
            return summary.to_context_string()

        # Build query-relevant context
        return self._build_query_relevant_context(summary, query)

    def _build_query_relevant_context(
        self, summary: PatientSummary, query: str
    ) -> str:
        """
        Build context filtered for query relevance.

        Args:
            summary: Patient summary
            query: User's query

        Returns:
            Filtered context string
        """
        query_lower = query.lower()
        lines = [
            "=== PATIENT CONTEXT ===",
            f"{summary.patient.name}, {summary.patient.age}y {summary.patient.gender.value}",
            f"MRN: {summary.patient.mrn}",
            "",
        ]

        # ALWAYS include allergies (critical safety)
        if summary.allergies:
            lines.append("⚠️ ALLERGIES:")
            for allergy in summary.allergies:
                lines.append(f"  {allergy.to_display_string()}")
            lines.append("")

        # Filter diagnoses by relevance
        relevant_diagnoses = self._filter_diagnoses_by_query(
            summary.active_diagnoses, query_lower
        )
        if relevant_diagnoses:
            lines.append("Relevant Diagnoses:")
            for dx in relevant_diagnoses:
                lines.append(f"  • {dx.diagnosis_name}")
            lines.append("")

        # Filter medications by relevance
        relevant_meds = self._filter_medications_by_query(
            summary.current_medications, query_lower
        )
        if relevant_meds:
            lines.append("Relevant Medications:")
            for med in relevant_meds:
                lines.append(f"  • {med.to_display_string()}")
            lines.append("")

        # Include vitals if query mentions them
        if self._is_vitals_relevant(query_lower) and summary.recent_vitals:
            lines.append("Recent Vitals:")
            v = summary.recent_vitals
            if v.weight_kg:
                lines.append(f"  • Weight: {v.weight_kg}kg")
            if v.bmi:
                lines.append(f"  • BMI: {v.bmi}")
            if v.blood_pressure:
                lines.append(f"  • BP: {v.blood_pressure} mmHg")
            lines.append("")

        # Filter labs by relevance
        relevant_labs = self._filter_labs_by_query(
            summary.recent_labs, query_lower
        )
        if relevant_labs:
            lines.append("Relevant Labs:")
            for lab in relevant_labs[:5]:
                lines.append(f"  • {lab.to_display_string()}")
            lines.append("")

        # Add derived values if relevant
        derived = self._calculate_derived_values(summary, query_lower)
        if derived:
            lines.append("Calculated Values:")
            for key, value in derived.items():
                lines.append(f"  • {key}: {value}")
            lines.append("")

        # Add clinical alerts
        alerts = self._generate_alerts(summary, query_lower)
        if alerts:
            lines.append("⚠️ ALERTS:")
            for alert in alerts:
                lines.append(f"  • {alert}")
            lines.append("")

        return "\n".join(lines)

    def _filter_diagnoses_by_query(
        self, diagnoses: list, query: str
    ) -> list:
        """Filter diagnoses relevant to query."""
        # Keywords that suggest diagnosis is relevant
        keywords = {
            "diabetes": ["diabetes", "dm", "sugar", "glucose", "metformin"],
            "hypertension": ["bp", "blood pressure", "hypertension", "htn"],
            "kidney": ["kidney", "renal", "creatinine", "egfr", "ckd"],
            "heart": ["heart", "cardiac", "cardio", "chest pain"],
            "lung": ["lung", "respiratory", "copd", "asthma", "breathing"],
        }

        relevant = []
        for dx in diagnoses:
            dx_name_lower = dx.diagnosis_name.lower()
            # Include if chronic/important
            if dx.is_chronic:
                relevant.append(dx)
                continue
            # Include if matches query keywords
            for category, kws in keywords.items():
                if any(kw in query for kw in kws):
                    if any(kw in dx_name_lower for kw in kws):
                        relevant.append(dx)
                        break

        return relevant if relevant else diagnoses[:3]  # Top 3 if no matches

    def _filter_medications_by_query(
        self, medications: list[Medication], query: str
    ) -> list[Medication]:
        """Filter medications relevant to query."""
        # Drug class keywords
        drug_classes = {
            "diabetes": ["metformin", "glipizide", "insulin", "sglt2", "dpp4"],
            "hypertension": [
                "lisinopril",
                "amlodipine",
                "losartan",
                "ace",
                "arb",
                "beta blocker",
            ],
            "cholesterol": ["statin", "atorvastatin", "rosuvastatin"],
            "anticoagulation": ["aspirin", "warfarin", "apixaban", "rivaroxaban"],
            "pain": ["nsaid", "ibuprofen", "naproxen", "acetaminophen"],
        }

        relevant = []
        for med in medications:
            drug_lower = med.drug_name.lower()
            # Include if drug name mentioned in query
            if drug_lower in query:
                relevant.append(med)
                continue
            # Include if drug class relevant
            for category, drugs in drug_classes.items():
                if category in query:
                    if any(drug in drug_lower for drug in drugs):
                        relevant.append(med)
                        break

        return relevant if relevant else medications  # All if no specific matches

    def _filter_labs_by_query(
        self, labs: list[LabResult], query: str
    ) -> list[LabResult]:
        """Filter labs relevant to query."""
        lab_keywords = {
            "kidney": ["creatinine", "bun", "egfr", "urea"],
            "diabetes": ["glucose", "hba1c", "a1c", "sugar"],
            "liver": ["alt", "ast", "bilirubin", "alkaline phosphatase"],
            "electrolyte": ["sodium", "potassium", "chloride", "calcium"],
            "anemia": ["hemoglobin", "hematocrit", "rbc", "iron"],
            "infection": ["wbc", "white blood", "crp", "esr"],
        }

        relevant = []
        for lab in labs:
            test_lower = lab.test_name.lower()
            # Include if test name in query
            if any(word in test_lower for word in query.split()):
                relevant.append(lab)
                continue
            # Include if abnormal (always relevant)
            if lab.is_abnormal:
                relevant.append(lab)
                continue
            # Include if category matches
            for category, tests in lab_keywords.items():
                if category in query:
                    if any(test in test_lower for test in tests):
                        relevant.append(lab)
                        break

        return relevant if relevant else labs[:5]  # Top 5 most recent if no matches

    def _is_vitals_relevant(self, query: str) -> bool:
        """Check if vitals are relevant to query."""
        vital_keywords = [
            "weight",
            "bmi",
            "bp",
            "blood pressure",
            "heart rate",
            "pulse",
            "temperature",
            "fever",
            "spo2",
            "oxygen",
            "vital",
        ]
        return any(kw in query for kw in vital_keywords)

    def _calculate_derived_values(
        self, summary: PatientSummary, query: str
    ) -> dict[str, str]:
        """
        Calculate derived clinical values.

        Args:
            summary: Patient summary
            query: User query

        Returns:
            Dict of calculated values
        """
        derived = {}

        # Calculate eGFR if creatinine available
        creatinine_lab = None
        for lab in summary.recent_labs:
            if "creatinine" in lab.test_name.lower():
                creatinine_lab = lab
                break

        if creatinine_lab and ("kidney" in query or "renal" in query or "egfr" in query):
            try:
                creat = float(creatinine_lab.result)
                egfr = self._calculate_egfr(
                    creat,
                    summary.patient.age,
                    summary.patient.gender.value,
                )
                stage = self._ckd_stage(egfr)
                derived["eGFR"] = f"{egfr} mL/min/1.73m² (CKD Stage {stage})"
            except (ValueError, TypeError):
                pass

        # Include BMI if weight-related query
        if summary.recent_vitals and summary.recent_vitals.bmi:
            if any(kw in query for kw in ["weight", "bmi", "obese", "overweight"]):
                bmi = summary.recent_vitals.bmi
                category = self._bmi_category(bmi)
                derived["BMI"] = f"{bmi} ({category})"

        return derived

    def _calculate_egfr(
        self, creatinine: float, age: int, gender: str
    ) -> int:
        """
        Calculate eGFR using CKD-EPI equation (simplified).

        Args:
            creatinine: Serum creatinine (mg/dL)
            age: Patient age
            gender: M or F

        Returns:
            eGFR in mL/min/1.73m²
        """
        # Simplified CKD-EPI calculation
        k = 0.7 if gender == "F" else 0.9
        alpha = -0.329 if gender == "F" else -0.411
        sex_factor = 1.018 if gender == "F" else 1.0

        egfr = (
            141
            * min(creatinine / k, 1) ** alpha
            * max(creatinine / k, 1) ** -1.209
            * 0.993**age
            * sex_factor
        )

        return round(egfr)

    def _ckd_stage(self, egfr: int) -> str:
        """Determine CKD stage from eGFR."""
        if egfr >= 90:
            return "1 (Normal)"
        elif egfr >= 60:
            return "2 (Mild)"
        elif egfr >= 45:
            return "3a (Moderate)"
        elif egfr >= 30:
            return "3b (Moderate)"
        elif egfr >= 15:
            return "4 (Severe)"
        else:
            return "5 (Kidney Failure)"

    def _bmi_category(self, bmi: float) -> str:
        """Categorize BMI."""
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def _generate_alerts(
        self, summary: PatientSummary, query: str
    ) -> list[str]:
        """
        Generate clinical alerts based on patient data.

        Args:
            summary: Patient summary
            query: User query

        Returns:
            List of alert strings
        """
        alerts = []

        # Check for renal dosing requirements
        for lab in summary.recent_labs:
            if "creatinine" in lab.test_name.lower():
                try:
                    creat = float(lab.result)
                    if creat > 1.5:
                        alerts.append(
                            "Impaired renal function - consider dose adjustments"
                        )
                except ValueError:
                    pass

        # Check for hyperkalemia with ACE/ARB
        potassium_high = False
        for lab in summary.recent_labs:
            if "potassium" in lab.test_name.lower():
                try:
                    k = float(lab.result)
                    if k > 5.0:
                        potassium_high = True
                except ValueError:
                    pass

        if potassium_high:
            for med in summary.current_medications:
                drug_lower = med.drug_name.lower()
                if any(
                    ace in drug_lower
                    for ace in ["lisinopril", "enalapril", "ramipril", "losartan"]
                ):
                    alerts.append(
                        "Elevated potassium with ACE/ARB - monitor closely"
                    )
                    break

        # Check for NSAIDs in CKD
        has_ckd = any(
            "kidney" in dx.diagnosis_name.lower() or "ckd" in dx.diagnosis_name.lower()
            for dx in summary.active_diagnoses
        )
        if has_ckd and any(
            kw in query for kw in ["pain", "nsaid", "ibuprofen", "naproxen"]
        ):
            alerts.append("CKD present - AVOID NSAIDs (use acetaminophen instead)")

        # Check for elderly with polypharmacy
        if summary.patient.age >= 65 and len(summary.current_medications) >= 5:
            alerts.append(
                "Elderly with polypharmacy - review for interactions and deprescribing"
            )

        return alerts

    async def build_context_for_prescription(
        self, patient_id: int, drug_name: str
    ) -> str:
        """
        Build specialized context for prescription decision.

        Args:
            patient_id: Patient ID
            drug_name: Drug being considered

        Returns:
            Context focused on prescription safety
        """
        summary = await self.emr.get_patient_summary(patient_id)
        if not summary:
            return ""

        lines = [
            f"=== PRESCRIPTION CONTEXT FOR {drug_name.upper()} ===",
            f"Patient: {summary.patient.name}, {summary.patient.age}y {summary.patient.gender.value}",
            "",
        ]

        # CRITICAL: Allergies
        if summary.allergies:
            lines.append("🚨 ALLERGIES:")
            for allergy in summary.allergies:
                lines.append(f"  {allergy.to_display_string()}")
            lines.append("")

        # Current medications (check interactions)
        if summary.current_medications:
            lines.append("Current Medications:")
            for med in summary.current_medications:
                lines.append(f"  • {med.to_display_string()}")
            lines.append("")

        # Relevant diagnoses for contraindications
        if summary.active_diagnoses:
            lines.append("Active Diagnoses:")
            for dx in summary.active_diagnoses:
                lines.append(f"  • {dx.diagnosis_name}")
            lines.append("")

        # Renal function (for dosing)
        for lab in summary.recent_labs:
            if "creatinine" in lab.test_name.lower():
                lines.append("Renal Function:")
                lines.append(f"  • {lab.to_display_string()}")
                try:
                    creat = float(lab.result)
                    egfr = self._calculate_egfr(
                        creat,
                        summary.patient.age,
                        summary.patient.gender.value,
                    )
                    lines.append(f"  • eGFR: {egfr} mL/min/1.73m² (CKD Stage {self._ckd_stage(egfr)})")
                except ValueError:
                    pass
                lines.append("")
                break

        return "\n".join(lines)
