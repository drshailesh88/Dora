"""
AI-Assisted Academic Writing

Provides AI assistance for writing medical research papers.
Generates structured abstracts, methods, results sections, and more.
"""

from typing import Optional

from src.core.config import settings
from .models import (
    Manuscript,
    ManuscriptSection,
    StudyType,
    WritingPrompt,
    WritingResult,
)


class AcademicWritingAssistant:
    """
    AI assistant for academic medical writing.

    Features:
    - Generate structured abstracts
    - Draft methodology sections
    - Format results sections
    - Suggest improvements
    - Check for common issues
    """

    def __init__(self, prefer_local: bool = False):
        """
        Initialize writing assistant.

        Args:
            prefer_local: Prefer local LLM over cloud
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

    async def generate_abstract(
        self,
        title: str,
        study_type: StudyType,
        context: dict,
        max_words: int = 250,
        structured: bool = True,
    ) -> WritingResult:
        """
        Generate a structured abstract.

        Args:
            title: Paper title
            study_type: Type of study
            context: Context with findings, methods, etc.
            max_words: Maximum word count
            structured: Whether to use structured format

        Returns:
            Writing result with generated abstract
        """
        if structured:
            prompt = self._build_structured_abstract_prompt(
                title, study_type, context, max_words
            )
        else:
            prompt = self._build_unstructured_abstract_prompt(
                title, study_type, context, max_words
            )

        content = await self._generate(prompt)
        word_count = len(content.split())

        warnings = []
        if word_count > max_words:
            warnings.append(f"Abstract exceeds {max_words} words ({word_count} words)")

        suggestions = [
            "Review for clarity and conciseness",
            "Ensure all key findings are included",
            "Check that conclusions are supported by results",
        ]

        return WritingResult(
            section=ManuscriptSection.ABSTRACT,
            content=content,
            word_count=word_count,
            suggestions=suggestions,
            warnings=warnings,
        )

    async def generate_methods(
        self,
        study_type: StudyType,
        context: dict,
        max_words: Optional[int] = None,
    ) -> WritingResult:
        """
        Generate methodology section.

        Args:
            study_type: Type of study
            context: Context with study details
            max_words: Maximum word count

        Returns:
            Writing result with methods section
        """
        prompt = self._build_methods_prompt(study_type, context, max_words)
        content = await self._generate(prompt)
        word_count = len(content.split())

        suggestions = [
            "Ensure all procedures are described in sufficient detail",
            "Include statistical methods used",
            "Mention ethical approval and consent",
        ]

        warnings = []
        if "ethical approval" not in content.lower():
            warnings.append("Consider adding ethical approval statement")
        if "statistical" not in content.lower():
            warnings.append("Consider adding statistical analysis methods")

        return WritingResult(
            section=ManuscriptSection.METHODS,
            content=content,
            word_count=word_count,
            suggestions=suggestions,
            warnings=warnings,
        )

    async def generate_results(
        self,
        context: dict,
        max_words: Optional[int] = None,
    ) -> WritingResult:
        """
        Generate results section.

        Args:
            context: Context with study results, tables, figures
            max_words: Maximum word count

        Returns:
            Writing result with results section
        """
        prompt = self._build_results_prompt(context, max_words)
        content = await self._generate(prompt)
        word_count = len(content.split())

        suggestions = [
            "Present results objectively without interpretation",
            "Reference all tables and figures",
            "Report exact p-values where appropriate",
        ]

        warnings = []
        if max_words and word_count > max_words:
            warnings.append(f"Results section may be too long ({word_count} words)")

        return WritingResult(
            section=ManuscriptSection.RESULTS,
            content=content,
            word_count=word_count,
            suggestions=suggestions,
            warnings=warnings,
        )

    async def generate_discussion(
        self,
        context: dict,
        max_words: Optional[int] = None,
    ) -> WritingResult:
        """
        Generate discussion section.

        Args:
            context: Context with results, implications, limitations
            max_words: Maximum word count

        Returns:
            Writing result with discussion section
        """
        prompt = self._build_discussion_prompt(context, max_words)
        content = await self._generate(prompt)
        word_count = len(content.split())

        suggestions = [
            "Compare findings with existing literature",
            "Discuss study limitations",
            "Suggest directions for future research",
        ]

        warnings = []
        if "limitation" not in content.lower():
            warnings.append("Consider adding study limitations")

        return WritingResult(
            section=ManuscriptSection.DISCUSSION,
            content=content,
            word_count=word_count,
            suggestions=suggestions,
            warnings=warnings,
        )

    async def improve_section(
        self,
        section: ManuscriptSection,
        current_text: str,
        improvement_type: str = "clarity",
    ) -> WritingResult:
        """
        Suggest improvements for a section.

        Args:
            section: Section being improved
            current_text: Current section text
            improvement_type: Type of improvement (clarity, conciseness, grammar)

        Returns:
            Writing result with improved text
        """
        prompt = self._build_improvement_prompt(
            section, current_text, improvement_type
        )
        content = await self._generate(prompt)
        word_count = len(content.split())

        return WritingResult(
            section=section,
            content=content,
            word_count=word_count,
            suggestions=[],
            warnings=[],
        )

    def check_plagiarism_indicators(self, text: str) -> list[str]:
        """
        Check for potential plagiarism indicators.

        Args:
            text: Text to check

        Returns:
            List of warnings about potential issues
        """
        warnings = []

        # Check for overly long direct quotes
        if '"' in text:
            quote_count = text.count('"') // 2
            if quote_count > 3:
                warnings.append(
                    f"Contains {quote_count} quoted passages - ensure proper citation"
                )

        # Check for suspiciously formal language (simple heuristic)
        formal_markers = [
            "heretofore", "aforementioned", "pursuant to",
            "notwithstanding", "ipso facto"
        ]
        found_markers = [m for m in formal_markers if m in text.lower()]
        if len(found_markers) > 2:
            warnings.append(
                "Contains unusually formal language - review for originality"
            )

        # Check for proper citation markers
        if "[1]" not in text and "(" not in text:
            if len(text.split()) > 100:
                warnings.append(
                    "Long section without citations - ensure proper referencing"
                )

        return warnings

    def format_table_description(
        self,
        table_data: dict,
        table_number: int,
    ) -> str:
        """
        Generate description for a table.

        Args:
            table_data: Dictionary with table information
            table_number: Table number

        Returns:
            Formatted table description
        """
        title = table_data.get("title", f"Table {table_number}")
        caption = table_data.get("caption", "")

        description = f"Table {table_number}: {title}\n"
        if caption:
            description += f"{caption}\n"

        return description

    def format_figure_description(
        self,
        figure_data: dict,
        figure_number: int,
    ) -> str:
        """
        Generate description for a figure.

        Args:
            figure_data: Dictionary with figure information
            figure_number: Figure number

        Returns:
            Formatted figure description
        """
        title = figure_data.get("title", f"Figure {figure_number}")
        caption = figure_data.get("caption", "")

        description = f"Figure {figure_number}: {title}\n"
        if caption:
            description += f"{caption}\n"

        return description

    # Private methods for prompt building

    def _build_structured_abstract_prompt(
        self,
        title: str,
        study_type: StudyType,
        context: dict,
        max_words: int,
    ) -> str:
        """Build prompt for structured abstract."""
        return f"""Generate a structured abstract for a medical research paper.

