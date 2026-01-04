"""
Peer Comparison Analytics

Anonymous benchmarking against similar doctors:
- Same specialty
- Same region
- Same experience level
- Performance percentiles
"""

from datetime import date
from typing import Optional, List
import statistics

from .models import ComparisonMetrics, ComparisonType


class PeerComparisonAnalyzer:
    """
    Provides anonymous peer comparison analytics.

    Privacy-preserving comparison against:
    - Same specialty peers
    - Same region peers
    - Same experience level
    - All users (aggregate)
    """

    def __init__(self):
        """Initialize peer comparison analyzer."""
        pass

    def compare_with_peers(
        self,
        user_id: str,
        comparison_type: ComparisonType,
        start_date: date,
        end_date: date,
        user_specialty: Optional[str] = None,
        user_region: Optional[str] = None,
        user_experience_years: Optional[int] = None,
        user_metrics: Optional[dict] = None,
        peer_data: Optional[List[dict]] = None,
    ) -> ComparisonMetrics:
        """
        Compare user metrics with peers.

        Args:
            user_id: User identifier
            comparison_type: Type of peer group comparison
            start_date: Start of period
            end_date: End of period
            user_specialty: User's specialty
            user_region: User's region
            user_experience_years: Years of experience
            user_metrics: User's metrics dict
            peer_data: List of peer metrics (anonymized)

        Returns:
            ComparisonMetrics with benchmarking data
        """
        if not user_metrics:
            user_metrics = {}

        if not peer_data:
            peer_data = []

        # Filter peer data based on comparison type
        filtered_peers = self._filter_peers(
            peer_data,
            comparison_type,
            user_specialty,
            user_region,
            user_experience_years,
        )

        # Extract user metrics
        user_queries = user_metrics.get('total_queries', 0)
        user_generic_rate = user_metrics.get('generic_percentage', 0.0)
        user_cme_credits = user_metrics.get('total_cme_credits', 0.0)
        user_quiz_accuracy = user_metrics.get('avg_quiz_score', 0.0)
        user_streak = user_metrics.get('current_streak', 0)
        user_safety = user_metrics.get('safety_score', 1.0)

        # Calculate peer statistics
        peer_queries = [p.get('total_queries', 0) for p in filtered_peers]
        peer_generic_rates = [p.get('generic_percentage', 0.0) for p in filtered_peers]
        peer_cme = [p.get('total_cme_credits', 0.0) for p in filtered_peers]
        peer_quiz = [p.get('avg_quiz_score', 0.0) for p in filtered_peers]
        peer_streaks = [p.get('current_streak', 0) for p in filtered_peers]
        peer_safety = [p.get('safety_score', 1.0) for p in filtered_peers]

        # Peer group description
        peer_group_desc = self._get_peer_group_description(
            comparison_type,
            user_specialty,
            user_region,
            user_experience_years,
        )

        # Calculate percentiles
        queries_percentile = self._calculate_percentile(user_queries, peer_queries)
        generic_percentile = self._calculate_percentile(user_generic_rate, peer_generic_rates)
        cme_percentile = self._calculate_percentile(user_cme_credits, peer_cme)
        quiz_percentile = self._calculate_percentile(user_quiz_accuracy, peer_quiz)
        streak_percentile = self._calculate_percentile(user_streak, peer_streaks)
        safety_percentile = self._calculate_percentile(user_safety, peer_safety)

        # Overall rank (simple average of percentiles)
        all_percentiles = [
            queries_percentile,
            generic_percentile,
            cme_percentile,
            quiz_percentile,
            streak_percentile,
            safety_percentile,
        ]
        overall_percentile = sum(all_percentiles) / len(all_percentiles)
        overall_rank = int((100 - overall_percentile) / 100 * len(filtered_peers)) + 1

        # Identify strengths and opportunities
        strengths = self._identify_strengths(
            queries_percentile,
            generic_percentile,
            cme_percentile,
            quiz_percentile,
            streak_percentile,
            safety_percentile,
        )

        opportunities = self._identify_opportunities(
            queries_percentile,
            generic_percentile,
            cme_percentile,
            quiz_percentile,
            streak_percentile,
            safety_percentile,
        )

        return ComparisonMetrics(
            user_id=user_id,
            comparison_type=comparison_type,
            period_start=start_date,
            period_end=end_date,
            peer_group_size=len(filtered_peers),
            peer_group_description=peer_group_desc,
            user_queries=user_queries,
            peer_avg_queries=self._safe_mean(peer_queries),
            peer_median_queries=self._safe_median(peer_queries),
            peer_top_10_percent_queries=self._top_10_percent(peer_queries),
            queries_percentile=queries_percentile,
            user_generic_rate=user_generic_rate,
            peer_avg_generic_rate=self._safe_mean(peer_generic_rates),
            peer_top_10_percent_generic_rate=self._top_10_percent(peer_generic_rates),
            generic_rate_percentile=generic_percentile,
            user_cme_credits=user_cme_credits,
            peer_avg_cme_credits=self._safe_mean(peer_cme),
            peer_top_10_percent_cme_credits=self._top_10_percent(peer_cme),
            cme_percentile=cme_percentile,
            user_quiz_accuracy=user_quiz_accuracy,
            peer_avg_quiz_accuracy=self._safe_mean(peer_quiz),
            peer_top_10_percent_quiz_accuracy=self._top_10_percent(peer_quiz),
            quiz_accuracy_percentile=quiz_percentile,
            user_current_streak=user_streak,
            peer_avg_streak=self._safe_mean(peer_streaks),
            peer_top_10_percent_streak=self._top_10_percent(peer_streaks),
            streak_percentile=streak_percentile,
            user_safety_score=user_safety,
            peer_avg_safety_score=self._safe_mean(peer_safety),
            safety_percentile=safety_percentile,
            overall_rank=overall_rank,
            overall_percentile=overall_percentile,
            strengths=strengths,
            opportunities=opportunities,
        )

    def _filter_peers(
        self,
        peer_data: List[dict],
        comparison_type: ComparisonType,
        user_specialty: Optional[str],
        user_region: Optional[str],
        user_experience: Optional[int],
    ) -> List[dict]:
        """Filter peers based on comparison type."""
        if comparison_type == ComparisonType.ALL_USERS:
            return peer_data

        filtered = []

        for peer in peer_data:
            if comparison_type == ComparisonType.SAME_SPECIALTY:
                if peer.get('specialty') == user_specialty:
                    filtered.append(peer)

            elif comparison_type == ComparisonType.SAME_REGION:
                if peer.get('region') == user_region:
                    filtered.append(peer)

            elif comparison_type == ComparisonType.SAME_EXPERIENCE:
                peer_exp = peer.get('experience_years', 0)
                if user_experience and abs(peer_exp - user_experience) <= 3:
                    filtered.append(peer)

        return filtered if filtered else peer_data  # Fallback to all if no matches

    def _get_peer_group_description(
        self,
        comparison_type: ComparisonType,
        specialty: Optional[str],
        region: Optional[str],
        experience: Optional[int],
    ) -> str:
        """Generate peer group description."""
        if comparison_type == ComparisonType.SAME_SPECIALTY:
            return f"{specialty} specialists" if specialty else "Similar specialty"

        elif comparison_type == ComparisonType.SAME_REGION:
            return f"Doctors in {region}" if region else "Same region"

        elif comparison_type == ComparisonType.SAME_EXPERIENCE:
            return f"~{experience} years experience" if experience else "Similar experience"

        else:
            return "All Dora users"

    def _calculate_percentile(self, user_value: float, peer_values: List[float]) -> float:
        """Calculate user's percentile rank (0-100)."""
        if not peer_values:
            return 50.0

        # Count how many peers user beats
        beats_count = sum(1 for p in peer_values if user_value >= p)
        percentile = (beats_count / len(peer_values)) * 100 if peer_values else 50.0

        return percentile

    def _safe_mean(self, values: List[float]) -> float:
        """Calculate mean, handling empty list."""
        return statistics.mean(values) if values else 0.0

    def _safe_median(self, values: List[float]) -> float:
        """Calculate median, handling empty list."""
        return statistics.median(values) if values else 0.0

    def _top_10_percent(self, values: List[float]) -> float:
        """Get top 10% threshold."""
        if not values:
            return 0.0

        sorted_values = sorted(values, reverse=True)
        index = max(0, int(len(sorted_values) * 0.1) - 1)
        return sorted_values[index]

    def _identify_strengths(
        self,
        queries_pct: float,
        generic_pct: float,
        cme_pct: float,
        quiz_pct: float,
        streak_pct: float,
        safety_pct: float,
    ) -> List[str]:
        """Identify user's strengths (top 25% areas)."""
        strengths = []

        if queries_pct >= 75:
            strengths.append("High engagement with medical queries")

        if generic_pct >= 75:
            strengths.append("Excellent generic medication prescribing")

        if cme_pct >= 75:
            strengths.append("Strong commitment to continuing education")

        if quiz_pct >= 75:
            strengths.append("Superior quiz performance")

        if streak_pct >= 75:
            strengths.append("Consistent daily learning habit")

        if safety_pct >= 75:
            strengths.append("Exemplary prescription safety")

        return strengths

    def _identify_opportunities(
        self,
        queries_pct: float,
        generic_pct: float,
        cme_pct: float,
        quiz_pct: float,
        streak_pct: float,
        safety_pct: float,
    ) -> List[str]:
        """Identify improvement opportunities (bottom 25% areas)."""
        opportunities = []

        if queries_pct < 25:
            opportunities.append("Increase engagement with Dora's knowledge base")

        if generic_pct < 25:
            opportunities.append("Consider prescribing more generic medications")

        if cme_pct < 25:
            opportunities.append("Accelerate CME credit accumulation")

        if quiz_pct < 25:
            opportunities.append("Review weak topics and retake quizzes")

        if streak_pct < 25:
            opportunities.append("Build a consistent daily learning habit")

        if safety_pct < 25:
            opportunities.append("Review prescription safety alerts more carefully")

        return opportunities


__all__ = ["PeerComparisonAnalyzer"]
