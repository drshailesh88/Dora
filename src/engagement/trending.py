"""
Trending Queries

Aggregates and ranks queries by specialty, geography, and time period.
Shows doctors what their peers are asking.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from src.engagement.models import (
    TrendingQuery,
    TrendingPeriod,
    GeographicScope,
)


class TrendingAnalyzer:
    """Analyzes and generates trending query data."""

    def __init__(self):
        """Initialize trending analyzer."""
        self.query_cache = defaultdict(list)
        self.trending_cache = {}

    def compute_trending(
        self,
        specialty: Optional[str] = None,
        period: TrendingPeriod = TrendingPeriod.LAST_7D,
        geographic_scope: GeographicScope = GeographicScope.GLOBAL,
        location: Optional[str] = None,
        limit: int = 10,
    ) -> list[TrendingQuery]:
        """
        Compute trending queries.

        Args:
            specialty: Filter by specialty (None for all)
            period: Time period to analyze
            geographic_scope: Geographic filtering scope
            location: Location string (city, state, country)
            limit: Number of trending queries to return

        Returns:
            List of TrendingQuery objects
        """
        # Get queries from the specified period
        queries = self._fetch_queries_for_period(
            period=period,
            specialty=specialty,
            geographic_scope=geographic_scope,
            location=location,
        )

        # Aggregate and count
        query_counts = self._aggregate_queries(queries)

        # Get previous period for trend direction
        previous_counts = self._get_previous_period_counts(
            period=period,
            specialty=specialty,
            geographic_scope=geographic_scope,
            location=location,
        )

        # Create TrendingQuery objects
        trending_queries = []
        for rank, (query_text, data) in enumerate(query_counts.most_common(limit), 1):
            previous_rank = self._get_previous_rank(query_text, previous_counts)
            trend_direction = self._calculate_trend_direction(rank, previous_rank)

            trending_query = TrendingQuery(
                query_text=query_text,
                query_count=data["count"],
                unique_users=data["unique_users"],
                specialty=specialty,
                category=data.get("category"),
                geographic_scope=geographic_scope,
                location=location,
                period=period,
                trend_direction=trend_direction,
                rank=rank,
                previous_rank=previous_rank,
                related_queries=self._find_related_queries(query_text, query_counts),
            )
            trending_queries.append(trending_query)

        return trending_queries

    def get_specialty_trending(
        self,
        specialty: str,
        period: TrendingPeriod = TrendingPeriod.LAST_7D,
    ) -> dict[str, Any]:
        """
        Get comprehensive trending data for a specialty.

        Args:
            specialty: Medical specialty
            period: Time period

        Returns:
            Dict with trending queries, categories, and insights
        """
        # Get trending queries
        trending = self.compute_trending(
            specialty=specialty,
            period=period,
            limit=20,
        )

        # Analyze by category
        category_distribution = self._analyze_categories(trending)

        # Find emerging topics (new queries gaining traction)
        emerging = [
            t for t in trending
            if t.trend_direction == "new" or t.trend_direction == "rising"
        ]

        # Find hot topics (high volume, rising)
        hot_topics = [
            t for t in trending
            if t.query_count > 50 and t.trend_direction in ["rising", "stable"]
        ]

        return {
            "specialty": specialty,
            "period": period.value,
            "trending_queries": [self._to_dict(t) for t in trending],
            "category_distribution": category_distribution,
            "emerging_topics": [self._to_dict(t) for t in emerging[:5]],
            "hot_topics": [self._to_dict(t) for t in hot_topics[:5]],
            "total_queries": sum(t.query_count for t in trending),
            "computed_at": datetime.utcnow().isoformat(),
        }

    def get_geographic_trending(
        self,
        location: str,
        scope: GeographicScope = GeographicScope.CITY,
        period: TrendingPeriod = TrendingPeriod.LAST_7D,
    ) -> list[TrendingQuery]:
        """
        Get trending queries for a geographic location.

        Args:
            location: Location name
            scope: Geographic scope
            period: Time period

        Returns:
            List of TrendingQuery objects
        """
        return self.compute_trending(
            specialty=None,
            period=period,
            geographic_scope=scope,
            location=location,
            limit=10,
        )

    def get_personalized_trending(
        self,
        user_profile: dict[str, Any],
        period: TrendingPeriod = TrendingPeriod.LAST_7D,
    ) -> list[TrendingQuery]:
        """
        Get personalized trending based on user profile.

        Args:
            user_profile: User's medical profile
            period: Time period

        Returns:
            List of TrendingQuery objects
        """
        specialty = user_profile.get("specialty")
        location = user_profile.get("location")

        # Get specialty trending
        trending = self.compute_trending(
            specialty=specialty,
            period=period,
            limit=15,
        )

        # Boost queries related to user's interests
        user_interests = set(user_profile.get("common_conditions", []))
        if user_interests:
            trending = self._boost_by_interests(trending, user_interests)

        return trending[:10]

    def track_query(
        self,
        query_text: str,
        user_id: str,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
    ) -> None:
        """
        Track a query for trending analysis.

        Args:
            query_text: The query text (will be anonymized)
            user_id: User ID (for unique user counting)
            specialty: User's specialty
            category: Query category
            location: User's location
        """
        # Anonymize query (remove patient-specific info)
        anonymized_query = self._anonymize_query(query_text)

        # Store in cache/database
        query_record = {
            "query": anonymized_query,
            "user_id": user_id,
            "specialty": specialty,
            "category": category,
            "location": location,
            "timestamp": datetime.utcnow(),
        }

        # In real implementation, store in database
        cache_key = f"{specialty}_{category}"
        self.query_cache[cache_key].append(query_record)

    def _fetch_queries_for_period(
        self,
        period: TrendingPeriod,
        specialty: Optional[str] = None,
        geographic_scope: GeographicScope = GeographicScope.GLOBAL,
        location: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Fetch queries from database for the specified period."""
        # Calculate time range
        days_back = self._period_to_days(period)
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # In real implementation, query database
        # For now, return mock data
        return self._mock_query_data(specialty, days_back)

    def _aggregate_queries(
        self,
        queries: list[dict[str, Any]],
    ) -> Counter:
        """
        Aggregate queries and count occurrences.

        Args:
            queries: List of query records

        Returns:
            Counter with query text as key and data dict as value
        """
        aggregated = defaultdict(lambda: {"count": 0, "unique_users": set(), "categories": []})

        for query in queries:
            query_text = query["query"]
            user_id = query["user_id"]
            category = query.get("category")

            aggregated[query_text]["count"] += 1
            aggregated[query_text]["unique_users"].add(user_id)
            if category and category not in aggregated[query_text]["categories"]:
                aggregated[query_text]["categories"].append(category)

        # Convert sets to counts
        result = Counter()
        for query_text, data in aggregated.items():
            result[query_text] = {
                "count": data["count"],
                "unique_users": len(data["unique_users"]),
                "category": data["categories"][0] if data["categories"] else None,
            }

        return result

    def _get_previous_period_counts(
        self,
        period: TrendingPeriod,
        specialty: Optional[str] = None,
        geographic_scope: GeographicScope = GeographicScope.GLOBAL,
        location: Optional[str] = None,
    ) -> Counter:
        """Get query counts from previous period for comparison."""
        # In real implementation, fetch from database
        # For now, return empty counter
        return Counter()

    def _get_previous_rank(
        self,
        query_text: str,
        previous_counts: Counter,
    ) -> Optional[int]:
        """Get the rank of a query in the previous period."""
        if not previous_counts:
            return None

        ranked = previous_counts.most_common()
        for rank, (query, _) in enumerate(ranked, 1):
            if query == query_text:
                return rank

        return None

    def _calculate_trend_direction(
        self,
        current_rank: int,
        previous_rank: Optional[int],
    ) -> str:
        """
        Calculate trend direction.

        Args:
            current_rank: Current ranking
            previous_rank: Previous ranking (None if new)

        Returns:
            "new", "rising", "falling", or "stable"
        """
        if previous_rank is None:
            return "new"

        diff = previous_rank - current_rank
        if diff > 3:
            return "rising"
        elif diff < -3:
            return "falling"
        else:
            return "stable"

    def _find_related_queries(
        self,
        query_text: str,
        all_queries: Counter,
    ) -> list[str]:
        """Find related queries using keyword similarity."""
        # Simple keyword-based similarity
        query_words = set(query_text.lower().split())

        related = []
        for other_query, _ in all_queries.most_common(50):
            if other_query == query_text:
                continue

            other_words = set(other_query.lower().split())
            overlap = len(query_words & other_words)

            if overlap >= 2:  # At least 2 words in common
                related.append(other_query)

            if len(related) >= 3:
                break

        return related

    def _analyze_categories(
        self,
        trending: list[TrendingQuery],
    ) -> dict[str, int]:
        """Analyze distribution of categories in trending."""
        categories = Counter()

        for query in trending:
            if query.category:
                categories[query.category] += query.query_count

        return dict(categories)

    def _boost_by_interests(
        self,
        trending: list[TrendingQuery],
        interests: set[str],
    ) -> list[TrendingQuery]:
        """Boost trending queries related to user interests."""
        # Calculate relevance scores
        scored = []
        for query in trending:
            score = query.query_count

            # Boost if related to interests
            query_words = set(query.query_text.lower().split())
            interest_matches = sum(
                1 for interest in interests
                if interest.lower() in query.query_text.lower()
            )
            score *= (1 + interest_matches * 0.5)

            scored.append((score, query))

        # Sort by boosted score
        scored.sort(reverse=True, key=lambda x: x[0])

        return [query for _, query in scored]

    def _anonymize_query(self, query_text: str) -> str:
        """
        Anonymize query by removing patient-specific information.

        Args:
            query_text: Original query

        Returns:
            Anonymized query
        """
        # Remove common patient identifiers
        anonymized = query_text

        # Remove numbers (could be age, dates, etc.)
        import re
        anonymized = re.sub(r'\b\d+\b', 'X', anonymized)

        # Remove proper nouns (patient names)
        # In real implementation, use NER
        words = anonymized.split()
        anonymized = ' '.join([
            w if not w[0].isupper() or w in self._medical_terms()
            else 'Patient'
            for w in words
        ])

        return anonymized

    def _medical_terms(self) -> set[str]:
        """Common medical terms that should not be anonymized."""
        return {
            "Aspirin", "Metformin", "Insulin", "Warfarin",
            "Diabetes", "Hypertension", "Cancer", "Heart",
            # Add more
        }

    def _period_to_days(self, period: TrendingPeriod) -> int:
        """Convert period enum to number of days."""
        period_map = {
            TrendingPeriod.LAST_24H: 1,
            TrendingPeriod.LAST_7D: 7,
            TrendingPeriod.LAST_30D: 30,
        }
        return period_map.get(period, 7)

    def _to_dict(self, trending_query: TrendingQuery) -> dict[str, Any]:
        """Convert TrendingQuery to dict for API response."""
        return {
            "query": trending_query.query_text,
            "count": trending_query.query_count,
            "unique_users": trending_query.unique_users,
            "rank": trending_query.rank,
            "trend": trending_query.trend_direction,
            "related": trending_query.related_queries,
        }

    def _mock_query_data(
        self,
        specialty: Optional[str],
        days_back: int,
    ) -> list[dict[str, Any]]:
        """Mock query data for testing."""
        base_queries = [
            "What is the first-line treatment for hypertension?",
            "Differential diagnosis for chest pain",
            "Metformin dosing guidelines",
            "When to start insulin in type 2 diabetes?",
            "Heart failure management guidelines",
            "AFib rate control vs rhythm control",
            "Beta blocker in heart failure",
            "SGLT2 inhibitors in diabetes",
        ]

        queries = []
        for i, query in enumerate(base_queries):
            # Simulate multiple users asking same question
            for user_num in range((len(base_queries) - i) * 5):
                queries.append({
                    "query": query,
                    "user_id": f"user_{user_num}",
                    "specialty": specialty or "cardiology",
                    "category": "treatment",
                    "location": "Mumbai",
                    "timestamp": datetime.utcnow() - timedelta(days=i % days_back),
                })

        return queries
