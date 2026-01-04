"""
Learning Analytics

Analyzes learning patterns and CME progress:
- CME credit accumulation
- Quiz performance
- Learning streaks
- Knowledge gaps
- Topic mastery
"""

from collections import Counter
from datetime import date, timedelta
from typing import Optional, List, Dict

from .models import LearningMetrics


class LearningAnalyzer:
    """
    Analyzes learning patterns and CME progress.

    Provides insights on:
    - CME credit accumulation
    - Quiz performance trends
    - Knowledge gaps
    - Learning velocity
    - Specialty depth vs breadth
    """

    def __init__(self):
        """Initialize learning analyzer."""
        # Annual CME requirements (India MCI)
        self.annual_cme_requirement = 30.0
        self.category_1_min = 15.0

    def analyze_learning(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        learning_activities: Optional[List[dict]] = None,
        quiz_attempts: Optional[List[dict]] = None,
        streak_data: Optional[dict] = None,
    ) -> LearningMetrics:
        """
        Analyze learning patterns for a user.

        Args:
            user_id: User identifier
            start_date: Start of period
            end_date: End of period
            learning_activities: List of learning activity dicts
            quiz_attempts: List of quiz attempt dicts
            streak_data: Streak tracking data

        Returns:
            LearningMetrics with comprehensive analytics
        """
        if not learning_activities:
            learning_activities = []
        if not quiz_attempts:
            quiz_attempts = []

        # CME credits
        total_cme = sum(a.get('cme_credits_earned', 0) for a in learning_activities)
        cat1_credits = sum(
            a.get('cme_credits_earned', 0)
            for a in learning_activities
            if a.get('cme_category') == 'category_1'
        )
        cat2_credits = sum(
            a.get('cme_credits_earned', 0)
            for a in learning_activities
            if a.get('cme_category') == 'category_2'
        )
        cat3_credits = sum(
            a.get('cme_credits_earned', 0)
            for a in learning_activities
            if a.get('cme_category') == 'category_3'
        )

        # Calculate progress toward annual goal
        # Prorate based on time of year
        today = date.today()
        days_in_year = 366 if self._is_leap_year(today.year) else 365
        days_elapsed = (today - date(today.year, 1, 1)).days + 1
        prorated_goal = (days_elapsed / days_in_year) * self.annual_cme_requirement
        credits_needed = max(0, prorated_goal - total_cme)
        pct_of_goal = (total_cme / prorated_goal * 100) if prorated_goal > 0 else 0

        # Activity counts
        total_activities = len(learning_activities)
        articles_read = sum(1 for a in learning_activities if a.get('activity_type') == 'article_read')
        videos_watched = sum(1 for a in learning_activities if a.get('activity_type') == 'video_view')
        cases_studied = sum(1 for a in learning_activities if a.get('activity_type') == 'case_study')

        # Quiz analysis
        quizzes_attempted = len(quiz_attempts)
        quizzes_passed = sum(1 for q in quiz_attempts if q.get('passed', False))
        quiz_pass_rate = (quizzes_passed / quizzes_attempted * 100) if quizzes_attempted > 0 else 0

        # Average quiz score
        scores = [q.get('score', 0) for q in quiz_attempts]
        avg_quiz_score = (sum(scores) / len(scores) * 100) if scores else 0

        # Quiz accuracy by topic
        topic_accuracy = self._calculate_topic_accuracy(quiz_attempts)

        # Streak data
        current_streak = streak_data.get('current_streak', 0) if streak_data else 0
        longest_streak = streak_data.get('longest_streak', 0) if streak_data else 0
        milestones = streak_data.get('milestones_achieved', []) if streak_data else []

        # Time investment
        total_time = sum(a.get('duration_seconds', 0) for a in learning_activities)
        total_hours = total_time / 3600
        period_days = (end_date - start_date).days + 1
        avg_daily_minutes = (total_time / 60 / period_days) if period_days > 0 else 0

        # Topics studied
        topics_studied = self._analyze_topics_studied(learning_activities, quiz_attempts)

        # Knowledge gaps
        weak_areas = self._identify_weak_areas(quiz_attempts, topic_accuracy)

        # Depth vs breadth
        specialty_depth = self._calculate_specialty_depth(learning_activities)
        knowledge_breadth = self._calculate_knowledge_breadth(learning_activities)

        # Learning paths
        paths_enrolled = len(set(
            a.get('path_id') for a in learning_activities if a.get('path_id')
        ))
        paths_completed = sum(
            1 for a in learning_activities
            if a.get('activity_type') == 'path_complete'
        )
        path_completion_rate = (
            paths_completed / paths_enrolled * 100 if paths_enrolled > 0 else 0
        )

        # Achievements
        achievements = sum(1 for a in learning_activities if a.get('achievement_earned'))
        total_points = sum(a.get('points_earned', 0) for a in learning_activities)
        current_level = self._calculate_level(total_points)

        return LearningMetrics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            total_cme_credits=total_cme,
            category_1_credits=cat1_credits,
            category_2_credits=cat2_credits,
            category_3_credits=cat3_credits,
            credits_needed_for_annual_goal=credits_needed,
            percentage_of_annual_goal=pct_of_goal,
            total_learning_activities=total_activities,
            articles_read=articles_read,
            videos_watched=videos_watched,
            quizzes_attempted=quizzes_attempted,
            quizzes_passed=quizzes_passed,
            cases_studied=cases_studied,
            avg_quiz_score=avg_quiz_score,
            quiz_pass_rate=quiz_pass_rate,
            quiz_accuracy_by_topic=topic_accuracy,
            current_streak=current_streak,
            longest_streak=longest_streak,
            streak_milestones=milestones,
            total_learning_time_hours=total_hours,
            avg_daily_learning_minutes=avg_daily_minutes,
            topics_studied=topics_studied,
            weak_areas=weak_areas,
            specialty_depth_score=specialty_depth,
            knowledge_breadth_score=knowledge_breadth,
            paths_enrolled=paths_enrolled,
            paths_completed=paths_completed,
            path_completion_rate=path_completion_rate,
            achievements_earned=achievements,
            total_points=total_points,
            current_level=current_level,
        )

    def get_learning_recommendations(
        self,
        metrics: LearningMetrics,
    ) -> List[str]:
        """
        Get personalized learning recommendations.

        Args:
            metrics: LearningMetrics data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # CME progress
        if metrics.percentage_of_annual_goal < 50:
            recommendations.append(
                f"You're at {metrics.percentage_of_annual_goal:.0f}% of your annual CME goal. "
                f"Aim for {metrics.credits_needed_for_annual_goal:.1f} more credits to stay on track."
            )
        elif metrics.percentage_of_annual_goal >= 100:
            recommendations.append(
                "Excellent! You've met your annual CME goal. Consider exploring new specialties."
            )

        # Quiz performance
        if metrics.avg_quiz_score < 70:
            recommendations.append(
                "Your average quiz score is below 70%. Review weak topics before attempting more quizzes."
            )
        elif metrics.avg_quiz_score >= 85:
            recommendations.append(
                "Great quiz performance! Consider increasing difficulty or exploring advanced topics."
            )

        # Streak
        if metrics.current_streak >= 30:
            recommendations.append(
                f"Amazing {metrics.current_streak}-day streak! Consistency is key to mastery."
            )
        elif metrics.current_streak < 7:
            recommendations.append(
                "Build a daily learning habit. Even 10 minutes daily can make a big difference."
            )

        # Knowledge gaps
        if metrics.weak_areas:
            top_weak = metrics.weak_areas[0]
            recommendations.append(
                f"Focus on {top_weak['topic']} - your accuracy is {top_weak['accuracy']*100:.0f}% in this area."
            )

        # Depth vs breadth
        if metrics.specialty_depth_score > 0.8:
            recommendations.append(
                "You're deep in your specialty. Consider broadening knowledge in related areas."
            )
        elif metrics.knowledge_breadth_score < 0.3:
            recommendations.append(
                "Your learning is quite focused. Explore diverse topics for well-rounded knowledge."
            )

        # Learning paths
        if metrics.paths_enrolled > 0 and metrics.path_completion_rate < 50:
            recommendations.append(
                f"You have {metrics.paths_enrolled} learning paths in progress. "
                "Focus on completing one before starting others."
            )

        return recommendations

    def _calculate_topic_accuracy(self, quiz_attempts: List[dict]) -> Dict[str, float]:
        """Calculate accuracy by topic."""
        topic_stats = {}

        for attempt in quiz_attempts:
            topics = attempt.get('topics', [])
            score = attempt.get('score', 0)

            for topic in topics:
                if topic not in topic_stats:
                    topic_stats[topic] = {'total_score': 0, 'count': 0}

                topic_stats[topic]['total_score'] += score
                topic_stats[topic]['count'] += 1

        # Calculate averages
        topic_accuracy = {}
        for topic, stats in topic_stats.items():
            topic_accuracy[topic] = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0

        return topic_accuracy

    def _analyze_topics_studied(
        self,
        activities: List[dict],
        quiz_attempts: List[dict],
    ) -> List[dict]:
        """Analyze topics studied with mastery scores."""
        topic_time = Counter()
        topic_scores = {}

        # Aggregate time spent
        for activity in activities:
            topics = activity.get('topics', [])
            time_spent = activity.get('duration_seconds', 0)

            for topic in topics:
                topic_time[topic] += time_spent

        # Aggregate quiz scores
        for attempt in quiz_attempts:
            topics = attempt.get('topics', [])
            score = attempt.get('score', 0)

            for topic in topics:
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(score)

        # Combine into topic analysis
        topics = []
        for topic, time_spent in topic_time.most_common(20):
            scores = topic_scores.get(topic, [])
            mastery = sum(scores) / len(scores) if scores else 0.5

            topics.append({
                'topic': topic,
                'time_spent': time_spent,
                'mastery': mastery,
            })

        return topics

    def _identify_weak_areas(
        self,
        quiz_attempts: List[dict],
        topic_accuracy: Dict[str, float],
    ) -> List[dict]:
        """Identify knowledge gaps."""
        # Find topics with low accuracy
        weak_areas = []

        for topic, accuracy in topic_accuracy.items():
            if accuracy < 0.6:  # Below 60%
                weak_areas.append({
                    'topic': topic,
                    'accuracy': accuracy,
                })

        # Sort by accuracy (worst first)
        weak_areas.sort(key=lambda x: x['accuracy'])

        return weak_areas[:10]  # Top 10 weak areas

    def _calculate_specialty_depth(self, activities: List[dict]) -> float:
        """Calculate depth of knowledge in primary specialty (0-1)."""
        if not activities:
            return 0.0

        # Count activities by specialty
        specialty_counts = Counter()
        for activity in activities:
            specialty = activity.get('specialty', 'general')
            specialty_counts[specialty] += 1

        # Depth = concentration in top specialty
        total = len(activities)
        top_specialty_count = specialty_counts.most_common(1)[0][1] if specialty_counts else 0

        return top_specialty_count / total if total > 0 else 0.0

    def _calculate_knowledge_breadth(self, activities: List[dict]) -> float:
        """Calculate breadth of knowledge across topics (0-1)."""
        if not activities:
            return 0.0

        # Count unique topics
        topics = set()
        for activity in activities:
            topics.update(activity.get('topics', []))

        # Normalize: more unique topics = higher breadth
        # Assuming 50+ unique topics is "very broad"
        breadth = min(1.0, len(topics) / 50.0)

        return breadth

    def _calculate_level(self, total_points: int) -> int:
        """Calculate user level based on points."""
        # Simple leveling: 1000 points per level
        return (total_points // 1000) + 1

    def _is_leap_year(self, year: int) -> bool:
        """Check if year is leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


__all__ = ["LearningAnalyzer"]
