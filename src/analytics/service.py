"""
Analytics Service

Main service coordinating all analytics components:
- Dashboard data retrieval
- Report generation
- Insight generation
- Peer comparison
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from .storage import AnalyticsStorage
from .collector import AnalyticsCollector
from .query_patterns import QueryPatternAnalyzer
from .prescriptions import PrescriptionAnalyzer
from .learning import LearningAnalyzer
from .comparisons import PeerComparisonAnalyzer
from .insights import InsightGenerator
from .reports import ReportGenerator
from .visualizations import ChartDataFormatter
from .models import (
    DashboardData,
    QueryAnalytics,
    UsageMetrics,
    LearningMetrics,
    TimeGranularity,
    ComparisonType,
)


class AnalyticsService:
    """
    Main analytics service orchestrating all analytics components.

    Provides high-level interface for:
    - Dashboard data
    - Reports
    - Insights
    - Comparisons
    - Visualizations
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
    ):
        """
        Initialize analytics service.

        Args:
            db_path: Path to analytics database
            reports_dir: Directory for generated reports
        """
        # Initialize storage and collection
        self.storage = AnalyticsStorage(db_path=db_path)
        self.collector = AnalyticsCollector(storage=self.storage)

        # Initialize analyzers
        self.query_analyzer = QueryPatternAnalyzer(storage=self.storage)
        self.prescription_analyzer = PrescriptionAnalyzer()
        self.learning_analyzer = LearningAnalyzer()
        self.comparison_analyzer = PeerComparisonAnalyzer()

        # Initialize generators
        self.insight_generator = InsightGenerator()
        self.report_generator = ReportGenerator(output_dir=reports_dir)
        self.chart_formatter = ChartDataFormatter()

    def get_dashboard_data(
        self,
        user_id: str,
        days: int = 30,
    ) -> DashboardData:
        """
        Get comprehensive dashboard data for a user.

        Args:
            user_id: User identifier
            days: Number of days to include (default: 30)

        Returns:
            DashboardData with all metrics and charts
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get analytics for current period
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        usage_metrics = self._get_usage_metrics(user_id, start_date, end_date)

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        prescription_patterns = self.prescription_analyzer.analyze_prescriptions(
            user_id, start_date, end_date
        )

        # Get previous period for comparison
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)

        prev_query_analytics = self.query_analyzer.analyze_queries(
            user_id, prev_start, prev_end
        )

        prev_learning = self.learning_analyzer.analyze_learning(
            user_id, prev_start, prev_end
        )

        # Calculate percentage changes
        queries_change = self._calculate_change(
            query_analytics.total_queries,
            prev_query_analytics.total_queries
        )

        prescriptions_change = self._calculate_change(
            prescription_patterns.total_prescriptions,
            0  # Would get from previous period
        )

        cme_change = self._calculate_change(
            learning_metrics.total_cme_credits,
            prev_learning.total_cme_credits
        )

        # Get trends
        query_trend = self.query_analyzer.get_query_trends(
            user_id, start_date, end_date, TimeGranularity.DAILY
        )

        # CME trend (simplified)
        cme_trend = query_trend  # Would calculate actual CME trend

        # Get recent insights
        insights = self.insight_generator.generate_insights(
            user_id=user_id,
            query_analytics=query_analytics,
            prescription_patterns=prescription_patterns,
            learning_metrics=learning_metrics,
        )

        # Format top lists
        top_specialties = [
            {'name': spec, 'count': count}
            for spec, count in sorted(
                query_analytics.specialty_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        top_medications = prescription_patterns.most_prescribed_drugs[:5]

        top_topics = query_analytics.top_topics[:5]

        return DashboardData(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            queries_this_month=query_analytics.total_queries,
            prescriptions_this_month=prescription_patterns.total_prescriptions,
            cme_credits_this_month=learning_metrics.total_cme_credits,
            current_streak=learning_metrics.current_streak,
            queries_change=queries_change,
            prescriptions_change=prescriptions_change,
            cme_change=cme_change,
            usage_metrics=usage_metrics,
            query_analytics=query_analytics,
            prescription_patterns=prescription_patterns,
            learning_metrics=learning_metrics,
            recent_insights=insights[:5],
            query_trend=query_trend,
            cme_trend=cme_trend,
            top_specialties=top_specialties,
            top_medications=top_medications,
            top_topics=top_topics,
        )

    def get_insights(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get personalized insights for a user.

        Args:
            user_id: User identifier
            days: Number of days to analyze
            limit: Maximum insights to return

        Returns:
            List of insight dicts
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get analytics
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        prescription_patterns = self.prescription_analyzer.analyze_prescriptions(
            user_id, start_date, end_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        # Generate insights
        insights = self.insight_generator.generate_insights(
            user_id=user_id,
            query_analytics=query_analytics,
            prescription_patterns=prescription_patterns,
            learning_metrics=learning_metrics,
        )

        return [i.model_dump() for i in insights[:limit]]

    def get_monthly_report(
        self,
        user_id: str,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get monthly practice report.

        Args:
            user_id: User identifier
            month: Month (1-12)
            year: Year

        Returns:
            Monthly report dict
        """
        report = self.report_generator.generate_monthly_report(
            user_id, month, year, generate_pdf=True
        )

        return report.model_dump()

    def compare_with_peers(
        self,
        user_id: str,
        comparison_type: ComparisonType = ComparisonType.SAME_SPECIALTY,
        days: int = 30,
        user_specialty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare user with peers.

        Args:
            user_id: User identifier
            comparison_type: Type of peer comparison
            days: Number of days to analyze
            user_specialty: User's specialty

        Returns:
            Comparison metrics dict
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get user metrics
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        prescription_patterns = self.prescription_analyzer.analyze_prescriptions(
            user_id, start_date, end_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        user_metrics = {
            'total_queries': query_analytics.total_queries,
            'generic_percentage': prescription_patterns.generic_percentage,
            'total_cme_credits': learning_metrics.total_cme_credits,
            'avg_quiz_score': learning_metrics.avg_quiz_score,
            'current_streak': learning_metrics.current_streak,
            'safety_score': prescription_patterns.safety_score,
        }

        # Get peer data (would fetch from database in production)
        peer_data = []  # Placeholder

        # Compare
        comparison = self.comparison_analyzer.compare_with_peers(
            user_id=user_id,
            comparison_type=comparison_type,
            start_date=start_date,
            end_date=end_date,
            user_specialty=user_specialty,
            user_metrics=user_metrics,
            peer_data=peer_data,
        )

        return comparison.model_dump()

    def get_chart_data(
        self,
        user_id: str,
        chart_type: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get formatted chart data.

        Args:
            user_id: User identifier
            chart_type: Type of chart (query_volume, specialty_pie, etc.)
            days: Number of days to include

        Returns:
            Chart configuration dict
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        if chart_type == 'query_volume':
            trend = self.query_analyzer.get_query_trends(
                user_id, start_date, end_date
            )
            return self.chart_formatter.format_query_volume_chart(trend)

        elif chart_type == 'specialty_pie':
            analytics = self.query_analyzer.analyze_queries(
                user_id, start_date, end_date
            )
            return self.chart_formatter.format_specialty_pie_chart(analytics)

        elif chart_type == 'cme_progress':
            learning = self.learning_analyzer.analyze_learning(
                user_id, start_date, end_date
            )
            return self.chart_formatter.format_cme_progress_chart(learning)

        elif chart_type == 'drug_classes':
            prescriptions = self.prescription_analyzer.analyze_prescriptions(
                user_id, start_date, end_date
            )
            return self.chart_formatter.format_drug_class_bar_chart(prescriptions)

        else:
            return {'error': f'Unknown chart type: {chart_type}'}

    def export_data(
        self,
        user_id: str,
        format: str = 'json',
        days: int = 30,
    ) -> Path:
        """
        Export analytics data.

        Args:
            user_id: User identifier
            format: Export format (json, csv)
            days: Number of days to include

        Returns:
            Path to exported file
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get all data
        dashboard_data = self.get_dashboard_data(user_id, days)

        if format == 'json':
            output_path = self.storage.export_to_json(
                Path(f"/tmp/analytics_{user_id}_{datetime.now().strftime('%Y%m%d')}.json")
            )
        elif format == 'csv':
            output_path = self.report_generator.export_to_csv(
                dashboard_data.model_dump()
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def _get_usage_metrics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> UsageMetrics:
        """Get usage metrics for a period."""
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        metrics_dict = self.collector.collect_usage_metrics(
            user_id, start_dt, end_dt
        )

        return UsageMetrics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date,
            granularity=TimeGranularity.DAILY,
            **metrics_dict
        )

    def _calculate_change(
        self,
        current: float,
        previous: float,
    ) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0

        return ((current - previous) / previous) * 100


__all__ = ["AnalyticsService"]
