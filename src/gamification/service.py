"""
Gamification Service

Main service that orchestrates all gamification components.
"""

from datetime import date, datetime
from typing import Optional

from .badges import BadgeService
from .challenges import ChallengeService
from .leaderboard import LeaderboardService
from .levels import LevelService
from .models import (
    BadgeTier,
    ChallengeType,
    LeaderboardType,
    LeaderboardPeriod,
    PointEventType,
)
from .points import PointsService
from .rewards import RewardService
from .streaks import StreakService


class GamificationService:
    """
    Main gamification service that coordinates all gamification features.
    """

    def __init__(self, storage):
        """
        Initialize gamification service.

        Args:
            storage: Storage backend (database, cache, etc.)
        """
        self.storage = storage

        # Initialize sub-services
        self.points = PointsService(storage)
        self.levels = LevelService(storage)
        self.badges = BadgeService(storage)
        self.streaks = StreakService(storage)
        self.challenges = ChallengeService(storage)
        self.leaderboard = LeaderboardService(storage)
        self.rewards = RewardService(storage)

    # ========== User Profile ==========

    def get_user_profile(self, user_id: str) -> dict:
        """
        Get complete gamification profile for a user.

        Args:
            user_id: User ID

        Returns:
            dict: Complete gamification profile
        """
        # Get progress
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            # Initialize new user
            progress = self._initialize_user(user_id)

        # Get level info
        level_info = self.levels.get_level_progress(progress.total_xp)

        # Get streak status
        streak_status = self.streaks.get_streak_status(user_id)

        # Get badges
        user_badges = self.badges.get_user_badges(user_id)
        showcased_badges = [
            b for b in user_badges
            if b.is_showcased
        ][:3]  # Max 3 showcased

        # Get active challenges
        daily_challenges = self.challenges.get_daily_challenges(user_id)
        weekly_challenges = self.challenges.get_weekly_challenges(user_id)

        # Get leaderboard rank
        global_rank = self.leaderboard.get_user_rank(
            user_id,
            LeaderboardType.GLOBAL,
            LeaderboardPeriod.ALL_TIME,
        )

        return {
            'user_id': user_id,
            'level': level_info,
            'xp': {
                'total': progress.total_xp,
                'current_level': progress.xp_current_level,
                'to_next_level': progress.xp_to_next_level,
            },
            'streak': streak_status,
            'badges': {
                'total': progress.total_badges,
                'rare': progress.rare_badges,
                'showcased': showcased_badges,
            },
            'rank': {
                'global': progress.global_rank,
                'specialty': progress.specialty_rank,
                'percentile': progress.percentile,
            },
            'challenges': {
                'daily': daily_challenges,
                'weekly': weekly_challenges,
            },
            'stats': {
                'total_queries': progress.total_queries,
                'total_quizzes': progress.total_quizzes,
                'total_cases': progress.total_cases_contributed,
                'total_consultations': progress.total_peer_consultations,
                'total_active_days': progress.total_active_days,
            },
        }

    def get_dashboard_summary(self, user_id: str) -> dict:
        """
        Get gamification dashboard summary.

        Args:
            user_id: User ID

        Returns:
            dict: Dashboard summary
        """
        profile = self.get_user_profile(user_id)

        # Get recent points
        recent_xp = self.points.get_daily_xp_summary(user_id, days=7)

        # Get available rewards
        available_rewards = self.rewards.get_available_rewards(user_id)
        affordable_rewards = [r for r in available_rewards if r['can_afford']]

        # Get badge progress
        progress_to_next_badges = self._get_next_badges_progress(user_id, limit=3)

        return {
            'profile': profile,
            'recent_xp': recent_xp,
            'available_rewards_count': len(affordable_rewards),
            'next_badges': progress_to_next_badges,
        }

    # ========== Activity Tracking ==========

    def record_activity(
        self,
        user_id: str,
        activity_type: str,
        **kwargs,
    ) -> dict:
        """
        Record user activity and update gamification state.

        Args:
            user_id: User ID
            activity_type: Type of activity (query, quiz, etc.)
            **kwargs: Additional activity data

        Returns:
            dict: Updated gamification state
        """
        # Record streak
        streak_result = self.streaks.record_activity(user_id)

        # Award points
        from .points import get_points_for_activity

        base_xp = get_points_for_activity(activity_type, **kwargs)
        event_type = self._map_activity_to_event_type(activity_type)

        if base_xp > 0 and event_type:
            points = self.points.award_points(
                user_id=user_id,
                event_type=event_type,
                event_description=f"{activity_type} activity",
                custom_xp=base_xp,
            )
        else:
            points = None

        # Check for badges
        new_badges = self.badges.check_and_award_badges(user_id)

        # Update challenges
        daily_challenges = self.challenges.get_daily_challenges(user_id)

        # Update leaderboard
        self.leaderboard.update_user_rankings(user_id)

        return {
            'streak': streak_result,
            'xp_earned': points.xp_amount if points else 0,
            'new_badges': new_badges,
            'challenges_updated': len(daily_challenges),
        }

    # ========== Points & Levels ==========

    def award_custom_points(
        self,
        user_id: str,
        xp_amount: int,
        reason: str,
    ) -> dict:
        """
        Award custom XP points to a user.

        Args:
            user_id: User ID
            xp_amount: Amount of XP to award
            reason: Reason for awarding points

        Returns:
            dict: Points information
        """
        points = self.points.award_points(
            user_id=user_id,
            event_type=PointEventType.BADGE_EARNED,  # Generic type
            event_description=reason,
            custom_xp=xp_amount,
        )

        # Check for level up
        progress = self.storage.get_user_progress(user_id)
        level_info = self.levels.get_level_progress(progress.total_xp)

        return {
            'xp_earned': points.xp_amount,
            'total_xp': points.total_xp_after,
            'level': level_info,
        }

    # ========== Streaks ==========

    def use_streak_freeze(self, user_id: str) -> dict:
        """Use a streak freeze token."""
        return self.streaks.use_freeze_token(user_id)

    def earn_streak_freeze(self, user_id: str, count: int = 1) -> dict:
        """Award streak freeze tokens."""
        return self.streaks.earn_freeze_token(user_id, count)

    # ========== Badges ==========

    def get_all_badges_progress(self, user_id: str) -> list[dict]:
        """
        Get progress towards all badges.

        Args:
            user_id: User ID

        Returns:
            list[dict]: Badge progress for all badges
        """
        all_badges = self.badges.get_all_badges()
        progress_list = []

        for badge in all_badges:
            progress = self.badges.get_user_progress_for_badge(
                user_id,
                badge.key,
            )
            if progress:
                progress_list.append(progress)

        # Sort by progress percentage
        progress_list.sort(
            key=lambda x: (
                x['is_earned'],
                -x['progress_percentage']
            )
        )

        return progress_list

    def showcase_badge(
        self,
        user_id: str,
        badge_id: str,
        showcase: bool = True,
    ) -> dict:
        """
        Toggle badge showcase on profile.

        Args:
            user_id: User ID
            badge_id: Badge ID
            showcase: Whether to showcase

        Returns:
            dict: Result
        """
        user_badge = self.storage.get_user_badge(user_id, badge_id)

        if not user_badge:
            return {
                'success': False,
                'message': 'Badge not found',
            }

        user_badge.is_showcased = showcase
        self.storage.save_user_badge(user_badge)

        return {
            'success': True,
            'message': f"Badge {'showcased' if showcase else 'hidden'}",
        }

    # ========== Challenges ==========

    def get_all_challenges(self, user_id: str) -> dict:
        """Get all active challenges for a user."""
        return {
            'daily': self.challenges.get_daily_challenges(user_id),
            'weekly': self.challenges.get_weekly_challenges(user_id),
            'monthly': self.challenges.get_monthly_challenges(user_id),
        }

    def complete_challenge(
        self,
        user_id: str,
        challenge_id: str,
    ) -> dict:
        """Complete a challenge."""
        return self.challenges.complete_challenge(user_id, challenge_id)

    # ========== Leaderboards ==========

    def get_all_leaderboards(self, user_id: str) -> dict:
        """Get all relevant leaderboards for a user."""
        user = self.storage.get_user(user_id)

        leaderboards = {
            'global_weekly': self.leaderboard.get_leaderboard(
                LeaderboardType.GLOBAL,
                LeaderboardPeriod.WEEKLY,
            ),
            'global_all_time': self.leaderboard.get_leaderboard(
                LeaderboardType.GLOBAL,
                LeaderboardPeriod.ALL_TIME,
            ),
            'friends': self.leaderboard.get_friends_leaderboard(user_id),
        }

        # Add specialty leaderboard if user has specialty
        if user and user.specialty:
            leaderboards['specialty'] = self.leaderboard.get_leaderboard(
                LeaderboardType.SPECIALTY,
                LeaderboardPeriod.ALL_TIME,
                specialty=user.specialty,
            )

        return leaderboards

    # ========== Rewards ==========

    def get_rewards_catalog(self, user_id: str) -> dict:
        """Get rewards catalog with user's affordability."""
        available_rewards = self.rewards.get_available_rewards(user_id)

        # Group by type
        by_type = {}
        for reward_info in available_rewards:
            reward_type = reward_info['reward'].reward_type
            if reward_type not in by_type:
                by_type[reward_type] = []
            by_type[reward_type].append(reward_info)

        return {
            'all_rewards': available_rewards,
            'by_type': by_type,
            'affordable_count': len([
                r for r in available_rewards
                if r['can_afford']
            ]),
        }

    def redeem_reward(self, user_id: str, reward_id: str) -> dict:
        """Redeem a reward."""
        return self.rewards.redeem_reward(user_id, reward_id)

    def get_user_rewards(self, user_id: str) -> list:
        """Get user's redeemed rewards."""
        return self.rewards.get_user_rewards(user_id)

    # ========== Helper Methods ==========

    def _initialize_user(self, user_id: str):
        """Initialize gamification for a new user."""
        from .models import UserProgress

        progress = UserProgress(user_id=user_id)
        self.storage.save_user_progress(progress)

        # Record first activity for streak
        self.streaks.record_activity(user_id)

        return progress

    def _map_activity_to_event_type(self, activity_type: str) -> Optional[PointEventType]:
        """Map activity type to point event type."""
        mapping = {
            'query': PointEventType.QUERY,
            'query_deep': PointEventType.QUERY_DEEP,
            'quiz': PointEventType.QUIZ_COMPLETE,
            'quiz_perfect': PointEventType.QUIZ_PERFECT,
            'case': PointEventType.CASE_CONTRIBUTION,
            'consultation': PointEventType.PEER_CONSULTATION,
            'login': PointEventType.DAILY_LOGIN,
            'article': PointEventType.ARTICLE_READ,
            'video': PointEventType.VIDEO_WATCHED,
            'rating': PointEventType.CONTENT_RATED,
        }

        return mapping.get(activity_type)

    def _get_next_badges_progress(self, user_id: str, limit: int = 3) -> list[dict]:
        """Get progress towards next achievable badges."""
        all_progress = self.get_all_badges_progress(user_id)

        # Filter to unearned badges
        unearned = [p for p in all_progress if not p['is_earned']]

        # Sort by progress (closest to achieving)
        unearned.sort(key=lambda x: -x['progress_percentage'])

        return unearned[:limit]


# Singleton instance (optional)
_gamification_service = None


def get_gamification_service(storage=None):
    """
    Get gamification service singleton.

    Args:
        storage: Storage backend (required on first call)

    Returns:
        GamificationService: Service instance
    """
    global _gamification_service

    if _gamification_service is None:
        if storage is None:
            raise ValueError("Storage required for first initialization")
        _gamification_service = GamificationService(storage)

    return _gamification_service
