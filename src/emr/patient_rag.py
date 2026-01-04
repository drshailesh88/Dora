"""Patient-specific RAG for contextual queries."""

from typing import Optional

from src.core.models import Chunk, PatientContext
from src.embeddings import MedicalEmbeddings
from src.retrieval import HybridRetriever

from .bridge import EMRBridge


class PatientRAG:
    """
    RAG system for patient-specific context.

    Indexes patient visits, investigations, and notes
    for retrieval during queries.
    """

    def __init__(
        self,
        emr_bridge: EMRBridge | None = None,
        embeddings: MedicalEmbeddings | None = None,
    ):
        """
        Initialize patient RAG.

        Args:
            emr_bridge: EMR connection.
            embeddings: Embedding model.
        """
        self.emr = emr_bridge or EMRBridge()
        self.embeddings = embeddings or MedicalEmbeddings()

        # Per-patient retrievers (cached)
        self._patient_retrievers: dict[int, HybridRetriever] = {}

    def _get_patient_retriever(self, patient_id: int) -> HybridRetriever:
        """Get or create retriever for a patient."""
        if patient_id not in self._patient_retrievers:
            retriever = HybridRetriever(
                collection_name=f"patient_{patient_id}",
                use_reranker=False,  # Skip reranking for speed
            )
            self._patient_retrievers[patient_id] = retriever
        return self._patient_retrievers[patient_id]

    def index_patient(self, patient_id: int) -> int:
        """
        Index all patient documents for RAG.

        Args:
            patient_id: Patient to index.

        Returns:
            Number of chunks indexed.
        """
        if not self.emr.is_connected:
            return 0

        chunks = []

        # Index visits
        visits = self.emr.get_patient_visits(patient_id, limit=50)
        for visit in visits:
            text = self._visit_to_text(visit)
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "type": "visit",
                        "patient_id": patient_id,
                        "date": visit.get("visit_date", ""),
                        "visit_id": visit.get("id"),
                    },
                )
            )

        # Index investigations
        investigations = self.emr.get_patient_investigations(patient_id, limit=100)
        for inv in investigations:
            text = self._investigation_to_text(inv)
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "type": "investigation",
                        "patient_id": patient_id,
                        "date": inv.get("test_date", ""),
                        "test_name": inv.get("test_name", ""),
                    },
                )
            )

        if chunks:
            retriever = self._get_patient_retriever(patient_id)
            retriever.add_chunks(chunks)

        return len(chunks)

    def _visit_to_text(self, visit: dict) -> str:
        """Convert visit record to searchable text."""
        parts = []

        if visit.get("visit_date"):
            parts.append(f"Visit on {visit['visit_date']}")
        if visit.get("chief_complaint"):
            parts.append(f"Chief complaint: {visit['chief_complaint']}")
        if visit.get("diagnosis"):
            parts.append(f"Diagnosis: {visit['diagnosis']}")
        if visit.get("notes"):
            parts.append(f"Notes: {visit['notes']}")

        return ". ".join(parts)

    def _investigation_to_text(self, inv: dict) -> str:
        """Convert investigation to searchable text."""
        parts = [f"{inv.get('test_name', 'Test')}"]

        if inv.get("result"):
            parts.append(f"Result: {inv['result']}")
            if inv.get("unit"):
                parts[-1] += f" {inv['unit']}"
        if inv.get("reference_range"):
            parts.append(f"(Reference: {inv['reference_range']})")
        if inv.get("abnormal"):
            parts.append("[ABNORMAL]")
        if inv.get("test_date"):
            parts.append(f"on {inv['test_date']}")

        return " ".join(parts)

    def retrieve_patient_context(
        self,
        patient_id: int,
        query: str,
        top_k: int = 5,
    ) -> list[Chunk]:
        """
        Retrieve relevant patient documents for a query.

        Args:
            patient_id: Patient ID.
            query: The user's query.
            top_k: Number of results.

        Returns:
            Relevant chunks from patient history.
        """
        retriever = self._get_patient_retriever(patient_id)
        results = retriever.retrieve(query, top_k=top_k)
        return [r.chunk for r in results]

    def get_patient_summary(self, patient_id: int) -> str:
        """
        Generate a summary of the patient for context.

        Args:
            patient_id: Patient ID.

        Returns:
            Summary string.
        """
        context = self.emr.get_patient_context(patient_id)
        if context:
            return context.to_context_string()
        return ""
