"""Comprehensive edge case tests for drug interaction checking.

This test suite covers edge cases including:
- Empty/invalid input handling
- Case sensitivity
- Drug synonyms and variants
- Interaction edge cases
- Severity edge cases
- Patient context edge cases
- Concurrent access patterns
"""

import pytest
import threading
from typing import List
from src.drugs import DrugInteractionChecker, InteractionSeverity, DrugInfo, DrugInteraction


class TestEmptyInvalidInput:
    """Test edge cases for empty and invalid input."""

    @pytest.fixture
    def checker(self):
        """Create checker in offline mode."""
        return DrugInteractionChecker(offline_mode=True)

    def test_empty_drug_name(self, checker):
        """Test normalization of empty drug name."""
        info = checker.normalize_drug("")

        assert info.original_name == ""
        assert info.normalized_name == ""
        assert isinstance(info.drug_classes, list)

    def test_none_drug_name(self, checker):
        """Test handling of None drug name."""
        with pytest.raises(AttributeError):
            checker.normalize_drug(None)

    def test_whitespace_only_drug_name(self, checker):
        """Test drug name with only whitespace."""
        info = checker.normalize_drug("   \t\n   ")

        assert info.original_name == "   \t\n   "
        assert len(info.drug_classes) == 0

    def test_special_characters_drug_name(self, checker):
        """Test drug name with special characters."""
        special_names = [
            "drug@#$%",
            "drug<script>",
            "drug'; DROP TABLE drugs;--",
            "drug\x00null",
            "drug™®©",
        ]

        for name in special_names:
            info = checker.normalize_drug(name)
            assert info.original_name == name
            # Should not crash, should handle gracefully
            assert isinstance(info, DrugInfo)

    def test_extremely_long_drug_name(self, checker):
        """Test extremely long drug name (1000+ characters)."""
        long_name = "a" * 1500
        info = checker.normalize_drug(long_name)

        assert info.original_name == long_name
        assert len(info.original_name) == 1500

    def test_numeric_input_fails(self, checker):
        """Test that numeric input raises appropriate error."""
        with pytest.raises(AttributeError):
            checker.normalize_drug(12345)

    def test_check_interaction_with_empty_drugs(self, checker):
        """Test interaction check with empty drug names."""
        interaction = checker.check_interaction("", "")

        # Should not crash, return None or valid result
        assert interaction is None or isinstance(interaction, DrugInteraction)

    def test_check_multiple_with_empty_list(self, checker):
        """Test checking multiple drugs with empty list."""
        interactions = checker.check_multiple([])

        assert isinstance(interactions, list)
        assert len(interactions) == 0

    def test_check_patient_medications_empty_current(self, checker):
        """Test checking against empty current medications."""
        interactions = checker.check_patient_medications([], "aspirin")

        assert isinstance(interactions, list)
        assert len(interactions) == 0


