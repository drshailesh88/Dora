"""
Admin Analytics Service

Aggregates and computes analytics from various data sources.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from ..auth.storage import get_auth_storage
from ..auth.models import UserRole
from ..payments.storage import PaymentStorage
from ..payments.service import get_payment_service
from .models import (
    PlatformStats, UserStats, AnalyticsDataPoint,
    TopQuery, SpecialtyStats, SystemHealth
)


class AnalyticsService:
    """Service for computing platform analytics"""

    def __init__(self):
        """Initialize analytics service"""
        self.auth_storage = get_auth_storage()
        self.payment_storage = PaymentStorage()

    def get_platform_stats(self) -> PlatformStats:
        """
        Compute platform-wide statistics.

        Returns:
            Platform statistics
        """
        stats = PlatformStats()

        # User statistics
        all_users = self.auth_storage.list_users(offset=0, limit=10000)
        stats.total_users = len(all_users)

        stats.active_users = sum(1 for u in all_users if u.is_active)
        stats.inactive_users = stats.total_users - stats.active_users

        # Count by license tier
        stats.trial_users = sum(1 for u in all_users if u.license_tier == "FREE")
        stats.paid_users = sum(1 for u in all_users if u.license_tier in ["BASIC", "PRO", "CLINIC"])

        # New users
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        stats.new_users_today = sum(
            1 for u in all_users if u.created_at >= today_start
        )
        stats.new_users_this_week = sum(
            1 for u in all_users if u.created_at >= week_start
        )
        stats.new_users_this_month = sum(
            1 for u in all_users if u.created_at >= month_start
        )

        # Revenue statistics (computed from payments)
        revenue_stats = self._compute_revenue_stats()
        stats.total_revenue = revenue_stats["total_revenue"]
        stats.revenue_today = revenue_stats["revenue_today"]
        stats.revenue_this_week = revenue_stats["revenue_this_week"]
        stats.revenue_this_month = revenue_stats["revenue_this_month"]
        stats.mrr = revenue_stats["mrr"]
        stats.arr = revenue_stats["arr"]

        # Subscription statistics
        sub_stats = self._compute_subscription_stats()
        stats.active_subscriptions = sub_stats["active"]
        stats.trial_subscriptions = sub_stats["trial"]
        stats.cancelled_subscriptions = sub_stats["cancelled"]
        stats.failed_payments = sub_stats["failed_payments"]

        # Usage statistics (mock data for now - would query from query logs)
        stats.queries_today = 142
        stats.queries_this_week = 1053
        stats.queries_this_month = 4231
        stats.total_queries = 12847

        # System health
        stats.storage_used_mb = 1247.5
        stats.api_requests_today = 2847
        stats.error_rate_percent = 0.23
        stats.avg_response_time_ms = 234.5

        return stats

    def _compute_revenue_stats(self) -> Dict[str, int]:
        """Compute revenue statistics"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.payment_storage.db_path))
            cursor = conn.cursor()

            # Total revenue
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM invoices WHERE is_paid = 1
            """)
            total_revenue = cursor.fetchone()[0]

            # Revenue today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM invoices
                WHERE is_paid = 1 AND paid_at >= ?
            """, (today_start.isoformat(),))
            revenue_today = cursor.fetchone()[0]

            # Revenue this week
            week_start = today_start - timedelta(days=7)
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM invoices
                WHERE is_paid = 1 AND paid_at >= ?
            """, (week_start.isoformat(),))
            revenue_this_week = cursor.fetchone()[0]

            # Revenue this month
            month_start = today_start - timedelta(days=30)
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM invoices
                WHERE is_paid = 1 AND paid_at >= ?
            """, (month_start.isoformat(),))
            revenue_this_month = cursor.fetchone()[0]

            # MRR (Monthly Recurring Revenue)
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM subscriptions
                WHERE status = 'active' AND billing_cycle = 'monthly'
            """)
            mrr_monthly = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM subscriptions
                WHERE status = 'active' AND billing_cycle = 'quarterly'
            """)
            mrr_quarterly = cursor.fetchone()[0] / 3  # Convert to monthly

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM subscriptions
                WHERE status = 'active' AND billing_cycle = 'yearly'
            """)
            mrr_yearly = cursor.fetchone()[0] / 12  # Convert to monthly

            mrr = int(mrr_monthly + mrr_quarterly + mrr_yearly)
            arr = mrr * 12

            conn.close()

            return {
                "total_revenue": int(total_revenue),
                "revenue_today": int(revenue_today),
                "revenue_this_week": int(revenue_this_week),
                "revenue_this_month": int(revenue_this_month),
                "mrr": mrr,
                "arr": arr,
            }

        except Exception as e:
            print(f"Error computing revenue stats: {e}")
            return {
                "total_revenue": 0,
                "revenue_today": 0,
                "revenue_this_week": 0,
                "revenue_this_month": 0,
                "mrr": 0,
                "arr": 0,
            }

    def _compute_subscription_stats(self) -> Dict[str, int]:
        """Compute subscription statistics"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.payment_storage.db_path))
            cursor = conn.cursor()

            # Active subscriptions
            cursor.execute("""
                SELECT COUNT(*) FROM subscriptions WHERE status = 'active'
            """)
            active = cursor.fetchone()[0]

            # Trial subscriptions
            cursor.execute("""
                SELECT COUNT(*) FROM subscriptions WHERE is_trial = 1
            """)
            trial = cursor.fetchone()[0]

            # Cancelled subscriptions
            cursor.execute("""
                SELECT COUNT(*) FROM subscriptions WHERE status = 'cancelled'
            """)
            cancelled = cursor.fetchone()[0]

            # Failed payments
            cursor.execute("""
                SELECT COUNT(*) FROM payments WHERE status = 'failed'
            """)
            failed_payments = cursor.fetchone()[0]

            conn.close()

            return {
                "active": active,
                "trial": trial,
                "cancelled": cancelled,
                "failed_payments": failed_payments,
            }

        except Exception as e:
            print(f"Error computing subscription stats: {e}")
            return {
                "active": 0,
                "trial": 0,
                "cancelled": 0,
                "failed_payments": 0,
            }

    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """
        Get statistics for a specific user.

        Args:
            user_id: User ID

        Returns:
            User statistics or None if user not found
        """
        user = self.auth_storage.get_user(user_id)
        if not user:
            return None

        stats = UserStats(user_id=user_id)

        # Subscription info
        payment_service = get_payment_service()
        subscription = payment_service.get_user_subscription(user_id)

        if subscription:
            stats.subscription_status = subscription.status.value
            stats.subscription_plan = subscription.plan_id
            stats.subscription_started_at = subscription.started_at

        # Total paid
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.payment_storage.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) FROM invoices
                WHERE user_id = ? AND is_paid = 1
            """, (user_id,))
            stats.total_paid = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            print(f"Error getting user payment stats: {e}")

        # Login stats
        stats.login_count = 42  # Mock data
        stats.last_login_at = user.last_login

        # Usage stats (mock data - would query from query logs)
        stats.total_queries = 127
        stats.queries_this_week = 23
        stats.queries_this_month = 89
        stats.drug_checks = 15
        stats.documents_uploaded = 3
        stats.favorites_count = 12

        return stats

    def get_daily_active_users(self, days: int = 30) -> List[AnalyticsDataPoint]:
        """
        Get daily active users for the last N days.

        Args:
            days: Number of days

        Returns:
            List of data points
        """
        data_points = []
        now = datetime.utcnow()

        # Mock data - would query from session logs
        for i in range(days):
            date = now - timedelta(days=days - i - 1)
            # Simulate growth with some randomness
            base_users = 50 + i * 2
            import random
            value = base_users + random.randint(-10, 10)

            data_points.append(
                AnalyticsDataPoint(
                    timestamp=date.replace(hour=0, minute=0, second=0, microsecond=0),
                    value=value,
                    label=date.strftime("%Y-%m-%d"),
                )
            )

        return data_points

    def get_query_volume(self, days: int = 30) -> List[AnalyticsDataPoint]:
        """
        Get query volume over time.

        Args:
            days: Number of days

        Returns:
            List of data points
        """
        data_points = []
        now = datetime.utcnow()

        # Mock data - would query from query logs
        for i in range(days):
            date = now - timedelta(days=days - i - 1)
            import random
            value = 100 + i * 5 + random.randint(-20, 20)

            data_points.append(
                AnalyticsDataPoint(
                    timestamp=date.replace(hour=0, minute=0, second=0, microsecond=0),
                    value=value,
                    label=date.strftime("%Y-%m-%d"),
                )
            )

        return data_points

    def get_top_queries(self, limit: int = 10) -> List[TopQuery]:
        """
        Get most popular queries.

        Args:
            limit: Number of queries to return

        Returns:
            List of top queries
        """
        # Mock data - would query from query logs
        queries = [
            ("Treatment options for Type 2 Diabetes", 342, 234.5, 0.98),
            ("Hypertension management guidelines", 287, 189.2, 0.99),
            ("Drug interactions with Metformin", 213, 156.7, 0.97),
            ("COVID-19 latest guidelines", 198, 201.3, 0.96),
            ("Asthma treatment protocol", 176, 178.9, 0.98),
            ("Heart failure diagnosis", 154, 212.4, 0.95),
            ("Antibiotic resistance patterns", 142, 245.6, 0.97),
            ("Diabetes screening guidelines", 128, 167.8, 0.99),
            ("Pneumonia treatment", 119, 188.4, 0.98),
            ("Chronic kidney disease stages", 107, 203.7, 0.96),
        ]

        result = []
        for query, count, response_time, success_rate in queries[:limit]:
            result.append(
                TopQuery(
                    query=query,
                    count=count,
                    avg_response_time_ms=response_time,
                    success_rate=success_rate,
                    last_queried_at=datetime.utcnow() - timedelta(hours=count % 24),
                )
            )

        return result

    def get_specialty_stats(self) -> List[SpecialtyStats]:
        """
        Get usage statistics by specialty.

        Returns:
            List of specialty statistics
        """
        all_users = self.auth_storage.list_users(offset=0, limit=10000)

        # Group by specialty
        specialty_users = defaultdict(int)
        for user in all_users:
            if user.specialty:
                specialty_users[user.specialty] += 1

        # Mock query counts - would query from query logs
        result = []
        for specialty, user_count in specialty_users.items():
            query_count = user_count * 50  # Mock data
            result.append(
                SpecialtyStats(
                    specialty=specialty,
                    user_count=user_count,
                    query_count=query_count,
                    avg_queries_per_user=query_count / user_count if user_count > 0 else 0,
                )
            )

        # Sort by user count
        result.sort(key=lambda x: x.user_count, reverse=True)
        return result

    def get_system_health(self) -> SystemHealth:
        """
        Get system health metrics.

        Returns:
            System health status
        """
        health = SystemHealth()

        # Mock data - would check actual services
        health.api_status = "healthy"
        health.database_status = "healthy"
        health.vector_db_status = "healthy"
        health.llm_status = "healthy"
        health.payment_status = "healthy"

        # Mock resource usage
        health.cpu_usage_percent = 45.2
        health.memory_usage_percent = 62.8
        health.disk_usage_percent = 34.5

        # Mock performance metrics
        health.avg_query_latency_ms = 234.5
        health.p95_query_latency_ms = 567.8
        health.error_rate_percent = 0.23

        return health


# Global instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
