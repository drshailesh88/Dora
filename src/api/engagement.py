"""
Engagement API Endpoints

RESTful API for daily briefings, alerts, trending queries, clinical pearls,
and engagement analytics.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth import get_current_user
from src.engagement import (
    get_engagement_service,
    DailyBriefing,
    TrendingQuery,
    TrendingPeriod,
    ClinicalPearl,
    NotificationPreference,
    EngagementStatistics,
)


router = APIRouter(prefix="/api/v1/engagement", tags=["engagement"])


# ==================== Request/Response Models ====================

class BriefingItemClickRequest(BaseModel):
    """Request to track briefing item click."""
    briefing_id: str
    item_id: str


class AlertActionRequest(BaseModel):
    """Request to perform action on alert."""
    alert_id: str
    action: str = Field(..., description="open, dismiss, acknowledge")


class PreferenceUpdateRequest(BaseModel):
    """Request to update notification preferences."""
    briefing_enabled: Optional[bool] = None
    briefing_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    briefing_days: Optional[list[int]] = Field(None, min_items=0, max_items=7)

    research_alerts: Optional[bool] = None
    guideline_alerts: Optional[bool] = None
    drug_alerts: Optional[bool] = None
    critical_only: Optional[bool] = None

    push_notifications: Optional[bool] = None
    email_digest: Optional[bool] = None
    in_app_only: Optional[bool] = None

    quiet_hours_enabled: Optional[bool] = None
    quiet_start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    quiet_end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")

    max_briefing_items: Optional[int] = Field(None, ge=3, le=15)
    include_trending: Optional[bool] = None
    include_pearls: Optional[bool] = None


class SessionTrackRequest(BaseModel):
    """Request to track user session."""
    duration_seconds: int = Field(..., ge=0)


class TrendingResponse(BaseModel):
    """Response with trending queries."""
    queries: list[dict[str, Any]]
    specialty: Optional[str] = None
    period: str
    computed_at: str


class EngagementInsightsResponse(BaseModel):
    """Response with engagement insights."""
    current_score: float
    average_score: float
    trend: str
    streak_days: int
    insights: list[str]
    recommendations: list[str]
    at_risk: bool


# ==================== Briefing Endpoints ====================

@router.get("/briefing", response_model=DailyBriefing)
async def get_daily_briefing(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    current_user: dict = Depends(get_current_user),
) -> DailyBriefing:
    """
    Get daily briefing for the user.

    Returns:
        Daily briefing with patient preview, pearls, alerts, trending.
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    # Get briefing
    briefing = service.get_briefing(user_id, date)

    if not briefing:
        # Generate briefing if not exists
        user_profile = {
            "user_id": user_id,
            "name": current_user.get("name", "Doctor"),
            "specialty": current_user.get("specialty", "general"),
        }

        briefing = await service.generate_daily_briefing(
            user_id=user_id,
            user_profile=user_profile,
        )

    # Mark as opened
    service.mark_briefing_opened(user_id, briefing.id)

    return briefing


