"""
Achievement and Badge System

Gamification system to reward learning milestones and encourage engagement.
"""

from typing import Optional
import logging

from .models import (
    Achievement,
    UserAchievement,
    LearningActivity,
    ActivityType,
)

logger = logging.getLogger(__name__)


class AchievementSystem:
    """Manages achievements and badges"""

    def __init__(self):
        self.achievements: dict[str, Achievement] = {}
        self.user_achievements: dict[str, list[UserAchievement]] = {}
        self._initialize_achievements()

    def _initialize_achievements(self):
        """Initialize predefined achievements"""

        # Streak achievements
        self.register_achievement(Achievement(
            key="first_streak",
            title="First Streak",
            description="Maintain a 7-day learning streak",
            icon="🔥",
            criteria_type="streak",
            criteria_value=7,
            points=100,
            badge_tier="bronze",
        ))

        self.register_achievement(Achievement(
            key="streak_master",
            title="Streak Master",
            description="Maintain a 30-day learning streak",
            icon="🏆",
            criteria_type="streak",
            criteria_value=30,
            points=500,
            badge_tier="gold",
        ))

        self.register_achievement(Achievement(
            key="century_club",
            title="Century Club",
            description="Maintain a 100-day learning streak",
            icon="💯",
            criteria_type="streak",
            criteria_value=100,
            points=2000,
            badge_tier="platinum",
        ))

        # Query achievements
        self.register_achievement(Achievement(
            key="curious_mind",
            title="Curious Mind",
            description="Complete 10 medical queries",
            icon="🤔",
            criteria_type="queries",
            criteria_value=10,
            points=50,
            badge_tier="bronze",
        ))

        self.register_achievement(Achievement(
            key="knowledge_seeker",
            title="Knowledge Seeker",
            description="Complete 100 medical queries",
            icon="📚",
            criteria_type="queries",
            criteria_value=100,
            points=300,
            badge_tier="silver",
        ))

        self.register_achievement(Achievement(
            key="medical_scholar",
            title="Medical Scholar",
            description="Complete 1000 medical queries",
            icon="🎓",
            criteria_type="queries",
            criteria_value=1000,
            points=2000,
            badge_tier="platinum",
        ))

        # Quiz achievements
        self.register_achievement(Achievement(
            key="quiz_starter",
            title="Quiz Starter",
            description="Pass your first quiz",
            icon="📝",
            criteria_type="quizzes_passed",
            criteria_value=1,
            points=50,
            badge_tier="bronze",
        ))

        self.register_achievement(Achievement(
            key="quiz_champion",
            title="Quiz Champion",
            description="Achieve 100% on 10 quizzes",
            icon="🧠",
            criteria_type="perfect_quizzes",
            criteria_value=10,
            points=1000,
            badge_tier="gold",
        ))

        self.register_achievement(Achievement(
            key="quiz_master",
            title="Quiz Master",
            description="Pass 100 quizzes",
            icon="🎯",
            criteria_type="quizzes_passed",
            criteria_value=100,
            points=1500,
            badge_tier="platinum",
        ))

        # Specialty mastery
        for specialty in ["cardiology", "neurology", "pediatrics", "surgery", "internal_medicine"]:
            self.register_achievement(Achievement(
                key=f"{specialty}_expert",
                title=f"{specialty.title()} Expert",
                description=f"Complete 100 activities in {specialty}",
                icon="🏥",
                criteria_type=f"specialty_{specialty}",
                criteria_value=100,
                points=500,
                badge_tier="gold",
            ))

        # CME achievements
        self.register_achievement(Achievement(
            key="cme_starter",
            title="CME Starter",
            description="Earn your first CME credit",
            icon="⭐",
            criteria_type="cme_credits",
            criteria_value=1,
            points=25,
            badge_tier="bronze",
        ))

        self.register_achievement(Achievement(
            key="lifelong_learner",
            title="Lifelong Learner",
            description="Earn 30 CME credits in a year",
            icon="📖",
            criteria_type="annual_cme_credits",
            criteria_value=30,
            points=1000,
            badge_tier="gold",
        ))

        self.register_achievement(Achievement(
            key="cme_overachiever",
            title="CME Overachiever",
            description="Earn 100 CME credits (lifetime)",
            icon="🌟",
            criteria_type="total_cme_credits",
            criteria_value=100,
            points=3000,
            badge_tier="platinum",
        ))

        # Learning path achievements
        self.register_achievement(Achievement(
            key="path_explorer",
            title="Path Explorer",
            description="Complete your first learning path",
            icon="🗺️",
            criteria_type="paths_completed",
            criteria_value=1,
            points=200,
            badge_tier="bronze",
        ))

        self.register_achievement(Achievement(
            key="path_master",
            title="Path Master",
            description="Complete 10 learning paths",
            icon="🎖️",
            criteria_type="paths_completed",
            criteria_value=10,
            points=2000,
            badge_tier="platinum",
        ))

        # Time-based achievements
        self.register_achievement(Achievement(
            key="early_bird",
            title="Early Bird",
            description="Complete 30 activities before 8 AM",
            icon="🌅",
            criteria_type="early_morning_activities",
            criteria_value=30,
            points=300,
            badge_tier="silver",
            is_hidden=True,
        ))

        self.register_achievement(Achievement(
            key="night_owl",
            title="Night Owl",
            description="Complete 30 activities after 10 PM",
            icon="🦉",
            criteria_type="late_night_activities",
            criteria_value=30,
            points=300,
            badge_tier="silver",
            is_hidden=True,
        ))

        # Special achievements
        self.register_achievement(Achievement(
            key="speed_learner",
            title="Speed Learner",
            description="Complete 10 activities in one day",
            icon="⚡",
            criteria_type="activities_per_day",
            criteria_value=10,
            points=500,
            badge_tier="gold",
        ))

        self.register_achievement(Achievement(
            key="renaissance_doctor",
            title="Renaissance Doctor",
            description="Complete activities in 10 different specialties",
            icon="🎨",
            criteria_type="specialties_explored",
            criteria_value=10,
            points=750,
            badge_tier="gold",
        ))

        logger.info(f"Initialized {len(self.achievements)} achievements")

    def register_achievement(self, achievement: Achievement) -> None:
        """
        Register a new achievement

        Args:
            achievement: Achievement to register
        """
        self.achievements[achievement.key] = achievement

    def check_achievement(
        self,
        user_id: str,
        criteria_type: str,
        current_value: int,
    ) -> Optional[UserAchievement]:
        """
        Check if user has earned an achievement

        Args:
            user_id: User ID
            criteria_type: Type of criteria
            current_value: Current value for criteria

        Returns:
            UserAchievement if earned, None otherwise
        """
        # Find matching achievement
        achievement = None
        for ach in self.achievements.values():
            if ach.criteria_type == criteria_type:
                # Check if criteria met
                if current_value >= ach.criteria_value:
                    # Check if already earned
                    if not self._has_achievement(user_id, ach.key):
                        achievement = ach
                        break

        if not achievement:
            return None

        # Award achievement
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id,
            achievement_key=achievement.key,
            title=achievement.title,
            icon=achievement.icon,
            points_earned=achievement.points,
            progress_value=current_value,
        )

        # Store
        if user_id not in self.user_achievements:
            self.user_achievements[user_id] = []

        self.user_achievements[user_id].append(user_achievement)

        logger.info(
            f"User {user_id} earned achievement: {achievement.title} "
            f"(+{achievement.points} points)"
        )

        return user_achievement

    def get_user_achievements(self, user_id: str) -> list[UserAchievement]:
        """
        Get all achievements earned by user

        Args:
            user_id: User ID

        Returns:
            List of UserAchievements
        """
        return self.user_achievements.get(user_id, [])

    def get_user_points(self, user_id: str) -> int:
        """
        Get total points for user

        Args:
            user_id: User ID

        Returns:
            Total points
        """
        achievements = self.get_user_achievements(user_id)
        return sum(a.points_earned for a in achievements)

    def get_user_level(self, user_id: str) -> int:
        """
        Calculate user's level based on points

        Args:
            user_id: User ID

        Returns:
            Level (1-based)
        """
        points = self.get_user_points(user_id)

        # Level calculation: 100 points per level, increasing
        # Level 1: 0-99 points
        # Level 2: 100-299 points
        # Level 3: 300-599 points
        # etc.

        if points < 100:
            return 1

        level = 1
        threshold = 100

        while points >= threshold:
            level += 1
            threshold += level * 100

        return level

    def get_progress_to_next_level(self, user_id: str) -> dict:
        """
        Get progress toward next level

        Args:
            user_id: User ID

        Returns:
            Dict with level progress info
        """
        points = self.get_user_points(user_id)
        current_level = self.get_user_level(user_id)

        # Calculate points needed for current level
        points_for_level = 0
        for i in range(1, current_level):
            points_for_level += i * 100

        # Calculate points needed for next level
        points_for_next_level = points_for_level + current_level * 100

        points_in_level = points - points_for_level
        points_needed = points_for_next_level - points

        progress_percentage = (points_in_level / (current_level * 100)) * 100

        return {
            "current_level": current_level,
            "total_points": points,
            "points_in_level": points_in_level,
            "points_needed_for_next": points_needed,
            "progress_percentage": progress_percentage,
            "next_level": current_level + 1,
        }

    def get_available_achievements(self, user_id: str) -> list[dict]:
        """
        Get achievements user hasn't earned yet (with progress)

        Args:
            user_id: User ID

        Returns:
            List of available achievements with progress
        """
        earned_keys = set(a.achievement_key for a in self.get_user_achievements(user_id))

        available = []
        for achievement in self.achievements.values():
            if achievement.key not in earned_keys and not achievement.is_hidden:
                available.append({
                    "achievement": achievement,
                    "progress": 0,  # Would need to calculate based on user stats
                    "progress_percentage": 0.0,
                })

        return available

    def get_showcased_achievements(self, user_id: str) -> list[UserAchievement]:
        """
        Get achievements user has chosen to showcase

        Args:
            user_id: User ID

        Returns:
            List of showcased achievements
        """
        achievements = self.get_user_achievements(user_id)
        return [a for a in achievements if a.is_showcased]

    def showcase_achievement(self, user_id: str, achievement_id: str) -> bool:
        """
        Set an achievement to be showcased on profile

        Args:
            user_id: User ID
            achievement_id: Achievement ID

        Returns:
            True if successful
        """
        achievements = self.get_user_achievements(user_id)

        for achievement in achievements:
            if achievement.id == achievement_id:
                achievement.is_showcased = True
                logger.info(f"User {user_id} showcasing achievement: {achievement.title}")
                return True

        return False

    def unshowcase_achievement(self, user_id: str, achievement_id: str) -> bool:
        """
        Remove achievement from showcase

        Args:
            user_id: User ID
            achievement_id: Achievement ID

        Returns:
            True if successful
        """
        achievements = self.get_user_achievements(user_id)

        for achievement in achievements:
            if achievement.id == achievement_id:
                achievement.is_showcased = False
                return True

        return False

    def _has_achievement(self, user_id: str, achievement_key: str) -> bool:
        """
        Check if user has already earned an achievement

        Args:
            user_id: User ID
            achievement_key: Achievement key

        Returns:
            True if already earned
        """
        achievements = self.get_user_achievements(user_id)
        return any(a.achievement_key == achievement_key for a in achievements)


# Global achievement system instance
_achievement_system = AchievementSystem()


def get_achievement_system() -> AchievementSystem:
    """Get the global achievement system instance"""
    return _achievement_system
