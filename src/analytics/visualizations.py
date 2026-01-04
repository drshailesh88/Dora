"""
Chart Data Formatting

Formats analytics data for visualization libraries:
- Time series data
- Pie charts
- Bar charts
- Heatmaps
- Sankey diagrams
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from .models import (
    QueryAnalytics,
    PrescriptionPatterns,
    LearningMetrics,
    TrendData,
    TimeGranularity,
)


class ChartDataFormatter:
    """
    Formats analytics data for chart libraries (Recharts, Chart.js, etc.).

    Provides data structures optimized for:
    - Web dashboards (Recharts/React)
    - Desktop UI (Matplotlib/Plotly)
    - Mobile apps (Charts library)
    """

    def __init__(self):
        """Initialize chart data formatter."""
        pass

    def format_time_series(
        self,
        trend_data: TrendData,
        date_format: str = "%Y-%m-%d",
    ) -> List[Dict[str, Any]]:
        """
        Format time series data for line/area charts.

        Args:
            trend_data: TrendData object
            date_format: Date format string

        Returns:
            List of {date, value} dicts
        """
        formatted = []

        for point in trend_data.data_points:
            formatted.append({
                'date': point['date'],
                'value': point['value'],
                'label': point['date'],  # For tooltip
            })

        return formatted

    def format_query_volume_chart(
        self,
        trend_data: TrendData,
    ) -> Dict[str, Any]:
        """
        Format query volume data for area chart.

        Args:
            trend_data: Query volume trend data

        Returns:
            Chart configuration dict
        """
        return {
            'type': 'area',
            'title': 'Query Volume Over Time',
            'data': self.format_time_series(trend_data),
            'xAxis': {
                'dataKey': 'date',
                'label': 'Date',
            },
            'yAxis': {
                'dataKey': 'value',
                'label': 'Queries',
            },
            'tooltip': {
                'enabled': True,
            },
            'color': '#3b82f6',  # Blue
        }

    def format_specialty_pie_chart(
        self,
        query_analytics: QueryAnalytics,
    ) -> Dict[str, Any]:
        """
        Format specialty distribution for pie chart.

        Args:
            query_analytics: QueryAnalytics object

        Returns:
            Pie chart configuration dict
        """
        data = []

        for specialty, count in query_analytics.specialty_distribution.items():
            percentage = (count / query_analytics.total_queries * 100
                         if query_analytics.total_queries > 0 else 0)
            data.append({
                'name': specialty.title(),
                'value': count,
                'percentage': round(percentage, 1),
            })

        # Sort by value descending
        data.sort(key=lambda x: x['value'], reverse=True)

        return {
            'type': 'pie',
            'title': 'Queries by Specialty',
            'data': data,
            'colors': [
                '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
                '#10b981', '#6366f1', '#14b8a6', '#f97316'
            ],
        }

    def format_drug_class_bar_chart(
        self,
        prescription_patterns: PrescriptionPatterns,
    ) -> Dict[str, Any]:
        """
        Format drug class distribution for bar chart.

        Args:
            prescription_patterns: PrescriptionPatterns object

        Returns:
            Bar chart configuration dict
        """
        data = [
            {
                'class': item['class'],
                'count': item['count'],
                'percentage': round(item['percentage'], 1),
            }
            for item in prescription_patterns.top_drug_classes
        ]

        return {
            'type': 'bar',
            'title': 'Top Drug Classes Prescribed',
            'data': data,
            'xAxis': {
                'dataKey': 'class',
                'label': 'Drug Class',
            },
            'yAxis': {
                'dataKey': 'count',
                'label': 'Prescriptions',
            },
            'color': '#10b981',  # Green
        }

    def format_cme_progress_chart(
        self,
        learning_metrics: LearningMetrics,
        annual_goal: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Format CME progress for radial/gauge chart.

        Args:
            learning_metrics: LearningMetrics object
            annual_goal: Annual CME goal

        Returns:
            Gauge chart configuration dict
        """
        percentage = (learning_metrics.total_cme_credits / annual_goal * 100
                     if annual_goal > 0 else 0)

        return {
            'type': 'gauge',
            'title': 'CME Progress',
            'data': {
                'current': learning_metrics.total_cme_credits,
                'goal': annual_goal,
                'percentage': min(percentage, 100),
            },
            'color': '#8b5cf6',  # Purple
            'ranges': [
                {'min': 0, 'max': 50, 'color': '#ef4444'},    # Red (behind)
                {'min': 50, 'max': 80, 'color': '#f59e0b'},   # Orange (on track)
                {'min': 80, 'max': 100, 'color': '#10b981'},  # Green (ahead)
            ],
        }

    def format_quiz_performance_chart(
        self,
        learning_metrics: LearningMetrics,
    ) -> Dict[str, Any]:
        """
        Format quiz performance by topic for bar chart.

        Args:
            learning_metrics: LearningMetrics object

        Returns:
            Bar chart configuration dict
        """
        data = []

        for topic, accuracy in learning_metrics.quiz_accuracy_by_topic.items():
            data.append({
                'topic': topic.title()[:20],  # Truncate long names
                'accuracy': round(accuracy * 100, 1),
            })

        # Sort by accuracy
        data.sort(key=lambda x: x['accuracy'])

        return {
            'type': 'bar',
            'title': 'Quiz Performance by Topic',
            'data': data[-10:],  # Top 10
            'xAxis': {
                'dataKey': 'topic',
                'label': 'Topic',
            },
            'yAxis': {
                'dataKey': 'accuracy',
                'label': 'Accuracy (%)',
            },
            'color': '#6366f1',  # Indigo
        }

    def format_activity_heatmap(
        self,
        start_date: date,
        end_date: date,
        daily_counts: Dict[date, int],
    ) -> Dict[str, Any]:
        """
        Format activity heatmap (GitHub-style).

        Args:
            start_date: Start date
            end_date: End date
            daily_counts: Dict mapping date to activity count

        Returns:
            Heatmap configuration dict
        """
        data = []
        current_date = start_date

        while current_date <= end_date:
            count = daily_counts.get(current_date, 0)

            # Determine intensity level (0-4)
            if count == 0:
                level = 0
            elif count <= 2:
                level = 1
            elif count <= 5:
                level = 2
            elif count <= 10:
                level = 3
            else:
                level = 4

            data.append({
                'date': current_date.isoformat(),
                'count': count,
                'level': level,
                'weekday': current_date.weekday(),
                'week': current_date.isocalendar()[1],
            })

            current_date += timedelta(days=1)

        return {
            'type': 'heatmap',
            'title': 'Learning Activity',
            'data': data,
            'colors': {
                0: '#ebedf0',  # Gray (no activity)
                1: '#c6e48b',  # Light green
                2: '#7bc96f',  # Medium green
                3: '#239a3b',  # Dark green
                4: '#196127',  # Darkest green
            },
        }

    def format_comparison_radar_chart(
        self,
        user_metrics: Dict[str, float],
        peer_avg: Dict[str, float],
        metrics_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Format peer comparison for radar chart.

        Args:
            user_metrics: User's metric values (0-100)
            peer_avg: Peer average values (0-100)
            metrics_labels: Metric labels

        Returns:
            Radar chart configuration dict
        """
        if not metrics_labels:
            metrics_labels = list(user_metrics.keys())

        data = []

        for label in metrics_labels:
            data.append({
                'metric': label.replace('_', ' ').title(),
                'user': user_metrics.get(label, 0),
                'peer_avg': peer_avg.get(label, 0),
            })

        return {
            'type': 'radar',
            'title': 'Performance vs Peers',
            'data': data,
            'series': [
                {
                    'name': 'You',
                    'dataKey': 'user',
                    'color': '#3b82f6',
                },
                {
                    'name': 'Peer Average',
                    'dataKey': 'peer_avg',
                    'color': '#94a3b8',
                },
            ],
        }

    def format_prescription_safety_donut(
        self,
        prescription_patterns: PrescriptionPatterns,
    ) -> Dict[str, Any]:
        """
        Format prescription safety metrics for donut chart.

        Args:
            prescription_patterns: PrescriptionPatterns object

        Returns:
            Donut chart configuration dict
        """
        total = prescription_patterns.total_prescriptions

        data = [
            {
                'name': 'Safe',
                'value': total - prescription_patterns.drug_interactions_detected,
                'color': '#10b981',
            },
            {
                'name': 'Interactions',
                'value': prescription_patterns.drug_interactions_detected,
                'color': '#f59e0b',
            },
            {
                'name': 'Allergy Alerts',
                'value': prescription_patterns.allergy_alerts_triggered,
                'color': '#ef4444',
            },
        ]

        return {
            'type': 'donut',
            'title': 'Prescription Safety',
            'data': data,
            'centerText': f'{prescription_patterns.safety_score:.1%}',
            'centerSubtext': 'Safety Score',
        }

    def format_streak_calendar(
        self,
        start_date: date,
        end_date: date,
        active_dates: List[date],
    ) -> Dict[str, Any]:
        """
        Format learning streak calendar.

        Args:
            start_date: Start date
            end_date: End date
            active_dates: List of dates with activity

        Returns:
            Calendar visualization data
        """
        active_set = set(active_dates)
        data = []

        current_date = start_date
        while current_date <= end_date:
            data.append({
                'date': current_date.isoformat(),
                'active': current_date in active_set,
                'weekday': current_date.weekday(),
                'day': current_date.day,
            })
            current_date += timedelta(days=1)

        return {
            'type': 'calendar',
            'title': 'Learning Streak',
            'data': data,
            'colors': {
                'active': '#10b981',
                'inactive': '#e5e7eb',
            },
        }

    def format_topic_sankey(
        self,
        query_analytics: QueryAnalytics,
    ) -> Dict[str, Any]:
        """
        Format query flow from specialty to topic (Sankey diagram).

        Args:
            query_analytics: QueryAnalytics object

        Returns:
            Sankey diagram data
        """
        nodes = []
        links = []

        # Add specialty nodes
        specialty_map = {}
        for idx, (specialty, count) in enumerate(query_analytics.specialty_distribution.items()):
            specialty_map[specialty] = idx
            nodes.append({
                'id': idx,
                'name': specialty.title(),
            })

        # Add topic nodes
        topic_map = {}
        topic_start_idx = len(nodes)
        for idx, topic_data in enumerate(query_analytics.top_topics[:10]):
            topic_id = topic_start_idx + idx
            topic_map[topic_data['topic']] = topic_id
            nodes.append({
                'id': topic_id,
                'name': topic_data['topic'].title(),
            })

            # Create link (simplified - assumes topic belongs to primary specialty)
            # In production, would track actual specialty->topic relationships
            links.append({
                'source': 0,  # Simplified: link to first specialty
                'target': topic_id,
                'value': topic_data['count'],
            })

        return {
            'type': 'sankey',
            'title': 'Query Flow: Specialty → Topic',
            'nodes': nodes,
            'links': links,
        }

    def format_dashboard_summary_cards(
        self,
        query_analytics: QueryAnalytics,
        prescription_patterns: Optional[PrescriptionPatterns],
        learning_metrics: LearningMetrics,
    ) -> List[Dict[str, Any]]:
        """
        Format summary cards for dashboard.

        Args:
            query_analytics: QueryAnalytics object
            prescription_patterns: PrescriptionPatterns object
            learning_metrics: LearningMetrics object

        Returns:
            List of card configurations
        """
        cards = [
            {
                'title': 'Queries',
                'value': query_analytics.total_queries,
                'subtitle': 'this month',
                'icon': '🔍',
                'trend': None,  # Would calculate from previous period
                'color': 'blue',
            },
            {
                'title': 'CME Credits',
                'value': f"{learning_metrics.total_cme_credits:.1f}",
                'subtitle': f"{learning_metrics.percentage_of_annual_goal:.0f}% of goal",
                'icon': '🎓',
                'trend': None,
                'color': 'purple',
            },
            {
                'title': 'Current Streak',
                'value': learning_metrics.current_streak,
                'subtitle': 'days',
                'icon': '🔥',
                'trend': None,
                'color': 'orange',
            },
            {
                'title': 'Quiz Score',
                'value': f"{learning_metrics.avg_quiz_score:.0f}%",
                'subtitle': f"{learning_metrics.quizzes_attempted} attempted",
                'icon': '📝',
                'trend': None,
                'color': 'green',
            },
        ]

        if prescription_patterns:
            cards.insert(1, {
                'title': 'Prescriptions',
                'value': prescription_patterns.total_prescriptions,
                'subtitle': f"{prescription_patterns.generic_percentage:.0f}% generic",
                'icon': '💊',
                'trend': None,
                'color': 'indigo',
            })

        return cards


__all__ = ["ChartDataFormatter"]