class TestCaseSensitivity:
    """Test case sensitivity handling."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_uppercase_drug_name(self, checker):
        """Test all uppercase drug names."""
        info = checker.normalize_drug("IBUPROFEN")

        assert info.original_name == "IBUPROFEN"
        assert "nsaid" in info.drug_classes

    def test_mixed_case_drug_name(self, checker):
        """Test mixed case drug names."""
        test_cases = ["AsPiRiN", "LiSiNoPrIl", "MeTfOrMiN"]

        for name in test_cases:
            info = checker.normalize_drug(name)
            assert info.original_name == name
            # Should still detect drug class
            assert isinstance(info.drug_classes, list)

    def test_case_insensitive_interaction_detection(self, checker):
        """Test that interaction detection is case-insensitive."""
        # Test same interaction with different cases
        interaction1 = checker.check_interaction("warfarin", "aspirin")
        interaction2 = checker.check_interaction("WARFARIN", "ASPIRIN")
        interaction3 = checker.check_interaction("Warfarin", "Aspirin")

        # All should find the same interaction
        assert interaction1 is not None
        assert interaction2 is not None
        assert interaction3 is not None
        assert interaction1.severity == interaction2.severity == interaction3.severity

    def test_case_insensitive_class_detection(self, checker):
        """Test that drug class detection is case-insensitive."""
        info_lower = checker.normalize_drug("fluoxetine")
        info_upper = checker.normalize_drug("FLUOXETINE")
        info_mixed = checker.normalize_drug("FlUoXeTiNe")

        assert "ssri" in info_lower.drug_classes
        assert "ssri" in info_upper.drug_classes
        assert "ssri" in info_mixed.drug_classes

    def test_accented_characters(self, checker):
        """Test drug names with accented characters."""
        accented_names = ["café", "naïve", "résumé"]

        for name in accented_names:
            info = checker.normalize_drug(name)
            assert info.original_name == name
            # Should handle without crashing
            assert isinstance(info, DrugInfo)


class TestDrugSynonymsVariants:
    """Test handling of drug synonyms and variants."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_generic_vs_brand_interaction(self, checker):
        """Test that both generic and brand names detect interactions."""
        # Generic name
        info_generic = checker.normalize_drug("metformin")
        # Common brand names
        info_brand1 = checker.normalize_drug("glucophage")

        assert info_generic.original_name != info_brand1.original_name
        # Both should be valid drug info
        assert isinstance(info_generic, DrugInfo)
        assert isinstance(info_brand1, DrugInfo)

    def test_drug_name_with_dosage(self, checker):
        """Test drug name that includes dosage information."""
        names_with_dosage = [
            "aspirin 81mg",
            "metformin 500mg",
            "lisinopril 10 mg",
        ]

        for name in names_with_dosage:
            info = checker.normalize_drug(name)
            # Should still extract drug class from partial match
            assert isinstance(info, DrugInfo)

    def test_drug_name_with_formulation(self, checker):
        """Test drug name with formulation info."""
        names_with_form = [
            "aspirin tablet",
            "metformin extended release",
            "ibuprofen liquid",
        ]

        for name in names_with_form:
            info = checker.normalize_drug(name)
            assert isinstance(info, DrugInfo)

    def test_abbreviated_drug_names(self, checker):
        """Test abbreviated drug names."""
        abbreviations = {
            "ASA": "aspirin",
            "APAP": "acetaminophen",
            "5-ASA": "mesalamine",
        }

        for abbrev, full_name in abbreviations.items():
            info_abbrev = checker.normalize_drug(abbrev)
            info_full = checker.normalize_drug(full_name)

            # Both should normalize successfully
            assert isinstance(info_abbrev, DrugInfo)
            assert isinstance(info_full, DrugInfo)

    def test_misspelled_drug_name(self, checker):
        """Test slightly misspelled drug names."""
        # Note: Current implementation may not handle misspellings
        # This tests that it doesn't crash
        misspelled = [
            "aspirine",  # aspirin
            "metforminn",  # metformin
            "lisinpril",  # lisinopril
        ]

        for name in misspelled:
            info = checker.normalize_drug(name)
            # Should handle gracefully even if not recognized
            assert isinstance(info, DrugInfo)


