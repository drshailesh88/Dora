"""Sparse retrieval using BM25."""

import json
import pickle
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

from src.core.config import settings
from src.core.models import Chunk, RetrievalResult


class SparseRetriever:
    """
    Sparse retrieval using BM25.

    BM25 is effective for keyword matching and complements
    dense retrieval for hybrid search.
    """

    def __init__(
        self,
        index_path: str | Path | None = None,
    ):
        """
        Initialize sparse retriever.

        Args:
            index_path: Path to save/load the BM25 index.
        """
        self.index_path = Path(index_path) if index_path else None
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Chunk] = []
        self._tokenized_corpus: list[list[str]] = []

        # Try to load existing index
        if self.index_path and self.index_path.exists():
            self.load()

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on whitespace/punctuation
        import re

        tokens = re.findall(r"\b\w+\b", text.lower())
        return tokens

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Add chunks to the index.

        Args:
            chunks: List of chunks to index.
        """
        for chunk in chunks:
            self._chunks.append(chunk)
            tokens = self._tokenize(chunk.text)
            self._tokenized_corpus.append(tokens)

        # Rebuild BM25 index
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using BM25.

        Args:
            query: Query text.
            top_k: Number of results to return.

        Returns:
            List of retrieval results with scores.
        """
        if self._bm25 is None or len(self._chunks) == 0:
            return []

        top_k = top_k or settings.sparse_top_k

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        scores = self._bm25.get_scores(query_tokens)

        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append(
                    RetrievalResult(
                        chunk=self._chunks[idx],
                        score=float(scores[idx]),
                        retriever="sparse",
                    )
                )

        return results

    def save(self) -> None:
        """Save index to disk."""
        if self.index_path is None:
            raise ValueError("No index_path specified")

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "chunks": [c.model_dump() for c in self._chunks],
            "tokenized_corpus": self._tokenized_corpus,
        }

        with open(self.index_path, "wb") as f:
            pickle.dump(data, f)

    def load(self) -> None:
        """Load index from disk."""
        if self.index_path is None or not self.index_path.exists():
            return

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)

        self._chunks = [Chunk(**c) for c in data["chunks"]]
        self._tokenized_corpus = data["tokenized_corpus"]

        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    @property
    def size(self) -> int:
        """Number of documents in the index."""
        return len(self._chunks)
