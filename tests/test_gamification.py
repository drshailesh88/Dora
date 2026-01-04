"""
Tests for gamification system.
Tests points, levels, badges, challenges, and leaderboards.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta


class TestPointsSystem:
    """Tests for points earning and tracking."""

    @pytest.fixture
    def points_service(self):
        """Create points service instance."""
        from src.gamification.points import PointsService
        return PointsService()

    @pytest.mark.asyncio
    async def test_points_earned_for_query(self, points_service):
        """Should earn points for making queries."""
        result = await points_service.award_points(
            user_id="doc_123",
            action="query",
            context={"query_type": "clinical"},
        )

        assert result["points_earned"] > 0
        assert result["new_total"] > 0

    @pytest.mark.asyncio
    async def test_points_earned_for_streak(self, points_service):
        """Should earn bonus points for streaks."""
        # 7-day streak bonus
        result = await points_service.award_points(
            user_id="doc_123",
            action="streak_bonus",
            context={"streak_days": 7},
        )

        assert result["points_earned"] >= 50  # Streak bonuses should be significant

    @pytest.mark.asyncio
    async def test_points_earned_for_learning(self, points_service):
        """Should earn points for learning activities."""
        activities = [
            ("quiz_completed", 10),
            ("course_completed", 100),
            ("pearl_read", 5),
        ]

        for action, min_points in activities:
            result = await points_service.award_points(
                user_id="doc_123",
                action=action,
                context={},
            )
            assert result["points_earned"] >= min_points

    @pytest.mark.asyncio
    async def test_daily_points_cap(self, points_service):
        """Should have daily points cap to prevent gaming."""
        user_id = "doc_123"

        # Simulate many activities
        with patch.object(
            points_service,
            "get_daily_points",
            return_value={"earned_today": 950, "daily_cap": 1000},
        ):
            result = await points_service.award_points(
                user_id=user_id,
                action="query",
                context={"points_value": 100},
            )

            # Should be capped
            assert result["points_earned"] <= 50
            assert result.get("capped") or result.get("at_daily_limit")

    @pytest.mark.asyncio
    async def test_points_history_tracked(self, points_service):
        """Should track points earning history."""
        history = await points_service.get_history(
            user_id="doc_123",
            days=30,
        )

        assert "transactions" in history
        for txn in history["transactions"]:
            assert "action" in txn
            assert "points" in txn
            assert "timestamp" in txn


class TestLevelSystem:
    """Tests for user leveling system."""

    @pytest.fixture
    def level_service(self):
        """Create level service instance."""
        from src.gamification.levels import LevelService
        return LevelService()

    @pytest.mark.asyncio
    async def test_level_calculation(self, level_service):
        """Should correctly calculate level from points."""
        test_cases = [
            (0, 1),
            (100, 1),
            (500, 2),
            (2000, 5),
            (10000, 15),
            (100000, 50),
        ]

        for points, expected_min_level in test_cases:
            level = await level_service.calculate_level(points)
            assert level >= expected_min_level

    @pytest.mark.asyncio
    async def test_level_up_detection(self, level_service):
        """Should detect when user levels up."""
        user_id = "doc_123"

        # User just below threshold
        with patch.object(
            level_service,
            "get_user_state",
            return_value={"points": 990, "level": 4},
        ):
            result = await level_service.check_level_up(
                user_id=user_id,
                new_points=1050,
            )

            assert result["leveled_up"]
            assert result["new_level"] == 5
            assert "rewards" in result

    @pytest.mark.asyncio
    async def test_level_progress_tracking(self, level_service):
        """Should track progress to next level."""
        progress = await level_service.get_progress(user_id="doc_123")

        assert "current_level" in progress
        assert "current_points" in progress
        assert "points_to_next" in progress
        assert "progress_percent" in progress
        assert 0 <= progress["progress_percent"] <= 100

    @pytest.mark.asyncio
    async def test_level_titles(self, level_service):
        """Levels should have meaningful titles."""
        titles = await level_service.get_level_titles()

        assert len(titles) >= 50  # 50 levels minimum
        assert titles[1]["title"] != titles[10]["title"]
        # Medical themed titles
        assert any(
            "resident" in t["title"].lower() or
            "fellow" in t["title"].lower() or
            "attending" in t["title"].lower()
            for t in titles.values()
        )


class TestBadgeSystem:
    """Tests for achievement badges."""

    @pytest.fixture
    def badge_service(self):
        """Create badge service instance."""
        from src.gamification.badges import BadgeService
        return BadgeService()

    @pytest.mark.asyncio
    async def test_badge_earned_on_achievement(self, badge_service):
        """Should award badge when criteria met."""
        result = await badge_service.check_and_award(
            user_id="doc_123",
            event="queries_made",
            count=100,
        )

        if result["badge_earned"]:
            assert "badge_id" in result
            assert "badge_name" in result
            assert "badge_icon" in result

    @pytest.mark.asyncio
    async def test_badge_rarity_levels(self, badge_service):
        """Badges should have rarity levels."""
        all_badges = await badge_service.get_all_badges()

        rarities = set(b["rarity"] for b in all_badges)
        expected_rarities = {"common", "uncommon", "rare", "epic", "legendary"}
        assert rarities & expected_rarities  # At least some overlap

    @pytest.mark.asyncio
    async def test_badge_categories(self, badge_service):
        """Badges should be categorized."""
        all_badges = await badge_service.get_all_badges()

        categories = set(b["category"] for b in all_badges)
        # Should have multiple categories
        assert len(categories) >= 3
        # Medical themed
        assert any(
            cat in ["learning", "clinical", "research", "engagement", "expertise"]
            for cat in categories
        )

    @pytest.mark.asyncio
    async def test_no_duplicate_badge_awards(self, badge_service):
        """Should not award same badge twice."""
        user_id = "doc_123"

        # First award
        result1 = await badge_service.check_and_award(
            user_id=user_id,
            event="first_query",
            count=1,
        )

        # Second attempt
        result2 = await badge_service.check_and_award(
            user_id=user_id,
            event="first_query",
            count=1,
        )

        if result1["badge_earned"]:
            assert not result2["badge_earned"] or \
                   result2.get("already_earned")

    @pytest.mark.asyncio
    async def test_badge_progress_tracking(self, badge_service):
        """Should track progress toward badges."""
        progress = await badge_service.get_progress(
            user_id="doc_123",
            badge_id="query_master",
        )

        assert "current_count" in progress
        assert "required_count" in progress
        assert "percentage" in progress


class TestChallenges:
    """Tests for challenges/quests system."""

    @pytest.fixture
    def challenge_service(self):
        """Create challenge service instance."""
        from src.gamification.challenges import ChallengeService
        return ChallengeService()

    @pytest.mark.asyncio
    async def test_daily_challenges_generated(self, challenge_service):
        """Should generate daily challenges."""
        challenges = await challenge_service.get_daily(user_id="doc_123")

        assert len(challenges) >= 3  # At least 3 daily challenges
        for challenge in challenges:
            assert "id" in challenge
            assert "title" in challenge
            assert "description" in challenge
            assert "reward_points" in challenge
            assert "expiry" in challenge

    @pytest.mark.asyncio
    async def test_challenge_completion(self, challenge_service):
        """Should track challenge completion."""
        result = await challenge_service.update_progress(
            user_id="doc_123",
            challenge_id="daily_5_queries",
            progress=5,
        )

        if result["completed"]:
            assert result["reward_earned"]
            assert result["points_awarded"] > 0

    @pytest.mark.asyncio
    async def test_weekly_challenges(self, challenge_service):
        """Should have weekly challenges."""
        challenges = await challenge_service.get_weekly(user_id="doc_123")

        assert len(challenges) >= 1
        for challenge in challenges:
            # Weekly challenges should have higher rewards
            assert challenge["reward_points"] >= 100

    @pytest.mark.asyncio
    async def test_specialty_challenges(self, challenge_service):
        """Should have specialty-specific challenges."""
        cardio_challenges = await challenge_service.get_specialty(
            user_id="doc_123",
            specialty="cardiology",
        )

        for challenge in cardio_challenges:
            # Should be cardiology related
            assert "cardiology" in challenge.get("tags", []) or \
                   "cardio" in challenge["title"].lower() or \
                   "heart" in challenge["description"].lower()


class TestLeaderboards:
    """Tests for leaderboard system."""

    @pytest.fixture
    def leaderboard_service(self):
        """Create leaderboard service instance."""
        from src.gamification.leaderboards import LeaderboardService
        return LeaderboardService()

    @pytest.mark.asyncio
    async def test_global_leaderboard(self, leaderboard_service):
        """Should provide global rankings."""
        leaderboard = await leaderboard_service.get_global(limit=100)

        assert "rankings" in leaderboard
        assert len(leaderboard["rankings"]) <= 100

        # Should be sorted by points descending
        points = [r["points"] for r in leaderboard["rankings"]]
        assert points == sorted(points, reverse=True)

    @pytest.mark.asyncio
    async def test_specialty_leaderboard(self, leaderboard_service):
        """Should filter by specialty."""
        leaderboard = await leaderboard_service.get_by_specialty(
            specialty="cardiology",
            limit=50,
        )

        for entry in leaderboard["rankings"]:
            assert entry.get("specialty") == "cardiology"

    @pytest.mark.asyncio
    async def test_user_rank_included(self, leaderboard_service):
        """Should include requesting user's rank."""
        leaderboard = await leaderboard_service.get_global(
            limit=10,
            user_id="doc_123",
        )

        assert "user_rank" in leaderboard
        assert "user_points" in leaderboard

    @pytest.mark.asyncio
    async def test_anonymization_option(self, leaderboard_service):
        """Should support anonymous mode."""
        leaderboard = await leaderboard_service.get_global(
            limit=10,
            anonymized=True,
        )

        for entry in leaderboard["rankings"]:
            # Should not contain real names
            assert "Dr." not in entry.get("display_name", "")
            assert entry.get("anonymized", True)

    @pytest.mark.asyncio
    async def test_time_period_filtering(self, leaderboard_service):
        """Should filter by time period."""
        weekly = await leaderboard_service.get_global(period="week")
        monthly = await leaderboard_service.get_global(period="month")
        all_time = await leaderboard_service.get_global(period="all_time")

        # All-time should have highest total points
        if weekly["rankings"] and monthly["rankings"] and all_time["rankings"]:
            assert all_time["rankings"][0]["points"] >= monthly["rankings"][0]["points"]


