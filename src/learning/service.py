"""
Learning Service

Main service that coordinates all learning subsystems.
"""

from datetime import date, datetime, timedelta
from typing import Optional
import logging

from .models import (
    LearningActivity,
    CMECredit,
    CMECertificate,
    LearningStreak,
    UserAchievement,
    Quiz,
    QuizAttempt,
    LearningPath,
    PathEnrollment,
    LearningAnalytics,
    LearningGoal,
    LearningReminder,
    ActivityType,
    AccreditationBody,
)

from .tracker import get_tracker, ActivityTracker
from .cme import get_cme_system, CMECreditSystem
from .certificates import get_certificate_generator, CertificateGenerator
from .streaks import get_streak_manager, StreakManager
from .achievements import get_achievement_system, AchievementSystem
from .quizzes import get_quiz_system, QuizSystem
from .paths import get_path_manager, PathManager
from .reminders import get_reminder_system, ReminderSystem
from .analytics import get_analytics_engine, AnalyticsEngine

logger = logging.getLogger(__name__)


class LearningService:
    """
    Main learning service that coordinates all subsystems

    This service provides a unified interface for:
    - Tracking learning activities
    - Awarding CME credits
    - Managing streaks and achievements
    - Generating quizzes and certificates
    - Learning paths
    - Spaced repetition reminders
    - Learning analytics
    """

    def __init__(
        self,
        tracker: Optional[ActivityTracker] = None,
        cme_system: Optional[CMECreditSystem] = None,
        certificate_generator: Optional[CertificateGenerator] = None,
        streak_manager: Optional[StreakManager] = None,
        achievement_system: Optional[AchievementSystem] = None,
        quiz_system: Optional[QuizSystem] = None,
        path_manager: Optional[PathManager] = None,
        reminder_system: Optional[ReminderSystem] = None,
        analytics_engine: Optional[AnalyticsEngine] = None,
    ):
        self.tracker = tracker or get_tracker()
        self.cme_system = cme_system or get_cme_system()
        self.certificate_generator = certificate_generator or get_certificate_generator()
        self.streak_manager = streak_manager or get_streak_manager()
        self.achievement_system = achievement_system or get_achievement_system()
        self.quiz_system = quiz_system or get_quiz_system()
        self.path_manager = path_manager or get_path_manager()
        self.reminder_system = reminder_system or get_reminder_system()
        self.analytics_engine = analytics_engine or get_analytics_engine()

    # === Activity Tracking ===

    def track_query(
        self,
        user_id: str,
        query_id: str,
        query_text: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        confidence_score: Optional[float] = None,
        has_follow_up: bool = False,
    ) -> dict:
        """
        Track a medical query and award credits/achievements

        Returns:
            Dict with activity, credits, achievements, etc.
        """
        # Track activity
        activity = self.tracker.track_query(
            user_id=user_id,
            query_id=query_id,
            query_text=query_text,
            specialty=specialty,
            topics=topics,
            duration_seconds=duration_seconds,
            confidence_score=confidence_score,
            has_follow_up=has_follow_up,
        )

        # Award CME credit
        credit = self.cme_system.award_credit_for_activity(activity)

        # Update streak
        streak = self.streak_manager.update_streak(user_id)

        # Check achievements
        achievements = self._check_achievements(user_id)

        return {
            "activity": activity,
            "cme_credit": credit,
            "streak": streak,
            "new_achievements": achievements,
        }

    def track_quiz_completion(
        self,
        user_id: str,
        quiz_id: str,
        attempt: QuizAttempt,
    ) -> dict:
        """
        Track quiz completion and award credits

        Returns:
            Dict with activity, credits, achievements
        """
        quiz = self.quiz_system.get_quiz(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz not found: {quiz_id}")

        # Track as activity
        activity = self.tracker.track_quiz_attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            quiz_title=quiz.title,
            specialty=quiz.specialty,
            topics=quiz.topics,
            duration_seconds=attempt.time_taken_seconds,
            score=attempt.score,
            passed=attempt.passed,
            total_questions=attempt.total_questions,
            correct_count=attempt.correct_count,
        )

        # Award CME credit if passed
        credit = None
        if attempt.passed:
            credit = self.cme_system.award_credit_for_activity(activity)

        # Update streak
        streak = self.streak_manager.update_streak(user_id)

        # Check achievements
        achievements = self._check_achievements(user_id)

        # Schedule spaced repetition reminder
        if attempt.next_review_date:
            self.reminder_system.create_spaced_repetition_reminder(
                user_id=user_id,
                quiz_id=quiz_id,
                quiz_title=quiz.title,
                scheduled_for=datetime.combine(attempt.next_review_date, datetime.min.time()),
            )

        return {
            "activity": activity,
            "cme_credit": credit,
            "streak": streak,
            "new_achievements": achievements,
        }

    # === Dashboard ===

    def get_learning_dashboard(self, user_id: str) -> dict:
        """
        Get comprehensive learning dashboard

        Returns:
            Dict with all learning metrics
        """
        # Streak status
        streak_status = self.streak_manager.check_streak_status(user_id)

        # CME credits (current year)
        annual_credits = self.cme_system.get_annual_credits(user_id)

        # Achievements
        user_achievements = self.achievement_system.get_user_achievements(user_id)
        level_progress = self.achievement_system.get_progress_to_next_level(user_id)

        # Quiz performance
        quiz_performance = self.quiz_system.get_quiz_performance(user_id)

        # Active learning paths
        active_paths = self.path_manager.get_active_enrollments(user_id)

        # Pending reminders
        pending_reminders = self.reminder_system.get_pending_reminders(user_id)

        # Recent activities
        recent_activities = self.tracker.get_user_activities(
            user_id,
            start_date=datetime.utcnow() - timedelta(days=30),
        )

        # Analytics (last 30 days)
        analytics = self.get_analytics(user_id, days=30)

        return {
            "streak": streak_status,
            "cme_credits": annual_credits,
            "achievements": {
                "earned": len(user_achievements),
                "recent": user_achievements[:5],
                "level": level_progress,
            },
            "quiz_performance": quiz_performance,
            "active_paths": len(active_paths),
            "pending_reminders": len(pending_reminders),
            "recent_activities_count": len(recent_activities),
            "analytics": analytics,
        }

    # === CME Certificates ===

    def generate_certificate(
        self,
        user_id: str,
        doctor_name: str,
        period_start: date,
        period_end: date,
        registration_number: Optional[str] = None,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
    ) -> CMECertificate:
        """
        Generate CME certificate for a period

        Returns:
            CMECertificate
        """
        # Get credits for period
        credits = self.cme_system.get_user_credits(
            user_id,
            start_date=period_start,
            end_date=period_end,
        )

        if not credits:
            raise ValueError("No credits earned in this period")

        # Generate certificate
        certificate = self.certificate_generator.generate_certificate(
            user_id=user_id,
            doctor_name=doctor_name,
            credits=credits,
            registration_number=registration_number,
            specialty=specialty,
            institution=institution,
        )

        logger.info(
            f"Generated certificate for user {user_id}: "
            f"{certificate.total_credits} credits"
        )

        return certificate

    # === Analytics ===

    def get_analytics(
        self,
        user_id: str,
        days: int = 30,
    ) -> LearningAnalytics:
        """
        Get learning analytics for a period

        Returns:
            LearningAnalytics
        """
        period_end = date.today()
        period_start = period_end - timedelta(days=days)

        # Get activities
        activities = self.tracker.get_user_activities(
            user_id,
            start_date=datetime.combine(period_start, datetime.min.time()),
            end_date=datetime.combine(period_end, datetime.max.time()),
        )

        # Get CME credits
        cme_credits = self.cme_system.get_total_credits(
            user_id,
            start_date=period_start,
            end_date=period_end,
        )

        # Get streak info
        streak = self.streak_manager.get_streak(user_id)

        # Generate analytics
        analytics = self.analytics_engine.analyze_period(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            activities=activities,
            cme_credits=cme_credits,
            current_streak=streak.current_streak,
            longest_streak=streak.longest_streak,
        )

        # Add percentile comparison (would need all user stats in production)
        # analytics.percentile_rank = ...

        return analytics

    # === Achievements ===

    def _check_achievements(self, user_id: str) -> list[UserAchievement]:
        """
        Check and award any new achievements

        Returns:
            List of newly earned achievements
        """
        new_achievements = []

        # Get user stats
        activities = self.tracker.get_user_activities(user_id)
        streak = self.streak_manager.get_streak(user_id)
        cme_credits = self.cme_system.get_total_credits(user_id)
        quiz_performance = self.quiz_system.get_quiz_performance(user_id)

        # Check various criteria
        checks = [
            ("streak", streak.current_streak),
            ("queries", len([a for a in activities if a.activity_type in [ActivityType.QUERY, ActivityType.QUERY_DEEP]])),
            ("quizzes_passed", quiz_performance.get("quizzes_passed", 0)),
            ("perfect_quizzes", quiz_performance.get("perfect_scores", 0)),
            ("total_cme_credits", cme_credits),
        ]

        for criteria_type, value in checks:
            achievement = self.achievement_system.check_achievement(
                user_id=user_id,
                criteria_type=criteria_type,
                current_value=int(value),
            )
            if achievement:
                new_achievements.append(achievement)

        return new_achievements

    # === Streaks ===

    def check_streak_and_remind(self, user_id: str) -> dict:
        """
        Check streak status and create reminder if needed

        Returns:
            Dict with streak status and reminder info
        """
        status = self.streak_manager.check_streak_status(user_id)

        # Create reminder if at risk
        if status["status"] == "at_risk":
            # Schedule reminder for this evening
            reminder_time = datetime.now().replace(hour=18, minute=0, second=0)

            if reminder_time < datetime.now():
                # If already past 6 PM, don't remind today
                return {"status": status, "reminder": None}

            reminder = self.reminder_system.create_streak_reminder(
                user_id=user_id,
                current_streak=status["current_streak"],
                scheduled_for=reminder_time,
            )

            return {"status": status, "reminder": reminder}

        return {"status": status, "reminder": None}

    # === Learning Paths ===

    def get_recommended_paths(
        self,
        user_id: str,
        user_specialty: Optional[str] = None,
        limit: int = 5,
    ) -> list[LearningPath]:
        """Get recommended learning paths for user"""
        return self.path_manager.get_recommended_paths(
            user_id=user_id,
            user_specialty=user_specialty,
            limit=limit,
        )

    def enroll_in_path(self, user_id: str, path_id: str) -> PathEnrollment:
        """Enroll user in learning path"""
        return self.path_manager.enroll_user(user_id, path_id)

    def complete_path_module(
        self,
        user_id: str,
        path_id: str,
        module_id: str,
        time_spent_seconds: int = 0,
    ) -> dict:
        """
        Complete a learning path module

        Returns:
            Dict with enrollment, activity, credits
        """
        # Complete module
        enrollment = self.path_manager.complete_module(
            user_id=user_id,
            path_id=path_id,
            module_id=module_id,
            time_spent_seconds=time_spent_seconds,
            cme_credits_earned=2.0,  # Would get from module
        )

        # Track as activity
        path = self.path_manager.get_path(path_id)
        module = next((m for m in path.modules if m.id == module_id), None) if path else None

        if module:
            activity = self.tracker.track_module_completion(
                user_id=user_id,
                module_id=module_id,
                module_title=module.title,
                path_id=path_id,
                specialty=path.specialty if path else None,
                topics=path.topics if path else None,
                duration_seconds=time_spent_seconds,
                cme_credits=module.cme_credits,
            )

            # Award CME credit
            credit = self.cme_system.award_credit_for_activity(activity)

            # Update streak
            streak = self.streak_manager.update_streak(user_id)

            # Check achievements
            achievements = self._check_achievements(user_id)

            # If path completed, generate certificate
            certificate = None
            if enrollment.status == PathStatus.COMPLETED and path:
                try:
                    certificate = self.certificate_generator.generate_path_certificate(
                        user_id=user_id,
                        doctor_name="Doctor",  # Would get from user profile
                        path_title=path.title,
                        credits=self.cme_system.get_user_credits(user_id),  # All credits
                    )
                except Exception as e:
                    logger.error(f"Failed to generate certificate: {e}")

            return {
                "enrollment": enrollment,
                "activity": activity,
                "cme_credit": credit,
                "streak": streak,
                "new_achievements": achievements,
                "certificate": certificate,
            }

        return {"enrollment": enrollment}

    # === Reminders ===

    def process_reminders(self) -> list[LearningReminder]:
        """
        Process and send due reminders

        Returns:
            List of reminders that were sent
        """
        due_reminders = self.reminder_system.process_due_reminders()

        sent = []
        for reminder in due_reminders:
            # In production, this would actually send notifications
            logger.info(
                f"Sending reminder to user {reminder.user_id}: {reminder.title}"
            )

            self.reminder_system.mark_as_sent(reminder.id)
            sent.append(reminder)

        return sent


# Global learning service instance
_learning_service = LearningService()


def get_learning_service() -> LearningService:
    """Get the global learning service instance"""
    return _learning_service
