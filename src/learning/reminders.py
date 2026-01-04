"""
Learning Reminders

Spaced repetition and engagement reminders to keep doctors learning.
"""

from datetime import datetime, date, timedelta
from typing import Optional
import logging

from .models import LearningReminder

logger = logging.getLogger(__name__)


class ReminderSystem:
    """Manages learning reminders"""

    def __init__(self):
        self.reminders: list[LearningReminder] = []

    def create_spaced_repetition_reminder(
        self,
        user_id: str,
        quiz_id: str,
        quiz_title: str,
        scheduled_for: datetime,
        delivery_channels: Optional[list[str]] = None,
    ) -> LearningReminder:
        """
        Create spaced repetition reminder for quiz review

        Args:
            user_id: User ID
            quiz_id: Quiz ID to review
            quiz_title: Quiz title
            scheduled_for: When to send reminder
            delivery_channels: How to deliver (in_app, email, sms, push)

        Returns:
            LearningReminder
        """
        reminder = LearningReminder(
            user_id=user_id,
            reminder_type="spaced_repetition",
            title="Time to Review",
            message=f"Recall: {quiz_title}",
            reference_type="quiz",
            reference_id=quiz_id,
            scheduled_for=scheduled_for,
            delivery_channels=delivery_channels or ["in_app"],
        )

        self.reminders.append(reminder)

        logger.info(
            f"Created spaced repetition reminder for user {user_id}: {quiz_title}"
        )

        return reminder

    def create_streak_reminder(
        self,
        user_id: str,
        current_streak: int,
        scheduled_for: datetime,
        delivery_channels: Optional[list[str]] = None,
    ) -> LearningReminder:
        """
        Create streak maintenance reminder

        Args:
            user_id: User ID
            current_streak: Current streak count
            scheduled_for: When to send
            delivery_channels: Delivery channels

        Returns:
            LearningReminder
        """
        if current_streak == 0:
            message = "Start your learning streak today! Just one query keeps you sharp."
        elif current_streak < 7:
            message = f"🔥 Keep your {current_streak}-day streak alive! Complete an activity today."
        else:
            message = f"🔥 Don't break your {current_streak}-day streak! Quick learning activity?"

        reminder = LearningReminder(
            user_id=user_id,
            reminder_type="streak",
            title="Maintain Your Streak",
            message=message,
            scheduled_for=scheduled_for,
            delivery_channels=delivery_channels or ["in_app", "push"],
        )

        self.reminders.append(reminder)

        logger.info(f"Created streak reminder for user {user_id}")

        return reminder

    def create_goal_reminder(
        self,
        user_id: str,
        goal_type: str,
        target_value: int,
        current_value: int,
        scheduled_for: datetime,
        delivery_channels: Optional[list[str]] = None,
    ) -> LearningReminder:
        """
        Create learning goal reminder

        Args:
            user_id: User ID
            goal_type: Type of goal
            target_value: Target value
            current_value: Current progress
            scheduled_for: When to send
            delivery_channels: Delivery channels

        Returns:
            LearningReminder
        """
        remaining = target_value - current_value
        progress_pct = (current_value / target_value * 100) if target_value > 0 else 0

        message = (
            f"You're {progress_pct:.0f}% toward your goal! "
            f"Just {remaining} more to go."
        )

        reminder = LearningReminder(
            user_id=user_id,
            reminder_type="goal",
            title="Goal Progress",
            message=message,
            scheduled_for=scheduled_for,
            delivery_channels=delivery_channels or ["in_app"],
        )

        self.reminders.append(reminder)

        logger.info(f"Created goal reminder for user {user_id}")

        return reminder

    def create_quiz_review_reminder(
        self,
        user_id: str,
        quiz_id: str,
        quiz_title: str,
        last_score: float,
        scheduled_for: datetime,
        delivery_channels: Optional[list[str]] = None,
    ) -> LearningReminder:
        """
        Create quiz review reminder

        Args:
            user_id: User ID
            quiz_id: Quiz ID
            quiz_title: Quiz title
            last_score: Previous score
            scheduled_for: When to send
            delivery_channels: Delivery channels

        Returns:
            LearningReminder
        """
        message = (
            f"Time to review: {quiz_title}\n"
            f"Last score: {last_score*100:.0f}%. Can you do better?"
        )

        reminder = LearningReminder(
            user_id=user_id,
            reminder_type="quiz_review",
            title="Quiz Review",
            message=message,
            reference_type="quiz",
            reference_id=quiz_id,
            scheduled_for=scheduled_for,
            delivery_channels=delivery_channels or ["in_app"],
        )

        self.reminders.append(reminder)

        logger.info(f"Created quiz review reminder for user {user_id}")

        return reminder

    def get_pending_reminders(
        self,
        user_id: Optional[str] = None,
        before: Optional[datetime] = None,
    ) -> list[LearningReminder]:
        """
        Get pending (unsent) reminders

        Args:
            user_id: Filter by user ID
            before: Filter by scheduled time

        Returns:
            List of pending reminders
        """
        reminders = [r for r in self.reminders if not r.is_sent]

        if user_id:
            reminders = [r for r in reminders if r.user_id == user_id]

        if before:
            reminders = [r for r in reminders if r.scheduled_for <= before]

        return sorted(reminders, key=lambda x: x.scheduled_for)

    def get_user_reminders(
        self,
        user_id: str,
        include_sent: bool = False,
    ) -> list[LearningReminder]:
        """
        Get user's reminders

        Args:
            user_id: User ID
            include_sent: Include sent reminders

        Returns:
            List of reminders
        """
        reminders = [r for r in self.reminders if r.user_id == user_id]

        if not include_sent:
            reminders = [r for r in reminders if not r.is_sent]

        return sorted(reminders, key=lambda x: x.scheduled_for, reverse=True)

    def mark_as_sent(self, reminder_id: str) -> bool:
        """
        Mark reminder as sent

        Args:
            reminder_id: Reminder ID

        Returns:
            True if successful
        """
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                reminder.is_sent = True
                reminder.sent_at = datetime.utcnow()
                logger.info(f"Marked reminder {reminder_id} as sent")
                return True

        return False

    def mark_as_completed(self, reminder_id: str) -> bool:
        """
        Mark reminder as completed (user took action)

        Args:
            reminder_id: Reminder ID

        Returns:
            True if successful
        """
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                reminder.is_completed = True
                reminder.completed_at = datetime.utcnow()
                logger.info(f"Marked reminder {reminder_id} as completed")
                return True

        return False

    def process_due_reminders(self) -> list[LearningReminder]:
        """
        Get reminders that are due to be sent now

        Returns:
            List of due reminders
        """
        now = datetime.utcnow()
        due = self.get_pending_reminders(before=now)

        logger.info(f"Found {len(due)} due reminders")

        return due


# Global reminder system instance
_reminder_system = ReminderSystem()


def get_reminder_system() -> ReminderSystem:
    """Get the global reminder system instance"""
    return _reminder_system
