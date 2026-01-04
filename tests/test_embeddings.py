"""Tests for medical embeddings."""

import numpy as np
import pytest


class TestMedicalEmbeddings:
    """Test the medical embeddings module."""

    def test_embed_single_text(self):
        """Test embedding a single text."""
        from src.embeddings import MedicalEmbeddings

        embeddings = MedicalEmbeddings()
        text = "What is the treatment for hypertension?"

        result = embeddings.embed(text)

        assert isinstance(result, np.ndarray)
        assert result.shape == (embeddings.dimension,)

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        from src.embeddings import MedicalEmbeddings

        embeddings = MedicalEmbeddings()
        texts = [
            "What is diabetes?",
            "Treatment for hypertension",
            "Symptoms of heart failure",
        ]

        result = embeddings.embed(texts)

        assert isinstance(result, np.ndarray)
        assert result.shape == (3, embeddings.dimension)

    def test_similarity(self):
        """Test similarity calculation."""
        from src.embeddings import MedicalEmbeddings

        embeddings = MedicalEmbeddings()
        query = "diabetes treatment"
        docs = [
            "Management of type 2 diabetes mellitus with metformin",
            "The weather is sunny today",
            "Insulin therapy for diabetic patients",
        ]

        scores = embeddings.similarity(query, docs)

        # Medical docs should score higher than unrelated
        assert scores[0] > scores[1]
        assert scores[2] > scores[1]
