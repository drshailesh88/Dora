"""Graph-enhanced retrieval combining vector search with knowledge graph."""

from dataclasses import dataclass
from typing import Any

from src.core.models import RetrievedChunk
from src.retrieval import HybridRetriever
from .client import Neo4jClient
from .queries import MedicalGraphQueries


@dataclass
class GraphContext:
    """Additional context from knowledge graph."""

    related_diseases: list[dict]
    related_drugs: list[dict]
    symptoms: list[dict]
    treatments: list[dict]
    interactions: list[dict]
    differentials: list[dict]


class GraphEnhancedRetriever:
    """
    Combine vector retrieval with knowledge graph traversal.

    Enhances RAG retrieval by:
    1. Extracting medical entities from query
    2. Traversing knowledge graph for related concepts
    3. Augmenting retrieval with graph context
    4. Providing structured medical relationships
    """

    def __init__(
        self,
        vector_retriever: HybridRetriever | None = None,
        neo4j_client: Neo4jClient | None = None,
    ):
        """
        Initialize graph-enhanced retriever.

        Args:
            vector_retriever: Hybrid vector retriever.
            neo4j_client: Neo4j client for graph queries.
        """
        self.vector_retriever = vector_retriever or HybridRetriever()
        self.neo4j_client = neo4j_client

        self.graph_queries: MedicalGraphQueries | None = None
        if self.neo4j_client:
            self.graph_queries = MedicalGraphQueries(self.neo4j_client)

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        use_graph: bool = True,
    ) -> tuple[list[RetrievedChunk], GraphContext | None]:
        """
        Retrieve relevant content with graph enhancement.

        Args:
            query: User query.
            top_k: Number of results.
            use_graph: Whether to include graph context.

        Returns:
            Tuple of (retrieved chunks, graph context).
        """
        # Vector retrieval
        chunks = self.vector_retriever.retrieve(query, top_k=top_k)

        # Graph enhancement
        graph_context = None
        if use_graph and self.graph_queries:
            graph_context = self._get_graph_context(query, chunks)

        return chunks, graph_context

    def _get_graph_context(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> GraphContext:
        """
        Extract graph context for query and results.

        Args:
            query: Original query.
            chunks: Retrieved chunks.

        Returns:
            GraphContext with related entities.
        """
        # Extract potential medical entities from query
        entities = self._extract_entities(query)

        related_diseases = []
        related_drugs = []
        symptoms = []
        treatments = []
        interactions = []
        differentials = []

        # Query graph for each entity type
        for entity_type, entity_value in entities:
            if entity_type == "disease":
                # Get disease info
                disease = self.graph_queries.get_disease(entity_value)
                if disease:
                    related_diseases.append(disease)

                    # Get symptoms
                    disease_symptoms = self.graph_queries.get_disease_symptoms(entity_value)
                    symptoms.extend(disease_symptoms)

                    # Get treatments
                    disease_treatments = self.graph_queries.get_disease_treatments(entity_value)
                    treatments.extend(disease_treatments)

                    # Get differentials
                    diffs = self.graph_queries.get_differential_diagnosis(entity_value)
                    differentials.extend(diffs)

            elif entity_type == "drug":
                # Get drug info
                drug = self.graph_queries.get_drug(entity_value)
                if drug:
                    related_drugs.append(drug)

                    # Get interactions
                    drug_interactions = self.graph_queries.get_drug_interactions(entity_value)
                    interactions.extend(drug_interactions)

            elif entity_type == "symptom":
                # Get diseases from symptoms
                symptom_list = [entity_value]
                possible_diseases = self.graph_queries.symptoms_to_diseases(symptom_list)
                related_diseases.extend(possible_diseases[:5])

        return GraphContext(
            related_diseases=related_diseases[:10],
            related_drugs=related_drugs[:10],
            symptoms=symptoms[:15],
            treatments=treatments[:10],
            interactions=interactions[:10],
            differentials=differentials[:10],
        )

    def _extract_entities(self, query: str) -> list[tuple[str, str]]:
        """
        Extract medical entities from query.

        Simple keyword-based extraction.
        In production, use NER model.

        Args:
            query: User query.

        Returns:
            List of (entity_type, entity_value) tuples.
        """
        entities = []
        query_lower = query.lower()

        # Common disease keywords
        disease_keywords = [
            "diabetes", "hypertension", "heart failure", "asthma",
            "copd", "pneumonia", "stroke", "mi", "myocardial infarction",
            "cad", "coronary", "cancer", "infection", "sepsis",
        ]

        # Common drug keywords
        drug_keywords = [
            "metformin", "lisinopril", "atorvastatin", "aspirin",
            "warfarin", "insulin", "amlodipine", "omeprazole",
            "metoprolol", "losartan", "gabapentin", "prednisone",
        ]

        # Common symptom keywords
        symptom_keywords = [
            "pain", "fever", "cough", "dyspnea", "headache",
            "fatigue", "nausea", "vomiting", "diarrhea", "edema",
            "chest pain", "shortness of breath", "dizziness",
        ]

        for keyword in disease_keywords:
            if keyword in query_lower:
                entities.append(("disease", keyword))

        for keyword in drug_keywords:
            if keyword in query_lower:
                entities.append(("drug", keyword))

        for keyword in symptom_keywords:
            if keyword in query_lower:
                entities.append(("symptom", keyword))

        return entities

    def format_graph_context(self, context: GraphContext) -> str:
        """
        Format graph context for LLM prompt.

        Args:
            context: GraphContext object.

        Returns:
            Formatted string for prompt augmentation.
        """
        sections = []

        if context.related_diseases:
            disease_names = [d.get("name", d) for d in context.related_diseases[:5]]
            sections.append(f"**Related Conditions:** {', '.join(disease_names)}")

        if context.treatments:
            treatment_info = [
                f"{t['drug']} (Line {t.get('treatment_line', '?')}, Evidence: {t.get('evidence', 'N/A')})"
                for t in context.treatments[:5]
            ]
            sections.append(f"**Treatments:** {'; '.join(treatment_info)}")

        if context.symptoms:
            symptom_info = [
                f"{s['symptom']} ({s.get('frequency', 'unknown')} frequency)"
                for s in context.symptoms[:5]
            ]
            sections.append(f"**Common Symptoms:** {'; '.join(symptom_info)}")

        if context.interactions:
            interaction_warnings = [
                f"{i['interacting_drug']} ({i.get('severity', 'unknown')} severity)"
                for i in context.interactions[:3]
            ]
            sections.append(f"**Drug Interactions:** {'; '.join(interaction_warnings)}")

        if context.differentials:
            diff_names = [d.get("disease", d) for d in context.differentials[:5]]
            sections.append(f"**Differential Diagnoses:** {', '.join(diff_names)}")

        if sections:
            return "\n\n**Knowledge Graph Context:**\n" + "\n".join(sections)

        return ""

    def close(self):
        """Close connections."""
        if self.neo4j_client:
            self.neo4j_client.close()
