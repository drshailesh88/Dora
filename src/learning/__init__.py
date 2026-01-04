"""
Learning and CME Module for Dora

Comprehensive learning system with CME credits, streaks, achievements, and analytics.
"""

from .models import (
    # Enums
    ActivityType,
    CMECategory,
    AccreditationBody,
    DifficultyLevel,
    QuestionType,
    PathStatus,

    # Main models
    LearningActivity,
    CMECredit,
    CMECertificate,
    LearningStreak,
    Achievement,
    UserAchievement,
    Quiz,
    QuizQuestion,
    QuizAttempt,
    LearningPath,
    LearningModule,
    PathEnrollment,
    LearningGoal,
    LearningReminder,
    LearningAnalytics,
)

from .tracker import ActivityTracker, get_tracker
from .cme import CMECreditSystem, get_cme_system
from .certificates import CertificateGenerator, get_certificate_generator
from .streaks import StreakManager, get_streak_manager
from .achievements import AchievementSystem, get_achievement_system
from .quizzes import QuizSystem, get_quiz_system
from .paths import PathManager, get_path_manager
from .reminders import ReminderSystem, get_reminder_system
from .analytics import AnalyticsEngine, get_analytics_engine
from .service import LearningService, get_learning_service

__all__ = [
    # Enums
    "ActivityType",
    "CMECategory",
    "AccreditationBody",
    "DifficultyLevel",
    "QuestionType",
    "PathStatus",

    # Models
    "LearningActivity",
    "CMECredit",
    "CMECertificate",
    "LearningStreak",
    "Achievement",
    "UserAchievement",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "LearningPath",
    "LearningModule",
    "PathEnrollment",
    "LearningGoal",
    "LearningReminder",
    "LearningAnalytics",

    # Classes
    "ActivityTracker",
    "CMECreditSystem",
    "CertificateGenerator",
    "StreakManager",
    "AchievementSystem",
    "QuizSystem",
    "PathManager",
    "ReminderSystem",
    "AnalyticsEngine",
    "LearningService",

    # Factory functions
    "get_tracker",
    "get_cme_system",
    "get_certificate_generator",
    "get_streak_manager",
    "get_achievement_system",
    "get_quiz_system",
    "get_path_manager",
    "get_reminder_system",
    "get_analytics_engine",
    "get_learning_service",
]
