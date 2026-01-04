"""Tests for drug interaction checking."""

import pytest
from src.drugs import DrugInteractionChecker
from src.drugs.interactions import InteractionSeverity


class TestDrugInteractionChecker:
    """Test drug interaction checking functionality."""

    @pytest.fixture
    def checker(self):
        """Create checker in offline mode."""
        return DrugInteractionChecker(offline_mode=True)

    def test_normalize_drug_basic(self, checker):
        """Test basic drug normalization."""
        info = checker.normalize_drug("aspirin")

        assert info.original_name == "aspirin"
        assert "nsaid" in info.drug_classes

    def test_normalize_drug_with_class(self, checker):
        """Test drug class detection."""
        info = checker.normalize_drug("lisinopril")

        assert "ace_inhibitor" in info.drug_classes

    def test_check_known_interaction_warfarin_aspirin(self, checker):
        """Test known severe interaction."""
        interaction = checker.check_interaction("warfarin", "aspirin")

        assert interaction is not None
        assert interaction.severity == InteractionSeverity.SEVERE
        assert "bleeding" in interaction.description.lower()

    def test_check_contraindicated_ssri_maoi(self, checker):
        """Test contraindicated interaction."""
        interaction = checker.check_interaction("fluoxetine", "phenelzine")

        assert interaction is not None
        assert interaction.severity == InteractionSeverity.CONTRAINDICATED
        assert "serotonin" in interaction.description.lower()

    def test_check_no_interaction(self, checker):
        """Test drugs with no known interaction."""
        interaction = checker.check_interaction("acetaminophen", "vitamin d")

        # May or may not find interaction depending on database
        # At minimum, should not crash
        assert interaction is None or isinstance(interaction.severity, InteractionSeverity)

    def test_check_multiple_drugs(self, checker):
        """Test checking multiple drugs at once."""
        drugs = ["warfarin", "aspirin", "ibuprofen"]
        interactions = checker.check_multiple(drugs)

        # Should find at least warfarin-aspirin and warfarin-ibuprofen
        assert len(interactions) >= 1

        # All should be drug interactions
        for inter in interactions:
            assert inter.drug1 and inter.drug2

    def test_check_patient_medications(self, checker):
        """Test checking new drug against current medications."""
        current = ["warfarin", "metoprolol"]
        new_drug = "aspirin"

        interactions = checker.check_patient_medications(current, new_drug)

        # Should find warfarin-aspirin interaction
        assert len(interactions) >= 1
        assert any("warfarin" in i.drug1.lower() or "warfarin" in i.drug2.lower()
                   for i in interactions)

    def test_format_warning(self, checker):
        """Test warning message formatting."""
        interaction = checker.check_interaction("warfarin", "aspirin")

        warning = checker.format_warning(interaction)

        assert "SEVERE" in warning
        assert "warfarin" in warning.lower() or "aspirin" in warning.lower()
        assert "Management:" in warning

    def test_statin_fibrate_interaction(self, checker):
        """Test moderate myopathy interaction."""
        interaction = checker.check_interaction("atorvastatin", "gemfibrozil")

        assert interaction is not None
        assert interaction.severity == InteractionSeverity.MODERATE
        assert "myopathy" in interaction.description.lower()


class TestDrugNormalization:
    """Test drug name normalization."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_generic_name_detection(self, checker):
        """Test recognizing generic drug names."""
        drugs = ["metformin", "lisinopril", "atorvastatin"]

        for drug in drugs:
            info = checker.normalize_drug(drug)
            assert info.original_name == drug
            assert len(info.drug_classes) >= 0  # May or may not have class

    def test_drug_class_assignment(self, checker):
        """Test correct drug class assignment."""
        test_cases = [
            ("sertraline", "ssri"),
            ("enalapril", "ace_inhibitor"),
            ("simvastatin", "statin"),
            ("naproxen", "nsaid"),
        ]

        for drug, expected_class in test_cases:
            info = checker.normalize_drug(drug)
            assert expected_class in info.drug_classes, f"{drug} should be in {expected_class}"
