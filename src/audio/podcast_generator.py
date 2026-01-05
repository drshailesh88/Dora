"""Generate NotebookLM-style podcast scripts from medical documents."""

import logging
import time
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.models import Document

logger = logging.getLogger(__name__)


class PodcastLength(str, Enum):
    """Podcast length options."""

    SHORT = "5min"  # ~750 words
    MEDIUM = "10min"  # ~1500 words
    LONG = "15min"  # ~2250 words


class PodcastStyle(str, Enum):
    """Podcast conversation style."""

    CASUAL = "casual"  # Friendly, conversational
    PROFESSIONAL = "professional"  # More formal, academic
    TEACHING = "teaching"  # Explanatory, educational


class Speaker(BaseModel):
    """A speaker in the podcast."""

    name: str = Field(..., description="Speaker name (e.g., 'Host', 'Expert')")
    voice_id: str = Field(..., description="Voice ID for TTS")
    role: str = Field(..., description="Role in conversation")


class DialogueLine(BaseModel):
    """A single line of dialogue in the podcast."""

    speaker: str = Field(..., description="Speaker name")
    text: str = Field(..., description="What they say")
    timestamp: Optional[float] = Field(None, description="Timestamp in seconds")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class PodcastScript(BaseModel):
    """A complete podcast script."""

    title: str = Field(..., description="Podcast episode title")
    description: str = Field(..., description="Episode description")
    speakers: list[Speaker] = Field(..., description="List of speakers")
    dialogue: list[DialogueLine] = Field(..., description="Script dialogue")
    duration_estimate: int = Field(..., description="Estimated duration in seconds")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    generated_at: float = Field(default_factory=time.time)


