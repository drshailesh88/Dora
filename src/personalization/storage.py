"""Storage layer for personalization data."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.personalization.models import (
    DoctorProfile,
    QueryHistory,
    QueryPattern,
)


class PersonalizationStorage:
    """SQLite-based storage for personalization data."""

    def __init__(self, db_path: str = "data/personalization.db"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Doctor profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctor_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    last_query_at TIMESTAMP
                )
            """)

            # Query history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    category TEXT,
                    detected_specialty TEXT,
                    specialty_confidence REAL,
                    mentioned_drugs TEXT,
                    mentioned_conditions TEXT,
                    mentioned_procedures TEXT,
                    had_patient_context BOOLEAN,
                    result_count INTEGER,
                    user_feedback INTEGER,
                    clicked_results TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES doctor_profiles(user_id)
                )
            """)

            # Query patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    user_id TEXT PRIMARY KEY,
                    pattern_data TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES doctor_profiles(user_id)
                )
            """)

            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_history_user_id
                ON query_history(user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_history_timestamp
                ON query_history(timestamp DESC)
            """)

            conn.commit()

    def save_profile(self, profile: DoctorProfile) -> None:
        """
        Save or update doctor profile.

        Args:
            profile: Profile to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            profile_json = profile.model_dump_json()

            cursor.execute("""
                INSERT OR REPLACE INTO doctor_profiles
                (id, user_id, profile_data, created_at, updated_at, last_query_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                profile.id,
                profile.user_id,
                profile_json,
                profile.created_at,
                profile.updated_at,
                profile.last_query_at,
            ))

            conn.commit()

    def get_profile(self, user_id: str) -> Optional[DoctorProfile]:
        """
        Get doctor profile by user ID.

        Args:
            user_id: User ID.

        Returns:
            Doctor profile or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT profile_data FROM doctor_profiles
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()

            if row:
                return DoctorProfile.model_validate_json(row[0])

            return None

    def get_profile_by_id(self, profile_id: str) -> Optional[DoctorProfile]:
        """
        Get doctor profile by profile ID.

        Args:
            profile_id: Profile ID.

        Returns:
            Doctor profile or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT profile_data FROM doctor_profiles
                WHERE id = ?
            """, (profile_id,))

            row = cursor.fetchone()

            if row:
                return DoctorProfile.model_validate_json(row[0])

            return None

    def save_query_history(self, query_record: QueryHistory) -> None:
        """
        Save query history record.

        Args:
            query_record: Query history to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO query_history
                (id, user_id, query, category, detected_specialty, specialty_confidence,
                 mentioned_drugs, mentioned_conditions, mentioned_procedures,
                 had_patient_context, result_count, user_feedback, clicked_results, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_record.id,
                query_record.user_id,
                query_record.query,
                query_record.category.value if query_record.category else None,
                query_record.detected_specialty.value if query_record.detected_specialty else None,
                query_record.specialty_confidence,
                json.dumps(query_record.mentioned_drugs),
                json.dumps(query_record.mentioned_conditions),
                json.dumps(query_record.mentioned_procedures),
                query_record.had_patient_context,
                query_record.result_count,
                query_record.user_feedback,
                json.dumps(query_record.clicked_results),
                query_record.timestamp,
            ))

            conn.commit()

    def get_query_history(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[QueryHistory]:
        """
        Get query history for user.

        Args:
            user_id: User ID.
            limit: Maximum number of records.
            offset: Offset for pagination.

        Returns:
            List of query history records.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM query_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))

            rows = cursor.fetchall()

            return [self._row_to_query_history(row) for row in rows]

    def get_recent_query_history(
        self,
        user_id: str,
        days: int = 30,
    ) -> list[QueryHistory]:
        """
        Get recent query history.

        Args:
            user_id: User ID.
            days: Number of days to look back.

        Returns:
            List of recent query history records.
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM query_history
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (user_id, cutoff_date))

            rows = cursor.fetchall()

            return [self._row_to_query_history(row) for row in rows]

    def update_query_feedback(
        self,
        query_id: str,
        feedback_rating: int,
        clicked_results: Optional[list[str]] = None,
    ) -> None:
        """
        Update query feedback.

        Args:
            query_id: Query ID.
            feedback_rating: 1-5 rating.
            clicked_results: IDs of clicked results.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE query_history
                SET user_feedback = ?, clicked_results = ?
                WHERE id = ?
            """, (
                feedback_rating,
                json.dumps(clicked_results) if clicked_results else None,
                query_id,
            ))

            conn.commit()

    def save_query_pattern(self, pattern: QueryPattern) -> None:
        """
        Save query pattern.

        Args:
            pattern: Query pattern to save.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            pattern_json = pattern.model_dump_json()

            cursor.execute("""
                INSERT OR REPLACE INTO query_patterns
                (user_id, pattern_data, updated_at)
                VALUES (?, ?, ?)
            """, (
                pattern.user_id,
                pattern_json,
                pattern.updated_at,
            ))

            conn.commit()

    def get_query_pattern(self, user_id: str) -> Optional[QueryPattern]:
        """
        Get query pattern for user.

        Args:
            user_id: User ID.

        Returns:
            Query pattern or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pattern_data FROM query_patterns
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()

            if row:
                return QueryPattern.model_validate_json(row[0])

            return None

    def delete_user_data(self, user_id: str) -> None:
        """
        Delete all data for a user (for privacy compliance).

        Args:
            user_id: User ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM query_patterns WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM query_history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM doctor_profiles WHERE user_id = ?", (user_id,))

            conn.commit()

    def get_statistics(self) -> dict:
        """
        Get overall statistics.

        Returns:
            Dictionary of statistics.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total profiles
            cursor.execute("SELECT COUNT(*) FROM doctor_profiles")
            total_profiles = cursor.fetchone()[0]

            # Total queries
            cursor.execute("SELECT COUNT(*) FROM query_history")
            total_queries = cursor.fetchone()[0]

            # Queries with feedback
            cursor.execute("SELECT COUNT(*) FROM query_history WHERE user_feedback IS NOT NULL")
            queries_with_feedback = cursor.fetchone()[0]

            # Average feedback
            cursor.execute("SELECT AVG(user_feedback) FROM query_history WHERE user_feedback IS NOT NULL")
            avg_feedback = cursor.fetchone()[0] or 0.0

            return {
                "total_profiles": total_profiles,
                "total_queries": total_queries,
                "queries_with_feedback": queries_with_feedback,
                "average_feedback": round(avg_feedback, 2),
            }

    def count_queries_by_specialty(self, user_id: str, specialty: str) -> int:
        """
        Count queries for a specific specialty.

        Args:
            user_id: User ID.
            specialty: Specialty name.

        Returns:
            Count of queries in this specialty.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM query_history
                WHERE user_id = ? AND detected_specialty = ?
            """, (user_id, specialty))

            count = cursor.fetchone()[0]
            return count or 0

    def get_specialty_query_counts(self, user_id: str) -> dict[str, int]:
        """
        Get query counts for all specialties for a user.

        Args:
            user_id: User ID.

        Returns:
            Dictionary mapping specialty name to query count.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT detected_specialty, COUNT(*) as count
                FROM query_history
                WHERE user_id = ? AND detected_specialty IS NOT NULL
                GROUP BY detected_specialty
            """, (user_id,))

            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    def _row_to_query_history(self, row: sqlite3.Row) -> QueryHistory:
        """Convert database row to QueryHistory model."""
        from src.personalization.models import MedicalSpecialty, QueryCategory

        return QueryHistory(
            id=row["id"],
            user_id=row["user_id"],
            query=row["query"],
            category=QueryCategory(row["category"]) if row["category"] else None,
            detected_specialty=MedicalSpecialty(row["detected_specialty"]) if row["detected_specialty"] else None,
            specialty_confidence=row["specialty_confidence"] or 0.0,
            mentioned_drugs=json.loads(row["mentioned_drugs"]) if row["mentioned_drugs"] else [],
            mentioned_conditions=json.loads(row["mentioned_conditions"]) if row["mentioned_conditions"] else [],
            mentioned_procedures=json.loads(row["mentioned_procedures"]) if row["mentioned_procedures"] else [],
            had_patient_context=bool(row["had_patient_context"]),
            result_count=row["result_count"] or 0,
            user_feedback=row["user_feedback"],
            clicked_results=json.loads(row["clicked_results"]) if row["clicked_results"] else [],
            timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
        )
