"""
Integration tests for EMR module.

Run with: pytest tests/test_emr_integration.py -v
"""

import asyncio
import pytest

from src.emr import (
    # Models
    Patient,
    Medication,
    Allergy,
    VitalSigns,
    LabResult,
    Diagnosis,
    Order,
    OrderType,
    Gender,
    Severity,
    # Client
    MockEMRClient,
    # Service
    get_emr_service,
    # Alerts
    ClinicalAlertEngine,
    AlertLevel,
    # Feedback
    RecommendationFeedback,
    FeedbackType,
    OutcomeType,
    # FHIR
    FHIRConverter,
)


@pytest.mark.asyncio
async def test_mock_client_patient_retrieval():
    """Test mock EMR client returns sample patient."""
    client = MockEMRClient()

    patient = await client.get_patient_by_id(12345)
    assert patient is not None
    assert patient.name == "Ramesh Kumar"
    assert patient.age == 65
    assert patient.gender == Gender.MALE


@pytest.mark.asyncio
async def test_mock_client_medications():
    """Test mock client returns medications."""
    client = MockEMRClient()

    meds = await client.get_current_medications(12345)
    assert len(meds) == 3
    assert any("Metformin" in med.drug_name for med in meds)
    assert any("Lisinopril" in med.drug_name for med in meds)


@pytest.mark.asyncio
async def test_mock_client_allergies():
    """Test mock client returns allergies."""
    client = MockEMRClient()

    allergies = await client.get_allergies(12345)
    assert len(allergies) == 2
    assert any(a.allergen == "Penicillin" for a in allergies)
    assert any(a.severity == Severity.FATAL for a in allergies)


@pytest.mark.asyncio
async def test_patient_summary():
    """Test complete patient summary retrieval."""
    client = MockEMRClient()

    summary = await client.get_patient_summary(12345)
    assert summary is not None
    assert summary.patient.name == "Ramesh Kumar"
    assert len(summary.current_medications) == 3
    assert len(summary.allergies) == 2
    assert summary.recent_vitals is not None
    assert len(summary.recent_labs) == 3


@pytest.mark.asyncio
async def test_emr_service_context():
    """Test EMR service patient context generation."""
    emr = get_emr_service(use_mock=True)

    context = await emr.get_patient_context_for_query(
        patient_id=12345,
        query="What antibiotic for UTI?",
    )

    assert context is not None
    assert "Ramesh Kumar" in context
    assert "ALLERGIES" in context
    assert "Penicillin" in context


@pytest.mark.asyncio
async def test_clinical_alerts_drug_allergy():
    """Test drug-allergy alert detection."""
    client = MockEMRClient()
    summary = await client.get_patient_summary(12345)

    engine = ClinicalAlertEngine()
    alerts = engine.check_all_alerts(
        patient_summary=summary,
        proposed_medication="Penicillin",  # Patient is allergic
    )

    # Should have fatal allergy alert
    allergy_alerts = [a for a in alerts if "Penicillin" in a.message]
    assert len(allergy_alerts) > 0
    assert any(a.level == AlertLevel.FATAL for a in allergy_alerts)


@pytest.mark.asyncio
async def test_clinical_alerts_nsaid_ckd():
    """Test NSAID contraindication in CKD."""
    client = MockEMRClient()
    summary = await client.get_patient_summary(12345)

    engine = ClinicalAlertEngine()
    alerts = engine.check_all_alerts(
        patient_summary=summary,
        proposed_medication="Ibuprofen",  # NSAID in CKD patient
    )

    # Should have contraindication alert
    nsaid_alerts = [a for a in alerts if "NSAID" in a.message or "CKD" in a.message]
    assert len(nsaid_alerts) > 0


@pytest.mark.asyncio
async def test_clinical_alerts_renal_dosing():
    """Test renal dosing adjustment alerts."""
    client = MockEMRClient()
    summary = await client.get_patient_summary(12345)

    engine = ClinicalAlertEngine()
    alerts = engine.check_all_alerts(
        patient_summary=summary,
        proposed_medication="Metformin",  # Patient has CKD Stage 3
    )

    # Should have renal dosing alert
    renal_alerts = [a for a in alerts if "eGFR" in a.message or "renal" in a.message.lower()]
    assert len(renal_alerts) > 0