class PodcastGenerator:
    """
    Generate conversational podcast scripts from medical documents.

    Creates NotebookLM-style two-voice dialogues that summarize medical content
    in an engaging, accessible way.
    """

    # Default speakers
    DEFAULT_SPEAKERS = [
        Speaker(
            name="Dr. Sarah",
            voice_id="en_female_1",
            role="Host and primary explainer",
        ),
        Speaker(
            name="Dr. Michael",
            voice_id="en_male_1",
            role="Co-host and questioner",
        ),
    ]

    # Word counts for different lengths (assuming 150 words/min speaking rate)
    LENGTH_WORD_COUNTS = {
        PodcastLength.SHORT: 750,
        PodcastLength.MEDIUM: 1500,
        PodcastLength.LONG: 2250,
    }

    def __init__(
        self,
        prefer_local: bool = False,
    ):
        """
        Initialize podcast generator.

        Args:
            prefer_local: Prefer local LLM for script generation.
        """
        self.prefer_local = prefer_local
        self._anthropic_client = None
        self._openai_client = None
        self._ollama_client = None

        logger.info(f"Initialized PodcastGenerator (prefer_local={prefer_local})")

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

    def generate_from_document(
        self,
        document: Document,
        length: PodcastLength = PodcastLength.MEDIUM,
        style: PodcastStyle = PodcastStyle.PROFESSIONAL,
        speakers: Optional[list[Speaker]] = None,
    ) -> PodcastScript:
        """
        Generate a podcast script from a document.

        Args:
            document: Document to create podcast from.
            length: Desired podcast length.
            style: Conversation style.
            speakers: Custom speakers (defaults to Dr. Sarah and Dr. Michael).

        Returns:
            Generated podcast script.
        """
        speakers = speakers or self.DEFAULT_SPEAKERS
        target_words = self.LENGTH_WORD_COUNTS[length]

        logger.info(
            f"Generating podcast for document '{document.title}' "
            f"(length={length.value}, style={style.value}, target_words={target_words})"
        )

        # Generate the script using LLM
        script_text = self._generate_script_with_llm(
            document_title=document.title,
            document_content=self._extract_document_summary(document),
            target_words=target_words,
            style=style,
            speakers=speakers,
        )

        # Parse the script into dialogue lines
        dialogue = self._parse_script_to_dialogue(script_text, speakers)

        # Estimate duration (150 words per minute)
        total_words = sum(len(line.text.split()) for line in dialogue)
        duration_estimate = int((total_words / 150) * 60)  # seconds

        return PodcastScript(
            title=f"Medical Insight: {document.title}",
            description=f"A conversational overview of {document.title}",
            speakers=speakers,
            dialogue=dialogue,
            duration_estimate=duration_estimate,
            metadata={
                "document_id": document.id,
                "length": length.value,
                "style": style.value,
                "word_count": total_words,
            },
        )

    def generate_from_text(
        self,
        title: str,
        content: str,
        length: PodcastLength = PodcastLength.MEDIUM,
        style: PodcastStyle = PodcastStyle.PROFESSIONAL,
        speakers: Optional[list[Speaker]] = None,
    ) -> PodcastScript:
        """
        Generate a podcast script from raw text content.

        Args:
            title: Content title.
            content: Text content to create podcast from.
            length: Desired podcast length.
            style: Conversation style.
            speakers: Custom speakers.

        Returns:
            Generated podcast script.
        """
        speakers = speakers or self.DEFAULT_SPEAKERS
        target_words = self.LENGTH_WORD_COUNTS[length]

        logger.info(
            f"Generating podcast for '{title}' "
            f"(length={length.value}, style={style.value})"
        )

        # Generate the script using LLM
        script_text = self._generate_script_with_llm(
            document_title=title,
            document_content=content,
            target_words=target_words,
            style=style,
            speakers=speakers,
        )

        # Parse the script into dialogue lines
        dialogue = self._parse_script_to_dialogue(script_text, speakers)

        # Estimate duration
        total_words = sum(len(line.text.split()) for line in dialogue)
        duration_estimate = int((total_words / 150) * 60)

        return PodcastScript(
            title=f"Medical Insight: {title}",
            description=f"A conversational overview of {title}",
            speakers=speakers,
            dialogue=dialogue,
            duration_estimate=duration_estimate,
            metadata={
                "length": length.value,
                "style": style.value,
                "word_count": total_words,
            },
        )

    def _extract_document_summary(self, document: Document) -> str:
        """
        Extract a summary from the document for script generation.

        Retrieves actual document content from the vector store using the
        RAG pipeline to get the most relevant chunks.

        Args:
            document: Document to summarize.

        Returns:
            Document summary or content excerpt.
        """
        try:
            from src.retrieval import HybridRetriever

            # Initialize retriever
            retriever = HybridRetriever(use_reranker=False)

            # Query using document title to get relevant chunks
            results = retriever.search(
                query=document.title,
                top_k=5,  # Get top 5 chunks
                filter_conditions={"doc_id": document.id} if hasattr(document, 'id') else None,
            )

            # Extract text from results
            if results and len(results) > 0:
                content_parts = [
                    f"Title: {document.title}",
                    f"Type: {document.doc_type}",
                    f"Source: {document.source}",
                    "",
                    "Content Summary:",
                ]

                # Add chunk texts
                for i, result in enumerate(results[:5], 1):
                    if hasattr(result, 'text'):
                        content_parts.append(f"\n[Section {i}]")
                        content_parts.append(result.text[:500])  # Limit chunk size

                return "\n".join(content_parts)

        except Exception as e:
            logger.warning(f"Could not retrieve document content: {e}, using metadata")

        # Fallback to metadata if retrieval fails
        summary_parts = [
            f"Title: {document.title}",
            f"Type: {document.doc_type}",
            f"Source: {document.source}",
        ]

        if document.metadata:
            summary_parts.append(f"Additional info: {document.metadata}")

        return "\n".join(summary_parts)

    def _generate_script_with_llm(
        self,
        document_title: str,
        document_content: str,
        target_words: int,
        style: PodcastStyle,
        speakers: list[Speaker],
    ) -> str:
        """
        Generate the podcast script using an LLM.

        Args:
            document_title: Title of the document.
            document_content: Content to discuss.
            target_words: Target word count.
            style: Conversation style.
            speakers: List of speakers.

        Returns:
            Raw script text.
        """
        # Build the prompt
        prompt = self._build_script_prompt(
            document_title, document_content, target_words, style, speakers
        )

        # Generate using best available LLM
        if self.prefer_local or not settings.has_cloud_llm:
            script_text = self._generate_with_ollama(prompt)
        elif self.anthropic_client:
            script_text = self._generate_with_anthropic(prompt)
        elif self.openai_client:
            script_text = self._generate_with_openai(prompt)
        else:
            script_text = self._generate_with_ollama(prompt)

        return script_text

    def _build_script_prompt(
        self,
        document_title: str,
        document_content: str,
        target_words: int,
        style: PodcastStyle,
        speakers: list[Speaker],
    ) -> str:
        """Build the prompt for script generation."""
        speaker_names = [s.name for s in speakers]

        style_guidance = {
            PodcastStyle.CASUAL: "conversational and friendly, using analogies and relatable examples",
            PodcastStyle.PROFESSIONAL: "professional yet accessible, balancing accuracy with clarity",
            PodcastStyle.TEACHING: "pedagogical and explanatory, breaking down complex concepts step-by-step",
        }

        style_desc = style_guidance.get(style, style_guidance[PodcastStyle.PROFESSIONAL])

        prompt = f"""You are writing a podcast script for a medical education show. Create an engaging, conversational dialogue between {speaker_names[0]} and {speaker_names[1]} discussing the following medical content.

CONTENT TO DISCUSS:
Title: {document_title}
{document_content}

REQUIREMENTS:
1. Target length: ~{target_words} words
2. Style: {style_desc}
3. Format as natural dialogue with speaker labels (e.g., "{speaker_names[0]}: ...")
4. Include:
   - Engaging opening hook
   - Key points from the content
   - Real-world clinical relevance
   - Natural transitions and questions
   - Memorable takeaways
   - Clear closing summary

5. Make it sound like NotebookLM:
   - Natural interruptions and agreements ("Right!", "Exactly", "That's interesting...")
   - Questions that anticipate listener confusion
   - Analogies and examples for complex concepts
   - Enthusiasm for the topic
   - Periodic recaps of key points

6. CRITICAL: This is for physician education, maintain medical accuracy but make it engaging

SCRIPT FORMAT:
{speaker_names[0]}: [Opening dialogue]
{speaker_names[1]}: [Response]
{speaker_names[0]}: [Continues...]
...

Begin the script now:"""

        return prompt

    def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate script using Claude."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            # Fallback to local
            return self._generate_with_ollama(prompt)

    def _generate_with_openai(self, prompt: str) -> str:
        """Generate script using GPT-4."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            # Fallback to local
            return self._generate_with_ollama(prompt)

    def _generate_with_ollama(self, prompt: str) -> str:
        """Generate script using local Ollama."""
        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            # Return a fallback script
            return self._generate_fallback_script()

    def _generate_fallback_script(self) -> str:
        """Generate a simple fallback script when all LLMs fail."""
        return """Dr. Sarah: Welcome to today's medical insight session.
