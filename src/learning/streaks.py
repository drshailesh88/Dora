"""
Learning Streaks System

Tracks daily learning streaks to encourage consistent engagement.
"""

from datetime import date, timedelta
from typing import Optional
import logging

from .models import LearningStreak, LearningActivity

logger = logging.getLogger(__name__)


class StreakManager:
    """Manages learning streaks"""

    # Streak milestones
    MILESTONES = [7, 14, 30, 50, 100, 200, 365]

    # Freeze tokens
    FREEZE_TOKEN_GRANT_MILESTONES = [7, 30, 100]  # Grant tokens at these milestones
    MAX_FREEZE_TOKENS = 3

    def __init__(self):
        self.streaks: dict[str, LearningStreak] = {}

    def get_streak(self, user_id: str) -> LearningStreak:
        """
        Get user's streak

        Args:
            user_id: User ID

        Returns:
            LearningStreak
        """
        if user_id not in self.streaks:
            self.streaks[user_id] = LearningStreak(user_id=user_id)

        return self.streaks[user_id]

    def update_streak(self, user_id: str, activity_date: Optional[date] = None) -> LearningStreak:
        """
        Update user's streak based on activity

        Args:
            user_id: User ID
            activity_date: Date of activity (default: today)

        Returns:
            Updated LearningStreak
        """
        if activity_date is None:
            activity_date = date.today()

        streak = self.get_streak(user_id)

        # If this is the first activity
        if streak.last_activity_date is None:
            streak.current_streak = 1
            streak.longest_streak = 1
            streak.streak_start_date = activity_date
            streak.last_activity_date = activity_date
            streak.total_active_days = 1
            logger.info(f"Started streak for user {user_id}")
            return streak

        # If already logged activity today, no change
        if streak.last_activity_date == activity_date:
            return streak

        # Calculate days since last activity
        days_since_last = (activity_date - streak.last_activity_date).days

        if days_since_last == 1:
            # Consecutive day - increment streak
            streak.current_streak += 1
            streak.last_activity_date = activity_date
            streak.total_active_days += 1

            # Check for new longest streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

            # Check for milestone achievements
            self._check_milestones(streak)

            logger.info(
                f"Extended streak for user {user_id} to {streak.current_streak} days"
            )

        elif days_since_last > 1:
            # Streak broken - check for freeze token
            if self._can_use_freeze_token(streak, activity_date):
                # Use freeze token to save streak
                streak.freeze_tokens -= 1
                streak.freeze_used_dates.append(streak.last_activity_date + timedelta(days=1))
                streak.last_activity_date = activity_date
                streak.total_active_days += 1

                logger.info(
                    f"Used freeze token to save streak for user {user_id}. "
                    f"Remaining tokens: {streak.freeze_tokens}"
                )
            else:
                # Streak broken
                old_streak = streak.current_streak
                streak.current_streak = 1
                streak.streak_start_date = activity_date
                streak.last_activity_date = activity_date
                streak.total_active_days += 1

                logger.info(
                    f"Streak broken for user {user_id}. Old: {old_streak}, New: 1"
                )

        return streak

    def check_streak_status(self, user_id: str) -> dict:
        """
        Check current streak status

        Args:
            user_id: User ID

        Returns:
            Dict with streak status
        """
        streak = self.get_streak(user_id)

        if streak.last_activity_date is None:
            return {
                "current_streak": 0,
                "status": "new",
                "days_until_break": 1,
                "next_milestone": self.MILESTONES[0],
                "days_to_next_milestone": self.MILESTONES[0],
            }

        today = date.today()
        days_since_last = (today - streak.last_activity_date).days

        if days_since_last == 0:
            # Activity today
            status = "active"
            days_until_break = 1
        elif days_since_last == 1:
            # Need to log activity today to maintain streak
            status = "at_risk"
            days_until_break = 0
        else:
            # Streak broken (unless using freeze)
            if streak.freeze_tokens > 0:
                status = "can_freeze"
                days_until_break = 0
            else:
                status = "broken"
                days_until_break = 0

        # Next milestone
        next_milestone = None
        days_to_next_milestone = 0
        for milestone in self.MILESTONES:
            if streak.current_streak < milestone:
                next_milestone = milestone
                days_to_next_milestone = milestone - streak.current_streak
                break

        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "status": status,
            "days_until_break": days_until_break,
            "next_milestone": next_milestone,
            "days_to_next_milestone": days_to_next_milestone,
            "freeze_tokens": streak.freeze_tokens,
            "milestones_achieved": streak.milestones_achieved,
            "total_active_days": streak.total_active_days,
        }

    def use_freeze_token(self, user_id: str) -> bool:
        """
        Manually use a freeze token to protect streak

        Args:
            user_id: User ID

        Returns:
            True if successful, False if no tokens available
        """
        streak = self.get_streak(user_id)

        if streak.freeze_tokens <= 0:
            logger.warning(f"User {user_id} has no freeze tokens available")
            return False

        if streak.last_activity_date is None:
            logger.warning(f"User {user_id} has no streak to protect")
            return False

        yesterday = date.today() - timedelta(days=1)

        # Only allow using freeze if missed yesterday
        if streak.last_activity_date != yesterday:
            logger.warning(f"User {user_id} can only use freeze for yesterday")
            return False

        # Use freeze token
        streak.freeze_tokens -= 1
        streak.freeze_used_dates.append(date.today())
        streak.last_activity_date = date.today()

        logger.info(
            f"User {user_id} used freeze token. Remaining: {streak.freeze_tokens}"
        )

        return True

    def grant_freeze_token(self, user_id: str, reason: str = "") -> bool:
        """
        Grant a freeze token to user

        Args:
            user_id: User ID
            reason: Reason for grant

        Returns:
            True if granted
        """
        streak = self.get_streak(user_id)

        if streak.freeze_tokens >= self.MAX_FREEZE_TOKENS:
            logger.warning(f"User {user_id} already has max freeze tokens")
            return False

        streak.freeze_tokens += 1
        logger.info(f"Granted freeze token to user {user_id}. Reason: {reason}")

        return True

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """
        Get streak leaderboard (anonymized)

        Args:
            limit: Number of top streaks to return

        Returns:
            List of top streaks
        """
        # Sort by current streak
        sorted_streaks = sorted(
            self.streaks.values(),
            key=lambda x: x.current_streak,
            reverse=True
        )

        leaderboard = []
        for i, streak in enumerate(sorted_streaks[:limit], 1):
            leaderboard.append({
                "rank": i,
                "user_id": streak.user_id[:8] + "...",  # Anonymized
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "total_active_days": streak.total_active_days,
            })

        return leaderboard

    def get_user_rank(self, user_id: str) -> int:
        """
        Get user's rank in leaderboard

        Args:
            user_id: User ID

        Returns:
            Rank (1-based)
        """
        sorted_streaks = sorted(
            self.streaks.values(),
            key=lambda x: x.current_streak,
            reverse=True
        )

        for i, streak in enumerate(sorted_streaks, 1):
            if streak.user_id == user_id:
                return i

        return len(sorted_streaks) + 1

    def _check_milestones(self, streak: LearningStreak) -> None:
        """
        Check if new milestones were achieved

        Args:
            streak: LearningStreak
        """
        for milestone in self.MILESTONES:
            if (
                streak.current_streak >= milestone
                and milestone not in streak.milestones_achieved
            ):
                streak.milestones_achieved.append(milestone)
                logger.info(
                    f"User {streak.user_id} achieved {milestone}-day streak milestone!"
                )

                # Grant freeze token at certain milestones
                if milestone in self.FREEZE_TOKEN_GRANT_MILESTONES:
                    if streak.freeze_tokens < self.MAX_FREEZE_TOKENS:
                        streak.freeze_tokens += 1
                        logger.info(
                            f"Granted freeze token to user {streak.user_id} "
                            f"for {milestone}-day milestone"
                        )

    def _can_use_freeze_token(self, streak: LearningStreak, activity_date: date) -> bool:
        """
        Check if user can use freeze token

        Args:
            streak: LearningStreak
            activity_date: Current activity date

        Returns:
            True if can use freeze token
        """
        # Must have tokens
        if streak.freeze_tokens <= 0:
            return False

        # Can only freeze 1 day
        days_since_last = (activity_date - streak.last_activity_date).days
        if days_since_last > 2:
            return False

        # Haven't already used freeze for this date
        freeze_date = streak.last_activity_date + timedelta(days=1)
        if freeze_date in streak.freeze_used_dates:
            return False

        return True


# Global streak manager instance
_streak_manager = StreakManager()


def get_streak_manager() -> StreakManager:
    """Get the global streak manager instance"""
    return _streak_manager
