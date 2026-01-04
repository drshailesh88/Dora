"""
Learning Analytics

Analyzes learning patterns and provides insights to improve medical knowledge.
"""

from datetime import date, datetime, timedelta
from typing import Optional
import logging

from .models import (
    LearningAnalytics,
    LearningActivity,
    ActivityType,
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Generates learning analytics and insights"""

    def __init__(self):
        self.activities: list[LearningActivity] = []

    def analyze_period(
        self,
        user_id: str,
        period_start: date,
        period_end: date,
        activities: list[LearningActivity],
        cme_credits: float,
        current_streak: int,
        longest_streak: int,
    ) -> LearningAnalytics:
        """
        Generate analytics for a time period

        Args:
            user_id: User ID
            period_start: Period start date
            period_end: Period end date
            activities: Learning activities
            cme_credits: Total CME credits earned
            current_streak: Current streak
            longest_streak: Longest streak in period

        Returns:
            LearningAnalytics
        """
        analytics = LearningAnalytics(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
        )

        # Basic stats
        analytics.total_activities = len(activities)
        analytics.total_time_spent_seconds = sum(a.duration_seconds for a in activities)
        analytics.total_cme_credits = cme_credits

        # Activities by type
        activities_by_type: dict[str, int] = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            activities_by_type[activity_type] = activities_by_type.get(activity_type, 0) + 1

        analytics.activities_by_type = activities_by_type

        # CME credits by category
        # (Would integrate with CME system in production)
        analytics.credits_by_category = {
            "category_1": cme_credits * 0.6,  # Simplified
            "category_2": cme_credits * 0.4,
        }

        # Credits by specialty
        credits_by_specialty: dict[str, float] = {}
        for activity in activities:
            if activity.specialty and activity.cme_credits_earned > 0:
                specialty = activity.specialty
                credits_by_specialty[specialty] = (
                    credits_by_specialty.get(specialty, 0.0) + activity.cme_credits_earned
                )

        analytics.credits_by_specialty = credits_by_specialty

        # Streaks
        analytics.current_streak = current_streak
        analytics.longest_streak = longest_streak

        # Quiz performance
        quiz_activities = [
            a for a in activities
            if a.activity_type in [ActivityType.QUIZ_ATTEMPT, ActivityType.QUIZ_PASS]
        ]
        analytics.total_quizzes = len(quiz_activities)
        analytics.quizzes_passed = len([
            a for a in quiz_activities
            if a.activity_type == ActivityType.QUIZ_PASS
        ])

        if quiz_activities:
            total_score = sum(
                a.accuracy for a in quiz_activities
                if a.accuracy is not None
            )
            analytics.average_quiz_score = total_score / len(quiz_activities)

        # Top topics
        topic_counts: dict[str, int] = {}
        topic_accuracy: dict[str, list[float]] = {}

        for activity in activities:
            for topic in activity.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

                if activity.accuracy is not None:
                    if topic not in topic_accuracy:
                        topic_accuracy[topic] = []
                    topic_accuracy[topic].append(activity.accuracy)

        # Calculate topic mastery
        top_topics = []
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            # Calculate mastery (combination of frequency and accuracy)
            accuracy_scores = topic_accuracy.get(topic, [])
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.5

            mastery = min(1.0, (count / 10) * avg_accuracy)  # Simplified mastery calculation

            top_topics.append({
                "topic": topic,
                "count": count,
                "mastery": mastery,
            })

        analytics.top_topics = top_topics

        # Identify weak areas (topics with low accuracy)
        weak_areas = []
        for topic, accuracy_scores in topic_accuracy.items():
            if len(accuracy_scores) >= 3:  # Need at least 3 attempts to judge
                avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)

                if avg_accuracy < 0.7:  # Below 70%
                    weak_areas.append({
                        "topic": topic,
                        "accuracy": avg_accuracy,
                        "attempts": len(accuracy_scores),
                        "recommendation": self._get_improvement_recommendation(topic, avg_accuracy),
                    })

        analytics.weak_areas = sorted(weak_areas, key=lambda x: x["accuracy"])[:5]

        # Achievements
        # (Would integrate with achievement system in production)
        analytics.achievements_earned = 0  # Placeholder
        analytics.total_points = 0  # Placeholder
        analytics.current_level = 1  # Placeholder

        logger.info(
            f"Generated analytics for user {user_id}: "
            f"{analytics.total_activities} activities, {analytics.total_cme_credits} credits"
        )

        return analytics

    def get_learning_velocity(
        self,
        user_id: str,
        activities: list[LearningActivity],
        days: int = 30,
    ) -> dict:
        """
        Calculate learning velocity (activities per day, trending)

        Args:
            user_id: User ID
            activities: Activities
            days: Number of days to analyze

        Returns:
            Velocity metrics
        """
        if not activities:
            return {
                "avg_activities_per_day": 0,
                "avg_time_per_day": 0,
                "trend": "stable",
                "velocity_score": 0,
            }

        # Group by day
        activities_by_day: dict[date, int] = {}
        time_by_day: dict[date, int] = {}

        for activity in activities:
            activity_date = activity.started_at.date()

            activities_by_day[activity_date] = activities_by_day.get(activity_date, 0) + 1
            time_by_day[activity_date] = (
                time_by_day.get(activity_date, 0) + activity.duration_seconds
            )

        # Calculate averages
        avg_activities = sum(activities_by_day.values()) / days
        avg_time = sum(time_by_day.values()) / days

        # Calculate trend (compare first half vs second half)
        midpoint = days // 2
        first_half_dates = list(activities_by_day.keys())[:midpoint]
        second_half_dates = list(activities_by_day.keys())[midpoint:]

        first_half_avg = (
            sum(activities_by_day.get(d, 0) for d in first_half_dates) / midpoint
            if first_half_dates else 0
        )
        second_half_avg = (
            sum(activities_by_day.get(d, 0) for d in second_half_dates) / (days - midpoint)
            if second_half_dates else 0
        )

        if second_half_avg > first_half_avg * 1.2:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"

        # Velocity score (normalized 0-100)
        velocity_score = min(100, int(avg_activities * 10))

        return {
            "avg_activities_per_day": avg_activities,
            "avg_time_per_day_seconds": avg_time,
            "avg_time_per_day_minutes": avg_time // 60,
            "trend": trend,
            "velocity_score": velocity_score,
            "most_active_day": max(activities_by_day, key=activities_by_day.get) if activities_by_day else None,
        }

    def compare_to_peers(
        self,
        user_id: str,
        user_activities: int,
        user_cme_credits: float,
        user_streak: int,
        all_user_stats: list[dict],
    ) -> dict:
        """
        Compare user's learning to peers (anonymized)

        Args:
            user_id: User ID
            user_activities: User's activity count
            user_cme_credits: User's CME credits
            user_streak: User's current streak
            all_user_stats: Stats for all users (for percentile calculation)

        Returns:
            Comparison metrics
        """
        if not all_user_stats:
            return {
                "percentile_activities": 50.0,
                "percentile_credits": 50.0,
                "percentile_streak": 50.0,
                "overall_percentile": 50.0,
            }

        # Calculate percentiles
        activities_list = sorted([s["activities"] for s in all_user_stats])
        credits_list = sorted([s["credits"] for s in all_user_stats])
        streaks_list = sorted([s["streak"] for s in all_user_stats])

        percentile_activities = self._calculate_percentile(user_activities, activities_list)
        percentile_credits = self._calculate_percentile(user_cme_credits, credits_list)
        percentile_streak = self._calculate_percentile(user_streak, streaks_list)

        overall_percentile = (percentile_activities + percentile_credits + percentile_streak) / 3

        return {
            "percentile_activities": percentile_activities,
            "percentile_credits": percentile_credits,
            "percentile_streak": percentile_streak,
            "overall_percentile": overall_percentile,
            "rank_category": self._get_rank_category(overall_percentile),
        }

    def get_improvement_recommendations(
        self,
        user_id: str,
        analytics: LearningAnalytics,
    ) -> list[dict]:
        """
        Get personalized improvement recommendations

        Args:
            user_id: User ID
            analytics: User's analytics

        Returns:
            List of recommendations
        """
        recommendations = []

        # Weak areas
        if analytics.weak_areas:
            for weak_area in analytics.weak_areas[:3]:
                recommendations.append({
                    "type": "weak_area",
                    "priority": "high",
                    "title": f"Improve {weak_area['topic']}",
                    "description": weak_area["recommendation"],
                    "action": f"Review materials on {weak_area['topic']}",
                })

        # Low activity
        if analytics.total_activities < 10:
            recommendations.append({
                "type": "engagement",
                "priority": "medium",
                "title": "Increase Learning Activity",
                "description": "Aim for at least 2-3 queries per day to build knowledge.",
                "action": "Start with a quick clinical query",
            })

        # Low streak
        if analytics.current_streak < 7:
            recommendations.append({
                "type": "consistency",
                "priority": "medium",
                "title": "Build a Learning Streak",
                "description": "Daily learning leads to better retention.",
                "action": "Complete one activity daily this week",
            })

        # CME credits
        if analytics.total_cme_credits < 2.5:  # Monthly target
            recommendations.append({
                "type": "cme",
                "priority": "high",
                "title": "Earn More CME Credits",
                "description": "You're behind on your annual CME requirement.",
                "action": "Complete a quiz or learning module",
            })

        return recommendations

    def _get_improvement_recommendation(self, topic: str, accuracy: float) -> str:
        """Generate improvement recommendation for a topic"""
        if accuracy < 0.5:
            return f"Review fundamentals of {topic}. Consider taking a learning path."
        elif accuracy < 0.7:
            return f"Practice more questions on {topic} to improve retention."
        else:
            return f"Almost there! A few more practice questions on {topic}."

    def _calculate_percentile(self, value: float, sorted_values: list[float]) -> float:
        """Calculate percentile rank"""
        if not sorted_values:
            return 50.0

        rank = sum(1 for v in sorted_values if v < value)
        percentile = (rank / len(sorted_values)) * 100

        return round(percentile, 1)

    def _get_rank_category(self, percentile: float) -> str:
        """Get rank category based on percentile"""
        if percentile >= 90:
            return "Top Performer"
        elif percentile >= 75:
            return "Above Average"
        elif percentile >= 50:
            return "Average"
        elif percentile >= 25:
            return "Developing"
        else:
            return "Needs Focus"


# Global analytics engine instance
_analytics_engine = AnalyticsEngine()


def get_analytics_engine() -> AnalyticsEngine:
    """Get the global analytics engine instance"""
    return _analytics_engine