Dr. Michael: Thanks for having me. What are we discussing today?
Dr. Sarah: We're exploring an important medical topic that physicians need to understand.
Dr. Michael: That sounds fascinating. Can you give us the key points?
Dr. Sarah: Absolutely. The main takeaways are evidence-based and clinically relevant.
Dr. Michael: Great summary. Any final thoughts?
Dr. Sarah: Remember to always verify information before clinical decisions. Thanks for listening!"""

    def _parse_script_to_dialogue(
        self, script_text: str, speakers: list[Speaker]
    ) -> list[DialogueLine]:
        """
        Parse raw script text into structured dialogue lines.

        Args:
            script_text: Raw script from LLM.
            speakers: List of speakers.

        Returns:
            List of dialogue lines.
        """
        dialogue = []
        speaker_names = {s.name for s in speakers}

        # Split into lines
        lines = script_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for speaker label (e.g., "Dr. Sarah: ..." or "Sarah: ...")
            for speaker_name in speaker_names:
                if line.startswith(f"{speaker_name}:"):
                    text = line[len(speaker_name) + 1 :].strip()
                    dialogue.append(
                        DialogueLine(
                            speaker=speaker_name,
                            text=text,
                        )
                    )
                    break

        # If no dialogue was parsed, try a more lenient approach
        if not dialogue:
            logger.warning("Failed to parse dialogue with strict format, trying lenient parsing")
            dialogue = self._parse_script_lenient(script_text, speakers)

        return dialogue

    def _parse_script_lenient(
        self, script_text: str, speakers: list[Speaker]
    ) -> list[DialogueLine]:
        """
        Lenient parsing when strict format fails.

        Alternates speakers for each paragraph.
        """
        dialogue = []
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            speaker = speakers[i % len(speakers)]
            # Remove any speaker labels
            text = paragraph
            for s in speakers:
                text = text.replace(f"{s.name}:", "").strip()

            dialogue.append(
                DialogueLine(
                    speaker=speaker.name,
                    text=text,
                )
            )

        return dialogue

    def export_script_text(self, script: PodcastScript) -> str:
        """
        Export script as plain text.

        Args:
            script: Podcast script.

        Returns:
            Formatted text script.
        """
        lines = [
            f"# {script.title}",
            f"{script.description}",
            "",
            f"Duration: ~{script.duration_estimate // 60} minutes",
            "",
            "---",
            "",
        ]

        for line in script.dialogue:
            lines.append(f"{line.speaker}: {line.text}")
            lines.append("")

        return "\n".join(lines)
