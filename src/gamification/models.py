"""
Gamification Data Models

Gamification system for making medical learning addictive and rewarding.
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class BadgeTier(str, Enum):
    """Badge tier levels"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    LEGENDARY = "legendary"


class ChallengeType(str, Enum):
    """Type of challenge"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SPECIAL = "special"  # Conference week, holidays


class ChallengeStatus(str, Enum):
    """Challenge completion status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class LeaderboardType(str, Enum):
    """Type of leaderboard"""
    GLOBAL = "global"
    SPECIALTY = "specialty"
    REGIONAL = "regional"  # City, state
    FRIENDS = "friends"
    TEAM = "team"


class LeaderboardPeriod(str, Enum):
    """Leaderboard time period"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class RewardType(str, Enum):
    """Type of reward"""
    PREMIUM_FEATURE = "premium_feature"
    SUBSCRIPTION_DISCOUNT = "subscription_discount"
    CONFERENCE_TICKET = "conference_ticket"
    MEDICAL_BOOK = "medical_book"
    CME_COURSE = "cme_course"
    GIFT_CARD = "gift_card"
    CUSTOM = "custom"


class RewardStatus(str, Enum):
    """Reward redemption status"""
    AVAILABLE = "available"
    LOCKED = "locked"  # Level requirement not met
    REDEEMED = "redeemed"
    EXPIRED = "expired"


class PointEventType(str, Enum):
    """Types of point-earning events"""
    QUERY = "query"  # +5 XP
    QUERY_DEEP = "query_deep"  # +10 XP
    QUIZ_COMPLETE = "quiz_complete"  # +25 XP
    QUIZ_PERFECT = "quiz_perfect"  # +50 XP
    CASE_CONTRIBUTION = "case_contribution"  # +100 XP
    PEER_CONSULTATION = "peer_consultation"  # +50 XP
    DAILY_LOGIN = "daily_login"  # +10 XP
    STREAK_BONUS = "streak_bonus"  # Multiplier
    BADGE_EARNED = "badge_earned"  # Variable
    CHALLENGE_COMPLETE = "challenge_complete"  # Variable
    REFERRAL = "referral"  # +200 XP
    CONTENT_RATED = "content_rated"  # +5 XP
    ARTICLE_READ = "article_read"  # +5 XP
    VIDEO_WATCHED = "video_watched"  # +10 XP


class UserProgress(BaseModel):
    """Overall gamification progress for a user"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")

    # Points and Level
    total_xp: int = Field(0, description="Total experience points")
    current_level: int = Field(1, description="Current level (1-100)")
    xp_current_level: int = Field(0, description="XP earned in current level")
    xp_to_next_level: int = Field(100, description="XP needed for next level")

    # Rank
    global_rank: Optional[int] = Field(None, description="Global ranking")
    specialty_rank: Optional[int] = Field(None, description="Rank within specialty")
    percentile: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentile rank")

    # Streaks
    current_streak: int = Field(0, description="Current daily streak")
    longest_streak: int = Field(0, description="Longest ever streak")
    streak_freeze_tokens: int = Field(0, description="Tokens to skip a day")

    # Achievements
    total_badges: int = Field(0, description="Total badges earned")
    rare_badges: int = Field(0, description="Rare/legendary badges")
    showcased_badges: list[str] = Field(default_factory=list, description="Badge IDs to display")

    # Activity Stats
    total_queries: int = Field(0)
    total_quizzes: int = Field(0)
    total_cases_contributed: int = Field(0)
    total_peer_consultations: int = Field(0)
    total_active_days: int = Field(0)

    # Timestamps
    last_activity_date: Optional[date] = None
    last_xp_earned_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Points(BaseModel):
    """Individual XP points transaction"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")

    # Points
    xp_amount: int = Field(..., description="Points earned (can be negative for penalties)")
    event_type: PointEventType
    event_description: str = Field(..., description="What earned these points")

    # Multipliers
    base_xp: int = Field(..., description="Base XP before multipliers")
    streak_multiplier: float = Field(1.0, description="Streak bonus multiplier")
    level_multiplier: float = Field(1.0, description="High-level player bonus")
    event_multiplier: float = Field(1.0, description="Special event multiplier")

    # Context
    reference_type: Optional[str] = Field(None, description="query, quiz, case, etc.")
    reference_id: Optional[str] = Field(None, description="ID of related entity")

    # State at earning
    level_at_earn: int = Field(..., description="User level when earned")
    total_xp_after: int = Field(..., description="Total XP after this transaction")

    # Timestamps
    earned_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Level(BaseModel):
    """Level definition (1-100)"""

    level: int = Field(..., ge=1, le=100, description="Level number")
    name: str = Field(..., description="Level name")
    title: str = Field(..., description="Title earned at this level")

    # XP Requirements
    xp_required: int = Field(..., description="Total XP needed to reach this level")
    xp_for_level: int = Field(..., description="XP needed within this level")

    # Rewards
    reward_description: str = Field(..., description="What you get at this level")
    unlocks: list[str] = Field(default_factory=list, description="Features unlocked")

    # Display
    icon: str = Field("⭐", description="Level icon/emoji")
    color: str = Field("#FFD700", description="Display color (hex)")

    # Special abilities
    xp_bonus_multiplier: float = Field(1.0, description="XP earning multiplier")
    special_abilities: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Badge(BaseModel):
    """Achievement badge definition"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str = Field(..., description="Unique badge key (e.g., 'streak_7_days')")

    # Display
    title: str = Field(..., description="Badge name")
    description: str = Field(..., description="How to earn this badge")
    icon: str = Field(..., description="Badge emoji/icon")
    tier: BadgeTier = Field(BadgeTier.BRONZE, description="Badge rarity")

    # Criteria
    criteria_type: str = Field(..., description="Type of achievement")
    criteria_value: int = Field(..., description="Threshold to earn")
    criteria_description: str = Field(..., description="Human-readable criteria")

    # Category
    category: str = Field(..., description="streak, query, learning, competition, community, specialty")

    # Rewards
    xp_reward: int = Field(0, description="XP awarded when earned")

    # Visibility
    is_hidden: bool = Field(False, description="Secret achievement")
    is_rare: bool = Field(False, description="Rare/legendary badge")

    # Requirements
    required_level: int = Field(1, description="Minimum level to earn")
    prerequisite_badges: list[str] = Field(default_factory=list, description="Required badge keys")

    # Stats
    total_earned: int = Field(0, description="How many users earned this")
    earn_percentage: float = Field(0.0, description="% of users who earned")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class UserBadge(BaseModel):
    """User's earned badge"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    badge_id: str = Field(..., description="Badge ID")

    # Badge details (cached for performance)
    badge_key: str
    badge_title: str
    badge_icon: str
    badge_tier: BadgeTier
    badge_category: str

    # Earning details
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress_value: int = Field(..., description="Value when earned (e.g., 30 for 30-day streak)")
    xp_earned: int = Field(0, description="XP awarded")

    # Display
    is_showcased: bool = Field(False, description="Display on profile")
    showcase_order: int = Field(0, description="Order in showcase")

    # Notification
    notification_sent: bool = Field(False)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Streak(BaseModel):
    """User's activity streak"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")

    # Current streak
    current_streak: int = Field(0, description="Current consecutive days")
    longest_streak: int = Field(0, description="Longest ever streak")

    # Dates
    streak_start_date: Optional[date] = None
    last_activity_date: Optional[date] = None
    next_required_date: Optional[date] = None

    # Streak protection
    freeze_tokens: int = Field(0, description="Tokens to skip a day")
    freeze_used_dates: list[date] = Field(default_factory=list)
    freeze_available: int = Field(0, description="Total freezes available")

    # Milestones
    milestones_achieved: list[int] = Field(
        default_factory=list,
        description="Milestones reached (7, 30, 100, 365)"
    )

    # Stats
    total_active_days: int = Field(0, description="Total days with activity")
    total_streak_breaks: int = Field(0, description="Times streak was broken")
    recovery_count: int = Field(0, description="Times recovered within 24h")

    # XP Bonus
    current_multiplier: float = Field(1.0, description="Current streak XP multiplier")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Challenge(BaseModel):
    """A daily/weekly/monthly challenge"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    challenge_type: ChallengeType

    # Content
    title: str = Field(..., description="Challenge name")
    description: str = Field(..., description="What to do")
    icon: str = Field("🎯", description="Challenge icon")

    # Criteria
    goal_type: str = Field(..., description="queries, quizzes, reading, etc.")
    goal_value: int = Field(..., description="Target to achieve")

    # Rewards
    xp_reward: int = Field(..., description="XP for completion")
    bonus_rewards: list[str] = Field(default_factory=list, description="Extra rewards")

    # Validity
    start_date: date = Field(..., description="When challenge starts")
    end_date: date = Field(..., description="When challenge ends")
    is_active: bool = Field(True)

    # Requirements
    required_level: int = Field(1, description="Minimum level")
    specialty: Optional[str] = Field(None, description="Specialty-specific challenge")

    # Stats
    total_participants: int = Field(0)
    total_completions: int = Field(0)
    completion_rate: float = Field(0.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class UserChallenge(BaseModel):
    """User's challenge progress"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    challenge_id: str = Field(..., description="Challenge ID")

    # Challenge details (cached)
    challenge_title: str
    challenge_type: ChallengeType
    goal_type: str
    goal_value: int

    # Progress
    current_value: int = Field(0, description="Current progress")
    status: ChallengeStatus = Field(ChallengeStatus.ACTIVE)

    # Completion
    completed_at: Optional[datetime] = None
    xp_earned: int = Field(0)

    # Timestamps
    accepted_at: datetime = Field(default_factory=datetime.utcnow)
    last_progress_at: Optional[datetime] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Leaderboard(BaseModel):
    """Leaderboard rankings"""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Leaderboard info
    leaderboard_type: LeaderboardType
    period: LeaderboardPeriod

    # Scope
    specialty: Optional[str] = Field(None, description="For specialty leaderboards")
    region: Optional[str] = Field(None, description="For regional leaderboards")

    # Period
    period_start: date
    period_end: date

    # Rankings (top 100)
    rankings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{'rank': int, 'user_id': str, 'username': str, 'xp': int, 'level': int}]"
    )

    # Stats
    total_participants: int = Field(0)

    # Cache
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    cache_valid_until: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=1)
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class LeaderboardEntry(BaseModel):
    """User's position in a leaderboard"""

    user_id: str = Field(..., description="User ID")
    leaderboard_id: str = Field(..., description="Leaderboard ID")

    # Position
    rank: int = Field(..., description="Current rank")
    previous_rank: Optional[int] = Field(None, description="Previous rank for change indicator")

    # User info (cached)
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    specialty: Optional[str] = None

    # Score
    xp_amount: int = Field(..., description="XP in this period")
    level: int = Field(..., description="Current level")
    badges_count: int = Field(0)

    # Display
    is_anonymous: bool = Field(False, description="Hide identity")

    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class Reward(BaseModel):
    """Redeemable reward definition"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    reward_type: RewardType

    # Content
    title: str = Field(..., description="Reward name")
    description: str = Field(..., description="Reward details")
    icon: str = Field("🎁", description="Reward icon")

    # Cost
    xp_cost: int = Field(0, description="XP cost to redeem")
    level_required: int = Field(1, description="Minimum level")

    # Availability
    total_quantity: Optional[int] = Field(None, description="Total available (None = unlimited)")
    remaining_quantity: Optional[int] = Field(None)

    # Value
    monetary_value: Optional[float] = Field(None, description="Value in INR")
    partner: Optional[str] = Field(None, description="Partner providing reward")

    # Validity
    valid_from: date = Field(default_factory=date.today)
    valid_until: Optional[date] = None
    is_active: bool = Field(True)

    # Requirements
    required_badges: list[str] = Field(default_factory=list, description="Required badge keys")
    specialty: Optional[str] = Field(None, description="Specialty-specific reward")

    # Stats
    total_redemptions: int = Field(0)
    redemption_rate: float = Field(0.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class UserReward(BaseModel):
    """User's redeemed reward"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    reward_id: str = Field(..., description="Reward ID")

    # Reward details (cached)
    reward_title: str
    reward_type: RewardType
    reward_description: str

    # Redemption
    xp_spent: int = Field(..., description="XP spent")
    status: RewardStatus = Field(RewardStatus.AVAILABLE)

    # Delivery
    redemption_code: str = Field(
        default_factory=lambda: str(uuid4())[:12].upper(),
        description="Unique redemption code"
    )
    redemption_url: Optional[str] = Field(None, description="URL to claim reward")
    instructions: Optional[str] = Field(None, description="How to use reward")

    # Fulfillment
    fulfilled: bool = Field(False)
    fulfilled_at: Optional[datetime] = None
    fulfillment_notes: Optional[str] = None

    # Timestamps
    redeemed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Milestone(BaseModel):
    """Major gamification milestone"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    milestone_type: str = Field(..., description="xp, level, streak, badges, specialty_mastery")

    # Content
    title: str = Field(..., description="Milestone name")
    description: str = Field(..., description="Achievement description")
    icon: str = Field("🏆", description="Milestone icon")

    # Criteria
    threshold_value: int = Field(..., description="Value to achieve")

    # Rewards
    xp_reward: int = Field(0)
    badge_id: Optional[str] = Field(None, description="Badge awarded")
    special_rewards: list[str] = Field(default_factory=list)

    # Display
    celebration_message: str = Field(..., description="Congratulations message")
    animation: Optional[str] = Field(None, description="Celebration animation type")

    # Stats
    total_achieved: int = Field(0)
    achievement_rate: float = Field(0.0, description="% of users who achieved")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class UserMilestone(BaseModel):
    """User's achieved milestone"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., description="User ID")
    milestone_id: str = Field(..., description="Milestone ID")

    # Milestone details (cached)
    milestone_title: str
    milestone_type: str
    threshold_value: int

    # Achievement
    achieved_at: datetime = Field(default_factory=datetime.utcnow)
    actual_value: int = Field(..., description="Actual value when achieved")
    xp_earned: int = Field(0)

    # Celebration
    celebration_shown: bool = Field(False)
    shared_publicly: bool = Field(False)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class GamificationEvent(BaseModel):
    """Special gamification event (bonus XP week, etc.)"""

    id: str = Field(default_factory=lambda: str(uuid4()))

    # Event info
    title: str = Field(..., description="Event name")
    description: str = Field(..., description="Event description")
    icon: str = Field("🎉", description="Event icon")

    # Type
    event_type: str = Field(..., description="bonus_xp, special_challenges, limited_rewards")

    # Bonuses
    xp_multiplier: float = Field(1.0, description="XP earning multiplier")
    special_challenges: list[str] = Field(default_factory=list, description="Challenge IDs")
    limited_rewards: list[str] = Field(default_factory=list, description="Reward IDs")

    # Validity
    start_date: datetime = Field(..., description="Event start")
    end_date: datetime = Field(..., description="Event end")
    is_active: bool = Field(True)

    # Requirements
    required_level: int = Field(1)
    eligible_specialties: list[str] = Field(default_factory=list, description="Empty = all")

    # Stats
    total_participants: int = Field(0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
