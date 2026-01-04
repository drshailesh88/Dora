"""
Leaderboard System

Multiple leaderboards for different scopes and time periods.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from .models import (
    Leaderboard,
    LeaderboardType,
    LeaderboardPeriod,
    LeaderboardEntry,
)


class LeaderboardService:
    """Service for managing leaderboards"""

    def __init__(self, storage):
        """
        Initialize leaderboard service.

        Args:
            storage: Storage backend
        """
        self.storage = storage

    def get_leaderboard(
        self,
        leaderboard_type: LeaderboardType = LeaderboardType.GLOBAL,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME,
        specialty: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> Leaderboard:
        """
        Get leaderboard rankings.

        Args:
            leaderboard_type: Type of leaderboard
            period: Time period
            specialty: Specialty filter (for specialty leaderboards)
            region: Region filter (for regional leaderboards)
            limit: Maximum number of entries

        Returns:
            Leaderboard: Leaderboard with rankings
        """
        # Calculate period dates
        period_start, period_end = self._get_period_dates(period)

        # Check cache
        cached = self.storage.get_cached_leaderboard(
            leaderboard_type=leaderboard_type,
            period=period,
            specialty=specialty,
            region=region,
        )

        if cached and cached.cache_valid_until > datetime.utcnow():
            return cached

        # Generate fresh leaderboard
        rankings = self._generate_rankings(
            leaderboard_type=leaderboard_type,
            period_start=period_start,
            period_end=period_end,
            specialty=specialty,
            region=region,
            limit=limit,
        )

        leaderboard = Leaderboard(
            leaderboard_type=leaderboard_type,
            period=period,
            specialty=specialty,
            region=region,
            period_start=period_start,
            period_end=period_end,
            rankings=rankings,
            total_participants=len(rankings),
        )

        # Cache leaderboard
        self.storage.save_leaderboard(leaderboard)

        return leaderboard

    def get_user_rank(
        self,
        user_id: str,
        leaderboard_type: LeaderboardType = LeaderboardType.GLOBAL,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME,
    ) -> Optional[LeaderboardEntry]:
        """
        Get user's rank in a leaderboard.

        Args:
            user_id: User ID
            leaderboard_type: Type of leaderboard
            period: Time period

        Returns:
            Optional[LeaderboardEntry]: User's ranking or None
        """
        leaderboard = self.get_leaderboard(
            leaderboard_type=leaderboard_type,
            period=period,
        )

        # Find user in rankings
        for rank, entry in enumerate(leaderboard.rankings, start=1):
            if entry['user_id'] == user_id:
                return LeaderboardEntry(
                    user_id=user_id,
                    leaderboard_id=leaderboard.id,
                    rank=rank,
                    username=entry['username'],
                    display_name=entry['display_name'],
                    xp_amount=entry['xp'],
                    level=entry['level'],
                    badges_count=entry.get('badges_count', 0),
                )

        return None

    def get_user_percentile(
        self,
        user_id: str,
        leaderboard_type: LeaderboardType = LeaderboardType.GLOBAL,
    ) -> float:
        """
        Get user's percentile rank.

        Args:
            user_id: User ID
            leaderboard_type: Leaderboard type

        Returns:
            float: Percentile (0-100)
        """
        rank_entry = self.get_user_rank(
            user_id,
            leaderboard_type,
            LeaderboardPeriod.ALL_TIME,
        )

        if not rank_entry:
            return 0.0

        leaderboard = self.get_leaderboard(leaderboard_type)
        total = leaderboard.total_participants

        if total == 0:
            return 0.0

        # Calculate percentile (higher is better)
        percentile = ((total - rank_entry.rank) / total) * 100
        return round(percentile, 2)

    def update_user_rankings(self, user_id: str):
        """
        Update user's ranking in all relevant leaderboards.

        Args:
            user_id: User ID
        """
        # Get user progress
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return

        # Get user info
        user = self.storage.get_user(user_id)
        if not user:
            return

        # Update global rank
        global_rank = self._calculate_global_rank(user_id)
        progress.global_rank = global_rank

        # Update specialty rank
        if user.specialty:
            specialty_rank = self._calculate_specialty_rank(
                user_id,
                user.specialty,
            )
            progress.specialty_rank = specialty_rank

        # Calculate percentile
        progress.percentile = self.get_user_percentile(user_id)

        # Save progress
        self.storage.save_user_progress(progress)

    def get_friends_leaderboard(
        self,
        user_id: str,
        period: LeaderboardPeriod = LeaderboardPeriod.WEEKLY,
    ) -> Leaderboard:
        """
        Get leaderboard of user's friends.

        Args:
            user_id: User ID
            period: Time period

        Returns:
            Leaderboard: Friends leaderboard
        """
        # Get user's friends
        friend_ids = self.storage.get_user_friends(user_id)
        friend_ids.append(user_id)  # Include self

        period_start, period_end = self._get_period_dates(period)

        # Get XP for each friend in period
        rankings = []
        for friend_id in friend_ids:
            xp = self.storage.get_period_xp(
                friend_id,
                period_start,
                period_end,
            )
            progress = self.storage.get_user_progress(friend_id)
            user = self.storage.get_user(friend_id)

            if progress and user:
                rankings.append({
                    'user_id': friend_id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'xp': xp,
                    'level': progress.current_level,
                    'badges_count': progress.total_badges,
                })

        # Sort by XP
        rankings.sort(key=lambda x: x['xp'], reverse=True)

        return Leaderboard(
            leaderboard_type=LeaderboardType.FRIENDS,
            period=period,
            period_start=period_start,
            period_end=period_end,
            rankings=rankings,
            total_participants=len(rankings),
        )

    def _generate_rankings(
        self,
        leaderboard_type: LeaderboardType,
        period_start: date,
        period_end: date,
        specialty: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Generate leaderboard rankings."""
        # Get all users with their period XP
        users_data = self.storage.get_users_with_period_xp(
            period_start=period_start,
            period_end=period_end,
            specialty=specialty,
            region=region,
        )

        # Filter out anonymous users or apply filters
        if leaderboard_type == LeaderboardType.SPECIALTY and specialty:
            users_data = [u for u in users_data if u.get('specialty') == specialty]
        elif leaderboard_type == LeaderboardType.REGIONAL and region:
            users_data = [u for u in users_data if u.get('region') == region]

        # Sort by XP
        users_data.sort(key=lambda x: x['xp'], reverse=True)

        # Limit to top N
        users_data = users_data[:limit]

        # Format rankings
        rankings = []
        for user in users_data:
            rankings.append({
                'rank': len(rankings) + 1,
                'user_id': user['user_id'],
                'username': user.get('username', 'Anonymous'),
                'display_name': user.get('display_name', 'Anonymous User'),
                'avatar_url': user.get('avatar_url'),
                'specialty': user.get('specialty'),
                'xp': user['xp'],
                'level': user.get('level', 1),
                'badges_count': user.get('badges_count', 0),
            })

        return rankings

    def _calculate_global_rank(self, user_id: str) -> int:
        """Calculate user's global rank."""
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return 99999

        # Count users with more XP
        users_above = self.storage.count_users_with_more_xp(progress.total_xp)

        return users_above + 1

    def _calculate_specialty_rank(self, user_id: str, specialty: str) -> int:
        """Calculate user's rank within specialty."""
        progress = self.storage.get_user_progress(user_id)
        if not progress:
            return 99999

        # Count specialty users with more XP
        users_above = self.storage.count_specialty_users_with_more_xp(
            specialty,
            progress.total_xp,
        )

        return users_above + 1

    def _get_period_dates(
        self,
        period: LeaderboardPeriod,
    ) -> tuple[date, date]:
        """Get start and end dates for a period."""
        today = date.today()

        if period == LeaderboardPeriod.DAILY:
            return today, today

        elif period == LeaderboardPeriod.WEEKLY:
            # Start of week (Monday)
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end

        elif period == LeaderboardPeriod.MONTHLY:
            # Start of month
            start = date(today.year, today.month, 1)
            # End of month
            if today.month == 12:
                end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(today.year, today.month + 1, 1) - timedelta(days=1)
            return start, end

        else:  # ALL_TIME
            # Use a very old date as start
            start = date(2020, 1, 1)
            return start, today
