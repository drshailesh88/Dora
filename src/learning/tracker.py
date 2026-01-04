"""
Learning Activity Tracker

Tracks all learning activities and categorizes them for CME credit calculation.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

from .models import (
    LearningActivity,
    ActivityType,
)

logger = logging.getLogger(__name__)


class ActivityTracker:
    """Tracks and categorizes learning activities"""

    def __init__(self):
        self.activities: list[LearningActivity] = []

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
    ) -> LearningActivity:
        """
        Track a medical query as a learning activity

        Args:
            user_id: User ID
            query_id: Query ID for reference
            query_text: The query text
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time spent on query
            confidence_score: Confidence in answer
            has_follow_up: Whether user did follow-up queries (deep learning)

        Returns:
            LearningActivity
        """
        activity_type = ActivityType.QUERY_DEEP if has_follow_up else ActivityType.QUERY

        # Calculate credits based on activity type
        cme_credits = self._calculate_query_credits(has_follow_up, duration_seconds)

        # Calculate points
        points = self._calculate_points(activity_type, duration_seconds)

        activity = LearningActivity(
            user_id=user_id,
            activity_type=activity_type,
            title=f"Query: {query_text[:100]}...",
            description=query_text,
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            confidence_score=confidence_score,
            query_id=query_id,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            metadata={
                "has_follow_up": has_follow_up,
                "query_length": len(query_text),
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked query activity for user {user_id}: {cme_credits} credits")

        return activity

    def track_calculator_use(
        self,
        user_id: str,
        calculator_name: str,
        specialty: Optional[str] = None,
        duration_seconds: int = 0,
        inputs: Optional[dict] = None,
        result: Optional[dict] = None,
    ) -> LearningActivity:
        """
        Track use of medical calculator

        Args:
            user_id: User ID
            calculator_name: Name of calculator used
            specialty: Medical specialty
            duration_seconds: Time spent
            inputs: Calculator inputs
            result: Calculator result

        Returns:
            LearningActivity
        """
        cme_credits = 0.05  # Small credit for calculator use
        points = 5

        activity = LearningActivity(
            user_id=user_id,
            activity_type=ActivityType.CALCULATOR,
            title=f"Calculator: {calculator_name}",
            description=f"Used {calculator_name} medical calculator",
            specialty=specialty,
            topics=[calculator_name.lower().replace(" ", "_")],
            duration_seconds=duration_seconds,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            metadata={
                "calculator_name": calculator_name,
                "inputs": inputs or {},
                "result": result or {},
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked calculator use for user {user_id}: {calculator_name}")

        return activity

    def track_article_read(
        self,
        user_id: str,
        article_id: str,
        article_title: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        completion_percentage: float = 100.0,
        source: Optional[str] = None,
    ) -> LearningActivity:
        """
        Track reading a medical article

        Args:
            user_id: User ID
            article_id: Article ID
            article_title: Article title
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time spent reading
            completion_percentage: How much was read (0-100)
            source: Article source (PubMed, Harrison's, etc.)

        Returns:
            LearningActivity
        """
        # Only award credits if read >70%
        if completion_percentage >= 70:
            cme_credits = 0.25
            points = 25
        else:
            cme_credits = 0.0
            points = 10

        activity = LearningActivity(
            user_id=user_id,
            activity_type=ActivityType.ARTICLE_READ,
            title=article_title,
            description=f"Read article from {source or 'knowledge base'}",
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow() - timedelta(seconds=duration_seconds),
            completed_at=datetime.utcnow(),
            metadata={
                "article_id": article_id,
                "completion_percentage": completion_percentage,
                "source": source,
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked article read for user {user_id}: {article_title}")

        return activity

    def track_video_view(
        self,
        user_id: str,
        video_id: str,
        video_title: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        watch_percentage: float = 100.0,
    ) -> LearningActivity:
        """
        Track watching an educational video

        Args:
            user_id: User ID
            video_id: Video ID
            video_title: Video title
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time spent watching
            watch_percentage: How much was watched (0-100)

        Returns:
            LearningActivity
        """
        # Only award credits if watched >80%
        if watch_percentage >= 80:
            cme_credits = 0.5
            points = 50
        else:
            cme_credits = 0.0
            points = 20

        activity = LearningActivity(
            user_id=user_id,
            activity_type=ActivityType.VIDEO_VIEW,
            title=video_title,
            description=f"Watched educational video",
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow() - timedelta(seconds=duration_seconds),
            completed_at=datetime.utcnow(),
            metadata={
                "video_id": video_id,
                "watch_percentage": watch_percentage,
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked video view for user {user_id}: {video_title}")

        return activity

    def track_quiz_attempt(
        self,
        user_id: str,
        quiz_id: str,
        quiz_title: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        score: float = 0.0,
        passed: bool = False,
        total_questions: int = 0,
        correct_count: int = 0,
    ) -> LearningActivity:
        """
        Track quiz attempt

        Args:
            user_id: User ID
            quiz_id: Quiz ID
            quiz_title: Quiz title
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time taken
            score: Score (0-1)
            passed: Whether user passed
            total_questions: Total questions
            correct_count: Correct answers

        Returns:
            LearningActivity
        """
        # Award credits only if passed
        activity_type = ActivityType.QUIZ_PASS if passed else ActivityType.QUIZ_ATTEMPT

        if passed:
            cme_credits = 0.5
            points = 100
        else:
            cme_credits = 0.0
            points = 25  # Participation points

        activity = LearningActivity(
            user_id=user_id,
            activity_type=activity_type,
            title=quiz_title,
            description=f"Quiz attempt - Score: {score*100:.0f}%",
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            accuracy=score,
            quiz_id=quiz_id,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow() - timedelta(seconds=duration_seconds),
            completed_at=datetime.utcnow(),
            metadata={
                "score": score,
                "passed": passed,
                "total_questions": total_questions,
                "correct_count": correct_count,
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked quiz attempt for user {user_id}: {quiz_title} - {'Passed' if passed else 'Failed'}")

        return activity

    def track_case_study(
        self,
        user_id: str,
        case_id: str,
        case_title: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        completed: bool = True,
    ) -> LearningActivity:
        """
        Track case study completion

        Args:
            user_id: User ID
            case_id: Case ID
            case_title: Case title
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time spent
            completed: Whether case was completed

        Returns:
            LearningActivity
        """
        if completed:
            cme_credits = 1.0  # Case studies are worth more
            points = 150
        else:
            cme_credits = 0.0
            points = 25

        activity = LearningActivity(
            user_id=user_id,
            activity_type=ActivityType.CASE_STUDY,
            title=case_title,
            description=f"Case study: {case_title}",
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow() - timedelta(seconds=duration_seconds),
            completed_at=datetime.utcnow() if completed else None,
            metadata={
                "case_id": case_id,
                "completed": completed,
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked case study for user {user_id}: {case_title}")

        return activity

    def track_module_completion(
        self,
        user_id: str,
        module_id: str,
        module_title: str,
        path_id: str,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        duration_seconds: int = 0,
        cme_credits: float = 2.0,
    ) -> LearningActivity:
        """
        Track learning module completion

        Args:
            user_id: User ID
            module_id: Module ID
            module_title: Module title
            path_id: Learning path ID
            specialty: Medical specialty
            topics: Topics covered
            duration_seconds: Time spent
            cme_credits: Credits for module

        Returns:
            LearningActivity
        """
        points = int(cme_credits * 100)  # 100 points per credit

        activity = LearningActivity(
            user_id=user_id,
            activity_type=ActivityType.MODULE_COMPLETE,
            title=module_title,
            description=f"Completed module: {module_title}",
            specialty=specialty,
            topics=topics or [],
            duration_seconds=duration_seconds,
            path_id=path_id,
            cme_credits_earned=cme_credits,
            points_earned=points,
            started_at=datetime.utcnow() - timedelta(seconds=duration_seconds),
            completed_at=datetime.utcnow(),
            metadata={
                "module_id": module_id,
                "path_id": path_id,
            }
        )

        self.activities.append(activity)
        logger.info(f"Tracked module completion for user {user_id}: {module_title}")

        return activity

    def get_user_activities(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        activity_type: Optional[ActivityType] = None,
    ) -> list[LearningActivity]:
        """
        Get user's learning activities

        Args:
            user_id: User ID
            start_date: Filter by start date
            end_date: Filter by end date
            activity_type: Filter by activity type

        Returns:
            List of learning activities
        """
        activities = [a for a in self.activities if a.user_id == user_id]

        if start_date:
            activities = [a for a in activities if a.started_at >= start_date]

        if end_date:
            activities = [a for a in activities if a.started_at <= end_date]

        if activity_type:
            activities = [a for a in activities if a.activity_type == activity_type]

        return sorted(activities, key=lambda x: x.started_at, reverse=True)

    def get_total_time_spent(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Get total time spent learning

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Total seconds spent
        """
        activities = self.get_user_activities(user_id, start_date, end_date)
        return sum(a.duration_seconds for a in activities)

    def get_activities_by_specialty(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, int]:
        """
        Get activity count by specialty

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict of specialty -> count
        """
        activities = self.get_user_activities(user_id, start_date, end_date)

        specialty_counts: dict[str, int] = {}
        for activity in activities:
            if activity.specialty:
                specialty_counts[activity.specialty] = specialty_counts.get(activity.specialty, 0) + 1

        return specialty_counts

    def get_activities_by_topic(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, int]:
        """
        Get activity count by topic

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            Dict of topic -> count
        """
        activities = self.get_user_activities(user_id, start_date, end_date)

        topic_counts: dict[str, int] = {}
        for activity in activities:
            for topic in activity.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return topic_counts

    def _calculate_query_credits(self, has_follow_up: bool, duration_seconds: int) -> float:
        """
        Calculate CME credits for a query

        Args:
            has_follow_up: Whether query had follow-up depth
            duration_seconds: Time spent

        Returns:
            CME credits
        """
        if has_follow_up and duration_seconds >= 120:  # 2+ minutes with depth
            return 0.1
        elif duration_seconds >= 60:  # 1+ minute
            return 0.05
        else:
            return 0.0  # Quick queries don't earn credits

    def _calculate_points(self, activity_type: ActivityType, duration_seconds: int) -> int:
        """
        Calculate XP points for an activity

        Args:
            activity_type: Type of activity
            duration_seconds: Time spent

        Returns:
            Points earned
        """
        base_points = {
            ActivityType.QUERY: 5,
            ActivityType.QUERY_DEEP: 15,
            ActivityType.CALCULATOR: 5,
            ActivityType.ARTICLE_READ: 25,
            ActivityType.VIDEO_VIEW: 50,
            ActivityType.QUIZ_ATTEMPT: 25,
            ActivityType.QUIZ_PASS: 100,
            ActivityType.CASE_STUDY: 150,
            ActivityType.MODULE_COMPLETE: 200,
            ActivityType.PATH_COMPLETE: 500,
        }

        points = base_points.get(activity_type, 0)

        # Bonus for longer engagement
        if duration_seconds >= 600:  # 10+ minutes
            points = int(points * 1.5)
        elif duration_seconds >= 300:  # 5+ minutes
            points = int(points * 1.2)

        return points

    def check_daily_limit(self, user_id: str, activity_date: Optional[datetime] = None) -> tuple[float, bool]:
        """
        Check if user has hit daily CME credit limit

        Args:
            user_id: User ID
            activity_date: Date to check (default: today)

        Returns:
            Tuple of (credits_earned_today, limit_reached)
        """
        if activity_date is None:
            activity_date = datetime.utcnow()

        start_of_day = activity_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        activities = self.get_user_activities(user_id, start_of_day, end_of_day)
        credits_today = sum(a.cme_credits_earned for a in activities)

        max_daily_credits = 2.0  # Max 2 credits per day
        limit_reached = credits_today >= max_daily_credits

        return credits_today, limit_reached


# Global tracker instance
_tracker = ActivityTracker()


def get_tracker() -> ActivityTracker:
    """Get the global activity tracker instance"""
    return _tracker
