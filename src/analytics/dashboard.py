"""Analytics dashboard API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .storage import AnalyticsStorage
from .tracker import EventType


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Initialize storage (will be replaced by dependency injection)
storage = AnalyticsStorage()


class SummaryStats(BaseModel):
    """Summary statistics response."""

    period_days: int
    total_queries: int
    total_drug_checks: int
    total_voice_queries: int
    unique_users: int
    avg_latency_ms: float
    error_rate: float
    high_confidence_rate: float


class DailyMetric(BaseModel):
    """Daily metric response."""

    date: str
    total_queries: int
    drug_checks: int
    voice_queries: int
    unique_users: int
    avg_latency: float
    errors: int
    high_confidence_rate: float


class PopularQuery(BaseModel):
    """Popular query response."""

    query: str
    count: int
    avg_latency: float
    high_confidence_rate: float


@router.get("/summary", response_model=SummaryStats)
async def get_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get summary statistics for the specified period.

    Returns aggregated metrics including query counts, latency,
    error rates, and user engagement.
    """
    stats = storage.get_summary_stats(days=days)
    return SummaryStats(
        period_days=stats["period_days"],
        total_queries=stats["total_queries"],
        total_drug_checks=stats["total_drug_checks"],
        total_voice_queries=stats["total_voice_queries"],
        unique_users=stats["unique_users"],
        avg_latency_ms=stats["avg_latency_ms"],
        error_rate=stats["error_rate"],
        high_confidence_rate=stats["high_confidence_rate"],
    )


@router.get("/daily", response_model=list[DailyMetric])
async def get_daily_metrics(
    days: int = Query(30, ge=1, le=90, description="Number of days to include"),
):
    """
    Get daily metrics for charting.

    Returns per-day aggregated metrics for the specified period.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    metrics = storage.get_daily_metrics(start_date=start_date, end_date=end_date)

    return [
        DailyMetric(
            date=m["date"],
            total_queries=m["total_queries"] or 0,
            drug_checks=m["drug_checks"] or 0,
            voice_queries=m["voice_queries"] or 0,
            unique_users=m["unique_users"] or 0,
            avg_latency=m["avg_latency"] or 0,
            errors=m["errors"] or 0,
            high_confidence_rate=m["high_confidence_rate"] or 0,
        )
        for m in metrics
    ]


@router.get("/popular-queries", response_model=list[PopularQuery])
async def get_popular_queries(
    limit: int = Query(20, ge=1, le=100, description="Number of queries to return"),
):
    """
    Get most frequently asked queries.

    Returns popular query patterns with performance metrics.
    """
    queries = storage.get_popular_queries(limit=limit)

    return [
        PopularQuery(
            query=q["query"],
            count=q["count"],
            avg_latency=q["avg_latency"] or 0,
            high_confidence_rate=q["high_confidence_rate"] or 0,
        )
        for q in queries
    ]


@router.get("/realtime")
async def get_realtime_stats():
    """
    Get real-time statistics for dashboard.

    Returns current session counts and recent activity.
    """
    # Get stats for today
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    today_events = storage.get_events(
        start_date=today_start,
        limit=10000,
    )

    queries_today = sum(1 for e in today_events if e["event_type"] == "query")
    errors_today = sum(1 for e in today_events if not e["success"])

    return {
        "queries_today": queries_today,
        "drug_checks_today": sum(
            1 for e in today_events if e["event_type"] == "drug_check"
        ),
        "errors_today": errors_today,
        "error_rate_today": errors_today / queries_today if queries_today > 0 else 0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/export")
async def export_analytics(
    format: str = Query("json", regex="^(json|csv)$"),
):
    """
    Export analytics data.

    Exports summary data to the specified format.
    """
    from pathlib import Path
    import tempfile

    output_dir = Path(tempfile.gettempdir()) / "dora_analytics"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"analytics_{timestamp}.{format}"

    if format == "json":
        count = storage.export_to_json(output_path)
    else:
        # CSV export would go here
        count = 0

    return {
        "success": True,
        "file_path": str(output_path),
        "records_exported": count,
    }


class AnalyticsDashboard:
    """
    Dashboard widget for desktop/web UI.

    Provides formatted analytics for display.
    """

    def __init__(self, storage: AnalyticsStorage | None = None):
        self.storage = storage or AnalyticsStorage()

    def get_dashboard_data(self) -> dict:
        """Get all dashboard data."""
        return {
            "summary": self.storage.get_summary_stats(days=30),
            "daily": self.storage.get_daily_metrics(),
            "popular": self.storage.get_popular_queries(limit=10),
        }

    def format_summary_text(self) -> str:
        """Format summary as text for CLI."""
        stats = self.storage.get_summary_stats(days=30)

        return f"""
📊 Dora Analytics (Last 30 Days)
================================
Total Queries:     {stats['total_queries']:,}
Drug Checks:       {stats['total_drug_checks']:,}
Voice Queries:     {stats['total_voice_queries']:,}
Unique Users:      {stats['unique_users']:,}

Performance:
  Avg Latency:     {stats['avg_latency_ms']:.0f}ms
  Error Rate:      {stats['error_rate']*100:.1f}%
  High Confidence: {stats['high_confidence_rate']*100:.1f}%
"""

    def get_health_status(self) -> dict:
        """Get system health based on analytics."""
        stats = self.storage.get_summary_stats(days=1)

        # Define health thresholds
        status = "healthy"
        issues = []

        if stats["error_rate"] > 0.1:
            status = "degraded"
            issues.append("High error rate (>10%)")

        if stats["avg_latency_ms"] > 5000:
            status = "degraded"
            issues.append("High latency (>5s)")

        if stats["high_confidence_rate"] < 0.5:
            status = "warning"
            issues.append("Low confidence rate (<50%)")

        return {
            "status": status,
            "issues": issues,
            "metrics": {
                "error_rate": stats["error_rate"],
                "avg_latency_ms": stats["avg_latency_ms"],
                "high_confidence_rate": stats["high_confidence_rate"],
            },
        }
