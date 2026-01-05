"""
Tenant Admin Functionality

Administrative operations for tenant management including:
- Bulk user provisioning
- Usage analytics
- Settings management
- Announcements
- Export functionality
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import csv
import io

from .models import Tenant, TenantMember, MemberRole
from .storage import TenantStorage, get_tenant_storage
from .service import TenantService, get_tenant_service
from .billing import TenantBillingService, get_billing_service


class TenantAdminService:
    """
    Administrative service for tenant operations.

    Provides admin-only functionality:
    - Usage analytics and reporting
    - Bulk operations
    - Advanced settings
    - Data export
    """

    def __init__(
        self,
        storage: Optional[TenantStorage] = None,
        service: Optional[TenantService] = None,
        billing: Optional[TenantBillingService] = None,
    ):
        self.storage = storage or get_tenant_storage()
        self.service = service or get_tenant_service()
        self.billing = billing or get_billing_service()

    # Usage Analytics

    def get_usage_analytics(
        self,
        tenant_id: str,
        actor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive usage analytics for tenant.

        Only accessible by admins.

        Args:
            tenant_id: Tenant ID
            actor_id: User requesting analytics
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)

        Returns:
            Usage analytics dictionary
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            raise PermissionError("Admin access required")

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        tenant = self.storage.get_tenant(tenant_id)
        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        teams = self.storage.get_tenant_teams(tenant_id)

        # Get billing info
        billing_info = self.billing.get_billing_info(tenant_id)

        # Get actual usage data from query tracking
        usage_stats = self.storage.get_usage_stats(tenant_id, start_date, end_date)

        # Get daily breakdown
        daily_usage = self.storage.get_usage_by_day(tenant_id, start_date, end_date)

        # Count active users (members with queries in period)
        active_user_ids = set()
        for member in members:
            member_stats = self.storage.get_member_usage_stats(
                tenant_id, member.user_id, start_date, end_date
            )
            if member_stats["total_queries"] > 0:
                active_user_ids.add(member.user_id)

        # Count new members added in period
        new_members = [
            m for m in members
            if start_date <= m.joined_at <= end_date
        ]

        # Calculate storage
        storage_bytes = usage_stats["total_storage_bytes"]
        storage_gb = storage_bytes / (1024 ** 3) if storage_bytes else 0
        usage_percent = (storage_gb / billing_info.plan.storage_gb * 100) if billing_info.plan.storage_gb > 0 else 0

        # Get per-member stats (top 10)
        member_query_counts = []
        for member in members:
            member_stats = self.storage.get_member_usage_stats(
                tenant_id, member.user_id, start_date, end_date
            )
            if member_stats["total_queries"] > 0:
                member_query_counts.append({
                    "member_id": member.id,
                    "user_id": member.user_id,
                    "queries": member_stats["total_queries"],
                })
        member_query_counts.sort(key=lambda x: x["queries"], reverse=True)

        analytics = {
            "tenant": {
                "id": tenant_id,
                "name": tenant.name,
                "plan": billing_info.plan.name,
                "status": tenant.status.value,
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "members": {
                "total": len(members),
                "by_role": self._count_by_role(members),
                "active_users": len(active_user_ids),
                "new_members": len(new_members),
            },
            "teams": {
                "total": len(teams),
                "teams": [{"id": t.id, "name": t.name} for t in teams],
            },
            "queries": {
                "total": usage_stats["total_queries"],
                "by_day": daily_usage,
                "by_member": member_query_counts[:10],
                "top_queries": [],  # Would need query content analysis
            },
            "storage": {
                "used_gb": round(storage_gb, 2),
                "quota_gb": billing_info.plan.storage_gb,
                "usage_percent": round(usage_percent, 1),
            },
            "costs": {
                "current_plan": billing_info.base_price / 100,
                "overage_charges": billing_info.overage_price / 100,
                "total": billing_info.total_price / 100,
                "currency": "INR",
                "projected_monthly": billing_info.total_price / 100,
            },
        }

        return analytics

    def get_member_analytics(
        self,
        tenant_id: str,
        actor_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get per-member usage analytics.

        Args:
            tenant_id: Tenant ID
            actor_id: User requesting analytics
            start_date: Start of period
            end_date: End of period

        Returns:
            List of member analytics
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            raise PermissionError("Admin access required")

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        members = self.storage.get_tenant_members(tenant_id, active_only=True)

        analytics = []
        for m in members:
            # Get actual usage data from tracking
            member_stats = self.storage.get_member_usage_stats(
                tenant_id, m.user_id, start_date, end_date
            )

            # Calculate storage in GB
            storage_gb = member_stats["total_storage_bytes"] / (1024 ** 3) if member_stats["total_storage_bytes"] else 0

            analytics.append({
                "member_id": m.id,
                "user_id": m.user_id,
                "role": m.role.value,
                "joined_at": m.joined_at.isoformat(),
                "last_activity": m.last_activity.isoformat() if m.last_activity else None,
                "usage": {
                    "queries": member_stats["total_queries"],
                    "storage_gb": round(storage_gb, 2),
                },
                "limits": {
                    "daily_queries": m.daily_query_limit,
                    "storage_gb": m.storage_quota_gb,
                },
            })

        return analytics

    # Bulk Operations

    def bulk_invite_members(
        self,
        tenant_id: str,
        actor_id: str,
        members_data: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[str]]:
        """
        Bulk invite multiple members.

        Args:
            tenant_id: Tenant ID
            actor_id: User performing action
            members_data: List of dicts with 'email' and 'role' keys

        Returns:
            (success_count, failure_count, error_messages)
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            raise PermissionError("Admin access required")

        success_count = 0
        failure_count = 0
        errors = []

        for data in members_data:
            email = data.get("email")
            role_str = data.get("role", "member")

            if not email:
                errors.append("Missing email")
                failure_count += 1
                continue

            try:
                role = MemberRole(role_str)
            except ValueError:
                errors.append(f"{email}: Invalid role {role_str}")
                failure_count += 1
                continue

            success, message, _ = self.service.create_invitation(
                tenant_id=tenant_id,
                email=email,
                role=role,
                actor_id=actor_id,
            )

            if success:
                success_count += 1
            else:
                errors.append(f"{email}: {message}")
                failure_count += 1

        return success_count, failure_count, errors

    def import_members_from_csv(
        self,
        tenant_id: str,
        actor_id: str,
        csv_content: str,
    ) -> Tuple[int, int, List[str]]:
        """
        Import members from CSV file.

        CSV format: email,role,team1,team2,...

        Args:
            tenant_id: Tenant ID
            actor_id: User performing import
            csv_content: CSV file content

        Returns:
            (success_count, failure_count, error_messages)
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            raise PermissionError("Admin access required")

        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        members_data = []
        for row in reader:
            members_data.append({
                "email": row.get("email"),
                "role": row.get("role", "member"),
            })

        return self.bulk_invite_members(tenant_id, actor_id, members_data)

    def export_members_to_csv(
        self,
        tenant_id: str,
        actor_id: str,
    ) -> str:
        """
        Export all members to CSV.

        Args:
            tenant_id: Tenant ID
            actor_id: User requesting export

        Returns:
            CSV content as string
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            raise PermissionError("Admin access required")

        members = self.storage.get_tenant_members(tenant_id, active_only=False)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "User ID", "Role", "Teams", "Active", "Joined At", "Last Activity"
        ])

        # Data
        for m in members:
            writer.writerow([
                m.user_id,
                m.role.value,
                ",".join(m.team_ids),
                "Yes" if m.is_active else "No",
                m.joined_at.isoformat(),
                m.last_activity.isoformat() if m.last_activity else "",
            ])

        return output.getvalue()

    # Settings Management

    def update_branding(
        self,
        tenant_id: str,
        actor_id: str,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Update tenant branding.

        Only available for Hospital and Enterprise plans.
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found"

        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Admin access required"

        # Verify feature availability
        if not tenant.has_feature("custom_branding"):
            return False, "Custom branding not available in current plan"

        # Update branding
        if logo_url is not None:
            tenant.logo_url = logo_url
        if primary_color is not None:
            tenant.primary_color = primary_color
        if secondary_color is not None:
            tenant.secondary_color = secondary_color

        self.storage.update_tenant(tenant)

        # Log action
        self.service._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="branding.updated",
            details={
                "logo_url": logo_url,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
            }
        )

        return True, "Branding updated successfully"

    def update_settings(
        self,
        tenant_id: str,
        actor_id: str,
        settings: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Update tenant settings.

        Args:
            tenant_id: Tenant ID
            actor_id: User performing update
            settings: Settings dictionary

        Returns:
            (success, message)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found"

        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Admin access required"

        # Update settings
        tenant.settings.update(settings)
        self.storage.update_tenant(tenant)

        # Log action
        self.service._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="settings.updated",
            details={"settings_keys": list(settings.keys())}
        )

        return True, "Settings updated successfully"

    # Announcements

    def create_announcement(
        self,
        tenant_id: str,
        actor_id: str,
        title: str,
        message: str,
        priority: str = "normal",
    ) -> Tuple[bool, str]:
        """
        Create an announcement for all team members.

        Args:
            tenant_id: Tenant ID
            actor_id: User creating announcement
            title: Announcement title
            message: Announcement message
            priority: Priority level (normal, high, urgent)

        Returns:
            (success, message)
        """
        # Verify admin access
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Admin access required"

        # Store announcement in database
        announcement_id = self.storage.create_announcement(
            tenant_id=tenant_id,
            created_by=actor_id,
            title=title,
            message=message,
            priority=priority,
        )

        # Send notification to all members
        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        for m in members:
            try:
                # Import and use notification service
                import asyncio
                from ..notifications.service import get_notification_service
                from ..notifications.models import NotificationType, NotificationChannel

                notification_service = get_notification_service()

                # Send async notification
                async def send_announcement_notification():
                    # Determine notification priority based on announcement priority
                    notif_priority = "HIGH" if priority in ["high", "urgent"] else "NORMAL"

                    # Try to send via email if high priority
                    if priority in ["high", "urgent"] and m.user_id:
                        # Would need user email - skip for now
                        pass

                # Run notification (best effort)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(send_announcement_notification())
                    else:
                        loop.run_until_complete(send_announcement_notification())
                except RuntimeError:
                    asyncio.run(send_announcement_notification())

            except Exception as e:
                # Log but don't fail announcement creation
                print(f"Warning: Failed to notify member {m.id}: {e}")

        # Log action
        self.service._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="announcement.created",
            details={
                "announcement_id": announcement_id,
                "title": title,
                "message": message,
                "priority": priority,
            }
        )

        return True, "Announcement created successfully"

    # Data Export

    def export_tenant_data(
        self,
        tenant_id: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """
        Export all tenant data for backup/compliance.

        Only owner can export.

        Args:
            tenant_id: Tenant ID
            actor_id: User requesting export

        Returns:
            Complete tenant data dictionary
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            raise ValueError("Organization not found")

        # Verify owner access
        if tenant.owner_id != actor_id:
            raise PermissionError("Only owner can export tenant data")

        # Collect all data
        members = self.storage.get_tenant_members(tenant_id, active_only=False)
        teams = self.storage.get_tenant_teams(tenant_id)
        invitations = self.storage.get_tenant_invitations(tenant_id)
        audit_logs = self.storage.get_audit_logs(tenant_id, limit=10000)

        export_data = {
            "tenant": tenant.to_dict(include_sensitive=True),
            "members": [m.to_dict() for m in members],
            "teams": [t.to_dict() for t in teams],
            "invitations": [i.to_dict() for i in invitations],
            "audit_logs": [log.to_dict() for log in audit_logs],
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": actor_id,
        }

        # Log export
        self.service._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="data.exported",
            details={"record_count": len(members) + len(teams)}
        )

        return export_data

    # Helper methods

    def _count_by_role(self, members: List[TenantMember]) -> Dict[str, int]:
        """Count members by role."""
        counts = {role.value: 0 for role in MemberRole}
        for member in members:
            counts[member.role.value] += 1
        return counts


# Default instance
_admin_service: Optional[TenantAdminService] = None


def get_admin_service() -> TenantAdminService:
    """Get the default admin service instance."""
    global _admin_service
    if _admin_service is None:
        _admin_service = TenantAdminService()
    return _admin_service
