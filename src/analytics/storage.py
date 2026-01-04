"""Analytics storage backend."""

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .tracker import QueryEvent, UserSession, EventType


class AnalyticsStorage:
    """
    SQLite-based storage for analytics data.

    Stores:
    - Query events
    - User sessions
    - Aggregated metrics

    Designed for privacy:
    - No PII storage
    - Data retention limits
    - Local-only by default
    """

    def __init__(
        self,
        db_path: Path | None = None,
        retention_days: int = 90,
    ):
        """
        Initialize analytics storage.

        Args:
            db_path: Path to SQLite database.
            retention_days: Days to retain data.
        """
        self.db_path = db_path or Path.home() / ".dora" / "analytics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    session_id TEXT,
                    user_id TEXT,
                    question TEXT,
                    query_length INTEGER,
                    answer_length INTEGER,
                    confidence TEXT,
                    citation_count INTEGER,
                    latency_ms INTEGER,
                    model_used TEXT,
                    patient_context INTEGER,
                    voice_input INTEGER,
                    success INTEGER,
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    license_tier TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    query_count INTEGER DEFAULT 0,
                    drug_check_count INTEGER DEFAULT 0,
                    voice_query_count INTEGER DEFAULT 0,
                    total_latency_ms INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    platform TEXT,
                    app_version TEXT,
                    is_offline INTEGER
                );

                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    total_queries INTEGER DEFAULT 0,
                    total_drug_checks INTEGER DEFAULT 0,
                    total_voice_queries INTEGER DEFAULT 0,
                    unique_users INTEGER DEFAULT 0,
                    avg_latency_ms REAL DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    high_confidence_rate REAL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);
            """)

    def save_events(self, events: list[QueryEvent]):
        """
        Save events to database.

        Args:
            events: List of events to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute("""
                    INSERT OR REPLACE INTO events (
                        event_id, timestamp, event_type, session_id, user_id,
                        question, query_length, answer_length, confidence,
                        citation_count, latency_ms, model_used, patient_context,
                        voice_input, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.session_id,
                    event.user_id,
                    event.question,
                    event.query_length,
                    event.answer_length,
                    event.confidence,
                    event.citation_count,
                    event.latency_ms,
                    event.model_used,
                    1 if event.patient_context else 0,
                    1 if event.voice_input else 0,
                    1 if event.success else 0,
                    event.error_message,
                ))

    def save_session(self, session: UserSession):
        """
        Save session to database.

        Args:
            session: Session to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, user_id, license_tier, started_at, ended_at,
                    query_count, drug_check_count, voice_query_count,
                    total_latency_ms, error_count, platform, app_version, is_offline
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.license_tier,
                session.started_at.isoformat(),
                session.ended_at.isoformat() if session.ended_at else None,
                session.query_count,
                session.drug_check_count,
                session.voice_query_count,
                session.total_latency_ms,
                session.error_count,
                session.platform,
                session.app_version,
                1 if session.is_offline else 0,
            ))

    def get_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: EventType | None = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Query events from database.

        Args:
            start_date: Start of date range.
            end_date: End of date range.
            event_type: Filter by event type.
            limit: Maximum events to return.

        Returns:
            List of event dicts.
        """
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict]:
        """
        Get daily aggregated metrics.

        Args:
            start_date: Start of date range.
            end_date: End of date range.

        Returns:
            List of daily metric dicts.
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    date(timestamp) as date,
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN event_type = 'drug_check' THEN 1 ELSE 0 END) as drug_checks,
                    SUM(CASE WHEN voice_input = 1 THEN 1 ELSE 0 END) as voice_queries,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors,
                    AVG(CASE WHEN confidence = 'high' THEN 1.0 ELSE 0.0 END) as high_confidence_rate
                FROM events
                WHERE timestamp >= ? AND timestamp <= ?
                    AND event_type IN ('query', 'voice_query', 'drug_check')
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat()))

            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(
        self,
        days: int = 30,
    ) -> dict:
        """
        Get summary statistics.

        Args:
            days: Number of days to include.

        Returns:
            Summary statistics dict.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_events,
                    SUM(CASE WHEN event_type = 'query' THEN 1 ELSE 0 END) as total_queries,
                    SUM(CASE WHEN event_type = 'drug_check' THEN 1 ELSE 0 END) as total_drug_checks,
                    SUM(CASE WHEN voice_input = 1 THEN 1 ELSE 0 END) as total_voice,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as total_errors,
                    AVG(CASE WHEN confidence = 'high' THEN 1.0 ELSE 0.0 END) as high_confidence_rate
                FROM events
                WHERE timestamp >= ?
            """, (start_date.isoformat(),))

            row = cursor.fetchone()
            return {
                "period_days": days,
                "total_events": row[0] or 0,
                "total_queries": row[1] or 0,
                "total_drug_checks": row[2] or 0,
                "total_voice_queries": row[3] or 0,
                "unique_users": row[4] or 0,
                "avg_latency_ms": row[5] or 0,
                "total_errors": row[6] or 0,
                "high_confidence_rate": row[7] or 0,
                "error_rate": (row[6] or 0) / (row[0] or 1),
            }

    def get_popular_queries(self, limit: int = 20) -> list[dict]:
        """
        Get most common query patterns.

        Args:
            limit: Number of queries to return.

        Returns:
            List of popular query patterns.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    question,
                    COUNT(*) as count,
                    AVG(latency_ms) as avg_latency,
                    AVG(CASE WHEN confidence = 'high' THEN 1.0 ELSE 0.0 END) as high_conf_rate
                FROM events
                WHERE event_type = 'query' AND question != ''
                GROUP BY question
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            return [
                {
                    "query": row[0],
                    "count": row[1],
                    "avg_latency": row[2],
                    "high_confidence_rate": row[3],
                }
                for row in cursor.fetchall()
            ]

    def cleanup_old_data(self):
        """Remove data older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM events WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            conn.execute(
                "DELETE FROM sessions WHERE started_at < ?",
                (cutoff.isoformat(),)
            )
            conn.execute("VACUUM")

    def export_to_json(self, output_path: Path) -> int:
        """
        Export analytics data to JSON.

        Args:
            output_path: Output file path.

        Returns:
            Number of records exported.
        """
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.get_summary_stats(),
            "daily_metrics": self.get_daily_metrics(),
            "popular_queries": self.get_popular_queries(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return len(data.get("daily_metrics", []))
