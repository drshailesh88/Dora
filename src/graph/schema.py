"""Medical knowledge graph schema definition."""

from dataclasses import dataclass
from enum import Enum


class NodeLabel(str, Enum):
    """Node types in the medical knowledge graph."""

    # Clinical entities
    DISEASE = "Disease"
    SYMPTOM = "Symptom"
    DRUG = "Drug"
    PROCEDURE = "Procedure"
    ANATOMY = "Anatomy"
    LAB_TEST = "LabTest"
    FINDING = "Finding"

    # Medical concepts
    DRUG_CLASS = "DrugClass"
    DISEASE_CATEGORY = "DiseaseCategory"
    SPECIALTY = "Specialty"

    # Knowledge sources
    GUIDELINE = "Guideline"
    ARTICLE = "Article"
    TEXTBOOK = "Textbook"


class RelationType(str, Enum):
    """Relationship types in the medical knowledge graph."""

    # Disease relationships
    CAUSES = "CAUSES"
    PRESENTS_WITH = "PRESENTS_WITH"
    TREATED_BY = "TREATED_BY"
    DIAGNOSED_BY = "DIAGNOSED_BY"
    DIFFERENTIAL_OF = "DIFFERENTIAL_OF"
    COMPLICATION_OF = "COMPLICATION_OF"
    RISK_FACTOR_FOR = "RISK_FACTOR_FOR"

    # Drug relationships
    INTERACTS_WITH = "INTERACTS_WITH"
    CONTRAINDICATED_IN = "CONTRAINDICATED_IN"
    INDICATED_FOR = "INDICATED_FOR"
    BELONGS_TO_CLASS = "BELONGS_TO_CLASS"
    METABOLIZED_BY = "METABOLIZED_BY"

    # Anatomical relationships
    LOCATED_IN = "LOCATED_IN"
    AFFECTS = "AFFECTS"
    PART_OF = "PART_OF"

    # Knowledge relationships
    REFERENCES = "REFERENCES"
    RECOMMENDS = "RECOMMENDS"
    SUPPORTS = "SUPPORTS"

    # Hierarchical
    SUBCLASS_OF = "SUBCLASS_OF"
    INSTANCE_OF = "INSTANCE_OF"


@dataclass
class NodeSchema:
    """Schema definition for a node type."""

    label: NodeLabel
    properties: list[str]
    required: list[str]
    indexes: list[str]


@dataclass
class RelationSchema:
    """Schema definition for a relationship type."""

    relation_type: RelationType
    from_label: NodeLabel
    to_label: NodeLabel
    properties: list[str]


