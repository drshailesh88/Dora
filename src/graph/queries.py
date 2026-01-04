"""Medical knowledge graph queries."""

from dataclasses import dataclass
from typing import Any

from .client import Neo4jClient
from .schema import NodeLabel, RelationType


@dataclass
class GraphResult:
    """Result from a graph query."""

    nodes: list[dict]
    relationships: list[dict]
    paths: list[dict]


class MedicalGraphQueries:
    """
    Query interface for medical knowledge graph.

    Provides medical-domain specific queries for:
    - Disease information and relationships
    - Drug interactions and indications
    - Symptom-based differential diagnosis
    - Treatment recommendations
    """

    def __init__(self, client: Neo4jClient):
        """
        Initialize queries with Neo4j client.

        Args:
            client: Neo4j client instance.
        """
        self.client = client

    # ===================
    # Disease Queries
    # ===================

    def get_disease(self, identifier: str) -> dict | None:
        """
        Get disease by CUI, ICD-10, or name.

        Args:
            identifier: Disease identifier (CUI, ICD-10, or name).

        Returns:
            Disease node data or None.
        """
        query = """
        MATCH (d:Disease)
        WHERE d.cui = $id OR d.icd10 = $id OR toLower(d.name) = toLower($id)
        RETURN d
        LIMIT 1
        """
        results = self.client.execute_query(query, {"id": identifier})
        return results[0]["d"] if results else None

    def get_disease_symptoms(self, disease_identifier: str) -> list[dict]:
        """
        Get symptoms associated with a disease.

        Args:
            disease_identifier: Disease CUI, ICD-10, or name.

        Returns:
            List of symptoms with frequency/specificity.
        """
        query = """
        MATCH (d:Disease)-[r:PRESENTS_WITH]->(s:Symptom)
        WHERE d.cui = $id OR d.icd10 = $id OR toLower(d.name) = toLower($id)
        RETURN s.name AS symptom, s.cui AS cui,
               r.frequency AS frequency, r.specificity AS specificity,
               r.onset AS onset
        ORDER BY r.frequency DESC
        """
        return self.client.execute_query(query, {"id": disease_identifier})

    def get_disease_treatments(self, disease_identifier: str) -> list[dict]:
        """
        Get treatments for a disease.

        Args:
            disease_identifier: Disease identifier.

        Returns:
            List of treatments with evidence level.
        """
        query = """
        MATCH (d:Disease)-[r:TREATED_BY]->(drug:Drug)
        WHERE d.cui = $id OR d.icd10 = $id OR toLower(d.name) = toLower($id)
        OPTIONAL MATCH (drug)-[:BELONGS_TO_CLASS]->(dc:DrugClass)
        RETURN drug.name AS drug, drug.rxcui AS rxcui,
               r.line AS treatment_line, r.evidence_level AS evidence,
               dc.name AS drug_class
        ORDER BY r.line, r.evidence_level DESC
        """
        return self.client.execute_query(query, {"id": disease_identifier})

    def get_differential_diagnosis(self, disease_identifier: str) -> list[dict]:
        """
        Get differential diagnoses for a disease.

        Args:
            disease_identifier: Disease identifier.

        Returns:
            List of differential diagnoses with distinguishing features.
        """
        query = """
        MATCH (d:Disease)-[r:DIFFERENTIAL_OF]-(other:Disease)
        WHERE d.cui = $id OR d.icd10 = $id OR toLower(d.name) = toLower($id)
        RETURN other.name AS disease, other.cui AS cui, other.icd10 AS icd10,
               r.distinguishing_features AS distinguishing_features
        """
        return self.client.execute_query(query, {"id": disease_identifier})

    # ===================
    # Drug Queries
    # ===================

    def get_drug(self, identifier: str) -> dict | None:
        """
        Get drug by RxCUI or name.

        Args:
            identifier: Drug RxCUI or name.

        Returns:
            Drug node data or None.
        """
        query = """
        MATCH (d:Drug)
        WHERE d.rxcui = $id OR toLower(d.name) = toLower($id)
              OR toLower(d.generic_name) = toLower($id)
        RETURN d
        LIMIT 1
        """
        results = self.client.execute_query(query, {"id": identifier})
        return results[0]["d"] if results else None

    def get_drug_interactions(self, drug_identifier: str) -> list[dict]:
        """
        Get interactions for a drug.

        Args:
            drug_identifier: Drug RxCUI or name.

        Returns:
            List of drug interactions with severity.
        """
        query = """
        MATCH (d:Drug)-[r:INTERACTS_WITH]-(other:Drug)
        WHERE d.rxcui = $id OR toLower(d.name) = toLower($id)
        RETURN other.name AS interacting_drug, other.rxcui AS rxcui,
               r.severity AS severity, r.mechanism AS mechanism,
               r.clinical_effect AS effect
        ORDER BY r.severity DESC
        """
        return self.client.execute_query(query, {"id": drug_identifier})

    def check_drug_interaction(self, drug1: str, drug2: str) -> dict | None:
        """
        Check if two drugs interact.

        Args:
            drug1: First drug identifier.
            drug2: Second drug identifier.

        Returns:
            Interaction details or None.
        """
        query = """
        MATCH (d1:Drug)-[r:INTERACTS_WITH]-(d2:Drug)
        WHERE (d1.rxcui = $drug1 OR toLower(d1.name) = toLower($drug1))
          AND (d2.rxcui = $drug2 OR toLower(d2.name) = toLower($drug2))
        RETURN d1.name AS drug1, d2.name AS drug2,
               r.severity AS severity, r.mechanism AS mechanism,
               r.clinical_effect AS effect
        LIMIT 1
        """
        results = self.client.execute_query(
            query, {"drug1": drug1, "drug2": drug2}
        )
        return results[0] if results else None

    def get_drug_indications(self, drug_identifier: str) -> list[dict]:
        """
        Get indications for a drug.

        Args:
            drug_identifier: Drug identifier.

        Returns:
            List of indicated diseases.
        """
        query = """
        MATCH (d:Drug)-[r:INDICATED_FOR]->(disease:Disease)
        WHERE d.rxcui = $id OR toLower(d.name) = toLower($id)
        RETURN disease.name AS indication, disease.cui AS cui,
               r.fda_approved AS fda_approved, r.evidence AS evidence
        ORDER BY r.fda_approved DESC, r.evidence DESC
        """
        return self.client.execute_query(query, {"id": drug_identifier})

    def get_drug_contraindications(self, drug_identifier: str) -> list[dict]:
        """
        Get contraindications for a drug.

        Args:
            drug_identifier: Drug identifier.

        Returns:
            List of contraindicated conditions.
        """
        query = """
        MATCH (d:Drug)-[r:CONTRAINDICATED_IN]->(disease:Disease)
        WHERE d.rxcui = $id OR toLower(d.name) = toLower($id)
        RETURN disease.name AS condition, disease.cui AS cui,
               r.reason AS reason, r.severity AS severity
        ORDER BY r.severity DESC
        """
        return self.client.execute_query(query, {"id": drug_identifier})

    # ===================
    # Symptom Queries
    # ===================

    def symptoms_to_diseases(self, symptoms: list[str]) -> list[dict]:
        """
        Find diseases matching a set of symptoms.

        Args:
            symptoms: List of symptom names.

        Returns:
            Ranked list of diseases with match scores.
        """
        query = """
        UNWIND $symptoms AS symptom_name
        MATCH (s:Symptom)<-[r:PRESENTS_WITH]-(d:Disease)
        WHERE toLower(s.name) CONTAINS toLower(symptom_name)
        WITH d, COUNT(DISTINCT s) AS match_count,
             COLLECT(DISTINCT s.name) AS matched_symptoms,
             AVG(r.frequency) AS avg_frequency
        RETURN d.name AS disease, d.cui AS cui, d.icd10 AS icd10,
               match_count, matched_symptoms, avg_frequency
        ORDER BY match_count DESC, avg_frequency DESC
        LIMIT 20
        """
        return self.client.execute_query(query, {"symptoms": symptoms})

    # ===================
    # Graph Traversal
    # ===================

    def find_path(
        self,
        from_node: str,
        from_label: NodeLabel,
        to_node: str,
        to_label: NodeLabel,
        max_hops: int = 3,
    ) -> list[dict]:
        """
        Find paths between two nodes.

        Args:
            from_node: Starting node identifier.
            from_label: Starting node label.
            to_node: Target node identifier.
            to_label: Target node label.
            max_hops: Maximum path length.

        Returns:
            List of paths with nodes and relationships.
        """
        query = f"""
        MATCH path = shortestPath(
            (from:{from_label.value})-[*1..{max_hops}]-(to:{to_label.value})
        )
        WHERE (from.name = $from_id OR from.cui = $from_id OR from.rxcui = $from_id)
          AND (to.name = $to_id OR to.cui = $to_id OR to.rxcui = $to_id)
        RETURN [n in nodes(path) | n.name] AS node_names,
               [r in relationships(path) | type(r)] AS relationship_types,
               length(path) AS path_length
        LIMIT 5
        """
        return self.client.execute_query(
            query, {"from_id": from_node, "to_id": to_node}
        )

    def get_neighborhood(
        self,
        node_identifier: str,
        node_label: NodeLabel,
        depth: int = 1,
    ) -> GraphResult:
        """
        Get the neighborhood around a node.

        Args:
            node_identifier: Node identifier.
            node_label: Node type.
            depth: Number of hops.

        Returns:
            GraphResult with nodes and relationships.
        """
        query = f"""
        MATCH (center:{node_label.value})
        WHERE center.name = $id OR center.cui = $id OR center.rxcui = $id
        CALL apoc.path.subgraphAll(center, {{
            maxLevel: {depth},
            limit: 100
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        # Fallback if APOC not available
        fallback_query = f"""
        MATCH (center:{node_label.value})-[r*1..{depth}]-(neighbor)
        WHERE center.name = $id OR center.cui = $id OR center.rxcui = $id
        RETURN DISTINCT neighbor, labels(neighbor)[0] AS label, type(r[-1]) AS rel_type
        LIMIT 50
        """

        try:
            results = self.client.execute_query(query, {"id": node_identifier})
            if results:
                return GraphResult(
                    nodes=results[0].get("nodes", []),
                    relationships=results[0].get("relationships", []),
                    paths=[],
                )
        except Exception:
            pass

        # Use fallback
        results = self.client.execute_query(fallback_query, {"id": node_identifier})
        return GraphResult(
            nodes=[r["neighbor"] for r in results],
            relationships=[{"type": r["rel_type"]} for r in results],
            paths=[],
        )

    # ===================
    # Guideline Queries
    # ===================

    def get_treatment_guidelines(self, disease_identifier: str) -> list[dict]:
        """
        Get treatment guidelines for a disease.

        Args:
            disease_identifier: Disease identifier.

        Returns:
            List of guidelines with recommendations.
        """
        query = """
        MATCH (d:Disease)<-[:INDICATED_FOR]-(drug:Drug)<-[r:RECOMMENDS]-(g:Guideline)
        WHERE d.cui = $id OR d.icd10 = $id OR toLower(d.name) = toLower($id)
        RETURN g.title AS guideline, g.source AS source, g.year AS year,
               drug.name AS recommended_drug, r.grade AS grade, r.context AS context
        ORDER BY g.year DESC, r.grade
        """
        return self.client.execute_query(query, {"id": disease_identifier})

    # ===================
    # Statistics
    # ===================

    def get_stats(self) -> dict:
        """Get graph statistics."""
        query = """
        CALL apoc.meta.stats() YIELD nodeCount, relCount, labels, relTypes
        RETURN nodeCount, relCount, labels, relTypes
        """

        try:
            results = self.client.execute_query(query)
            if results:
                return results[0]
        except Exception:
            pass

        # Fallback without APOC
        fallback = """
        MATCH (n) WITH count(n) as nodeCount
        MATCH ()-[r]->() WITH nodeCount, count(r) as relCount
        RETURN nodeCount, relCount
        """
        results = self.client.execute_query(fallback)
        return results[0] if results else {"nodeCount": 0, "relCount": 0}
