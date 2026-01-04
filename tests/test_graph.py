"""Tests for knowledge graph module."""

import pytest
from unittest.mock import MagicMock, patch

from src.graph.schema import NodeLabel, RelationType, MedicalGraphSchema
from src.graph.queries import MedicalGraphQueries


class TestGraphSchema:
    """Test knowledge graph schema."""

    def test_node_labels_defined(self):
        """Test all expected node labels exist."""
        expected = ["Disease", "Symptom", "Drug", "Procedure", "DrugClass"]

        for label in expected:
            assert hasattr(NodeLabel, label.upper())

    def test_relationship_types_defined(self):
        """Test all expected relationship types exist."""
        expected = [
            "CAUSES", "PRESENTS_WITH", "TREATED_BY", "INTERACTS_WITH",
            "CONTRAINDICATED_IN", "INDICATED_FOR"
        ]

        for rel in expected:
            assert hasattr(RelationType, rel)

    def test_node_schema_properties(self):
        """Test node schemas have required properties."""
        disease_schema = MedicalGraphSchema.NODES.get(NodeLabel.DISEASE)

        assert disease_schema is not None
        assert "cui" in disease_schema.properties
        assert "name" in disease_schema.properties
        assert "cui" in disease_schema.required

    def test_create_constraints_query(self):
        """Test constraint query generation."""
        query = MedicalGraphSchema.create_constraints_query()

        assert "CREATE CONSTRAINT" in query
        assert "Disease" in query

    def test_create_indexes_query(self):
        """Test index query generation."""
        query = MedicalGraphSchema.create_indexes_query()

        # May be empty if no additional indexes needed
        assert isinstance(query, str)


class TestGraphQueries:
    """Test knowledge graph queries."""

    @pytest.fixture
    def mock_client(self):
        """Mock Neo4j client."""
        mock = MagicMock()
        mock.execute_query = MagicMock(return_value=[])
        return mock

    @pytest.fixture
    def queries(self, mock_client):
        """Create queries instance with mock client."""
        return MedicalGraphQueries(mock_client)

    def test_get_disease_calls_correct_query(self, queries, mock_client):
        """Test disease lookup query structure."""
        mock_client.execute_query.return_value = [
            {"d": {"cui": "C0011849", "name": "Diabetes Mellitus Type 2"}}
        ]

        result = queries.get_disease("C0011849")

        assert result is not None
        assert result["cui"] == "C0011849"
        mock_client.execute_query.assert_called_once()

    def test_get_disease_not_found(self, queries, mock_client):
        """Test disease lookup when not found."""
        mock_client.execute_query.return_value = []

        result = queries.get_disease("nonexistent")

        assert result is None

    def test_get_disease_symptoms(self, queries, mock_client):
        """Test getting symptoms for a disease."""
        mock_client.execute_query.return_value = [
            {"symptom": "Polyuria", "frequency": "common"},
            {"symptom": "Polydipsia", "frequency": "common"},
        ]

        symptoms = queries.get_disease_symptoms("C0011849")

        assert len(symptoms) == 2
        assert symptoms[0]["symptom"] == "Polyuria"

    def test_get_disease_treatments(self, queries, mock_client):
        """Test getting treatments for a disease."""
        mock_client.execute_query.return_value = [
            {"drug": "Metformin", "treatment_line": 1, "evidence": "high"},
        ]

        treatments = queries.get_disease_treatments("C0011849")

        assert len(treatments) == 1
        assert treatments[0]["drug"] == "Metformin"

    def test_get_drug_interactions(self, queries, mock_client):
        """Test getting drug interactions."""
        mock_client.execute_query.return_value = [
            {
                "interacting_drug": "Aspirin",
                "severity": "severe",
                "effect": "Increased bleeding risk",
            }
        ]

        interactions = queries.get_drug_interactions("11289")  # Warfarin

        assert len(interactions) == 1
        assert interactions[0]["severity"] == "severe"

    def test_check_drug_interaction(self, queries, mock_client):
        """Test checking specific drug pair interaction."""
        mock_client.execute_query.return_value = [
            {
                "drug1": "Warfarin",
                "drug2": "Aspirin",
                "severity": "severe",
            }
        ]

        interaction = queries.check_drug_interaction("warfarin", "aspirin")

        assert interaction is not None
        assert interaction["severity"] == "severe"

    def test_symptoms_to_diseases(self, queries, mock_client):
        """Test symptom-based disease lookup."""
        mock_client.execute_query.return_value = [
            {
                "disease": "Diabetes Mellitus Type 2",
                "match_count": 2,
                "matched_symptoms": ["Polyuria", "Polydipsia"],
            }
        ]

        diseases = queries.symptoms_to_diseases(["polyuria", "polydipsia"])

        assert len(diseases) >= 1
        assert diseases[0]["match_count"] == 2

    def test_get_stats(self, queries, mock_client):
        """Test getting graph statistics."""
        mock_client.execute_query.return_value = [
            {"nodeCount": 1000, "relCount": 5000}
        ]

        stats = queries.get_stats()

        assert stats["nodeCount"] == 1000
        assert stats["relCount"] == 5000


class TestGraphBuilder:
    """Test knowledge graph builder."""

    @pytest.fixture
    def mock_client(self):
        mock = MagicMock()
        mock.execute_query = MagicMock(return_value=[{"d": {}}])
        mock.execute_write = MagicMock()
        return mock

    def test_create_disease(self, mock_client):
        """Test creating a disease node."""
        from src.graph.builder import KnowledgeGraphBuilder

        builder = KnowledgeGraphBuilder(mock_client)
        result = builder.create_disease(
            cui="C0011849",
            name="Diabetes Mellitus Type 2",
            icd10="E11",
        )

        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        assert "MERGE" in call_args[0][0]

    def test_create_drug(self, mock_client):
        """Test creating a drug node."""
        from src.graph.builder import KnowledgeGraphBuilder

        builder = KnowledgeGraphBuilder(mock_client)
        result = builder.create_drug(
            rxcui="6809",
            name="Metformin",
            generic_name="metformin",
        )

        mock_client.execute_query.assert_called_once()

    def test_create_drug_interaction(self, mock_client):
        """Test creating drug interaction relationship."""
        from src.graph.builder import KnowledgeGraphBuilder

        builder = KnowledgeGraphBuilder(mock_client)
        builder.create_drug_interaction(
            drug1_rxcui="11289",
            drug2_rxcui="1191",
            severity="severe",
            mechanism="Additive anticoagulant effect",
        )

        mock_client.execute_query.assert_called_once()
        call_args = mock_client.execute_query.call_args
        assert "INTERACTS_WITH" in call_args[0][0]
