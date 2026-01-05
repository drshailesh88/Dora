"""
Change Summarizer

Generates AI-powered summaries of document comparison results,
including clinical implications and recommendations.
"""

import logging
from typing import Optional

from src.core.config import settings

from .models import (
    ChangeType,
    ComparisonResult,
    ComparisonSummary,
)

logger = logging.getLogger(__name__)


class ChangeSummarizer:
    """
    Generate human-readable summaries of document changes.

    Uses LLM to produce:
    - Overall change summary
    - Key changes list
    - Clinical implications
    - Recommendations
    """

    def __init__(self, prefer_local: bool = False):
        """
        Initialize summarizer.

        Args:
            prefer_local: Prefer local LLM
        """
        self.prefer_local = prefer_local
        self._anthropic_client = None
        self._openai_client = None

        logger.info(f"Initialized ChangeSummarizer (prefer_local={prefer_local})")

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

    async def summarize(
        self,
        comparison: ComparisonResult,
        focus_areas: Optional[list[str]] = None,
    ) -> ComparisonSummary:
        """
        Generate summary of comparison.

        Args:
            comparison: Comparison result to summarize
            focus_areas: Specific areas to focus on

        Returns:
            ComparisonSummary
        """
        logger.info(
            f"Summarizing comparison: {comparison.total_changes} changes"
        )

        # Build prompt
        prompt = self._build_summary_prompt(comparison, focus_areas)

        # Generate summary
        model_used = "unknown"

        if self.prefer_local or not settings.has_cloud_llm:
            summary_text = await self._summarize_with_ollama(prompt)
            model_used = settings.ollama_model
        elif self.anthropic_client:
            summary_text = await self._summarize_with_anthropic(prompt)
            model_used = "claude-3-5-sonnet-20241022"
        elif self.openai_client:
            summary_text = await self._summarize_with_openai(prompt)
            model_used = "gpt-4o"
        else:
            summary_text = await self._summarize_with_ollama(prompt)
            model_used = settings.ollama_model

        # Parse summary
        summary = self._parse_summary(summary_text, comparison, model_used)

        comparison.summary = summary
        return summary

    def _build_summary_prompt(
        self,
        comparison: ComparisonResult,
        focus_areas: Optional[list[str]] = None,
    ) -> str:
        """Build prompt for summary generation."""
        # Prepare changes summary
        changes_by_type = {
            "added": [],
            "removed": [],
            "modified": [],
        }

        for change in comparison.changes[:30]:  # Limit for prompt
            change_desc = self._describe_change(change)
            changes_by_type[change.type.value].append(change_desc)

        # Prepare semantic groups
        groups_text = ""
        if comparison.semantic_groups:
            groups_text = "\n".join(
                f"- {g.category}: {g.summary}"
                for g in comparison.semantic_groups[:10]
            )

        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\nFocus particularly on: {', '.join(focus_areas)}"

        return f"""Summarize the following changes between two medical documents for a physician audience.

DOCUMENT COMPARISON:
From: {comparison.left_document.title}
To: {comparison.right_document.title}

STATISTICS:
- Total changes: {comparison.total_changes}
- Additions: {comparison.additions}
- Removals: {comparison.deletions}
- Modifications: {comparison.modifications}

SEMANTIC GROUPS:
{groups_text}

KEY CHANGES:
Additions:
{chr(10).join(f'- {c}' for c in changes_by_type['added'][:5]) or '(none)'}

Removals:
{chr(10).join(f'- {c}' for c in changes_by_type['removed'][:5]) or '(none)'}

Modifications:
{chr(10).join(f'- {c}' for c in changes_by_type['modified'][:5]) or '(none)'}
{focus_instruction}

Please provide:
1. OVERALL SUMMARY: A 2-3 sentence overview of the changes
2. KEY CHANGES: List the 3-5 most important changes
3. CLINICAL IMPLICATIONS: What do these changes mean for clinical practice?
4. RISK LEVEL: Overall risk level (high/medium/low/none) based on the nature of changes
5. RECOMMENDATIONS: Actionable recommendations for practitioners

Format your response with clear section headers."""

    def _describe_change(self, change) -> str:
        """Create brief description of a change."""
        if change.type == ChangeType.ADDED:
            text = (change.right_text or "")[:100]
            return f"Added: {text}..."
        elif change.type == ChangeType.REMOVED:
            text = (change.left_text or "")[:100]
            return f"Removed: {text}..."
        else:
            left = (change.left_text or "")[:50]
            right = (change.right_text or "")[:50]
            return f"Changed: '{left}...' → '{right}...'"

    async def _summarize_with_anthropic(self, prompt: str) -> str:
        """Summarize using Claude."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic summarization failed: {e}")
            return self._generate_fallback_summary()

    async def _summarize_with_openai(self, prompt: str) -> str:
        """Summarize using GPT-4."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            return self._generate_fallback_summary()

    async def _summarize_with_ollama(self, prompt: str) -> str:
        """Summarize using local Ollama."""
        try:
            import ollama
            client = ollama.Client(host=settings.ollama_base_url)
            response = client.generate(
                model=settings.ollama_model,
                prompt=prompt,
            )
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama summarization failed: {e}")
            return self._generate_fallback_summary()

    def _generate_fallback_summary(self) -> str:
        """Generate basic fallback summary when LLM fails."""
        return """OVERALL SUMMARY:
Document changes detected. Manual review recommended.

KEY CHANGES:
- Multiple changes detected in the document
- Please review the detailed diff for specifics

CLINICAL IMPLICATIONS:
- Review required to assess clinical impact

RISK LEVEL: medium

RECOMMENDATIONS:
- Carefully review all changes before clinical application
- Consult with colleagues if changes affect treatment protocols"""

    def _parse_summary(
        self,
        summary_text: str,
        comparison: ComparisonResult,
        model_used: str,
    ) -> ComparisonSummary:
        """Parse LLM response into ComparisonSummary."""
        # Extract sections
        overall = self._extract_section(summary_text, "OVERALL SUMMARY", "KEY CHANGES")
        key_changes = self._extract_list(summary_text, "KEY CHANGES", "CLINICAL")
        implications = self._extract_list(summary_text, "CLINICAL IMPLICATIONS", "RISK")
        risk = self._extract_section(summary_text, "RISK LEVEL", "RECOMMENDATIONS")
        recommendations = self._extract_list(summary_text, "RECOMMENDATIONS", None)

        # Parse risk level
        risk_level = "medium"
        risk_lower = risk.lower()
        if "high" in risk_lower:
            risk_level = "high"
        elif "low" in risk_lower:
            risk_level = "low"
        elif "none" in risk_lower:
            risk_level = "none"

        return ComparisonSummary(
            overall_summary=overall or f"Comparison shows {comparison.total_changes} changes.",
            key_changes=key_changes or [f"{comparison.total_changes} total changes detected"],
            clinical_implications=implications or ["Review recommended"],
            risk_level=risk_level,
            recommendations=recommendations or ["Review all changes carefully"],
            model_used=model_used,
        )

    def _extract_section(
        self,
        text: str,
        start_marker: str,
        end_marker: Optional[str],
    ) -> str:
        """Extract section between markers."""
        try:
            start_idx = text.upper().find(start_marker.upper())
            if start_idx == -1:
                return ""

            start_idx = text.find("\n", start_idx) + 1

            if end_marker:
                end_idx = text.upper().find(end_marker.upper(), start_idx)
                if end_idx == -1:
                    end_idx = len(text)
            else:
                end_idx = len(text)

            return text[start_idx:end_idx].strip()

        except Exception:
            return ""

    def _extract_list(
        self,
        text: str,
        start_marker: str,
        end_marker: Optional[str],
    ) -> list[str]:
        """Extract bullet list from section."""
        section = self._extract_section(text, start_marker, end_marker)
        if not section:
            return []

        items = []
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                items.append(line[1:].strip())
            elif line and line[0].isdigit() and "." in line[:3]:
                items.append(line.split(".", 1)[1].strip())

        return items