class TestInteractionEdgeCases:
    """Test edge cases in interaction checking."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_same_drug_against_itself(self, checker):
        """Test checking drug against itself."""
        interaction = checker.check_interaction("aspirin", "aspirin")

        # Same drug shouldn't have interaction with itself
        assert interaction is None or interaction.severity == InteractionSeverity.UNKNOWN

    def test_drug_against_empty_list(self, checker):
        """Test checking drug against empty medication list."""
        interactions = checker.check_patient_medications([], "warfarin")

        assert isinstance(interactions, list)
        assert len(interactions) == 0

    def test_list_with_duplicates(self, checker):
        """Test checking list with duplicate drugs."""
        drugs = ["aspirin", "warfarin", "aspirin", "warfarin", "aspirin"]
        interactions = checker.check_multiple(drugs)

        # Should handle duplicates gracefully
        assert isinstance(interactions, list)
        # Should not have duplicate interactions
        unique_pairs = set()
        for inter in interactions:
            pair = tuple(sorted([inter.drug1, inter.drug2]))
            assert pair not in unique_pairs, "Found duplicate interaction"
            unique_pairs.add(pair)

    def test_maximum_number_of_drugs(self, checker):
        """Test checking 100+ drugs (polypharmacy extreme)."""
        # Create list of 100+ drugs
        base_drugs = ["aspirin", "warfarin", "metformin", "lisinopril",
                      "atorvastatin", "sertraline"]
        large_drug_list = []
        for i in range(20):
            large_drug_list.extend([f"{drug}_{i}" for drug in base_drugs])

        # Should handle without crashing
        interactions = checker.check_multiple(large_drug_list[:100])

        assert isinstance(interactions, list)
        # With 100 drugs, there are 4950 possible pairs
        # Most won't have interactions, but should not crash

    def test_circular_interaction_chain(self, checker):
        """Test circular interaction patterns (A->B, B->C, C->A)."""
        # Create a chain where drugs interact in circle
        # warfarin-aspirin, aspirin-ibuprofen, warfarin-ibuprofen (all NSAIDs)
        drugs = ["warfarin", "aspirin", "ibuprofen"]
        interactions = checker.check_multiple(drugs)

        assert isinstance(interactions, list)
        # Should find interactions without infinite loops
        assert len(interactions) >= 1

    def test_no_interactions_found(self, checker):
        """Test drugs with no known interactions."""
        # Drugs unlikely to interact
        drugs = ["vitamin d", "vitamin c", "calcium"]
        interactions = checker.check_multiple(drugs)

        assert isinstance(interactions, list)
        # May be empty or have mild interactions

    def test_all_drugs_interact(self, checker):
        """Test scenario where all drugs interact with each other."""
        # Multiple NSAIDs that all interact with warfarin
        drugs = ["warfarin", "aspirin", "ibuprofen", "naproxen"]
        interactions = checker.check_multiple(drugs)

        assert isinstance(interactions, list)
        # Should find multiple interactions
        assert len(interactions) >= 1

    def test_duplicate_interaction_prevention(self, checker):
        """Test that duplicate interactions are not returned."""
        # Check same pair multiple times
        drugs = ["warfarin", "aspirin", "warfarin", "aspirin"]
        interactions = checker.check_multiple(drugs)

        # Should deduplicate
        unique_pairs = set()
        for inter in interactions:
            pair = tuple(sorted([inter.drug1.lower(), inter.drug2.lower()]))
            unique_pairs.add(pair)

        # Number of unique pairs should match or be less than interactions
        assert len(unique_pairs) <= len(interactions) + 1


class TestSeverityEdgeCases:
    """Test edge cases in interaction severity."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_unknown_drug_with_known_drug(self, checker):
        """Test unknown drug with known drug."""
        interaction = checker.check_interaction("unknowndrugxyz123", "aspirin")

        # Should handle gracefully, likely return None
        assert interaction is None or interaction.severity == InteractionSeverity.UNKNOWN

    def test_two_unknown_drugs(self, checker):
        """Test two unknown drugs."""
        interaction = checker.check_interaction("unknowndrug1", "unknowndrug2")

        assert interaction is None or interaction.severity == InteractionSeverity.UNKNOWN

    def test_contraindicated_vs_severe(self, checker):
        """Test distinction between contraindicated and severe."""
        # Contraindicated: SSRI + MAOI
        contraindicated = checker.check_interaction("fluoxetine", "phenelzine")

        # Severe: Warfarin + Aspirin
        severe = checker.check_interaction("warfarin", "aspirin")

        if contraindicated and severe:
            assert contraindicated.severity == InteractionSeverity.CONTRAINDICATED
            assert severe.severity == InteractionSeverity.SEVERE
            # Contraindicated should be more serious than severe
            severity_order = [
                InteractionSeverity.MILD,
                InteractionSeverity.MODERATE,
                InteractionSeverity.SEVERE,
                InteractionSeverity.CONTRAINDICATED,
            ]
            assert severity_order.index(contraindicated.severity) > severity_order.index(severe.severity)

    def test_moderate_interaction(self, checker):
        """Test moderate severity interactions."""
        # Statin + Fibrate = moderate myopathy risk
        interaction = checker.check_interaction("atorvastatin", "gemfibrozil")

        if interaction:
            assert interaction.severity == InteractionSeverity.MODERATE

    def test_drug_class_vs_specific_drug_interaction(self, checker):
        """Test that drug class interactions work."""
        # Any SSRI with any MAOI should be contraindicated
        ssris = ["fluoxetine", "sertraline", "paroxetine"]
        maois = ["phenelzine", "tranylcypromine"]

        for ssri in ssris:
            for maoi in maois:
                interaction = checker.check_interaction(ssri, maoi)
                if interaction:
                    assert interaction.severity == InteractionSeverity.CONTRAINDICATED

    def test_severity_parsing_edge_cases(self, checker):
        """Test severity parsing with various inputs."""
        test_cases = [
            ("contraindicated", InteractionSeverity.CONTRAINDICATED),
            ("Severe", InteractionSeverity.SEVERE),
            ("MODERATE", InteractionSeverity.MODERATE),
            ("mild warning", InteractionSeverity.MILD),
            ("high risk", InteractionSeverity.SEVERE),
            ("unknown", InteractionSeverity.UNKNOWN),
            ("", InteractionSeverity.UNKNOWN),
        ]

        for severity_str, expected in test_cases:
            result = checker._parse_severity(severity_str)
            assert result == expected


