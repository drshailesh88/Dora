"""Tests for retrieval components."""

import pytest


class TestSparseRetriever:
    """Test BM25 sparse retriever."""

    def test_add_and_retrieve(self, sample_chunks):
        """Test adding chunks and retrieving."""
        from src.retrieval import SparseRetriever

        retriever = SparseRetriever()
        retriever.add_chunks(sample_chunks)

        results = retriever.retrieve("metformin diabetes", top_k=5)

        assert len(results) > 0
        assert results[0].retriever == "sparse"
        assert "metformin" in results[0].chunk.text.lower()

    def test_empty_retriever(self):
        """Test retrieval from empty index."""
        from src.retrieval import SparseRetriever

        retriever = SparseRetriever()
        results = retriever.retrieve("test query")

        assert results == []


class TestRRFFusion:
    """Test Reciprocal Rank Fusion."""

    def test_fusion(self, sample_chunks):
        """Test fusing multiple result lists."""
        from src.retrieval import ReciprocalRankFusion
        from src.core.models import RetrievalResult

        fusion = ReciprocalRankFusion(k=60)

        # Create mock result lists
        list1 = [
            RetrievalResult(chunk=sample_chunks[0], score=0.9, retriever="dense"),
        ]
        list2 = [
            RetrievalResult(chunk=sample_chunks[0], score=0.8, retriever="sparse"),
        ]

        results = fusion.fuse([list1, list2])

        assert len(results) == 1
        assert results[0].retriever == "rrf_fusion"


class TestChunker:
    """Test medical-aware chunking."""

    def test_chunking(self, sample_text):
        """Test basic chunking."""
        from src.ingestion import MedicalChunker

        chunker = MedicalChunker(chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk(sample_text, metadata={"source": "test"})

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata["source"] == "test"

    def test_preserves_dosing(self):
        """Test that dosing information stays together."""
        from src.ingestion import MedicalChunker

        text = "Dosage: Metformin 500mg BD for 7 days. Monitor renal function."
        chunker = MedicalChunker(chunk_size=100)
        chunks = chunker.chunk(text)

        # The dosing info should be in one chunk
        dosing_found = any("500mg BD" in c.text for c in chunks)
        assert dosing_found
