"""
Learning and CME Data Models
"""

from datetime import datetime, date
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Type of learning activity"""
    QUERY = "query"
    QUERY_DEEP = "query_deep"  # Query with follow-up depth
    CALCULATOR = "calculator"
    ARTICLE_READ = "article_read"
    VIDEO_VIEW = "video_view"
    QUIZ_ATTEMPT = "quiz_attempt"
    QUIZ_PASS = "quiz_pass"
    CASE_STUDY = "case_study"
    MODULE_COMPLETE = "module_complete"
    PATH_COMPLETE = "path_complete"
    DISCUSSION = "discussion"  # Community participation


class CMECategory(str, Enum):
    """CME credit categories (MCI compliant)"""
    CATEGORY_1 = "category_1"  # Formal CME activities
    CATEGORY_2 = "category_2"  # Journal reading, self-study
    CATEGORY_3 = "category_3"  # Teaching, presentations


class AccreditationBody(str, Enum):
    """Accreditation bodies"""
    MCI = "mci"  # Medical Council of India
    STATE_COUNCIL = "state_council"  # State medical councils
    IMA = "ima"  # Indian Medical Association
    SELF_DIRECTED = "self_directed"  # Self-directed learning


class DifficultyLevel(str, Enum):
    """Quiz difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QuestionType(str, Enum):
    """Quiz question types"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    CASE_BASED = "case_based"
    IMAGE_BASED = "image_based"
    CLINICAL_SCENARIO = "clinical_scenario"


class PathStatus(str, Enum):
    """Learning path enrollment status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class LearningActivity(BaseModel):
    """A learning activity performed by a user"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    activity_type: ActivityType

    # Content details
    title: str = Field(..., description="Activity title")
    description: Optional[str] = Field(None, description="Activity description")
    specialty: Optional[str] = Field(None, description="Medical specialty")
    topics: list[str] = Field(default_factory=list, description="Topics covered")

    # Metadata
    duration_seconds: int = Field(0, description="Time spent on activity")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quiz accuracy")

    # Context
    query_id: Optional[str] = Field(None, description="Related query ID")
    quiz_id: Optional[str] = Field(None, description="Related quiz ID")
    path_id: Optional[str] = Field(None, description="Related learning path ID")

    # Credits
    cme_credits_earned: float = Field(0.0, description="CME credits awarded")
    points_earned: int = Field(0, description="XP points earned")

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class CMECredit(BaseModel):
    """A CME credit record"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    activity_id: str

    # Credit details
    credits: float = Field(..., description="Number of CME credits")
    category: CMECategory
    accreditation_body: AccreditationBody

    # Activity info
    activity_title: str
    activity_type: ActivityType
    specialty: Optional[str] = None
    topics: list[str] = Field(default_factory=list)

    # Validity
    earned_date: date = Field(default_factory=date.today)
    expires_date: date  # Usually 5 years from earning
    is_valid: bool = True

    # Compliance
    certificate_id: Optional[str] = Field(None, description="Associated certificate")
    verification_code: str = Field(default_factory=lambda: str(uuid4())[:8].upper())

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class CMECertificate(BaseModel):
    """A CME certificate"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str

    # User details (cached for certificate)
    doctor_name: str
    registration_number: Optional[str] = None
    specialty: Optional[str] = None
    institution: Optional[str] = None

    # Certificate details
    certificate_number: str = Field(default_factory=lambda: f"DORA-{str(uuid4())[:12].upper()}")
    title: str = Field(..., description="Certificate title")
    description: str = Field(..., description="What was learned")

    # Credits
    total_credits: float = Field(..., description="Total CME credits")
    category: CMECategory
    accreditation_body: AccreditationBody

    # Content
    topics_covered: list[str] = Field(default_factory=list)
    activities_completed: int = Field(0, description="Number of activities")

    # Dates
    issued_date: date = Field(default_factory=date.today)
    valid_until: date  # Usually 5 years

    # Verification
    qr_code_data: str = Field(..., description="QR code URL for verification")
    verification_url: str = Field(..., description="Public verification URL")
    digital_signature: Optional[str] = Field(None, description="Digital signature")

    # Files
    pdf_path: Optional[str] = Field(None, description="Path to generated PDF")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class LearningStreak(BaseModel):
    """User's learning streak tracking"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str

    # Current streak
    current_streak: int = Field(0, description="Current consecutive days")
    longest_streak: int = Field(0, description="Longest ever streak")

    # Dates
    streak_start_date: Optional[date] = None
    last_activity_date: Optional[date] = None

    # Streak protection
    freeze_tokens: int = Field(0, description="Tokens to skip a day")
    freeze_used_dates: list[date] = Field(default_factory=list)

    # Milestones
    milestones_achieved: list[int] = Field(default_factory=list, description="[7, 30, 100, 365]")

    # Stats
    total_active_days: int = Field(0, description="Total days with activity")

    class Config:
        use_enum_values = True


