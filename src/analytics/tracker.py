"""Usage tracking for analytics."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of tracked events."""

    QUERY = "query"
    DRUG_CHECK = "drug_check"
    VOICE_QUERY = "voice_query"
    DOCUMENT_INGEST = "document_ingest"
    LOGIN = "login"
    LOGOUT = "logout"
    LICENSE_CHECK = "license_check"
    ERROR = "error"


@dataclass
class QueryEvent:
    """A query event for analytics."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType = EventType.QUERY

    # Query details
    question: str = ""
    query_length: int = 0

    # Response details
    answer_length: int = 0
    confidence: str = ""
    citation_count: int = 0
    latency_ms: int = 0

    # Context
    user_id: str | None = None
    session_id: str | None = None
    patient_context: bool = False
    voice_input: bool = False

    # Model info
    model_used: str = ""
    embedding_model: str = ""

    # Status
    success: bool = True
    error_message: str | None = None


@dataclass
class UserSession:
    """A user session for analytics."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    license_tier: str = "free"

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None

    # Aggregated stats
    query_count: int = 0
    drug_check_count: int = 0
    voice_query_count: int = 0
    total_latency_ms: int = 0
    error_count: int = 0

    # Device info
    platform: str = ""
    app_version: str = ""
    is_offline: bool = False


class UsageTracker:
    """
    Track usage analytics for Dora.

    Provides privacy-respecting usage tracking for:
    - Query patterns and performance
    - Feature usage
    - Error rates
    - User engagement
    """

    def __init__(self, storage: "AnalyticsStorage" = None):
        """
        Initialize usage tracker.

        Args:
            storage: Storage backend for analytics.
        """
        from .storage import AnalyticsStorage

        self.storage = storage or AnalyticsStorage()
        self.current_session: UserSession | None = None
        self._events_buffer: list[QueryEvent] = []
        self._buffer_size = 10

    def start_session(
        self,
        user_id: str = "",
        license_tier: str = "free",
        platform: str = "",
        app_version: str = "",
    ) -> UserSession:
        """
        Start a new user session.

        Args:
            user_id: User identifier (anonymized).
            license_tier: License tier.
            platform: Platform (desktop/web/mobile).
            app_version: Application version.

        Returns:
            UserSession object.
        """
        self.current_session = UserSession(
            user_id=user_id,
            license_tier=license_tier,
            platform=platform,
            app_version=app_version,
        )

        # Log session start
        self._log_event(QueryEvent(
            event_type=EventType.LOGIN,
            user_id=user_id,
            session_id=self.current_session.session_id,
        ))

        return self.current_session

    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.ended_at = datetime.now(timezone.utc)

            # Log session end
            self._log_event(QueryEvent(
                event_type=EventType.LOGOUT,
                user_id=self.current_session.user_id,
                session_id=self.current_session.session_id,
            ))

            # Save session
            self.storage.save_session(self.current_session)

            # Flush remaining events
            self._flush_buffer()

            self.current_session = None

    def track_query(
        self,
        question: str,
        answer: str,
        confidence: str,
        citation_count: int,
        latency_ms: int,
        model_used: str = "",
        patient_context: bool = False,
        voice_input: bool = False,
        success: bool = True,
        error_message: str | None = None,
    ):
        """
        Track a query event.

        Args:
            question: The question asked (will be truncated for privacy).
            answer: The answer provided (will be truncated).
            confidence: Confidence level.
            citation_count: Number of citations.
            latency_ms: Response latency.
            model_used: Model used for synthesis.
            patient_context: Whether patient context was used.
            voice_input: Whether voice input was used.
            success: Whether query succeeded.
            error_message: Error message if failed.
        """
        event = QueryEvent(
            event_type=EventType.VOICE_QUERY if voice_input else EventType.QUERY,
            question=question[:100] if question else "",  # Truncate for privacy
            query_length=len(question) if question else 0,
            answer_length=len(answer) if answer else 0,
            confidence=confidence,
            citation_count=citation_count,
            latency_ms=latency_ms,
            model_used=model_used,
            patient_context=patient_context,
            voice_input=voice_input,
            success=success,
            error_message=error_message,
            user_id=self.current_session.user_id if self.current_session else None,
            session_id=self.current_session.session_id if self.current_session else None,
        )

        # Update session stats
        if self.current_session:
            self.current_session.query_count += 1
            if voice_input:
                self.current_session.voice_query_count += 1
            self.current_session.total_latency_ms += latency_ms
            if not success:
                self.current_session.error_count += 1

        self._log_event(event)

    def track_drug_check(
        self,
        drug_count: int,
        interaction_count: int,
        latency_ms: int,
        success: bool = True,
    ):
        """
        Track a drug interaction check.

        Args:
            drug_count: Number of drugs checked.
            interaction_count: Number of interactions found.
            latency_ms: Response latency.
            success: Whether check succeeded.
        """
        event = QueryEvent(
            event_type=EventType.DRUG_CHECK,
            query_length=drug_count,  # Repurpose for drug count
            citation_count=interaction_count,  # Repurpose for interaction count
            latency_ms=latency_ms,
            success=success,
            user_id=self.current_session.user_id if self.current_session else None,
            session_id=self.current_session.session_id if self.current_session else None,
        )

        if self.current_session:
            self.current_session.drug_check_count += 1

        self._log_event(event)

    def track_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None,
    ):
        """
        Track an error event.

        Args:
            error_type: Type of error.
            error_message: Error message.
            context: Additional context.
        """
        event = QueryEvent(
            event_type=EventType.ERROR,
            question=error_type,
            error_message=error_message[:200] if error_message else "",
            success=False,
            user_id=self.current_session.user_id if self.current_session else None,
            session_id=self.current_session.session_id if self.current_session else None,
        )

        if self.current_session:
            self.current_session.error_count += 1

        self._log_event(event)

    def _log_event(self, event: QueryEvent):
        """Add event to buffer and flush if needed."""
        self._events_buffer.append(event)

        if len(self._events_buffer) >= self._buffer_size:
            self._flush_buffer()

    def _flush_buffer(self):
        """Flush events buffer to storage."""
        if self._events_buffer:
            self.storage.save_events(self._events_buffer)
            self._events_buffer.clear()

    def get_session_stats(self) -> dict:
        """Get current session statistics."""
        if not self.current_session:
            return {}

        duration = (
            datetime.now(timezone.utc) - self.current_session.started_at
        ).total_seconds()

        avg_latency = (
            self.current_session.total_latency_ms / self.current_session.query_count
            if self.current_session.query_count > 0
            else 0
        )

        return {
            "session_id": self.current_session.session_id,
            "duration_seconds": duration,
            "query_count": self.current_session.query_count,
            "drug_check_count": self.current_session.drug_check_count,
            "voice_query_count": self.current_session.voice_query_count,
            "avg_latency_ms": avg_latency,
            "error_count": self.current_session.error_count,
            "error_rate": (
                self.current_session.error_count / self.current_session.query_count
                if self.current_session.query_count > 0
                else 0
            ),
        }
