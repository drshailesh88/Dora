"""
Analytics API Endpoints

Provides REST API for practice analytics:
- Dashboard data
- Query patterns
- Prescription analytics
- Learning metrics
- Peer comparisons
- Insights
- Reports
"""

from datetime import date
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from ..analytics import (
    AnalyticsService,
    DashboardData,
    ComparisonType,
    TimeGranularity,
)


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Initialize analytics service
analytics_service = AnalyticsService()


# Request/Response Models
class PeriodQuery(BaseModel):
    """Query parameters for time period."""
    days: int = 30


class ComparisonQuery(BaseModel):
    """Query parameters for peer comparison."""
    comparison_type: str = "same_specialty"
    days: int = 30
    specialty: Optional[str] = None


# Dashboard Endpoints
@router.get("/dashboard")
async def get_dashboard(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
) -> DashboardData:
    """
    Get comprehensive dashboard data.

    Returns all metrics, charts, and insights for the analytics dashboard.
    """
    try:
        dashboard_data = analytics_service.get_dashboard_data(user_id, days)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


# Query Analytics Endpoints
@router.get("/queries")
async def get_query_analytics(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get detailed query pattern analytics.

    Returns:
    - Query volume metrics
    - Specialty distribution
    - Peak usage times
    - Top topics
    - Complexity analysis
    """
    try:
        end_date = date.today()
        start_date = date.today()
        start_date = start_date.replace(day=1)

        from ..analytics import QueryPatternAnalyzer
        analyzer = QueryPatternAnalyzer()

        query_analytics = analyzer.analyze_queries(user_id, start_date, end_date)
        return query_analytics.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/trends")
async def get_query_trends(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily", regex="^(hourly|daily|weekly|monthly)$"),
):
    """
    Get query volume trends over time.

    Returns time series data for charting.
    """
    try:
        from datetime import timedelta
        from ..analytics import QueryPatternAnalyzer, TimeGranularity

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = QueryPatternAnalyzer()
        granularity_enum = TimeGranularity(granularity)

        trends = analyzer.get_query_trends(user_id, start_date, end_date, granularity_enum)
        return trends.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queries/specialties")
async def get_specialty_breakdown(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get detailed metrics by medical specialty.

    Returns metrics for each specialty the user queries about.
    """
    try:
        from datetime import timedelta
        from ..analytics import QueryPatternAnalyzer

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = QueryPatternAnalyzer()
        specialty_metrics = analyzer.get_specialty_breakdown(user_id, start_date, end_date)

        return [m.model_dump() for m in specialty_metrics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Prescription Analytics Endpoints
@router.get("/prescriptions")
async def get_prescription_analytics(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get prescription pattern analytics.

    Returns:
    - Generic vs brand usage
    - Antibiotic stewardship metrics
    - Drug class distribution
    - Safety scores
    - Cost analysis
    """
    try:
        from datetime import timedelta
        from ..analytics import PrescriptionAnalyzer

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = PrescriptionAnalyzer()
        patterns = analyzer.analyze_prescriptions(user_id, start_date, end_date)

        return patterns.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prescriptions/stewardship")
async def get_antibiotic_stewardship(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get antibiotic stewardship score and recommendations.

    Returns stewardship metrics and best practices suggestions.
    """
    try:
        from datetime import timedelta
        from ..analytics import PrescriptionAnalyzer

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = PrescriptionAnalyzer()
        patterns = analyzer.analyze_prescriptions(user_id, start_date, end_date)
        stewardship = analyzer.get_antibiotic_stewardship_score(patterns)

        return stewardship
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Learning Analytics Endpoints
@router.get("/learning")
async def get_learning_analytics(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get learning and CME analytics.

    Returns:
    - CME credit accumulation
    - Quiz performance
    - Learning streaks
    - Knowledge gaps
    - Topic mastery
    """
    try:
        from datetime import timedelta
        from ..analytics import LearningAnalyzer

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = LearningAnalyzer()
        metrics = analyzer.analyze_learning(user_id, start_date, end_date)

        return metrics.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/recommendations")
async def get_learning_recommendations(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get personalized learning recommendations.

    Returns tailored suggestions based on learning patterns and gaps.
    """
    try:
        from datetime import timedelta
        from ..analytics import LearningAnalyzer

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        analyzer = LearningAnalyzer()
        metrics = analyzer.analyze_learning(user_id, start_date, end_date)
        recommendations = analyzer.get_learning_recommendations(metrics)

        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Peer Comparison Endpoints
@router.get("/comparisons")
async def get_peer_comparison(
    user_id: str = Query(..., description="User identifier"),
    comparison_type: str = Query("same_specialty", regex="^(same_specialty|same_region|same_experience|all_users)$"),
    days: int = Query(30, ge=1, le=365),
    specialty: Optional[str] = Query(None, description="User's specialty"),
):
    """
    Compare performance with peers.

    Returns anonymous benchmarking against similar doctors.
    """
    try:
        comparison_type_enum = ComparisonType(comparison_type)
        comparison = analytics_service.compare_with_peers(
            user_id, comparison_type_enum, days, specialty
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Insights Endpoints
@router.get("/insights")
async def get_insights(
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50, description="Maximum insights to return"),
):
    """
    Get AI-generated practice insights.

    Returns personalized insights including:
    - Achievements and milestones
    - Trend analysis
    - Recommendations
    - Learning opportunities
    """
    try:
        insights = analytics_service.get_insights(user_id, days, limit)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Report Endpoints
@router.get("/reports/monthly")
async def get_monthly_report(
    user_id: str = Query(..., description="User identifier"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12)"),
    year: Optional[int] = Query(None, ge=2020, le=2030, description="Year"),
):
    """
    Get comprehensive monthly practice report.

    Returns detailed analytics, insights, and trends for the month.
    """
    try:
        report = analytics_service.get_monthly_report(user_id, month, year)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/weekly")
async def get_weekly_digest(
    user_id: str = Query(..., description="User identifier"),
):
    """
    Get weekly practice digest.

    Returns summary of the past 7 days.
    """
    try:
        from ..analytics import ReportGenerator

        generator = ReportGenerator()
        digest = generator.generate_weekly_digest(user_id)
        return digest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/daily")
async def get_daily_summary(
    user_id: str = Query(..., description="User identifier"),
    date_str: Optional[str] = Query(None, description="Date (YYYY-MM-DD)"),
):
    """
    Get daily practice summary.

    Returns summary for a specific day (default: yesterday).
    """
    try:
        from ..analytics import ReportGenerator
        from datetime import datetime

        target_date = None
        if date_str:
            target_date = datetime.fromisoformat(date_str).date()

        generator = ReportGenerator()
        summary = generator.generate_daily_summary(user_id, target_date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/custom")
async def generate_custom_report(
    user_id: str = Query(..., description="User identifier"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    sections: Optional[List[str]] = Query(None, description="Sections to include"),
):
    """
    Generate custom date range report.

    Returns analytics for a custom time period.
    """
    try:
        from ..analytics import ReportGenerator
        from datetime import datetime

        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()

        generator = ReportGenerator()
        report = generator.generate_custom_report(user_id, start, end, sections)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chart Data Endpoints
@router.get("/charts/{chart_type}")
async def get_chart_data(
    chart_type: str,
    user_id: str = Query(..., description="User identifier"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get formatted chart data.

    Available chart types:
    - query_volume: Query volume over time
    - specialty_pie: Specialty distribution
    - cme_progress: CME progress gauge
    - drug_classes: Drug class bar chart
    """
    try:
        chart_data = analytics_service.get_chart_data(user_id, chart_type, days)
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints
@router.get("/export")
async def export_analytics(
    user_id: str = Query(..., description="User identifier"),
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Export analytics data.

    Exports data in JSON or CSV format.
    """
    try:
        file_path = analytics_service.export_data(user_id, format, days)

        # Read and return file
        with open(file_path, 'r') as f:
            content = f.read()

        media_type = "application/json" if format == "json" else "text/csv"
        filename = f"analytics_{user_id}.{format}"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def health_check():
    """
    Analytics service health check.

    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "1.0.0",
    }


__all__ = ["router"]
