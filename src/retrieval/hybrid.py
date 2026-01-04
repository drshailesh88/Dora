"""Hybrid retriever combining dense, sparse, and optional graph retrieval."""

from typing import Optional

from src.core.config import settings
from src.core.models import Chunk, RetrievalResult

from .dense import DenseRetriever
from .sparse import SparseRetriever
from .fusion import ReciprocalRankFusion
from .reranker import CohereReranker, LocalReranker


class HybridRetriever:
    """
    Hybrid retriever that combines multiple retrieval strategies.

    Pipeline:
    1. Dense retrieval (semantic similarity via PubMedBERT)
    2. Sparse retrieval (keyword matching via BM25)
    3. RRF fusion to combine results
    4. Neural reranking for final precision
    """

    def __init__(
        self,
        collection_name: str = "medical_knowledge",
        dense_retriever: DenseRetriever | None = None,
        sparse_retriever: SparseRetriever | None = None,
        use_reranker: bool = True,
    ):
        """
        Initialize hybrid retriever.

        Args:
            collection_name: Vector collection name.
            dense_retriever: Pre-configured dense retriever.
            sparse_retriever: Pre-configured sparse retriever.
            use_reranker: Whether to use neural reranking.
        """
        self.dense = dense_retriever or DenseRetriever(collection_name=collection_name)
        self.sparse = sparse_retriever or SparseRetriever()
        self.fusion = ReciprocalRankFusion()

        self.use_reranker = use_reranker
        if use_reranker:
            if settings.has_reranker:
                self.reranker = CohereReranker()
            else:
                # Fall back to local reranker
                self.reranker = LocalReranker()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        filter_conditions: dict | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using hybrid search.

        Args:
            query: Query text.
            top_k: Number of final results.
            dense_weight: Weight for dense results in fusion.
            sparse_weight: Weight for sparse results in fusion.
            filter_conditions: Optional metadata filters (dense only).

        Returns:
            Fused and optionally reranked results.
        """
        top_k = top_k or settings.rerank_top_k

        # 1. Dense retrieval
        dense_results = self.dense.retrieve(
            query,
            top_k=settings.dense_top_k,
            filter_conditions=filter_conditions,
        )

        # 2. Sparse retrieval
        sparse_results = self.sparse.retrieve(
            query,
            top_k=settings.sparse_top_k,
        )

        # 3. Fuse results
        if dense_results and sparse_results:
            fused = self.fusion.fuse_with_weights(
                [dense_results, sparse_results],
                weights=[dense_weight, sparse_weight],
                top_k=settings.dense_top_k,  # Get more for reranking
            )
        elif dense_results:
            fused = dense_results
        elif sparse_results:
            fused = sparse_results
        else:
            return []

        # 4. Rerank if enabled
        if self.use_reranker and hasattr(self, "reranker"):
            fused = self.reranker.rerank(query, fused, top_k=top_k)
        else:
            fused = fused[:top_k]

        return fused

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Add chunks to both retrievers.

        Args:
            chunks: List of chunks to index.
        """
        self.dense.add_chunks(chunks)
        self.sparse.add_chunks(chunks)

    def index_stats(self) -> dict:
        """Get statistics about the indexes."""
        return {
            "sparse_size": self.sparse.size,
            "collection": self.dense.collection_name,
        }
