"""
Engagement Analytics

Tracks and analyzes user engagement metrics.
Calculates engagement scores, detects churn signals, and provides insights.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from src.engagement.models import (
    UserEngagement,
    EngagementStatistics,
    NotificationDeliveryStatus,
)


class EngagementAnalytics:
    """Analyzes user engagement patterns."""

    def __init__(self):
        """Initialize engagement analytics."""
        self.engagement_cache = {}

    def track_briefing_open(
        self,
        user_id: str,
        briefing_id: str,
        opened_at: datetime,
    ) -> None:
        """
        Track when user opens daily briefing.

        Args:
            user_id: User ID
            briefing_id: Briefing ID
            opened_at: When briefing was opened
        """
        today = opened_at.strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.briefing_opened = True
        engagement.briefing_opened_at = opened_at
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_briefing_item_click(
        self,
        user_id: str,
        item_id: str,
    ) -> None:
        """
        Track when user clicks on briefing item.

        Args:
            user_id: User ID
            item_id: Item ID that was clicked
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.briefing_items_clicked += 1
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_alert_delivery(
        self,
        user_id: str,
        alert_id: str,
    ) -> None:
        """
        Track alert delivery.

        Args:
            user_id: User ID
            alert_id: Alert ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.alerts_received += 1
        engagement.updated_at = datetime.utcnow()

        self._save_engagement(engagement)

    def track_alert_open(
        self,
        user_id: str,
        alert_id: str,
    ) -> None:
        """
        Track alert open.

        Args:
            user_id: User ID
            alert_id: Alert ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.alerts_opened += 1
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_alert_dismiss(
        self,
        user_id: str,
        alert_id: str,
    ) -> None:
        """
        Track alert dismissal.

        Args:
            user_id: User ID
            alert_id: Alert ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.alerts_dismissed += 1
        engagement.updated_at = datetime.utcnow()

        self._save_engagement(engagement)

    def track_query(
        self,
        user_id: str,
    ) -> None:
        """
        Track query made.

        Args:
            user_id: User ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.queries_made += 1
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_pearl_view(
        self,
        user_id: str,
        pearl_id: str,
    ) -> None:
        """
        Track clinical pearl view.

        Args:
            user_id: User ID
            pearl_id: Pearl ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.pearls_viewed += 1
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_trending_view(
        self,
        user_id: str,
    ) -> None:
        """
        Track trending queries view.

        Args:
            user_id: User ID
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.trending_viewed += 1
        engagement.updated_at = datetime.utcnow()

        # Recalculate score
        engagement.engagement_score = engagement.calculate_engagement_score()

        self._save_engagement(engagement)

    def track_session(
        self,
        user_id: str,
        duration_seconds: int,
    ) -> None:
        """
        Track user session.

        Args:
            user_id: User ID
            duration_seconds: Session duration in seconds
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        engagement = self._get_or_create_engagement(user_id, today)

        engagement.sessions += 1
        engagement.total_time_seconds += duration_seconds
        engagement.updated_at = datetime.utcnow()

        self._save_engagement(engagement)

    def get_engagement_score(
        self,
        user_id: str,
        date: Optional[str] = None,
    ) -> float:
        """
        Get engagement score for user.

        Args:
            user_id: User ID
            date: Date (YYYY-MM-DD) or None for today

        Returns:
            Engagement score (0-100)
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        engagement = self._get_engagement(user_id, date)

        if not engagement:
            return 0.0

        return engagement.engagement_score

    def get_engagement_trend(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get engagement trend over time.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Dict with trend data
        """
        scores = []
        dates = []

        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            engagement = self._get_engagement(user_id, date)

            dates.append(date)
            scores.append(engagement.engagement_score if engagement else 0.0)

        # Calculate trend direction
        if len(scores) < 2:
            trend = "stable"
        else:
            recent_avg = sum(scores[:3]) / 3
            older_avg = sum(scores[-3:]) / 3

            if recent_avg > older_avg * 1.2:
                trend = "rising"
            elif recent_avg < older_avg * 0.8:
                trend = "falling"
            else:
                trend = "stable"

        return {
            "user_id": user_id,
            "period_days": days,
            "dates": list(reversed(dates)),
            "scores": list(reversed(scores)),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "trend": trend,
        }

    def is_at_risk(
        self,
        user_id: str,
        threshold_days: int = 3,
        threshold_score: float = 20.0,
    ) -> bool:
        """
        Check if user is at risk of churning.

        Args:
            user_id: User ID
            threshold_days: Number of days to check
            threshold_score: Minimum acceptable score

        Returns:
            True if user is at risk
        """
        # Check recent engagement
        recent_scores = []

        for i in range(threshold_days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            engagement = self._get_engagement(user_id, date)
            recent_scores.append(engagement.engagement_score if engagement else 0.0)

        # If all recent scores are below threshold, user is at risk
        avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0.0

        return avg_recent < threshold_score

    def is_dormant(
        self,
        user_id: str,
        days: int = 7,
    ) -> bool:
        """
        Check if user is dormant (no activity).

        Args:
            user_id: User ID
            days: Number of days to check

        Returns:
            True if user is dormant
        """
        # Check if user has any engagement in the period
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            engagement = self._get_engagement(user_id, date)

            if engagement and engagement.engagement_score > 0:
                return False

        return True

    def compute_platform_statistics(self) -> EngagementStatistics:
        """
        Compute platform-wide engagement statistics.

        Returns:
            EngagementStatistics object
        """
        # In real implementation, query database
        # For now, compute from cache

        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Count active users
        active_today = 0
        active_7d = 0
        active_30d = 0

        high_engagement = 0
        medium_engagement = 0
        low_engagement = 0

        at_risk = 0
        dormant = 0

        all_scores = []

        # Simulate with some data
        # In production, this would query database
        total_users = 1000  # Mock

        # Calculate metrics
        # This is simplified - real implementation would query actual data

        return EngagementStatistics(
            total_users=total_users,
            active_users_today=active_today or 350,
            active_users_7d=active_7d or 650,
            active_users_30d=active_30d or 850,
            briefings_sent_today=350,
            briefing_open_rate=0.65,
            briefing_click_rate=0.42,
            alerts_sent_today=125,
            alert_open_rate=0.78,
            alert_ack_rate=0.85,
            high_engagement_users=high_engagement or 200,
            medium_engagement_users=medium_engagement or 500,
            low_engagement_users=low_engagement or 300,
            avg_engagement_score=58.5,
            engagement_trend="rising",
            at_risk_users=at_risk or 75,
            dormant_users=dormant or 150,
        )

    def get_engagement_insights(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Get personalized engagement insights.

        Args:
            user_id: User ID

        Returns:
            Dict with insights and recommendations
        """
        # Get 7-day trend
        trend = self.get_engagement_trend(user_id, days=7)

        # Get today's engagement
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_engagement = self._get_engagement(user_id, today)

        # Calculate streak
        streak = self._calculate_streak(user_id)

        # Generate insights
        insights = []

        if trend["trend"] == "rising":
            insights.append("Your engagement is improving! Keep it up.")
        elif trend["trend"] == "falling":
            insights.append("Your engagement has decreased recently.")

        if streak > 7:
            insights.append(f"Amazing! You're on a {streak}-day streak.")
        elif streak > 0:
            insights.append(f"You're on a {streak}-day streak.")

        if today_engagement:
            if today_engagement.queries_made > 5:
                insights.append("You're very active today!")
            if today_engagement.briefing_opened:
                insights.append("Good job checking your morning briefing.")

        # Generate recommendations
        recommendations = []

        if not today_engagement or not today_engagement.briefing_opened:
            recommendations.append("Check your daily briefing to stay updated.")

        if today_engagement and today_engagement.queries_made == 0:
            recommendations.append("Try asking a clinical question today.")

        if today_engagement and today_engagement.pearls_viewed == 0:
            recommendations.append("Learn something new with today's clinical pearl.")

        return {
            "user_id": user_id,
            "current_score": today_engagement.engagement_score if today_engagement else 0.0,
            "average_score": trend["average_score"],
            "trend": trend["trend"],
            "streak_days": streak,
            "insights": insights,
            "recommendations": recommendations,
            "at_risk": self.is_at_risk(user_id),
            "computed_at": datetime.utcnow().isoformat(),
        }

    def get_cohort_analysis(
        self,
        cohort_date: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Analyze cohort retention.

        Args:
            cohort_date: Cohort start date (YYYY-MM-DD)
            days: Number of days to analyze

        Returns:
            Dict with cohort analysis
        """
        # In real implementation, this would query database
        # For now, return mock data

        retention = []
        for day in range(days):
            # Mock retention curve (typically decreases over time)
            rate = 100 * (0.95 ** day)  # 5% daily decay
            retention.append(round(rate, 1))

        return {
            "cohort_date": cohort_date,
            "cohort_size": 100,  # Mock
            "days_analyzed": days,
            "retention_rates": retention,
            "day_1": retention[0] if retention else 0,
            "day_7": retention[6] if len(retention) > 6 else 0,
            "day_30": retention[29] if len(retention) > 29 else 0,
        }

    def _get_or_create_engagement(
        self,
        user_id: str,
        date: str,
    ) -> UserEngagement:
        """Get or create engagement record."""
        engagement = self._get_engagement(user_id, date)

        if not engagement:
            engagement = UserEngagement(
                user_id=user_id,
                date=date,
            )

        return engagement

    def _get_engagement(
        self,
        user_id: str,
        date: str,
    ) -> Optional[UserEngagement]:
        """Get engagement record from cache/database."""
        key = f"{user_id}_{date}"
        return self.engagement_cache.get(key)

    def _save_engagement(self, engagement: UserEngagement) -> None:
        """Save engagement record to cache/database."""
        key = f"{engagement.user_id}_{engagement.date}"
        self.engagement_cache[key] = engagement

        # In real implementation, also save to database

    def _calculate_streak(self, user_id: str) -> int:
        """Calculate current engagement streak."""
        streak = 0
        current_date = datetime.utcnow().date()

        while True:
            date_str = current_date.strftime("%Y-%m-%d")
            engagement = self._get_engagement(user_id, date_str)

            if engagement and engagement.engagement_score > 20:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

            # Cap at 365 days
            if streak >= 365:
                break

        return streak
