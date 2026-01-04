"""
Challenge System

Daily, weekly, and monthly challenges to keep users engaged.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from .models import (
    Challenge,
    ChallengeType,
    ChallengeStatus,
    UserChallenge,
)


# Daily challenge templates
DAILY_CHALLENGE_TEMPLATES = [
    {
        'title': 'Daily Explorer',
        'description': 'Ask 5 medical queries today',
        'icon': '🔍',
        'goal_type': 'queries',
        'goal_value': 5,
        'xp_reward': 50,
    },
    {
        'title': 'Quiz Time',
        'description': 'Complete 1 quiz today',
        'icon': '📝',
        'goal_type': 'quizzes',
        'goal_value': 1,
        'xp_reward': 50,
    },
    {
        'title': 'Knowledge Consumer',
        'description': 'Read 3 articles today',
        'icon': '📚',
        'goal_type': 'articles',
        'goal_value': 3,
        'xp_reward': 50,
    },
    {
        'title': 'Perfect Score',
        'description': 'Get 100% on any quiz today',
        'icon': '💯',
        'goal_type': 'quiz_perfect',
        'goal_value': 1,
        'xp_reward': 100,
    },
    {
        'title': 'Learning Streak',
        'description': 'Maintain your daily streak',
        'icon': '🔥',
        'goal_type': 'streak_maintain',
        'goal_value': 1,
        'xp_reward': 25,
    },
]

# Weekly challenge templates
WEEKLY_CHALLENGE_TEMPLATES = [
    {
        'title': 'Weekly Warrior',
        'description': 'Maintain a 7-day streak this week',
        'icon': '⚔️',
        'goal_type': 'streak',
        'goal_value': 7,
        'xp_reward': 500,
    },
    {
        'title': 'Quiz Master',
        'description': 'Complete 10 quizzes this week',
        'icon': '🎓',
        'goal_type': 'quizzes',
        'goal_value': 10,
        'xp_reward': 300,
    },
    {
        'title': 'Community Helper',
        'description': 'Help 3 peers with consultations',
        'icon': '🤝',
        'goal_type': 'peer_help',
        'goal_value': 3,
        'xp_reward': 400,
    },
    {
        'title': 'Specialty Focus',
        'description': 'Complete 20 queries in your specialty',
        'icon': '🎯',
        'goal_type': 'specialty_queries',
        'goal_value': 20,
        'xp_reward': 350,
    },
    {
        'title': 'Learning Path',
        'description': 'Complete 1 learning module',
        'icon': '🛤️',
        'goal_type': 'modules',
        'goal_value': 1,
        'xp_reward': 600,
    },
]

# Monthly challenge templates
MONTHLY_CHALLENGE_TEMPLATES = [
    {
        'title': 'Monthly Dedication',
        'description': 'Maintain 30-day streak',
        'icon': '🏅',
        'goal_type': 'streak',
        'goal_value': 30,
        'xp_reward': 2000,
    },
    {
        'title': 'Knowledge Champion',
        'description': 'Complete 50 quizzes this month',
        'icon': '👑',
        'goal_type': 'quizzes',
        'goal_value': 50,
        'xp_reward': 1500,
    },
    {
        'title': 'Case Contributor',
        'description': 'Contribute 5 clinical cases',
        'icon': '📋',
        'goal_type': 'cases',
        'goal_value': 5,
        'xp_reward': 2500,
    },
    {
        'title': 'Top Performer',
        'description': 'Reach top 100 in leaderboard',
        'icon': '⭐',
        'goal_type': 'leaderboard',
        'goal_value': 100,
        'xp_reward': 3000,
    },
]


class ChallengeService:
    """Service for managing challenges"""

    def __init__(self, storage):
        """
        Initialize challenge service.

        Args:
            storage: Storage backend
        """
        self.storage = storage

    def get_active_challenges(
        self,
        user_id: str,
        challenge_type: Optional[ChallengeType] = None,
    ) -> list[UserChallenge]:
        """
        Get user's active challenges.

        Args:
            user_id: User ID
            challenge_type: Filter by type (optional)

        Returns:
            list[UserChallenge]: Active challenges
        """
        # Get all user challenges
        challenges = self.storage.get_user_challenges(
            user_id=user_id,
            status=ChallengeStatus.ACTIVE,
        )

        if challenge_type:
            challenges = [
                c for c in challenges
                if c.challenge_type == challenge_type
            ]

        # Update progress
        for challenge in challenges:
            self._update_challenge_progress(user_id, challenge)

        return challenges

    def get_daily_challenges(self, user_id: str) -> list[UserChallenge]:
        """Get today's daily challenges."""
        today = date.today()

        # Check if daily challenges already exist
        existing = self.storage.get_user_challenges_by_date(
            user_id=user_id,
            challenge_date=today,
            challenge_type=ChallengeType.DAILY,
        )

        if existing:
            # Update progress
            for challenge in existing:
                self._update_challenge_progress(user_id, challenge)
            return existing

        # Generate new daily challenges (3 per day)
        import random
        selected = random.sample(DAILY_CHALLENGE_TEMPLATES, min(3, len(DAILY_CHALLENGE_TEMPLATES)))

        challenges = []
        for template in selected:
            challenge = self._create_challenge_from_template(
                template,
                ChallengeType.DAILY,
                today,
                today,
            )
            user_challenge = self._assign_challenge_to_user(user_id, challenge)
            challenges.append(user_challenge)

        return challenges

    def get_weekly_challenges(self, user_id: str) -> list[UserChallenge]:
        """Get this week's challenges."""
        # Get start of week (Monday)
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Check if weekly challenges exist
        existing = self.storage.get_user_challenges_by_date(
            user_id=user_id,
            challenge_date=start_of_week,
            challenge_type=ChallengeType.WEEKLY,
        )

        if existing:
            for challenge in existing:
                self._update_challenge_progress(user_id, challenge)
            return existing

        # Generate weekly challenges (2 per week)
        import random
        selected = random.sample(WEEKLY_CHALLENGE_TEMPLATES, min(2, len(WEEKLY_CHALLENGE_TEMPLATES)))

        challenges = []
        for template in selected:
            challenge = self._create_challenge_from_template(
                template,
                ChallengeType.WEEKLY,
                start_of_week,
                end_of_week,
            )
            user_challenge = self._assign_challenge_to_user(user_id, challenge)
            challenges.append(user_challenge)

        return challenges

    def get_monthly_challenges(self, user_id: str) -> list[UserChallenge]:
        """Get this month's challenges."""
        today = date.today()
        start_of_month = date(today.year, today.month, 1)

        # Calculate end of month
        if today.month == 12:
            end_of_month = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # Check if monthly challenges exist
        existing = self.storage.get_user_challenges_by_date(
            user_id=user_id,
            challenge_date=start_of_month,
            challenge_type=ChallengeType.MONTHLY,
        )

        if existing:
            for challenge in existing:
                self._update_challenge_progress(user_id, challenge)
            return existing

        # Generate monthly challenges (3 per month)
        import random
        selected = random.sample(MONTHLY_CHALLENGE_TEMPLATES, min(3, len(MONTHLY_CHALLENGE_TEMPLATES)))

        challenges = []
        for template in selected:
            challenge = self._create_challenge_from_template(
                template,
                ChallengeType.MONTHLY,
                start_of_month,
                end_of_month,
            )
            user_challenge = self._assign_challenge_to_user(user_id, challenge)
            challenges.append(user_challenge)

        return challenges

    def complete_challenge(
        self,
        user_id: str,
        challenge_id: str,
    ) -> dict:
        """
        Mark a challenge as completed.

        Args:
            user_id: User ID
            challenge_id: Challenge ID

        Returns:
            dict: Completion result
        """
        user_challenge = self.storage.get_user_challenge(user_id, challenge_id)

        if not user_challenge:
            return {
                'success': False,
                'message': 'Challenge not found',
            }

        if user_challenge.status == ChallengeStatus.COMPLETED:
            return {
                'success': False,
                'message': 'Challenge already completed',
            }

        # Check if goal reached
        self._update_challenge_progress(user_id, user_challenge)

        if user_challenge.current_value >= user_challenge.goal_value:
            # Mark as completed
            user_challenge.status = ChallengeStatus.COMPLETED
            user_challenge.completed_at = datetime.utcnow()
            self.storage.save_user_challenge(user_challenge)

            # Award XP
            from .points import PointsService, PointEventType

            points_service = PointsService(self.storage)
            points = points_service.award_points(
                user_id=user_id,
                event_type=PointEventType.CHALLENGE_COMPLETE,
                event_description=f"Completed challenge: {user_challenge.challenge_title}",
                reference_type='challenge',
                reference_id=challenge_id,
                custom_xp=user_challenge.xp_earned,
            )

            # Send notification
            from .notifications import send_challenge_complete_notification
            send_challenge_complete_notification(user_id, user_challenge, self.storage)

            return {
                'success': True,
                'message': f'Challenge completed! Earned {user_challenge.xp_earned} XP',
                'xp_earned': user_challenge.xp_earned,
            }
        else:
            return {
                'success': False,
                'message': f'Challenge not yet complete ({user_challenge.current_value}/{user_challenge.goal_value})',
            }

    def _create_challenge_from_template(
        self,
        template: dict,
        challenge_type: ChallengeType,
        start_date: date,
        end_date: date,
    ) -> Challenge:
        """Create a challenge from a template."""
        challenge = Challenge(
            challenge_type=challenge_type,
            title=template['title'],
            description=template['description'],
            icon=template.get('icon', '🎯'),
            goal_type=template['goal_type'],
            goal_value=template['goal_value'],
            xp_reward=template['xp_reward'],
            start_date=start_date,
            end_date=end_date,
            bonus_rewards=template.get('bonus_rewards', []),
        )

        self.storage.save_challenge(challenge)
        return challenge

    def _assign_challenge_to_user(
        self,
        user_id: str,
        challenge: Challenge,
    ) -> UserChallenge:
        """Assign a challenge to a user."""
        user_challenge = UserChallenge(
            user_id=user_id,
            challenge_id=challenge.id,
            challenge_title=challenge.title,
            challenge_type=challenge.challenge_type,
            goal_type=challenge.goal_type,
            goal_value=challenge.goal_value,
            xp_earned=challenge.xp_reward,
        )

        self.storage.save_user_challenge(user_challenge)
        return user_challenge

    def _update_challenge_progress(
        self,
        user_id: str,
        user_challenge: UserChallenge,
    ):
        """Update challenge progress."""
        # Get current value based on goal type
        current_value = self._get_progress_value(user_id, user_challenge.goal_type)

        user_challenge.current_value = current_value
        user_challenge.last_progress_at = datetime.utcnow()

        # Auto-complete if goal reached
        if (current_value >= user_challenge.goal_value and
            user_challenge.status == ChallengeStatus.ACTIVE):
            self.complete_challenge(user_id, user_challenge.challenge_id)

        self.storage.save_user_challenge(user_challenge)

    def _get_progress_value(self, user_id: str, goal_type: str) -> int:
        """Get current progress value for a goal type."""
        # This would query the storage for various stats
        # For now, return 0 as placeholder
        progress_getters = {
            'queries': lambda: self.storage.count_today_queries(user_id),
            'quizzes': lambda: self.storage.count_period_quizzes(user_id),
            'articles': lambda: self.storage.count_today_articles(user_id),
            'quiz_perfect': lambda: self.storage.count_period_perfect_quizzes(user_id),
            'streak_maintain': lambda: 1 if self.storage.get_streak(user_id).last_activity_date == date.today() else 0,
            'streak': lambda: self.storage.get_streak(user_id).current_streak if self.storage.get_streak(user_id) else 0,
            'peer_help': lambda: self.storage.count_period_consultations(user_id),
            'specialty_queries': lambda: self.storage.count_period_specialty_queries(user_id),
            'modules': lambda: self.storage.count_period_modules(user_id),
            'cases': lambda: self.storage.count_period_cases(user_id),
            'leaderboard': lambda: self.storage.get_user_progress(user_id).global_rank or 9999,
        }

        getter = progress_getters.get(goal_type)
        return getter() if getter else 0
