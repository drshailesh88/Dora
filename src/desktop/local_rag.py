"""
Local RAG Implementation with Ollama for Offline Queries

This module implements a fully offline RAG system using:
- Ollama for local LLM inference (Qwen 2.5)
- ChromaDB for local vector storage
- Cached documents as knowledge base

Features:
- Fully offline operation
- Medical domain optimization
- Citation generation
- Confidence scoring
"""

import logging
from typing import Optional, List, Dict, Any
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalRAG:
    """
    Local RAG system for offline medical knowledge queries

    Uses Ollama (Qwen 2.5) for LLM and ChromaDB for vector storage.
    Falls back gracefully if Ollama is not available.
    """

    def __init__(self, storage):
        self.storage = storage
        self.ollama_client = None
        self.chroma_client = None
        self.collection = None

        self.model_name = "qwen2.5:3b"  # Lightweight model for offline
        self.available = False

    async def initialize(self):
        """Initialize local RAG components"""
        try:
            # Initialize Ollama client
            await self._init_ollama()

            # Initialize ChromaDB
            await self._init_chromadb()

            # Load cached documents into vector DB
            await self._index_cached_documents()

            self.available = True
            logger.info("Local RAG initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize local RAG: {e}")
            self.available = False

    async def _init_ollama(self):
        """Initialize Ollama client"""
        try:
            import ollama

            # Test Ollama connection
            self.ollama_client = ollama.Client()

            # Check if model is available
            models = self.ollama_client.list()
            model_names = [m['name'] for m in models.get('models', [])]

            if self.model_name not in model_names:
                logger.warning(
                    f"Model {self.model_name} not found. "
                    "Please install: ollama pull qwen2.5:3b"
                )
                self.available = False
            else:
                logger.info(f"Ollama model {self.model_name} ready")

        except ImportError:
            logger.error("Ollama package not installed: pip install ollama")
            raise
        except Exception as e:
            logger.error(f"Ollama initialization error: {e}")
            raise

    async def _init_chromadb(self):
        """Initialize ChromaDB for local vector storage"""
        try:
            import chromadb
            from chromadb.config import Settings

            # Create persistent client
            db_path = Path.home() / ".dora" / "chromadb"
            db_path.mkdir(parents=True, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="medical_documents",
                metadata={"description": "Cached medical documents for offline RAG"}
            )

            logger.info("ChromaDB initialized")

        except ImportError:
            logger.error("ChromaDB package not installed: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"ChromaDB initialization error: {e}")
            raise

    async def _index_cached_documents(self):
        """Index cached documents into ChromaDB"""
        try:
            # Get all pinned documents (high priority for offline)
            documents = self.storage.search_documents(
                pinned_only=True,
                limit=1000
            )

            if not documents:
                logger.warning("No cached documents to index")
                return

            # Prepare for indexing
            doc_ids = []
            doc_texts = []
            metadatas = []

            for doc in documents:
                doc_ids.append(doc.doc_id)
                doc_texts.append(doc.content)
                metadatas.append({
                    'title': doc.title,
                    'specialty': doc.specialty or 'general',
                    'category': doc.category,
                })

            # Add to ChromaDB (it will auto-generate embeddings)
            self.collection.upsert(
                ids=doc_ids,
                documents=doc_texts,
                metadatas=metadatas
            )

            logger.info(f"Indexed {len(documents)} documents into ChromaDB")

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")

    async def query(
        self,
        query_text: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Process query using local RAG

        Args:
            query_text: User's question
            top_k: Number of documents to retrieve

        Returns:
            Dictionary with answer, sources, and confidence
        """
        if not self.available:
            return {
                'error': 'Local RAG not available',
                'suggestion': 'Connect to internet for cloud queries'
            }

        try:
            # Step 1: Retrieve relevant documents
            retrieval_results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k
            )

            if not retrieval_results['documents'] or not retrieval_results['documents'][0]:
                return {
                    'answer': 'No relevant information found in offline cache.',
                    'sources': [],
                    'confidence': 0.0
                }

            # Extract documents and metadata
            documents = retrieval_results['documents'][0]
            metadatas = retrieval_results['metadatas'][0]
            distances = retrieval_results['distances'][0]

            # Step 2: Construct prompt for LLM
            context = self._build_context(documents, metadatas)
            prompt = self._build_prompt(query_text, context)

            # Step 3: Generate answer with Ollama
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Low temperature for medical accuracy
                    'top_p': 0.9,
                    'num_predict': 512,
                }
            )

            answer = response['response']

            # Step 4: Extract sources
            sources = [
                {
                    'title': meta['title'],
                    'specialty': meta['specialty'],
                    'category': meta['category'],
                    'relevance': 1 - (dist / max(distances)) if distances else 1.0
                }
                for meta, dist in zip(metadatas, distances)
            ]

            # Step 5: Calculate confidence score
            confidence = self._calculate_confidence(distances, answer)

            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'mode': 'local_rag',
                'model': self.model_name
            }

        except Exception as e:
            logger.error(f"Local RAG query error: {e}")
            return {
                'error': str(e),
                'sources': [],
                'confidence': 0.0
            }

    def _build_context(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> str:
        """Build context from retrieved documents"""
        context_parts = []

        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            # Truncate long documents
            doc_text = doc[:1000] if len(doc) > 1000 else doc

            context_parts.append(
                f"[Source {i}: {meta['title']}]\n{doc_text}\n"
            )

        return "\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM"""
        return f"""You are a medical AI assistant with access to offline medical references. Answer the following question based ONLY on the provided context. If the context doesn't contain enough information, say so clearly.

Context:
{context}

Question: {query}

Instructions:
1. Answer based only on the provided context
2. Be concise and accurate
3. If unsure, state the limitations
4. Cite sources by number [Source 1], [Source 2], etc.
5. For medical advice, always recommend consulting a physician

Answer:"""

    def _calculate_confidence(
        self,
        distances: List[float],
        answer: str
    ) -> float:
        """Calculate confidence score for the answer"""
        if not distances:
            return 0.0

        # Base confidence on retrieval quality
        avg_distance = sum(distances) / len(distances)

        # Lower distance = higher confidence
        # Normalize to 0-1 range
        retrieval_confidence = max(0, 1 - (avg_distance / 2))

        # Reduce confidence if answer mentions uncertainty
        uncertainty_keywords = [
            'not sure', 'unclear', 'unknown', 'cannot determine',
            'limited information', 'insufficient'
        ]

        answer_lower = answer.lower()
        has_uncertainty = any(
            keyword in answer_lower
            for keyword in uncertainty_keywords
        )

        final_confidence = retrieval_confidence * (0.5 if has_uncertainty else 1.0)

        return round(final_confidence, 2)

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """Add new document to local RAG"""
        try:
            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            logger.info(f"Added document {doc_id} to local RAG")

        except Exception as e:
            logger.error(f"Error adding document to local RAG: {e}")

    async def remove_document(self, doc_id: str):
        """Remove document from local RAG"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Removed document {doc_id} from local RAG")

        except Exception as e:
            logger.error(f"Error removing document from local RAG: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get local RAG statistics"""
        try:
            count = self.collection.count()

            return {
                'available': self.available,
                'model': self.model_name,
                'indexed_documents': count,
                'vector_db': 'ChromaDB',
                'llm_provider': 'Ollama'
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'available': False}

    async def cleanup(self):
        """Cleanup resources"""
        # ChromaDB client cleanup if needed
        self.chroma_client = None
        self.collection = None
        logger.info("Local RAG cleanup complete")


class OfflineCalculators:
    """
    Offline medical calculators (no LLM needed)

    Fully functional offline calculators for common medical calculations.
    """

    @staticmethod
    def bmi(weight_kg: float, height_m: float) -> Dict[str, Any]:
        """Calculate BMI"""
        bmi = weight_kg / (height_m ** 2)

        category = 'Normal'
        if bmi < 18.5:
            category = 'Underweight'
        elif bmi >= 25 and bmi < 30:
            category = 'Overweight'
        elif bmi >= 30:
            category = 'Obese'

        return {
            'value': round(bmi, 1),
            'category': category,
            'unit': 'kg/m²'
        }

    @staticmethod
    def creatinine_clearance(
        age: int,
        weight_kg: float,
        creatinine_mg_dl: float,
        is_female: bool = False
    ) -> Dict[str, Any]:
        """Calculate Creatinine Clearance (Cockcroft-Gault)"""
        ccr = ((140 - age) * weight_kg) / (72 * creatinine_mg_dl)

        if is_female:
            ccr *= 0.85

        return {
            'value': round(ccr, 1),
            'unit': 'mL/min',
            'formula': 'Cockcroft-Gault'
        }

    @staticmethod
    def gfr(
        creatinine_mg_dl: float,
        age: int,
        is_female: bool = False,
        is_black: bool = False
    ) -> Dict[str, Any]:
        """Calculate GFR (MDRD)"""
        gfr = 186 * (creatinine_mg_dl ** -1.154) * (age ** -0.203)

        if is_female:
            gfr *= 0.742

        if is_black:
            gfr *= 1.212

        return {
            'value': round(gfr, 1),
            'unit': 'mL/min/1.73m²',
            'formula': 'MDRD'
        }

    @staticmethod
    def get_available_calculators() -> List[str]:
        """Get list of available offline calculators"""
        return [
            'bmi',
            'creatinine_clearance',
            'gfr',
            # Add more calculators as needed
        ]
