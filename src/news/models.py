"""
News Feed Data Models

Models for medical news articles, conference updates, guideline changes,
drug approvals, and user preferences.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class NewsCategory(str, Enum):
    """News categories for medical content."""

    RESEARCH = "research"
    GUIDELINES = "guidelines"
    DRUG_APPROVALS = "drug_approvals"
    DRUG_SAFETY = "drug_safety"
    CONFERENCES = "conferences"
    CLINICAL_PRACTICE = "clinical_practice"
    HEALTH_POLICY = "health_policy"
    MEDICAL_TECHNOLOGY = "medical_technology"
    PROFESSIONAL_UPDATES = "professional_updates"


class NewsPriority(str, Enum):
    """Priority levels for news items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NewsSource(str, Enum):
    """Trusted medical news sources."""

    PUBMED = "pubmed"
    NEJM = "nejm"
    LANCET = "lancet"
    JAMA = "jama"
    BMJ = "bmj"
    MEDSCAPE = "medscape"
    FDA = "fda"
    CDSCO = "cdsco"
    WHO = "who"
    ICMR = "icmr"
    AHA = "aha"
    ACC = "acc"
    ASCO = "asco"
    ESC = "esc"
    OTHER = "other"

    @property
    def credibility_score(self) -> float:
        """Get credibility score for source (0-1)."""
        scores = {
            NewsSource.PUBMED: 0.95,
            NewsSource.NEJM: 1.0,
            NewsSource.LANCET: 1.0,
            NewsSource.JAMA: 1.0,
            NewsSource.BMJ: 0.95,
            NewsSource.MEDSCAPE: 0.85,
            NewsSource.FDA: 1.0,
            NewsSource.CDSCO: 0.95,
            NewsSource.WHO: 1.0,
            NewsSource.ICMR: 0.95,
            NewsSource.AHA: 0.95,
            NewsSource.ACC: 0.95,
            NewsSource.ASCO: 0.95,
            NewsSource.ESC: 0.95,
            NewsSource.OTHER: 0.7,
        }
        return scores.get(self, 0.7)


class ReadingStatus(str, Enum):
    """Reading status for articles."""

    UNREAD = "unread"
    READING = "reading"
    READ = "read"
    SAVED = "saved"
    ARCHIVED = "archived"


