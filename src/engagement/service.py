"""
Engagement Service

Main service that coordinates briefings, alerts, trending, pearls,
scheduling, and analytics.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.engagement.models import (
    DailyBriefing,
    ResearchAlert,
    GuidelineUpdate,
    DrugAlert,
    TrendingQuery,
    ClinicalPearl,
    NotificationPreference,
    UserEngagement,
    EngagementStatistics,
    AlertSeverity,
    TrendingPeriod,
)
from src.engagement.briefing import BriefingGenerator
from src.engagement.alerts import AlertManager
from src.engagement.trending import TrendingAnalyzer
from src.engagement.pearls import PearlManager
from src.engagement.scheduler import NotificationScheduler
from src.engagement.analytics import EngagementAnalytics


class EngagementService:
    """Main engagement service coordinating all engagement features."""

    def __init__(self):
        """Initialize engagement service."""
        self.briefing_generator = BriefingGenerator()
        self.alert_manager = AlertManager()
        self.trending_analyzer = TrendingAnalyzer()
        self.pearl_manager = PearlManager()
        self.scheduler = NotificationScheduler()
        self.analytics = EngagementAnalytics()

        # Storage would be injected in production
        self.preferences_store = {}
        self.briefing_store = {}

    # ==================== Briefing Methods ====================

    async def generate_daily_briefing(
        self,
        user_id: str,
        user_profile: dict[str, Any],
        emr_data: Optional[dict[str, Any]] = None,
    ) -> DailyBriefing:
        """
        Generate daily briefing for a user.

        Args:
            user_id: User ID
            user_profile: User's profile with specialty, etc.
            emr_data: Optional EMR data

        Returns:
            DailyBriefing object
        """
        # Get user preferences
        preferences = self._get_preferences(user_id)

        # Get specialty
        specialty = user_profile.get("specialty", "general")

        # Fetch pending alerts
        alerts = await self._fetch_pending_alerts(user_id, specialty)

        # Get trending queries
        trending = self.trending_analyzer.get_personalized_trending(
            user_profile=user_profile,
            period=TrendingPeriod.LAST_7D,
        )

        # Get daily pearl
        pearl = self.pearl_manager.get_daily_pearl(
            user_id=user_id,
            specialty=specialty,
        )

        # Generate briefing
        briefing = self.briefing_generator.generate_briefing(
            user_id=user_id,
            user_profile=user_profile,
            preferences=preferences,
            emr_data=emr_data,
            alerts=[self._alert_to_dict(a) for a in alerts],
            trending=[self._trending_to_dict(t) for t in trending],
            pearl=self._pearl_to_dict(pearl) if pearl else None,
        )

        # Schedule delivery
        send_time = self.scheduler.schedule_briefing(
            user_id=user_id,
            preferences=preferences,
            briefing_data=briefing.model_dump(),
        )

        # Store briefing
        self._save_briefing(briefing)

        # Track analytics
        self.analytics.track_briefing_delivery(user_id, briefing.id)

        return briefing

    def get_briefing(
        self,
        user_id: str,
        date: Optional[str] = None,
    ) -> Optional[DailyBriefing]:
        """
        Get briefing for a specific date.

        Args:
            user_id: User ID
            date: Date string (YYYY-MM-DD) or None for today

        Returns:
            DailyBriefing or None
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        key = f"{user_id}_{date}"
        return self.briefing_store.get(key)

    def mark_briefing_opened(
        self,
        user_id: str,
        briefing_id: str,
    ) -> None:
        """
        Mark briefing as opened.

        Args:
            user_id: User ID
            briefing_id: Briefing ID
        """
        # Track in analytics
        self.analytics.track_briefing_open(
            user_id=user_id,
            briefing_id=briefing_id,
            opened_at=datetime.utcnow(),
        )

        # Update briefing
        # In production, update in database

    def click_briefing_item(
        self,
        user_id: str,
        briefing_id: str,
        item_id: str,
    ) -> None:
        """
        Track briefing item click.

        Args:
            user_id: User ID
            briefing_id: Briefing ID
            item_id: Item ID that was clicked
        """
        self.analytics.track_briefing_item_click(user_id, item_id)

    # ==================== Alert Methods ====================

    async def create_research_alert(
        self,
        user_id: str,
        specialty: str,
        paper_data: dict[str, Any],
        relevance_score: float,
    ) -> ResearchAlert:
        """Create and schedule research alert."""
        alert = await self.alert_manager.create_research_alert(
            user_id=user_id,
            specialty=specialty,
            paper_data=paper_data,
            relevance_score=relevance_score,
        )

        # Schedule delivery
        preferences = self._get_preferences(user_id)
        self.scheduler.schedule_alert(
            user_id=user_id,
            preferences=preferences,
            alert_data=alert.model_dump(),
            severity=AlertSeverity.MEDIUM,
        )

        # Track analytics
        self.analytics.track_alert_delivery(user_id, alert.id)

        return alert

    async def create_guideline_alert(
        self,
        user_id: str,
        specialty: str,
        guideline_data: dict[str, Any],
    ) -> GuidelineUpdate:
        """Create and schedule guideline update alert."""
        alert = await self.alert_manager.create_guideline_alert(
            user_id=user_id,
            specialty=specialty,
            guideline_data=guideline_data,
        )

        # Schedule delivery
        preferences = self._get_preferences(user_id)
        self.scheduler.schedule_alert(
            user_id=user_id,
            preferences=preferences,
            alert_data=alert.model_dump(),
            severity=alert.severity,
        )

        # Track analytics
        self.analytics.track_alert_delivery(user_id, alert.id)

        return alert

    async def create_drug_alert(
        self,
        user_id: str,
        drug_data: dict[str, Any],
        affected_patients: int = 0,
    ) -> DrugAlert:
        """Create and schedule drug alert."""
        alert = await self.alert_manager.create_drug_alert(
            user_id=user_id,
            drug_data=drug_data,
            affected_patients=affected_patients,
        )

        # Schedule delivery
        preferences = self._get_preferences(user_id)
        self.scheduler.schedule_alert(
            user_id=user_id,
            preferences=preferences,
            alert_data=alert.model_dump(),
            severity=alert.severity,
        )

        # Track analytics
        self.analytics.track_alert_delivery(user_id, alert.id)

        return alert

    def mark_alert_opened(
        self,
        user_id: str,
        alert_id: str,
    ) -> None:
        """Mark alert as opened."""
        self.analytics.track_alert_open(user_id, alert_id)

    def dismiss_alert(
        self,
        user_id: str,
        alert_id: str,
    ) -> None:
        """Dismiss an alert."""
        self.analytics.track_alert_dismiss(user_id, alert_id)

    # ==================== Trending Methods ====================

    def get_trending(
        self,
        specialty: str,
        period: TrendingPeriod = TrendingPeriod.LAST_7D,
    ) -> list[TrendingQuery]:
        """Get trending queries for specialty."""
        return self.trending_analyzer.compute_trending(
            specialty=specialty,
            period=period,
            limit=10,
        )

    def get_personalized_trending(
        self,
        user_id: str,
        user_profile: dict[str, Any],
    ) -> list[TrendingQuery]:
        """Get personalized trending queries."""
        return self.trending_analyzer.get_personalized_trending(
            user_profile=user_profile,
        )

    def track_query_for_trending(
        self,
        user_id: str,
        query_text: str,
        specialty: Optional[str] = None,
        category: Optional[str] = None,
    ) -> None:
        """Track a query for trending analysis."""
        self.trending_analyzer.track_query(
            query_text=query_text,
            user_id=user_id,
            specialty=specialty,
            category=category,
        )

        # Also track in analytics
        self.analytics.track_query(user_id)

    def mark_trending_viewed(self, user_id: str) -> None:
        """Track trending queries view."""
        self.analytics.track_trending_view(user_id)

    # ==================== Clinical Pearls Methods ====================

    def get_daily_pearl(
        self,
        user_id: str,
        specialty: str,
    ) -> Optional[ClinicalPearl]:
        """Get daily clinical pearl."""
        pearl = self.pearl_manager.get_daily_pearl(
            user_id=user_id,
            specialty=specialty,
        )

        if pearl:
            self.analytics.track_pearl_view(user_id, pearl.id)

        return pearl

    def get_pearl_quiz(
        self,
        user_id: str,
        specialty: str,
    ) -> Optional[ClinicalPearl]:
        """Get pearl as quiz."""
        return self.pearl_manager.get_pearl_quiz(
            user_id=user_id,
            specialty=specialty,
        )

    def search_pearls(
        self,
        query: str,
        specialty: Optional[str] = None,
    ) -> list[ClinicalPearl]:
        """Search clinical pearls."""
        return self.pearl_manager.search_pearls(
            query=query,
            specialty=specialty,
        )

    # ==================== Preferences Methods ====================

    def get_preferences(self, user_id: str) -> NotificationPreference:
        """Get user notification preferences."""
        return self._get_preferences(user_id)

    def update_preferences(
        self,
        user_id: str,
        **updates,
    ) -> NotificationPreference:
        """
        Update user notification preferences.

        Args:
            user_id: User ID
            **updates: Preference fields to update

        Returns:
            Updated NotificationPreference
        """
        preferences = self._get_preferences(user_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        preferences.updated_at = datetime.utcnow()

        # Save
        self._save_preferences(preferences)

        return preferences

    # ==================== Analytics Methods ====================

    def get_engagement_score(
        self,
        user_id: str,
    ) -> float:
        """Get current engagement score."""
        return self.analytics.get_engagement_score(user_id)

    def get_engagement_trend(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get engagement trend over time."""
        return self.analytics.get_engagement_trend(user_id, days)

    def get_engagement_insights(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """Get personalized engagement insights."""
        return self.analytics.get_engagement_insights(user_id)

    def get_platform_statistics(self) -> EngagementStatistics:
        """Get platform-wide engagement statistics."""
        return self.analytics.compute_platform_statistics()

    def track_session(
        self,
        user_id: str,
        duration_seconds: int,
    ) -> None:
        """Track user session."""
        self.analytics.track_session(user_id, duration_seconds)

    # ==================== Background Jobs ====================

    async def run_daily_briefing_job(self) -> None:
        """
        Background job to generate and send daily briefings.

        Should be run every morning at 5am.
        """
        # In production, this would query database for all active users
        # For now, this is a placeholder

        # For each user:
        # 1. Check if briefing should be sent today
        # 2. Generate briefing
        # 3. Schedule delivery
        pass

    async def run_alert_fetch_job(self) -> None:
        """
        Background job to fetch new alerts.

        Should be run every hour.
        """
        # Fetch new research papers
        # Fetch guideline updates
        # Fetch drug alerts
        # Create alerts for relevant users
        pass

    async def run_trending_computation_job(self) -> None:
        """
        Background job to compute trending queries.

        Should be run every 6 hours.
        """
        # Compute trending for each specialty
        # Cache results
        pass

    # ==================== Helper Methods ====================

    async def _fetch_pending_alerts(
        self,
        user_id: str,
        specialty: str,
    ) -> list[Any]:
        """Fetch pending alerts for user."""
        # In production, query database
        # For now, return empty list
        return []

    def _get_preferences(self, user_id: str) -> NotificationPreference:
        """Get or create notification preferences."""
        if user_id not in self.preferences_store:
            self.preferences_store[user_id] = NotificationPreference(
                user_id=user_id
            )

        return self.preferences_store[user_id]

    def _save_preferences(self, preferences: NotificationPreference) -> None:
        """Save notification preferences."""
        self.preferences_store[preferences.user_id] = preferences

        # In production, save to database

    def _save_briefing(self, briefing: DailyBriefing) -> None:
        """Save briefing."""
        key = f"{briefing.user_id}_{briefing.date}"
        self.briefing_store[key] = briefing

        # In production, save to database

    def _alert_to_dict(self, alert: Any) -> dict[str, Any]:
        """Convert alert object to dict."""
        if hasattr(alert, 'model_dump'):
            return alert.model_dump()
        return {}

    def _trending_to_dict(self, trending: TrendingQuery) -> dict[str, Any]:
        """Convert trending query to dict."""
        return trending.model_dump()

    def _pearl_to_dict(self, pearl: ClinicalPearl) -> dict[str, Any]:
        """Convert pearl to dict."""
        return pearl.model_dump()


# Global service instance
_engagement_service = None


def get_engagement_service() -> EngagementService:
    """Get global engagement service instance."""
    global _engagement_service

    if _engagement_service is None:
        _engagement_service = EngagementService()

    return _engagement_service
