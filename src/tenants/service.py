"""
Tenant Management Service

Central service for all tenant operations including:
- Organization creation and management
- Member management
- Team management
- Invitations
- Audit logging
"""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import secrets
import os

from .models import (
    Tenant, Team, TenantMember, TenantInvitation, TenantAuditLog,
    MemberRole, InvitationStatus, TenantStatus, TenantType, TENANT_PLANS
)
from .storage import TenantStorage, get_tenant_storage
from .billing import TenantBillingService, get_billing_service


class TenantService:
    """
    Central service for tenant operations.

    Provides high-level operations for:
    - Creating and managing organizations
    - Member and team management
    - Invitations
    - Audit logging
    """

    def __init__(
        self,
        storage: Optional[TenantStorage] = None,
        billing: Optional[TenantBillingService] = None,
    ):
        self.storage = storage or get_tenant_storage()
        self.billing = billing or get_billing_service()

    # Organization management

    def create_organization(
        self,
        name: str,
        email: str,
        owner_id: str,
        tenant_type: TenantType = TenantType.CLINIC,
        plan_id: str = "clinic",
        trial_days: int = 14,
        **kwargs,
    ) -> Tuple[bool, str, Optional[Tenant]]:
        """
        Create a new tenant organization.

        Args:
            name: Organization name
            email: Organization email
            owner_id: User ID of owner
            tenant_type: Type of organization
            plan_id: Subscription plan
            trial_days: Trial period in days
            **kwargs: Additional tenant fields

        Returns:
            (success, message, tenant)
        """
        # Check if user already owns a tenant
        existing = self.storage.get_tenant_by_owner(owner_id)
        if existing:
            return False, "User already owns an organization", None

        # Validate plan
        if plan_id not in TENANT_PLANS:
            return False, f"Invalid plan: {plan_id}", None

        # Create tenant
        tenant = Tenant(
            name=name,
            display_name=kwargs.get("display_name", name),
            tenant_type=tenant_type,
            email=email,
            owner_id=owner_id,
            plan_id=plan_id,
            status=TenantStatus.TRIAL,
            trial_ends_at=datetime.utcnow() + timedelta(days=trial_days),
            **{k: v for k, v in kwargs.items() if k in [
                "phone", "website", "address_line1", "address_line2",
                "city", "state", "postal_code", "country",
                "registration_number", "tax_id", "billing_email"
            ]}
        )

        self.storage.create_tenant(tenant)

        # Add owner as member
        owner_member = TenantMember(
            tenant_id=tenant.id,
            user_id=owner_id,
            role=MemberRole.OWNER,
        )
        self.storage.add_member(owner_member)

        # Log creation
        self._log_action(
            tenant_id=tenant.id,
            actor_id=owner_id,
            action="tenant.created",
            details={"plan_id": plan_id, "trial_days": trial_days}
        )

        return True, "Organization created successfully", tenant

    def get_organization(self, tenant_id: str) -> Optional[Tenant]:
        """Get organization by ID."""
        return self.storage.get_tenant(tenant_id)

    def update_organization(
        self,
        tenant_id: str,
        actor_id: str,
        **updates,
    ) -> Tuple[bool, str, Optional[Tenant]]:
        """
        Update organization details.

        Only owner can update.
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found", None

        # Verify actor is owner
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or member.role != MemberRole.OWNER:
            return False, "Only owner can update organization details", None

        # Update fields
        updated_fields = []
        for field, value in updates.items():
            if hasattr(tenant, field):
                setattr(tenant, field, value)
                updated_fields.append(field)

        self.storage.update_tenant(tenant)

        # Log update
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="tenant.updated",
            details={"updated_fields": updated_fields}
        )

        return True, "Organization updated successfully", tenant

    def delete_organization(
        self,
        tenant_id: str,
        actor_id: str,
    ) -> Tuple[bool, str]:
        """
        Delete organization.

        Only owner can delete. Cascades to all members, teams, etc.
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found"

        # Verify actor is owner
        if tenant.owner_id != actor_id:
            return False, "Only owner can delete organization"

        # Cancel subscription if active
        try:
            self.billing.cancel_subscription(tenant_id, immediate=True)
        except Exception as e:
            # Log but don't block deletion
            print(f"Warning: Failed to cancel subscription: {e}")

        # Export data for user (for compliance/backup)
        try:
            from .admin import TenantAdminService
            admin_service = TenantAdminService(self.storage, self, self.billing)
            export_data = admin_service.export_tenant_data(tenant_id, actor_id)
            # Save export data to file
            import json
            from pathlib import Path
            export_dir = Path.home() / ".dora" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            export_file = export_dir / f"{tenant_id}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"Data exported to: {export_file}")
        except Exception as e:
            print(f"Warning: Failed to export data: {e}")

        # Delete tenant (cascade deletes members, teams, etc)
        self.storage.delete_tenant(tenant_id)

        return True, "Organization deleted successfully"

    # Member management

    def add_member(
        self,
        tenant_id: str,
        user_id: str,
        actor_id: str,
        role: MemberRole = MemberRole.MEMBER,
        team_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, str, Optional[TenantMember]]:
        """
        Add a member to the organization.

        Args:
            tenant_id: Tenant ID
            user_id: User ID to add
            actor_id: User performing the action
            role: Member role
            team_ids: Teams to add member to

        Returns:
            (success, message, member)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found", None

        # Verify actor can manage members
        actor_member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not actor_member or not actor_member.can_manage_members():
            return False, "Permission denied: Cannot manage members", None

        # Check if user is already a member
        existing = self.storage.get_member_by_user(tenant_id, user_id)
        if existing:
            return False, "User is already a member", None

        # Check member limit
        members = self.storage.get_tenant_members(tenant_id, active_only=True)
        plan = TENANT_PLANS.get(tenant.plan_id)
        if plan and plan.max_members > 0 and len(members) >= plan.max_members:
            return False, f"Member limit reached ({plan.max_members}). Please upgrade your plan.", None

        # Create member
        member = TenantMember(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            team_ids=team_ids or [],
            invited_by=actor_id,
        )

        self.storage.add_member(member)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="member.added",
            target_id=member.id,
            details={"user_id": user_id, "role": role.value}
        )

        return True, "Member added successfully", member

    def remove_member(
        self,
        tenant_id: str,
        member_id: str,
        actor_id: str,
    ) -> Tuple[bool, str]:
        """
        Remove a member from the organization.

        Cannot remove owner.
        """
        member = self.storage.get_member(member_id)
        if not member or member.tenant_id != tenant_id:
            return False, "Member not found"

        # Cannot remove owner
        if member.role == MemberRole.OWNER:
            return False, "Cannot remove organization owner"

        # Verify actor can manage members
        actor_member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not actor_member or not actor_member.can_manage_members():
            return False, "Permission denied: Cannot manage members"

        # Remove member
        self.storage.remove_member(member_id)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="member.removed",
            target_id=member_id,
            details={"user_id": member.user_id}
        )

        return True, "Member removed successfully"

    def update_member_role(
        self,
        tenant_id: str,
        member_id: str,
        new_role: MemberRole,
        actor_id: str,
    ) -> Tuple[bool, str, Optional[TenantMember]]:
        """
        Update a member's role.

        Only owner can change roles.
        Cannot change owner role.
        """
        member = self.storage.get_member(member_id)
        if not member or member.tenant_id != tenant_id:
            return False, "Member not found", None

        # Cannot change owner role
        if member.role == MemberRole.OWNER:
            return False, "Cannot change owner role", None

        # Verify actor is owner
        actor_member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not actor_member or actor_member.role != MemberRole.OWNER:
            return False, "Only owner can change member roles", None

        old_role = member.role
        member.role = new_role
        self.storage.update_member(member)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="member.role_changed",
            target_id=member_id,
            details={"old_role": old_role.value, "new_role": new_role.value}
        )

        return True, "Member role updated successfully", member

    def get_members(self, tenant_id: str) -> List[TenantMember]:
        """Get all members of an organization."""
        return self.storage.get_tenant_members(tenant_id, active_only=True)

    # Team management

    def create_team(
        self,
        tenant_id: str,
        name: str,
        description: str,
        actor_id: str,
    ) -> Tuple[bool, str, Optional[Team]]:
        """Create a team/department within organization."""
        # Verify actor is admin
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Permission denied: Admin access required", None

        team = Team(
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_by=actor_id,
        )

        self.storage.create_team(team)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="team.created",
            target_id=team.id,
            details={"name": name}
        )

        return True, "Team created successfully", team

    def get_teams(self, tenant_id: str) -> List[Team]:
        """Get all teams for an organization."""
        return self.storage.get_tenant_teams(tenant_id)

    def delete_team(
        self,
        tenant_id: str,
        team_id: str,
        actor_id: str,
    ) -> Tuple[bool, str]:
        """Delete a team."""
        team = self.storage.get_team(team_id)
        if not team or team.tenant_id != tenant_id:
            return False, "Team not found"

        # Verify actor is admin
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Permission denied: Admin access required"

        self.storage.delete_team(team_id)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="team.deleted",
            target_id=team_id,
            details={"name": team.name}
        )

        return True, "Team deleted successfully"

    # Invitation management

    def create_invitation(
        self,
        tenant_id: str,
        email: str,
        role: MemberRole,
        actor_id: str,
        team_ids: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[TenantInvitation]]:
        """
        Create an invitation to join the organization.

        Args:
            tenant_id: Tenant ID
            email: Invitee email
            role: Role to assign
            actor_id: User sending invitation
            team_ids: Teams to add invitee to
            message: Optional personal message

        Returns:
            (success, message, invitation)
        """
        tenant = self.storage.get_tenant(tenant_id)
        if not tenant:
            return False, "Organization not found", None

        # Verify actor can manage members
        member = self.storage.get_member_by_user(tenant_id, actor_id)
        if not member or not member.can_manage_members():
            return False, "Permission denied: Cannot invite members", None

        # Check if email already has pending invitation
        existing_invitations = self.storage.get_tenant_invitations(tenant_id, InvitationStatus.PENDING)
        for inv in existing_invitations:
            if inv.email == email and inv.is_valid():
                return False, "Pending invitation already exists for this email", None

        # Create invitation
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            team_ids=team_ids or [],
            message=message,
            invited_by=actor_id,
        )

        self.storage.create_invitation(invitation)

        # Send invitation email
        self._send_invitation_email(tenant, invitation)

        # Log action
        self._log_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="invitation.sent",
            target_id=invitation.id,
            details={"email": email, "role": role.value}
        )

        return True, "Invitation sent successfully", invitation

    def accept_invitation(
        self,
        token: str,
        user_id: str,
    ) -> Tuple[bool, str, Optional[TenantMember]]:
        """
        Accept an invitation.

        Args:
            token: Invitation token
            user_id: User accepting the invitation

        Returns:
            (success, message, member)
        """
        invitation = self.storage.get_invitation_by_token(token)
        if not invitation:
            return False, "Invalid invitation token", None

        if not invitation.is_valid():
            return False, "Invitation has expired or is no longer valid", None

        # Add member to organization
        success, message, member = self.add_member(
            tenant_id=invitation.tenant_id,
            user_id=user_id,
            actor_id=invitation.invited_by,
            role=invitation.role,
            team_ids=invitation.team_ids,
        )

        if not success:
            return False, message, None

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        self.storage.update_invitation(invitation)

        # Log action
        self._log_action(
            tenant_id=invitation.tenant_id,
            actor_id=user_id,
            action="invitation.accepted",
            target_id=invitation.id,
            details={"email": invitation.email}
        )

        return True, "Invitation accepted successfully", member

    def decline_invitation(
        self,
        token: str,
    ) -> Tuple[bool, str]:
        """Decline an invitation."""
        invitation = self.storage.get_invitation_by_token(token)
        if not invitation:
            return False, "Invalid invitation token"

        if invitation.status != InvitationStatus.PENDING:
            return False, "Invitation is no longer pending"

        invitation.status = InvitationStatus.DECLINED
        invitation.declined_at = datetime.utcnow()
        self.storage.update_invitation(invitation)

        return True, "Invitation declined"

    def get_invitations(
        self,
        tenant_id: str,
        status: Optional[InvitationStatus] = None,
    ) -> List[TenantInvitation]:
        """Get invitations for an organization."""
        return self.storage.get_tenant_invitations(tenant_id, status)

    # Audit logging

    def _log_action(
        self,
        tenant_id: str,
        actor_id: str,
        action: str,
        target_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Internal method to log tenant actions."""
        log = TenantAuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.storage.add_audit_log(log)

    def get_audit_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TenantAuditLog]:
        """Get audit logs for an organization."""
        return self.storage.get_audit_logs(tenant_id, limit, offset)

    def _send_invitation_email(self, tenant: Tenant, invitation: TenantInvitation):
        """Send invitation email to invitee."""
        try:
            # Import notification service
            import asyncio
            from ..notifications.service import get_notification_service
            from ..notifications.models import NotificationType, NotificationChannel

            notification_service = get_notification_service()

            # Build invitation URL
            base_url = os.environ.get("APP_BASE_URL", "https://docassist.in")
            invitation_url = f"{base_url}/invitations/accept?token={invitation.token}"

            # Send email asynchronously
            async def send():
                await notification_service.send(
                    user_id=invitation.invited_by,
                    notification_type=NotificationType.CUSTOM,
                    channel=NotificationChannel.EMAIL,
                    recipient=invitation.email,
                    context={
                        "tenant_name": tenant.display_name or tenant.name,
                        "role": invitation.role.value,
                        "invitation_url": invitation_url,
                        "expires_days": (invitation.expires_at - datetime.utcnow()).days,
                        "personal_message": invitation.message or "",
                    },
                    priority="NORMAL",
                )

            # Run async function
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a task
                    asyncio.create_task(send())
                else:
                    # If loop is not running, run until complete
                    loop.run_until_complete(send())
            except RuntimeError:
                # If no event loop, create new one
                asyncio.run(send())

        except Exception as e:
            # Log error but don't fail invitation creation
            print(f"Warning: Failed to send invitation email: {e}")


# Default instance
_tenant_service: Optional[TenantService] = None


def get_tenant_service() -> TenantService:
    """Get the default tenant service instance."""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService()
    return _tenant_service
