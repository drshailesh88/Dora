"""
Error monitoring and alerting for Dora API.
Provides error tracking, aggregation, and notification capabilities.
"""

import os
import logging
import traceback
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Represents a captured error event."""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    stack_trace: str
    request_path: str
    request_method: str
    user_id: Optional[str]
    client_ip: str
    user_agent: str
    request_id: str
    severity: ErrorSeverity
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class ErrorAggregator:
    """Aggregates and groups similar errors."""

    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self._errors: Dict[str, List[ErrorEvent]] = defaultdict(list)
        self._last_cleanup = datetime.utcnow()

    def add(self, error: ErrorEvent) -> str:
        """Add error and return fingerprint."""
        fingerprint = self._get_fingerprint(error)
        self._errors[fingerprint].append(error)
        self._cleanup_old_errors()
        return fingerprint

    def get_error_count(self, fingerprint: str) -> int:
        """Get count of similar errors in time window."""
        return len(self._errors.get(fingerprint, []))

    def get_recent_errors(self, limit: int = 100) -> List[ErrorEvent]:
        """Get recent errors across all fingerprints."""
        all_errors = []
        for errors in self._errors.values():
            all_errors.extend(errors)
        return sorted(all_errors, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error patterns."""
        summary = {}
        for fingerprint, errors in self._errors.items():
            if errors:
                summary[fingerprint] = {
                    "count": len(errors),
                    "first_seen": min(e.timestamp for e in errors).isoformat(),
                    "last_seen": max(e.timestamp for e in errors).isoformat(),
                    "error_type": errors[0].error_type,
                    "message": errors[0].message[:100],
                    "severity": errors[0].severity.value,
                }
        return summary

    def _get_fingerprint(self, error: ErrorEvent) -> str:
        """Generate fingerprint for error grouping."""
        import hashlib
        data = f"{error.error_type}:{error.request_path}:{error.message[:50]}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _cleanup_old_errors(self):
        """Remove errors outside the time window."""
        now = datetime.utcnow()
        if (now - self._last_cleanup).seconds < 300:  # Cleanup every 5 min
            return

        cutoff = now - timedelta(minutes=self.window_minutes)
        for fingerprint in list(self._errors.keys()):
            self._errors[fingerprint] = [
                e for e in self._errors[fingerprint] if e.timestamp > cutoff
            ]
            if not self._errors[fingerprint]:
                del self._errors[fingerprint]

        self._last_cleanup = now


