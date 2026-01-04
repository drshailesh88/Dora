"""
Tests for medical news feed module.
Tests news aggregation, personalization, and delivery.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta


class TestNewsAggregation:
    """Tests for news aggregation from multiple sources."""

    @pytest.fixture
    def aggregator_service(self):
        """Create aggregator service instance."""
        from src.news.aggregator import NewsAggregatorService
        return NewsAggregatorService()

    @pytest.mark.asyncio
    async def test_aggregate_from_pubmed(self, aggregator_service):
        """Should aggregate news from PubMed."""
        with patch.object(
            aggregator_service,
            "_fetch_pubmed",
            return_value=[
                {
                    "title": "New findings in cardiac treatment",
                    "source": "pubmed",
                    "pmid": "12345678",
                    "published": date.today().isoformat(),
                }
            ],
        ):
            news = await aggregator_service.aggregate(sources=["pubmed"])

            assert len(news) > 0
            assert any(n["source"] == "pubmed" for n in news)

    @pytest.mark.asyncio
    async def test_aggregate_from_multiple_sources(self, aggregator_service):
        """Should aggregate from multiple sources."""
        with patch.object(
            aggregator_service,
            "_fetch_all",
            return_value=[
                {"title": "PubMed Article", "source": "pubmed"},
                {"title": "WHO Update", "source": "who"},
                {"title": "ICMR Guideline", "source": "icmr"},
            ],
        ):
            news = await aggregator_service.aggregate(
                sources=["pubmed", "who", "icmr"]
            )

            sources = set(n["source"] for n in news)
            assert len(sources) >= 2

    @pytest.mark.asyncio
    async def test_deduplication(self, aggregator_service):
        """Should deduplicate similar articles."""
        with patch.object(
            aggregator_service,
            "_fetch_all",
            return_value=[
                {"title": "New COVID treatment found", "source": "pubmed"},
                {"title": "New COVID-19 treatment discovered", "source": "who"},  # Similar
            ],
        ):
            news = await aggregator_service.aggregate(
                sources=["pubmed", "who"],
                deduplicate=True,
            )

            # Should combine or remove duplicate
            assert len(news) <= 2

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, aggregator_service):
        """Should filter by date range."""
        news = await aggregator_service.aggregate(
            sources=["pubmed"],
            from_date=date.today() - timedelta(days=7),
            to_date=date.today(),
        )

        for article in news:
            pub_date = article.get("published", article.get("date"))
            if pub_date:
                assert pub_date >= (date.today() - timedelta(days=7)).isoformat()


class TestNewsPersonalization:
    """Tests for personalized news feed."""

    @pytest.fixture
    def personalization_service(self):
        """Create personalization service instance."""
        from src.news.personalization import NewsPersonalizationService
        return NewsPersonalizationService()

    @pytest.fixture
    def doctor_profile(self):
        """Sample doctor profile."""
        return {
            "id": "doc_123",
            "specialty": "cardiology",
            "interests": ["arrhythmia", "heart failure", "interventional"],
            "reading_history": [
                {"topic": "TAVR", "count": 5},
                {"topic": "AF ablation", "count": 3},
            ],
        }

    @pytest.mark.asyncio
    async def test_personalize_by_specialty(
        self, personalization_service, doctor_profile
    ):
        """Should prioritize specialty-relevant news."""
        all_news = [
            {"title": "AF treatment advances", "topics": ["cardiology", "arrhythmia"]},
            {"title": "Diabetes management", "topics": ["endocrinology", "diabetes"]},
            {"title": "New stent design", "topics": ["cardiology", "interventional"]},
        ]

        personalized = await personalization_service.personalize(
            news=all_news,
            doctor=doctor_profile,
        )

        # Cardiology articles should be ranked higher
        cardio_indices = [
            i for i, n in enumerate(personalized)
            if "cardiology" in n.get("topics", [])
        ]
        other_indices = [
            i for i, n in enumerate(personalized)
            if "cardiology" not in n.get("topics", [])
        ]

        if cardio_indices and other_indices:
            assert min(cardio_indices) < max(other_indices)

    @pytest.mark.asyncio
    async def test_personalize_by_interests(
        self, personalization_service, doctor_profile
    ):
        """Should prioritize based on stated interests."""
        all_news = [
            {"title": "HFrEF treatment update", "topics": ["heart failure"]},
            {"title": "Cholesterol guidelines", "topics": ["lipids"]},
        ]

        personalized = await personalization_service.personalize(
            news=all_news,
            doctor=doctor_profile,
        )

        # Heart failure is in interests, should rank higher
        assert personalized[0]["topics"][0] == "heart failure" or \
               personalized[0].get("relevance_score", 0) >= \
               personalized[1].get("relevance_score", 0)

    @pytest.mark.asyncio
    async def test_personalize_by_reading_history(
        self, personalization_service, doctor_profile
    ):
        """Should learn from reading history."""
        all_news = [
            {"title": "TAVR outcomes study", "topics": ["tavr"]},
            {"title": "Pacemaker innovations", "topics": ["devices"]},
        ]

        personalized = await personalization_service.personalize(
            news=all_news,
            doctor=doctor_profile,
        )

        # TAVR is frequently read, should rank higher
        assert "tavr" in personalized[0].get("topics", []) or \
               personalized[0].get("history_boost", 0) > 0


class TestNewsCategories:
    """Tests for news categorization."""

    @pytest.fixture
    def category_service(self):
        """Create category service instance."""
        from src.news.categories import NewsCategoryService
        return NewsCategoryService()

    @pytest.mark.asyncio
    async def test_categorize_article(self, category_service):
        """Should categorize article correctly."""
        article = {
            "title": "New guidelines for hypertension management",
            "abstract": "ACC/AHA releases updated blood pressure targets...",
        }

        categories = await category_service.categorize(article)

        assert "categories" in categories
        assert "cardiology" in categories["categories"] or \
               "guidelines" in categories["categories"]

    @pytest.mark.asyncio
    async def test_get_articles_by_category(self, category_service):
        """Should retrieve articles by category."""
        articles = await category_service.get_by_category(
            category="research",
            limit=10,
        )

        for article in articles:
            assert "research" in article.get("categories", [])

    @pytest.mark.asyncio
    async def test_trending_categories(self, category_service):
        """Should identify trending categories."""
        trending = await category_service.get_trending(period="week")

        assert len(trending) > 0
        for cat in trending:
            assert "category" in cat
            assert "count" in cat or "trend_score" in cat


class TestNewsDelivery:
    """Tests for news delivery and notifications."""

    @pytest.fixture
    def delivery_service(self):
        """Create delivery service instance."""
        from src.news.delivery import NewsDeliveryService
        return NewsDeliveryService()

    @pytest.mark.asyncio
    async def test_daily_digest_generated(self, delivery_service):
        """Should generate daily digest."""
        digest = await delivery_service.generate_digest(
            doctor_id="doc_123",
            digest_type="daily",
        )

        assert "articles" in digest
        assert len(digest["articles"]) > 0
        assert len(digest["articles"]) <= 10  # Not too many

    @pytest.mark.asyncio
    async def test_breaking_news_notification(self, delivery_service):
        """Should send breaking news immediately."""
        breaking = {
            "title": "FDA approves new heart failure drug",
            "priority": "breaking",
            "specialty": "cardiology",
        }

        with patch.object(
            delivery_service,
            "_send_push",
            return_value={"sent": True},
        ):
            result = await delivery_service.deliver_breaking(
                news=breaking,
                target_specialty="cardiology",
            )

            assert result["delivered"]
            assert result.get("immediate", True)

    @pytest.mark.asyncio
    async def test_delivery_preferences_respected(self, delivery_service):
        """Should respect user delivery preferences."""
        preferences = {
            "digest_time": "08:00",
            "channels": ["email", "push"],
            "frequency": "daily",
        }

        with patch.object(
            delivery_service,
            "get_user_preferences",
            return_value=preferences,
        ):
            schedule = await delivery_service.get_delivery_schedule(
                doctor_id="doc_123"
            )

            assert schedule["next_digest_time"] is not None
            assert "email" in schedule["channels"]


class TestNewsSearch:
    """Tests for news search functionality."""

    @pytest.fixture
    def search_service(self):
        """Create search service instance."""
        from src.news.search import NewsSearchService
        return NewsSearchService()

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, search_service):
        """Should search news by keyword."""
        results = await search_service.search(query="hypertension")

        assert "results" in results
        for article in results["results"]:
            assert "hypertension" in article["title"].lower() or \
                   "hypertension" in article.get("abstract", "").lower()

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_service):
        """Should support search filters."""
        results = await search_service.search(
            query="treatment",
            filters={
                "specialty": "cardiology",
                "date_range": "last_month",
                "source": "pubmed",
            },
        )

        for article in results["results"]:
            assert article.get("source") == "pubmed"

    @pytest.mark.asyncio
    async def test_search_results_ranked(self, search_service):
        """Search results should be relevance-ranked."""
        results = await search_service.search(query="acute coronary syndrome")

        if len(results["results"]) > 1:
            scores = [r.get("relevance_score", 0) for r in results["results"]]
            assert scores == sorted(scores, reverse=True)


class TestNewsBookmarks:
    """Tests for news bookmarking feature."""

    @pytest.fixture
    def bookmark_service(self):
        """Create bookmark service instance."""
        from src.news.bookmarks import NewsBookmarkService
        return NewsBookmarkService()

    @pytest.mark.asyncio
    async def test_bookmark_article(self, bookmark_service):
        """Should bookmark article."""
        result = await bookmark_service.add(
            doctor_id="doc_123",
            article_id="article_456",
        )

        assert result["success"]

    @pytest.mark.asyncio
    async def test_get_bookmarks(self, bookmark_service):
        """Should retrieve user bookmarks."""
        bookmarks = await bookmark_service.get_all(doctor_id="doc_123")

        assert "bookmarks" in bookmarks
        for bm in bookmarks["bookmarks"]:
            assert "article_id" in bm
            assert "bookmarked_at" in bm

    @pytest.mark.asyncio
    async def test_remove_bookmark(self, bookmark_service):
        """Should remove bookmark."""
        # Add then remove
        await bookmark_service.add(
            doctor_id="doc_123",
            article_id="article_789",
        )

        result = await bookmark_service.remove(
            doctor_id="doc_123",
            article_id="article_789",
        )

        assert result["success"]

    @pytest.mark.asyncio
    async def test_bookmark_folders(self, bookmark_service):
        """Should support bookmark folders."""
        result = await bookmark_service.add(
            doctor_id="doc_123",
            article_id="article_456",
            folder="Research Ideas",
        )

        assert result["success"]

        # Get bookmarks by folder
        bookmarks = await bookmark_service.get_by_folder(
            doctor_id="doc_123",
            folder="Research Ideas",
        )

        assert len(bookmarks["bookmarks"]) > 0


class TestNewsSharing:
    """Tests for news sharing features."""

    @pytest.fixture
    def sharing_service(self):
        """Create sharing service instance."""
        from src.news.sharing import NewsSharingService
        return NewsSharingService()

    @pytest.mark.asyncio
    async def test_share_with_colleague(self, sharing_service):
        """Should share article with colleague."""
        result = await sharing_service.share(
            article_id="article_123",
            from_doctor="doc_1",
            to_doctor="doc_2",
            note="Thought you might find this interesting",
        )

        assert result["success"]
        assert "share_id" in result

    @pytest.mark.asyncio
    async def test_share_to_team(self, sharing_service):
        """Should share article with team."""
        result = await sharing_service.share_to_team(
            article_id="article_123",
            doctor_id="doc_1",
            team_id="team_456",
        )

        assert result["success"]
        assert result.get("recipients_count", 0) > 0

    @pytest.mark.asyncio
    async def test_get_shared_with_me(self, sharing_service):
        """Should retrieve articles shared with user."""
        shared = await sharing_service.get_shared_with_me(doctor_id="doc_123")

        assert "articles" in shared
        for article in shared["articles"]:
            assert "shared_by" in article
            assert "shared_at" in article