Title: {title}
Study Type: {study_type.value}

Context:
{self._format_context(context)}

Requirements:
1. Use structured format with sections: Background, Methods, Results, Conclusions
2. Maximum {max_words} words total
3. Be specific and quantitative
4. Use past tense for completed work
5. Do not include citations in abstract

Generate the structured abstract:"""

    def _build_unstructured_abstract_prompt(
        self,
        title: str,
        study_type: StudyType,
        context: dict,
        max_words: int,
    ) -> str:
        """Build prompt for unstructured abstract."""
        return f"""Generate an unstructured abstract for a medical research paper.

Title: {title}
Study Type: {study_type.value}

Context:
{self._format_context(context)}

Requirements:
1. Single paragraph format
2. Maximum {max_words} words
3. Cover background, methods, results, and conclusions
4. Be specific and quantitative
5. Use past tense for completed work

Generate the abstract:"""

    def _build_methods_prompt(
        self,
        study_type: StudyType,
        context: dict,
        max_words: Optional[int],
    ) -> str:
        """Build prompt for methods section."""
        word_limit = f"Maximum {max_words} words." if max_words else ""

        return f"""Generate a methods section for a medical research paper.

Study Type: {study_type.value}

Context:
{self._format_context(context)}

Requirements:
1. Describe study design, setting, participants
2. Detail data collection and measurement methods
3. Explain statistical analysis
4. Mention ethical approval
5. Use past tense
6. Be specific and reproducible
{word_limit}

