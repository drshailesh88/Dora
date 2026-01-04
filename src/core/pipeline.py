"""Main query pipeline orchestrating all components."""

import time
from typing import Optional

from src.core.config import settings
from src.core.models import MedicalAnswer, PatientContext, RetrievalResult
from src.embeddings import MedicalEmbeddings
from src.llm import MedicalSynthesizer, QueryExpander
from src.personalization import (
    DoctorProfile,
    PersonalizationStorage,
    ProfileLearner,
    QueryHistory,
    QueryPersonalizer,
    SpecialtyDetector,
)
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
        use_personalization: bool = True,
    ):
        """
        Initialize the query pipeline.

        Args:
            collection_name: Vector collection to search.
            use_multi_query: Enable multi-query expansion.
            use_hyde: Enable HyDE query expansion.
            use_reranker: Enable neural reranking.
            prefer_local_llm: Prefer local LLM over cloud.
            use_personalization: Enable personalization based on doctor profile.
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
        self.use_personalization = use_personalization

        # Personalization components
        if use_personalization:
            self.personalizer = QueryPersonalizer()
            self.detector = SpecialtyDetector()
            self.learner = ProfileLearner()
            self.storage = PersonalizationStorage()
        else:
            self.personalizer = None
            self.detector = None
            self.learner = None
            self.storage = None

    async def query(
        self,
        question: str,
        patient_context: PatientContext | None = None,
        top_k: int | None = None,
        filter_conditions: dict | None = None,
        user_id: Optional[str] = None,
    ) -> MedicalAnswer:
        """
        Execute the full query pipeline with personalization.

        Args:
            question: User's medical question.
            patient_context: Optional patient information for personalization.
            top_k: Number of final results.
            filter_conditions: Optional metadata filters.
            user_id: User ID for personalization (optional).

        Returns:
            Structured medical answer with citations.
        """
        top_k = top_k or settings.rerank_top_k

        # 0. Personalization setup
        doctor_profile = None
        if self.use_personalization and user_id and self.storage:
            doctor_profile = self.storage.get_profile(user_id)

            # Enhance query with specialty context
            if doctor_profile and self.personalizer:
                question = self.personalizer.add_specialty_context(question, doctor_profile)

            # Add specialty filters
            if doctor_profile and self.personalizer:
                specialty_filters = self.personalizer.filter_metadata(doctor_profile)
                if filter_conditions:
                    filter_conditions.update(specialty_filters)
                else:
                    filter_conditions = specialty_filters

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

        # 2.5. Apply personalization to results
        if doctor_profile and self.personalizer:
            top_results = self.personalizer.personalize_results(
                top_results,
                doctor_profile,
                question,
            )

        # 3. Synthesize answer
        answer = self.synthesizer.synthesize(
            question=question,
            context=top_results,
            patient_context=patient_context,
        )

        # 4. Track query for learning
        if self.use_personalization and user_id and self.detector and self.storage:
            # Detect specialty from query
            detection = self.detector.detect_from_query(question)
            entities = self.detector.extract_entities(question)

            # Create query history record
            query_record = QueryHistory(
                user_id=user_id,
                query=question,
                detected_specialty=detection[0] if detection else None,
                specialty_confidence=detection[1] if detection else 0.0,
                mentioned_drugs=entities.get("drugs", []),
                mentioned_conditions=entities.get("conditions", []),
                mentioned_procedures=entities.get("procedures", []),
                had_patient_context=patient_context is not None,
                result_count=len(top_results),
            )

            # Save query history
            self.storage.save_query_history(query_record)

            # Update profile
            if doctor_profile and self.learner:
                doctor_profile = self.learner.update_profile_from_query(
                    doctor_profile,
                    query_record,
                )
                self.storage.save_profile(doctor_profile)

        return answer

    def query_sync(
        self,
        question: str,
        patient_context: PatientContext | None = None,
        top_k: int | None = None,
        filter_conditions: dict | None = None,
        user_id: Optional[str] = None,
    ) -> MedicalAnswer:
        """Synchronous version of query with personalization."""
        import asyncio

        return asyncio.run(
            self.query(
                question=question,
                patient_context=patient_context,
                top_k=top_k,
                filter_conditions=filter_conditions,
                user_id=user_id,
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
