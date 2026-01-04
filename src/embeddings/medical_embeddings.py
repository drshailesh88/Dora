"""Medical-optimized embeddings using PubMedBERT."""

from functools import lru_cache
from typing import Union

import numpy as np
from sentence_transformers import SentenceTransformer

from src.core.config import settings


class MedicalEmbeddings:
    """
    Medical-optimized embeddings using PubMedBERT.

    PubMedBERT is trained on biomedical literature and produces
    better embeddings for medical text than general-purpose models.
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):
        """
        Initialize the embedding model.

        Args:
            model_name: HuggingFace model name. Defaults to settings.
            device: Device to run on ('cuda', 'cpu', or None for auto).
        """
        self.model_name = model_name or settings.embedding_model
        self._device = device
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model."""
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self._device,
            )
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()

    def embed(
        self,
        texts: Union[str, list[str]],
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts to embed.
            normalize: Whether to L2-normalize embeddings (recommended for cosine similarity).
            show_progress: Show progress bar for large batches.

        Returns:
            numpy array of shape (n_texts, dimension) or (dimension,) for single text.
        """
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        if single_input:
            return embeddings[0]
        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a query (alias for embed with single text).

        Args:
            query: The query text.

        Returns:
            Embedding vector.
        """
        return self.embed(query, normalize=True)

    def embed_documents(
        self,
        documents: list[str],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> np.ndarray:
        """
        Embed multiple documents with batching.

        Args:
            documents: List of document texts.
            batch_size: Batch size for processing.
            show_progress: Show progress bar.

        Returns:
            Array of embeddings.
        """
        return self.model.encode(
            documents,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

    def similarity(self, query: str, documents: list[str]) -> np.ndarray:
        """
        Compute cosine similarity between query and documents.

        Args:
            query: Query text.
            documents: List of document texts.

        Returns:
            Array of similarity scores.
        """
        query_emb = self.embed_query(query)
        doc_embs = self.embed_documents(documents, show_progress=False)

        # Cosine similarity (embeddings are normalized)
        return np.dot(doc_embs, query_emb)


@lru_cache(maxsize=1)
def get_embeddings() -> MedicalEmbeddings:
    """Get cached embeddings instance."""
    return MedicalEmbeddings()
