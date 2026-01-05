"""
Semantic Document Diff Engine

Uses AI to detect and categorize semantically meaningful changes
in medical documents, particularly for guideline updates.
"""

import logging
import re
from typing import Optional

from src.core.config import settings

from .models import (
    ChangeType,
    ComparisonResult,
    DocumentChange,
    SemanticChangeGroup,
)

logger = logging.getLogger(__name__)


# Medical semantic categories
MEDICAL_CATEGORIES = {
    "dosage_change": {
        "keywords": ["mg", "dose", "dosage", "dosing", "titrate", "maximum", "minimum"],
        "description": "Medication dosage modification",
        "clinical_significance": "high",
    },
    "contraindication_change": {
        "keywords": ["contraindicated", "contraindication", "avoid", "not recommended", "caution"],
        "description": "Contraindication update",
        "clinical_significance": "high",
    },
    "indication_change": {
        "keywords": ["indicated", "indication", "approved", "use for", "treatment of"],
        "description": "Indication modification",
        "clinical_significance": "high",
    },
    "warning_change": {
        "keywords": ["warning", "black box", "adverse", "side effect", "risk", "serious"],
        "description": "Safety warning update",
        "clinical_significance": "high",
    },
    "monitoring_change": {
        "keywords": ["monitor", "monitoring", "test", "check", "measure", "assess"],
        "description": "Monitoring requirement change",
        "clinical_significance": "medium",
    },
    "recommendation_change": {
        "keywords": ["recommend", "recommendation", "guideline", "consensus", "grade"],
        "description": "Clinical recommendation update",
        "clinical_significance": "high",
    },
    "evidence_change": {
        "keywords": ["evidence", "study", "trial", "research", "data", "outcome"],
        "description": "Supporting evidence update",
        "clinical_significance": "medium",
    },
    "procedure_change": {
        "keywords": ["procedure", "protocol", "technique", "method", "approach", "step"],
        "description": "Procedural modification",
        "clinical_significance": "medium",
    },
    "formatting_change": {
        "keywords": [],
        "description": "Formatting or wording change",
        "clinical_significance": "low",
    },
}


