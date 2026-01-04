"""
Tests for the CME/Learning module.
Tests streaks, certificates, quizzes, and progress tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta


class TestLearningStreaks:
    """Tests for learning streak tracking."""

    @pytest.fixture
    def streak_service(self):
        """Create streak service instance."""
        from src.learning.streaks import StreakService
        return StreakService()

    @pytest.mark.asyncio
    async def test_streak_increments_on_activity(self, streak_service):
        """Streak should increment on daily activity."""
        user_id = "doc_123"

        # Record activity
        result = await streak_service.record_activity(
            user_id=user_id,
            activity_type="query",
            date=date.today(),
        )

        assert result["current_streak"] >= 1

    @pytest.mark.asyncio
    async def test_streak_resets_on_missed_day(self, streak_service):
        """Streak should reset if a day is missed."""
        user_id = "doc_123"

        # Setup: user had 5-day streak ending 2 days ago
        with patch.object(
            streak_service,
            "get_streak_data",
            return_value={
                "current_streak": 5,
                "last_activity_date": date.today() - timedelta(days=2),
            },
        ):
            result = await streak_service.record_activity(
                user_id=user_id,
                activity_type="query",
                date=date.today(),
            )

            # Streak should reset to 1
            assert result["current_streak"] == 1
            assert result["streak_broken"]

    @pytest.mark.asyncio
    async def test_streak_preserved_same_day(self, streak_service):
        """Multiple activities same day should not double-count."""
        user_id = "doc_123"

        # First activity
        result1 = await streak_service.record_activity(
            user_id=user_id,
            activity_type="query",
            date=date.today(),
        )

        # Second activity same day
        result2 = await streak_service.record_activity(
            user_id=user_id,
            activity_type="query",
            date=date.today(),
        )

        assert result1["current_streak"] == result2["current_streak"]

    @pytest.mark.asyncio
    async def test_longest_streak_tracked(self, streak_service):
        """Should track longest streak ever."""
        user_id = "doc_123"

        with patch.object(
            streak_service,
            "get_streak_data",
            return_value={
                "current_streak": 10,
                "longest_streak": 15,
                "last_activity_date": date.today() - timedelta(days=1),
            },
        ):
            result = await streak_service.get_streak_info(user_id)

            assert result["longest_streak"] == 15
            assert result["current_streak"] == 10

    @pytest.mark.asyncio
    async def test_streak_freeze_protection(self, streak_service):
        """Streak freeze should protect streak for one day."""
        user_id = "doc_123"

        # User has streak freeze available
        with patch.object(
            streak_service,
            "get_streak_data",
            return_value={
                "current_streak": 20,
                "last_activity_date": date.today() - timedelta(days=2),
                "streak_freezes": 1,
            },
        ):
            result = await streak_service.record_activity(
                user_id=user_id,
                activity_type="query",
                date=date.today(),
                use_freeze=True,
            )

            # Streak should be preserved
            assert result["current_streak"] == 21
            assert result["freeze_used"]


class TestCMECredits:
    """Tests for CME credit tracking."""

    @pytest.fixture
    def cme_service(self):
        """Create CME service instance."""
        from src.learning.cme import CMEService
        return CMEService()

    @pytest.mark.asyncio
    async def test_credit_earned_for_learning_activity(self, cme_service):
        """CME credits should be earned for learning activities."""
        result = await cme_service.record_learning(
            user_id="doc_123",
            activity_type="case_study",
            duration_minutes=30,
            topic="Cardiac Arrhythmias",
            specialty="cardiology",
        )

        assert result["credits_earned"] > 0

    @pytest.mark.asyncio
    async def test_credit_calculation_by_activity_type(self, cme_service):
        """Different activities should earn different credits."""
        # Case study (higher value)
        case_result = await cme_service.record_learning(
            user_id="doc_123",
            activity_type="case_study",
            duration_minutes=30,
            topic="Topic 1",
            specialty="cardiology",
        )

        # Quiz (lower value)
        quiz_result = await cme_service.record_learning(
            user_id="doc_123",
            activity_type="quiz",
            duration_minutes=30,
            topic="Topic 2",
            specialty="cardiology",
        )

        # Case study should earn more per hour
        assert case_result["credits_earned"] >= quiz_result["credits_earned"]

    @pytest.mark.asyncio
    async def test_annual_credit_limit(self, cme_service):
        """Should respect annual CME credit limits."""
        user_id = "doc_123"

        # User near annual limit
        with patch.object(
            cme_service,
            "get_annual_credits",
            return_value={"earned": 145, "limit": 150},
        ):
            result = await cme_service.record_learning(
                user_id=user_id,
                activity_type="case_study",
                duration_minutes=60,  # Would normally earn 10 credits
                topic="Topic",
                specialty="cardiology",
            )

            # Should be capped
            assert result["credits_earned"] <= 5
            assert result.get("limit_reached") or result.get("capped")

    @pytest.mark.asyncio
    async def test_credit_summary_by_category(self, cme_service):
        """Should provide credit summary by category."""
        summary = await cme_service.get_credit_summary(
            user_id="doc_123",
            year=2025,
        )

        assert "total_credits" in summary
        assert "by_category" in summary or "categories" in summary
        categories = summary.get("by_category", summary.get("categories", {}))
        assert len(categories) > 0


class TestCertificates:
    """Tests for CME certificate generation."""

    @pytest.fixture
    def certificate_service(self):
        """Create certificate service instance."""
        from src.learning.certificates import CertificateService
        return CertificateService()

    @pytest.mark.asyncio
    async def test_certificate_generated_with_required_fields(self, certificate_service):
        """Certificate should have all required fields."""
        cert = await certificate_service.generate(
            user_id="doc_123",
            course_id="course_456",
            completion_date=date.today(),
        )

        assert "certificate_id" in cert
        assert "user_name" in cert or "recipient" in cert
        assert "course_name" in cert or "title" in cert
        assert "credits" in cert
        assert "date" in cert or "completion_date" in cert
        assert "verification_code" in cert or "verification_url" in cert

    @pytest.mark.asyncio
    async def test_certificate_verification(self, certificate_service):
        """Generated certificates should be verifiable."""
        cert = await certificate_service.generate(
            user_id="doc_123",
            course_id="course_456",
            completion_date=date.today(),
        )

        verification = await certificate_service.verify(
            certificate_id=cert["certificate_id"],
            verification_code=cert["verification_code"],
        )

        assert verification["valid"]
        assert verification["certificate_id"] == cert["certificate_id"]

    @pytest.mark.asyncio
    async def test_certificate_pdf_generation(self, certificate_service):
        """Should generate PDF certificate."""
        cert = await certificate_service.generate(
            user_id="doc_123",
            course_id="course_456",
            completion_date=date.today(),
            format="pdf",
        )

        assert "pdf_url" in cert or "pdf_data" in cert

    @pytest.mark.asyncio
    async def test_certificate_includes_accreditation(self, certificate_service):
        """Certificate should include accreditation body."""
        cert = await certificate_service.generate(
            user_id="doc_123",
            course_id="course_456",
            completion_date=date.today(),
        )

        assert "accreditation" in cert or "accredited_by" in cert


class TestQuizzes:
    """Tests for learning quizzes."""

    @pytest.fixture
    def quiz_service(self):
        """Create quiz service instance."""
        from src.learning.quizzes import QuizService
        return QuizService()

    @pytest.mark.asyncio
    async def test_quiz_generation_by_topic(self, quiz_service):
        """Should generate quiz for specific topic."""
        quiz = await quiz_service.generate(
            topic="Hypertension Management",
            difficulty="medium",
            num_questions=5,
        )

        assert len(quiz["questions"]) == 5
        for q in quiz["questions"]:
            assert "question" in q
            assert "options" in q or "choices" in q
            assert "correct_answer" in q or "answer" in q

    @pytest.mark.asyncio
    async def test_quiz_scoring(self, quiz_service):
        """Should correctly score quiz answers."""
        quiz_id = "quiz_123"
        answers = {
            "q1": "B",
            "q2": "A",
            "q3": "C",
            "q4": "D",
            "q5": "A",
        }

        # Mock quiz data with correct answers
        with patch.object(
            quiz_service,
            "get_quiz",
            return_value={
                "questions": [
                    {"id": "q1", "correct_answer": "B"},
                    {"id": "q2", "correct_answer": "A"},
                    {"id": "q3", "correct_answer": "D"},  # User got wrong
                    {"id": "q4", "correct_answer": "D"},
                    {"id": "q5", "correct_answer": "B"},  # User got wrong
                ]
            },
        ):
            result = await quiz_service.submit(
                quiz_id=quiz_id,
                user_id="doc_123",
                answers=answers,
            )

            assert result["score"] == 60  # 3/5 = 60%
            assert result["correct_count"] == 3
            assert result["total_questions"] == 5

    @pytest.mark.asyncio
    async def test_quiz_explanations_provided(self, quiz_service):
        """Quiz results should include explanations."""
        result = await quiz_service.submit(
            quiz_id="quiz_123",
            user_id="doc_123",
            answers={"q1": "B"},
        )

        assert "explanations" in result or "feedback" in result
        explanations = result.get("explanations", result.get("feedback", []))
        for exp in explanations:
            assert "explanation" in exp or "rationale" in exp

    @pytest.mark.asyncio
    async def test_adaptive_difficulty(self, quiz_service):
        """Quiz difficulty should adapt to user performance."""
        user_id = "doc_123"

        # User has high performance history
        with patch.object(
            quiz_service,
            "get_user_performance",
            return_value={"avg_score": 90, "total_quizzes": 20},
        ):
            quiz = await quiz_service.generate(
                topic="Cardiology",
                user_id=user_id,
                adaptive=True,
            )

            assert quiz["difficulty"] in ["hard", "advanced", "expert"]


class TestLearningPaths:
    """Tests for structured learning paths."""

    @pytest.fixture
    def path_service(self):
        """Create learning path service instance."""
        from src.learning.paths import LearningPathService
        return LearningPathService()

    @pytest.mark.asyncio
    async def test_path_has_modules(self, path_service):
        """Learning path should have ordered modules."""
        path = await path_service.get_path("cardiology_fundamentals")

        assert "modules" in path
        assert len(path["modules"]) > 0
        for module in path["modules"]:
            assert "order" in module or "sequence" in module
            assert "title" in module
            assert "duration_minutes" in module or "estimated_time" in module

    @pytest.mark.asyncio
    async def test_progress_tracking(self, path_service):
        """Should track user progress through path."""
        user_id = "doc_123"
        path_id = "cardiology_fundamentals"

        # Complete a module
        await path_service.complete_module(
            user_id=user_id,
            path_id=path_id,
            module_id="module_1",
        )

        progress = await path_service.get_progress(
            user_id=user_id,
            path_id=path_id,
        )

        assert progress["completed_modules"] >= 1
        assert "percentage" in progress or "progress_percent" in progress

    @pytest.mark.asyncio
    async def test_prerequisite_enforcement(self, path_service):
        """Should enforce module prerequisites."""
        user_id = "doc_123"
        path_id = "advanced_cardiology"

        # Try to access advanced module without completing basics
        with patch.object(
            path_service,
            "get_progress",
            return_value={"completed_modules": 0, "completed_ids": []},
        ):
            result = await path_service.can_access_module(
                user_id=user_id,
                path_id=path_id,
                module_id="advanced_module_3",
            )

            assert not result["can_access"]
            assert "prerequisites" in result or "required" in result


class TestSpacedRepetition:
    """Tests for spaced repetition system."""

    @pytest.fixture
    def srs_service(self):
        """Create SRS service instance."""
        from src.learning.spaced_repetition import SpacedRepetitionService
        return SpacedRepetitionService()

    @pytest.mark.asyncio
    async def test_new_card_schedule(self, srs_service):
        """New cards should start with short intervals."""
        card = await srs_service.create_card(
            user_id="doc_123",
            question="What is the first-line treatment for hypertension?",
            answer="Lifestyle modifications and/or ACE inhibitor/ARB/CCB/thiazide",
            topic="cardiology",
        )

        # Next review should be soon (within 1 day)
        next_review = card["next_review"]
        assert next_review <= datetime.now() + timedelta(days=1)

    @pytest.mark.asyncio
    async def test_interval_increases_on_correct(self, srs_service):
        """Correct answers should increase review interval."""
        user_id = "doc_123"
        card_id = "card_123"

        # Initial interval
        card_before = await srs_service.get_card(card_id)
        interval_before = card_before["interval_days"]

        # Review as correct
        await srs_service.review(
            user_id=user_id,
            card_id=card_id,
            quality=5,  # Perfect recall
        )

        card_after = await srs_service.get_card(card_id)
        interval_after = card_after["interval_days"]

        assert interval_after > interval_before

    @pytest.mark.asyncio
    async def test_interval_resets_on_incorrect(self, srs_service):
        """Incorrect answers should reset interval."""
        user_id = "doc_123"
        card_id = "card_123"

        # Card with established interval
        with patch.object(
            srs_service,
            "get_card",
            return_value={"id": card_id, "interval_days": 30, "ease_factor": 2.5},
        ):
            await srs_service.review(
                user_id=user_id,
                card_id=card_id,
                quality=1,  # Complete failure
            )

            # Verify interval was reset
            card_after = await srs_service.get_card(card_id)
            assert card_after["interval_days"] < 30

    @pytest.mark.asyncio
    async def test_due_cards_retrieval(self, srs_service):
        """Should retrieve cards due for review."""
        user_id = "doc_123"

        due_cards = await srs_service.get_due_cards(
            user_id=user_id,
            limit=20,
        )

        # All cards should be due (next_review <= now)
        for card in due_cards:
            assert card["next_review"] <= datetime.now()


class TestProgressDashboard:
    """Tests for learning progress dashboard."""

    @pytest.fixture
    def dashboard_service(self):
        """Create dashboard service instance."""
        from src.learning.dashboard import LearningDashboardService
        return LearningDashboardService()

    @pytest.mark.asyncio
    async def test_dashboard_includes_summary(self, dashboard_service):
        """Dashboard should include learning summary."""
        summary = await dashboard_service.get_summary(user_id="doc_123")

        assert "total_learning_time" in summary or "time_spent" in summary
        assert "credits_earned" in summary or "cme_credits" in summary
        assert "courses_completed" in summary or "completed_courses" in summary

    @pytest.mark.asyncio
    async def test_dashboard_includes_recent_activity(self, dashboard_service):
        """Dashboard should show recent activity."""
        summary = await dashboard_service.get_summary(user_id="doc_123")

        assert "recent_activity" in summary
        activities = summary["recent_activity"]
        for activity in activities:
            assert "type" in activity
            assert "date" in activity or "timestamp" in activity

    @pytest.mark.asyncio
    async def test_dashboard_includes_recommendations(self, dashboard_service):
        """Dashboard should include personalized recommendations."""
        summary = await dashboard_service.get_summary(user_id="doc_123")

        assert "recommendations" in summary or "suggested" in summary
        recs = summary.get("recommendations", summary.get("suggested", []))
        assert len(recs) > 0
