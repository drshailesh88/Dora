"""
Gamification Module

Complete gamification system for Dora medical knowledge platform.
Makes medical learning addictive and rewarding.
"""

# Models
from .models import (
    # Enums
    BadgeTier,
    ChallengeType,
    ChallengeStatus,
    LeaderboardType,
    LeaderboardPeriod,
    RewardType,
    RewardStatus,
    PointEventType,

    # Core Models
    UserProgress,
    Points,
    Level,
    Badge,
    UserBadge,
    Streak,
    Challenge,
    UserChallenge,
    Leaderboard,
    LeaderboardEntry,
    Reward,
    UserReward,
    Milestone,
    UserMilestone,
    GamificationEvent,
)

# Services
from .service import GamificationService, get_gamification_service
from .points import PointsService, get_points_for_activity, BASE_XP_VALUES
from .levels import LevelService, calculate_xp_for_level, LEVEL_TIERS
from .badges import BadgeService, BADGE_DEFINITIONS
from .streaks import StreakService, STREAK_MILESTONES
from .challenges import (
    ChallengeService,
    DAILY_CHALLENGE_TEMPLATES,
    WEEKLY_CHALLENGE_TEMPLATES,
    MONTHLY_CHALLENGE_TEMPLATES,
)
from .leaderboard import LeaderboardService
from .rewards import RewardService, REWARD_CATALOG

# Notifications
from .notifications import (
    send_level_up_notification,
    send_badge_earned_notification,
    send_streak_milestone_notification,
    send_streak_at_risk_notification,
    send_challenge_complete_notification,
    send_reward_redeemed_notification,
    send_daily_challenge_notification,
    send_leaderboard_rank_up_notification,
    send_xp_milestone_notification,
    get_celebration_animation,
)


__all__ = [
    # Main Service
    'GamificationService',
    'get_gamification_service',

    # Sub-services
    'PointsService',
    'LevelService',
    'BadgeService',
    'StreakService',
    'ChallengeService',
    'LeaderboardService',
    'RewardService',

    # Models - Enums
    'BadgeTier',
    'ChallengeType',
    'ChallengeStatus',
    'LeaderboardType',
    'LeaderboardPeriod',
    'RewardType',
    'RewardStatus',
    'PointEventType',

    # Models - Core
    'UserProgress',
    'Points',
    'Level',
    'Badge',
    'UserBadge',
    'Streak',
    'Challenge',
    'UserChallenge',
    'Leaderboard',
    'LeaderboardEntry',
    'Reward',
    'UserReward',
    'Milestone',
    'UserMilestone',
    'GamificationEvent',

    # Constants
    'BASE_XP_VALUES',
    'LEVEL_TIERS',
    'BADGE_DEFINITIONS',
    'STREAK_MILESTONES',
    'DAILY_CHALLENGE_TEMPLATES',
    'WEEKLY_CHALLENGE_TEMPLATES',
    'MONTHLY_CHALLENGE_TEMPLATES',
    'REWARD_CATALOG',

    # Notifications
    'send_level_up_notification',
    'send_badge_earned_notification',
    'send_streak_milestone_notification',
    'send_streak_at_risk_notification',
    'send_challenge_complete_notification',
    'send_reward_redeemed_notification',
    'send_daily_challenge_notification',
    'send_leaderboard_rank_up_notification',
    'send_xp_milestone_notification',
    'get_celebration_animation',

    # Utilities
    'get_points_for_activity',
    'calculate_xp_for_level',
]


# Version
__version__ = '1.0.0'
