"""
Engagement Module

Daily engagement system for habit formation including:
- Daily briefings
- Research and guideline alerts
- Trending queries
- Clinical pearls
- Smart notification scheduling
- Engagement analytics
"""

from src.engagement.models import (
    # Alert models
    AlertSeverity,
    AlertType,
    ResearchAlert,
    GuidelineUpdate,
    DrugAlert,

    # Trending models
    TrendingQuery,
    TrendingPeriod,
    GeographicScope,

    # Briefing models
    DailyBriefing,
    BriefingItemType,

    # Pearl models
    ClinicalPearl,

    # Engagement tracking
    UserEngagement,
    EngagementStatistics,

    # Preferences
    NotificationPreference,
    NotificationDeliveryStatus,
)

from src.engagement.briefing import BriefingGenerator
from src.engagement.alerts import AlertManager
from src.engagement.trending import TrendingAnalyzer
from src.engagement.pearls import PearlManager
from src.engagement.scheduler import NotificationScheduler
from src.engagement.analytics import EngagementAnalytics
from src.engagement.service import EngagementService, get_engagement_service

__all__ = [
    # Models
    "AlertSeverity",
    "AlertType",
    "ResearchAlert",
    "GuidelineUpdate",
    "DrugAlert",
    "TrendingQuery",
    "TrendingPeriod",
    "GeographicScope",
    "DailyBriefing",
    "BriefingItemType",
    "ClinicalPearl",
    "UserEngagement",
    "EngagementStatistics",
    "NotificationPreference",
    "NotificationDeliveryStatus",

    # Generators and Managers
    "BriefingGenerator",
    "AlertManager",
    "TrendingAnalyzer",
    "PearlManager",
    "NotificationScheduler",
    "EngagementAnalytics",

    # Service
    "EngagementService",
    "get_engagement_service",
]
