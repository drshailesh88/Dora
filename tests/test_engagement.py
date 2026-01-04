"""
Tests for the daily engagement system.
Tests morning briefings, alerts, clinical pearls, and trending queries.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta


class TestMorningBriefing:
    """Tests for morning briefing generation."""

    @pytest.fixture
    def briefing_service(self):
        """Create briefing service instance."""
        from src.engagement.briefings import MorningBriefingService
        return MorningBriefingService()

    @pytest.fixture
    def sample_doctor(self):
        """Sample doctor profile."""
        return {
            "id": "doc_123",
            "name": "Dr. Sharma",
            "specialty": "cardiology",
            "preferences": {
                "briefing_time": "08:00",
                "language": "en",
                "include_research": True,
            },
        }

    @pytest.fixture
    def sample_appointments(self):
        """Sample today's appointments."""
        return [
            {
                "patient_id": "pat_1",
                "patient_name": "Rahul Kumar",
                "time": "09:00",
                "reason": "Follow-up: Hypertension",
                "conditions": ["Hypertension", "Type 2 Diabetes"],
            },
            {
                "patient_id": "pat_2",
                "patient_name": "Priya Singh",
                "time": "09:30",
                "reason": "New patient: Chest pain evaluation",
                "conditions": [],
            },
            {
                "patient_id": "pat_3",
                "patient_name": "Amit Patel",
                "time": "10:00",
                "reason": "Follow-up: Post-MI",
                "conditions": ["CAD", "Prior MI", "CHF"],
            },
        ]

    @pytest.mark.asyncio
    async def test_briefing_includes_patient_preview(
        self, briefing_service, sample_doctor, sample_appointments
    ):
        """Briefing should include today's patient summary."""
        with patch.object(
            briefing_service, "get_appointments", return_value=sample_appointments
        ):
            briefing = await briefing_service.generate(
                doctor=sample_doctor,
                date=date.today(),
            )

        assert "patients" in briefing or "appointments" in briefing
        assert len(briefing.get("patients", briefing.get("appointments", []))) == 3

    @pytest.mark.asyncio
    async def test_briefing_includes_clinical_pearl(
        self, briefing_service, sample_doctor
    ):
        """Briefing should include specialty-relevant clinical pearl."""
        briefing = await briefing_service.generate(
            doctor=sample_doctor,
            date=date.today(),
        )

        assert "clinical_pearl" in briefing or "pearl" in briefing
        pearl = briefing.get("clinical_pearl", briefing.get("pearl", {}))
        # Pearl should be cardiology-related
        assert pearl.get("specialty") == "cardiology" or \
               "cardiology" in pearl.get("tags", [])

    @pytest.mark.asyncio
    async def test_briefing_includes_trending(
        self, briefing_service, sample_doctor
    ):
        """Briefing should include trending topics in specialty."""
        briefing = await briefing_service.generate(
            doctor=sample_doctor,
            date=date.today(),
        )

        assert "trending" in briefing
        assert len(briefing["trending"]) > 0

    @pytest.mark.asyncio
    async def test_briefing_personalized_by_specialty(self, briefing_service):
        """Briefing content should differ by specialty."""
        cardiologist = {"id": "doc_1", "specialty": "cardiology"}
        neurologist = {"id": "doc_2", "specialty": "neurology"}

        cardio_brief = await briefing_service.generate(
            doctor=cardiologist, date=date.today()
        )
        neuro_brief = await briefing_service.generate(
            doctor=neurologist, date=date.today()
        )

        # Clinical pearls should differ
        assert cardio_brief.get("clinical_pearl") != neuro_brief.get("clinical_pearl")

    @pytest.mark.asyncio
    async def test_briefing_highlights_complex_patients(
        self, briefing_service, sample_doctor, sample_appointments
    ):
        """Complex patients should be highlighted."""
        with patch.object(
            briefing_service, "get_appointments", return_value=sample_appointments
        ):
            briefing = await briefing_service.generate(
                doctor=sample_doctor,
                date=date.today(),
            )

        # Patient with multiple conditions should be flagged
        highlights = briefing.get("highlights", [])
        assert any("Amit Patel" in str(h) for h in highlights) or \
               any("complex" in str(h).lower() for h in highlights)


