"""Dense retrieval using vector similarity search."""

from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.core.config import settings
from src.core.models import Chunk, RetrievalResult
from src.embeddings import MedicalEmbeddings


class DenseRetriever:
    """
    Dense retrieval using PubMedBERT embeddings and Qdrant.

    Uses semantic similarity to find relevant documents.
    """

    def __init__(
        self,
        collection_name: str = "medical_knowledge",
        embeddings: MedicalEmbeddings | None = None,
        client: QdrantClient | None = None,
    ):
        """
        Initialize dense retriever.

        Args:
            collection_name: Qdrant collection to search.
            embeddings: Embedding model (uses default if None).
            client: Qdrant client (creates one if None).
        """
        self.collection_name = collection_name
        self.embeddings = embeddings or MedicalEmbeddings()

        if client:
            self.client = client
        else:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filter_conditions: dict | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using dense vector search.

        Args:
            query: Query text.
            top_k: Number of results to return.
            filter_conditions: Optional metadata filters.

        Returns:
            List of retrieval results with scores.
        """
        top_k = top_k or settings.dense_top_k

        # Embed the query
        query_vector = self.embeddings.embed_query(query)

        # Build filter if provided
        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = self._build_filter(filter_conditions)

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        # Convert to RetrievalResult
        return [
            RetrievalResult(
                chunk=Chunk(
                    id=str(hit.id),
                    text=hit.payload.get("text", ""),
                    metadata={k: v for k, v in hit.payload.items() if k != "text"},
                ),
                score=hit.score,
                retriever="dense",
            )
            for hit in results
        ]

    def _build_filter(self, conditions: dict) -> qmodels.Filter:
        """Build Qdrant filter from conditions dict."""
        must_conditions = []

        for key, value in conditions.items():
            if isinstance(value, list):
                must_conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchAny(any=value),
                    )
                )
            else:
                must_conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=value),
                    )
                )

        return qmodels.Filter(must=must_conditions)

    def ensure_collection(self) -> None:
        """Ensure the collection exists, create if not."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.embeddings.dimension,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Add chunks to the collection.

        Args:
            chunks: List of chunks to add.
        """
        self.ensure_collection()

        # Generate embeddings for chunks without them
        texts = [c.text for c in chunks]
        embeddings = self.embeddings.embed_documents(texts)

        points = [
            qmodels.PointStruct(
                id=chunk.id,
                vector=embedding.tolist(),
                payload={"text": chunk.text, **chunk.metadata},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
