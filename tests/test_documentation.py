"""
Tests for clinical documentation AI module.
Tests SOAP notes, discharge summaries, referral letters, and more.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date


class TestSOAPNoteGeneration:
    """Tests for SOAP note generation."""

    @pytest.fixture
    def soap_service(self):
        """Create SOAP note service instance."""
        from src.documentation.soap import SOAPNoteService
        return SOAPNoteService()

    @pytest.fixture
    def encounter_data(self):
        """Sample encounter data."""
        return {
            "patient": {
                "name": "Rahul Sharma",
                "age": 45,
                "sex": "male",
            },
            "chief_complaint": "Chest pain for 2 days",
            "history": {
                "present_illness": "Onset 2 days ago, sharp, worse with exertion, better at rest",
                "past_medical": ["Hypertension", "Type 2 Diabetes"],
                "medications": ["Metformin 500mg BID", "Lisinopril 10mg daily"],
                "allergies": ["Penicillin"],
                "social": "Non-smoker, occasional alcohol",
            },
            "vitals": {
                "bp": "160/100",
                "hr": 88,
                "rr": 18,
                "temp": 37.0,
                "spo2": 98,
            },
            "physical_exam": {
                "general": "Alert, oriented, in mild distress",
                "cardiovascular": "Regular rhythm, no murmurs, no JVD",
                "respiratory": "Clear to auscultation bilaterally",
            },
            "assessment": "Unstable angina, rule out ACS",
            "plan": [
                "ECG stat",
                "Troponin x3",
                "Aspirin 325mg",
                "Cardiology consult",
            ],
        }

    @pytest.mark.asyncio
    async def test_soap_note_generated(self, soap_service, encounter_data):
        """Should generate complete SOAP note."""
        result = await soap_service.generate(encounter_data)

        assert "subjective" in result or "S" in result
        assert "objective" in result or "O" in result
        assert "assessment" in result or "A" in result
        assert "plan" in result or "P" in result

    @pytest.mark.asyncio
    async def test_subjective_includes_hpi(self, soap_service, encounter_data):
        """Subjective should include history of present illness."""
        result = await soap_service.generate(encounter_data)

        subjective = result.get("subjective", result.get("S", "")).lower()
        assert "chest pain" in subjective
        assert "2 days" in subjective

    @pytest.mark.asyncio
    async def test_objective_includes_vitals(self, soap_service, encounter_data):
        """Objective should include vital signs."""
        result = await soap_service.generate(encounter_data)

        objective = result.get("objective", result.get("O", "")).lower()
        assert "160/100" in objective or "bp" in objective
        assert "88" in objective or "heart rate" in objective

    @pytest.mark.asyncio
    async def test_plan_structured(self, soap_service, encounter_data):
        """Plan should be structured with action items."""
        result = await soap_service.generate(encounter_data)

        plan = result.get("plan", result.get("P", []))
        if isinstance(plan, list):
            assert len(plan) >= 3
        else:
            assert "ecg" in plan.lower()
            assert "troponin" in plan.lower()

    @pytest.mark.asyncio
    async def test_icd_codes_suggested(self, soap_service, encounter_data):
        """Should suggest ICD-10 codes."""
        result = await soap_service.generate(encounter_data)

        assert "icd_codes" in result or "diagnoses" in result
        codes = result.get("icd_codes", result.get("diagnoses", []))
        # Should suggest angina-related code
        assert any("I20" in str(c) for c in codes)


class TestDischargeSummary:
    """Tests for discharge summary generation."""

    @pytest.fixture
    def discharge_service(self):
        """Create discharge summary service instance."""
        from src.documentation.discharge import DischargeSummaryService
        return DischargeSummaryService()

    @pytest.fixture
    def admission_data(self):
        """Sample admission data."""
        return {
            "patient": {
                "name": "Priya Singh",
                "age": 62,
                "mrn": "MRN-2024-002",
            },
            "admission_date": date(2025, 1, 1),
            "discharge_date": date(2025, 1, 5),
            "admitting_diagnosis": "Acute STEMI",
            "procedures": [
                {
                    "name": "Primary PCI",
                    "date": date(2025, 1, 1),
                    "findings": "LAD 90% stenosis, stent placed",
                }
            ],
            "hospital_course": "Presented with chest pain, ECG showed STEMI, emergent PCI performed.",
            "discharge_diagnosis": ["STEMI - LAD", "Hypertension", "Type 2 Diabetes"],
            "discharge_medications": [
                {"drug": "Aspirin", "dose": "75mg", "frequency": "daily"},
                {"drug": "Clopidogrel", "dose": "75mg", "frequency": "daily"},
                {"drug": "Atorvastatin", "dose": "80mg", "frequency": "daily"},
            ],
            "follow_up": [
                {"specialty": "Cardiology", "timing": "1 week"},
                {"specialty": "Primary Care", "timing": "2 weeks"},
            ],
        }

    @pytest.mark.asyncio
    async def test_discharge_summary_complete(self, discharge_service, admission_data):
        """Should generate complete discharge summary."""
        result = await discharge_service.generate(admission_data)

        required_sections = [
            "patient_info",
            "admission_date",
            "discharge_date",
            "diagnosis",
            "procedures",
            "hospital_course",
            "discharge_medications",
            "follow_up",
        ]

        for section in required_sections:
            assert section in result or any(
                section.replace("_", " ") in str(result).lower()
                for _ in [1]
            )

    @pytest.mark.asyncio
    async def test_medication_reconciliation(self, discharge_service, admission_data):
        """Should include medication reconciliation."""
        result = await discharge_service.generate(admission_data)

        meds = result.get("discharge_medications", [])
        assert len(meds) >= 3
        # Should include DAPT after stent
        drug_names = [m["drug"].lower() for m in meds]
        assert "aspirin" in drug_names
        assert "clopidogrel" in drug_names

    @pytest.mark.asyncio
    async def test_patient_instructions_included(self, discharge_service, admission_data):
        """Should include patient instructions."""
        result = await discharge_service.generate(admission_data)

        assert "instructions" in result or "patient_education" in result
        instructions = result.get("instructions", result.get("patient_education", ""))
        # Post-stent instructions
        assert "aspirin" in str(instructions).lower() or \
               "medication" in str(instructions).lower()

    @pytest.mark.asyncio
    async def test_warning_signs_included(self, discharge_service, admission_data):
        """Should include warning signs to watch for."""
        result = await discharge_service.generate(admission_data)

        assert "warning_signs" in result or "red_flags" in result or \
               "when_to_seek_care" in result


class TestReferralLetter:
    """Tests for referral letter generation."""

    @pytest.fixture
    def referral_service(self):
        """Create referral letter service instance."""
        from src.documentation.referral import ReferralLetterService
        return ReferralLetterService()

    @pytest.fixture
    def referral_data(self):
        """Sample referral data."""
        return {
            "patient": {
                "name": "Amit Patel",
                "age": 55,
                "mrn": "MRN-2024-003",
            },
            "referring_doctor": {
                "name": "Dr. Sharma",
                "specialty": "General Medicine",
            },
            "referred_to": {
                "name": "Dr. Gupta",
                "specialty": "Cardiology",
            },
            "reason": "Evaluation of chest pain with abnormal stress test",
            "clinical_summary": "55M with HTN, DM, presenting with exertional chest pain. Stress test showed 2mm ST depression in leads V4-V6.",
            "investigations": [
                {"name": "ECG", "result": "Normal sinus rhythm"},
                {"name": "Stress Test", "result": "Positive for ischemia"},
            ],
            "urgency": "urgent",
        }

    @pytest.mark.asyncio
    async def test_referral_letter_generated(self, referral_service, referral_data):
        """Should generate complete referral letter."""
        result = await referral_service.generate(referral_data)

        assert "letter" in result or "content" in result
        letter = result.get("letter", result.get("content", ""))
        assert len(letter) > 100

    @pytest.mark.asyncio
    async def test_referral_includes_clinical_context(
        self, referral_service, referral_data
    ):
        """Should include relevant clinical context."""
        result = await referral_service.generate(referral_data)

        letter = result.get("letter", result.get("content", "")).lower()
        assert "chest pain" in letter
        assert "stress test" in letter
        assert "ischemia" in letter

    @pytest.mark.asyncio
    async def test_referral_includes_investigations(
        self, referral_service, referral_data
    ):
        """Should summarize relevant investigations."""
        result = await referral_service.generate(referral_data)

        letter = result.get("letter", result.get("content", "")).lower()
        assert "ecg" in letter or "electrocardiogram" in letter
        assert "stress" in letter

    @pytest.mark.asyncio
    async def test_urgent_referral_flagged(self, referral_service, referral_data):
        """Urgent referrals should be clearly marked."""
        result = await referral_service.generate(referral_data)

        letter = result.get("letter", result.get("content", "")).lower()
        assert "urgent" in letter or result.get("urgency") == "urgent"


class TestOperativeNote:
    """Tests for operative note generation."""

    @pytest.fixture
    def operative_service(self):
        """Create operative note service instance."""
        from src.documentation.operative import OperativeNoteService
        return OperativeNoteService()

    @pytest.fixture
    def surgery_data(self):
        """Sample surgery data."""
        return {
            "patient": {"name": "Test Patient", "mrn": "MRN-001"},
            "date": date(2025, 1, 1),
            "procedure": "Laparoscopic Cholecystectomy",
            "surgeon": "Dr. Kumar",
            "assistant": "Dr. Singh",
            "anesthesia": "General",
            "indication": "Symptomatic cholelithiasis",
            "findings": "Inflamed gallbladder with multiple stones",
            "technique": "Standard 4-port laparoscopic technique...",
            "specimens": "Gallbladder with stones",
            "estimated_blood_loss": "50ml",
            "complications": "None",
        }

    @pytest.mark.asyncio
    async def test_operative_note_complete(self, operative_service, surgery_data):
        """Should generate complete operative note."""
        result = await operative_service.generate(surgery_data)

        required = ["procedure", "indication", "findings", "technique"]
        for field in required:
            assert field in result or field in str(result).lower()

    @pytest.mark.asyncio
    async def test_operative_note_timing(self, operative_service, surgery_data):
        """Should include timing information."""
        result = await operative_service.generate(surgery_data)

        assert "date" in result
        # May also include duration
        assert "duration" in result or "time" in str(result).lower()


class TestMedicalCertificate:
    """Tests for medical certificate generation."""

    @pytest.fixture
    def certificate_service(self):
        """Create certificate service instance."""
        from src.documentation.certificate import MedicalCertificateService
        return MedicalCertificateService()

    @pytest.mark.asyncio
    async def test_fitness_certificate(self, certificate_service):
        """Should generate fitness certificate."""
        result = await certificate_service.generate(
            certificate_type="fitness",
            patient={"name": "Test Patient", "age": 30},
            purpose="employment",
            findings="Patient is fit for regular employment duties",
        )

        assert "certificate" in result
        cert = result["certificate"]
        assert "fit" in cert.lower()
        assert "employment" in cert.lower()

    @pytest.mark.asyncio
    async def test_sick_leave_certificate(self, certificate_service):
        """Should generate sick leave certificate."""
        result = await certificate_service.generate(
            certificate_type="sick_leave",
            patient={"name": "Test Patient", "age": 40},
            diagnosis="Acute viral fever",
            leave_period={"from": date(2025, 1, 1), "to": date(2025, 1, 3)},
        )

        assert "certificate" in result
        cert = result["certificate"]
        assert "rest" in cert.lower() or "leave" in cert.lower()

    @pytest.mark.asyncio
    async def test_certificate_includes_doctor_details(self, certificate_service):
        """Certificate should include issuing doctor details."""
        result = await certificate_service.generate(
            certificate_type="fitness",
            patient={"name": "Test Patient"},
            doctor={
                "name": "Dr. Test",
                "registration": "MCI-12345",
                "qualification": "MBBS, MD",
            },
        )

        cert = result["certificate"]
        assert "Dr. Test" in cert or "MCI-12345" in cert


class TestClinicalSummary:
    """Tests for clinical summary generation."""

    @pytest.fixture
    def summary_service(self):
        """Create clinical summary service instance."""
        from src.documentation.summary import ClinicalSummaryService
        return ClinicalSummaryService()

    @pytest.mark.asyncio
    async def test_patient_summary_generated(self, summary_service):
        """Should generate patient clinical summary."""
        patient_data = {
            "demographics": {"name": "Test", "age": 50, "sex": "male"},
            "conditions": ["Hypertension", "Diabetes"],
            "medications": ["Metformin", "Lisinopril"],
            "recent_visits": [
                {"date": date(2025, 1, 1), "reason": "Follow-up"},
            ],
            "labs": {"hba1c": 7.2, "creatinine": 1.1},
        }

        result = await summary_service.generate(patient_data)

        assert "summary" in result
        summary = result["summary"]
        assert "hypertension" in summary.lower()
        assert "diabetes" in summary.lower()

    @pytest.mark.asyncio
    async def test_summary_includes_key_values(self, summary_service):
        """Summary should highlight key clinical values."""
        patient_data = {
            "demographics": {"name": "Test", "age": 60},
            "conditions": ["CKD Stage 3"],
            "labs": {"egfr": 45, "creatinine": 1.8},
        }

        result = await summary_service.generate(patient_data)

        summary = result["summary"]
        assert "egfr" in summary.lower() or "45" in summary
        assert "ckd" in summary.lower() or "kidney" in summary.lower()


class TestDocumentTemplates:
    """Tests for document template system."""

    @pytest.fixture
    def template_service(self):
        """Create template service instance."""
        from src.documentation.templates import TemplateService
        return TemplateService()

    @pytest.mark.asyncio
    async def test_list_templates(self, template_service):
        """Should list available templates."""
        templates = await template_service.list_templates()

        assert len(templates) > 0
        template_types = [t["type"] for t in templates]
        assert "soap" in template_types or "SOAP" in template_types

    @pytest.mark.asyncio
    async def test_custom_template_creation(self, template_service):
        """Should allow custom template creation."""
        template = {
            "name": "My Custom SOAP",
            "type": "soap",
            "sections": ["S", "O", "A", "P"],
            "formatting": {"header": "bold"},
        }

        result = await template_service.create(template)

        assert result["success"]
        assert "template_id" in result

    @pytest.mark.asyncio
    async def test_template_rendering(self, template_service):
        """Should render template with data."""
        data = {
            "patient_name": "Test Patient",
            "date": date.today().isoformat(),
            "chief_complaint": "Headache",
        }

        result = await template_service.render(
            template_id="default_soap",
            data=data,
        )

        assert "rendered" in result
        rendered = result["rendered"]
        assert "Test Patient" in rendered
        assert "Headache" in rendered
