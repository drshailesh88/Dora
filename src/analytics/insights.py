"""
AI-Generated Insights

Generates actionable insights from analytics data:
- Achievements and milestones
- Trend identification
- Anomaly detection
- Personalized recommendations
- Learning opportunities
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import uuid4

from .models import (
    InsightReport,
    InsightCategory,
    QueryAnalytics,
    PrescriptionPatterns,
    LearningMetrics,
    ComparisonMetrics,
    TrendData,
)


class InsightGenerator:
    """
    Generates AI-powered practice insights.

    Creates actionable insights from:
    - Analytics trends
    - Milestone achievements
    - Peer comparisons
    - Performance patterns
    """

    def __init__(self):
        """Initialize insight generator."""
        pass

    def generate_insights(
        self,
        user_id: str,
        query_analytics: Optional[QueryAnalytics] = None,
        prescription_patterns: Optional[PrescriptionPatterns] = None,
        learning_metrics: Optional[LearningMetrics] = None,
        comparison_metrics: Optional[ComparisonMetrics] = None,
        trends: Optional[List[TrendData]] = None,
    ) -> List[InsightReport]:
        """
        Generate comprehensive insights from all analytics.

        Args:
            user_id: User identifier
            query_analytics: Query pattern analytics
            prescription_patterns: Prescription analytics
            learning_metrics: Learning analytics
            comparison_metrics: Peer comparison data
            trends: Trend data

        Returns:
            List of InsightReport objects
        """
        insights = []

        # Query insights
        if query_analytics:
            insights.extend(self._generate_query_insights(user_id, query_analytics))

        # Prescription insights
        if prescription_patterns:
            insights.extend(self._generate_prescription_insights(user_id, prescription_patterns))

        # Learning insights
        if learning_metrics:
            insights.extend(self._generate_learning_insights(user_id, learning_metrics))

        # Comparison insights
        if comparison_metrics:
            insights.extend(self._generate_comparison_insights(user_id, comparison_metrics))

        # Trend insights
        if trends:
            insights.extend(self._generate_trend_insights(user_id, trends))

        # Sort by priority and impact
        insights.sort(key=lambda i: (
            {'high': 3, 'medium': 2, 'low': 1}.get(i.priority, 1),
            i.impact_score
        ), reverse=True)

        return insights

    def _generate_query_insights(
        self,
        user_id: str,
        analytics: QueryAnalytics,
    ) -> List[InsightReport]:
        """Generate insights from query analytics."""
        insights = []

        # High query volume achievement
        if analytics.total_queries >= 100:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="Query Master!",
                message=f"You've made {analytics.total_queries} queries this month!",
                detailed_explanation=(
                    "Your active engagement with Dora shows strong commitment to "
                    "evidence-based practice. Keep leveraging this knowledge!"
                ),
                priority="medium",
                impact_score=0.6,
                metric_name="total_queries",
                metric_value=float(analytics.total_queries),
            ))

        # High confidence rate
        if analytics.high_confidence_rate >= 80:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="High-Quality Queries",
                message=f"{analytics.high_confidence_rate:.0f}% of your queries had high-confidence answers!",
                detailed_explanation=(
                    "You're asking well-formulated questions that match our knowledge base. "
                    "This indicates effective use of Dora for clinical decision support."
                ),
                priority="low",
                impact_score=0.5,
            ))

        # Error rate warning
        if analytics.error_rate > 10:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.WARNING,
                title="Query Error Rate Alert",
                message=f"{analytics.error_rate:.0f}% of queries encountered errors.",
                detailed_explanation=(
                    "Some of your queries may be too complex or outside our knowledge domain. "
                    "Try breaking complex questions into smaller parts."
                ),
                recommendations=[
                    "Break complex questions into simpler parts",
                    "Check your internet connection for cloud queries",
                    "Contact support if errors persist",
                ],
                priority="medium",
                impact_score=0.7,
            ))

        # Specialty focus insight
        if analytics.specialty_distribution:
            top_specialty = max(
                analytics.specialty_distribution.items(),
                key=lambda x: x[1]
            )[0]
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.TREND,
                title=f"Focus on {top_specialty.title()}",
                message=f"Most of your queries are about {top_specialty}.",
                detailed_explanation=(
                    f"You're building deep expertise in {top_specialty}. "
                    "Consider exploring related specialties to broaden your knowledge."
                ),
                recommendations=[
                    f"Complete a learning path in {top_specialty}",
                    "Explore complementary specialties",
                ],
                related_topics=[top_specialty],
                priority="low",
                impact_score=0.4,
            ))

        return insights

    def _generate_prescription_insights(
        self,
        user_id: str,
        patterns: PrescriptionPatterns,
    ) -> List[InsightReport]:
        """Generate insights from prescription patterns."""
        insights = []

        # Generic prescribing excellence
        if patterns.generic_percentage >= 75:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="Generic Prescribing Champion!",
                message=f"{patterns.generic_percentage:.0f}% generic medication usage!",
                detailed_explanation=(
                    f"You've saved patients approximately ₹{patterns.cost_savings_from_generics:,.0f} "
                    "by preferring generic medications. Excellent cost-conscious prescribing!"
                ),
                priority="high",
                impact_score=0.9,
                metric_name="generic_percentage",
                metric_value=patterns.generic_percentage,
            ))

        # Low generic rate warning
        elif patterns.generic_percentage < 50:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.RECOMMENDATION,
                title="Increase Generic Prescribing",
                message=f"Only {patterns.generic_percentage:.0f}% of prescriptions use generics.",
                detailed_explanation=(
                    "Generic medications can significantly reduce patient costs while "
                    "maintaining therapeutic equivalence. Consider generics when appropriate."
                ),
                recommendations=[
                    "Review generic alternatives for common prescriptions",
                    "Enable Dora's generic suggestion feature",
                    "Educate patients on generic equivalence",
                ],
                actionable_steps=[
                    "Use Dora's drug alternative suggestions",
                    "Set generic as default in prescription templates",
                ],
                priority="medium",
                impact_score=0.7,
            ))

        # Antibiotic stewardship
        if patterns.antibiotic_percentage > 30:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.WARNING,
                title="High Antibiotic Usage",
                message=f"{patterns.antibiotic_percentage:.0f}% of prescriptions include antibiotics.",
                detailed_explanation=(
                    "High antibiotic prescribing may contribute to resistance. "
                    "Review antibiotic guidelines and consider narrower-spectrum options."
                ),
                recommendations=[
                    "Follow antibiotic stewardship guidelines",
                    "Prefer narrow-spectrum antibiotics",
                    "Review indications for antibiotic therapy",
                ],
                priority="high",
                impact_score=0.8,
            ))

        # Safety excellence
        if patterns.safety_score >= 0.9 and patterns.total_prescriptions >= 10:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="Perfect Safety Record",
                message="Zero safety alerts in your prescriptions!",
                detailed_explanation=(
                    "Your prescriptions have minimal drug interactions and contraindications. "
                    "This demonstrates excellent clinical judgment and safety awareness."
                ),
                priority="medium",
                impact_score=0.7,
            ))

        return insights

    def _generate_learning_insights(
        self,
        user_id: str,
        metrics: LearningMetrics,
    ) -> List[InsightReport]:
        """Generate insights from learning metrics."""
        insights = []

        # CME goal achievement
        if metrics.percentage_of_annual_goal >= 100:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.MILESTONE,
                title="Annual CME Goal Achieved!",
                message=f"You've earned {metrics.total_cme_credits:.1f} CME credits!",
                detailed_explanation=(
                    "Congratulations on completing your annual CME requirement! "
                    "Your commitment to continuous learning is exemplary."
                ),
                priority="high",
                impact_score=1.0,
            ))

        # CME behind schedule
        elif metrics.percentage_of_annual_goal < 50:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.RECOMMENDATION,
                title="CME Progress Check",
                message=f"You're at {metrics.percentage_of_annual_goal:.0f}% of your annual CME goal.",
                detailed_explanation=(
                    f"You need {metrics.credits_needed_for_annual_goal:.1f} more credits to stay on track. "
                    "Consider scheduling regular learning time."
                ),
                recommendations=[
                    "Complete 1 quiz daily (5-10 minutes)",
                    "Enroll in a learning path",
                    "Use Dora queries to earn Category 2 credits",
                ],
                actionable_steps=[
                    "Set a daily learning reminder",
                    "Block 30 minutes weekly for CME",
                ],
                priority="medium",
                impact_score=0.7,
            ))

        # Streak milestone
        if metrics.current_streak >= 30:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.MILESTONE,
                title=f"{metrics.current_streak}-Day Streak!",
                message="Your consistency is remarkable!",
                detailed_explanation=(
                    "Daily learning builds lasting knowledge. "
                    "Your streak demonstrates exceptional dedication to continuous improvement."
                ),
                priority="high",
                impact_score=0.9,
            ))

        # Broken streak encouragement
        elif metrics.current_streak == 0 and metrics.longest_streak >= 7:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.RECOMMENDATION,
                title="Rebuild Your Streak",
                message=f"Your longest streak was {metrics.longest_streak} days.",
                detailed_explanation=(
                    "Get back on track! Even 5 minutes of learning daily can rebuild momentum."
                ),
                recommendations=[
                    "Start with a quick quiz today",
                    "Set a daily learning reminder",
                ],
                priority="low",
                impact_score=0.5,
            ))

        # Quiz performance
        if metrics.avg_quiz_score >= 85:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="Quiz Expert!",
                message=f"{metrics.avg_quiz_score:.0f}% average quiz score!",
                detailed_explanation=(
                    "Your quiz performance is excellent. Consider increasing difficulty "
                    "or exploring advanced topics."
                ),
                priority="medium",
                impact_score=0.6,
            ))

        # Knowledge gaps
        if metrics.weak_areas:
            weakest = metrics.weak_areas[0]
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.LEARNING_GAP,
                title="Knowledge Gap Identified",
                message=f"Focus needed in {weakest['topic']}",
                detailed_explanation=(
                    f"Your accuracy in {weakest['topic']} is {weakest['accuracy']*100:.0f}%. "
                    "Targeted study can quickly improve this area."
                ),
                recommendations=[
                    f"Review {weakest['topic']} learning materials",
                    f"Take quizzes on {weakest['topic']}",
                    f"Query Dora about {weakest['topic']} cases",
                ],
                related_topics=[weakest['topic']],
                priority="medium",
                impact_score=0.7,
            ))

        return insights

    def _generate_comparison_insights(
        self,
        user_id: str,
        comparison: ComparisonMetrics,
    ) -> List[InsightReport]:
        """Generate insights from peer comparisons."""
        insights = []

        # Overall excellence
        if comparison.overall_percentile >= 90:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.ACHIEVEMENT,
                title="Top 10% Performer!",
                message=f"You rank in the top 10% among {comparison.peer_group_description}!",
                detailed_explanation=(
                    "Your overall performance exceeds 90% of your peers. "
                    "Your dedication to excellence is evident!"
                ),
                priority="high",
                impact_score=1.0,
            ))

        # Highlight strengths
        if comparison.strengths:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.BEST_PRACTICE,
                title="Your Strengths",
                message="Areas where you excel compared to peers:",
                detailed_explanation="\n• ".join([""] + comparison.strengths),
                priority="low",
                impact_score=0.5,
            ))

        # Improvement opportunities
        if comparison.opportunities:
            insights.append(InsightReport(
                user_id=user_id,
                category=InsightCategory.RECOMMENDATION,
                title="Growth Opportunities",
                message="Areas for potential improvement:",
                detailed_explanation="\n• ".join([""] + comparison.opportunities),
                recommendations=comparison.opportunities,
                priority="medium",
                impact_score=0.6,
            ))

        return insights

    def _generate_trend_insights(
        self,
        user_id: str,
        trends: List[TrendData],
    ) -> List[InsightReport]:
        """Generate insights from trend data."""
        insights = []

        for trend in trends:
            # Significant increasing trend
            if trend.trend_percentage > 20:
                insights.append(InsightReport(
                    user_id=user_id,
                    category=InsightCategory.TREND,
                    title=f"Growing {trend.metric_name.replace('_', ' ').title()}",
                    message=f"{trend.metric_name.replace('_', ' ').title()} increased by {trend.trend_percentage:.0f}%!",
                    detailed_explanation=(
                        f"Your {trend.metric_name.replace('_', ' ')} shows strong upward momentum. "
                        "Keep up this positive trend!"
                    ),
                    priority="low",
                    impact_score=0.5,
                    metric_name=trend.metric_name,
                    metric_value=trend.mean_value,
                ))

            # Concerning decreasing trend
            elif trend.trend_percentage < -20:
                insights.append(InsightReport(
                    user_id=user_id,
                    category=InsightCategory.WARNING,
                    title=f"Declining {trend.metric_name.replace('_', ' ').title()}",
                    message=f"{trend.metric_name.replace('_', ' ').title()} decreased by {abs(trend.trend_percentage):.0f}%",
                    detailed_explanation=(
                        f"Your {trend.metric_name.replace('_', ' ')} is trending downward. "
                        "Consider adjusting your approach to maintain engagement."
                    ),
                    recommendations=[
                        "Review what changed in your routine",
                        "Set reminders to maintain consistency",
                    ],
                    priority="medium",
                    impact_score=0.6,
                ))

        return insights


__all__ = ["InsightGenerator"]