def test_fhir_patient_conversion():
    """Test FHIR patient conversion."""
    patient = Patient(
        id=12345,
        mrn="MH2024-001234",
        name="Ramesh Kumar",
        age=65,
        gender=Gender.MALE,
        phone="+91-9876543210",
    )

    converter = FHIRConverter()
    fhir_patient = converter.patient_to_fhir(patient)

    assert fhir_patient["resourceType"] == "Patient"
    assert fhir_patient["gender"] == "male"
    assert len(fhir_patient["identifier"]) > 0


def test_fhir_allergy_conversion():
    """Test FHIR allergy conversion."""
    allergy = Allergy(
        patient_id=12345,
        allergen="Penicillin",
        allergen_type="drug",
        reaction="Anaphylaxis",
        severity=Severity.FATAL,
    )

    converter = FHIRConverter()
    fhir_allergy = converter.allergy_to_fhir(allergy)

    assert fhir_allergy["resourceType"] == "AllergyIntolerance"
    assert fhir_allergy["criticality"] == "high"
    assert fhir_allergy["code"]["text"] == "Penicillin"


def test_feedback_analytics():
    """Test feedback analytics calculation."""
    from src.emr.feedback import FeedbackStore

    store = FeedbackStore()

    # Add sample feedback
    for i in range(10):
        fb = RecommendationFeedback(
            patient_id=12345,
            query=f"Query {i}",
            recommendation=f"Recommendation {i}",
            feedback_type=FeedbackType.FOLLOWED if i < 7 else FeedbackType.REJECTED,
            action_taken=f"Action {i}",
            outcome=OutcomeType.IMPROVED if i < 6 else OutcomeType.UNCHANGED,
        )
        store.add_feedback(fb)

    analytics = store.get_analytics()

    assert analytics.total_recommendations == 10
    assert analytics.followed_count == 7
    assert analytics.rejected_count == 3
    assert analytics.follow_rate == 70.0
    assert analytics.improved_count == 6


@pytest.mark.asyncio
async def test_prescription_context():
    """Test prescription-specific context generation."""
    emr = get_emr_service(use_mock=True)

    context, alerts = await emr.get_prescription_context(
        patient_id=12345,
        drug_name="Amoxicillin",
    )

    assert "PRESCRIPTION CONTEXT" in context
    assert "ALLERGIES" in context
    assert "Penicillin" in context  # Should warn about cross-allergy


@pytest.mark.asyncio
async def test_create_order_with_alerts():
    """Test order creation with safety checks."""
    emr = get_emr_service(use_mock=True)

    order = Order(
        patient_id=12345,
        order_type=OrderType.LAB,
        order_name="Complete Blood Count",
        order_details={"fasting": False},
    )

    created = await emr.create_order(12345, order)
    # Lab orders should succeed (no drug alerts)
    assert created is not None


def test_patient_summary_context_string():
    """Test patient summary to context string conversion."""
    patient = Patient(
        id=12345,
        mrn="TEST",
        name="Test Patient",
        age=65,
        gender=Gender.MALE,
    )

    from src.emr.models import PatientSummary

    summary = PatientSummary(
        patient=patient,
        active_diagnoses=[
            Diagnosis(
                patient_id=12345,
                diagnosis_name="Type 2 Diabetes",
                is_chronic=True,
            )
        ],
        current_medications=[
            Medication(
                patient_id=12345,
                drug_name="Metformin",
                dosage="1000mg",
                frequency="BID",
            )
        ],
        allergies=[
            Allergy(
                patient_id=12345,
                allergen="Penicillin",
                reaction="Rash",
                severity=Severity.MODERATE,
            )
        ],
    )

    context_str = summary.to_context_string()

    assert "Test Patient" in context_str
    assert "Type 2 Diabetes" in context_str
    assert "Metformin" in context_str
    assert "Penicillin" in context_str


def test_bmi_calculation():
    """Test automatic BMI calculation."""
    vitals = VitalSigns(
        patient_id=12345,
        weight_kg=82.0,
        height_cm=170.0,
    )

    bmi = vitals.calculate_bmi()
    assert bmi is not None
    assert 28.0 <= bmi <= 29.0  # Should be ~28.4


@pytest.mark.asyncio
async def test_sync_status():
    """Test sync status reporting."""
    emr = get_emr_service(use_mock=True)

    status = emr.get_sync_status()

    assert "offline_mode" in status
    assert "cached_patients" in status
    assert "sync_stats" in status
    assert isinstance(status["cached_patients"], int)


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
