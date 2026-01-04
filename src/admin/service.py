"""
Admin Service Layer

High-level service for admin operations.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from ..auth import User, UserRole
from ..auth.storage import get_auth_storage
from ..payments.service import get_payment_service
from .models import AuditLog, AuditAction, PlatformStats, UserStats
from .storage import get_admin_storage
from .analytics import get_analytics_service


@dataclass
class AdminResult:
    """Result of admin operation"""
    success: bool
    error: Optional[str] = None
    data: Optional[dict] = None


class AdminService:
    """Service for admin operations"""

    def __init__(self):
        """Initialize admin service"""
        self.storage = get_admin_storage()
        self.auth_storage = get_auth_storage()
        self.payment_service = get_payment_service()
        self.analytics = get_analytics_service()

    def log_audit(
        self,
        admin_user: User,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        description: str = "",
        changes: Optional[dict] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> bool:
        """
        Log an admin action to audit trail.

        Args:
            admin_user: User performing the action
            action: Action type
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            description: Human-readable description
            changes: Before/after changes
            metadata: Additional metadata
            ip_address: IP address
            user_agent: User agent
            success: Whether action succeeded
            error: Error message if failed

        Returns:
            True if logged successfully
        """
        log = AuditLog(
            user_id=admin_user.id,
            user_email=admin_user.email,
            user_role=admin_user.role.value,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            changes=changes,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error=error,
        )

        return self.storage.log_audit(log)

    def get_platform_stats(self, use_cache: bool = True) -> PlatformStats:
        """
        Get platform statistics.

        Args:
            use_cache: Whether to use cached stats

        Returns:
            Platform statistics
        """
        if use_cache:
            cached = self.storage.get_cached_stats()
            if cached:
                return PlatformStats(**cached)

        # Compute fresh stats
        stats = self.analytics.get_platform_stats()

        # Cache for 5 minutes
        self.storage.cache_stats(stats.to_dict())

        return stats

    def get_user_list(
        self,
        offset: int = 0,
        limit: int = 50,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        license_tier: Optional[str] = None,
    ) -> List[User]:
        """
        Get list of users with filters.

        Args:
            offset: Pagination offset
            limit: Max results
            role: Filter by role
            search: Search by name/email
            is_active: Filter by active status
            license_tier: Filter by license tier

        Returns:
            List of users
        """
        users = self.auth_storage.list_users(offset=offset, limit=limit, role=role)

        # Apply additional filters
        if search:
            search_lower = search.lower()
            users = [
                u for u in users
                if search_lower in u.email.lower() or search_lower in u.name.lower()
            ]

        if is_active is not None:
            users = [u for u in users if u.is_active == is_active]

        if license_tier:
            users = [u for u in users if u.license_tier == license_tier]

        return users

    def get_user_details(self, user_id: str) -> Optional[dict]:
        """
        Get detailed user information.

        Args:
            user_id: User ID

        Returns:
            User details including stats
        """
        user = self.auth_storage.get_user(user_id)
        if not user:
            return None

        # Get user stats
        stats = self.analytics.get_user_stats(user_id)

        # Get subscription
        subscription = self.payment_service.get_user_subscription(user_id)

        # Get recent payments
        payments = self.payment_service.get_user_payments(user_id, limit=10)

        return {
            "user": user.to_dict(),
            "stats": stats.to_dict() if stats else None,
            "subscription": subscription.to_dict() if subscription else None,
            "recent_payments": [p.to_dict() for p in payments],
        }

    def suspend_user(
        self,
        admin_user: User,
        user_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminResult:
        """
        Suspend a user account.

        Args:
            admin_user: Admin performing action
            user_id: User to suspend
            reason: Reason for suspension
            ip_address: IP address
            user_agent: User agent

        Returns:
            Result of operation
        """
        user = self.auth_storage.get_user(user_id)
        if not user:
            return AdminResult(success=False, error="User not found")

        if not user.is_active:
            return AdminResult(success=False, error="User already suspended")

        # Cannot suspend yourself
        if user_id == admin_user.id:
            return AdminResult(success=False, error="Cannot suspend yourself")

        # Update user
        old_status = user.is_active
        user.is_active = False
        self.auth_storage.update_user(user)

        # Log audit
        self.log_audit(
            admin_user=admin_user,
            action=AuditAction.USER_SUSPEND,
            resource_type="user",
            resource_id=user_id,
            description=f"Suspended user {user.email}: {reason}",
            changes={"is_active": {"before": old_status, "after": False}},
            metadata={"reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AdminResult(
            success=True,
            data={"user": user.to_dict()}
        )

    def activate_user(
        self,
        admin_user: User,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminResult:
        """
        Activate a suspended user account.

        Args:
            admin_user: Admin performing action
            user_id: User to activate
            ip_address: IP address
            user_agent: User agent

        Returns:
            Result of operation
        """
        user = self.auth_storage.get_user(user_id)
        if not user:
            return AdminResult(success=False, error="User not found")

        if user.is_active:
            return AdminResult(success=False, error="User already active")

        # Update user
        old_status = user.is_active
        user.is_active = True
        self.auth_storage.update_user(user)

        # Log audit
        self.log_audit(
            admin_user=admin_user,
            action=AuditAction.USER_ACTIVATE,
            resource_type="user",
            resource_id=user_id,
            description=f"Activated user {user.email}",
            changes={"is_active": {"before": old_status, "after": True}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AdminResult(
            success=True,
            data={"user": user.to_dict()}
        )

    def update_user_role(
        self,
        admin_user: User,
        user_id: str,
        new_role: UserRole,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminResult:
        """
        Update user role.

        Args:
            admin_user: Admin performing action
            user_id: User to update
            new_role: New role
            ip_address: IP address
            user_agent: User agent

        Returns:
            Result of operation
        """
        # Only super_admin can change roles
        if admin_user.role != UserRole.SUPER_ADMIN:
            return AdminResult(success=False, error="Only super admin can change roles")

        user = self.auth_storage.get_user(user_id)
        if not user:
            return AdminResult(success=False, error="User not found")

        old_role = user.role
        user.role = new_role
        self.auth_storage.update_user(user)

        # Log audit
        self.log_audit(
            admin_user=admin_user,
            action=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=user_id,
            description=f"Changed role of {user.email} from {old_role.value} to {new_role.value}",
            changes={"role": {"before": old_role.value, "after": new_role.value}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AdminResult(
            success=True,
            data={"user": user.to_dict()}
        )

    def get_audit_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """
        Get audit logs with filters.

        Args:
            offset: Pagination offset
            limit: Max results
            user_id: Filter by admin user ID
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of audit logs
        """
        return self.storage.get_audit_logs(
            offset=offset,
            limit=limit,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
        )

    def export_users_csv(self) -> str:
        """
        Export users to CSV format.

        Returns:
            CSV string
        """
        users = self.auth_storage.list_users(offset=0, limit=10000)

        # CSV header
        csv = "ID,Email,Name,Role,Specialty,Institution,Active,License Tier,Created At,Last Login\n"

        # CSV rows
        for user in users:
            csv += f"{user.id},{user.email},{user.name},{user.role.value},"
            csv += f"{user.specialty or ''},{user.institution or ''},"
            csv += f"{user.is_active},{user.license_tier},"
            csv += f"{user.created_at.isoformat()},"
            csv += f"{user.last_login.isoformat() if user.last_login else ''}\n"

        return csv

    def export_subscriptions_csv(self) -> str:
        """
        Export subscriptions to CSV format.

        Returns:
            CSV string
        """
        # This would query all subscriptions from payment storage
        # For now, returning mock CSV
        csv = "ID,User ID,Plan,Status,Amount,Billing Cycle,Started At,Next Billing\n"
        return csv


# Global instance
_admin_service: Optional[AdminService] = None


def get_admin_service() -> AdminService:
    """Get admin service instance"""
    global _admin_service
    if _admin_service is None:
        _admin_service = AdminService()
    return _admin_service
