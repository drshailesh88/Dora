"""
Points System

XP (experience points) system for rewarding user activities.
"""

from datetime import datetime, timedelta
from typing import Optional

from .models import (
    Points,
    PointEventType,
    UserProgress,
)


# Base XP values for different activities
BASE_XP_VALUES = {
    PointEventType.QUERY: 5,
    PointEventType.QUERY_DEEP: 10,
    PointEventType.QUIZ_COMPLETE: 25,
    PointEventType.QUIZ_PERFECT: 50,
    PointEventType.CASE_CONTRIBUTION: 100,
    PointEventType.PEER_CONSULTATION: 50,
    PointEventType.DAILY_LOGIN: 10,
    PointEventType.STREAK_BONUS: 0,  # Calculated based on streak
    PointEventType.BADGE_EARNED: 0,  # Variable based on badge
    PointEventType.CHALLENGE_COMPLETE: 0,  # Variable based on challenge
    PointEventType.REFERRAL: 200,
    PointEventType.CONTENT_RATED: 5,
    PointEventType.ARTICLE_READ: 5,
    PointEventType.VIDEO_WATCHED: 10,
}


class PointsService:
    """Service for managing XP points"""

    def __init__(self, storage):
        """
        Initialize points service.

        Args:
            storage: Storage backend (database, cache, etc.)
        """
        self.storage = storage

    def award_points(
        self,
        user_id: str,
        event_type: PointEventType,
        event_description: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        custom_xp: Optional[int] = None,
    ) -> Points:
        """
        Award points to a user for an activity.

        Args:
            user_id: User ID
            event_type: Type of point-earning event
            event_description: Description of what earned the points
            reference_type: Type of related entity (optional)
            reference_id: ID of related entity (optional)
            custom_xp: Custom XP amount (overrides base value)

        Returns:
            Points: Created points record
        """
        # Get user's current progress
        progress = self._get_user_progress(user_id)

        # Calculate base XP
        base_xp = custom_xp if custom_xp is not None else BASE_XP_VALUES.get(event_type, 0)

        # Calculate multipliers
        streak_multiplier = self._calculate_streak_multiplier(user_id)
        level_multiplier = self._calculate_level_multiplier(progress.current_level)
        event_multiplier = self._get_event_multiplier()

        # Calculate final XP
        total_multiplier = streak_multiplier * level_multiplier * event_multiplier
        final_xp = int(base_xp * total_multiplier)

        # Create points record
        points = Points(
            user_id=user_id,
            xp_amount=final_xp,
            event_type=event_type,
            event_description=event_description,
            base_xp=base_xp,
            streak_multiplier=streak_multiplier,
            level_multiplier=level_multiplier,
            event_multiplier=event_multiplier,
            reference_type=reference_type,
            reference_id=reference_id,
            level_at_earn=progress.current_level,
            total_xp_after=progress.total_xp + final_xp,
        )

        # Save points
        self.storage.save_points(points)

        # Update user progress
        self._update_user_progress(user_id, final_xp, event_type)

        return points

    def get_user_points_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Points]:
        """
        Get user's points history.

        Args:
            user_id: User ID
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            list[Points]: Points history
        """
        return self.storage.get_points_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def get_daily_xp_summary(
        self,
        user_id: str,
        days: int = 30,
    ) -> dict:
        """
        Get daily XP summary for the past N days.

        Args:
            user_id: User ID
            days: Number of days to include

        Returns:
            dict: Daily XP summary with chart data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        points_history = self.storage.get_points_in_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Group by date
        daily_xp = {}
        for point in points_history:
            date_key = point.earned_at.date().isoformat()
            if date_key not in daily_xp:
                daily_xp[date_key] = {
                    'date': date_key,
                    'total_xp': 0,
                    'events': [],
                }
            daily_xp[date_key]['total_xp'] += point.xp_amount
            daily_xp[date_key]['events'].append({
                'type': point.event_type,
                'xp': point.xp_amount,
                'description': point.event_description,
            })

        # Sort by date
        sorted_daily_xp = sorted(
            daily_xp.values(),
            key=lambda x: x['date'],
        )

        # Calculate stats
        total_xp = sum(day['total_xp'] for day in sorted_daily_xp)
        avg_xp_per_day = total_xp / days if days > 0 else 0
        max_day = max(sorted_daily_xp, key=lambda x: x['total_xp']) if sorted_daily_xp else None

        return {
            'daily_data': sorted_daily_xp,
            'total_xp': total_xp,
            'avg_xp_per_day': round(avg_xp_per_day, 2),
            'max_day': max_day,
        }

    def get_xp_breakdown(self, user_id: str) -> dict:
        """
        Get breakdown of XP by event type.

        Args:
            user_id: User ID

        Returns:
            dict: XP breakdown by event type
        """
        points_history = self.storage.get_all_points(user_id)

        breakdown = {}
        for point in points_history:
            event_type = point.event_type
            if event_type not in breakdown:
                breakdown[event_type] = {
                    'event_type': event_type,
                    'total_xp': 0,
                    'count': 0,
                    'avg_xp': 0,
                }
            breakdown[event_type]['total_xp'] += point.xp_amount
            breakdown[event_type]['count'] += 1

        # Calculate averages
        for event_type in breakdown:
            count = breakdown[event_type]['count']
            total = breakdown[event_type]['total_xp']
            breakdown[event_type]['avg_xp'] = round(total / count, 2) if count > 0 else 0

        # Sort by total XP
        sorted_breakdown = sorted(
            breakdown.values(),
            key=lambda x: x['total_xp'],
            reverse=True,
        )

        return {
            'breakdown': sorted_breakdown,
            'total_events': sum(b['count'] for b in breakdown.values()),
            'total_xp': sum(b['total_xp'] for b in breakdown.values()),
        }

    def calculate_next_level_progress(self, user_id: str) -> dict:
        """
        Calculate progress towards next level.

        Args:
            user_id: User ID

        Returns:
            dict: Level progress information
        """
        progress = self._get_user_progress(user_id)

        return {
            'current_level': progress.current_level,
            'current_xp': progress.total_xp,
            'xp_current_level': progress.xp_current_level,
            'xp_to_next_level': progress.xp_to_next_level,
            'progress_percentage': round(
                (progress.xp_current_level / progress.xp_to_next_level * 100)
                if progress.xp_to_next_level > 0 else 0,
                2
            ),
        }

    def _calculate_streak_multiplier(self, user_id: str) -> float:
        """
        Calculate XP multiplier based on current streak.

        Multipliers:
        - 1-6 days: 1.0x (no bonus)
        - 7-29 days: 1.1x (10% bonus)
        - 30-99 days: 1.25x (25% bonus)
        - 100-364 days: 1.5x (50% bonus)
        - 365+ days: 2.0x (100% bonus)

        Args:
            user_id: User ID

        Returns:
            float: Streak multiplier
        """
        streak = self.storage.get_streak(user_id)

        if not streak:
            return 1.0

        current_streak = streak.current_streak

        if current_streak >= 365:
            return 2.0
        elif current_streak >= 100:
            return 1.5
        elif current_streak >= 30:
            return 1.25
        elif current_streak >= 7:
            return 1.1
        else:
            return 1.0

    def _calculate_level_multiplier(self, level: int) -> float:
        """
        Calculate XP multiplier based on user level.

        Higher level players get slightly more XP to maintain engagement.

        Multipliers:
        - Level 1-25: 1.0x
        - Level 26-50: 1.05x
        - Level 51-75: 1.1x
        - Level 76-100: 1.15x

        Args:
            level: User level

        Returns:
            float: Level multiplier
        """
        if level >= 76:
            return 1.15
        elif level >= 51:
            return 1.1
        elif level >= 26:
            return 1.05
        else:
            return 1.0

    def _get_event_multiplier(self) -> float:
        """
        Get current event multiplier (for special events).

        Returns:
            float: Event multiplier (default 1.0)
        """
        # Check if there's an active event
        active_event = self.storage.get_active_event()

        if active_event and active_event.is_active:
            return active_event.xp_multiplier

        return 1.0

    def _get_user_progress(self, user_id: str) -> UserProgress:
        """Get or create user progress."""
        progress = self.storage.get_user_progress(user_id)

        if not progress:
            # Create new progress
            progress = UserProgress(user_id=user_id)
            self.storage.save_user_progress(progress)

        return progress

    def _update_user_progress(
        self,
        user_id: str,
        xp_earned: int,
        event_type: PointEventType,
    ):
        """Update user progress after earning XP."""
        progress = self._get_user_progress(user_id)

        # Update XP
        progress.total_xp += xp_earned
        progress.xp_current_level += xp_earned
        progress.last_xp_earned_at = datetime.utcnow()

        # Update activity counters
        if event_type == PointEventType.QUERY or event_type == PointEventType.QUERY_DEEP:
            progress.total_queries += 1
        elif event_type in [PointEventType.QUIZ_COMPLETE, PointEventType.QUIZ_PERFECT]:
            progress.total_quizzes += 1
        elif event_type == PointEventType.CASE_CONTRIBUTION:
            progress.total_cases_contributed += 1
        elif event_type == PointEventType.PEER_CONSULTATION:
            progress.total_peer_consultations += 1

        # Check for level up
        from .levels import LevelService
        level_service = LevelService(self.storage)

        while progress.xp_current_level >= progress.xp_to_next_level:
            # Level up!
            progress.xp_current_level -= progress.xp_to_next_level
            progress.current_level += 1

            # Get new level requirements
            new_level = level_service.get_level(progress.current_level)
            if new_level:
                progress.xp_to_next_level = new_level.xp_for_level

            # Trigger level up notification
            self._on_level_up(user_id, progress.current_level)

        progress.updated_at = datetime.utcnow()
        self.storage.save_user_progress(progress)

    def _on_level_up(self, user_id: str, new_level: int):
        """Handle level up event."""
        # This will trigger notifications, check for new badges, etc.
        # Import here to avoid circular dependency
        from .notifications import send_level_up_notification

        send_level_up_notification(user_id, new_level, self.storage)


def get_points_for_activity(
    activity_type: str,
    **kwargs,
) -> int:
    """
    Get base XP points for an activity.

    Args:
        activity_type: Type of activity
        **kwargs: Additional context (e.g., quiz_score for quiz activities)

    Returns:
        int: Base XP points
    """
    # Map activity types to point event types
    event_type_map = {
        'query': PointEventType.QUERY,
        'query_deep': PointEventType.QUERY_DEEP,
        'quiz': PointEventType.QUIZ_COMPLETE,
        'quiz_perfect': PointEventType.QUIZ_PERFECT,
        'case': PointEventType.CASE_CONTRIBUTION,
        'consultation': PointEventType.PEER_CONSULTATION,
        'login': PointEventType.DAILY_LOGIN,
        'referral': PointEventType.REFERRAL,
        'rating': PointEventType.CONTENT_RATED,
        'article': PointEventType.ARTICLE_READ,
        'video': PointEventType.VIDEO_WATCHED,
    }

    event_type = event_type_map.get(activity_type)

    if not event_type:
        return 0

    # Special handling for quiz - check score
    if activity_type == 'quiz':
        score = kwargs.get('score', 0)
        if score >= 1.0:  # Perfect score
            return BASE_XP_VALUES[PointEventType.QUIZ_PERFECT]
        else:
            return BASE_XP_VALUES[PointEventType.QUIZ_COMPLETE]

    return BASE_XP_VALUES.get(event_type, 0)
