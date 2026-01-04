"""Query expansion techniques for improved retrieval."""

from typing import Optional

from src.core.config import settings
from src.embeddings import MedicalEmbeddings


class QueryExpander:
    """
    Expands queries for improved retrieval coverage.

    Techniques:
    1. Multi-query: Generate query variations
    2. HyDE: Hypothetical Document Embedding
    """

    def __init__(
        self,
        embeddings: MedicalEmbeddings | None = None,
    ):
        """
        Initialize query expander.

        Args:
            embeddings: Embedding model for HyDE.
        """
        self.embeddings = embeddings or MedicalEmbeddings()
        self._ollama_client = None

    @property
    def ollama_client(self):
        """Lazy load Ollama client."""
        if self._ollama_client is None:
            import ollama

            self._ollama_client = ollama.Client(host=settings.ollama_base_url)
        return self._ollama_client

    def multi_query(self, query: str, num_variations: int = 3) -> list[str]:
        """
        Generate query variations for broader retrieval.

        Args:
            query: Original query.
            num_variations: Number of variations to generate.

        Returns:
            List of query variations including original.
        """
        prompt = f"""Generate {num_variations} alternative phrasings of this medical question.
Each variation should capture the same intent but use different words.

Original question: {query}

Return only the variations, one per line, without numbering or explanation:"""

        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )

            variations = [query]  # Always include original
            for line in response["response"].strip().split("\n"):
                line = line.strip()
                if line and line != query:
                    variations.append(line)

            return variations[:num_variations + 1]

        except Exception:
            # Return just original if expansion fails
            return [query]

    def hyde(self, query: str) -> str:
        """
        Generate Hypothetical Document for embedding.

        HyDE generates a hypothetical answer to the query,
        then uses its embedding for retrieval. This often
        improves retrieval for complex questions.

        Args:
            query: The query to expand.

        Returns:
            Hypothetical document text.
        """
        prompt = f"""You are a medical textbook. Write a brief, factual paragraph that would answer this question.
Do not add disclaimers or caveats. Write as if from an authoritative medical source.

Question: {query}

Answer:"""

        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            return response["response"].strip()

        except Exception:
            # Return original query if HyDE fails
            return query

    def expand_with_medical_terms(self, query: str) -> list[str]:
        """
        Expand query with medical terminology.

        Args:
            query: Original query.

        Returns:
            List including original and medical term variations.
        """
        prompt = f"""Given this medical question, add relevant medical terminology.
Return the expanded question that includes proper medical terms.

Question: {query}

Expanded with medical terms:"""

        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            expanded = response["response"].strip()
            return [query, expanded] if expanded != query else [query]

        except Exception:
            return [query]
