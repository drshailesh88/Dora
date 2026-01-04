"""
Analytics Data Collector

Privacy-preserving collection of practice analytics data.
Aggregates raw events into meaningful metrics while respecting HIPAA/DISHA compliance.
"""

import sqlite3
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Optional

from .storage import AnalyticsStorage
from .tracker import EventType


class AnalyticsCollector:
    """
    Collects and aggregates analytics data from raw events.

    Privacy-first approach:
    - No PII storage
    - Anonymized aggregation
    - Local-only by default
    - Configurable retention
    """

    def __init__(
        self,
        storage: Optional[AnalyticsStorage] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize analytics collector.

        Args:
            storage: Analytics storage backend
            db_path: Path to analytics database
        """
        self.storage = storage or AnalyticsStorage(db_path=db_path)
        self.db_path = self.storage.db_path

    def collect_query_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Collect query-related metrics for a user.

        Args:
            user_id: User identifier (anonymized)
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary of query metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get all query events
            cursor = conn.execute("""
                SELECT *
                FROM events
                WHERE user_id = ?
                    AND timestamp >= ?
                    AND timestamp <= ?
                    AND event_type IN ('query', 'voice_query')
                ORDER BY timestamp
            """, (user_id, start_date.isoformat(), end_date.isoformat()))

            events = cursor.fetchall()

            if not events:
                return self._empty_query_metrics()

            # Calculate metrics
            total_queries = len(events)
            voice_queries = sum(1 for e in events if e['voice_input'])
            text_queries = total_queries - voice_queries
            with_patient_context = sum(1 for e in events if e['patient_context'])

            # Confidence metrics
            high_confidence = sum(1 for e in events if e['confidence'] == 'high')
            avg_confidence = high_confidence / total_queries if total_queries > 0 else 0

            # Citations
            total_citations = sum(e['citation_count'] or 0 for e in events)
            avg_citations = total_citations / total_queries if total_queries > 0 else 0

            # Latency metrics
            latencies = [e['latency_ms'] for e in events if e['latency_ms']]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            sorted_latencies = sorted(latencies)
            median_latency = (
                sorted_latencies[len(sorted_latencies) // 2]
                if sorted_latencies else 0
            )
            p95_index = int(len(sorted_latencies) * 0.95)
            p95_latency = sorted_latencies[p95_index] if sorted_latencies else 0

            # Peak hours
            hours = [datetime.fromisoformat(e['timestamp']).hour for e in events]
            hour_counts = {}
            for hour in hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            peak_hours = sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:3]

            # Weekday distribution
            weekday_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekdays = [datetime.fromisoformat(e['timestamp']).weekday() for e in events]
            weekday_dist = {}
            for wd in weekdays:
                day_name = weekday_map[wd]
                weekday_dist[day_name] = weekday_dist.get(day_name, 0) + 1

            # Query complexity
            query_lengths = [e['query_length'] or 0 for e in events]
            avg_query_length = sum(query_lengths) / len(query_lengths) if query_lengths else 0
            complex_queries = sum(1 for length in query_lengths if length > 100)

            # Error rate
            errors = sum(1 for e in events if not e['success'])
            error_rate = errors / total_queries if total_queries > 0 else 0

            return {
                'total_queries': total_queries,
                'voice_queries': voice_queries,
                'text_queries': text_queries,
                'queries_with_patient_context': with_patient_context,
                'avg_confidence_score': avg_confidence,
                'high_confidence_rate': avg_confidence,
                'avg_citations_per_query': avg_citations,
                'avg_latency_ms': avg_latency,
                'median_latency_ms': median_latency,
                'p95_latency_ms': p95_latency,
                'peak_hours': peak_hours,
                'weekday_distribution': weekday_dist,
                'avg_query_length': avg_query_length,
                'complex_queries_count': complex_queries,
                'error_count': errors,
                'error_rate': error_rate,
            }

    def collect_prescription_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Collect prescription-related metrics.

        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary of prescription metrics
        """
        # This would integrate with the prescription module's database
        # For now, return empty structure
        return {
            'total_prescriptions': 0,
            'total_medications_prescribed': 0,
            'avg_medications_per_prescription': 0.0,
            'generic_count': 0,
            'brand_count': 0,
            'generic_percentage': 0.0,
            'antibiotic_prescriptions': 0,
            'antibiotic_percentage': 0.0,
            'safety_score': 1.0,
        }

    def collect_learning_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Collect learning and CME metrics.

        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary of learning metrics
        """
        # This would integrate with the learning module's database
        # For now, return empty structure
        return {
            'total_cme_credits': 0.0,
            'category_1_credits': 0.0,
            'category_2_credits': 0.0,
            'category_3_credits': 0.0,
            'total_learning_activities': 0,
            'quizzes_attempted': 0,
            'quizzes_passed': 0,
            'avg_quiz_score': 0.0,
            'current_streak': 0,
            'longest_streak': 0,
        }

    def collect_usage_metrics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Collect overall usage metrics.

        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary of usage metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get sessions
            cursor = conn.execute("""
                SELECT *
                FROM sessions
                WHERE user_id = ?
                    AND started_at >= ?
                    AND started_at <= ?
            """, (user_id, start_date.isoformat(), end_date.isoformat()))

            sessions = cursor.fetchall()

            if not sessions:
                return self._empty_usage_metrics(start_date, end_date)

            # Calculate metrics
            total_sessions = len(sessions)

            # Active days
            session_dates = set()
            for session in sessions:
                started = datetime.fromisoformat(session['started_at'])
                session_dates.add(started.date())
            active_days = len(session_dates)

            # Session duration
            total_duration = 0
            for session in sessions:
                if session['ended_at']:
                    started = datetime.fromisoformat(session['started_at'])
                    ended = datetime.fromisoformat(session['ended_at'])
                    total_duration += (ended - started).total_seconds()

            avg_session_duration = (
                total_duration / total_sessions if total_sessions > 0 else 0
            )

            # Feature usage
            queries_count = sum(s['query_count'] or 0 for s in sessions)
            drug_checks_count = sum(s['drug_check_count'] or 0 for s in sessions)
            voice_queries_count = sum(s['voice_query_count'] or 0 for s in sessions)

            # Platform distribution
            desktop_sessions = sum(1 for s in sessions if s['platform'] == 'desktop')
            web_sessions = sum(1 for s in sessions if s['platform'] == 'web')
            mobile_sessions = sum(1 for s in sessions if s['platform'] == 'mobile')

            # Offline usage
            offline_sessions = sum(1 for s in sessions if s['is_offline'])
            offline_percentage = (
                offline_sessions / total_sessions * 100 if total_sessions > 0 else 0
            )

            # Engagement
            period_days = (end_date - start_date).days + 1
            avg_queries_per_day = queries_count / period_days if period_days > 0 else 0

            # Most active day
            day_query_counts = {}
            for session in sessions:
                started = datetime.fromisoformat(session['started_at'])
                day = started.date()
                day_query_counts[day] = day_query_counts.get(day, 0) + session['query_count']

            most_active_day = (
                max(day_query_counts.keys(), key=lambda d: day_query_counts[d])
                if day_query_counts else None
            )

            return {
                'active_days': active_days,
                'total_sessions': total_sessions,
                'avg_session_duration_seconds': avg_session_duration,
                'queries_count': queries_count,
                'drug_checks_count': drug_checks_count,
                'desktop_sessions': desktop_sessions,
                'web_sessions': web_sessions,
                'mobile_sessions': mobile_sessions,
                'offline_sessions': offline_sessions,
                'offline_percentage': offline_percentage,
                'avg_queries_per_day': avg_queries_per_day,
                'most_active_day': most_active_day.isoformat() if most_active_day else None,
            }

    def aggregate_daily(self, target_date: date):
        """
        Aggregate metrics for a specific day.

        Args:
            target_date: Date to aggregate
        """
        start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            # Get all users active on this day
            cursor = conn.execute("""
                SELECT DISTINCT user_id
                FROM events
                WHERE date(timestamp) = ?
            """, (target_date.isoformat(),))

            users = [row[0] for row in cursor.fetchall()]

            for user_id in users:
                # Collect metrics for this user
                query_metrics = self.collect_query_metrics(user_id, start_dt, end_dt)
                usage_metrics = self.collect_usage_metrics(user_id, start_dt, end_dt)

                # Store aggregated metrics
                # This could be stored in a separate aggregated_metrics table
                # For now, we rely on on-the-fly calculation

    def backfill_metrics(self, days: int = 30):
        """
        Backfill aggregated metrics for the past N days.

        Args:
            days: Number of days to backfill
        """
        today = date.today()
        for i in range(days):
            target_date = today - timedelta(days=i)
            self.aggregate_daily(target_date)

    def _empty_query_metrics(self) -> dict:
        """Return empty query metrics structure."""
        return {
            'total_queries': 0,
            'voice_queries': 0,
            'text_queries': 0,
            'queries_with_patient_context': 0,
            'avg_confidence_score': 0.0,
            'high_confidence_rate': 0.0,
            'avg_citations_per_query': 0.0,
            'avg_latency_ms': 0.0,
            'median_latency_ms': 0.0,
            'p95_latency_ms': 0.0,
            'peak_hours': [],
            'weekday_distribution': {},
            'avg_query_length': 0.0,
            'complex_queries_count': 0,
            'error_count': 0,
            'error_rate': 0.0,
        }

    def _empty_usage_metrics(self, start_date: datetime, end_date: datetime) -> dict:
        """Return empty usage metrics structure."""
        return {
            'active_days': 0,
            'total_sessions': 0,
            'avg_session_duration_seconds': 0.0,
            'queries_count': 0,
            'drug_checks_count': 0,
            'desktop_sessions': 0,
            'web_sessions': 0,
            'mobile_sessions': 0,
            'offline_sessions': 0,
            'offline_percentage': 0.0,
            'avg_queries_per_day': 0.0,
            'most_active_day': None,
        }


__all__ = ["AnalyticsCollector"]