class NewsArticle(BaseModel):
    """Medical news article."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Core metadata
    title: str = Field(..., description="Article title")
    subtitle: Optional[str] = Field(None, description="Subtitle or deck")
    url: str = Field(..., description="Article URL")
    source: NewsSource = Field(..., description="News source")
    category: NewsCategory = Field(..., description="Article category")

    # Authors and publication
    authors: list[str] = Field(default_factory=list)
    journal: Optional[str] = Field(None, description="Journal name if applicable")
    publication_date: datetime = Field(..., description="Publication date")

    # Content
    summary: str = Field(..., description="Brief summary (2-3 sentences)")
    key_findings: list[str] = Field(
        default_factory=list,
        description="Bulleted key findings (3-5 points)"
    )
    clinical_implications: Optional[str] = Field(
        None,
        description="What this means for clinical practice"
    )
    full_text: Optional[str] = Field(None, description="Full article text if available")

    # Media
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Classification
    specialty: list[str] = Field(
        default_factory=list,
        description="Relevant medical specialties"
    )
    keywords: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(
        default_factory=list,
        description="Related medical conditions"
    )

    # Metrics
    priority: NewsPriority = Field(default=NewsPriority.MEDIUM)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reading_time_minutes: int = Field(default=5, ge=1)

    # External IDs
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None

    # Engagement
    views_count: int = Field(default=0)
    bookmarks_count: int = Field(default=0)
    shares_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "title": "New ESC Guidelines for Heart Failure Management",
                "source": "esc",
                "category": "guidelines",
                "summary": "European Society of Cardiology releases updated heart failure guidelines with new recommendations for SGLT2 inhibitors.",
                "key_findings": [
                    "SGLT2i now recommended as first-line for all HF patients",
                    "Updated target NT-proBNP levels for treatment monitoring",
                    "New risk stratification model for acute HF"
                ],
                "specialty": ["cardiology"],
                "priority": "high"
            }
        }


class ConferenceHighlight(BaseModel):
    """Major medical conference update."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Conference details
    conference_name: str = Field(..., description="Conference name (e.g., ACC 2026)")
    conference_organization: str = Field(..., description="Organizing body")
    conference_url: Optional[str] = None
    conference_dates: str = Field(..., description="Conference dates")
    location: Optional[str] = None

    # Highlight details
    title: str = Field(..., description="Highlight title")
    session_type: str = Field(
        ...,
        description="late_breaking, keynote, abstract, presentation"
    )
    presenters: list[str] = Field(default_factory=list)

    # Content
    summary: str = Field(..., description="Brief summary")
    key_findings: list[str] = Field(default_factory=list)
    clinical_significance: str = Field(
        ...,
        description="Why this matters clinically"
    )

    # Study/Trial details (if applicable)
    study_name: Optional[str] = Field(None, description="Trial or study name")
    study_design: Optional[str] = None
    sample_size: Optional[int] = None
    primary_endpoint: Optional[str] = None
    results: Optional[str] = None

    # Classification
    specialty: list[str] = Field(default_factory=list)
    topic: list[str] = Field(default_factory=list)

    # Media
    presentation_url: Optional[str] = None
    slides_url: Optional[str] = None
    video_url: Optional[str] = None

    # Engagement
    practice_changing: bool = Field(
        default=False,
        description="Is this practice-changing?"
    )
    controversy_level: str = Field(
        default="none",
        description="none, mild, moderate, high"
    )

    # Timestamps
    presentation_date: datetime = Field(..., description="When it was presented")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class GuidelineUpdate(BaseModel):
    """Medical guideline change notification."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Guideline identification
    guideline_name: str = Field(..., description="Official guideline name")
    organization: str = Field(
        ...,
        description="Issuing organization (ICMR, WHO, AHA, etc.)"
    )
    version: str = Field(..., description="Version number or year")
    previous_version: Optional[str] = None

    # URLs and access
    guideline_url: Optional[str] = None
    pdf_url: Optional[str] = None
    summary_url: Optional[str] = None

    # Update details
    update_type: str = Field(
        ...,
        description="new, revision, update, correction"
    )
    release_date: datetime = Field(..., description="Official release date")
    effective_date: Optional[datetime] = Field(
        None,
        description="When changes take effect"
    )

    # Changes
    summary: str = Field(..., description="What changed summary")
    key_changes: list[str] = Field(
        default_factory=list,
        description="Bullet points of major changes"
    )
    whats_new: list[str] = Field(
        default_factory=list,
        description="New recommendations"
    )
    whats_removed: list[str] = Field(
        default_factory=list,
        description="Deprecated recommendations"
    )
    whats_modified: list[str] = Field(
        default_factory=list,
        description="Modified recommendations"
    )

    # Clinical impact
    impact_level: str = Field(
        default="moderate",
        description="low, moderate, high, critical"
    )
    clinical_implications: str = Field(
        ...,
        description="How this affects clinical practice"
    )
    implementation_guidance: Optional[str] = Field(
        None,
        description="How to implement changes"
    )

    # Classification
    specialty: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(
        default_factory=list,
        description="Medical conditions covered"
    )
    topics: list[str] = Field(
        default_factory=list,
        description="Topics (diagnosis, treatment, screening, etc.)"
    )

    # Supporting evidence
    evidence_level: str = Field(
        default="high",
        description="Quality of evidence: low, moderate, high"
    )
    key_references: list[str] = Field(
        default_factory=list,
        description="Key supporting studies"
    )

    # Engagement
    priority: NewsPriority = Field(default=NewsPriority.MEDIUM)
    must_read: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DrugApproval(BaseModel):
    """New drug approval or significant update."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Drug identification
    drug_name: str = Field(..., description="Generic name")
    brand_names: list[str] = Field(default_factory=list)
    manufacturer: str = Field(..., description="Pharmaceutical company")
    drug_class: str = Field(..., description="Pharmacological class")

    # Approval details
    approval_type: str = Field(
        ...,
        description="new_drug, new_indication, generic, biosimilar, label_update"
    )
    regulatory_body: str = Field(
        ...,
        description="FDA, CDSCO, EMA, etc."
    )
    approval_date: datetime = Field(..., description="Approval date")

    # URLs
    announcement_url: Optional[str] = None
    prescribing_info_url: Optional[str] = None

    # Indication and usage
    indication: str = Field(..., description="Approved indication")
    mechanism_of_action: Optional[str] = None
    dosage_forms: list[str] = Field(
        default_factory=list,
        description="Available dosage forms"
    )
    route_of_administration: list[str] = Field(default_factory=list)

    # Clinical data
    pivotal_trials: list[str] = Field(
        default_factory=list,
        description="Key clinical trial names"
    )
    efficacy_summary: Optional[str] = Field(
        None,
        description="Summary of efficacy data"
    )
    safety_summary: Optional[str] = Field(
        None,
        description="Summary of safety profile"
    )

    # Significance
    significance: str = Field(
        ...,
        description="Why this approval matters"
    )
    first_in_class: bool = Field(default=False)
    breakthrough_designation: bool = Field(default=False)
    orphan_drug: bool = Field(default=False)

    # Warnings and contraindications
    boxed_warnings: list[str] = Field(
        default_factory=list,
        description="Black box warnings"
    )
    contraindications: list[str] = Field(default_factory=list)
    notable_interactions: list[str] = Field(default_factory=list)

    # Classification
    specialty: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)

    # Market info
    expected_availability: Optional[str] = None
    estimated_cost: Optional[str] = None

    # Engagement
    priority: NewsPriority = Field(default=NewsPriority.MEDIUM)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class ResearchBreakthrough(BaseModel):
    """Significant research finding."""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Publication details
    title: str = Field(..., description="Study title")
    authors: list[str] = Field(default_factory=list)
    institution: list[str] = Field(
        default_factory=list,
        description="Lead institutions"
    )
    journal: str = Field(..., description="Publishing journal")
    publication_date: datetime = Field(..., description="Publication date")

    # URLs
    article_url: Optional[str] = None
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None

    # Study design
    study_type: str = Field(
        ...,
        description="rct, cohort, case_control, meta_analysis, etc."
    )
    study_design: str = Field(..., description="Detailed study design")
    sample_size: int = Field(..., ge=1)
    duration: Optional[str] = None

    # Findings
    summary: str = Field(..., description="Brief summary")
    primary_outcome: str = Field(..., description="Primary outcome measure")
    key_results: list[str] = Field(
        default_factory=list,
        description="Key numerical results"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Main findings in plain language"
    )

    # Significance
    clinical_significance: str = Field(
        ...,
        description="Clinical implications"
    )
    practice_changing: bool = Field(default=False)
    paradigm_shift: bool = Field(default=False)

    # Limitations
    study_limitations: list[str] = Field(
        default_factory=list,
        description="Key limitations to consider"
    )

    # Classification
    specialty: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(
        default_factory=list,
        description="Interventions studied"
    )

    # Quality metrics
    evidence_level: str = Field(
        default="high",
        description="Quality of evidence"
    )
    impact_factor: Optional[float] = Field(
        None,
        description="Journal impact factor"
    )

    # Engagement
    priority: NewsPriority = Field(default=NewsPriority.MEDIUM)
    expert_commentary: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class UserPreference(BaseModel):
    """User preferences for news feed personalization."""

    user_id: str = Field(..., description="User ID")

    # Specialty preferences
    primary_specialty: str = Field(..., description="Primary medical specialty")
    sub_specialties: list[str] = Field(
        default_factory=list,
        description="Sub-specialty interests"
    )
    additional_interests: list[str] = Field(
        default_factory=list,
        description="Other areas of interest"
    )

    # Category preferences (1-5 scale)
    category_weights: dict[str, int] = Field(
        default_factory=lambda: {
            "research": 5,
            "guidelines": 5,
            "drug_approvals": 4,
            "drug_safety": 5,
            "conferences": 3,
            "clinical_practice": 4,
            "health_policy": 2,
            "medical_technology": 3,
        },
        description="Interest level per category (1-5)"
    )

    # Content preferences
    preferred_sources: list[NewsSource] = Field(
        default_factory=list,
        description="Preferred news sources"
    )
    blocked_sources: list[NewsSource] = Field(
        default_factory=list,
        description="Sources to exclude"
    )

    # Conditions of interest
    conditions: list[str] = Field(
        default_factory=list,
        description="Specific conditions to follow"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Custom keywords to track"
    )

    # Feed settings
    items_per_page: int = Field(default=20, ge=10, le=100)
    show_summaries: bool = Field(default=True)
    auto_mark_read_on_scroll: bool = Field(default=False)

    # Notification preferences
    breaking_news_notifications: bool = Field(default=True)
    daily_digest: bool = Field(default=True)
    digest_time: str = Field(default="07:00", description="HH:MM format")

    # Learning preferences
    learn_from_reading: bool = Field(
        default=True,
        description="Learn preferences from reading behavior"
    )
    learn_from_searches: bool = Field(default=True)
    learn_from_bookmarks: bool = Field(default=True)

    # Display preferences
    show_images: bool = Field(default=True)
    compact_view: bool = Field(default=False)
    dark_mode: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "primary_specialty": "cardiology",
                "sub_specialties": ["interventional_cardiology", "heart_failure"],
                "category_weights": {
                    "research": 5,
                    "guidelines": 5,
                    "drug_approvals": 4
                },
                "daily_digest": True,
                "digest_time": "07:30"
            }
        }


