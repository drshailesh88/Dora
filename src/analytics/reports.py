"""
Analytics Report Generation

Generates comprehensive practice reports:
- Daily summaries
- Weekly digests
- Monthly reports (PDF)
- Annual reviews
- Custom date ranges
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .models import MonthlyReport, InsightReport
from .query_patterns import QueryPatternAnalyzer
from .prescriptions import PrescriptionAnalyzer
from .learning import LearningAnalyzer
from .comparisons import PeerComparisonAnalyzer
from .insights import InsightGenerator
from .visualizations import ChartDataFormatter


class ReportGenerator:
    """
    Generates practice analytics reports.

    Report types:
    - Daily summary
    - Weekly digest
    - Monthly comprehensive report
    - Annual review
    - Custom date range
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for report outputs
        """
        self.output_dir = output_dir or Path.home() / ".dora" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize analyzers
        self.query_analyzer = QueryPatternAnalyzer()
        self.prescription_analyzer = PrescriptionAnalyzer()
        self.learning_analyzer = LearningAnalyzer()
        self.comparison_analyzer = PeerComparisonAnalyzer()
        self.insight_generator = InsightGenerator()
        self.chart_formatter = ChartDataFormatter()

    def generate_daily_summary(
        self,
        user_id: str,
        target_date: Optional[date] = None,
    ) -> dict:
        """
        Generate daily practice summary.

        Args:
            user_id: User identifier
            target_date: Date to summarize (default: yesterday)

        Returns:
            Dict with daily summary
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        # Get analytics for the day
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, target_date, target_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, target_date, target_date
        )

        # Format summary
        summary = {
            'date': target_date.isoformat(),
            'queries': query_analytics.total_queries,
            'voice_queries': query_analytics.voice_queries,
            'cme_credits_earned': learning_metrics.total_cme_credits,
            'quizzes_completed': learning_metrics.quizzes_attempted,
            'current_streak': learning_metrics.current_streak,
            'top_topic': (
                query_analytics.top_topics[0]['topic']
                if query_analytics.top_topics else None
            ),
            'highlights': self._generate_daily_highlights(
                query_analytics,
                learning_metrics,
            ),
        }

        return summary

    def generate_weekly_digest(
        self,
        user_id: str,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Generate weekly practice digest.

        Args:
            user_id: User identifier
            end_date: End of week (default: yesterday)

        Returns:
            Dict with weekly digest
        """
        if not end_date:
            end_date = date.today() - timedelta(days=1)

        start_date = end_date - timedelta(days=6)

        # Get analytics
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        # Weekly trends
        query_trend = self.query_analyzer.get_query_trends(
            user_id, start_date, end_date
        )

        digest = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'summary': {
                'total_queries': query_analytics.total_queries,
                'avg_queries_per_day': query_analytics.total_queries / 7,
                'total_cme_credits': learning_metrics.total_cme_credits,
                'active_days': learning_metrics.total_learning_time_hours > 0,
                'current_streak': learning_metrics.current_streak,
            },
            'top_topics': query_analytics.top_topics[:5],
            'quiz_performance': {
                'attempted': learning_metrics.quizzes_attempted,
                'passed': learning_metrics.quizzes_passed,
                'avg_score': learning_metrics.avg_quiz_score,
            },
            'trends': {
                'query_trend': query_trend.trend_direction,
                'query_change_pct': query_trend.trend_percentage,
            },
            'highlights': self._generate_weekly_highlights(
                query_analytics,
                learning_metrics,
            ),
        }

        return digest

    def generate_monthly_report(
        self,
        user_id: str,
        month: Optional[int] = None,
        year: Optional[int] = None,
        generate_pdf: bool = True,
    ) -> MonthlyReport:
        """
        Generate comprehensive monthly report.

        Args:
            user_id: User identifier
            month: Month (1-12, default: last month)
            year: Year (default: current year)
            generate_pdf: Whether to generate PDF

        Returns:
            MonthlyReport object
        """
        # Default to last month
        if not month or not year:
            last_month = date.today().replace(day=1) - timedelta(days=1)
            month = last_month.month
            year = last_month.year

        # Calculate date range
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # Get all analytics
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        prescription_patterns = self.prescription_analyzer.analyze_prescriptions(
            user_id, start_date, end_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        # Get comparison (would need peer data in production)
        comparison_metrics = None  # self.comparison_analyzer.compare_with_peers(...)

        # Generate insights
        insights = self.insight_generator.generate_insights(
            user_id=user_id,
            query_analytics=query_analytics,
            prescription_patterns=prescription_patterns,
            learning_metrics=learning_metrics,
            comparison_metrics=comparison_metrics,
        )

        # Get trends
        query_trend = self.query_analyzer.get_query_trends(
            user_id, start_date, end_date
        )

        # Key achievements
        achievements = self._extract_achievements(insights)
        milestones = self._extract_milestones(insights)

        # Top topics and medications
        top_topics = [t['topic'] for t in query_analytics.top_topics[:10]]
        top_medications = [
            m['drug'] for m in prescription_patterns.most_prescribed_drugs[:10]
        ]

        # Create report
        report = MonthlyReport(
            user_id=user_id,
            month=month,
            year=year,
            total_queries=query_analytics.total_queries,
            total_prescriptions=prescription_patterns.total_prescriptions,
            total_cme_credits=learning_metrics.total_cme_credits,
            active_days=learning_metrics.total_learning_time_hours,  # Simplified
            key_achievements=achievements,
            milestones_reached=milestones,
            query_analytics=query_analytics,
            prescription_patterns=prescription_patterns,
            learning_metrics=learning_metrics,
            comparison_metrics=comparison_metrics,
            insights=insights[:10],  # Top 10 insights
            trends=[query_trend],
            top_topics_studied=top_topics,
            top_medications_prescribed=top_medications,
        )

        # Save JSON report
        report_path = self.output_dir / f"monthly_report_{year}_{month:02d}_{user_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)

        # Generate PDF if requested
        if generate_pdf:
            pdf_path = self._generate_pdf_report(report)
            report.pdf_path = str(pdf_path)

        return report

    def generate_annual_review(
        self,
        user_id: str,
        year: Optional[int] = None,
    ) -> dict:
        """
        Generate annual practice review.

        Args:
            user_id: User identifier
            year: Year (default: last year)

        Returns:
            Dict with annual review
        """
        if not year:
            year = date.today().year - 1

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Get full year analytics
        query_analytics = self.query_analyzer.analyze_queries(
            user_id, start_date, end_date
        )

        learning_metrics = self.learning_analyzer.analyze_learning(
            user_id, start_date, end_date
        )

        # Monthly breakdown
        monthly_stats = []
        for month in range(1, 13):
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year, 12, 31)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)

            month_analytics = self.query_analyzer.analyze_queries(
                user_id, month_start, month_end
            )

            monthly_stats.append({
                'month': month,
                'queries': month_analytics.total_queries,
                'cme_credits': learning_metrics.total_cme_credits / 12,  # Simplified
            })

        review = {
            'year': year,
            'summary': {
                'total_queries': query_analytics.total_queries,
                'total_cme_credits': learning_metrics.total_cme_credits,
                'total_quizzes': learning_metrics.quizzes_attempted,
                'longest_streak': learning_metrics.longest_streak,
            },
            'monthly_breakdown': monthly_stats,
            'top_topics': query_analytics.top_topics[:20],
            'achievements': learning_metrics.achievements_earned,
            'level': learning_metrics.current_level,
        }

        return review

    def generate_custom_report(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        include_sections: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate custom date range report.

        Args:
            user_id: User identifier
            start_date: Start date
            end_date: End date
            include_sections: Sections to include

        Returns:
            Dict with custom report
        """
        if not include_sections:
            include_sections = ['queries', 'prescriptions', 'learning']

        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days + 1,
            },
        }

        if 'queries' in include_sections:
            query_analytics = self.query_analyzer.analyze_queries(
                user_id, start_date, end_date
            )
            report['queries'] = query_analytics.model_dump()

        if 'prescriptions' in include_sections:
            prescription_patterns = self.prescription_analyzer.analyze_prescriptions(
                user_id, start_date, end_date
            )
            report['prescriptions'] = prescription_patterns.model_dump()

        if 'learning' in include_sections:
            learning_metrics = self.learning_analyzer.analyze_learning(
                user_id, start_date, end_date
            )
            report['learning'] = learning_metrics.model_dump()

        return report

    def export_to_csv(
        self,
        report_data: dict,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Export report data to CSV.

        Args:
            report_data: Report data dict
            output_path: Output CSV path

        Returns:
            Path to generated CSV
        """
        import csv

        if not output_path:
            output_path = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Flatten report data for CSV
        # This is simplified - production version would handle nested structures
        with open(output_path, 'w', newline='') as f:
            if report_data:
                writer = csv.DictWriter(f, fieldnames=report_data.keys())
                writer.writeheader()
                writer.writerow(report_data)

        return output_path

    def _generate_pdf_report(self, report: MonthlyReport) -> Path:
        """
        Generate PDF version of monthly report.

        Args:
            report: MonthlyReport object

        Returns:
            Path to generated PDF
        """
        # PDF generation would use reportlab or similar
        # For now, just create a placeholder

        pdf_path = self.output_dir / f"monthly_report_{report.year}_{report.month:02d}_{report.user_id}.pdf"

        # In production, would generate actual PDF with:
        # - Cover page
        # - Summary statistics
        # - Charts and graphs
        # - Detailed analytics
        # - Insights and recommendations

        # Placeholder: write text summary
        with open(pdf_path, 'w') as f:
            f.write(f"Monthly Practice Report - {report.year}/{report.month:02d}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Queries: {report.total_queries}\n")
            f.write(f"Total Prescriptions: {report.total_prescriptions}\n")
            f.write(f"CME Credits: {report.total_cme_credits}\n\n")
            f.write("Key Achievements:\n")
            for achievement in report.key_achievements:
                f.write(f"  • {achievement}\n")

        return pdf_path

    def _generate_daily_highlights(self, query_analytics, learning_metrics) -> list[str]:
        """Generate daily highlights."""
        highlights = []

        if query_analytics.total_queries > 10:
            highlights.append(f"Highly active day with {query_analytics.total_queries} queries!")

        if learning_metrics.total_cme_credits > 0:
            highlights.append(f"Earned {learning_metrics.total_cme_credits:.1f} CME credits")

        if learning_metrics.quizzes_passed > 0:
            highlights.append(f"Passed {learning_metrics.quizzes_passed} quiz(zes)")

        return highlights

    def _generate_weekly_highlights(self, query_analytics, learning_metrics) -> list[str]:
        """Generate weekly highlights."""
        highlights = []

        if query_analytics.total_queries >= 50:
            highlights.append("Exceptional engagement this week!")

        if learning_metrics.current_streak >= 7:
            highlights.append(f"Maintained {learning_metrics.current_streak}-day streak!")

        if learning_metrics.total_cme_credits >= 2:
            highlights.append(f"Earned {learning_metrics.total_cme_credits:.1f} CME credits")

        return highlights

    def _extract_achievements(self, insights: list[InsightReport]) -> list[str]:
        """Extract achievement insights."""
        from .models import InsightCategory

        return [
            i.message
            for i in insights
            if i.category == InsightCategory.ACHIEVEMENT
        ]

    def _extract_milestones(self, insights: list[InsightReport]) -> list[str]:
        """Extract milestone insights."""
        from .models import InsightCategory

        return [
            i.message
            for i in insights
            if i.category == InsightCategory.MILESTONE
        ]


__all__ = ["ReportGenerator"]
