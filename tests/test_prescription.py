"""
Tests for prescription integration module.
Tests prescription extraction, drug validation, e-prescribing, and alerts.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date


class TestPrescriptionExtraction:
    """Tests for extracting prescription from query responses."""

    @pytest.fixture
    def extraction_service(self):
        """Create extraction service instance."""
        from src.prescription.extraction import PrescriptionExtractionService
        return PrescriptionExtractionService()

    @pytest.mark.asyncio
    async def test_extract_single_drug(self, extraction_service):
        """Should extract single drug prescription."""
        query_response = """
        For this patient with type 2 diabetes, I recommend starting:
        - Metformin 500mg twice daily with meals
        """

        result = await extraction_service.extract(query_response)

        assert len(result["medications"]) >= 1
        med = result["medications"][0]
        assert "metformin" in med["drug"].lower()
        assert med["dose"] == "500mg" or "500" in str(med["dose"])
        assert "twice" in med["frequency"].lower() or "bid" in med["frequency"].lower()

    @pytest.mark.asyncio
    async def test_extract_multiple_drugs(self, extraction_service):
        """Should extract multiple medications."""
        query_response = """
        Treatment regimen:
        1. Amlodipine 5mg once daily
        2. Metoprolol 50mg twice daily
        3. Aspirin 75mg once daily
        """

        result = await extraction_service.extract(query_response)

        assert len(result["medications"]) >= 3
        drug_names = [m["drug"].lower() for m in result["medications"]]
        assert any("amlodipine" in d for d in drug_names)
        assert any("metoprolol" in d for d in drug_names)
        assert any("aspirin" in d for d in drug_names)

    @pytest.mark.asyncio
    async def test_extract_with_duration(self, extraction_service):
        """Should extract treatment duration."""
        query_response = """
        Prescribe:
        - Amoxicillin 500mg TDS for 7 days
        - Ibuprofen 400mg as needed for 5 days
        """

        result = await extraction_service.extract(query_response)

        for med in result["medications"]:
            assert "duration" in med or "days" in str(med)

    @pytest.mark.asyncio
    async def test_extract_with_instructions(self, extraction_service):
        """Should extract special instructions."""
        query_response = """
        Start Pantoprazole 40mg before breakfast, avoid alcohol and NSAIDs.
        Take on empty stomach, at least 30 minutes before food.
        """

        result = await extraction_service.extract(query_response)

        med = result["medications"][0]
        assert "instructions" in med or "notes" in med
        instructions = med.get("instructions", med.get("notes", "")).lower()
        assert "empty stomach" in instructions or "before" in instructions


class TestDrugValidation:
    """Tests for drug validation against patient data."""

    @pytest.fixture
    def validation_service(self):
        """Create validation service instance."""
        from src.prescription.validation import DrugValidationService
        return DrugValidationService()

    @pytest.fixture
    def patient_with_allergy(self):
        """Patient with known allergy."""
        return {
            "id": "pat_123",
            "allergies": [
                {"drug": "Penicillin", "reaction": "anaphylaxis", "severity": "severe"}
            ],
            "medications": [],
            "conditions": [],
            "labs": {"creatinine": 1.0, "egfr": 90},
        }

    @pytest.fixture
    def patient_with_renal_impairment(self):
        """Patient with renal impairment."""
        return {
            "id": "pat_456",
            "allergies": [],
            "medications": [],
            "conditions": [{"name": "CKD Stage 4", "icd10": "N18.4"}],
            "labs": {"creatinine": 3.5, "egfr": 20},
        }

    @pytest.mark.asyncio
    async def test_allergy_cross_reactivity_detected(
        self, validation_service, patient_with_allergy
    ):
        """Should detect cross-reactive allergy."""
        prescription = {
            "medications": [
                {"drug": "Amoxicillin", "dose": "500mg", "frequency": "TDS"}
            ]
        }

        result = await validation_service.validate(prescription, patient_with_allergy)

        assert len(result["warnings"]) > 0
        assert any(
            w["type"] == "allergy" or "allergy" in w.get("message", "").lower()
            for w in result["warnings"]
        )
        assert any(w["severity"] in ["high", "severe", "critical"] for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_renal_dosing_alert(
        self, validation_service, patient_with_renal_impairment
    ):
        """Should alert for renal dose adjustment."""
        prescription = {
            "medications": [
                {"drug": "Metformin", "dose": "1000mg", "frequency": "BID"}
            ]
        }

        result = await validation_service.validate(prescription, patient_with_renal_impairment)

        assert len(result["warnings"]) > 0
        assert any(
            "renal" in w.get("message", "").lower() or
            "contraindicated" in w.get("message", "").lower()
            for w in result["warnings"]
        )

    @pytest.mark.asyncio
    async def test_drug_interaction_detected(self, validation_service):
        """Should detect drug-drug interactions."""
        patient = {
            "id": "pat_789",
            "allergies": [],
            "medications": [
                {"drug": "Warfarin", "dose": "5mg", "frequency": "daily"}
            ],
            "conditions": [],
            "labs": {},
        }

        prescription = {
            "medications": [
                {"drug": "Aspirin", "dose": "325mg", "frequency": "daily"}
            ]
        }

        result = await validation_service.validate(prescription, patient)

        assert len(result["warnings"]) > 0
        assert any(
            w["type"] == "interaction" or "interaction" in w.get("message", "").lower()
            for w in result["warnings"]
        )

    @pytest.mark.asyncio
    async def test_valid_prescription_passes(self, validation_service):
        """Valid prescription should pass validation."""
        patient = {
            "id": "pat_999",
            "allergies": [],
            "medications": [],
            "conditions": [{"name": "Hypertension", "icd10": "I10"}],
            "labs": {"creatinine": 1.0, "egfr": 90},
        }

        prescription = {
            "medications": [
                {"drug": "Amlodipine", "dose": "5mg", "frequency": "daily"}
            ]
        }

        result = await validation_service.validate(prescription, patient)

        # Should have no critical warnings
        critical = [w for w in result["warnings"] if w["severity"] == "critical"]
        assert len(critical) == 0


class TestPrescriptionGeneration:
    """Tests for prescription document generation."""

    @pytest.fixture
    def generation_service(self):
        """Create generation service instance."""
        from src.prescription.generation import PrescriptionGenerationService
        return PrescriptionGenerationService()

    @pytest.fixture
    def sample_prescription_data(self):
        """Sample prescription data."""
        return {
            "patient": {
                "name": "Rahul Sharma",
                "age": 45,
                "mrn": "MRN-2024-001",
            },
            "doctor": {
                "name": "Dr. Priya Singh",
                "license": "MCI-12345",
                "specialty": "Cardiology",
            },
            "medications": [
                {
                    "drug": "Amlodipine",
                    "dose": "5mg",
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "quantity": 30,
                },
                {
                    "drug": "Metoprolol",
                    "dose": "50mg",
                    "frequency": "Twice daily",
                    "duration": "30 days",
                    "quantity": 60,
                },
            ],
            "diagnosis": "Essential Hypertension (I10)",
        }

    @pytest.mark.asyncio
    async def test_generate_prescription_pdf(
        self, generation_service, sample_prescription_data
    ):
        """Should generate prescription PDF."""
        result = await generation_service.generate(
            data=sample_prescription_data,
            format="pdf",
        )

        assert result["success"]
        assert "pdf_url" in result or "pdf_data" in result

    @pytest.mark.asyncio
    async def test_prescription_includes_required_fields(
        self, generation_service, sample_prescription_data
    ):
        """Prescription should have all legally required fields."""
        result = await generation_service.generate(
            data=sample_prescription_data,
            format="json",
        )

        rx = result["prescription"]
        # Required fields
        assert "patient_name" in rx or "patient" in rx
        assert "doctor_name" in rx or "prescriber" in rx
        assert "license_number" in rx or "registration" in rx
        assert "date" in rx
        assert "medications" in rx or "drugs" in rx
        assert "signature" in rx or "signed" in rx

    @pytest.mark.asyncio
    async def test_prescription_id_generated(
        self, generation_service, sample_prescription_data
    ):
        """Should generate unique prescription ID."""
        result1 = await generation_service.generate(
            data=sample_prescription_data,
            format="json",
        )
        result2 = await generation_service.generate(
            data=sample_prescription_data,
            format="json",
        )

        assert result1["prescription"]["id"] != result2["prescription"]["id"]


class TestGenericSubstitution:
    """Tests for generic drug substitution suggestions."""

    @pytest.fixture
    def substitution_service(self):
        """Create substitution service instance."""
        from src.prescription.substitution import GenericSubstitutionService
        return GenericSubstitutionService()

    @pytest.mark.asyncio
    async def test_suggest_generic_alternatives(self, substitution_service):
        """Should suggest generic alternatives."""
        result = await substitution_service.find_alternatives(
            brand_name="Glucophage",
            dose="500mg",
        )

        assert len(result["alternatives"]) > 0
        assert any(
            "metformin" in alt["generic_name"].lower()
            for alt in result["alternatives"]
        )

    @pytest.mark.asyncio
    async def test_alternatives_include_pricing(self, substitution_service):
        """Alternatives should include pricing info."""
        result = await substitution_service.find_alternatives(
            brand_name="Crestor",
            dose="10mg",
        )

        for alt in result["alternatives"]:
            assert "price" in alt or "cost" in alt

    @pytest.mark.asyncio
    async def test_alternatives_ranked_by_cost(self, substitution_service):
        """Alternatives should be ranked by cost."""
        result = await substitution_service.find_alternatives(
            brand_name="Lipitor",
            dose="20mg",
        )

        if len(result["alternatives"]) > 1:
            prices = [alt.get("price", 0) for alt in result["alternatives"]]
            assert prices == sorted(prices)  # Ascending order


class TestEPrescribing:
    """Tests for e-prescribing functionality."""

    @pytest.fixture
    def eprescribe_service(self):
        """Create e-prescribe service instance."""
        from src.prescription.eprescribe import EPrescribeService
        return EPrescribeService()

    @pytest.mark.asyncio
    async def test_send_to_pharmacy(self, eprescribe_service):
        """Should send prescription to pharmacy."""
        prescription = {
            "id": "rx_123",
            "patient_id": "pat_456",
            "medications": [
                {"drug": "Metformin", "dose": "500mg", "quantity": 60}
            ],
        }
        pharmacy = {
            "id": "pharm_789",
            "name": "Apollo Pharmacy",
            "email": "pharmacy@apollo.com",
        }

        with patch.object(
            eprescribe_service,
            "_send_to_pharmacy",
            return_value={"success": True, "tracking_id": "track_123"},
        ):
            result = await eprescribe_service.send(
                prescription=prescription,
                pharmacy=pharmacy,
            )

            assert result["success"]
            assert "tracking_id" in result

    @pytest.mark.asyncio
    async def test_patient_notification(self, eprescribe_service):
        """Should notify patient when Rx is sent."""
        prescription = {"id": "rx_123", "patient_id": "pat_456"}
        patient = {"id": "pat_456", "phone": "+919876543210"}

        with patch.object(
            eprescribe_service,
            "_notify_patient",
            return_value={"sent": True},
        ):
            result = await eprescribe_service.send(
                prescription=prescription,
                pharmacy={"id": "pharm_1"},
                notify_patient=True,
                patient=patient,
            )

            assert result.get("patient_notified")


class TestPrescriptionHistory:
    """Tests for prescription history tracking."""

    @pytest.fixture
    def history_service(self):
        """Create history service instance."""
        from src.prescription.history import PrescriptionHistoryService
        return PrescriptionHistoryService()

    @pytest.mark.asyncio
    async def test_get_patient_history(self, history_service):
        """Should retrieve patient's prescription history."""
        history = await history_service.get_patient_history(
            patient_id="pat_123",
            limit=10,
        )

        assert "prescriptions" in history
        for rx in history["prescriptions"]:
            assert "date" in rx
            assert "medications" in rx

    @pytest.mark.asyncio
    async def test_history_sorted_by_date(self, history_service):
        """History should be sorted by date descending."""
        history = await history_service.get_patient_history(
            patient_id="pat_123",
            limit=10,
        )

        if len(history["prescriptions"]) > 1:
            dates = [rx["date"] for rx in history["prescriptions"]]
            assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_refill_tracking(self, history_service):
        """Should track prescription refills."""
        result = await history_service.get_refill_status(
            prescription_id="rx_123",
        )

        assert "refills_remaining" in result or "refill_count" in result
        assert "last_filled" in result or "fill_date" in result


