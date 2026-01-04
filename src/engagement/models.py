"""
Engagement Data Models

Models for daily briefings, alerts, trending queries, clinical pearls,
and engagement analytics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""

    RESEARCH_PAPER = "research_paper"
    GUIDELINE_UPDATE = "guideline_update"
    DRUG_RECALL = "drug_recall"
    DRUG_SAFETY = "drug_safety"
    DRUG_INTERACTION = "drug_interaction"
    CRITICAL_LAB = "critical_lab"
    SYSTEM_UPDATE = "system_update"


class TrendingPeriod(str, Enum):
    """Trending time periods."""

    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"


class GeographicScope(str, Enum):
    """Geographic filtering scope."""

    GLOBAL = "global"
    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    HOSPITAL = "hospital"


class NotificationDeliveryStatus(str, Enum):
    """Delivery status for engagement notifications."""

    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    FAILED = "failed"


class BriefingItemType(str, Enum):
    """Types of items in daily briefing."""

    PATIENT_PREVIEW = "patient_preview"
    CLINICAL_PEARL = "clinical_pearl"
    TRENDING_QUERY = "trending_query"
    RESEARCH_ALERT = "research_alert"
    GUIDELINE_UPDATE = "guideline_update"
    DRUG_ALERT = "drug_alert"
    SYSTEM_MESSAGE = "system_message"


class DailyBriefing(BaseModel):
    """Morning digest content for a user."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID this briefing is for")
    date: str = Field(..., description="Date in YYYY-MM-DD format")

    # Briefing content
    greeting: str = Field(..., description="Personalized greeting")
    summary_line: str = Field(..., description="One-line summary of the day")
    items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of briefing items (patient previews, pearls, alerts, etc.)"
    )

    # Metadata
    specialty: Optional[str] = Field(None, description="User's primary specialty")
    patient_count_today: int = Field(default=0, description="Number of patients scheduled")

    # Delivery tracking
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    items_clicked: list[str] = Field(default_factory=list, description="IDs of clicked items")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "date": "2026-01-04",
                "greeting": "Good morning, Dr. Sharma!",
                "summary_line": "You have 8 patients scheduled today, plus 2 new cardiology papers.",
                "items": [
                    {
                        "type": "patient_preview",
                        "title": "8 patients scheduled today",
                        "content": "Including 2 follow-ups for heart failure"
                    }
                ],
                "specialty": "cardiology",
                "patient_count_today": 8
            }
        }


class ResearchAlert(BaseModel):
    """New research paper notification."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID to notify")

    # Paper details
    paper_title: str = Field(..., description="Research paper title")
    authors: list[str] = Field(default_factory=list)
    journal: str = Field(..., description="Journal name")
    publication_date: str = Field(..., description="Publication date")
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None

    # Content
    abstract: str = Field(..., description="Paper abstract")
    key_findings: list[str] = Field(
        default_factory=list,
        description="Bulleted key findings"
    )
    clinical_relevance: str = Field(
        ...,
        description="Why this matters to the doctor"
    )

    # Relevance
    specialty: str = Field(..., description="Relevant specialty")
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    saved: bool = Field(default=False, description="User saved for later")

    class Config:
        use_enum_values = True


class GuidelineUpdate(BaseModel):
    """Guideline change alert."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID to notify")

    # Guideline details
    guideline_name: str = Field(..., description="Name of the guideline")
    organization: str = Field(..., description="Issuing organization (ICMR, WHO, AHA, etc.)")
    version: str = Field(..., description="Version or year")
    url: Optional[str] = None

    # Changes
    summary: str = Field(..., description="What changed summary")
    key_changes: list[str] = Field(
        default_factory=list,
        description="Bullet points of key changes"
    )
    impact: str = Field(..., description="Clinical impact description")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM)

    # Relevance
    specialty: str = Field(..., description="Relevant specialty")
    conditions: list[str] = Field(default_factory=list, description="Relevant conditions")

    # Tracking
    effective_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class DrugAlert(BaseModel):
    """Drug recall or safety alert."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID to notify")

    # Drug details
    drug_name: str = Field(..., description="Generic name")
    brand_names: list[str] = Field(default_factory=list)
    alert_type: str = Field(..., description="recall, safety_update, interaction, shortage")

    # Alert content
    title: str = Field(..., description="Alert headline")
    description: str = Field(..., description="Full alert description")
    action_required: str = Field(..., description="What doctors should do")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM)

    # Source
    source: str = Field(..., description="FDA, CDSCO, manufacturer, etc.")
    source_url: Optional[str] = None
    alert_date: datetime = Field(default_factory=datetime.utcnow)

    # Relevance
    specialty: Optional[str] = None
    affected_patients: int = Field(
        default=0,
        description="Number of user's patients on this drug"
    )

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    dismissed: bool = False

    class Config:
        use_enum_values = True


class TrendingQuery(BaseModel):
    """Popular query in specialty."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Query details
    query_text: str = Field(..., description="The trending query (anonymized)")
    query_count: int = Field(..., ge=1, description="Number of times asked")
    unique_users: int = Field(..., ge=1, description="Number of unique users")

    # Context
    specialty: Optional[str] = None
    category: Optional[str] = None  # diagnosis, treatment, drug_info, etc.

    # Geographic
    geographic_scope: GeographicScope = Field(default=GeographicScope.GLOBAL)
    location: Optional[str] = Field(None, description="City, state, or country")

    # Time
    period: TrendingPeriod = Field(default=TrendingPeriod.LAST_7D)
    trend_direction: str = Field(
        default="stable",
        description="rising, falling, stable, new"
    )
    rank: int = Field(..., ge=1, description="Ranking in trending list")
    previous_rank: Optional[int] = None

    # Metadata
    related_queries: list[str] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ClinicalPearl(BaseModel):
    """Daily clinical tip/fact."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Content
    title: str = Field(..., description="Short memorable title")
    content: str = Field(..., description="The pearl itself (1-2 sentences)")
    explanation: Optional[str] = Field(
        None,
        description="Optional detailed explanation"
    )

    # Evidence
    citations: list[str] = Field(
        default_factory=list,
        description="Source citations"
    )
    evidence_level: str = Field(
        default="high",
        description="high, medium, low"
    )

    # Categorization
    specialty: str = Field(..., description="Relevant specialty")
    category: str = Field(
        ...,
        description="diagnosis, treatment, prescribing, procedure, etc."
    )
    keywords: list[str] = Field(default_factory=list)

    # Quiz format (optional)
    question: Optional[str] = Field(None, description="Quiz question format")
    answer: Optional[str] = Field(None, description="Quiz answer")
    distractors: list[str] = Field(
        default_factory=list,
        description="Wrong answer options for quiz"
    )

    # Metadata
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Beta Blockers First in AFib",
                "content": "Remember: BB before CCB in rate control for AFib with heart failure",
                "explanation": "Beta blockers have mortality benefit in HFrEF, while rate-limiting CCBs (diltiazem, verapamil) are contraindicated.",
                "specialty": "cardiology",
                "category": "treatment",
                "evidence_level": "high",
                "citations": ["ACC/AHA 2019 AFib Guidelines"]
            }
        }


class UserEngagement(BaseModel):
    """User engagement metrics."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    date: str = Field(..., description="Date in YYYY-MM-DD format")

    # Daily metrics
    briefing_opened: bool = False
    briefing_opened_at: Optional[datetime] = None
    briefing_items_clicked: int = 0

    alerts_received: int = 0
    alerts_opened: int = 0
    alerts_dismissed: int = 0

    queries_made: int = 0
    pearls_viewed: int = 0
    trending_viewed: int = 0

    # Session metrics
    sessions: int = 0
    total_time_seconds: int = 0

    # Engagement score
    engagement_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Daily engagement score (0-100)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_engagement_score(self) -> float:
        """
        Calculate engagement score based on activity.

        Returns:
            Engagement score (0-100)
        """
        score = 0.0

        # Briefing engagement (30 points)
        if self.briefing_opened:
            score += 15
        score += min(self.briefing_items_clicked * 3, 15)

        # Alert engagement (20 points)
        if self.alerts_received > 0:
            alert_rate = self.alerts_opened / self.alerts_received
            score += alert_rate * 20

        # Query activity (30 points)
        score += min(self.queries_made * 5, 30)

        # Content viewing (20 points)
        score += min(self.pearls_viewed * 5, 10)
        score += min(self.trending_viewed * 2, 10)

        return min(score, 100.0)


