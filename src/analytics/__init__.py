"""Analytics and usage tracking module."""

from .tracker import UsageTracker, QueryEvent, UserSession, EventType
from .storage import AnalyticsStorage
from .dashboard import AnalyticsDashboard
from .collector import AnalyticsCollector
from .service import AnalyticsService
from .query_patterns import QueryPatternAnalyzer
from .prescriptions import PrescriptionAnalyzer
from .learning import LearningAnalyzer
from .comparisons import PeerComparisonAnalyzer
from .insights import InsightGenerator
from .reports import ReportGenerator
from .visualizations import ChartDataFormatter

# Export models
from .models import (
    QueryAnalytics,
    SpecialtyMetrics,
    UsageMetrics,
    PrescriptionPatterns,
    LearningMetrics,
    ComparisonMetrics,
    TrendData,
    InsightReport,
    MonthlyReport,
    DashboardData,
    TimeGranularity,
    ComparisonType,
    InsightCategory,
)

__all__ = [
    # Tracking
    "UsageTracker",
    "QueryEvent",
    "UserSession",
    "EventType",

    # Storage and collection
    "AnalyticsStorage",
    "AnalyticsCollector",

    # Main service
    "AnalyticsService",

    # Analyzers
    "QueryPatternAnalyzer",
    "PrescriptionAnalyzer",
    "LearningAnalyzer",
    "PeerComparisonAnalyzer",

    # Generators
    "InsightGenerator",
    "ReportGenerator",
    "ChartDataFormatter",

    # Legacy
    "AnalyticsDashboard",

    # Models
    "QueryAnalytics",
    "SpecialtyMetrics",
    "UsageMetrics",
    "PrescriptionPatterns",
    "LearningMetrics",
    "ComparisonMetrics",
    "TrendData",
    "InsightReport",
    "MonthlyReport",
    "DashboardData",
    "TimeGranularity",
    "ComparisonType",
    "InsightCategory",
]