class NewsBookmark(BaseModel):
    """Saved/bookmarked article."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    article_id: str = Field(..., description="Article ID")

    # Article snapshot (denormalized for offline access)
    article_title: str = Field(..., description="Article title")
    article_url: str = Field(..., description="Article URL")
    article_source: NewsSource = Field(..., description="Source")

    # Organization
    collection_id: Optional[str] = Field(
        None,
        description="Collection ID if organized"
    )
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, description="User notes")

    # Reading
    reading_status: ReadingStatus = Field(default=ReadingStatus.SAVED)
    reading_progress: int = Field(default=0, ge=0, le=100)

    # Sharing
    shared_with: list[str] = Field(
        default_factory=list,
        description="User IDs shared with"
    )

    # Timestamps
    bookmarked_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class NewsCollection(BaseModel):
    """Collection of bookmarked articles."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")

    # Collection details
    name: str = Field(..., description="Collection name")
    description: Optional[str] = None
    emoji: Optional[str] = Field(None, description="Collection emoji icon")
    color: Optional[str] = Field(None, description="Collection color code")

    # Settings
    is_public: bool = Field(default=False)
    is_collaborative: bool = Field(default=False)
    collaborators: list[str] = Field(
        default_factory=list,
        description="User IDs with edit access"
    )

    # Metadata
    article_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "name": "Heart Failure 2026",
                "description": "Latest HF research and guidelines",
                "emoji": "❤️",
                "color": "#FF6B6B"
            }
        }


