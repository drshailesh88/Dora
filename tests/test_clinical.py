"""
Tests for clinical decision support module.
Tests differential diagnosis, drug dosing, protocols, and clinical reasoning.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestDifferentialDiagnosis:
    """Tests for differential diagnosis generation."""

    @pytest.fixture
    def symptom_analyzer(self):
        """Create symptom analyzer instance."""
        from src.clinical.differential import SymptomAnalyzer
        return SymptomAnalyzer()

    @pytest.fixture
    def sample_symptoms(self):
        """Common symptom presentations."""
        return {
            "chest_pain": {
                "symptoms": ["chest pain", "shortness of breath", "diaphoresis"],
                "vitals": {"bp": "160/100", "hr": 110, "spo2": 94},
                "age": 55,
                "sex": "male",
                "risk_factors": ["diabetes", "hypertension", "smoking"],
            },
            "headache": {
                "symptoms": ["severe headache", "photophobia", "neck stiffness"],
                "vitals": {"bp": "140/90", "hr": 88, "temp": 39.2},
                "age": 25,
                "sex": "female",
                "risk_factors": [],
            },
            "abdominal_pain": {
                "symptoms": ["RLQ pain", "nausea", "anorexia", "fever"],
                "vitals": {"bp": "120/80", "hr": 92, "temp": 38.5},
                "age": 22,
                "sex": "male",
                "risk_factors": [],
            },
        }

    def test_chest_pain_includes_acs(self, symptom_analyzer, sample_symptoms):
        """Chest pain DDx should include ACS."""
        presentation = sample_symptoms["chest_pain"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
            risk_factors=presentation["risk_factors"],
        )

        diagnoses = [d["name"].lower() for d in result["differentials"]]
        assert any("acute coronary" in d or "acs" in d or "mi" in d for d in diagnoses)

    def test_meningitis_presentation(self, symptom_analyzer, sample_symptoms):
        """Classic meningitis triad should flag meningitis."""
        presentation = sample_symptoms["headache"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
        )

        diagnoses = [d["name"].lower() for d in result["differentials"]]
        assert any("meningitis" in d for d in diagnoses)
        # Should be high priority
        top_3 = diagnoses[:3]
        assert any("meningitis" in d for d in top_3)

    def test_appendicitis_presentation(self, symptom_analyzer, sample_symptoms):
        """RLQ pain with fever should include appendicitis."""
        presentation = sample_symptoms["abdominal_pain"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
        )

        diagnoses = [d["name"].lower() for d in result["differentials"]]
        assert any("appendicitis" in d for d in diagnoses)

    def test_differential_includes_likelihood(self, symptom_analyzer, sample_symptoms):
        """Each diagnosis should have likelihood score."""
        presentation = sample_symptoms["chest_pain"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
        )

        for dx in result["differentials"]:
            assert "likelihood" in dx or "probability" in dx or "score" in dx

    def test_red_flags_identified(self, symptom_analyzer, sample_symptoms):
        """Critical symptoms should flag red flags."""
        presentation = sample_symptoms["headache"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
        )

        assert "red_flags" in result or "warnings" in result

    def test_workup_recommendations(self, symptom_analyzer, sample_symptoms):
        """Should recommend appropriate workup."""
        presentation = sample_symptoms["chest_pain"]
        result = symptom_analyzer.generate_differential(
            symptoms=presentation["symptoms"],
            vitals=presentation["vitals"],
            demographics={"age": presentation["age"], "sex": presentation["sex"]},
        )

        assert "workup" in result or "investigations" in result or "tests" in result


class TestDrugDosingEngine:
    """Tests for drug dosing calculations."""

    @pytest.fixture
    def dosing_engine(self):
        """Create dosing engine instance."""
        from src.clinical.dosing import DrugDosingEngine
        return DrugDosingEngine()

    @pytest.fixture
    def patient_contexts(self):
        """Various patient contexts for dosing."""
        return {
            "normal_adult": {
                "weight": 70,
                "height": 170,
                "age": 45,
                "sex": "male",
                "creatinine": 1.0,
                "egfr": 90,
                "liver_function": "normal",
            },
            "renal_impaired": {
                "weight": 65,
                "height": 165,
                "age": 70,
                "sex": "female",
                "creatinine": 2.5,
                "egfr": 25,
                "liver_function": "normal",
            },
            "pediatric": {
                "weight": 20,
                "height": 110,
                "age": 6,
                "sex": "male",
                "creatinine": 0.5,
                "egfr": 120,
                "liver_function": "normal",
            },
            "hepatic_impaired": {
                "weight": 75,
                "height": 175,
                "age": 55,
                "sex": "male",
                "creatinine": 1.0,
                "egfr": 85,
                "liver_function": "child_pugh_b",
            },
        }

    def test_vancomycin_renal_adjustment(self, dosing_engine, patient_contexts):
        """Vancomycin should be adjusted for renal function."""
        normal = dosing_engine.calculate_dose(
            drug="vancomycin",
            indication="MRSA bacteremia",
            patient=patient_contexts["normal_adult"],
        )

        impaired = dosing_engine.calculate_dose(
            drug="vancomycin",
            indication="MRSA bacteremia",
            patient=patient_contexts["renal_impaired"],
        )

        # Dose or frequency should be reduced
        assert impaired["daily_dose"] < normal["daily_dose"] or \
               impaired["frequency_hours"] > normal["frequency_hours"]

    def test_pediatric_weight_based_dosing(self, dosing_engine, patient_contexts):
        """Pediatric doses should be weight-based."""
        result = dosing_engine.calculate_dose(
            drug="amoxicillin",
            indication="acute otitis media",
            patient=patient_contexts["pediatric"],
        )

        # Should have mg/kg in calculation
        assert "per_kg" in result or result.get("weight_based", False)
        # Total dose should be appropriate for 20kg child
        assert result["single_dose_mg"] < 1000  # Adult dose is 500-1000mg

    def test_hepatic_dose_adjustment(self, dosing_engine, patient_contexts):
        """Hepatically metabolized drugs need adjustment."""
        result = dosing_engine.calculate_dose(
            drug="metronidazole",
            indication="intra-abdominal infection",
            patient=patient_contexts["hepatic_impaired"],
        )

        assert result.get("hepatic_adjustment", False) or \
               "reduce" in result.get("notes", "").lower()

    def test_loading_dose_calculation(self, dosing_engine, patient_contexts):
        """Some drugs require loading doses."""
        result = dosing_engine.calculate_dose(
            drug="digoxin",
            indication="atrial fibrillation rate control",
            patient=patient_contexts["normal_adult"],
        )

        assert "loading_dose" in result

    def test_dose_includes_route(self, dosing_engine, patient_contexts):
        """Dose should specify administration route."""
        result = dosing_engine.calculate_dose(
            drug="ciprofloxacin",
            indication="UTI",
            patient=patient_contexts["normal_adult"],
        )

        assert "route" in result
        assert result["route"] in ["oral", "IV", "IM", "SC", "topical", "PO", "IV/PO"]

    def test_max_dose_not_exceeded(self, dosing_engine, patient_contexts):
        """Should not exceed maximum safe dose."""
        # Very heavy patient
        heavy_patient = patient_contexts["normal_adult"].copy()
        heavy_patient["weight"] = 150

        result = dosing_engine.calculate_dose(
            drug="acetaminophen",
            indication="pain",
            patient=heavy_patient,
        )

        # Should not exceed 4g/day for acetaminophen
        assert result["max_daily_mg"] <= 4000


class TestClinicalProtocols:
    """Tests for clinical protocol engine."""

    @pytest.fixture
    def protocol_engine(self):
        """Create protocol engine instance."""
        from src.clinical.protocols import ProtocolEngine
        return ProtocolEngine()

    def test_sepsis_protocol_steps(self, protocol_engine):
        """Sepsis protocol should include SEP-1 bundle."""
        result = protocol_engine.get_protocol("sepsis")

        steps = [s["action"].lower() for s in result["steps"]]

        # SEP-1 bundle components
        assert any("lactate" in s for s in steps)
        assert any("blood culture" in s for s in steps)
        assert any("antibiotic" in s for s in steps)
        assert any("fluid" in s for s in steps)

    def test_stroke_protocol_timing(self, protocol_engine):
        """Stroke protocol should have time-critical steps."""
        result = protocol_engine.get_protocol("acute_stroke")

        # Should have timing requirements
        has_timing = any(
            s.get("time_limit") or s.get("within_minutes")
            for s in result["steps"]
        )
        assert has_timing

    def test_protocol_includes_decision_points(self, protocol_engine):
        """Protocols should have decision branch points."""
        result = protocol_engine.get_protocol("chest_pain")

        # Should have conditional branches
        has_conditions = any(
            s.get("condition") or s.get("if") or s.get("branch")
            for s in result["steps"]
        )
        assert has_conditions

    def test_protocol_references(self, protocol_engine):
        """Protocols should cite guideline sources."""
        result = protocol_engine.get_protocol("heart_failure")

        assert "references" in result or "sources" in result or "guidelines" in result


class TestClinicalAlerts:
    """Tests for clinical alert system."""

    @pytest.fixture
    def alert_engine(self):
        """Create alert engine instance."""
        from src.clinical.alerts import ClinicalAlertEngine
        return ClinicalAlertEngine()

    @pytest.fixture
    def patient_with_allergy(self):
        """Patient with penicillin allergy."""
        return {
            "allergies": [
                {"drug": "Penicillin", "reaction": "anaphylaxis", "severity": "severe"}
            ],
            "medications": [
                {"name": "Lisinopril", "dose": "10mg", "frequency": "daily"}
            ],
        }

    def test_allergy_alert_triggered(self, alert_engine, patient_with_allergy):
        """Prescribing penicillin to allergic patient should alert."""
        alerts = alert_engine.check_prescription(
            drug="amoxicillin",  # Penicillin-class
            patient=patient_with_allergy,
        )

        allergy_alerts = [a for a in alerts if a["type"] == "allergy"]
        assert len(allergy_alerts) > 0
        assert any(a["severity"] in ["high", "severe", "critical"] for a in allergy_alerts)

    def test_drug_interaction_alert(self, alert_engine):
        """Dangerous drug combinations should alert."""
        patient = {
            "allergies": [],
            "medications": [
                {"name": "Warfarin", "dose": "5mg", "frequency": "daily"}
            ],
        }

        alerts = alert_engine.check_prescription(
            drug="aspirin",
            patient=patient,
        )

        interaction_alerts = [a for a in alerts if a["type"] == "interaction"]
        assert len(interaction_alerts) > 0

    def test_contraindication_alert(self, alert_engine):
        """Contraindicated drugs should alert."""
        patient = {
            "allergies": [],
            "medications": [],
            "conditions": [{"name": "Severe liver failure", "icd10": "K72.9"}],
        }

        alerts = alert_engine.check_prescription(
            drug="metformin",
            patient=patient,
        )

        contra_alerts = [a for a in alerts if a["type"] == "contraindication"]
        assert len(contra_alerts) > 0

    def test_alert_includes_recommendation(self, alert_engine, patient_with_allergy):
        """Alerts should include actionable recommendations."""
        alerts = alert_engine.check_prescription(
            drug="amoxicillin",
            patient=patient_with_allergy,
        )

        for alert in alerts:
            assert "recommendation" in alert or "action" in alert or "alternative" in alert


class TestClinicalReasoning:
    """Tests for AI clinical reasoning."""

    @pytest.fixture
    def reasoning_engine(self):
        """Create reasoning engine instance."""
        from src.clinical.reasoning import ClinicalReasoningEngine
        return ClinicalReasoningEngine()

    @pytest.mark.asyncio
    async def test_reasoning_chain_generated(self, reasoning_engine):
        """Should generate step-by-step reasoning."""
        query = "45yo male with crushing chest pain, diaphoresis, and ST elevations in leads II, III, aVF"

        result = await reasoning_engine.analyze(query)

        assert "reasoning_chain" in result or "steps" in result
        assert len(result.get("reasoning_chain", result.get("steps", []))) >= 3

    @pytest.mark.asyncio
    async def test_evidence_cited(self, reasoning_engine):
        """Reasoning should cite evidence."""
        query = "What is first-line treatment for community-acquired pneumonia?"

        result = await reasoning_engine.analyze(query)

        assert "citations" in result or "references" in result or "evidence" in result

    @pytest.mark.asyncio
    async def test_confidence_score_included(self, reasoning_engine):
        """Should include confidence in conclusion."""
        query = "Patient with fever, cough, and bilateral infiltrates - what are the likely diagnoses?"

        result = await reasoning_engine.analyze(query)

        assert "confidence" in result or any(
            "confidence" in str(d).lower()
            for d in result.get("differentials", [])
        )

    @pytest.mark.asyncio
    async def test_uncertainty_acknowledged(self, reasoning_engine):
        """Should acknowledge uncertainty when appropriate."""
        query = "Nonspecific symptoms: fatigue and mild headache for 2 weeks"

        result = await reasoning_engine.analyze(query)

        # Should indicate broad differential or uncertainty
        assert result.get("uncertainty_level") or \
               len(result.get("differentials", [])) > 5 or \
               "broad" in str(result).lower()


class TestLabInterpretation:
    """Tests for lab result interpretation."""

    @pytest.fixture
    def lab_interpreter(self):
        """Create lab interpreter instance."""
        from src.clinical.labs import LabInterpreter
        return LabInterpreter()

    def test_critical_value_flagged(self, lab_interpreter):
        """Critical values should be flagged."""
        labs = {
            "potassium": 6.8,  # Critical high
            "sodium": 140,
            "chloride": 100,
        }

        result = lab_interpreter.interpret(labs)

        k_result = result["potassium"]
        assert k_result["flag"] in ["critical", "critical_high", "panic"]

    def test_pattern_recognition(self, lab_interpreter):
        """Should recognize lab patterns."""
        # DKA pattern
        labs = {
            "glucose": 450,
            "pH": 7.15,
            "bicarbonate": 10,
            "anion_gap": 28,
            "potassium": 5.8,
        }

        result = lab_interpreter.interpret(labs)

        patterns = result.get("patterns", [])
        pattern_names = [p["name"].lower() for p in patterns]
        assert any("dka" in p or "ketoacidosis" in p for p in pattern_names)

    def test_trending_analysis(self, lab_interpreter):
        """Should analyze trends over time."""
        labs_series = [
            {"creatinine": 1.0, "timestamp": "2025-01-01"},
            {"creatinine": 1.5, "timestamp": "2025-01-02"},
            {"creatinine": 2.2, "timestamp": "2025-01-03"},
        ]

        result = lab_interpreter.interpret_trend(labs_series)

        assert "trend" in result
        assert result["trend"]["creatinine"]["direction"] in ["increasing", "rising", "upward"]

    def test_reference_ranges_applied(self, lab_interpreter):
        """Should use appropriate reference ranges."""
        # Same value, different context
        adult_labs = {"hemoglobin": 11.0}
        pediatric_labs = {"hemoglobin": 11.0}

        adult_result = lab_interpreter.interpret(
            adult_labs,
            context={"age": 45, "sex": "male"}
        )
        child_result = lab_interpreter.interpret(
            pediatric_labs,
            context={"age": 5, "sex": "male"}
        )

        # 11 g/dL is low for adult male but normal for child
        assert adult_result["hemoglobin"]["flag"] in ["low", "abnormal"]
        assert child_result["hemoglobin"]["flag"] in ["normal", "none"]