@router.post("/briefing/click")
async def click_briefing_item(
    request: BriefingItemClickRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Track briefing item click.

    Args:
        request: Click tracking request

    Returns:
        Success message
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    service.click_briefing_item(
        user_id=user_id,
        briefing_id=request.briefing_id,
        item_id=request.item_id,
    )

    return {
        "status": "success",
        "message": "Click tracked",
    }


# ==================== Alert Endpoints ====================

@router.get("/alerts")
async def get_alerts(
    unread_only: bool = Query(False, description="Only unread alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get pending alerts for user.

    Args:
        unread_only: Only return unread alerts
        severity: Filter by severity level
        limit: Maximum number of alerts

    Returns:
        List of alerts
    """
    user_id = current_user["sub"]

    # In production, fetch from database
    # For now, return empty list
    return {
        "alerts": [],
        "total": 0,
        "unread": 0,
    }


@router.post("/alerts/action")
async def alert_action(
    request: AlertActionRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Perform action on alert.

    Args:
        request: Alert action request

    Returns:
        Success message
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    if request.action == "open":
        service.mark_alert_opened(user_id, request.alert_id)
    elif request.action == "dismiss":
        service.dismiss_alert(user_id, request.alert_id)
    elif request.action == "acknowledge":
        # Acknowledge alert
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {request.action}"
        )

    return {
        "status": "success",
        "message": f"Alert {request.action}ed",
        "alert_id": request.alert_id,
    }


# ==================== Trending Endpoints ====================

@router.get("/trending", response_model=TrendingResponse)
async def get_trending(
    period: TrendingPeriod = Query(TrendingPeriod.LAST_7D),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    current_user: dict = Depends(get_current_user),
) -> TrendingResponse:
    """
    Get trending queries.

    Args:
        period: Time period (last_24h, last_7d, last_30d)
        specialty: Filter by specialty (None for personalized)

    Returns:
        Trending queries
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    if specialty:
        # Get trending for specific specialty
        trending = service.get_trending(
            specialty=specialty,
            period=period,
        )
    else:
        # Get personalized trending
        user_profile = {
            "user_id": user_id,
            "specialty": current_user.get("specialty", "general"),
            "common_conditions": [],
        }
        trending = service.get_personalized_trending(
            user_id=user_id,
            user_profile=user_profile,
        )

    # Mark as viewed
    service.mark_trending_viewed(user_id)

    # Convert to dict
    queries = [
        {
            "query": t.query_text,
            "count": t.query_count,
            "unique_users": t.unique_users,
            "rank": t.rank,
            "trend": t.trend_direction,
            "related": t.related_queries,
        }
        for t in trending
    ]

    return TrendingResponse(
        queries=queries,
        specialty=specialty or current_user.get("specialty"),
        period=period.value,
        computed_at=datetime.utcnow().isoformat(),
    )


# ==================== Clinical Pearls Endpoints ====================

@router.get("/pearls/daily", response_model=ClinicalPearl)
async def get_daily_pearl(
    current_user: dict = Depends(get_current_user),
) -> ClinicalPearl:
    """
    Get daily clinical pearl.

    Returns:
        Clinical pearl for today
    """
    user_id = current_user["sub"]
    specialty = current_user.get("specialty", "general")

    service = get_engagement_service()
    pearl = service.get_daily_pearl(user_id, specialty)

    if not pearl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pearl available"
        )

    return pearl


@router.get("/pearls/quiz", response_model=ClinicalPearl)
async def get_pearl_quiz(
    current_user: dict = Depends(get_current_user),
) -> ClinicalPearl:
    """
    Get clinical pearl as quiz.

    Returns:
        Clinical pearl in quiz format
    """
    user_id = current_user["sub"]
    specialty = current_user.get("specialty", "general")

    service = get_engagement_service()
    pearl = service.get_pearl_quiz(user_id, specialty)

    if not pearl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz available"
        )

    return pearl


@router.get("/pearls/search")
async def search_pearls(
    q: str = Query(..., min_length=2, description="Search query"),
    specialty: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Search clinical pearls.

    Args:
        q: Search query
        specialty: Filter by specialty

    Returns:
        List of matching pearls
    """
    service = get_engagement_service()

    pearls = service.search_pearls(
        query=q,
        specialty=specialty,
    )

    return {
        "query": q,
        "results": [p.model_dump() for p in pearls],
        "count": len(pearls),
    }


# ==================== Preferences Endpoints ====================

@router.get("/preferences", response_model=NotificationPreference)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
) -> NotificationPreference:
    """
    Get notification preferences.

    Returns:
        User's notification preferences
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    return service.get_preferences(user_id)


@router.put("/preferences", response_model=NotificationPreference)
async def update_preferences(
    request: PreferenceUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> NotificationPreference:
    """
    Update notification preferences.

    Args:
        request: Preference updates

    Returns:
        Updated preferences
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    # Build updates dict (only non-None values)
    updates = {
        k: v for k, v in request.model_dump().items()
        if v is not None
    }

    preferences = service.update_preferences(user_id, **updates)

    return preferences


# ==================== Analytics Endpoints ====================

@router.get("/stats", response_model=EngagementInsightsResponse)
async def get_engagement_stats(
    current_user: dict = Depends(get_current_user),
) -> EngagementInsightsResponse:
    """
    Get engagement statistics and insights.

    Returns:
        Engagement insights with score, trend, and recommendations
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    insights = service.get_engagement_insights(user_id)

    return EngagementInsightsResponse(**insights)


@router.get("/stats/trend")
async def get_engagement_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get engagement trend over time.

    Args:
        days: Number of days to analyze

    Returns:
        Trend data with scores over time
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    trend = service.get_engagement_trend(user_id, days)

    return trend


@router.post("/stats/session")
async def track_session(
    request: SessionTrackRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Track user session.

    Args:
        request: Session tracking request

    Returns:
        Success message
    """
    user_id = current_user["sub"]
    service = get_engagement_service()

    service.track_session(user_id, request.duration_seconds)

    return {
        "status": "success",
        "message": "Session tracked",
        "duration_seconds": request.duration_seconds,
    }


@router.get("/stats/platform", response_model=EngagementStatistics)
async def get_platform_statistics(
    current_user: dict = Depends(get_current_user),
) -> EngagementStatistics:
    """
    Get platform-wide engagement statistics.

    Note: In production, this should be admin-only.

    Returns:
        Platform statistics
    """
    # TODO: Check if user is admin

    service = get_engagement_service()
    stats = service.get_platform_statistics()

    return stats


# ==================== Utility Endpoints ====================

@router.post("/dismiss/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dismiss a notification.

    Args:
        notification_id: Notification ID to dismiss

    Returns:
        Success message
    """
    # In production, mark notification as dismissed in database

    return {
        "status": "success",
        "message": "Notification dismissed",
        "notification_id": notification_id,
    }