class Achievement(BaseModel):
    """Achievement/badge definition"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str = Field(..., description="Unique achievement key")

    # Display
    title: str
    description: str
    icon: str = Field(..., description="Emoji or icon name")

    # Criteria
    criteria_type: str = Field(..., description="streak, queries, quizzes, specialty_mastery, etc.")
    criteria_value: int = Field(..., description="Threshold to earn")

    # Rewards
    points: int = Field(0, description="XP points awarded")
    badge_tier: str = Field("bronze", description="bronze, silver, gold, platinum")

    # Visibility
    is_hidden: bool = Field(False, description="Secret achievement")

    class Config:
        use_enum_values = True


class UserAchievement(BaseModel):
    """User's earned achievement"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    achievement_id: str

    # Achievement details (cached)
    achievement_key: str
    title: str
    icon: str
    points_earned: int

    # Earning
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress_value: int = Field(..., description="Value when earned")

    # Display
    is_showcased: bool = Field(False, description="Show on profile")

    class Config:
        use_enum_values = True


class Quiz(BaseModel):
    """A quiz/assessment"""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Content
    title: str
    description: str
    specialty: Optional[str] = None
    topics: list[str] = Field(default_factory=list)

    # Difficulty
    difficulty: DifficultyLevel
    estimated_time_minutes: int = Field(10, description="Estimated completion time")

    # Questions
    questions: list["QuizQuestion"] = Field(default_factory=list)
    total_questions: int = Field(0)

    # CME
    cme_credits: float = Field(0.5, description="CME credits for completion")
    passing_score: float = Field(0.7, description="Minimum score to pass (0-1)")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Creator user ID")
    is_active: bool = True

    # Analytics
    attempt_count: int = 0
    average_score: float = 0.0

    # Source
    source_query_id: Optional[str] = Field(None, description="Generated from query")
    source_content_id: Optional[str] = Field(None, description="Based on content")

    class Config:
        use_enum_values = True


class QuizQuestion(BaseModel):
    """A single quiz question"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    quiz_id: str

    # Question
    question_type: QuestionType
    question_text: str
    question_context: Optional[str] = Field(None, description="Case scenario, patient details")

    # Media
    image_url: Optional[str] = Field(None, description="Image for image-based questions")

    # Options (for MCQ)
    options: list[dict[str, Any]] = Field(default_factory=list, description="[{'text': '...', 'is_correct': bool}]")

    # Answer
    correct_answer: str = Field(..., description="The correct answer or explanation")
    explanation: str = Field(..., description="Why this is correct")

    # References
    citations: list[str] = Field(default_factory=list, description="Supporting sources")

    # Difficulty
    difficulty: DifficultyLevel
    points: int = Field(1, description="Points for correct answer")

    # Analytics
    times_shown: int = 0
    times_correct: int = 0
    times_incorrect: int = 0

    class Config:
        use_enum_values = True


class QuizAttempt(BaseModel):
    """User's quiz attempt"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    quiz_id: str

    # Answers
    answers: dict[str, Any] = Field(default_factory=dict, description="question_id -> user_answer")

    # Scoring
    score: float = Field(..., ge=0.0, le=1.0, description="Score as percentage")
    correct_count: int = 0
    incorrect_count: int = 0
    total_questions: int = 0

    # Result
    passed: bool = False
    time_taken_seconds: int = 0

    # Credits
    cme_credits_earned: float = 0.0
    points_earned: int = 0

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Spaced repetition
    next_review_date: Optional[date] = Field(None, description="When to review again")
    ease_factor: float = Field(2.5, description="SM-2 algorithm ease factor")
    interval_days: int = Field(0, description="Days until next review")

    class Config:
        use_enum_values = True


