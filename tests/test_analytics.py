"""
Tests for practice analytics module.
Tests query patterns, prescription analytics, and insights.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta


class TestQueryAnalytics:
    """Tests for query pattern analytics."""

    @pytest.fixture
    def query_analytics(self):
        """Create query analytics service instance."""
        from src.analytics.queries import QueryAnalyticsService
        return QueryAnalyticsService()

    @pytest.mark.asyncio
    async def test_query_count_by_period(self, query_analytics):
        """Should count queries by time period."""
        stats = await query_analytics.get_query_stats(
            doctor_id="doc_123",
            period="week",
        )

        assert "total_queries" in stats
        assert "by_day" in stats or "daily" in stats
        assert stats["total_queries"] >= 0

    @pytest.mark.asyncio
    async def test_query_topics_distribution(self, query_analytics):
        """Should analyze query topic distribution."""
        topics = await query_analytics.get_topic_distribution(
            doctor_id="doc_123",
            period="month",
        )

        assert "topics" in topics
        for topic in topics["topics"]:
            assert "name" in topic
            assert "count" in topic or "percentage" in topic

    @pytest.mark.asyncio
    async def test_query_trends(self, query_analytics):
        """Should identify query trends."""
        trends = await query_analytics.get_trends(
            doctor_id="doc_123",
            period="month",
        )

        assert "trending_up" in trends or "increasing" in trends
        assert "trending_down" in trends or "decreasing" in trends

    @pytest.mark.asyncio
    async def test_peak_usage_times(self, query_analytics):
        """Should identify peak usage times."""
        usage = await query_analytics.get_usage_patterns(
            doctor_id="doc_123",
            period="month",
        )

        assert "peak_hours" in usage or "by_hour" in usage
        assert "peak_days" in usage or "by_day" in usage


class TestPrescriptionAnalytics:
    """Tests for prescription pattern analytics."""

    @pytest.fixture
    def rx_analytics(self):
        """Create prescription analytics service instance."""
        from src.analytics.prescriptions import PrescriptionAnalyticsService
        return PrescriptionAnalyticsService()

    @pytest.mark.asyncio
    async def test_top_prescribed_drugs(self, rx_analytics):
        """Should identify top prescribed drugs."""
        top_drugs = await rx_analytics.get_top_drugs(
            doctor_id="doc_123",
            period="month",
            limit=10,
        )

        assert "drugs" in top_drugs
        assert len(top_drugs["drugs"]) <= 10

        # Should be sorted by count
        counts = [d["count"] for d in top_drugs["drugs"]]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_prescribing_by_category(self, rx_analytics):
        """Should analyze prescribing by drug category."""
        by_category = await rx_analytics.get_by_category(
            doctor_id="doc_123",
            period="month",
        )

        assert "categories" in by_category
        for cat in by_category["categories"]:
            assert "name" in cat
            assert "count" in cat or "percentage" in cat

    @pytest.mark.asyncio
    async def test_generic_vs_brand_ratio(self, rx_analytics):
        """Should calculate generic vs brand ratio."""
        ratio = await rx_analytics.get_generic_ratio(
            doctor_id="doc_123",
            period="month",
        )

        assert "generic_percentage" in ratio
        assert "brand_percentage" in ratio
        assert ratio["generic_percentage"] + ratio["brand_percentage"] == 100

    @pytest.mark.asyncio
    async def test_prescribing_trends(self, rx_analytics):
        """Should identify prescribing trends."""
        trends = await rx_analytics.get_prescribing_trends(
            doctor_id="doc_123",
            period="quarter",
        )

        assert "trends" in trends
        for trend in trends["trends"]:
            assert "drug" in trend or "category" in trend
            assert "direction" in trend  # increasing/decreasing


class TestDiagnosisAnalytics:
    """Tests for diagnosis pattern analytics."""

    @pytest.fixture
    def dx_analytics(self):
        """Create diagnosis analytics service instance."""
        from src.analytics.diagnoses import DiagnosisAnalyticsService
        return DiagnosisAnalyticsService()

    @pytest.mark.asyncio
    async def test_top_diagnoses(self, dx_analytics):
        """Should identify top diagnoses."""
        top_dx = await dx_analytics.get_top_diagnoses(
            doctor_id="doc_123",
            period="month",
            limit=20,
        )

        assert "diagnoses" in top_dx
        for dx in top_dx["diagnoses"]:
            assert "name" in dx or "icd10" in dx
            assert "count" in dx

    @pytest.mark.asyncio
    async def test_diagnosis_by_specialty(self, dx_analytics):
        """Should group diagnoses by specialty alignment."""
        by_specialty = await dx_analytics.get_specialty_alignment(
            doctor_id="doc_123",
            doctor_specialty="cardiology",
            period="month",
        )

        assert "in_specialty" in by_specialty
        assert "out_of_specialty" in by_specialty

    @pytest.mark.asyncio
    async def test_comorbidity_patterns(self, dx_analytics):
        """Should identify common comorbidity patterns."""
        comorbidities = await dx_analytics.get_comorbidity_patterns(
            doctor_id="doc_123",
            period="year",
        )

        assert "patterns" in comorbidities
        for pattern in comorbidities["patterns"]:
            assert "diagnoses" in pattern
            assert len(pattern["diagnoses"]) >= 2
            assert "frequency" in pattern or "count" in pattern


class TestPatientOutcomes:
    """Tests for patient outcome analytics."""

    @pytest.fixture
    def outcomes_service(self):
        """Create outcomes analytics service instance."""
        from src.analytics.outcomes import OutcomesAnalyticsService
        return OutcomesAnalyticsService()

    @pytest.mark.asyncio
    async def test_readmission_rates(self, outcomes_service):
        """Should calculate readmission rates."""
        rates = await outcomes_service.get_readmission_rates(
            doctor_id="doc_123",
            period="quarter",
        )

        assert "readmission_rate" in rates
        assert 0 <= rates["readmission_rate"] <= 100
        assert "by_diagnosis" in rates or "breakdown" in rates

    @pytest.mark.asyncio
    async def test_followup_compliance(self, outcomes_service):
        """Should track follow-up compliance."""
        compliance = await outcomes_service.get_followup_compliance(
            doctor_id="doc_123",
            period="month",
        )

        assert "compliance_rate" in compliance
        assert "appointments_scheduled" in compliance
        assert "appointments_kept" in compliance

    @pytest.mark.asyncio
    async def test_treatment_success_rates(self, outcomes_service):
        """Should calculate treatment success rates."""
        success = await outcomes_service.get_treatment_success(
            doctor_id="doc_123",
            condition="hypertension",
            period="year",
        )

        assert "success_rate" in success
        assert "criteria" in success  # How success is defined


class TestBenchmarking:
    """Tests for comparative benchmarking."""

    @pytest.fixture
    def benchmark_service(self):
        """Create benchmarking service instance."""
        from src.analytics.benchmarks import BenchmarkService
        return BenchmarkService()

    @pytest.mark.asyncio
    async def test_peer_comparison(self, benchmark_service):
        """Should compare to peer average."""
        comparison = await benchmark_service.compare_to_peers(
            doctor_id="doc_123",
            metric="queries_per_day",
            peer_group="specialty",
        )

        assert "doctor_value" in comparison
        assert "peer_average" in comparison
        assert "percentile" in comparison

    @pytest.mark.asyncio
    async def test_specialty_benchmarks(self, benchmark_service):
        """Should provide specialty-specific benchmarks."""
        benchmarks = await benchmark_service.get_specialty_benchmarks(
            specialty="cardiology",
        )

        assert "metrics" in benchmarks
        for metric in benchmarks["metrics"]:
            assert "name" in metric
            assert "average" in metric or "median" in metric
            assert "percentile_75" in metric or "top_quartile" in metric

    @pytest.mark.asyncio
    async def test_improvement_suggestions(self, benchmark_service):
        """Should provide improvement suggestions."""
        suggestions = await benchmark_service.get_suggestions(
            doctor_id="doc_123",
        )

        assert "suggestions" in suggestions
        for suggestion in suggestions["suggestions"]:
            assert "area" in suggestion
            assert "current" in suggestion
            assert "target" in suggestion or "benchmark" in suggestion


class TestInsightsGeneration:
    """Tests for automated insight generation."""

    @pytest.fixture
    def insights_service(self):
        """Create insights service instance."""
        from src.analytics.insights import InsightsService
        return InsightsService()

    @pytest.mark.asyncio
    async def test_generate_weekly_insights(self, insights_service):
        """Should generate weekly insights."""
        insights = await insights_service.generate(
            doctor_id="doc_123",
            period="week",
        )

        assert "insights" in insights
        assert len(insights["insights"]) > 0
        for insight in insights["insights"]:
            assert "title" in insight
            assert "description" in insight
            assert "type" in insight  # trend, anomaly, achievement, etc.

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, insights_service):
        """Should detect anomalies in practice patterns."""
        anomalies = await insights_service.detect_anomalies(
            doctor_id="doc_123",
            period="week",
        )

        for anomaly in anomalies:
            assert "metric" in anomaly
            assert "expected" in anomaly
            assert "actual" in anomaly
            assert "deviation" in anomaly or "severity" in anomaly

    @pytest.mark.asyncio
    async def test_achievement_recognition(self, insights_service):
        """Should recognize achievements."""
        achievements = await insights_service.get_achievements(
            doctor_id="doc_123",
            period="month",
        )

        for achievement in achievements:
            assert "title" in achievement
            assert "description" in achievement
            assert "metric" in achievement or "value" in achievement


class TestReportGeneration:
    """Tests for analytics report generation."""

    @pytest.fixture
    def report_service(self):
        """Create report service instance."""
        from src.analytics.reports import ReportService
        return ReportService()

    @pytest.mark.asyncio
    async def test_generate_monthly_report(self, report_service):
        """Should generate monthly practice report."""
        report = await report_service.generate(
            doctor_id="doc_123",
            report_type="monthly",
            month=12,
            year=2025,
        )

        assert "summary" in report
        assert "query_analytics" in report or "queries" in report
        assert "prescriptions" in report or "rx_analytics" in report

    @pytest.mark.asyncio
    async def test_report_pdf_export(self, report_service):
        """Should export report as PDF."""
        result = await report_service.export(
            doctor_id="doc_123",
            report_type="monthly",
            format="pdf",
            month=12,
            year=2025,
        )

        assert result["success"]
        assert "url" in result or "data" in result

    @pytest.mark.asyncio
    async def test_report_comparison(self, report_service):
        """Should compare reports across periods."""
        comparison = await report_service.compare(
            doctor_id="doc_123",
            period_a={"month": 11, "year": 2025},
            period_b={"month": 12, "year": 2025},
        )

        assert "changes" in comparison
        for change in comparison["changes"]:
            assert "metric" in change
            assert "period_a_value" in change or "before" in change
            assert "period_b_value" in change or "after" in change
            assert "change_percent" in change or "delta" in change


class TestDashboard:
    """Tests for analytics dashboard."""

    @pytest.fixture
    def dashboard_service(self):
        """Create dashboard service instance."""
        from src.analytics.dashboard import AnalyticsDashboardService
        return AnalyticsDashboardService()

    @pytest.mark.asyncio
    async def test_dashboard_summary(self, dashboard_service):
        """Should return dashboard summary."""
        summary = await dashboard_service.get_summary(doctor_id="doc_123")

        # Key metrics should be present
        assert "total_queries" in summary or "queries" in summary
        assert "active_streak" in summary or "streak" in summary
        assert "cme_credits" in summary or "learning" in summary

    @pytest.mark.asyncio
    async def test_dashboard_charts_data(self, dashboard_service):
        """Should return data for charts."""
        charts = await dashboard_service.get_charts_data(
            doctor_id="doc_123",
            period="month",
        )

        assert "query_trend" in charts or "queries_over_time" in charts
        assert "top_topics" in charts or "topic_distribution" in charts

    @pytest.mark.asyncio
    async def test_dashboard_widgets(self, dashboard_service):
        """Should return widget data."""
        widgets = await dashboard_service.get_widgets(doctor_id="doc_123")

        assert "widgets" in widgets
        for widget in widgets["widgets"]:
            assert "id" in widget
            assert "type" in widget
            assert "data" in widget


class TestDataExport:
    """Tests for analytics data export."""

    @pytest.fixture
    def export_service(self):
        """Create export service instance."""
        from src.analytics.export import AnalyticsExportService
        return AnalyticsExportService()

    @pytest.mark.asyncio
    async def test_export_raw_data(self, export_service):
        """Should export raw analytics data."""
        result = await export_service.export_data(
            doctor_id="doc_123",
            data_type="queries",
            format="csv",
            period="year",
        )

        assert result["success"]
        assert "download_url" in result or "data" in result

    @pytest.mark.asyncio
    async def test_export_gdpr_compliant(self, export_service):
        """Export should be GDPR compliant."""
        result = await export_service.export_all_data(
            doctor_id="doc_123",
            purpose="data_portability",
        )

        assert result["success"]
        assert "includes" in result  # List of included data types
        # Should include all personal data
        assert "queries" in result["includes"]
        assert "preferences" in result["includes"]
