"""
Gamification Storage Backend

In-memory storage for gamification data. In production, this should be
replaced with a proper database backend (PostgreSQL, Redis, etc.).
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional

from .models import (
    Badge,
    Challenge,
    GamificationEvent,
    Leaderboard,
    LeaderboardEntry,
    Points,
    Reward,
    Streak,
    UserBadge,
    UserChallenge,
    UserMilestone,
    UserProgress,
    UserReward,
)


class GamificationStorage:
    """
    In-memory storage for gamification data.

    NOTE: This is a simple implementation for development/testing.
    For production, replace with PostgreSQL/Redis implementation.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        # User progress
        self._user_progress: dict[str, UserProgress] = {}

        # Points
        self._points: dict[str, list[Points]] = defaultdict(list)

        # Badges
        self._badges: dict[str, Badge] = {}
        self._user_badges: dict[str, list[UserBadge]] = defaultdict(list)

        # Streaks
        self._streaks: dict[str, Streak] = {}

        # Challenges
        self._challenges: dict[str, Challenge] = {}
        self._user_challenges: dict[str, list[UserChallenge]] = defaultdict(list)

        # Leaderboards
        self._leaderboards: dict[str, Leaderboard] = {}

        # Rewards
        self._rewards: dict[str, Reward] = {}
        self._user_rewards: dict[str, list[UserReward]] = defaultdict(list)

        # Events
        self._events: dict[str, list[GamificationEvent]] = defaultdict(list)

    # ========== User Progress ==========

    def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get user progress."""
        return self._user_progress.get(user_id)

    def save_user_progress(self, progress: UserProgress) -> UserProgress:
        """Save user progress."""
        self._user_progress[progress.user_id] = progress
        return progress

    # ========== Points ==========

    def save_points(self, points: Points) -> Points:
        """Save points entry."""
        self._points[points.user_id].append(points)
        return points

    def get_user_points(self, user_id: str, limit: int = 50) -> list[Points]:
        """Get user's points history."""
        points = self._points.get(user_id, [])
        return sorted(points, key=lambda p: p.timestamp, reverse=True)[:limit]

    # ========== Badges ==========

    def save_badge(self, badge: Badge) -> Badge:
        """Save badge definition."""
        self._badges[badge.key] = badge
        return badge

    def get_badge_by_key(self, key: str) -> Optional[Badge]:
        """Get badge by key."""
        return self._badges.get(key)

    def get_all_badges(self) -> list[Badge]:
        """Get all badge definitions."""
        return list(self._badges.values())

    def get_badges_by_category(self, category: str) -> list[Badge]:
        """Get badges by category."""
        return [b for b in self._badges.values() if b.category == category]

    def save_user_badge(self, user_badge: UserBadge) -> UserBadge:
        """Save user badge."""
        self._user_badges[user_badge.user_id].append(user_badge)
        return user_badge

    def get_user_badges(self, user_id: str) -> list[UserBadge]:
        """Get all badges earned by user."""
        return self._user_badges.get(user_id, [])

    def get_user_badge_by_key(self, user_id: str, badge_key: str) -> Optional[UserBadge]:
        """Get user badge by key."""
        badges = self._user_badges.get(user_id, [])
        for badge in badges:
            if badge.badge_key == badge_key:
                return badge
        return None

    # ========== Streaks ==========

    def get_streak(self, user_id: str) -> Optional[Streak]:
        """Get user streak."""
        return self._streaks.get(user_id)

    def save_streak(self, streak: Streak) -> Streak:
        """Save user streak."""
        self._streaks[streak.user_id] = streak
        return streak

    # ========== Challenges ==========

    def save_challenge(self, challenge: Challenge) -> Challenge:
        """Save challenge definition."""
        self._challenges[challenge.id] = challenge
        return challenge

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Get challenge by ID."""
        return self._challenges.get(challenge_id)

    def save_user_challenge(self, user_challenge: UserChallenge) -> UserChallenge:
        """Save user challenge."""
        self._user_challenges[user_challenge.user_id].append(user_challenge)
        return user_challenge

    def get_user_challenges(self, user_id: str) -> list[UserChallenge]:
        """Get user's challenges."""
        return self._user_challenges.get(user_id, [])

    # ========== Leaderboards ==========

    def save_leaderboard(self, leaderboard: Leaderboard) -> Leaderboard:
        """Save leaderboard."""
        key = f"{leaderboard.leaderboard_type}_{leaderboard.period}"
        self._leaderboards[key] = leaderboard
        return leaderboard

    def get_leaderboard(
        self, leaderboard_type: str, period: str
    ) -> Optional[Leaderboard]:
        """Get leaderboard."""
        key = f"{leaderboard_type}_{period}"
        return self._leaderboards.get(key)

    # ========== Rewards ==========

    def save_reward(self, reward: Reward) -> Reward:
        """Save reward definition."""
        self._rewards[reward.id] = reward
        return reward

    def get_reward(self, reward_id: str) -> Optional[Reward]:
        """Get reward by ID."""
        return self._rewards.get(reward_id)

    def get_all_rewards(self) -> list[Reward]:
        """Get all rewards."""
        return list(self._rewards.values())

    def save_user_reward(self, user_reward: UserReward) -> UserReward:
        """Save user reward."""
        self._user_rewards[user_reward.user_id].append(user_reward)
        return user_reward

    def get_user_rewards(self, user_id: str) -> list[UserReward]:
        """Get user's rewards."""
        return self._user_rewards.get(user_id, [])

    # ========== Events ==========

    def save_event(self, event: GamificationEvent) -> GamificationEvent:
        """Save gamification event."""
        self._events[event.user_id].append(event)
        return event

    def get_user_events(self, user_id: str, limit: int = 100) -> list[GamificationEvent]:
        """Get user's events."""
        events = self._events.get(user_id, [])
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    # ========== Counting/Stats Methods ==========

    def count_perfect_quizzes(self, user_id: str) -> int:
        """Count perfect quiz scores."""
        # Placeholder - needs quiz tracking implementation
        return 0

    def count_referrals(self, user_id: str) -> int:
        """Count user referrals."""
        # Placeholder - needs referral tracking implementation
        return 0

    def count_articles_read(self, user_id: str) -> int:
        """Count articles read."""
        # Placeholder - needs article tracking implementation
        return 0

    def count_videos_watched(self, user_id: str) -> int:
        """Count videos watched."""
        # Placeholder - needs video tracking implementation
        return 0

    def count_completed_challenges(self, user_id: str) -> int:
        """Count completed challenges."""
        challenges = self._user_challenges.get(user_id, [])
        from .models import ChallengeStatus

        return sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED)


# Global storage instance
_storage: Optional[GamificationStorage] = None


def get_gamification_storage() -> GamificationStorage:
    """Get the global gamification storage instance."""
    global _storage
    if _storage is None:
        _storage = GamificationStorage()
    return _storage
