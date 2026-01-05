"""
Badge System

50+ achievement badges across different categories.
"""

from datetime import datetime
from typing import Optional

from .models import Badge, BadgeTier, UserBadge, UserProgress


# Badge definitions organized by category
BADGE_DEFINITIONS = [
    # ============ STREAK BADGES (🔥) ============
    {
        'key': 'streak_7_days',
        'title': '7-Day Streak',
        'description': 'Maintain a 7-day learning streak',
        'icon': '🔥',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'streak',
        'criteria_value': 7,
        'criteria_description': 'Learn for 7 consecutive days',
        'category': 'streak',
        'xp_reward': 100,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
    },
    {
        'key': 'streak_30_days',
        'title': '30-Day Warrior',
        'description': 'Maintain a 30-day learning streak',
        'icon': '🔥',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'streak',
        'criteria_value': 30,
        'criteria_description': 'Learn for 30 consecutive days',
        'category': 'streak',
        'xp_reward': 500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
        'prerequisite_badges': ['streak_7_days'],
    },
    {
        'key': 'streak_100_days',
        'title': '100-Day Champion',
        'description': 'Maintain a 100-day learning streak',
        'icon': '🔥',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'streak',
        'criteria_value': 100,
        'criteria_description': 'Learn for 100 consecutive days',
        'category': 'streak',
        'xp_reward': 2000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 1,
        'prerequisite_badges': ['streak_30_days'],
    },
    {
        'key': 'streak_365_days',
        'title': 'Year of Excellence',
        'description': 'Maintain a 365-day learning streak',
        'icon': '🔥',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'streak',
        'criteria_value': 365,
        'criteria_description': 'Learn for 365 consecutive days',
        'category': 'streak',
        'xp_reward': 10000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 1,
        'prerequisite_badges': ['streak_100_days'],
    },
    {
        'key': 'streak_500_days',
        'title': 'Unstoppable Legend',
        'description': 'Maintain a 500-day learning streak',
        'icon': '🔥',
        'tier': BadgeTier.LEGENDARY,
        'criteria_type': 'streak',
        'criteria_value': 500,
        'criteria_description': 'Learn for 500 consecutive days',
        'category': 'streak',
        'xp_reward': 25000,
        'is_hidden': True,
        'is_rare': True,
        'required_level': 1,
        'prerequisite_badges': ['streak_365_days'],
    },

    # ============ QUERY BADGES (🎯) ============
    {
        'key': 'queries_100',
        'title': 'Curious Mind',
        'description': 'Ask 100 medical queries',
        'icon': '🎯',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'queries',
        'criteria_value': 100,
        'criteria_description': 'Ask 100 queries',
        'category': 'query',
        'xp_reward': 200,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
    },
    {
        'key': 'queries_500',
        'title': 'Knowledge Seeker',
        'description': 'Ask 500 medical queries',
        'icon': '🎯',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'queries',
        'criteria_value': 500,
        'criteria_description': 'Ask 500 queries',
        'category': 'query',
        'xp_reward': 1000,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 5,
        'prerequisite_badges': ['queries_100'],
    },
    {
        'key': 'queries_1000',
        'title': 'Inquisitive Expert',
        'description': 'Ask 1000 medical queries',
        'icon': '🎯',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'queries',
        'criteria_value': 1000,
        'criteria_description': 'Ask 1000 queries',
        'category': 'query',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
        'prerequisite_badges': ['queries_500'],
    },
    {
        'key': 'queries_5000',
        'title': 'Question Master',
        'description': 'Ask 5000 medical queries',
        'icon': '🎯',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'queries',
        'criteria_value': 5000,
        'criteria_description': 'Ask 5000 queries',
        'category': 'query',
        'xp_reward': 10000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 25,
        'prerequisite_badges': ['queries_1000'],
    },

    # ============ LEARNING BADGES (📚) ============
    {
        'key': 'quiz_master_10',
        'title': 'Quiz Novice',
        'description': 'Complete 10 quizzes',
        'icon': '📚',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'quizzes',
        'criteria_value': 10,
        'criteria_description': 'Complete 10 quizzes',
        'category': 'learning',
        'xp_reward': 150,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
    },
    {
        'key': 'quiz_master_50',
        'title': 'Quiz Enthusiast',
        'description': 'Complete 50 quizzes',
        'icon': '📚',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'quizzes',
        'criteria_value': 50,
        'criteria_description': 'Complete 50 quizzes',
        'category': 'learning',
        'xp_reward': 750,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 5,
        'prerequisite_badges': ['quiz_master_10'],
    },
    {
        'key': 'quiz_master_100',
        'title': 'Quiz Master',
        'description': 'Complete 100 quizzes',
        'icon': '📚',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'quizzes',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 quizzes',
        'category': 'learning',
        'xp_reward': 2000,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
        'prerequisite_badges': ['quiz_master_50'],
    },
    {
        'key': 'perfect_score_10',
        'title': 'Perfectionist',
        'description': 'Get 10 perfect quiz scores',
        'icon': '💯',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'quiz_perfects',
        'criteria_value': 10,
        'criteria_description': 'Score 100% on 10 quizzes',
        'category': 'learning',
        'xp_reward': 1500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'perfect_score_50',
        'title': 'Perfection Master',
        'description': 'Get 50 perfect quiz scores',
        'icon': '💯',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'quiz_perfects',
        'criteria_value': 50,
        'criteria_description': 'Score 100% on 50 quizzes',
        'category': 'learning',
        'xp_reward': 7500,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 25,
        'prerequisite_badges': ['perfect_score_10'],
    },

    # ============ COMPETITION BADGES (🏆) ============
    {
        'key': 'leaderboard_top_100',
        'title': 'Rising Star',
        'description': 'Reach top 100 in global leaderboard',
        'icon': '⭐',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'leaderboard_rank',
        'criteria_value': 100,
        'criteria_description': 'Rank in top 100',
        'category': 'competition',
        'xp_reward': 500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'leaderboard_top_50',
        'title': 'Elite Performer',
        'description': 'Reach top 50 in global leaderboard',
        'icon': '🌟',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'leaderboard_rank',
        'criteria_value': 50,
        'criteria_description': 'Rank in top 50',
        'category': 'competition',
        'xp_reward': 1500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 20,
        'prerequisite_badges': ['leaderboard_top_100'],
    },
    {
        'key': 'leaderboard_top_10',
        'title': 'Champion',
        'description': 'Reach top 10 in global leaderboard',
        'icon': '🏆',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'leaderboard_rank',
        'criteria_value': 10,
        'criteria_description': 'Rank in top 10',
        'category': 'competition',
        'xp_reward': 5000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 40,
        'prerequisite_badges': ['leaderboard_top_50'],
    },
    {
        'key': 'leaderboard_rank_1',
        'title': 'Number One',
        'description': 'Reach #1 in global leaderboard',
        'icon': '👑',
        'tier': BadgeTier.LEGENDARY,
        'criteria_type': 'leaderboard_rank',
        'criteria_value': 1,
        'criteria_description': 'Rank #1 globally',
        'category': 'competition',
        'xp_reward': 25000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 50,
        'prerequisite_badges': ['leaderboard_top_10'],
    },

    # ============ COMMUNITY BADGES (🤝) ============
    {
        'key': 'peer_help_10',
        'title': 'Helpful Colleague',
        'description': 'Help 10 peers with consultations',
        'icon': '🤝',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'peer_consultations',
        'criteria_value': 10,
        'criteria_description': 'Provide 10 peer consultations',
        'category': 'community',
        'xp_reward': 250,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 15,
    },
    {
        'key': 'peer_help_50',
        'title': 'Community Leader',
        'description': 'Help 50 peers with consultations',
        'icon': '🤝',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'peer_consultations',
        'criteria_value': 50,
        'criteria_description': 'Provide 50 peer consultations',
        'category': 'community',
        'xp_reward': 1500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
        'prerequisite_badges': ['peer_help_10'],
    },
    {
        'key': 'peer_help_100',
        'title': 'Mentor',
        'description': 'Help 100 peers with consultations',
        'icon': '🤝',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'peer_consultations',
        'criteria_value': 100,
        'criteria_description': 'Provide 100 peer consultations',
        'category': 'community',
        'xp_reward': 5000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 40,
        'prerequisite_badges': ['peer_help_50'],
    },
    {
        'key': 'case_contributor_10',
        'title': 'Case Contributor',
        'description': 'Contribute 10 clinical cases',
        'icon': '📝',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'cases',
        'criteria_value': 10,
        'criteria_description': 'Contribute 10 cases',
        'category': 'community',
        'xp_reward': 500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 20,
    },
    {
        'key': 'case_contributor_50',
        'title': 'Case Expert',
        'description': 'Contribute 50 clinical cases',
        'icon': '📝',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'cases',
        'criteria_value': 50,
        'criteria_description': 'Contribute 50 cases',
        'category': 'community',
        'xp_reward': 3000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 35,
        'prerequisite_badges': ['case_contributor_10'],
    },

    # ============ SPECIALTY BADGES (💊) ============
    {
        'key': 'cardiology_expert',
        'title': 'Cardiology Expert',
        'description': 'Master cardiology topics',
        'icon': '❤️',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 cardiology queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'neurology_expert',
        'title': 'Neurology Expert',
        'description': 'Master neurology topics',
        'icon': '🧠',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 neurology queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'pediatrics_expert',
        'title': 'Pediatrics Expert',
        'description': 'Master pediatrics topics',
        'icon': '👶',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 pediatrics queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'surgery_expert',
        'title': 'Surgery Expert',
        'description': 'Master surgery topics',
        'icon': '🔪',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 surgery queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'emergency_expert',
        'title': 'Emergency Medicine Expert',
        'description': 'Master emergency medicine topics',
        'icon': '🚨',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 emergency medicine queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'oncology_expert',
        'title': 'Oncology Expert',
        'description': 'Master oncology topics',
        'icon': '🎗️',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'specialty_mastery',
        'criteria_value': 100,
        'criteria_description': 'Complete 100 oncology queries/quizzes',
        'category': 'specialty',
        'xp_reward': 2500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'multidisciplinary_master',
        'title': 'Multidisciplinary Master',
        'description': 'Master 5+ specialties',
        'icon': '🌈',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'specialty_count',
        'criteria_value': 5,
        'criteria_description': 'Master 5 different specialties',
        'category': 'specialty',
        'xp_reward': 10000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 50,
    },

    # ============ MILESTONE BADGES (🌟) ============
    {
        'key': 'first_query',
        'title': 'First Step',
        'description': 'Ask your first query',
        'icon': '🌟',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'queries',
        'criteria_value': 1,
        'criteria_description': 'Ask 1 query',
        'category': 'milestone',
        'xp_reward': 10,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
    },
    {
        'key': 'first_quiz',
        'title': 'Quiz Beginner',
        'description': 'Complete your first quiz',
        'icon': '🌟',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'quizzes',
        'criteria_value': 1,
        'criteria_description': 'Complete 1 quiz',
        'category': 'milestone',
        'xp_reward': 25,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 1,
    },
    {
        'key': 'level_10',
        'title': 'Level 10 Milestone',
        'description': 'Reach level 10',
        'icon': '🎖️',
        'tier': BadgeTier.BRONZE,
        'criteria_type': 'level',
        'criteria_value': 10,
        'criteria_description': 'Reach level 10',
        'category': 'milestone',
        'xp_reward': 500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'level_25',
        'title': 'Level 25 Milestone',
        'description': 'Reach level 25',
        'icon': '🎖️',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'level',
        'criteria_value': 25,
        'criteria_description': 'Reach level 25',
        'category': 'milestone',
        'xp_reward': 1500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 25,
    },
    {
        'key': 'level_50',
        'title': 'Level 50 Milestone',
        'description': 'Reach level 50',
        'icon': '🎖️',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'level',
        'criteria_value': 50,
        'criteria_description': 'Reach level 50',
        'category': 'milestone',
        'xp_reward': 5000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 50,
    },
    {
        'key': 'level_100',
        'title': 'Master Level',
        'description': 'Reach the maximum level 100',
        'icon': '👑',
        'tier': BadgeTier.LEGENDARY,
        'criteria_type': 'level',
        'criteria_value': 100,
        'criteria_description': 'Reach level 100',
        'category': 'milestone',
        'xp_reward': 50000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 100,
    },

    # ============ SPECIAL/RARE BADGES (💎) ============
    {
        'key': 'early_adopter',
        'title': 'Early Adopter',
        'description': 'Join Dora in the first month',
        'icon': '🚀',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'special',
        'criteria_value': 1,
        'criteria_description': 'Join during launch month',
        'category': 'special',
        'xp_reward': 1000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 1,
    },
    {
        'key': 'night_owl',
        'title': 'Night Owl',
        'description': 'Learn between midnight and 5 AM (50 times)',
        'icon': '🦉',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'time_of_day',
        'criteria_value': 50,
        'criteria_description': 'Learn 50 times at night (12 AM - 5 AM)',
        'category': 'special',
        'xp_reward': 500,
        'is_hidden': True,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'weekend_warrior',
        'title': 'Weekend Warrior',
        'description': 'Learn on weekends (20 consecutive weekends)',
        'icon': '⚔️',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'weekend',
        'criteria_value': 20,
        'criteria_description': 'Learn on 20 consecutive weekends',
        'category': 'special',
        'xp_reward': 1500,
        'is_hidden': True,
        'is_rare': False,
        'required_level': 15,
    },
    {
        'key': 'speed_learner',
        'title': 'Speed Learner',
        'description': 'Complete 10 quizzes in a single day',
        'icon': '⚡',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'daily_quizzes',
        'criteria_value': 10,
        'criteria_description': 'Complete 10 quizzes in one day',
        'category': 'special',
        'xp_reward': 1000,
        'is_hidden': True,
        'is_rare': False,
        'required_level': 20,
    },
    {
        'key': 'referral_champion',
        'title': 'Referral Champion',
        'description': 'Refer 10 doctors to Dora',
        'icon': '🎁',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'referrals',
        'criteria_value': 10,
        'criteria_description': 'Refer 10 new users',
        'category': 'special',
        'xp_reward': 5000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 15,
    },
    {
        'key': 'knowledge_explorer',
        'title': 'Knowledge Explorer',
        'description': 'Read 100 articles',
        'icon': '📖',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'articles_read',
        'criteria_value': 100,
        'criteria_description': 'Read 100 articles',
        'category': 'learning',
        'xp_reward': 750,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'video_enthusiast',
        'title': 'Video Enthusiast',
        'description': 'Watch 50 educational videos',
        'icon': '📹',
        'tier': BadgeTier.SILVER,
        'criteria_type': 'videos_watched',
        'criteria_value': 50,
        'criteria_description': 'Watch 50 videos',
        'category': 'learning',
        'xp_reward': 500,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 10,
    },
    {
        'key': 'challenge_champion',
        'title': 'Challenge Champion',
        'description': 'Complete 50 daily/weekly challenges',
        'icon': '🏅',
        'tier': BadgeTier.GOLD,
        'criteria_type': 'challenges',
        'criteria_value': 50,
        'criteria_description': 'Complete 50 challenges',
        'category': 'competition',
        'xp_reward': 3000,
        'is_hidden': False,
        'is_rare': False,
        'required_level': 30,
    },
    {
        'key': 'dedication_master',
        'title': 'Dedication Master',
        'description': 'Active for 365 total days (non-consecutive)',
        'icon': '💪',
        'tier': BadgeTier.PLATINUM,
        'criteria_type': 'active_days',
        'criteria_value': 365,
        'criteria_description': 'Active for 365 days total',
        'category': 'milestone',
        'xp_reward': 10000,
        'is_hidden': False,
        'is_rare': True,
        'required_level': 40,
    },
]


