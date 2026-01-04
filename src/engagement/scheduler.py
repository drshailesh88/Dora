"""
Notification Scheduler

Smart timing for engagement notifications.
Learns optimal delivery times from user behavior.
"""

from datetime import datetime, time, timedelta
from typing import Any, Optional
import asyncio

from src.engagement.models import (
    NotificationPreference,
    AlertSeverity,
    NotificationDeliveryStatus,
)


class NotificationScheduler:
    """Schedules engagement notifications intelligently."""

    def __init__(self):
        """Initialize notification scheduler."""
        self.scheduled_jobs = {}
        self.delivery_queue = []

    def schedule_briefing(
        self,
        user_id: str,
        preferences: NotificationPreference,
        briefing_data: dict[str, Any],
    ) -> datetime:
        """
        Schedule daily briefing delivery.

        Args:
            user_id: User ID
            preferences: User notification preferences
            briefing_data: Briefing content

        Returns:
            Scheduled delivery time
        """
        # Get optimal send time
        send_time = self._calculate_briefing_time(preferences)

        # Check if within quiet hours
        if self._is_in_quiet_hours(send_time.time(), preferences):
            # Adjust to end of quiet hours
            send_time = self._adjust_for_quiet_hours(send_time, preferences)

        # Schedule the notification
        self._schedule_notification(
            user_id=user_id,
            notification_type="briefing",
            content=briefing_data,
            send_time=send_time,
            priority="normal",
        )

        return send_time

    def schedule_alert(
        self,
        user_id: str,
        preferences: NotificationPreference,
        alert_data: dict[str, Any],
        severity: AlertSeverity,
    ) -> datetime:
        """
        Schedule alert delivery.

        Args:
            user_id: User ID
            preferences: User notification preferences
            alert_data: Alert content
            severity: Alert severity

        Returns:
            Scheduled delivery time
        """
        # Critical alerts go immediately
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            send_time = datetime.utcnow()
        else:
            # Low/medium alerts can wait for optimal time
            send_time = self._calculate_optimal_time(user_id, preferences)

            # Check if within quiet hours (even for medium alerts)
            if self._is_in_quiet_hours(send_time.time(), preferences):
                if severity == AlertSeverity.MEDIUM:
                    # Medium alerts wait until quiet hours end
                    send_time = self._adjust_for_quiet_hours(send_time, preferences)
                # Low alerts wait until next day

        # Schedule the notification
        priority = self._severity_to_priority(severity)
        self._schedule_notification(
            user_id=user_id,
            notification_type="alert",
            content=alert_data,
            send_time=send_time,
            priority=priority,
        )

        return send_time

    def batch_low_priority_notifications(
        self,
        user_id: str,
        notifications: list[dict[str, Any]],
        preferences: NotificationPreference,
    ) -> datetime:
        """
        Batch multiple low-priority notifications.

        Args:
            user_id: User ID
            notifications: List of notification content
            preferences: User notification preferences

        Returns:
            Scheduled batch delivery time
        """
        # Find optimal batching time (e.g., end of day)
        send_time = self._calculate_batch_time(preferences)

        # Create batched notification
        batched_content = {
            "type": "batch",
            "count": len(notifications),
            "items": notifications,
        }

        self._schedule_notification(
            user_id=user_id,
            notification_type="batch",
            content=batched_content,
            send_time=send_time,
            priority="low",
        )

        return send_time

    def learn_from_behavior(
        self,
        user_id: str,
        opened_at: datetime,
        notification_sent_at: datetime,
    ) -> None:
        """
        Learn optimal notification times from user behavior.

        Args:
            user_id: User ID
            opened_at: When notification was opened
            notification_sent_at: When notification was sent
        """
        # Calculate time-to-open
        time_to_open = (opened_at - notification_sent_at).total_seconds()

        # Extract hour when user opened
        open_hour = opened_at.hour

        # Store this pattern
        # In real implementation, update preferences with detected_active_hours
        # For now, just log the pattern
        pattern = {
            "user_id": user_id,
            "open_hour": open_hour,
            "time_to_open": time_to_open,
            "timestamp": datetime.utcnow(),
        }

        # Update user's detected active hours
        # This would update the NotificationPreference.detected_active_hours

    def should_send_now(
        self,
        user_id: str,
        preferences: NotificationPreference,
        severity: AlertSeverity,
    ) -> bool:
        """
        Check if notification should be sent now.

        Args:
            user_id: User ID
            preferences: User notification preferences
            severity: Notification severity

        Returns:
            True if should send now
        """
        now = datetime.utcnow().time()

        # Critical always sends
        if severity == AlertSeverity.CRITICAL:
            return True

        # Check quiet hours
        if self._is_in_quiet_hours(now, preferences):
            # High severity can interrupt quiet hours
            return severity == AlertSeverity.HIGH

        # During active hours, send
        return True

    def get_pending_notifications(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get pending notifications for user.

        Args:
            user_id: User ID

        Returns:
            List of pending notifications
        """
        pending = []

        for job_id, job in self.scheduled_jobs.items():
            if job["user_id"] == user_id:
                if job["send_time"] <= datetime.utcnow():
                    if job.get("status") != NotificationDeliveryStatus.SENT:
                        pending.append(job)

        return pending

    def cancel_notification(self, notification_id: str) -> bool:
        """
        Cancel a scheduled notification.

        Args:
            notification_id: Notification ID

        Returns:
            True if cancelled successfully
        """
        if notification_id in self.scheduled_jobs:
            del self.scheduled_jobs[notification_id]
            return True
        return False

    async def process_queue(self) -> None:
        """
        Process the notification queue.

        This is the main worker that sends notifications.
        Should be run as a background task.
        """
        while True:
            now = datetime.utcnow()

            # Find notifications ready to send
            ready_to_send = []
            for job_id, job in self.scheduled_jobs.items():
                if (job["send_time"] <= now and
                    job.get("status") != NotificationDeliveryStatus.SENT):
                    ready_to_send.append((job_id, job))

            # Send notifications
            for job_id, job in ready_to_send:
                await self._send_notification(job_id, job)

            # Sleep for a bit before next check
            await asyncio.sleep(60)  # Check every minute

    def _calculate_briefing_time(
        self,
        preferences: NotificationPreference,
    ) -> datetime:
        """Calculate when to send daily briefing."""
        # Parse preferred time
        time_parts = preferences.briefing_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        # If learning enabled, use detected active hours
        if (preferences.learn_from_behavior and
            preferences.detected_active_hours):
            # Find earliest morning active hour
            morning_hours = [h for h in preferences.detected_active_hours if 6 <= h <= 10]
            if morning_hours:
                hour = min(morning_hours)
                minute = 0

        # Create datetime for today
        today = datetime.utcnow().date()
        send_time = datetime.combine(today, time(hour, minute))

        # If time has passed, schedule for tomorrow
        if send_time < datetime.utcnow():
            send_time += timedelta(days=1)

        return send_time

    def _calculate_optimal_time(
        self,
        user_id: str,
        preferences: NotificationPreference,
    ) -> datetime:
        """Calculate optimal notification time based on user behavior."""
        now = datetime.utcnow()

        # If we have learned behavior, use detected active hours
        if (preferences.learn_from_behavior and
            preferences.detected_active_hours):
            current_hour = now.hour

            # Find next active hour
            active_hours = sorted(preferences.detected_active_hours)
            for hour in active_hours:
                if hour > current_hour:
                    return now.replace(hour=hour, minute=0, second=0, microsecond=0)

            # No active hour today, use first one tomorrow
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(
                hour=active_hours[0],
                minute=0,
                second=0,
                microsecond=0,
            )

        # Default: send in next 30 minutes
        return now + timedelta(minutes=30)

    def _calculate_batch_time(
        self,
        preferences: NotificationPreference,
    ) -> datetime:
        """Calculate when to send batched notifications."""
        # Default: end of work day (6 PM)
        batch_hour = 18

        # If user has detected active hours, use end of their active period
        if preferences.detected_active_hours:
            active_hours = sorted(preferences.detected_active_hours)
            if active_hours:
                # Use last active hour
                batch_hour = active_hours[-1]

        now = datetime.utcnow()
        batch_time = now.replace(hour=batch_hour, minute=0, second=0, microsecond=0)

        # If time has passed, schedule for tomorrow
        if batch_time < now:
            batch_time += timedelta(days=1)

        return batch_time

    def _is_in_quiet_hours(
        self,
        check_time: time,
        preferences: NotificationPreference,
    ) -> bool:
        """Check if time is within quiet hours."""
        if not preferences.quiet_hours_enabled:
            return False

        # Parse quiet hours
        quiet_start = self._parse_time(preferences.quiet_start)
        quiet_end = self._parse_time(preferences.quiet_end)

        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if quiet_start > quiet_end:
            return check_time >= quiet_start or check_time <= quiet_end
        else:
            return quiet_start <= check_time <= quiet_end

    def _adjust_for_quiet_hours(
        self,
        send_time: datetime,
        preferences: NotificationPreference,
    ) -> datetime:
        """Adjust send time to end of quiet hours."""
        if not preferences.quiet_hours_enabled:
            return send_time

        quiet_end = self._parse_time(preferences.quiet_end)

        # Create datetime for end of quiet hours
        adjusted = send_time.replace(
            hour=quiet_end.hour,
            minute=quiet_end.minute,
            second=0,
            microsecond=0,
        )

        # If quiet end time is before current send_time, it's for today
        # Otherwise, it might be for tomorrow
        if adjusted < send_time:
            adjusted += timedelta(days=1)

        return adjusted

    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object."""
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return time(hour, minute)

    def _severity_to_priority(self, severity: AlertSeverity) -> str:
        """Convert severity to priority string."""
        priority_map = {
            AlertSeverity.CRITICAL: "urgent",
            AlertSeverity.HIGH: "high",
            AlertSeverity.MEDIUM: "normal",
            AlertSeverity.LOW: "low",
            AlertSeverity.INFO: "low",
        }
        return priority_map.get(severity, "normal")

    def _schedule_notification(
        self,
        user_id: str,
        notification_type: str,
        content: dict[str, Any],
        send_time: datetime,
        priority: str,
    ) -> str:
        """Add notification to schedule."""
        import uuid

        job_id = str(uuid.uuid4())

        job = {
            "id": job_id,
            "user_id": user_id,
            "type": notification_type,
            "content": content,
            "send_time": send_time,
            "priority": priority,
            "status": NotificationDeliveryStatus.SCHEDULED,
            "created_at": datetime.utcnow(),
        }

        self.scheduled_jobs[job_id] = job

        return job_id

    async def _send_notification(
        self,
        job_id: str,
        job: dict[str, Any],
    ) -> None:
        """
        Send a notification.

        Args:
            job_id: Job ID
            job: Job data
        """
        # In real implementation, this would call notification service
        # (push notification, email, SMS, etc.)

        # Mark as sent
        job["status"] = NotificationDeliveryStatus.SENT
        job["sent_at"] = datetime.utcnow()

        # Log the send
        print(f"Sent {job['type']} notification to user {job['user_id']}")