class LearningPath(BaseModel):
    """A structured learning curriculum"""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Content
    title: str
    description: str
    specialty: str
    topics: list[str] = Field(default_factory=list)

    # Structure
    modules: list["LearningModule"] = Field(default_factory=list)
    total_modules: int = 0

    # Difficulty
    difficulty: DifficultyLevel
    estimated_hours: int = Field(..., description="Total estimated time")

    # CME
    total_cme_credits: float = Field(..., description="Total credits for completion")

    # Requirements
    prerequisites: list[str] = Field(default_factory=list, description="Required path IDs")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False

    # Analytics
    enrollment_count: int = 0
    completion_count: int = 0
    average_rating: float = 0.0

    # Display
    thumbnail_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class LearningModule(BaseModel):
    """A module within a learning path"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    path_id: str

    # Content
    title: str
    description: str
    order: int = Field(..., description="Module order in path")

    # Content items
    content_items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'type': 'article|quiz|video|case', 'id': '...', 'required': bool}]"
    )

    # Requirements
    is_required: bool = True

    # CME
    cme_credits: float = Field(0.0, description="Credits for module completion")

    # Estimated time
    estimated_minutes: int = 30

    class Config:
        use_enum_values = True


class PathEnrollment(BaseModel):
    """User's enrollment in a learning path"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    path_id: str

    # Progress
    status: PathStatus
    current_module_id: Optional[str] = None
    completed_module_ids: list[str] = Field(default_factory=list)

    # Stats
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)
    total_time_spent_seconds: int = 0

    # Credits
    cme_credits_earned: float = 0.0

    # Dates
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

    # Certificate
    certificate_id: Optional[str] = Field(None, description="Certificate if completed")

    # Rating
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None

    class Config:
        use_enum_values = True


class LearningGoal(BaseModel):
    """User's learning goal"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str

    # Goal
    goal_type: str = Field(..., description="daily_queries, weekly_credits, monthly_streak, etc.")
    target_value: int = Field(..., description="Target to achieve")
    current_value: int = Field(0, description="Current progress")

    # Period
    period_type: str = Field(..., description="daily, weekly, monthly, yearly")
    period_start: date
    period_end: date

    # Status
    is_active: bool = True
    is_achieved: bool = False
    achieved_at: Optional[datetime] = None

    # Reminders
    reminder_enabled: bool = True
    reminder_time: Optional[str] = Field(None, description="HH:MM format")

    class Config:
        use_enum_values = True


class LearningReminder(BaseModel):
    """Spaced repetition reminder"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str

    # Content
    reminder_type: str = Field(..., description="spaced_repetition, streak, goal, quiz_review")
    title: str
    message: str

    # Reference
    reference_type: Optional[str] = Field(None, description="query, quiz, activity")
    reference_id: Optional[str] = None

    # Scheduling
    scheduled_for: datetime
    sent_at: Optional[datetime] = None

    # Status
    is_sent: bool = False
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    # Delivery
    delivery_channels: list[str] = Field(default_factory=lambda: ["in_app"], description="in_app, email, sms, push")

    class Config:
        use_enum_values = True


class LearningAnalytics(BaseModel):
    """User's learning analytics summary"""

    user_id: str

    # Period
    period_start: date
    period_end: date

    # Activity summary
    total_activities: int = 0
    total_time_spent_seconds: int = 0
    activities_by_type: dict[str, int] = Field(default_factory=dict)

    # CME
    total_cme_credits: float = 0.0
    credits_by_category: dict[str, float] = Field(default_factory=dict)
    credits_by_specialty: dict[str, float] = Field(default_factory=dict)

    # Streaks
    current_streak: int = 0
    longest_streak: int = 0

    # Quiz performance
    total_quizzes: int = 0
    quizzes_passed: int = 0
    average_quiz_score: float = 0.0

    # Topics
    top_topics: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'topic': '...', 'count': int, 'mastery': float}]"
    )

    # Knowledge gaps
    weak_areas: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'topic': '...', 'accuracy': float, 'recommendation': '...'}]"
    )

    # Comparison
    percentile_rank: Optional[float] = Field(None, ge=0.0, le=100.0, description="Compared to peers")

    # Achievements
    achievements_earned: int = 0
    total_points: int = 0
    current_level: int = 1

    class Config:
        use_enum_values = True


# Update forward references
Quiz.model_rebuild()
LearningPath.model_rebuild()