class MedicalGraphSchema:
    """
    Schema manager for the medical knowledge graph.

    Defines node types, relationships, and constraints
    based on medical ontology standards (UMLS, SNOMED-CT).
    """

    # Node schemas
    NODES: dict[NodeLabel, NodeSchema] = {
        NodeLabel.DISEASE: NodeSchema(
            label=NodeLabel.DISEASE,
            properties=["cui", "name", "icd10", "snomed_id", "description", "synonyms"],
            required=["cui", "name"],
            indexes=["cui", "name", "icd10"],
        ),
        NodeLabel.SYMPTOM: NodeSchema(
            label=NodeLabel.SYMPTOM,
            properties=["cui", "name", "description", "body_location", "severity_range"],
            required=["cui", "name"],
            indexes=["cui", "name"],
        ),
        NodeLabel.DRUG: NodeSchema(
            label=NodeLabel.DRUG,
            properties=[
                "rxcui", "name", "generic_name", "brand_names",
                "drug_class", "mechanism", "dosage_forms",
            ],
            required=["rxcui", "name"],
            indexes=["rxcui", "name", "generic_name"],
        ),
        NodeLabel.PROCEDURE: NodeSchema(
            label=NodeLabel.PROCEDURE,
            properties=["cpt_code", "name", "description", "specialty", "invasiveness"],
            required=["name"],
            indexes=["cpt_code", "name"],
        ),
        NodeLabel.ANATOMY: NodeSchema(
            label=NodeLabel.ANATOMY,
            properties=["fma_id", "name", "system", "laterality"],
            required=["name"],
            indexes=["fma_id", "name"],
        ),
        NodeLabel.LAB_TEST: NodeSchema(
            label=NodeLabel.LAB_TEST,
            properties=["loinc", "name", "unit", "normal_range", "specimen"],
            required=["name"],
            indexes=["loinc", "name"],
        ),
        NodeLabel.DRUG_CLASS: NodeSchema(
            label=NodeLabel.DRUG_CLASS,
            properties=["atc_code", "name", "mechanism", "examples"],
            required=["name"],
            indexes=["atc_code", "name"],
        ),
        NodeLabel.GUIDELINE: NodeSchema(
            label=NodeLabel.GUIDELINE,
            properties=["source", "title", "year", "grade", "url"],
            required=["source", "title"],
            indexes=["source", "title"],
        ),
    }

    # Relationship schemas
    RELATIONSHIPS: list[RelationSchema] = [
        # Disease -> Symptom
        RelationSchema(
            relation_type=RelationType.PRESENTS_WITH,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.SYMPTOM,
            properties=["frequency", "specificity", "onset"],
        ),
        # Disease -> Drug (treatment)
        RelationSchema(
            relation_type=RelationType.TREATED_BY,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.DRUG,
            properties=["line", "evidence_level", "efficacy"],
        ),
        # Drug -> Drug (interaction)
        RelationSchema(
            relation_type=RelationType.INTERACTS_WITH,
            from_label=NodeLabel.DRUG,
            to_label=NodeLabel.DRUG,
            properties=["severity", "mechanism", "clinical_effect"],
        ),
        # Drug -> Disease (contraindication)
        RelationSchema(
            relation_type=RelationType.CONTRAINDICATED_IN,
            from_label=NodeLabel.DRUG,
            to_label=NodeLabel.DISEASE,
            properties=["reason", "severity"],
        ),
        # Drug -> Disease (indication)
        RelationSchema(
            relation_type=RelationType.INDICATED_FOR,
            from_label=NodeLabel.DRUG,
            to_label=NodeLabel.DISEASE,
            properties=["fda_approved", "off_label", "evidence"],
        ),
        # Drug -> DrugClass
        RelationSchema(
            relation_type=RelationType.BELONGS_TO_CLASS,
            from_label=NodeLabel.DRUG,
            to_label=NodeLabel.DRUG_CLASS,
            properties=[],
        ),
        # Disease -> LabTest (diagnosis)
        RelationSchema(
            relation_type=RelationType.DIAGNOSED_BY,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.LAB_TEST,
            properties=["sensitivity", "specificity", "finding"],
        ),
        # Disease -> Disease (differential)
        RelationSchema(
            relation_type=RelationType.DIFFERENTIAL_OF,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.DISEASE,
            properties=["distinguishing_features"],
        ),
        # Disease -> Disease (complication)
        RelationSchema(
            relation_type=RelationType.COMPLICATION_OF,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.DISEASE,
            properties=["frequency", "time_frame"],
        ),
        # Disease -> Anatomy
        RelationSchema(
            relation_type=RelationType.AFFECTS,
            from_label=NodeLabel.DISEASE,
            to_label=NodeLabel.ANATOMY,
            properties=["pathology"],
        ),
        # Symptom -> Anatomy
        RelationSchema(
            relation_type=RelationType.LOCATED_IN,
            from_label=NodeLabel.SYMPTOM,
            to_label=NodeLabel.ANATOMY,
            properties=[],
        ),
        # Guideline relationships
        RelationSchema(
            relation_type=RelationType.RECOMMENDS,
            from_label=NodeLabel.GUIDELINE,
            to_label=NodeLabel.DRUG,
            properties=["grade", "context"],
        ),
    ]

    @classmethod
    def create_constraints_query(cls) -> str:
        """Generate Cypher to create constraints."""
        queries = []

        for node_schema in cls.NODES.values():
            # Unique constraint on primary identifier
            if node_schema.indexes:
                primary_idx = node_schema.indexes[0]
                queries.append(
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_schema.label.value}) "
                    f"REQUIRE n.{primary_idx} IS UNIQUE"
                )

        return ";\n".join(queries) + ";"

    @classmethod
    def create_indexes_query(cls) -> str:
        """Generate Cypher to create indexes."""
        queries = []

        for node_schema in cls.NODES.values():
            for idx_prop in node_schema.indexes[1:]:  # Skip first (constraint)
                queries.append(
                    f"CREATE INDEX IF NOT EXISTS FOR (n:{node_schema.label.value}) "
                    f"ON (n.{idx_prop})"
                )

        return ";\n".join(queries) + ";" if queries else ""
