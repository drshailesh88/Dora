"""
News Feed Personalization Module

Personalizes news feed based on user preferences, specialty, reading behavior,
and engagement patterns.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from .models import (
    NewsArticle,
    NewsCategory,
    NewsEngagement,
    NewsSource,
    UserPreference,
)

logger = logging.getLogger(__name__)


class NewsPersonalizer:
    """Personalize news feed for individual users."""

    def __init__(self):
        self.min_relevance_score = 0.3
        self.decay_factor = 0.95  # Daily decay for trending

    def calculate_relevance_score(
        self,
        article: NewsArticle,
        preferences: UserPreference,
        engagement_history: Optional[list[NewsEngagement]] = None,
    ) -> float:
        """
        Calculate relevance score for an article based on user preferences.

        Args:
            article: News article
            preferences: User preferences
            engagement_history: Optional engagement history

        Returns:
            Relevance score (0-1)
        """
        score = 0.0

        # 1. Specialty matching (40% weight)
        specialty_score = self._calculate_specialty_score(article, preferences)
        score += specialty_score * 0.4

        # 2. Category preference (20% weight)
        category_score = self._calculate_category_score(article, preferences)
        score += category_score * 0.2

        # 3. Source credibility (15% weight)
        source_score = article.source.credibility_score
        score += source_score * 0.15

        # 4. Keywords matching (15% weight)
        keyword_score = self._calculate_keyword_score(article, preferences)
        score += keyword_score * 0.15

        # 5. Recency (10% weight)
        recency_score = self._calculate_recency_score(article)
        score += recency_score * 0.1

        # Boost if user has engaged with similar content
        if engagement_history:
            engagement_boost = self._calculate_engagement_boost(
                article, engagement_history
            )
            score = min(1.0, score * (1 + engagement_boost * 0.2))

        return min(1.0, max(0.0, score))

    def _calculate_specialty_score(
        self,
        article: NewsArticle,
        preferences: UserPreference,
    ) -> float:
        """Calculate specialty matching score."""
        if not article.specialty:
            return 0.5  # Neutral for untagged articles

        # Check primary specialty
        if preferences.primary_specialty.lower() in [
            s.lower() for s in article.specialty
        ]:
            return 1.0

        # Check sub-specialties
        if any(
            sub.lower() in [s.lower() for s in article.specialty]
            for sub in preferences.sub_specialties
        ):
            return 0.8

        # Check additional interests
        if any(
            interest.lower() in [s.lower() for s in article.specialty]
            for interest in preferences.additional_interests
        ):
            return 0.6

        return 0.2

    def _calculate_category_score(
        self,
        article: NewsArticle,
        preferences: UserPreference,
    ) -> float:
        """Calculate category preference score."""
        category_weight = preferences.category_weights.get(
            article.category.value, 3
        )
        # Normalize from 1-5 scale to 0-1 scale
        return (category_weight - 1) / 4.0

    def _calculate_keyword_score(
        self,
        article: NewsArticle,
        preferences: UserPreference,
    ) -> float:
        """Calculate keyword matching score."""
        if not preferences.keywords:
            return 0.5  # Neutral if no keywords set

        # Check title and keywords
        article_text = (
            article.title.lower()
            + " "
            + " ".join(article.keywords).lower()
        )

        matches = sum(
            1 for keyword in preferences.keywords
            if keyword.lower() in article_text
        )

        if not preferences.keywords:
            return 0.5

        return min(1.0, matches / len(preferences.keywords))

    def _calculate_recency_score(self, article: NewsArticle) -> float:
        """Calculate recency score (newer is better)."""
        age_days = (datetime.utcnow() - article.publication_date).days

        if age_days < 1:
            return 1.0
        elif age_days < 3:
            return 0.9
        elif age_days < 7:
            return 0.7
        elif age_days < 14:
            return 0.5
        elif age_days < 30:
            return 0.3
        else:
            return 0.1

    def _calculate_engagement_boost(
        self,
        article: NewsArticle,
        engagement_history: list[NewsEngagement],
    ) -> float:
        """Calculate boost based on past engagement patterns."""
        if not engagement_history:
            return 0.0

        # Find articles user engaged with positively
        positive_engagements = [
            e for e in engagement_history
            if e.read or e.bookmarked or (e.liked is True)
        ]

        if not positive_engagements:
            return 0.0

        # Simple heuristic: if user reads/saves articles from this source,
        # boost similar content
        boost = 0.0

        # Source affinity
        source_matches = sum(
            1 for e in positive_engagements
            # Would need to fetch article source from engagement
        )

        return min(0.5, boost)

    def filter_by_preferences(
        self,
        articles: list[NewsArticle],
        preferences: UserPreference,
    ) -> list[NewsArticle]:
        """
        Filter articles based on user preferences.

        Args:
            articles: List of articles
            preferences: User preferences

        Returns:
            Filtered articles
        """
        filtered = []

        for article in articles:
            # Skip blocked sources
            if article.source in preferences.blocked_sources:
                continue

            # Apply preferred sources boost
            if (
                preferences.preferred_sources
                and article.source not in preferences.preferred_sources
            ):
                # Don't skip, but de-prioritize
                pass

            filtered.append(article)

        return filtered

    def rank_articles(
        self,
        articles: list[NewsArticle],
        preferences: UserPreference,
        engagement_history: Optional[list[NewsEngagement]] = None,
    ) -> list[NewsArticle]:
        """
        Rank articles by relevance score.

        Args:
            articles: List of articles
            preferences: User preferences
            engagement_history: Optional engagement history

        Returns:
            Ranked articles (highest relevance first)
        """
        # Calculate relevance scores
        scored_articles = []

        for article in articles:
            score = self.calculate_relevance_score(
                article, preferences, engagement_history
            )
            article.relevance_score = score

            # Only include if above minimum threshold
            if score >= self.min_relevance_score:
                scored_articles.append(article)

        # Sort by relevance score (descending)
        scored_articles.sort(key=lambda x: x.relevance_score, reverse=True)

        return scored_articles

    def generate_personalized_feed(
        self,
        articles: list[NewsArticle],
        preferences: UserPreference,
        engagement_history: Optional[list[NewsEngagement]] = None,
        max_articles: int = 50,
    ) -> list[NewsArticle]:
        """
        Generate personalized news feed for user.

        Args:
            articles: Available articles
            preferences: User preferences
            engagement_history: Optional engagement history
            max_articles: Maximum articles to return

        Returns:
            Personalized and ranked articles
        """
        # Filter by preferences
        filtered = self.filter_by_preferences(articles, preferences)

        # Rank by relevance
        ranked = self.rank_articles(filtered, preferences, engagement_history)

        # Limit results
        return ranked[:max_articles]

    def group_by_category(
        self,
        articles: list[NewsArticle],
    ) -> dict[NewsCategory, list[NewsArticle]]:
        """
        Group articles by category.

        Args:
            articles: List of articles

        Returns:
            Articles grouped by category
        """
        grouped = defaultdict(list)

        for article in articles:
            grouped[article.category].append(article)

        return dict(grouped)

    def get_trending_topics(
        self,
        articles: list[NewsArticle],
        min_mentions: int = 3,
        max_topics: int = 10,
    ) -> list[tuple[str, int]]:
        """
        Identify trending topics from keywords.

        Args:
            articles: List of articles
            min_mentions: Minimum mentions to be trending
            max_topics: Maximum topics to return

        Returns:
            List of (topic, count) tuples
        """
        topic_counts = defaultdict(int)

        # Count keyword occurrences
        for article in articles:
            for keyword in article.keywords:
                topic_counts[keyword.lower()] += 1

            # Also count conditions
            for condition in article.conditions:
                topic_counts[condition.lower()] += 1

        # Filter by minimum mentions
        trending = [
            (topic, count)
            for topic, count in topic_counts.items()
            if count >= min_mentions
        ]

        # Sort by count and return top N
        trending.sort(key=lambda x: x[1], reverse=True)

        return trending[:max_topics]

    def suggest_articles(
        self,
        article: NewsArticle,
        all_articles: list[NewsArticle],
        max_suggestions: int = 5,
    ) -> list[NewsArticle]:
        """
        Suggest related articles based on current article.

        Args:
            article: Current article
            all_articles: All available articles
            max_suggestions: Maximum suggestions

        Returns:
            List of suggested articles
        """
        suggestions = []

        for candidate in all_articles:
            if candidate.id == article.id:
                continue

            similarity_score = self._calculate_article_similarity(
                article, candidate
            )

            if similarity_score > 0.3:
                suggestions.append((candidate, similarity_score))

        # Sort by similarity
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return [article for article, _ in suggestions[:max_suggestions]]

    def _calculate_article_similarity(
        self,
        article1: NewsArticle,
        article2: NewsArticle,
    ) -> float:
        """Calculate similarity score between two articles."""
        score = 0.0

        # Same category
        if article1.category == article2.category:
            score += 0.3

        # Overlapping specialties
        if article1.specialty and article2.specialty:
            overlap = set(article1.specialty) & set(article2.specialty)
            if overlap:
                score += 0.3

        # Overlapping keywords
        if article1.keywords and article2.keywords:
            overlap = set(
                k.lower() for k in article1.keywords
            ) & set(k.lower() for k in article2.keywords)
            if overlap:
                score += 0.2 * (len(overlap) / max(
                    len(article1.keywords),
                    len(article2.keywords)
                ))

        # Same source
        if article1.source == article2.source:
            score += 0.1

        # Similar publication time
        time_diff = abs(
            (article1.publication_date - article2.publication_date).days
        )
        if time_diff < 7:
            score += 0.1

        return min(1.0, score)

    def learn_from_engagement(
        self,
        preferences: UserPreference,
        recent_engagements: list[NewsEngagement],
        articles_map: dict[str, NewsArticle],
    ) -> UserPreference:
        """
        Update preferences based on reading behavior.

        Args:
            preferences: Current preferences
            recent_engagements: Recent engagement history
            articles_map: Map of article_id to NewsArticle

        Returns:
            Updated preferences
        """
        if not preferences.learn_from_reading:
            return preferences

        # Track category engagement
        category_engagement = defaultdict(int)
        total_engagement = 0

        for engagement in recent_engagements:
            if not engagement.read:
                continue

            article = articles_map.get(engagement.article_id)
            if not article:
                continue

            # Weight by reading time
            weight = min(1.0, engagement.reading_time_seconds / 120.0)
            category_engagement[article.category.value] += weight
            total_engagement += weight

            # Extract interesting keywords
            if preferences.learn_from_bookmarks and engagement.bookmarked:
                for keyword in article.keywords[:3]:
                    if keyword.lower() not in [
                        k.lower() for k in preferences.keywords
                    ]:
                        preferences.keywords.append(keyword)

        # Update category weights based on engagement
        if total_engagement > 0:
            for category, engagement_count in category_engagement.items():
                if category in preferences.category_weights:
                    # Gradually adjust weights
                    current_weight = preferences.category_weights[category]
                    engagement_ratio = engagement_count / total_engagement

                    # Increase weight if high engagement
                    if engagement_ratio > 0.3 and current_weight < 5:
                        preferences.category_weights[category] = min(
                            5, current_weight + 1
                        )

        preferences.updated_at = datetime.utcnow()
        return preferences

    def create_reading_list(
        self,
        articles: list[NewsArticle],
        preferences: UserPreference,
        time_available_minutes: int = 15,
    ) -> list[NewsArticle]:
        """
        Create curated reading list based on available time.

        Args:
            articles: Available articles
            preferences: User preferences
            time_available_minutes: Available reading time

        Returns:
            Curated reading list that fits time budget
        """
        # Rank articles
        ranked = self.rank_articles(articles, preferences)

        # Build reading list within time budget
        reading_list = []
        total_time = 0

        for article in ranked:
            if total_time + article.reading_time_minutes <= time_available_minutes:
                reading_list.append(article)
                total_time += article.reading_time_minutes
            else:
                break

        logger.info(
            f"Created reading list: {len(reading_list)} articles, "
            f"~{total_time} minutes"
        )

        return reading_list


async def get_news_personalizer() -> NewsPersonalizer:
    """Get news personalizer instance."""
    return NewsPersonalizer()
