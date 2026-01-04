"""
Query Pattern Analysis

Analyzes query patterns to identify:
- Most common query topics
- Specialty distribution
- Seasonal patterns
- Query complexity
- Time-based trends
"""

import sqlite3
from collections import Counter
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Optional, List
import re

from .storage import AnalyticsStorage
from .models import QueryAnalytics, SpecialtyMetrics, TrendData, TimeGranularity


class QueryPatternAnalyzer:
    """
    Analyzes query patterns for practice insights.

    Provides deep analysis of:
    - Topic clustering
    - Specialty distribution
    - Temporal patterns
    - Query complexity
    """

    def __init__(self, storage: Optional[AnalyticsStorage] = None):
        """
        Initialize query pattern analyzer.

        Args:
            storage: Analytics storage backend
        """
        self.storage = storage or AnalyticsStorage()
        self.db_path = self.storage.db_path

        # Medical specialty keywords (simple keyword matching)
        self.specialty_keywords = {
            'cardiology': ['heart', 'cardiac', 'ecg', 'hypertension', 'bp', 'cholesterol', 'statin'],
            'diabetes': ['diabetes', 'insulin', 'glucose', 'hba1c', 'metformin', 'diabetic'],
            'respiratory': ['asthma', 'copd', 'pneumonia', 'bronchitis', 'respiratory', 'lung'],
            'neurology': ['headache', 'seizure', 'stroke', 'migraine', 'epilepsy', 'neurological'],
            'gastroenterology': ['gastric', 'liver', 'hepatitis', 'gastritis', 'ibs', 'acid', 'ulcer'],
            'infectious': ['infection', 'fever', 'antibiotic', 'viral', 'bacterial', 'sepsis'],
            'pediatrics': ['child', 'pediatric', 'infant', 'vaccination', 'growth'],
            'gynecology': ['pregnancy', 'menstrual', 'gynec', 'obstetric', 'contraception'],
            'dermatology': ['skin', 'rash', 'dermatitis', 'acne', 'eczema'],
            'orthopedics': ['bone', 'fracture', 'joint', 'arthritis', 'orthopedic'],
        }

    def analyze_queries(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> QueryAnalytics:
        """
        Comprehensive query analysis for a user.

        Args:
            user_id: User identifier
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            QueryAnalytics model with all metrics
        """
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Get all queries
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT *
                FROM events
                WHERE user_id = ?
                    AND timestamp >= ?
                    AND timestamp <= ?
                    AND event_type IN ('query', 'voice_query')
            """, (user_id, start_dt.isoformat(), end_dt.isoformat()))

            events = cursor.fetchall()

        if not events:
            return self._empty_analytics(user_id, start_date, end_date)

        # Volume metrics
        total_queries = len(events)
        voice_queries = sum(1 for e in events if e['voice_input'])
        text_queries = total_queries - voice_queries
        with_context = sum(1 for e in events if e['patient_context'])

        # Quality metrics
        high_conf = sum(1 for e in events if e['confidence'] == 'high')
        high_conf_rate = high_conf / total_queries * 100 if total_queries > 0 else 0
        avg_citations = sum(e['citation_count'] or 0 for e in events) / total_queries

        # Performance
        latencies = [e['latency_ms'] for e in events if e['latency_ms']]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        sorted_lat = sorted(latencies)
        median_latency = sorted_lat[len(sorted_lat) // 2] if sorted_lat else 0
        p95_latency = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0

        # Timing patterns
        peak_hours = self._calculate_peak_hours(events)
        weekday_dist = self._calculate_weekday_distribution(events)

        # Topic analysis
        top_topics = self._extract_topics(events)
        specialty_dist = self._calculate_specialty_distribution(events)

        # Common queries
        common_queries = self._find_common_queries(events)

        # Complexity
        query_lengths = [e['query_length'] or 0 for e in events]
        avg_length = sum(query_lengths) / len(query_lengths) if query_lengths else 0
        complex_count = sum(1 for l in query_lengths if l > 100)

        # Errors
        errors = sum(1 for e in events if not e['success'])
        error_rate = errors / total_queries * 100 if total_queries > 0 else 0

        return QueryAnalytics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            total_queries=total_queries,
            voice_queries=voice_queries,
            text_queries=text_queries,
            queries_with_patient_context=with_context,
            avg_confidence_score=high_conf_rate / 100,
            high_confidence_rate=high_conf_rate,
            avg_citations_per_query=avg_citations,
            avg_latency_ms=avg_latency,
            median_latency_ms=median_latency,
            p95_latency_ms=p95_latency,
            peak_hours=peak_hours,
            weekday_distribution=weekday_dist,
            top_topics=top_topics,
            specialty_distribution=specialty_dist,
            most_common_queries=common_queries,
            avg_query_length=avg_length,
            complex_queries_count=complex_count,
            error_count=errors,
            error_rate=error_rate,
        )

    def get_specialty_breakdown(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> List[SpecialtyMetrics]:
        """
        Get detailed metrics for each specialty.

        Args:
            user_id: User identifier
            start_date: Start date
            end_date: End date

        Returns:
            List of SpecialtyMetrics
        """
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT *
                FROM events
                WHERE user_id = ?
                    AND timestamp >= ?
                    AND timestamp <= ?
                    AND event_type IN ('query', 'voice_query')
            """, (user_id, start_dt.isoformat(), end_dt.isoformat()))

            events = cursor.fetchall()

        if not events:
            return []

        # Classify queries by specialty
        specialty_queries = {}
        for event in events:
            query = (event['question'] or '').lower()
            specialty = self._classify_specialty(query)

            if specialty not in specialty_queries:
                specialty_queries[specialty] = []
            specialty_queries[specialty].append(event)

        # Calculate metrics for each specialty
        total_queries = len(events)
        specialty_metrics = []

        for specialty, queries in specialty_queries.items():
            count = len(queries)
            percentage = count / total_queries * 100

            # Extract unique topics (simplified)
            topics = set()
            for q in queries:
                words = (q['question'] or '').lower().split()
                topics.update(word for word in words if len(word) > 5)

            metrics = SpecialtyMetrics(
                specialty=specialty,
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                query_count=count,
                percentage_of_total=percentage,
                unique_topics=len(topics),
                avg_queries_per_topic=count / len(topics) if topics else 0,
            )
            specialty_metrics.append(metrics)

        # Sort by query count
        specialty_metrics.sort(key=lambda m: m.query_count, reverse=True)

        return specialty_metrics

    def get_query_trends(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        granularity: TimeGranularity = TimeGranularity.DAILY,
    ) -> TrendData:
        """
        Get query volume trends over time.

        Args:
            user_id: User identifier
            start_date: Start date
            end_date: End date
            granularity: Time granularity

        Returns:
            TrendData with time series
        """
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            if granularity == TimeGranularity.DAILY:
                cursor = conn.execute("""
                    SELECT
                        date(timestamp) as date,
                        COUNT(*) as count
                    FROM events
                    WHERE user_id = ?
                        AND timestamp >= ?
                        AND timestamp <= ?
                        AND event_type IN ('query', 'voice_query')
                    GROUP BY date(timestamp)
                    ORDER BY date
                """, (user_id, start_dt.isoformat(), end_dt.isoformat()))
            else:
                # Weekly/monthly aggregation would go here
                cursor = conn.execute("""
                    SELECT
                        date(timestamp) as date,
                        COUNT(*) as count
                    FROM events
                    WHERE user_id = ?
                        AND timestamp >= ?
                        AND timestamp <= ?
                        AND event_type IN ('query', 'voice_query')
                    GROUP BY date(timestamp)
                    ORDER BY date
                """, (user_id, start_dt.isoformat(), end_dt.isoformat()))

            rows = cursor.fetchall()

        data_points = [
            {'date': row[0], 'value': float(row[1])}
            for row in rows
        ]

        # Calculate trend
        values = [dp['value'] for dp in data_points]
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2) if len(values) > 0 else 0
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if len(values) > 0 else 0
            trend_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0

            if trend_pct > 10:
                trend_dir = "increasing"
            elif trend_pct < -10:
                trend_dir = "decreasing"
            else:
                trend_dir = "stable"
        else:
            trend_dir = "stable"
            trend_pct = 0.0

        # Statistical metrics
        mean_val = sum(values) / len(values) if values else 0
        sorted_vals = sorted(values)
        median_val = sorted_vals[len(sorted_vals) // 2] if sorted_vals else 0

        return TrendData(
            metric_name="query_volume",
            user_id=user_id,
            granularity=granularity,
            data_points=data_points,
            trend_direction=trend_dir,
            trend_percentage=trend_pct,
            mean_value=mean_val,
            median_value=median_val,
            min_value=min(values) if values else 0,
            max_value=max(values) if values else 0,
        )

    def _calculate_peak_hours(self, events) -> List[int]:
        """Calculate hours with most queries."""
        hours = [datetime.fromisoformat(e['timestamp']).hour for e in events]
        hour_counts = Counter(hours)
        return [h for h, _ in hour_counts.most_common(3)]

    def _calculate_weekday_distribution(self, events) -> dict:
        """Calculate query distribution by weekday."""
        weekday_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        weekdays = [datetime.fromisoformat(e['timestamp']).weekday() for e in events]

        weekday_dist = {}
        for wd in weekdays:
            day_name = weekday_map[wd]
            weekday_dist[day_name] = weekday_dist.get(day_name, 0) + 1

        return weekday_dist

    def _extract_topics(self, events, limit: int = 10) -> List[dict]:
        """Extract top topics from queries."""
        # Simple word frequency analysis
        # In production, would use NLP/embeddings for better topic extraction
        word_freq = Counter()

        for event in events:
            query = (event['question'] or '').lower()
            # Remove common words
            words = re.findall(r'\b[a-z]{4,}\b', query)
            word_freq.update(words)

        # Filter medical terms (simplified)
        stopwords = {'what', 'when', 'where', 'which', 'does', 'should', 'would', 'could'}
        topics = []

        for word, count in word_freq.most_common(limit * 2):
            if word not in stopwords:
                topics.append({
                    'topic': word,
                    'count': count,
                    'percentage': count / len(events) * 100
                })

            if len(topics) >= limit:
                break

        return topics

    def _calculate_specialty_distribution(self, events) -> dict:
        """Calculate distribution of queries by specialty."""
        specialty_counts = Counter()

        for event in events:
            query = (event['question'] or '').lower()
            specialty = self._classify_specialty(query)
            specialty_counts[specialty] += 1

        return dict(specialty_counts)

    def _classify_specialty(self, query: str) -> str:
        """Classify query into medical specialty."""
        query_lower = query.lower()

        # Count keyword matches for each specialty
        specialty_scores = {}
        for specialty, keywords in self.specialty_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                specialty_scores[specialty] = score

        if specialty_scores:
            return max(specialty_scores.keys(), key=lambda s: specialty_scores[s])

        return 'general'

    def _find_common_queries(self, events, limit: int = 10) -> List[dict]:
        """Find most common query patterns."""
        # Group similar queries (simplified - exact match)
        query_counts = Counter()

        for event in events:
            query = (event['question'] or '').strip()
            if query:
                # Truncate for privacy
                query_short = query[:80] + '...' if len(query) > 80 else query
                query_counts[query_short] += 1

        return [
            {'query': query, 'count': count}
            for query, count in query_counts.most_common(limit)
        ]

    def _empty_analytics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> QueryAnalytics:
        """Return empty analytics for no data."""
        return QueryAnalytics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
        )


__all__ = ["QueryPatternAnalyzer"]