Generate the methods section:"""

    def _build_results_prompt(
        self,
        context: dict,
        max_words: Optional[int],
    ) -> str:
        """Build prompt for results section."""
        word_limit = f"Maximum {max_words} words." if max_words else ""

        return f"""Generate a results section for a medical research paper.

Context:
{self._format_context(context)}

Requirements:
1. Present findings objectively
2. Reference tables and figures
3. Report statistical values (p-values, CIs, etc.)
4. Use past tense
5. Do not interpret results (save for Discussion)
{word_limit}

Generate the results section:"""

    def _build_discussion_prompt(
        self,
        context: dict,
        max_words: Optional[int],
    ) -> str:
        """Build prompt for discussion section."""
        word_limit = f"Maximum {max_words} words." if max_words else ""

        return f"""Generate a discussion section for a medical research paper.

Context:
{self._format_context(context)}

Requirements:
1. Interpret the findings
2. Compare with existing literature
3. Discuss limitations
4. Explain clinical implications
5. Suggest future research directions
{word_limit}

Generate the discussion section:"""

    def _build_improvement_prompt(
        self,
        section: ManuscriptSection,
        current_text: str,
        improvement_type: str,
    ) -> str:
        """Build prompt for text improvement."""
        return f"""Improve the following {section.value} section for {improvement_type}.

Current text:
{current_text}

Requirements:
1. Maintain the original meaning and findings
2. Improve {improvement_type}
3. Use appropriate academic tone
4. Preserve all citations
5. Keep approximately the same length

Generate improved version:"""

    def _format_context(self, context: dict) -> str:
        """Format context dictionary as text."""
        formatted = []
        for key, value in context.items():
            formatted.append(f"{key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)

    async def _generate(self, prompt: str) -> str:
        """Generate text using best available LLM."""
        if self.prefer_local or not settings.has_cloud_llm:
            return self._generate_local(prompt)
        elif self.anthropic_client:
            return self._generate_anthropic(prompt)
        elif self.openai_client:
            return self._generate_openai(prompt)
        else:
            return self._generate_local(prompt)

    def _generate_anthropic(self, prompt: str) -> str:
        """Generate using Claude."""
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _generate_openai(self, prompt: str) -> str:
        """Generate using GPT-4."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def _generate_local(self, prompt: str) -> str:
        """Generate using local Ollama."""
        try:
            response = self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            return response["response"]
        except Exception as e:
            return f"Error generating response: {str(e)}"


# Singleton instance
_writing_assistant: Optional[AcademicWritingAssistant] = None


def get_writing_assistant(prefer_local: bool = False) -> AcademicWritingAssistant:
    """Get the default writing assistant instance."""
    global _writing_assistant
    if _writing_assistant is None:
        _writing_assistant = AcademicWritingAssistant(prefer_local=prefer_local)
    return _writing_assistant
