"""Main query pipeline orchestrating all components."""

import time
from typing import Optional

from src.core.config import settings
from src.core.models import MedicalAnswer, PatientContext, RetrievalResult
from src.embeddings import MedicalEmbeddings
from src.llm import MedicalSynthesizer, QueryExpander
from src.retrieval import HybridRetriever


class MedicalQueryPipeline:
    """
    Main query pipeline for Dora.

    Pipeline:
    1. Query expansion (multi-query, HyDE)
    2. Hybrid retrieval (dense + sparse + RRF)
    3. Neural reranking
    4. LLM synthesis with citations
    """

    def __init__(
        self,
        collection_name: str = "medical_knowledge",
        use_multi_query: bool = True,
        use_hyde: bool = True,
        use_reranker: bool = True,
        prefer_local_llm: bool = False,
    ):
        """
        Initialize the query pipeline.

        Args:
            collection_name: Vector collection to search.
            use_multi_query: Enable multi-query expansion.
            use_hyde: Enable HyDE query expansion.
            use_reranker: Enable neural reranking.
            prefer_local_llm: Prefer local LLM over cloud.
        """
        self.embeddings = MedicalEmbeddings()
        self.retriever = HybridRetriever(
            collection_name=collection_name,
            use_reranker=use_reranker,
        )
        self.query_expander = QueryExpander(embeddings=self.embeddings)
        self.synthesizer = MedicalSynthesizer(prefer_local=prefer_local_llm)

        self.use_multi_query = use_multi_query
        self.use_hyde = use_hyde

    async def query(
        self,
        question: str,
        patient_context: PatientContext | None = None,
        top_k: int | None = None,
        filter_conditions: dict | None = None,
    ) -> MedicalAnswer:
        """
        Execute the full query pipeline.

        Args:
            question: User's medical question.
            patient_context: Optional patient information for personalization.
            top_k: Number of final results.
            filter_conditions: Optional metadata filters.

        Returns:
            Structured medical answer with citations.
        """
        top_k = top_k or settings.rerank_top_k

        # 1. Query expansion
        queries = [question]

        if self.use_multi_query:
            variations = self.query_expander.multi_query(question)
            queries.extend(variations)

        if self.use_hyde:
            hyde_doc = self.query_expander.hyde(question)
            queries.append(hyde_doc)

        # 2. Retrieve for all query variations and merge
        all_results: list[RetrievalResult] = []
        seen_ids = set()

        for q in queries:
            results = self.retriever.retrieve(
                query=q,
                top_k=top_k,
                filter_conditions=filter_conditions,
            )
            for r in results:
                if r.chunk.id not in seen_ids:
                    all_results.append(r)
                    seen_ids.add(r.chunk.id)

        # Sort by score and take top_k
        all_results.sort(key=lambda x: x.score, reverse=True)
        top_results = all_results[:top_k]

        # 3. Synthesize answer
        answer = self.synthesizer.synthesize(
            question=question,
            context=top_results,
            patient_context=patient_context,
        )

        return answer

    def query_sync(
        self,
        question: str,
        patient_context: PatientContext | None = None,
        top_k: int | None = None,
        filter_conditions: dict | None = None,
    ) -> MedicalAnswer:
        """Synchronous version of query."""
        import asyncio

        return asyncio.run(
            self.query(
                question=question,
                patient_context=patient_context,
                top_k=top_k,
                filter_conditions=filter_conditions,
            )
        )

    def retrieve_only(
        self,
        question: str,
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Only perform retrieval without synthesis.

        Useful for debugging or when you want to inspect retrieved documents.
        """
        return self.retriever.retrieve(query=question, top_k=top_k)