class SemanticDiffEngine:
    """
    AI-powered semantic document comparison.

    Detects clinically meaningful changes and groups them
    into semantic categories for easier review.
    """

    def __init__(self, prefer_local: bool = False):
        """
        Initialize semantic diff engine.

        Args:
            prefer_local: Use local LLM for analysis
        """
        self.prefer_local = prefer_local
        self._anthropic_client = None
        self._openai_client = None
        self._ollama_client = None

        logger.info(f"Initialized SemanticDiffEngine (prefer_local={prefer_local})")

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

    def analyze_changes(
        self,
        comparison: ComparisonResult,
    ) -> ComparisonResult:
        """
        Analyze changes semantically.

        Args:
            comparison: Basic comparison result

        Returns:
            Enhanced comparison with semantic analysis
        """
        logger.info(f"Analyzing {len(comparison.changes)} changes semantically")

        # First, categorize changes using keyword matching
        for change in comparison.changes:
            category, significance = self._categorize_change(change)
            change.semantic_category = category
            change.clinical_significance = significance

        # Group related changes
        comparison.semantic_groups = self._group_changes(comparison.changes)

        return comparison

    def _categorize_change(
        self,
        change: DocumentChange,
    ) -> tuple[str, str]:
        """
        Categorize a change using keyword matching.

        Args:
            change: Change to categorize

        Returns:
            (category, clinical_significance)
        """
        text = (change.left_text or "") + " " + (change.right_text or "")
        text_lower = text.lower()

        # Check each category
        best_category = "formatting_change"
        best_score = 0

        for category, config in MEDICAL_CATEGORIES.items():
            keywords = config["keywords"]
            if not keywords:
                continue

            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_category = category

        significance = MEDICAL_CATEGORIES[best_category]["clinical_significance"]
        return best_category, significance

    def _group_changes(
        self,
        changes: list[DocumentChange],
    ) -> list[SemanticChangeGroup]:
        """
        Group related changes by category.

        Args:
            changes: List of changes

        Returns:
            List of semantic groups
        """
        # Group by category
        groups_dict: dict[str, list[DocumentChange]] = {}
        for change in changes:
            category = change.semantic_category or "other"
            if category not in groups_dict:
                groups_dict[category] = []
            groups_dict[category].append(change)

        # Create group objects
        groups = []
        for category, group_changes in groups_dict.items():
            if not group_changes:
                continue

            # Get category config
            config = MEDICAL_CATEGORIES.get(category, {})
            description = config.get("description", category.replace("_", " ").title())
            significance = config.get("clinical_significance", "medium")

            # Generate summary
            summary = self._generate_group_summary(category, group_changes)

            groups.append(
                SemanticChangeGroup(
                    category=description,
                    changes=group_changes,
                    summary=summary,
                    clinical_impact=significance,
                )
            )

        # Sort by clinical significance
        significance_order = {"high": 0, "medium": 1, "low": 2}
        groups.sort(key=lambda g: significance_order.get(g.clinical_impact or "medium", 1))

        return groups

    def _generate_group_summary(
        self,
        category: str,
        changes: list[DocumentChange],
    ) -> str:
        """Generate summary for a group of changes."""
        count = len(changes)
        additions = sum(1 for c in changes if c.type == ChangeType.ADDED)
        removals = sum(1 for c in changes if c.type == ChangeType.REMOVED)
        modifications = sum(1 for c in changes if c.type == ChangeType.MODIFIED)

        parts = []
        if additions:
            parts.append(f"{additions} addition{'s' if additions > 1 else ''}")
        if removals:
            parts.append(f"{removals} removal{'s' if removals > 1 else ''}")
        if modifications:
            parts.append(f"{modifications} modification{'s' if modifications > 1 else ''}")

        return f"{count} {category.replace('_', ' ')} change{'s' if count > 1 else ''}: {', '.join(parts)}"

    async def analyze_with_llm(
        self,
        comparison: ComparisonResult,
    ) -> ComparisonResult:
        """
        Deep semantic analysis using LLM.

        Args:
            comparison: Comparison to analyze

        Returns:
            Enhanced comparison with AI analysis
        """
        logger.info("Performing LLM-based semantic analysis")

        # Build prompt
        prompt = self._build_analysis_prompt(comparison)

        # Generate analysis
        if self.prefer_local or not settings.has_cloud_llm:
            analysis = await self._analyze_with_ollama(prompt)
        elif self.anthropic_client:
            analysis = await self._analyze_with_anthropic(prompt)
        elif self.openai_client:
            analysis = await self._analyze_with_openai(prompt)
        else:
            analysis = await self._analyze_with_ollama(prompt)

        # Parse and apply analysis
        self._apply_llm_analysis(comparison, analysis)

        return comparison

    def _build_analysis_prompt(self, comparison: ComparisonResult) -> str:
        """Build prompt for LLM analysis."""
        changes_text = []
        for i, change in enumerate(comparison.changes[:20]):  # Limit for prompt size
            left = (change.left_text or "")[:200]
            right = (change.right_text or "")[:200]
            changes_text.append(f"Change {i + 1} ({change.type.value}):\n  Old: {left}\n  New: {right}")

        return f"""Analyze the following changes between two medical documents and provide clinical insights.

Document: {comparison.left_document.title} -> {comparison.right_document.title}

CHANGES:
{chr(10).join(changes_text)}

For each change, identify:
1. Clinical significance (high/medium/low)
2. Category (dosage, contraindication, warning, recommendation, etc.)
3. Brief clinical impact assessment

Respond in a structured format."""

    async def _analyze_with_anthropic(self, prompt: str) -> str:
        """Analyze using Claude."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic analysis failed: {e}")
            return ""

    async def _analyze_with_openai(self, prompt: str) -> str:
        """Analyze using GPT-4."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return ""

    async def _analyze_with_ollama(self, prompt: str) -> str:
        """Analyze using local Ollama."""
        try:
            import ollama
            client = ollama.Client(host=settings.ollama_base_url)
            response = client.generate(model=settings.ollama_model, prompt=prompt)
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return ""

    def _apply_llm_analysis(self, comparison: ComparisonResult, analysis: str) -> None:
        """Apply LLM analysis results to comparison."""
        # Simple parsing - in production would use structured output
        if not analysis:
            return

        # Look for high significance indicators
        high_indicators = ["critical", "important", "significant", "urgent", "immediate"]
        for change in comparison.changes:
            for indicator in high_indicators:
                if indicator in analysis.lower():
                    if change.clinical_significance != "high":
                        change.clinical_significance = "medium"
