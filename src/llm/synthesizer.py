"""Medical answer synthesis using LLMs."""

import time
from typing import Optional

from src.core.config import settings
from src.core.models import (
    Citation,
    ConfidenceLevel,
    MedicalAnswer,
    PatientContext,
    RetrievalResult,
)


class MedicalSynthesizer:
    """
    Synthesizes medical answers from retrieved context using LLMs.

    Supports both cloud (Claude, GPT-4) and local (Ollama) LLMs.
    """

    def __init__(
        self,
        prefer_local: bool = False,
    ):
        """
        Initialize synthesizer.

        Args:
            prefer_local: Prefer local LLM even when cloud is available.
        """
        self.prefer_local = prefer_local
        self._anthropic_client = None
        self._openai_client = None
        self._ollama_client = None

    @property
    def anthropic_client(self):
        """Lazy load Anthropic client."""
        if self._anthropic_client is None and settings.anthropic_api_key:
            import anthropic

            self._anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client

    @property
    def openai_client(self):
        """Lazy load OpenAI client."""
        if self._openai_client is None and settings.openai_api_key:
            import openai

            self._openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    @property
    def ollama_client(self):
        """Lazy load Ollama client."""
        if self._ollama_client is None:
            import ollama

            self._ollama_client = ollama.Client(host=settings.ollama_base_url)
        return self._ollama_client

    def synthesize(
        self,
        question: str,
        context: list[RetrievalResult],
        patient_context: PatientContext | None = None,
    ) -> MedicalAnswer:
        """
        Synthesize an answer from retrieved context.

        Args:
            question: User's question.
            context: Retrieved documents.
            patient_context: Optional patient information.

        Returns:
            Structured medical answer with citations.
        """
        start_time = time.time()

        # Build the context string
        context_str = self._build_context_string(context)

        # Build the prompt
        prompt = self._build_prompt(question, context_str, patient_context)

        # Generate answer using best available LLM
        if self.prefer_local or not settings.has_cloud_llm:
            answer_text, model_used = self._generate_local(prompt)
        elif self.anthropic_client:
            answer_text, model_used = self._generate_anthropic(prompt)
        elif self.openai_client:
            answer_text, model_used = self._generate_openai(prompt)
        else:
            answer_text, model_used = self._generate_local(prompt)

        # Extract citations from context
        citations = self._extract_citations(context)

        # Determine confidence based on retrieval scores
        confidence = self._determine_confidence(context)

        # Generate related queries
        related = self._generate_related_queries(question, answer_text)

        # Generate drug interaction warnings if patient context exists
        warnings = self._generate_warnings(question, answer_text, patient_context)

        latency_ms = int((time.time() - start_time) * 1000)

        return MedicalAnswer(
            question=question,
            answer=answer_text,
            confidence=confidence,
            citations=citations,
            related_queries=related,
            warnings=warnings,
            patient_context_used=patient_context is not None,
            model_used=model_used,
            latency_ms=latency_ms,
        )

    def _build_context_string(self, context: list[RetrievalResult]) -> str:
        """Build context string from retrieval results."""
        parts = []
        for i, result in enumerate(context, 1):
            source = result.chunk.metadata.get("source", "Unknown")
            page = result.chunk.metadata.get("page", "")
            page_str = f" (p. {page})" if page else ""

            parts.append(f"[{i}] {source}{page_str}:\n{result.chunk.text}\n")

        return "\n".join(parts)

    def _build_prompt(
        self,
        question: str,
        context: str,
        patient_context: PatientContext | None,
    ) -> str:
        """Build the synthesis prompt."""
        system = """You are a medical knowledge assistant helping physicians find evidence-based information.

CRITICAL RULES:
1. ONLY use information from the provided context. Do not use prior knowledge.
2. ALWAYS cite sources using [1], [2], etc. corresponding to the context numbers.
3. If the context doesn't contain relevant information, say "I couldn't find information about this in the available sources."
4. Be concise but thorough. Prioritize clinical relevance.
5. If there are conflicting recommendations, present both with their sources.
6. Include dosages, contraindications, and warnings when relevant.
7. This is for physician reference only - remind them to verify before clinical decisions."""

        patient_str = ""
        if patient_context:
            patient_str = f"""
PATIENT CONTEXT:
{patient_context.to_context_string()}

Consider this patient's conditions, medications, and allergies when answering.
"""

        prompt = f"""{system}

RETRIEVED CONTEXT:
{context}
{patient_str}
QUESTION: {question}

Provide a clear, evidence-based answer with citations:"""

        return prompt

    def _generate_anthropic(self, prompt: str) -> tuple[str, str]:
        """Generate using Claude."""
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text, "claude-3.5-sonnet"

    def _generate_openai(self, prompt: str) -> tuple[str, str]:
        """Generate using GPT-4."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content, "gpt-4o"

    def _generate_local(self, prompt: str) -> tuple[str, str]:
        """Generate using local Ollama."""
        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            return response["response"], f"ollama/{settings.ollama_model}"
        except Exception as e:
            return f"Error generating response: {str(e)}", "error"

    def _extract_citations(self, context: list[RetrievalResult]) -> list[Citation]:
        """Extract citations from context."""
        citations = []
        for result in context[:5]:  # Top 5 citations
            citations.append(
                Citation(
                    source=result.chunk.metadata.get("source", "Unknown"),
                    title=result.chunk.metadata.get("title", ""),
                    section=result.chunk.metadata.get("section"),
                    page=result.chunk.metadata.get("page"),
                    relevance_score=result.score,
                )
            )
        return citations

    def _determine_confidence(self, context: list[RetrievalResult]) -> ConfidenceLevel:
        """Determine confidence based on retrieval quality."""
        if not context:
            return ConfidenceLevel.LOW

        top_score = context[0].score
        avg_score = sum(r.score for r in context[:3]) / min(3, len(context))

        if top_score > 0.8 and avg_score > 0.7:
            return ConfidenceLevel.HIGH
        elif top_score > 0.6 and avg_score > 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _generate_warnings(
        self,
        question: str,
        answer: str,
        patient_context: PatientContext | None,
    ) -> list[str]:
        """Generate clinical warnings based on patient context and answer.

        Args:
            question: User's question
            answer: Generated answer
            patient_context: Patient information

        Returns:
            List of warning messages
        """
        warnings = []

        if not patient_context:
            return warnings

        # Drug interaction warnings
        if any(
            keyword in question.lower()
            for keyword in ["medication", "drug", "prescribe", "dose", "treatment"]
        ):
            # Check for common drug interactions based on current medications
            answer_lower = answer.lower()

            # Common interaction patterns
            interactions = {
                "warfarin": [
                    "aspirin",
                    "nsaid",
                    "ibuprofen",
                    "diclofenac",
                    "antibiotics",
                ],
                "metformin": ["contrast", "iodine", "creatinine"],
                "ace inhibitor": ["potassium", "nsaid", "diuretic"],
                "lisinopril": ["potassium", "nsaid"],
                "digoxin": ["amiodarone", "verapamil", "quinidine"],
            }

            for med in patient_context.current_medications:
                med_lower = med.lower()
                for drug, interacting_drugs in interactions.items():
                    if drug in med_lower:
                        for interacting in interacting_drugs:
                            if interacting in answer_lower:
                                warnings.append(
                                    f"⚠️ DRUG INTERACTION: Patient on {med}. "
                                    f"Check for interactions with {interacting}."
                                )

        # Renal function warnings
        if patient_context.active_diagnoses:
            for dx in patient_context.active_diagnoses:
                if any(
                    keyword in dx.lower()
                    for keyword in ["renal", "kidney", "ckd", "creatinine"]
                ):
                    if any(
                        keyword in answer.lower()
                        for keyword in ["nsaid", "metformin", "contrast", "dose"]
                    ):
                        warnings.append(
                            "⚠️ RENAL IMPAIRMENT: Patient has kidney disease. "
                            "Verify dose adjustment and contraindications."
                        )
                    break

        # Allergy warnings
        if patient_context.allergies:
            for allergy in patient_context.allergies:
                allergy_lower = allergy.lower()
                # Check if mentioned drug class is in answer
                if "penicillin" in allergy_lower and any(
                    abx in answer.lower()
                    for abx in [
                        "amoxicillin",
                        "ampicillin",
                        "penicillin",
                        "cephalosporin",
                    ]
                ):
                    warnings.append(
                        f"🚨 ALLERGY ALERT: Patient allergic to {allergy}. "
                        f"Cross-reactivity risk with beta-lactams."
                    )
                elif "sulfa" in allergy_lower and any(
                    drug in answer.lower()
                    for drug in ["sulfamethoxazole", "trimethoprim", "sulfa"]
                ):
                    warnings.append(
                        f"🚨 ALLERGY ALERT: Patient allergic to {allergy}. "
                        f"Avoid sulfa-containing medications."
                    )

        return warnings

    def _generate_related_queries(self, question: str, answer: str = "") -> list[str]:
        """Generate related follow-up queries using LLM.

        Args:
            question: Original question
            answer: Generated answer

        Returns:
            List of related queries
        """
        # Try LLM-based generation first
        try:
            if self.anthropic_client or self.openai_client:
                prompt = f"""Based on this medical question and answer, suggest 3 relevant follow-up questions a physician might ask.

Question: {question}
Answer: {answer[:500]}...

Generate 3 concise, clinically relevant follow-up questions (one per line):"""

                if self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=200,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    suggestions_text = response.content[0].text
                elif self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        max_tokens=200,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    suggestions_text = response.choices[0].message.content

                # Parse suggestions (one per line)
                suggestions = [
                    s.strip().lstrip("123.-) ")
                    for s in suggestions_text.strip().split("\n")
                    if s.strip()
                ]
                return suggestions[:3]
        except Exception:
            pass  # Fall back to heuristics

        # Fallback: heuristic-based suggestions
        suggestions = []

        if "treatment" in question.lower() or "treat" in question.lower():
            suggestions.append("What are the side effects?")
            suggestions.append("What are the contraindications?")
        elif "diagnosis" in question.lower():
            suggestions.append("What are the differential diagnoses?")
            suggestions.append("What investigations should be ordered?")
        elif "dose" in question.lower() or "dosage" in question.lower():
            suggestions.append("What about renal dose adjustment?")
            suggestions.append("What are the drug interactions?")
        else:
            # Generic follow-ups
            suggestions.append("What are the latest guidelines?")
            suggestions.append("What are the complications?")
            suggestions.append("When should I refer to a specialist?")

        return suggestions[:3]