class TestPrescriptionAlerts:
    """Tests for prescription safety alerts."""

    @pytest.fixture
    def alert_service(self):
        """Create alert service instance."""
        from src.prescription.alerts import PrescriptionAlertService
        return PrescriptionAlertService()

    @pytest.mark.asyncio
    async def test_duplicate_therapy_alert(self, alert_service):
        """Should alert for duplicate therapy."""
        patient = {
            "medications": [
                {"drug": "Lisinopril", "dose": "10mg"}
            ]
        }
        new_drug = {"drug": "Enalapril", "dose": "5mg"}

        alerts = await alert_service.check(new_drug, patient)

        assert any(
            a["type"] == "duplicate_therapy" or "duplicate" in a.get("message", "").lower()
            for a in alerts
        )

    @pytest.mark.asyncio
    async def test_max_dose_alert(self, alert_service):
        """Should alert when max dose exceeded."""
        patient = {"medications": [], "weight_kg": 70}
        new_drug = {"drug": "Acetaminophen", "dose": "2000mg", "frequency": "QID"}

        alerts = await alert_service.check(new_drug, patient)

        assert any(
            a["type"] == "max_dose" or "maximum" in a.get("message", "").lower()
            for a in alerts
        )

    @pytest.mark.asyncio
    async def test_pregnancy_alert(self, alert_service):
        """Should alert for pregnancy contraindications."""
        patient = {
            "medications": [],
            "pregnancy_status": "pregnant",
            "gestational_weeks": 8,
        }
        new_drug = {"drug": "Warfarin", "dose": "5mg"}

        alerts = await alert_service.check(new_drug, patient)

        assert any(
            a["type"] == "pregnancy" or "pregnan" in a.get("message", "").lower()
            for a in alerts
        )
        assert any(a["severity"] in ["high", "critical"] for a in alerts)
