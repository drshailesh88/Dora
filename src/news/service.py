"""
News Service - Main Service Layer

Coordinates all news functionality: aggregation, personalization,
summarization, bookmarks, and engagement tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from .aggregator import NewsAggregator
from .approvals import DrugApprovalTracker
from .bookmarks import BookmarkManager
from .conferences import ConferenceTracker
from .guidelines import GuidelineTracker
from .models import (
    NewsArticle,
    NewsCategory,
    NewsEngagement,
    UserPreference,
)
from .personalization import NewsPersonalizer
from .summarizer import NewsSummarizer

logger = logging.getLogger(__name__)


class NewsService:
    """Main news service coordinating all news functionality."""

    def __init__(
        self,
        aggregator: Optional[NewsAggregator] = None,
        summarizer: Optional[NewsSummarizer] = None,
        personalizer: Optional[NewsPersonalizer] = None,
        bookmark_manager: Optional[BookmarkManager] = None,
        conference_tracker: Optional[ConferenceTracker] = None,
        guideline_tracker: Optional[GuidelineTracker] = None,
        approval_tracker: Optional[DrugApprovalTracker] = None,
    ):
        self.aggregator = aggregator or NewsAggregator()
        self.summarizer = summarizer or NewsSummarizer()
        self.personalizer = personalizer or NewsPersonalizer()
        self.bookmark_manager = bookmark_manager or BookmarkManager()
        self.conference_tracker = conference_tracker or ConferenceTracker()
        self.guideline_tracker = guideline_tracker or GuidelineTracker()
        self.approval_tracker = approval_tracker or DrugApprovalTracker()

        # In-memory storage (in production, use database)
        self.articles: dict[str, NewsArticle] = {}
        self.preferences: dict[str, UserPreference] = {}
        self.engagements: dict[str, list[NewsEngagement]] = {}

    async def get_personalized_feed(
        self,
        user_id: str,
        days_back: int = 7,
        max_articles: int = 50,
        category: Optional[NewsCategory] = None,
    ) -> list[NewsArticle]:
        """
        Get personalized news feed for user.

        Args:
            user_id: User ID
            days_back: Number of days to look back
            max_articles: Maximum articles to return
            category: Optional category filter

        Returns:
            Personalized news feed
        """
        # Get user preferences
        preferences = await self.get_user_preferences(user_id)

        # Aggregate news from all sources
        articles = await self.aggregator.aggregate_all(
            specialty=preferences.primary_specialty,
            days_back=days_back,
            max_results_per_source=20,
        )

        # Filter by category if specified
        if category:
            articles = [a for a in articles if a.category == category]

        # Get user engagement history
        engagement_history = self.engagements.get(user_id, [])

        # Personalize and rank
        personalized = self.personalizer.generate_personalized_feed(
            articles=articles,
            preferences=preferences,
            engagement_history=engagement_history,
            max_articles=max_articles,
        )

        # Enrich with summaries
        enriched = await self.summarizer.batch_summarize(
            personalized,
            include_implications=True,
        )

        # Store articles
        for article in enriched:
            self.articles[article.id] = article

        logger.info(
            f"Generated personalized feed for user {user_id}: "
            f"{len(enriched)} articles"
        )

        return enriched

    async def get_trending_articles(
        self,
        specialty: Optional[str] = None,
        days_back: int = 3,
        max_articles: int = 20,
    ) -> list[NewsArticle]:
        """
        Get trending articles.

        Args:
            specialty: Filter by specialty
            days_back: Number of days to look back
            max_articles: Maximum articles

        Returns:
            Trending articles
        """
        # Aggregate recent articles
        articles = await self.aggregator.aggregate_all(
            specialty=specialty,
            days_back=days_back,
        )

        # Sort by engagement metrics
        # In production, would use actual view counts, shares, etc.
        articles.sort(
            key=lambda x: (
                x.priority.value,
                x.publication_date
            ),
            reverse=True,
        )

        return articles[:max_articles]

    async def get_breaking_news(
        self,
        specialty: Optional[str] = None,
        hours_back: int = 24,
    ) -> list[NewsArticle]:
        """
        Get breaking/urgent news.

        Args:
            specialty: Filter by specialty
            hours_back: Number of hours to look back

        Returns:
            Breaking news articles
        """
        days_back = max(1, hours_back // 24)

        articles = await self.aggregator.aggregate_all(
            specialty=specialty,
            days_back=days_back,
        )

        # Filter for high priority and recent
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        breaking = [
            a for a in articles
            if a.priority.value in ["high", "critical"]
            and a.publication_date >= cutoff_time
        ]

        # Sort by priority and recency
        breaking.sort(
            key=lambda x: (x.priority.value, x.publication_date),
            reverse=True,
        )

        return breaking

    async def get_article(
        self,
        article_id: str,
    ) -> Optional[NewsArticle]:
        """
        Get article by ID.

        Args:
            article_id: Article ID

        Returns:
            Article if found
        """
        return self.articles.get(article_id)

    async def search_articles(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[NewsCategory] = None,
        max_results: int = 20,
    ) -> list[NewsArticle]:
        """
        Search articles.

        Args:
            query: Search query
            user_id: Optional user ID for personalization
            category: Optional category filter
            max_results: Maximum results

        Returns:
            Matching articles
        """
        # Search using aggregator
        articles = await self.aggregator.fetch_pubmed_articles(
            query=query,
            max_results=max_results,
        )

        # Filter by category
        if category:
            articles = [a for a in articles if a.category == category]

        # Personalize if user provided
        if user_id:
            preferences = await self.get_user_preferences(user_id)
            articles = self.personalizer.rank_articles(
                articles,
                preferences,
            )

        return articles[:max_results]

    async def track_article_view(
        self,
        user_id: str,
        article_id: str,
    ) -> None:
        """
        Track article view.

        Args:
            user_id: User ID
            article_id: Article ID
        """
        if user_id not in self.engagements:
            self.engagements[user_id] = []

        # Find or create engagement
        engagement = None
        for e in self.engagements[user_id]:
            if e.article_id == article_id:
                engagement = e
                break

        if not engagement:
            engagement = NewsEngagement(
                user_id=user_id,
                article_id=article_id,
            )
            self.engagements[user_id].append(engagement)

        engagement.viewed = True
        engagement.viewed_at = datetime.utcnow()
        engagement.last_interaction = datetime.utcnow()

        # Update article view count
        article = self.articles.get(article_id)
        if article:
            article.views_count += 1

    async def track_article_read(
        self,
        user_id: str,
        article_id: str,
        reading_time_seconds: int,
    ) -> None:
        """
        Track article read completion.

        Args:
            user_id: User ID
            article_id: Article ID
            reading_time_seconds: Reading time in seconds
        """
        # Get or create engagement
        engagement = None
        for e in self.engagements.get(user_id, []):
            if e.article_id == article_id:
                engagement = e
                break

        if engagement:
            engagement.read = True
            engagement.read_at = datetime.utcnow()
            engagement.reading_time_seconds = reading_time_seconds
            engagement.last_interaction = datetime.utcnow()

    async def get_user_preferences(
        self,
        user_id: str,
    ) -> UserPreference:
        """
        Get user preferences.

        Args:
            user_id: User ID

        Returns:
            User preferences
        """
        if user_id not in self.preferences:
            # Create default preferences
            self.preferences[user_id] = UserPreference(
                user_id=user_id,
                primary_specialty="internal_medicine",
            )

        return self.preferences[user_id]

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreference,
    ) -> UserPreference:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: Updated preferences

        Returns:
            Updated preferences
        """
        preferences.updated_at = datetime.utcnow()
        self.preferences[user_id] = preferences

        logger.info(f"Updated preferences for user {user_id}")
        return preferences

    async def learn_from_behavior(
        self,
        user_id: str,
    ) -> UserPreference:
        """
        Update preferences based on user behavior.

        Args:
            user_id: User ID

        Returns:
            Updated preferences
        """
        preferences = await self.get_user_preferences(user_id)
        engagements = self.engagements.get(user_id, [])

        # Learn from recent engagements (last 30 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_engagements = [
            e for e in engagements
            if e.first_interaction >= recent_cutoff
        ]

        # Update preferences
        updated = self.personalizer.learn_from_engagement(
            preferences=preferences,
            recent_engagements=recent_engagements,
            articles_map=self.articles,
        )

        self.preferences[user_id] = updated
        return updated

    async def get_daily_digest(
        self,
        user_id: str,
    ) -> dict:
        """
        Get daily news digest for user.

        Args:
            user_id: User ID

        Returns:
            Daily digest
        """
        preferences = await self.get_user_preferences(user_id)

        # Get personalized feed
        articles = await self.get_personalized_feed(
            user_id=user_id,
            days_back=1,  # Today's news
            max_articles=10,
        )

        # Group by category
        by_category = self.personalizer.group_by_category(articles)

        # Generate digest intro
        intro = await self.summarizer.generate_daily_digest_intro(
            articles_by_category=by_category,
            specialty=preferences.primary_specialty,
        )

        # Get trending topics
        trending = self.personalizer.get_trending_topics(
            articles,
            min_mentions=2,
            max_topics=5,
        )

        digest = {
            "date": datetime.utcnow().date().isoformat(),
            "user_id": user_id,
            "introduction": intro,
            "articles": [a.model_dump() for a in articles],
            "by_category": {
                cat.value: [a.model_dump() for a in arts]
                for cat, arts in by_category.items()
            },
            "trending_topics": [
                {"topic": topic, "count": count}
                for topic, count in trending
            ],
        }

        return digest

    async def get_reading_list(
        self,
        user_id: str,
        time_available_minutes: int = 15,
    ) -> list[NewsArticle]:
        """
        Get curated reading list for available time.

        Args:
            user_id: User ID
            time_available_minutes: Available reading time

        Returns:
            Curated reading list
        """
        preferences = await self.get_user_preferences(user_id)

        # Get recent personalized feed
        articles = await self.get_personalized_feed(
            user_id=user_id,
            days_back=7,
            max_articles=100,
        )

        # Create time-based reading list
        reading_list = self.personalizer.create_reading_list(
            articles=articles,
            preferences=preferences,
            time_available_minutes=time_available_minutes,
        )

        return reading_list

    async def get_similar_articles(
        self,
        article_id: str,
        max_results: int = 5,
    ) -> list[NewsArticle]:
        """
        Get articles similar to given article.

        Args:
            article_id: Article ID
            max_results: Maximum results

        Returns:
            Similar articles
        """
        article = self.articles.get(article_id)
        if not article:
            return []

        all_articles = list(self.articles.values())

        similar = self.personalizer.suggest_articles(
            article=article,
            all_articles=all_articles,
            max_suggestions=max_results,
        )

        return similar

    # Bookmark methods (delegated to BookmarkManager)

    async def bookmark_article(
        self,
        user_id: str,
        article_id: str,
        collection_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ):
        """Bookmark an article."""
        article = self.articles.get(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")

        bookmark = await self.bookmark_manager.bookmark_article(
            user_id=user_id,
            article=article,
            collection_id=collection_id,
            tags=tags,
            notes=notes,
        )

        # Track engagement
        for e in self.engagements.get(user_id, []):
            if e.article_id == article_id:
                e.bookmarked = True
                e.bookmarked_at = datetime.utcnow()
                break

        # Update article bookmark count
        article.bookmarks_count += 1

        return bookmark

    async def get_user_bookmarks(
        self,
        user_id: str,
        collection_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ):
        """Get user's bookmarks."""
        return await self.bookmark_manager.get_user_bookmarks(
            user_id=user_id,
            collection_id=collection_id,
            tags=tags,
        )

    async def create_collection(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
    ):
        """Create bookmark collection."""
        return await self.bookmark_manager.create_collection(
            user_id=user_id,
            name=name,
            description=description,
            emoji=emoji,
        )

    async def get_user_collections(self, user_id: str):
        """Get user's collections."""
        return await self.bookmark_manager.get_user_collections(user_id)


# Singleton instance
_news_service: Optional[NewsService] = None


async def get_news_service() -> NewsService:
    """Get news service instance."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
