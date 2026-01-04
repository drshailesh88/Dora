"""Knowledge graph builder for medical ontologies."""

import json
from pathlib import Path
from typing import Iterator

from .client import Neo4jClient
from .schema import MedicalGraphSchema, NodeLabel, RelationType


class KnowledgeGraphBuilder:
    """
    Build medical knowledge graph from various sources.

    Supports importing from:
    - UMLS (Unified Medical Language System)
    - RxNorm (drug database)
    - ICD-10 (disease classification)
    - Custom JSON/CSV files
    """

    def __init__(self, client: Neo4jClient):
        """
        Initialize builder with Neo4j client.

        Args:
            client: Neo4j client instance.
        """
        self.client = client

    def setup_schema(self):
        """Create constraints and indexes."""
        # Create constraints
        constraints = MedicalGraphSchema.create_constraints_query()
        for statement in constraints.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    self.client.execute_write(statement)
                except Exception as e:
                    print(f"Constraint warning: {e}")

        # Create indexes
        indexes = MedicalGraphSchema.create_indexes_query()
        for statement in indexes.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    self.client.execute_write(statement)
                except Exception as e:
                    print(f"Index warning: {e}")

    def clear_graph(self):
        """Clear all nodes and relationships (use with caution!)."""
        self.client.execute_write("MATCH (n) DETACH DELETE n")

    # ===================
    # Node Creation
    # ===================

    def create_disease(
        self,
        cui: str,
        name: str,
        icd10: str | None = None,
        snomed_id: str | None = None,
        description: str | None = None,
        synonyms: list[str] | None = None,
    ) -> dict:
        """Create a disease node."""
        query = """
        MERGE (d:Disease {cui: $cui})
        SET d.name = $name,
            d.icd10 = $icd10,
            d.snomed_id = $snomed_id,
            d.description = $description,
            d.synonyms = $synonyms
        RETURN d
        """
        results = self.client.execute_query(
            query,
            {
                "cui": cui,
                "name": name,
                "icd10": icd10,
                "snomed_id": snomed_id,
                "description": description,
                "synonyms": synonyms or [],
            },
        )
        return results[0]["d"] if results else {}

    def create_symptom(
        self,
        cui: str,
        name: str,
        description: str | None = None,
        body_location: str | None = None,
    ) -> dict:
        """Create a symptom node."""
        query = """
        MERGE (s:Symptom {cui: $cui})
        SET s.name = $name,
            s.description = $description,
            s.body_location = $body_location
        RETURN s
        """
        results = self.client.execute_query(
            query,
            {
                "cui": cui,
                "name": name,
                "description": description,
                "body_location": body_location,
            },
        )
        return results[0]["s"] if results else {}

    def create_drug(
        self,
        rxcui: str,
        name: str,
        generic_name: str | None = None,
        brand_names: list[str] | None = None,
        drug_class: str | None = None,
        mechanism: str | None = None,
    ) -> dict:
        """Create a drug node."""
        query = """
        MERGE (d:Drug {rxcui: $rxcui})
        SET d.name = $name,
            d.generic_name = $generic_name,
            d.brand_names = $brand_names,
            d.drug_class = $drug_class,
            d.mechanism = $mechanism
        RETURN d
        """
        results = self.client.execute_query(
            query,
            {
                "rxcui": rxcui,
                "name": name,
                "generic_name": generic_name,
                "brand_names": brand_names or [],
                "drug_class": drug_class,
                "mechanism": mechanism,
            },
        )
        return results[0]["d"] if results else {}

    def create_drug_class(
        self,
        atc_code: str,
        name: str,
        mechanism: str | None = None,
    ) -> dict:
        """Create a drug class node."""
        query = """
        MERGE (dc:DrugClass {atc_code: $atc_code})
        SET dc.name = $name,
            dc.mechanism = $mechanism
        RETURN dc
        """
        results = self.client.execute_query(
            query,
            {
                "atc_code": atc_code,
                "name": name,
                "mechanism": mechanism,
            },
        )
        return results[0]["dc"] if results else {}

    # ===================
    # Relationship Creation
    # ===================

    def create_disease_symptom_relation(
        self,
        disease_cui: str,
        symptom_cui: str,
        frequency: str | None = None,
        specificity: str | None = None,
    ):
        """Create PRESENTS_WITH relationship."""
        query = """
        MATCH (d:Disease {cui: $disease_cui})
        MATCH (s:Symptom {cui: $symptom_cui})
        MERGE (d)-[r:PRESENTS_WITH]->(s)
        SET r.frequency = $frequency,
            r.specificity = $specificity
        RETURN r
        """
        self.client.execute_query(
            query,
            {
                "disease_cui": disease_cui,
                "symptom_cui": symptom_cui,
                "frequency": frequency,
                "specificity": specificity,
            },
        )

    def create_treatment_relation(
        self,
        disease_cui: str,
        drug_rxcui: str,
        line: int = 1,
        evidence_level: str = "moderate",
    ):
        """Create TREATED_BY relationship."""
        query = """
        MATCH (d:Disease {cui: $disease_cui})
        MATCH (drug:Drug {rxcui: $drug_rxcui})
        MERGE (d)-[r:TREATED_BY]->(drug)
        SET r.line = $line,
            r.evidence_level = $evidence_level
        RETURN r
        """
        self.client.execute_query(
            query,
            {
                "disease_cui": disease_cui,
                "drug_rxcui": drug_rxcui,
                "line": line,
                "evidence_level": evidence_level,
            },
        )

    def create_drug_interaction(
        self,
        drug1_rxcui: str,
        drug2_rxcui: str,
        severity: str,
        mechanism: str | None = None,
        clinical_effect: str | None = None,
    ):
        """Create INTERACTS_WITH relationship."""
        query = """
        MATCH (d1:Drug {rxcui: $drug1})
        MATCH (d2:Drug {rxcui: $drug2})
        MERGE (d1)-[r:INTERACTS_WITH]-(d2)
        SET r.severity = $severity,
            r.mechanism = $mechanism,
            r.clinical_effect = $clinical_effect
        RETURN r
        """
        self.client.execute_query(
            query,
            {
                "drug1": drug1_rxcui,
                "drug2": drug2_rxcui,
                "severity": severity,
                "mechanism": mechanism,
                "clinical_effect": clinical_effect,
            },
        )

    def create_drug_class_relation(self, drug_rxcui: str, class_atc: str):
        """Create BELONGS_TO_CLASS relationship."""
        query = """
        MATCH (d:Drug {rxcui: $drug})
        MATCH (dc:DrugClass {atc_code: $class})
        MERGE (d)-[:BELONGS_TO_CLASS]->(dc)
        """
        self.client.execute_query(query, {"drug": drug_rxcui, "class": class_atc})

    def create_indication(
        self,
        drug_rxcui: str,
        disease_cui: str,
        fda_approved: bool = False,
        evidence: str | None = None,
    ):
        """Create INDICATED_FOR relationship."""
        query = """
        MATCH (d:Drug {rxcui: $drug})
        MATCH (disease:Disease {cui: $disease})
        MERGE (d)-[r:INDICATED_FOR]->(disease)
        SET r.fda_approved = $fda,
            r.evidence = $evidence
        RETURN r
        """
        self.client.execute_query(
            query,
            {
                "drug": drug_rxcui,
                "disease": disease_cui,
                "fda": fda_approved,
                "evidence": evidence,
            },
        )

    def create_contraindication(
        self,
        drug_rxcui: str,
        disease_cui: str,
        reason: str | None = None,
        severity: str = "moderate",
    ):
        """Create CONTRAINDICATED_IN relationship."""
        query = """
        MATCH (d:Drug {rxcui: $drug})
        MATCH (disease:Disease {cui: $disease})
        MERGE (d)-[r:CONTRAINDICATED_IN]->(disease)
        SET r.reason = $reason,
            r.severity = $severity
        RETURN r
        """
        self.client.execute_query(
            query,
            {
                "drug": drug_rxcui,
                "disease": disease_cui,
                "reason": reason,
                "severity": severity,
            },
        )

    # ===================
    # Bulk Import
    # ===================

    def import_from_json(self, file_path: Path, node_type: NodeLabel):
        """
        Import nodes from JSON file.

        Expected format: [{"cui": "...", "name": "...", ...}, ...]
        """
        with open(file_path) as f:
            data = json.load(f)

        for item in data:
            if node_type == NodeLabel.DISEASE:
                self.create_disease(**item)
            elif node_type == NodeLabel.SYMPTOM:
                self.create_symptom(**item)
            elif node_type == NodeLabel.DRUG:
                self.create_drug(**item)
            elif node_type == NodeLabel.DRUG_CLASS:
                self.create_drug_class(**item)

    def import_relationships_from_json(
        self,
        file_path: Path,
        relation_type: RelationType,
    ):
        """
        Import relationships from JSON file.

        Expected format varies by relation type.
        """
        with open(file_path) as f:
            data = json.load(f)

        for item in data:
            if relation_type == RelationType.PRESENTS_WITH:
                self.create_disease_symptom_relation(
                    disease_cui=item["disease_cui"],
                    symptom_cui=item["symptom_cui"],
                    frequency=item.get("frequency"),
                    specificity=item.get("specificity"),
                )
            elif relation_type == RelationType.TREATED_BY:
                self.create_treatment_relation(
                    disease_cui=item["disease_cui"],
                    drug_rxcui=item["drug_rxcui"],
                    line=item.get("line", 1),
                    evidence_level=item.get("evidence_level", "moderate"),
                )
            elif relation_type == RelationType.INTERACTS_WITH:
                self.create_drug_interaction(
                    drug1_rxcui=item["drug1_rxcui"],
                    drug2_rxcui=item["drug2_rxcui"],
                    severity=item["severity"],
                    mechanism=item.get("mechanism"),
                    clinical_effect=item.get("clinical_effect"),
                )

    # ===================
    # Sample Data
    # ===================

    def create_sample_data(self):
        """Create sample medical knowledge graph data for testing."""

        # Sample diseases
        diseases = [
            {"cui": "C0011849", "name": "Diabetes Mellitus Type 2", "icd10": "E11"},
            {"cui": "C0020538", "name": "Hypertension", "icd10": "I10"},
            {"cui": "C0010068", "name": "Coronary Artery Disease", "icd10": "I25.1"},
            {"cui": "C0004096", "name": "Asthma", "icd10": "J45"},
            {"cui": "C0018802", "name": "Heart Failure", "icd10": "I50"},
        ]

        # Sample symptoms
        symptoms = [
            {"cui": "S001", "name": "Chest Pain", "body_location": "chest"},
            {"cui": "S002", "name": "Dyspnea", "body_location": "respiratory"},
            {"cui": "S003", "name": "Polyuria", "body_location": "urinary"},
            {"cui": "S004", "name": "Polydipsia", "body_location": "general"},
            {"cui": "S005", "name": "Headache", "body_location": "head"},
            {"cui": "S006", "name": "Wheezing", "body_location": "respiratory"},
        ]

        # Sample drugs
        drugs = [
            {"rxcui": "6809", "name": "Metformin", "generic_name": "metformin", "drug_class": "Biguanide"},
            {"rxcui": "1008842", "name": "Lisinopril", "generic_name": "lisinopril", "drug_class": "ACE Inhibitor"},
            {"rxcui": "83367", "name": "Atorvastatin", "generic_name": "atorvastatin", "drug_class": "Statin"},
            {"rxcui": "11289", "name": "Warfarin", "generic_name": "warfarin", "drug_class": "Anticoagulant"},
            {"rxcui": "1191", "name": "Aspirin", "generic_name": "aspirin", "drug_class": "NSAID"},
            {"rxcui": "2284", "name": "Albuterol", "generic_name": "albuterol", "drug_class": "Beta-2 Agonist"},
        ]

        # Drug classes
        drug_classes = [
            {"atc_code": "A10BA", "name": "Biguanides", "mechanism": "Decrease hepatic glucose production"},
            {"atc_code": "C09AA", "name": "ACE Inhibitors", "mechanism": "Block ACE enzyme"},
            {"atc_code": "C10AA", "name": "Statins", "mechanism": "Inhibit HMG-CoA reductase"},
            {"atc_code": "B01AA", "name": "Vitamin K Antagonists", "mechanism": "Inhibit vitamin K"},
            {"atc_code": "R03AC", "name": "Beta-2 Agonists", "mechanism": "Bronchodilation"},
        ]

        # Create nodes
        for d in diseases:
            self.create_disease(**d)

        for s in symptoms:
            self.create_symptom(**s)

        for d in drugs:
            self.create_drug(**d)

        for dc in drug_classes:
            self.create_drug_class(**dc)

        # Create relationships

        # Disease-Symptom
        self.create_disease_symptom_relation("C0011849", "S003", "common", "moderate")
        self.create_disease_symptom_relation("C0011849", "S004", "common", "moderate")
        self.create_disease_symptom_relation("C0020538", "S005", "common", "low")
        self.create_disease_symptom_relation("C0010068", "S001", "very common", "moderate")
        self.create_disease_symptom_relation("C0018802", "S002", "very common", "high")
        self.create_disease_symptom_relation("C0004096", "S006", "very common", "high")
        self.create_disease_symptom_relation("C0004096", "S002", "common", "moderate")

        # Disease-Drug (treatments)
        self.create_treatment_relation("C0011849", "6809", line=1, evidence_level="high")
        self.create_treatment_relation("C0020538", "1008842", line=1, evidence_level="high")
        self.create_treatment_relation("C0010068", "83367", line=1, evidence_level="high")
        self.create_treatment_relation("C0010068", "1191", line=2, evidence_level="high")
        self.create_treatment_relation("C0004096", "2284", line=1, evidence_level="high")

        # Drug interactions
        self.create_drug_interaction(
            "11289", "1191",
            severity="severe",
            mechanism="Additive anticoagulant effect",
            clinical_effect="Increased bleeding risk",
        )

        # Drug indications
        self.create_indication("6809", "C0011849", fda_approved=True, evidence="high")
        self.create_indication("1008842", "C0020538", fda_approved=True, evidence="high")
        self.create_indication("1008842", "C0018802", fda_approved=True, evidence="high")

        print("Sample data created successfully!")