class TestClinicalAlerts:
    """Tests for clinical alert notifications."""

    @pytest.fixture
    def alert_service(self):
        """Create alert service instance."""
        from src.engagement.alerts import ClinicalAlertService
        return ClinicalAlertService()

    @pytest.mark.asyncio
    async def test_guideline_update_alert(self, alert_service):
        """Guideline updates should generate alerts."""
        update = {
            "type": "guideline_update",
            "title": "2025 ACC/AHA Hypertension Guideline Update",
            "specialty": "cardiology",
            "summary": "New BP targets for elderly patients",
            "published_date": date.today(),
        }

        alert = await alert_service.create_alert(update)

        assert alert["priority"] in ["high", "medium"]
        assert "hypertension" in alert["title"].lower() or \
               "guideline" in alert["type"].lower()

    @pytest.mark.asyncio
    async def test_drug_recall_alert_high_priority(self, alert_service):
        """Drug recalls should be high priority."""
        recall = {
            "type": "drug_recall",
            "drug_name": "Valsartan 160mg",
            "manufacturer": "Acme Pharma",
            "reason": "NDMA contamination",
            "lot_numbers": ["A123", "B456"],
        }

        alert = await alert_service.create_alert(recall)

        assert alert["priority"] == "critical" or alert["priority"] == "high"
        assert alert.get("action_required", True)

    @pytest.mark.asyncio
    async def test_research_alert_filtered_by_specialty(self, alert_service):
        """Research alerts should match doctor's specialty."""
        doctor = {"id": "doc_1", "specialty": "cardiology"}

        # Cardiology paper
        cardio_paper = {
            "type": "research",
            "title": "Novel anticoagulation in AF",
            "journal": "NEJM",
            "specialty_tags": ["cardiology"],
        }

        # Neurology paper
        neuro_paper = {
            "type": "research",
            "title": "New MS treatment outcomes",
            "journal": "Lancet Neurology",
            "specialty_tags": ["neurology"],
        }

        cardio_alert = await alert_service.create_alert(cardio_paper, doctor=doctor)
        neuro_alert = await alert_service.create_alert(neuro_paper, doctor=doctor)

        # Cardiology alert should be higher priority for cardiologist
        assert cardio_alert["relevance_score"] > neuro_alert["relevance_score"]

    @pytest.mark.asyncio
    async def test_alert_deduplication(self, alert_service):
        """Duplicate alerts should be deduplicated."""
        alert_data = {
            "type": "guideline_update",
            "title": "Same Guideline",
            "content": "Same content",
        }

        alert1 = await alert_service.create_alert(alert_data)
        alert2 = await alert_service.create_alert(alert_data)

        # Should be same alert ID or marked as duplicate
        assert alert1["id"] == alert2["id"] or alert2.get("duplicate", False)


class TestClinicalPearls:
    """Tests for clinical pearl generation."""

    @pytest.fixture
    def pearl_service(self):
        """Create pearl service instance."""
        from src.engagement.pearls import ClinicalPearlService
        return ClinicalPearlService()

    @pytest.mark.asyncio
    async def test_pearl_has_required_fields(self, pearl_service):
        """Pearls should have all required fields."""
        pearl = await pearl_service.get_daily_pearl(specialty="cardiology")

        assert "title" in pearl
        assert "content" in pearl
        assert "source" in pearl or "reference" in pearl
        assert "specialty" in pearl

    @pytest.mark.asyncio
    async def test_pearl_not_repeated_recently(self, pearl_service):
        """Same pearl should not repeat within 30 days."""
        doctor_id = "doc_123"
        pearls = []

        for _ in range(10):
            pearl = await pearl_service.get_daily_pearl(
                specialty="cardiology",
                doctor_id=doctor_id,
            )
            pearls.append(pearl["id"])

        # All should be unique
        assert len(set(pearls)) == len(pearls)

    @pytest.mark.asyncio
    async def test_pearl_difficulty_progression(self, pearl_service):
        """Pearl difficulty should match doctor's experience."""
        junior_doc = {"id": "doc_1", "years_experience": 1}
        senior_doc = {"id": "doc_2", "years_experience": 20}

        junior_pearl = await pearl_service.get_daily_pearl(
            specialty="cardiology",
            doctor=junior_doc,
        )
        senior_pearl = await pearl_service.get_daily_pearl(
            specialty="cardiology",
            doctor=senior_doc,
        )

        # Difficulty levels should differ
        assert junior_pearl.get("difficulty") != senior_pearl.get("difficulty") or \
               junior_pearl.get("level") != senior_pearl.get("level")


