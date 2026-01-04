"""Neural reranking using Cohere."""

from typing import Optional

import cohere

from src.core.config import settings
from src.core.models import RetrievalResult


class CohereReranker:
    """
    Neural reranking using Cohere's rerank API.

    Reranking significantly improves precision by using a
    cross-encoder model to score query-document pairs.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "rerank-english-v3.0",
    ):
        """
        Initialize Cohere reranker.

        Args:
            api_key: Cohere API key (uses settings if None).
            model: Reranking model to use.
        """
        self.api_key = api_key or settings.cohere_api_key
        self.model = model
        self._client: cohere.Client | None = None

    @property
    def client(self) -> cohere.Client:
        """Lazy load Cohere client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("Cohere API key not configured")
            self._client = cohere.Client(self.api_key)
        return self._client

    @property
    def is_available(self) -> bool:
        """Check if reranker is available."""
        return bool(self.api_key)

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Rerank results using Cohere.

        Args:
            query: Original query.
            results: Results to rerank.
            top_k: Number of results to return after reranking.

        Returns:
            Reranked results with new scores.
        """
        if not results:
            return []

        if not self.is_available:
            # Return original results if reranker not available
            return results[:top_k] if top_k else results

        top_k = top_k or settings.rerank_top_k

        # Extract texts for reranking
        documents = [r.chunk.text for r in results]

        # Call Cohere rerank API
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=min(top_k, len(documents)),
            return_documents=False,
        )

        # Build reranked results
        reranked = []
        for result in response.results:
            original = results[result.index]
            reranked.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=result.relevance_score,
                    retriever="cohere_rerank",
                )
            )

        return reranked


class LocalReranker:
    """
    Fallback local reranking using cross-encoder.

    Used when Cohere is not available (offline mode).
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize local reranker.

        Args:
            model_name: Cross-encoder model to use.
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load cross-encoder model."""
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """Rerank using local cross-encoder."""
        if not results:
            return []

        top_k = top_k or settings.rerank_top_k

        # Prepare pairs for cross-encoder
        pairs = [(query, r.chunk.text) for r in results]

        # Score pairs
        scores = self.model.predict(pairs)

        # Sort by score
        scored_results = list(zip(results, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Build reranked results
        reranked = []
        for original, score in scored_results[:top_k]:
            reranked.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=float(score),
                    retriever="local_rerank",
                )
            )

        return reranked