class BadgeService:
    """Service for managing achievement badges"""

    def __init__(self, storage):
        """
        Initialize badge service.

        Args:
            storage: Storage backend
        """
        self.storage = storage
        self._initialize_badges()

    def _initialize_badges(self):
        """Initialize badge definitions in storage."""
        for badge_def in BADGE_DEFINITIONS:
            # Check if badge exists
            existing = self.storage.get_badge_by_key(badge_def['key'])
            if not existing:
                # Create new badge
                badge = Badge(**badge_def)
                self.storage.save_badge(badge)

    def get_all_badges(self) -> list[Badge]:
        """Get all badge definitions."""
        return self.storage.get_all_badges()

    def get_badges_by_category(self, category: str) -> list[Badge]:
        """Get badges in a category."""
        return self.storage.get_badges_by_category(category)

    def get_user_badges(self, user_id: str) -> list[UserBadge]:
        """Get all badges earned by a user."""
        return self.storage.get_user_badges(user_id)

    def get_user_progress_for_badge(
        self,
        user_id: str,
        badge_key: str,
    ) -> dict:
        """
        Get user's progress towards a badge.

        Args:
            user_id: User ID
            badge_key: Badge key

        Returns:
            dict: Progress information
        """
        badge = self.storage.get_badge_by_key(badge_key)
        if not badge:
            return None

        # Get current value based on criteria type
        current_value = self._get_criteria_value(user_id, badge.criteria_type)

        # Check if already earned
        earned_badge = self.storage.get_user_badge_by_key(user_id, badge_key)

        return {
            'badge': badge,
            'current_value': current_value,
            'target_value': badge.criteria_value,
            'progress_percentage': min(
                round((current_value / badge.criteria_value * 100), 2)
                if badge.criteria_value > 0 else 0,
                100
            ),
            'is_earned': earned_badge is not None,
            'earned_at': earned_badge.earned_at if earned_badge else None,
        }

    def check_and_award_badges(self, user_id: str) -> list[UserBadge]:
        """
        Check if user has earned any new badges and award them.

        Args:
            user_id: User ID

        Returns:
            list[UserBadge]: List of newly awarded badges
        """
        newly_awarded = []

        # Get all badges
        all_badges = self.get_all_badges()

        for badge in all_badges:
            # Skip if already earned
            if self.storage.get_user_badge_by_key(user_id, badge.key):
                continue

            # Check if user meets criteria
            if self._check_badge_criteria(user_id, badge):
                # Award badge
                user_badge = self._award_badge(user_id, badge)
                newly_awarded.append(user_badge)

        return newly_awarded

    def _check_badge_criteria(self, user_id: str, badge: Badge) -> bool:
        """Check if user meets badge criteria."""
        # Check level requirement
        progress = self.storage.get_user_progress(user_id)
        if not progress or progress.current_level < badge.required_level:
            return False

        # Check prerequisite badges
        for prereq_key in badge.prerequisite_badges:
            if not self.storage.get_user_badge_by_key(user_id, prereq_key):
                return False

        # Check criteria value
        current_value = self._get_criteria_value(user_id, badge.criteria_type)
        return current_value >= badge.criteria_value

    def _get_criteria_value(self, user_id: str, criteria_type: str) -> int:
        """Get current value for a criteria type."""
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return 0

        # Map criteria types to progress fields
        criteria_map = {
            'streak': lambda: self.storage.get_streak(user_id).current_streak
                              if self.storage.get_streak(user_id) else 0,
            'queries': lambda: progress.total_queries,
            'quizzes': lambda: progress.total_quizzes,
            'quiz_perfects': lambda: self.storage.count_perfect_quizzes(user_id),
            'leaderboard_rank': lambda: progress.global_rank or 99999,
            'peer_consultations': lambda: progress.total_peer_consultations,
            'cases': lambda: progress.total_cases_contributed,
            'specialty_mastery': lambda: self._get_specialty_query_count(user_id),
            'specialty_count': lambda: self._count_mastered_specialties(user_id),
            'level': lambda: progress.current_level,
            'referrals': lambda: self.storage.count_referrals(user_id),
            'articles_read': lambda: self.storage.count_articles_read(user_id),
            'videos_watched': lambda: self.storage.count_videos_watched(user_id),
            'challenges': lambda: self.storage.count_completed_challenges(user_id),
            'active_days': lambda: progress.total_active_days,
        }

        getter = criteria_map.get(criteria_type)
        return getter() if getter else 0

    def _get_specialty_query_count(self, user_id: str) -> int:
        """
        Get query count for a specific specialty.

        Uses personalization storage to count queries in detected specialties.
        For specialty mastery badges, this counts queries in the user's primary specialty.

        Args:
            user_id: User ID

        Returns:
            Count of queries in primary specialty
        """
        try:
            from src.personalization import PersonalizationStorage

            storage = PersonalizationStorage()
            profile = storage.get_profile(user_id)

            if not profile:
                return 0

            # Get the primary specialty from profile
            if not profile.primary_specialty:
                return 0

            # Count queries in this specialty
            return storage.count_queries_by_specialty(user_id, profile.primary_specialty)

        except Exception:
            # If personalization not available, return 0
            return 0

    def _count_mastered_specialties(self, user_id: str) -> int:
        """
        Count number of specialties where user has achieved mastery.

        Mastery is defined as 100+ queries in a specialty.

        Args:
            user_id: User ID

        Returns:
            Count of mastered specialties
        """
        try:
            from src.personalization import PersonalizationStorage

            storage = PersonalizationStorage()
            specialty_counts = storage.get_specialty_query_counts(user_id)

            # Count specialties with 100+ queries
            mastered = sum(1 for count in specialty_counts.values() if count >= 100)
            return mastered

        except Exception:
            # If personalization not available, return 0
            return 0

    def _award_badge(self, user_id: str, badge: Badge) -> UserBadge:
        """Award a badge to a user."""
        # Get current value
        current_value = self._get_criteria_value(user_id, badge.criteria_type)

        # Create user badge
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            badge_key=badge.key,
            badge_title=badge.title,
            badge_icon=badge.icon,
            badge_tier=badge.tier,
            badge_category=badge.category,
            progress_value=current_value,
            xp_earned=badge.xp_reward,
        )

        # Save badge
        self.storage.save_user_badge(user_badge)

        # Award XP
        from .points import PointsService, PointEventType

        points_service = PointsService(self.storage)
        points_service.award_points(
            user_id=user_id,
            event_type=PointEventType.BADGE_EARNED,
            event_description=f"Earned badge: {badge.title}",
            reference_type='badge',
            reference_id=badge.id,
            custom_xp=badge.xp_reward,
        )

        # Update user progress
        progress = self.storage.get_user_progress(user_id)
        progress.total_badges += 1
        if badge.is_rare:
            progress.rare_badges += 1
        self.storage.save_user_progress(progress)

        # Send notification
        from .notifications import send_badge_earned_notification
        send_badge_earned_notification(user_id, user_badge, self.storage)

        return user_badge
