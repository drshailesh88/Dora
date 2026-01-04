"""
Streak System

Daily activity streaks with freeze tokens and recovery mechanisms.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from .models import Streak


# Streak milestones
STREAK_MILESTONES = [7, 30, 50, 100, 200, 365, 500, 1000]


class StreakService:
    """Service for managing daily streaks"""

    def __init__(self, storage):
        """
        Initialize streak service.

        Args:
            storage: Storage backend
        """
        self.storage = storage

    def record_activity(self, user_id: str) -> dict:
        """
        Record user activity and update streak.

        Args:
            user_id: User ID

        Returns:
            dict: Streak information including if it was updated
        """
        today = date.today()

        # Get or create streak
        streak = self._get_or_create_streak(user_id)

        # Check if already recorded today
        if streak.last_activity_date == today:
            return {
                'streak': streak,
                'updated': False,
                'message': 'Activity already recorded today',
            }

        # Check if streak continues
        yesterday = today - timedelta(days=1)

        if streak.last_activity_date == yesterday:
            # Streak continues
            streak.current_streak += 1
            streak.total_active_days += 1

        elif streak.last_activity_date is None or \
             (today - streak.last_activity_date).days == 0:
            # First activity or same day
            streak.current_streak = 1
            streak.total_active_days = max(streak.total_active_days, 1)
            streak.streak_start_date = today

        elif self._can_use_freeze(streak, yesterday):
            # Use freeze token to maintain streak
            streak.freeze_used_dates.append(yesterday)
            streak.freeze_tokens -= 1
            streak.current_streak += 1  # Streak continues
            streak.total_active_days += 1

        else:
            # Streak broken
            streak = self._break_streak(streak)
            streak.current_streak = 1
            streak.streak_start_date = today
            streak.total_active_days += 1
            streak.total_streak_breaks += 1

        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        # Update dates
        streak.last_activity_date = today
        streak.next_required_date = today + timedelta(days=1)

        # Update multiplier
        streak.current_multiplier = self._calculate_streak_multiplier(
            streak.current_streak
        )

        # Check for milestones
        newly_achieved_milestones = []
        for milestone in STREAK_MILESTONES:
            if (streak.current_streak == milestone and
                milestone not in streak.milestones_achieved):
                streak.milestones_achieved.append(milestone)
                newly_achieved_milestones.append(milestone)

        # Save streak
        streak.updated_at = datetime.utcnow()
        self.storage.save_streak(streak)

        # Award milestone badges/XP
        if newly_achieved_milestones:
            self._on_milestone_achieved(user_id, newly_achieved_milestones)

        return {
            'streak': streak,
            'updated': True,
            'milestones_achieved': newly_achieved_milestones,
            'message': f"Streak updated to {streak.current_streak} days!",
        }

    def get_streak_status(self, user_id: str) -> dict:
        """
        Get current streak status.

        Args:
            user_id: User ID

        Returns:
            dict: Streak status information
        """
        streak = self._get_or_create_streak(user_id)
        today = date.today()

        # Check if at risk
        is_at_risk = False
        if streak.last_activity_date:
            days_since_activity = (today - streak.last_activity_date).days
            is_at_risk = days_since_activity >= 1

        # Calculate next milestone
        next_milestone = None
        for milestone in STREAK_MILESTONES:
            if milestone > streak.current_streak:
                next_milestone = milestone
                break

        return {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'streak_start_date': streak.streak_start_date,
            'last_activity_date': streak.last_activity_date,
            'next_required_date': streak.next_required_date,
            'is_at_risk': is_at_risk,
            'freeze_tokens': streak.freeze_tokens,
            'freeze_available': streak.freeze_available,
            'total_active_days': streak.total_active_days,
            'milestones_achieved': sorted(streak.milestones_achieved),
            'next_milestone': next_milestone,
            'days_to_next_milestone': (
                next_milestone - streak.current_streak
                if next_milestone else None
            ),
            'current_multiplier': streak.current_multiplier,
        }

    def use_freeze_token(self, user_id: str, freeze_date: Optional[date] = None) -> dict:
        """
        Manually use a freeze token.

        Args:
            user_id: User ID
            freeze_date: Date to freeze (default yesterday)

        Returns:
            dict: Result of freeze operation
        """
        if freeze_date is None:
            freeze_date = date.today() - timedelta(days=1)

        streak = self._get_or_create_streak(user_id)

        # Check if can freeze
        if streak.freeze_tokens <= 0:
            return {
                'success': False,
                'message': 'No freeze tokens available',
            }

        if freeze_date in streak.freeze_used_dates:
            return {
                'success': False,
                'message': 'Freeze token already used for this date',
            }

        # Apply freeze
        streak.freeze_used_dates.append(freeze_date)
        streak.freeze_tokens -= 1
        streak.updated_at = datetime.utcnow()
        self.storage.save_streak(streak)

        return {
            'success': True,
            'message': f'Freeze token used for {freeze_date}',
            'freeze_tokens_remaining': streak.freeze_tokens,
        }

    def earn_freeze_token(self, user_id: str, count: int = 1) -> dict:
        """
        Award freeze tokens to user.

        Args:
            user_id: User ID
            count: Number of tokens to award

        Returns:
            dict: Result
        """
        streak = self._get_or_create_streak(user_id)

        streak.freeze_tokens += count
        streak.freeze_available += count
        streak.updated_at = datetime.utcnow()
        self.storage.save_streak(streak)

        return {
            'success': True,
            'message': f'Earned {count} freeze token(s)',
            'freeze_tokens': streak.freeze_tokens,
        }

    def recover_streak(self, user_id: str) -> dict:
        """
        Recover broken streak within 24 hours.

        Args:
            user_id: User ID

        Returns:
            dict: Recovery result
        """
        today = date.today()
        streak = self._get_or_create_streak(user_id)

        # Check if can recover (within 24 hours of break)
        if not streak.last_activity_date:
            return {
                'success': False,
                'message': 'No streak to recover',
            }

        days_since = (today - streak.last_activity_date).days

        if days_since != 2:  # Broke yesterday, trying to recover today
            return {
                'success': False,
                'message': 'Can only recover within 24 hours of break',
            }

        # Use a freeze token if available
        if streak.freeze_tokens > 0:
            yesterday = today - timedelta(days=1)
            return self.use_freeze_token(user_id, yesterday)
        else:
            return {
                'success': False,
                'message': 'No freeze tokens available for recovery',
            }

    def _get_or_create_streak(self, user_id: str) -> Streak:
        """Get or create user streak."""
        streak = self.storage.get_streak(user_id)

        if not streak:
            streak = Streak(user_id=user_id)
            self.storage.save_streak(streak)

        return streak

    def _can_use_freeze(self, streak: Streak, freeze_date: date) -> bool:
        """Check if can use freeze token."""
        return (
            streak.freeze_tokens > 0 and
            freeze_date not in streak.freeze_used_dates
        )

    def _break_streak(self, streak: Streak) -> Streak:
        """Handle streak break."""
        # Reset streak but keep stats
        streak.current_streak = 0
        streak.streak_start_date = None
        streak.current_multiplier = 1.0

        return streak

    def _calculate_streak_multiplier(self, streak_days: int) -> float:
        """
        Calculate XP multiplier based on streak length.

        Multipliers:
        - 1-6 days: 1.0x (no bonus)
        - 7-29 days: 1.1x (10% bonus)
        - 30-99 days: 1.25x (25% bonus)
        - 100-364 days: 1.5x (50% bonus)
        - 365+ days: 2.0x (100% bonus)
        """
        if streak_days >= 365:
            return 2.0
        elif streak_days >= 100:
            return 1.5
        elif streak_days >= 30:
            return 1.25
        elif streak_days >= 7:
            return 1.1
        else:
            return 1.0

    def _on_milestone_achieved(
        self,
        user_id: str,
        milestones: list[int]
    ):
        """Handle milestone achievements."""
        from .points import PointsService, PointEventType
        from .notifications import send_streak_milestone_notification

        points_service = PointsService(self.storage)

        for milestone in milestones:
            # Award XP based on milestone
            xp_rewards = {
                7: 100,
                30: 500,
                50: 1000,
                100: 2500,
                200: 5000,
                365: 10000,
                500: 25000,
                1000: 100000,
            }

            xp = xp_rewards.get(milestone, 0)

            if xp > 0:
                points_service.award_points(
                    user_id=user_id,
                    event_type=PointEventType.STREAK_BONUS,
                    event_description=f"Achieved {milestone}-day streak milestone",
                    custom_xp=xp,
                )

            # Send notification
            send_streak_milestone_notification(
                user_id, milestone, self.storage
            )

        # Check for badges
        from .badges import BadgeService
        badge_service = BadgeService(self.storage)
        badge_service.check_and_award_badges(user_id)