class AlertManager:
    """Manages error alerts and notifications."""

    def __init__(self):
        self._alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.MEDIUM: 10,
            ErrorSeverity.LOW: 50,
        }
        self._last_alerts: Dict[str, datetime] = {}
        self._cooldown_minutes = 30

    async def check_and_alert(
        self, error: ErrorEvent, count: int, fingerprint: str
    ):
        """Check if alert should be sent and send if necessary."""
        threshold = self._alert_thresholds.get(error.severity, 10)

        if count >= threshold:
            if self._should_alert(fingerprint):
                await self._send_alert(error, count, fingerprint)
                self._last_alerts[fingerprint] = datetime.utcnow()

    def _should_alert(self, fingerprint: str) -> bool:
        """Check if we should alert (respecting cooldown)."""
        last_alert = self._last_alerts.get(fingerprint)
        if not last_alert:
            return True
        return (datetime.utcnow() - last_alert).seconds > self._cooldown_minutes * 60

    async def _send_alert(
        self, error: ErrorEvent, count: int, fingerprint: str
    ):
        """Send alert notification."""
        alert_data = {
            "title": f"[{error.severity.value.upper()}] {error.error_type}",
            "message": error.message[:200],
            "count": count,
            "fingerprint": fingerprint,
            "path": error.request_path,
            "timestamp": error.timestamp.isoformat(),
        }

        # Log alert
        logger.critical(f"ERROR ALERT: {alert_data}")

        # Send to external services
        await self._notify_slack(alert_data)
        await self._notify_pagerduty(alert_data)
        await self._notify_email(alert_data)

    async def _notify_slack(self, alert_data: Dict[str, Any]):
        """Send alert to Slack."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            return

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": f":rotating_light: *Error Alert*",
                    "attachments": [{
                        "color": "danger",
                        "title": alert_data["title"],
                        "text": alert_data["message"],
                        "fields": [
                            {"title": "Count", "value": str(alert_data["count"]), "short": True},
                            {"title": "Path", "value": alert_data["path"], "short": True},
                        ],
                        "ts": int(datetime.utcnow().timestamp()),
                    }],
                }
                await session.post(webhook_url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _notify_pagerduty(self, alert_data: Dict[str, Any]):
        """Send alert to PagerDuty."""
        routing_key = os.getenv("PAGERDUTY_ROUTING_KEY")
        if not routing_key:
            return

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    "routing_key": routing_key,
                    "event_action": "trigger",
                    "payload": {
                        "summary": f"{alert_data['title']}: {alert_data['message'][:100]}",
                        "severity": "critical",
                        "source": "dora-api",
                        "custom_details": alert_data,
                    },
                }
                await session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                )
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")

    async def _notify_email(self, alert_data: Dict[str, Any]):
        """Send alert via email."""
        email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS")
        if not email_recipients:
            logger.debug("No alert email recipients configured")
            return

        try:
            from src.notifications.email_service import get_email_service

            email_service = get_email_service()
            recipients = [r.strip() for r in email_recipients.split(",")]

            for recipient in recipients:
                await email_service.send_alert_email(
                    to=recipient,
                    alert_title=alert_data["title"],
                    alert_message=alert_data["message"],
                    alert_data={
                        "count": alert_data["count"],
                        "path": alert_data["path"],
                        "fingerprint": alert_data["fingerprint"],
                        "timestamp": alert_data["timestamp"],
                    },
                )
            logger.info(f"Alert email sent to {len(recipients)} recipient(s)")
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")


class ErrorMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error monitoring."""

    def __init__(self, app):
        super().__init__(app)
        self.aggregator = ErrorAggregator()
        self.alert_manager = AlertManager()
        self._error_counter = 0

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            response = await call_next(request)

            # Track 4xx and 5xx errors
            if response.status_code >= 400:
                await self._track_http_error(request, response.status_code)

            return response

        except Exception as e:
            await self._track_exception(request, e)
            raise

    async def _track_exception(self, request: Request, exception: Exception):
        """Track unhandled exception."""
        import hashlib

        self._error_counter += 1
        error_id = f"err_{hashlib.md5(str(self._error_counter).encode()).hexdigest()[:12]}"

        error = ErrorEvent(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            error_type=type(exception).__name__,
            message=str(exception),
            stack_trace=traceback.format_exc(),
            request_path=request.url.path,
            request_method=request.method,
            user_id=getattr(request.state, "user", {}).get("id") if hasattr(request.state, "user") else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            request_id=getattr(request.state, "request_id", "unknown"),
            severity=self._classify_severity(exception),
            context={
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
            },
            tags=self._get_error_tags(exception),
        )

        fingerprint = self.aggregator.add(error)
        count = self.aggregator.get_error_count(fingerprint)

        # Check if we need to alert
        asyncio.create_task(
            self.alert_manager.check_and_alert(error, count, fingerprint)
        )

        # Log error
        logger.error(
            f"Exception: {error.error_type} | "
            f"Path: {error.request_path} | "
            f"Error ID: {error.error_id} | "
            f"Count: {count}"
        )

    async def _track_http_error(self, request: Request, status_code: int):
        """Track HTTP error response."""
        severity = ErrorSeverity.HIGH if status_code >= 500 else ErrorSeverity.LOW

        logger.log(
            logging.ERROR if status_code >= 500 else logging.WARNING,
            f"HTTP {status_code} | Path: {request.url.path} | "
            f"Method: {request.method}"
        )

    def _classify_severity(self, exception: Exception) -> ErrorSeverity:
        """Classify error severity based on exception type."""
        critical_types = ["DatabaseError", "ConnectionError", "TimeoutError"]
        high_types = ["ValueError", "KeyError", "TypeError", "ValidationError"]

        error_type = type(exception).__name__

        if error_type in critical_types:
            return ErrorSeverity.CRITICAL
        elif error_type in high_types:
            return ErrorSeverity.HIGH
        elif isinstance(exception, (PermissionError, FileNotFoundError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.MEDIUM

    def _get_error_tags(self, exception: Exception) -> List[str]:
        """Generate tags for error categorization."""
        tags = [type(exception).__name__]

        if "database" in str(exception).lower():
            tags.append("database")
        if "connection" in str(exception).lower():
            tags.append("network")
        if "timeout" in str(exception).lower():
            tags.append("timeout")
        if "auth" in str(exception).lower():
            tags.append("auth")

        return tags

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class HealthCheckService:
    """Health check service for monitoring."""

    def __init__(self):
        self._checks = {}

    def register_check(self, name: str, check_func):
        """Register a health check function."""
        self._checks[name] = check_func

    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check in self._checks.items():
            try:
                result = await check()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "checked_at": datetime.utcnow().isoformat(),
                }
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "checked_at": datetime.utcnow().isoformat(),
                }
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global instances
error_aggregator = ErrorAggregator()
alert_manager = AlertManager()
health_service = HealthCheckService()


def setup_error_monitoring(app):
    """Setup error monitoring for FastAPI app."""
    app.add_middleware(ErrorMonitoringMiddleware)

    # Register default health checks
    async def check_db():
        """Check SQLite database connectivity."""
        try:
            from src.auth.storage import get_auth_storage
            storage = get_auth_storage()
            # Try a simple query
            with storage._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def check_redis():
        """Check Redis connectivity."""
        try:
            from src.core.redis_client import get_redis_client
            redis_client = get_redis_client()
            # Use ping to check connection
            return redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def check_vector_store():
        """Check Qdrant vector store connectivity."""
        try:
            from src.retrieval.dense import DenseRetriever
            from src.core.config import settings

            # Try to connect to Qdrant
            from qdrant_client import QdrantClient
            client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=5.0,
            )
            # Check if we can list collections
            collections = client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False

    health_service.register_check("database", check_db)
    health_service.register_check("redis", check_redis)
    health_service.register_check("vector_store", check_vector_store)
