"""Reciprocal Rank Fusion for combining retrieval results."""

from collections import defaultdict

from src.core.config import settings
from src.core.models import RetrievalResult


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining multiple retrieval results.

    RRF is a simple but effective method for combining ranked lists.
    Score = sum(1 / (k + rank)) for each list where the document appears.
    """

    def __init__(self, k: int | None = None):
        """
        Initialize RRF.

        Args:
            k: RRF constant (default 60). Higher values reduce the impact of high ranks.
        """
        self.k = k or settings.rrf_k

    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Fuse multiple retrieval result lists using RRF.

        Args:
            result_lists: List of result lists from different retrievers.
            top_k: Number of final results to return.

        Returns:
            Fused and re-ranked results.
        """
        # Calculate RRF scores
        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievalResult] = {}

        for result_list in result_lists:
            for rank, result in enumerate(result_list, start=1):
                chunk_id = result.chunk.id
                rrf_scores[chunk_id] += 1.0 / (self.k + rank)

                # Keep the result with metadata
                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = result

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build final results with new scores
        results = []
        for chunk_id in sorted_ids:
            original = chunk_map[chunk_id]
            results.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=rrf_scores[chunk_id],
                    retriever="rrf_fusion",
                )
            )

        if top_k:
            results = results[:top_k]

        return results

    def fuse_with_weights(
        self,
        result_lists: list[list[RetrievalResult]],
        weights: list[float],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Fuse with custom weights for each retriever.

        Args:
            result_lists: List of result lists.
            weights: Weight for each result list.
            top_k: Number of final results.

        Returns:
            Weighted fused results.
        """
        if len(result_lists) != len(weights):
            raise ValueError("Number of result lists must match number of weights")

        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievalResult] = {}

        for result_list, weight in zip(result_lists, weights):
            for rank, result in enumerate(result_list, start=1):
                chunk_id = result.chunk.id
                rrf_scores[chunk_id] += weight * (1.0 / (self.k + rank))

                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = result

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for chunk_id in sorted_ids:
            original = chunk_map[chunk_id]
            results.append(
                RetrievalResult(
                    chunk=original.chunk,
                    score=rrf_scores[chunk_id],
                    retriever="rrf_fusion_weighted",
                )
            )

        if top_k:
            results = results[:top_k]

        return results
