"""
AI-Powered News Summarization Module

Generates concise summaries, extracts key findings, and highlights
clinical implications using LLM.
"""

import logging
from typing import Optional

from src.llm import MedicalSynthesizer
from .models import NewsArticle, NewsCategory

logger = logging.getLogger(__name__)


class NewsSummarizer:
    """AI-powered summarization for medical news."""

    def __init__(self, synthesizer: Optional[MedicalSynthesizer] = None):
        self.synthesizer = synthesizer or MedicalSynthesizer()

    async def summarize_article(
        self,
        article: NewsArticle,
        max_sentences: int = 3,
    ) -> str:
        """
        Generate concise summary of article.

        Args:
            article: News article to summarize
            max_sentences: Maximum sentences in summary

        Returns:
            Brief summary (2-3 sentences)
        """
        try:
            prompt = f"""Summarize this medical news article in {max_sentences} clear, concise sentences.
Focus on the most important clinical information.

Title: {article.title}

Content: {article.full_text or article.summary}

Provide only the summary, no preamble."""

            summary = await self.synthesizer.synthesize(
                query=prompt,
                context=[],
                max_tokens=200,
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            # Fallback to existing summary
            return article.summary[:300] if article.summary else article.title

    async def extract_key_findings(
        self,
        article: NewsArticle,
        max_findings: int = 5,
    ) -> list[str]:
        """
        Extract key findings as bullet points.

        Args:
            article: News article
            max_findings: Maximum number of findings

        Returns:
            List of key findings (3-5 bullet points)
        """
        try:
            prompt = f"""Extract the {max_findings} most important key findings from this medical article.
Present them as clear, concise bullet points (each 1-2 sentences).
Focus on clinical data, results, and actionable information.

Title: {article.title}

Content: {article.full_text or article.summary}

Provide only the bullet points, one per line, without bullet symbols."""

            response = await self.synthesizer.synthesize(
                query=prompt,
                context=[],
                max_tokens=300,
            )

            # Parse bullet points
            findings = [
                line.strip()
                for line in response.strip().split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            # Clean up and limit
            findings = [
                f.lstrip("- •*").strip()
                for f in findings
                if f.strip()
            ][:max_findings]

            return findings

        except Exception as e:
            logger.error(f"Error extracting key findings: {e}")
            return article.key_findings if article.key_findings else []

    async def generate_clinical_implications(
        self,
        article: NewsArticle,
    ) -> str:
        """
        Generate "What this means for your practice" summary.

        Args:
            article: News article

        Returns:
            Clinical implications summary
        """
        try:
            specialty_context = ""
            if article.specialty:
                specialties = ", ".join(article.specialty[:3])
                specialty_context = f"\nRelevant specialties: {specialties}"

            prompt = f"""Explain what this medical news means for clinical practice.
Write a brief paragraph (2-4 sentences) explaining:
1. How this changes or confirms current practice
2. What actions clinicians should consider
3. Any important caveats or limitations{specialty_context}

Title: {article.title}

Summary: {article.summary}

Key Findings:
{chr(10).join('- ' + f for f in article.key_findings)}

Provide only the clinical implications paragraph, no preamble."""

            implications = await self.synthesizer.synthesize(
                query=prompt,
                context=[],
                max_tokens=250,
            )

            return implications.strip()

        except Exception as e:
            logger.error(f"Error generating clinical implications: {e}")
            return article.clinical_implications or ""

    async def estimate_reading_time(
        self,
        article: NewsArticle,
        words_per_minute: int = 200,
    ) -> int:
        """
        Estimate reading time in minutes.

        Args:
            article: News article
            words_per_minute: Average reading speed

        Returns:
            Estimated reading time in minutes
        """
        # Count words in full text or summary
        text = article.full_text or article.summary
        word_count = len(text.split())

        # Calculate reading time (minimum 1 minute)
        reading_time = max(1, round(word_count / words_per_minute))

        return reading_time

    async def generate_headline(
        self,
        article: NewsArticle,
        max_words: int = 12,
    ) -> str:
        """
        Generate attention-grabbing headline.

        Args:
            article: News article
            max_words: Maximum words in headline

        Returns:
            Engaging headline
        """
        try:
            prompt = f"""Create an engaging, accurate headline for this medical news article.
Requirements:
- Maximum {max_words} words
- Clear and informative
- Appropriate for medical professionals
- Focus on the key finding or implication

Original title: {article.title}

Summary: {article.summary[:200]}

Provide only the headline, no quotes or preamble."""

            headline = await self.synthesizer.synthesize(
                query=prompt,
                context=[],
                max_tokens=50,
            )

            return headline.strip().strip('"\'')

        except Exception as e:
            logger.error(f"Error generating headline: {e}")
            return article.title

    async def enrich_article(
        self,
        article: NewsArticle,
        include_implications: bool = True,
        include_key_findings: bool = True,
    ) -> NewsArticle:
        """
        Enrich article with AI-generated content.

        Args:
            article: Original news article
            include_implications: Generate clinical implications
            include_key_findings: Extract key findings

        Returns:
            Enriched article with summaries and insights
        """
        try:
            # Generate summary if not present or too long
            if not article.summary or len(article.summary) > 500:
                article.summary = await self.summarize_article(article)

            # Extract key findings if requested and not present
            if include_key_findings and not article.key_findings:
                article.key_findings = await self.extract_key_findings(article)

            # Generate clinical implications if requested and not present
            if include_implications and not article.clinical_implications:
                article.clinical_implications = await self.generate_clinical_implications(article)

            # Estimate reading time
            article.reading_time_minutes = await self.estimate_reading_time(article)

            logger.info(f"Enriched article: {article.title[:50]}...")
            return article

        except Exception as e:
            logger.error(f"Error enriching article: {e}")
            return article

    async def generate_category_summary(
        self,
        articles: list[NewsArticle],
        category: NewsCategory,
    ) -> str:
        """
        Generate summary of multiple articles in a category.

        Args:
            articles: List of articles in category
            category: News category

        Returns:
            Summary of trends and highlights
        """
        try:
            if not articles:
                return f"No recent {category.value} updates."

            # Prepare article summaries
            article_summaries = []
            for i, article in enumerate(articles[:5], 1):
                summary = f"{i}. {article.title}"
                if article.key_findings:
                    summary += f" - {article.key_findings[0]}"
                article_summaries.append(summary)

            prompt = f"""Summarize the key themes and trends from these recent {category.value} articles.
Write 2-3 sentences highlighting:
1. Main themes or patterns
2. Most significant developments
3. Overall clinical significance

Articles:
{chr(10).join(article_summaries)}

Provide only the summary paragraph, no preamble."""

            summary = await self.synthesizer.synthesize(
                query=prompt,
                context=[],
                max_tokens=200,
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"Error generating category summary: {e}")
            return f"{len(articles)} recent articles in {category.value}."

    async def generate_daily_digest_intro(
        self,
        articles_by_category: dict[NewsCategory, list[NewsArticle]],
        specialty: Optional[str] = None,
    ) -> str:
        """
        Generate introduction for daily news digest.

        Args:
            articles_by_category: Articles grouped by category
            specialty: User's specialty

        Returns:
            Digest introduction
        """
        try:
            total_articles = sum(len(articles) for articles in articles_by_category.values())

            if total_articles == 0:
                return "No new medical news updates today."

            # Count articles by category
            category_counts = [
                f"{len(articles)} {category.value}"
                for category, articles in articles_by_category.items()
                if articles
            ]

            specialty_text = f" in {specialty}" if specialty else ""

            intro = f"Good morning! Here are {total_articles} important medical updates{specialty_text}: "
            intro += ", ".join(category_counts[:3])

            if len(category_counts) > 3:
                intro += f", and {len(category_counts) - 3} more categories"

            intro += "."

            return intro

        except Exception as e:
            logger.error(f"Error generating digest intro: {e}")
            return "Here are today's medical news updates."

    def generate_plain_summary(
        self,
        article: NewsArticle,
        max_length: int = 200,
    ) -> str:
        """
        Generate plain text summary without AI (fallback).

        Args:
            article: News article
            max_length: Maximum character length

        Returns:
            Plain summary
        """
        # Use existing summary or create from title and first finding
        if article.summary:
            summary = article.summary
        elif article.key_findings:
            summary = f"{article.title}. {article.key_findings[0]}"
        else:
            summary = article.title

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."

        return summary

    async def batch_summarize(
        self,
        articles: list[NewsArticle],
        include_implications: bool = True,
    ) -> list[NewsArticle]:
        """
        Summarize multiple articles in batch.

        Args:
            articles: List of articles to summarize
            include_implications: Include clinical implications

        Returns:
            List of enriched articles
        """
        enriched = []

        for article in articles:
            try:
                enriched_article = await self.enrich_article(
                    article,
                    include_implications=include_implications,
                )
                enriched.append(enriched_article)
            except Exception as e:
                logger.error(f"Error in batch summarization: {e}")
                enriched.append(article)

        return enriched


async def get_news_summarizer() -> NewsSummarizer:
    """Get news summarizer instance."""
    return NewsSummarizer()