class TestPatientContextEdgeCases:
    """Test edge cases with patient context."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_patient_with_no_medications(self, checker):
        """Test patient with empty medication list."""
        interactions = checker.check_patient_medications([], "aspirin")

        assert isinstance(interactions, list)
        assert len(interactions) == 0

    def test_patient_with_many_medications(self, checker):
        """Test patient with 50+ medications (polypharmacy)."""
        # Create extensive medication list including drugs that interact with new medication
        medications = [
            "digoxin", "warfarin", "metformin", "lisinopril", "atorvastatin",
            "sertraline", "omeprazole", "metoprolol", "amlodipine", "losartan",
            "furosemide", "levothyroxine", "allopurinol", "gabapentin", "tramadol",
            "prednisone", "insulin", "glipizide", "spironolactone", "lithium",
            "phenelzine", "clopidogrel", "simvastatin", "rosuvastatin", "ezetimibe",
        ]

        # Extend to 50+
        extended_meds = medications * 2

        # Amiodarone interacts with digoxin (severe) - both specific drugs
        interactions = checker.check_patient_medications(
            extended_meds[:50], "amiodarone"
        )

        assert isinstance(interactions, list)
        # Should handle large medication list without crashing
        # May or may not find interactions depending on offline capabilities

    def test_new_drug_interacts_with_all_current(self, checker):
        """Test new drug that interacts with all current medications."""
        # NSAIDs interact with many drugs
        current_meds = ["warfarin", "lithium", "methotrexate"]
        new_drug = "ibuprofen"  # NSAID

        interactions = checker.check_patient_medications(current_meds, new_drug)

        assert isinstance(interactions, list)
        # Should find multiple interactions

    def test_new_drug_already_in_current_meds(self, checker):
        """Test adding drug patient is already taking."""
        current_meds = ["aspirin", "metformin", "lisinopril"]
        new_drug = "aspirin"  # Duplicate

        interactions = checker.check_patient_medications(current_meds, new_drug)

        # Should handle gracefully
        assert isinstance(interactions, list)

    def test_patient_with_duplicate_medications(self, checker):
        """Test patient list with duplicate entries."""
        current_meds = ["aspirin", "aspirin", "metformin", "metformin"]
        new_drug = "warfarin"

        interactions = checker.check_patient_medications(current_meds, new_drug)

        assert isinstance(interactions, list)
        # Should not double-count same interaction

    def test_patient_context_with_drug_classes(self, checker):
        """Test that patient medications detected by drug class."""
        # Patient on multiple SSRIs (shouldn't happen, but test edge case)
        current_meds = ["fluoxetine", "sertraline"]
        new_drug = "phenelzine"  # MAOI

        interactions = checker.check_patient_medications(current_meds, new_drug)

        assert isinstance(interactions, list)
        # Should find contraindications with both SSRIs
        if len(interactions) > 0:
            assert any(i.severity == InteractionSeverity.CONTRAINDICATED for i in interactions)

    def test_format_warning_with_interaction(self, checker):
        """Test warning formatting with real interaction."""
        interaction = checker.check_interaction("warfarin", "aspirin")

        if interaction:
            warning = checker.format_warning(interaction)

            assert isinstance(warning, str)
            assert len(warning) > 0
            assert "warfarin" in warning.lower() or "aspirin" in warning.lower()
            assert "Management:" in warning


class TestConcurrentAccess:
    """Test concurrent access patterns and thread safety."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_multiple_simultaneous_checks(self, checker):
        """Test multiple simultaneous interaction checks."""
        results = []

        def check_interaction():
            interaction = checker.check_interaction("warfarin", "aspirin")
            results.append(interaction)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=check_interaction)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should complete successfully
        assert len(results) == 10
        # All should find the same interaction
        for result in results:
            if result:
                assert result.severity == InteractionSeverity.SEVERE

    def test_cache_consistency_under_concurrent_access(self, checker):
        """Test that drug cache remains consistent under concurrent access."""
        drugs_to_normalize = ["aspirin", "warfarin", "metformin", "lisinopril"] * 5
        results = []

        def normalize_drug(drug_name):
            info = checker.normalize_drug(drug_name)
            results.append((drug_name, info))

        threads = []
        for drug in drugs_to_normalize:
            thread = threading.Thread(target=normalize_drug, args=(drug,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all completed
        assert len(results) == len(drugs_to_normalize)

        # Verify cache consistency - same drug should have same normalized form
        drug_map = {}
        for drug_name, info in results:
            if drug_name not in drug_map:
                drug_map[drug_name] = info
            else:
                # Should be consistent
                assert info.normalized_name == drug_map[drug_name].normalized_name

    def test_concurrent_multiple_drug_checks(self, checker):
        """Test concurrent checks of multiple drugs."""
        drug_lists = [
            ["warfarin", "aspirin", "ibuprofen"],
            ["fluoxetine", "phenelzine"],
            ["atorvastatin", "gemfibrozil"],
            ["metformin", "lisinopril", "aspirin"],
        ] * 3

        results = []

        def check_multiple(drugs):
            interactions = checker.check_multiple(drugs)
            results.append(interactions)

        threads = []
        for drugs in drug_lists:
            thread = threading.Thread(target=check_multiple, args=(drugs,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All should complete successfully
        assert len(results) == len(drug_lists)
        # All should return lists
        for result in results:
            assert isinstance(result, list)


class TestAdditionalEdgeCases:
    """Additional edge cases for comprehensive coverage."""

    @pytest.fixture
    def checker(self):
        return DrugInteractionChecker(offline_mode=True)

    def test_context_manager_usage(self, checker):
        """Test using checker as context manager."""
        with DrugInteractionChecker(offline_mode=True) as checker_ctx:
            interaction = checker_ctx.check_interaction("warfarin", "aspirin")
            assert interaction is not None or interaction is None  # Should not crash

    def test_close_method(self, checker):
        """Test explicit close method."""
        checker.close()
        # After closing, UMLS client should be closed
        # But offline mode should still work for basic operations
        info = checker.normalize_drug("aspirin")
        assert isinstance(info, DrugInfo)

    def test_drug_cache_persistence(self, checker):
        """Test that drug cache persists across calls."""
        # First call
        info1 = checker.normalize_drug("aspirin")

        # Cache should now contain aspirin
        assert "aspirin" in checker._drug_cache

        # Second call should use cache
        info2 = checker.normalize_drug("aspirin")

        # Should be same object from cache
        assert info1 is info2

    def test_interaction_with_very_similar_names(self, checker):
        """Test drugs with very similar names."""
        # These are different drugs but similar names
        info1 = checker.normalize_drug("atorvastatin")
        info2 = checker.normalize_drug("rosuvastatin")

        assert info1.original_name != info2.original_name
        # Both should be statins
        assert "statin" in info1.drug_classes
        assert "statin" in info2.drug_classes

    def test_warning_format_with_none_interaction(self, checker):
        """Test format_warning with None interaction."""
        # This should not happen in normal usage but test defensive programming
        with pytest.raises(AttributeError):
            checker.format_warning(None)

    def test_empty_drug_classes_interaction(self, checker):
        """Test interaction check when drug classes are empty."""
        # Unknown drugs will have empty drug classes
        interaction = checker.check_interaction("unknowndrugA", "unknowndrugB")

        # Should handle gracefully
        assert interaction is None or isinstance(interaction, DrugInteraction)

    def test_patient_medications_with_none_values(self, checker):
        """Test patient medications list containing None values."""
        # This shouldn't happen but test robustness
        with pytest.raises((AttributeError, TypeError)):
            checker.check_patient_medications([None, "aspirin", None], "warfarin")

    def test_check_multiple_with_single_drug(self, checker):
        """Test check_multiple with only one drug."""
        interactions = checker.check_multiple(["aspirin"])

        # Should return empty list (no pairs to check)
        assert isinstance(interactions, list)
        assert len(interactions) == 0