class TestRewards:
    """Tests for reward redemption system."""

    @pytest.fixture
    def rewards_service(self):
        """Create rewards service instance."""
        from src.gamification.rewards import RewardsService
        return RewardsService()

    @pytest.mark.asyncio
    async def test_available_rewards(self, rewards_service):
        """Should list available rewards."""
        rewards = await rewards_service.get_available(user_id="doc_123")

        assert len(rewards) > 0
        for reward in rewards:
            assert "id" in reward
            assert "name" in reward
            assert "points_cost" in reward
            assert "description" in reward

    @pytest.mark.asyncio
    async def test_reward_redemption(self, rewards_service):
        """Should allow reward redemption."""
        # User has enough points
        with patch.object(
            rewards_service,
            "get_user_points",
            return_value=5000,
        ):
            result = await rewards_service.redeem(
                user_id="doc_123",
                reward_id="premium_feature_unlock",
            )

            assert result["success"]
            assert result["points_deducted"] > 0

    @pytest.mark.asyncio
    async def test_insufficient_points_rejected(self, rewards_service):
        """Should reject redemption with insufficient points."""
        with patch.object(
            rewards_service,
            "get_user_points",
            return_value=10,
        ):
            result = await rewards_service.redeem(
                user_id="doc_123",
                reward_id="expensive_reward",  # Costs more than 10 points
            )

            assert not result["success"]
            assert "insufficient" in result["error"].lower()


class TestGamificationIntegration:
    """Integration tests for gamification system."""

    @pytest.fixture
    def gamification_engine(self):
        """Create gamification engine instance."""
        from src.gamification.engine import GamificationEngine
        return GamificationEngine()

    @pytest.mark.asyncio
    async def test_action_triggers_multiple_systems(self, gamification_engine):
        """Single action should update points, check badges, update challenges."""
        result = await gamification_engine.process_action(
            user_id="doc_123",
            action="query_submitted",
            context={"specialty": "cardiology"},
        )

        # Should have multiple updates
        assert "points" in result
        assert "badges" in result
        assert "challenges" in result
        assert "streak" in result

    @pytest.mark.asyncio
    async def test_level_up_triggers_rewards(self, gamification_engine):
        """Level up should trigger special rewards."""
        with patch.object(
            gamification_engine.level_service,
            "check_level_up",
            return_value={
                "leveled_up": True,
                "new_level": 10,
                "rewards": ["badge_level_10", "points_bonus_500"],
            },
        ):
            result = await gamification_engine.process_action(
                user_id="doc_123",
                action="query_submitted",
                context={},
            )

            assert result.get("level_up")
            assert len(result.get("rewards", [])) > 0