class NotificationPreference(BaseModel):
    """User notification preferences for engagement."""

    user_id: str = Field(..., description="User ID")

    # Briefing preferences
    briefing_enabled: bool = True
    briefing_time: str = Field(default="07:00", description="Preferred time (HH:MM)")
    briefing_days: list[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4, 5, 6],
        description="Days of week (0=Monday)"
    )

    # Alert preferences
    research_alerts: bool = True
    guideline_alerts: bool = True
    drug_alerts: bool = True
    critical_only: bool = False  # Only critical/high severity

    # Delivery preferences
    push_notifications: bool = True
    email_digest: bool = True
    in_app_only: bool = False

    # Timing preferences
    quiet_hours_enabled: bool = True
    quiet_start: str = Field(default="21:00", description="Quiet hours start (HH:MM)")
    quiet_end: str = Field(default="07:00", description="Quiet hours end (HH:MM)")

    # Smart scheduling
    learn_from_behavior: bool = Field(
        default=True,
        description="Learn optimal notification times from user behavior"
    )
    detected_active_hours: list[int] = Field(
        default_factory=list,
        description="Hours when user is most active"
    )

    # Content preferences
    max_briefing_items: int = Field(default=7, ge=3, le=15)
    include_trending: bool = True
    include_pearls: bool = True

    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "briefing_enabled": True,
                "briefing_time": "07:30",
                "quiet_start": "22:00",
                "quiet_end": "07:00",
                "research_alerts": True,
                "critical_only": False
            }
        }


class EngagementStatistics(BaseModel):
    """Aggregate engagement statistics."""

    # Overall metrics
    total_users: int = 0
    active_users_today: int = 0
    active_users_7d: int = 0
    active_users_30d: int = 0

    # Briefing metrics
    briefings_sent_today: int = 0
    briefing_open_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    briefing_click_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Alert metrics
    alerts_sent_today: int = 0
    alert_open_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    alert_ack_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Engagement distribution
    high_engagement_users: int = Field(default=0, description="Score > 70")
    medium_engagement_users: int = Field(default=0, description="Score 30-70")
    low_engagement_users: int = Field(default=0, description="Score < 30")

    # Trends
    avg_engagement_score: float = Field(default=0.0, ge=0.0, le=100.0)
    engagement_trend: str = Field(default="stable", description="rising, falling, stable")

    # Churn signals
    at_risk_users: int = Field(default=0, description="Low engagement, may churn")
    dormant_users: int = Field(default=0, description="No activity in 7+ days")

    # Metadata
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