class TestTrendingQueries:
    """Tests for trending queries tracking."""

    @pytest.fixture
    def trending_service(self):
        """Create trending service instance."""
        from src.engagement.trending import TrendingQueriesService
        return TrendingQueriesService()

    @pytest.mark.asyncio
    async def test_trending_ranked_by_frequency(self, trending_service):
        """Trending queries should be ranked by frequency."""
        trending = await trending_service.get_trending(
            specialty="cardiology",
            period="24h",
        )

        # Should be sorted by count descending
        counts = [q["count"] for q in trending]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_trending_filtered_by_specialty(self, trending_service):
        """Trending should be filterable by specialty."""
        cardio_trending = await trending_service.get_trending(specialty="cardiology")
        neuro_trending = await trending_service.get_trending(specialty="neurology")

        # Should have different queries
        cardio_queries = set(q["query"] for q in cardio_trending)
        neuro_queries = set(q["query"] for q in neuro_trending)

        # Not all should overlap
        assert cardio_queries != neuro_queries

    @pytest.mark.asyncio
    async def test_trending_excludes_pii(self, trending_service):
        """Trending should not contain PII."""
        trending = await trending_service.get_trending(specialty="cardiology")

        for query in trending:
            query_text = query["query"].lower()
            # Should not contain patient identifiers
            assert "mrn" not in query_text
            assert not any(
                pattern in query_text
                for pattern in ["@", "patient id", "record number"]
            )

    @pytest.mark.asyncio
    async def test_trending_respects_time_period(self, trending_service):
        """Trending should respect time period filter."""
        hourly = await trending_service.get_trending(specialty="cardiology", period="1h")
        daily = await trending_service.get_trending(specialty="cardiology", period="24h")
        weekly = await trending_service.get_trending(specialty="cardiology", period="7d")

        # Longer periods should have more total queries
        hourly_total = sum(q["count"] for q in hourly)
        daily_total = sum(q["count"] for q in daily)
        weekly_total = sum(q["count"] for q in weekly)

        assert hourly_total <= daily_total <= weekly_total


class TestEngagementMetrics:
    """Tests for engagement metrics tracking."""

    @pytest.fixture
    def metrics_service(self):
        """Create metrics service instance."""
        from src.engagement.metrics import EngagementMetricsService
        return EngagementMetricsService()

    @pytest.mark.asyncio
    async def test_daily_active_users_tracked(self, metrics_service):
        """Should track daily active users."""
        metrics = await metrics_service.get_metrics(period="today")

        assert "daily_active_users" in metrics or "dau" in metrics

    @pytest.mark.asyncio
    async def test_query_count_tracked(self, metrics_service):
        """Should track query counts."""
        metrics = await metrics_service.get_metrics(period="today")

        assert "total_queries" in metrics or "query_count" in metrics

    @pytest.mark.asyncio
    async def test_briefing_open_rate_tracked(self, metrics_service):
        """Should track briefing open rates."""
        metrics = await metrics_service.get_metrics(period="today")

        assert "briefing_open_rate" in metrics or "briefings" in metrics

    @pytest.mark.asyncio
    async def test_feature_usage_breakdown(self, metrics_service):
        """Should track feature-level usage."""
        metrics = await metrics_service.get_metrics(period="week")

        assert "feature_usage" in metrics or "features" in metrics
        features = metrics.get("feature_usage", metrics.get("features", {}))
        assert len(features) > 0


class TestNotificationDelivery:
    """Tests for notification delivery system."""

    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        from src.engagement.notifications import NotificationService
        return NotificationService()

    @pytest.mark.asyncio
    async def test_push_notification_sent(self, notification_service):
        """Push notifications should be sent."""
        with patch.object(
            notification_service, "_send_push", new_callable=AsyncMock
        ) as mock_push:
            mock_push.return_value = {"success": True}

            result = await notification_service.send(
                user_id="doc_123",
                channel="push",
                title="Morning Briefing Ready",
                body="Your personalized briefing is ready",
            )

            assert result["success"]
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_notification_respects_preferences(self, notification_service):
        """Should respect user notification preferences."""
        user_prefs = {
            "push_enabled": True,
            "email_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
        }

        with patch.object(
            notification_service, "get_user_preferences", return_value=user_prefs
        ):
            # During quiet hours
            with patch("src.engagement.notifications.datetime") as mock_dt:
                mock_dt.now.return_value = datetime(2025, 1, 1, 23, 0)  # 11 PM

                result = await notification_service.send(
                    user_id="doc_123",
                    channel="push",
                    title="Test",
                    body="Test body",
                    respect_quiet_hours=True,
                )

                # Should be queued, not sent immediately
                assert result.get("queued") or not result.get("sent_immediately")

    @pytest.mark.asyncio
    async def test_notification_rate_limiting(self, notification_service):
        """Should rate limit notifications."""
        user_id = "doc_123"

        # Send many notifications quickly
        results = []
        for i in range(20):
            result = await notification_service.send(
                user_id=user_id,
                channel="push",
                title=f"Notification {i}",
                body="Test",
            )
            results.append(result)

        # Some should be rate limited
        rate_limited = [r for r in results if r.get("rate_limited")]
        assert len(rate_limited) > 0 or results[-1].get("queued")