class NewsEngagement(BaseModel):
    """User engagement with news article."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    article_id: str = Field(..., description="Article ID")

    # Engagement metrics
    viewed: bool = Field(default=False)
    viewed_at: Optional[datetime] = None

    read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    reading_time_seconds: int = Field(default=0)

    bookmarked: bool = Field(default=False)
    bookmarked_at: Optional[datetime] = None

    shared: bool = Field(default=False)
    shared_at: Optional[datetime] = None
    shared_to: list[str] = Field(
        default_factory=list,
        description="Channels shared to"
    )

    # Feedback
    liked: Optional[bool] = None
    liked_at: Optional[datetime] = None

    rating: Optional[int] = Field(None, ge=1, le=5)
    rated_at: Optional[datetime] = None

    # Timestamps
    first_interaction: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class NewsFeedMetrics(BaseModel):
    """Aggregate metrics for news feed."""

    # Coverage metrics
    total_articles: int = Field(default=0)
    articles_today: int = Field(default=0)
    articles_this_week: int = Field(default=0)

    # By category
    by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Article count per category"
    )

    # By source
    by_source: dict[str, int] = Field(
        default_factory=dict,
        description="Article count per source"
    )

    # Engagement
    total_views: int = Field(default=0)
    total_reads: int = Field(default=0)
    total_bookmarks: int = Field(default=0)
    total_shares: int = Field(default=0)

    # Trending
    trending_topics: list[str] = Field(
        default_factory=list,
        description="Currently trending topics"
    )
    trending_specialties: list[str] = Field(
        default_factory=list,
        description="Specialties with most activity"
    )

    # Quality metrics
    avg_credibility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Timestamps
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
