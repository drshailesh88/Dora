"""
Practice Analytics Data Models

Comprehensive models for tracking and analyzing doctor practice patterns,
prescription behavior, learning progress, and peer comparisons.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics tracked."""
    QUERY = "query"
    PRESCRIPTION = "prescription"
    LEARNING = "learning"
    CME = "cme"
    DRUG_CHECK = "drug_check"
    PATIENT_EDUCATION = "patient_education"
    DOCUMENTATION = "documentation"


class TimeGranularity(str, Enum):
    """Time granularity for metrics."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ComparisonType(str, Enum):
    """Types of peer comparisons."""
    SAME_SPECIALTY = "same_specialty"
    SAME_REGION = "same_region"
    SAME_EXPERIENCE = "same_experience"
    ALL_USERS = "all_users"


class InsightCategory(str, Enum):
    """Categories of insights."""
    ACHIEVEMENT = "achievement"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    TREND = "trend"
    MILESTONE = "milestone"
    LEARNING_GAP = "learning_gap"
    BEST_PRACTICE = "best_practice"


class QueryAnalytics(BaseModel):
    """Query pattern analytics."""

    user_id: str
    period_start: date
    period_end: date

    # Volume metrics
    total_queries: int = 0
    voice_queries: int = 0
    text_queries: int = 0
    queries_with_patient_context: int = 0

    # Quality metrics
    avg_confidence_score: float = 0.0
    high_confidence_rate: float = 0.0  # Percentage
    avg_citations_per_query: float = 0.0

    # Performance metrics
    avg_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

    # Timing patterns
    peak_hours: list[int] = Field(default_factory=list, description="Hours with most queries (0-23)")
    weekday_distribution: dict[str, int] = Field(default_factory=dict)  # Mon-Sun

    # Topic analysis
    top_topics: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'topic': str, 'count': int, 'percentage': float}]"
    )
    specialty_distribution: dict[str, int] = Field(default_factory=dict)

    # Common queries
    most_common_queries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'query': str, 'count': int}]"
    )

    # Complexity
    avg_query_length: float = 0.0
    complex_queries_count: int = 0  # Queries > 100 chars

    # Error rate
    error_count: int = 0
    error_rate: float = 0.0


class SpecialtyMetrics(BaseModel):
    """Specialty-specific metrics."""

    specialty: str
    user_id: str
    period_start: date
    period_end: date

    # Query distribution
    query_count: int = 0
    percentage_of_total: float = 0.0

    # Top conditions queried
    top_conditions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'condition': str, 'count': int}]"
    )

    # Top medications prescribed
    top_medications: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'drug': str, 'count': int}]"
    )

    # Depth vs breadth
    unique_topics: int = 0
    avg_queries_per_topic: float = 0.0

    # Learning
    cme_credits_earned: float = 0.0
    quizzes_completed: int = 0
    avg_quiz_score: float = 0.0


class UsageMetrics(BaseModel):
    """Overall usage metrics."""

    user_id: str
    period_start: date
    period_end: date
    granularity: TimeGranularity = TimeGranularity.DAILY

    # Activity
    active_days: int = 0
    total_sessions: int = 0
    avg_session_duration_seconds: float = 0.0

    # Feature usage
    queries_count: int = 0
    drug_checks_count: int = 0
    prescriptions_generated: int = 0
    documentation_generated: int = 0
    patient_education_generated: int = 0

    # Platform
    desktop_sessions: int = 0
    web_sessions: int = 0
    mobile_sessions: int = 0

    # Offline usage
    offline_sessions: int = 0
    offline_percentage: float = 0.0

    # Engagement
    avg_queries_per_day: float = 0.0
    most_active_day: Optional[date] = None
    most_active_hour: Optional[int] = None

    # Trends
    week_over_week_change: float = 0.0  # Percentage change
    month_over_month_change: float = 0.0


class PrescriptionPatterns(BaseModel):
    """Prescription behavior analytics."""

    user_id: str
    period_start: date
    period_end: date

    # Volume
    total_prescriptions: int = 0
    total_medications_prescribed: int = 0
    avg_medications_per_prescription: float = 0.0

    # Drug class distribution
    top_drug_classes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'class': str, 'count': int, 'percentage': float}]"
    )

    # Generic vs brand
    generic_count: int = 0
    brand_count: int = 0
    generic_percentage: float = 0.0

    # Antibiotic stewardship
    antibiotic_prescriptions: int = 0
    antibiotic_percentage: float = 0.0
    broad_spectrum_antibiotics: int = 0
    narrow_spectrum_antibiotics: int = 0

    # Safety
    drug_interactions_detected: int = 0
    allergy_alerts_triggered: int = 0
    contraindication_alerts: int = 0
    safety_score: float = 1.0  # 0-1, higher is safer

    # Cost consciousness
    avg_prescription_cost: float = 0.0
    cost_savings_from_generics: float = 0.0

    # Common medications
    most_prescribed_drugs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'drug': str, 'count': int, 'generic': bool}]"
    )

    # Prescribing by condition
    prescriptions_by_condition: dict[str, int] = Field(default_factory=dict)

    # Schedule compliance
    schedule_h1_prescriptions: int = 0
    schedule_x_prescriptions: int = 0
    controlled_substance_percentage: float = 0.0


class LearningMetrics(BaseModel):
    """Learning and CME analytics."""

    user_id: str
    period_start: date
    period_end: date

    # CME credits
    total_cme_credits: float = 0.0
    category_1_credits: float = 0.0
    category_2_credits: float = 0.0
    category_3_credits: float = 0.0
    credits_needed_for_annual_goal: float = 0.0
    percentage_of_annual_goal: float = 0.0

    # Activities
    total_learning_activities: int = 0
    articles_read: int = 0
    videos_watched: int = 0
    quizzes_attempted: int = 0
    quizzes_passed: int = 0
    cases_studied: int = 0

    # Quiz performance
    avg_quiz_score: float = 0.0
    quiz_pass_rate: float = 0.0
    quiz_accuracy_by_topic: dict[str, float] = Field(default_factory=dict)

    # Streaks
    current_streak: int = 0
    longest_streak: int = 0
    streak_milestones: list[int] = Field(default_factory=list)

    # Time investment
    total_learning_time_hours: float = 0.0
    avg_daily_learning_minutes: float = 0.0

    # Topics studied
    topics_studied: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'topic': str, 'time_spent': int, 'mastery': float}]"
    )

    # Knowledge gaps
    weak_areas: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'topic': str, 'accuracy': float}]"
    )

    # Depth vs breadth
    specialty_depth_score: float = 0.0  # 0-1, focus in specialty
    knowledge_breadth_score: float = 0.0  # 0-1, diverse topics

    # Learning paths
    paths_enrolled: int = 0
    paths_completed: int = 0
    path_completion_rate: float = 0.0

    # Achievements
    achievements_earned: int = 0
    total_points: int = 0
    current_level: int = 1


class ComparisonMetrics(BaseModel):
    """Peer comparison metrics."""

    user_id: str
    comparison_type: ComparisonType
    period_start: date
    period_end: date

    # Peer group info
    peer_group_size: int = 0
    peer_group_description: str = ""

    # Query metrics comparison
    user_queries: int = 0
    peer_avg_queries: float = 0.0
    peer_median_queries: float = 0.0
    peer_top_10_percent_queries: float = 0.0
    queries_percentile: float = 0.0  # User's percentile rank

    # Generic prescribing
    user_generic_rate: float = 0.0
    peer_avg_generic_rate: float = 0.0
    peer_top_10_percent_generic_rate: float = 0.0
    generic_rate_percentile: float = 0.0

    # CME credits
    user_cme_credits: float = 0.0
    peer_avg_cme_credits: float = 0.0
    peer_top_10_percent_cme_credits: float = 0.0
    cme_percentile: float = 0.0

    # Quiz performance
    user_quiz_accuracy: float = 0.0
    peer_avg_quiz_accuracy: float = 0.0
    peer_top_10_percent_quiz_accuracy: float = 0.0
    quiz_accuracy_percentile: float = 0.0

    # Learning streak
    user_current_streak: int = 0
    peer_avg_streak: float = 0.0
    peer_top_10_percent_streak: float = 0.0
    streak_percentile: float = 0.0

    # Safety score
    user_safety_score: float = 0.0
    peer_avg_safety_score: float = 0.0
    safety_percentile: float = 0.0

    # Overall rank
    overall_rank: int = 0
    overall_percentile: float = 0.0

    # Strengths
    strengths: list[str] = Field(
        default_factory=list,
        description="Areas where user excels"
    )

    # Opportunities
    opportunities: list[str] = Field(
        default_factory=list,
        description="Areas for improvement"
    )


class TrendData(BaseModel):
    """Time series trend data."""

    metric_name: str
    user_id: str
    granularity: TimeGranularity

    # Data points
    data_points: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'date': str, 'value': float}]"
    )

    # Trend analysis
    trend_direction: str = "stable"  # increasing, decreasing, stable
    trend_percentage: float = 0.0  # Percentage change over period

    # Statistical
    mean_value: float = 0.0
    median_value: float = 0.0
    std_deviation: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0

    # Forecasting (optional)
    forecast_next_period: Optional[float] = None
    confidence_interval: Optional[dict[str, float]] = None


class InsightReport(BaseModel):
    """AI-generated insight."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    category: InsightCategory

    # Content
    title: str
    message: str
    detailed_explanation: Optional[str] = None

    # Supporting data
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    comparison_value: Optional[float] = None

    # Recommendations
    recommendations: list[str] = Field(default_factory=list)
    actionable_steps: list[str] = Field(default_factory=list)

    # Priority
    priority: str = "medium"  # low, medium, high
    impact_score: float = 0.5  # 0-1, potential impact

    # References
    related_topics: list[str] = Field(default_factory=list)
    learning_resources: list[dict[str, str]] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    is_dismissed: bool = False
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class MonthlyReport(BaseModel):
    """Comprehensive monthly practice report."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    month: int  # 1-12
    year: int

    # Summary stats
    total_queries: int = 0
    total_prescriptions: int = 0
    total_cme_credits: float = 0.0
    active_days: int = 0

    # Highlights
    key_achievements: list[str] = Field(default_factory=list)
    milestones_reached: list[str] = Field(default_factory=list)

    # Analytics sections
    query_analytics: Optional[QueryAnalytics] = None
    prescription_patterns: Optional[PrescriptionPatterns] = None
    learning_metrics: Optional[LearningMetrics] = None
    comparison_metrics: Optional[ComparisonMetrics] = None

    # Insights
    insights: list[InsightReport] = Field(default_factory=list)

    # Trends
    trends: list[TrendData] = Field(default_factory=list)

    # Top items
    top_topics_studied: list[str] = Field(default_factory=list)
    top_medications_prescribed: list[str] = Field(default_factory=list)

    # Goals progress
    goals_achieved: int = 0
    goals_in_progress: int = 0

    # Report metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    pdf_path: Optional[str] = None

    class Config:
        use_enum_values = True


class DashboardData(BaseModel):
    """Data for analytics dashboard."""

    user_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Current period (default: last 30 days)
    period_start: date
    period_end: date

    # Quick stats
    queries_this_month: int = 0
    prescriptions_this_month: int = 0
    cme_credits_this_month: float = 0.0
    current_streak: int = 0

    # Percentage changes (vs previous period)
    queries_change: float = 0.0
    prescriptions_change: float = 0.0
    cme_change: float = 0.0

    # Usage metrics
    usage_metrics: UsageMetrics

    # Analytics
    query_analytics: QueryAnalytics
    prescription_patterns: Optional[PrescriptionPatterns] = None
    learning_metrics: LearningMetrics

    # Comparisons
    comparison_metrics: Optional[ComparisonMetrics] = None

    # Recent insights
    recent_insights: list[InsightReport] = Field(default_factory=list)

    # Trends (for charts)
    query_trend: TrendData
    cme_trend: TrendData

    # Top lists
    top_specialties: list[dict[str, Any]] = Field(default_factory=list)
    top_medications: list[dict[str, Any]] = Field(default_factory=list)
    top_topics: list[dict[str, Any]] = Field(default_factory=list)


# Export all models
__all__ = [
    "MetricType",
    "TimeGranularity",
    "ComparisonType",
    "InsightCategory",
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
]
