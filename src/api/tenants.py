"""
Tenant API Endpoints

FastAPI endpoints for multi-tenant operations.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, EmailStr

from src.tenants import (
    TenantService, TenantBillingService, TenantAdminService,
    get_tenant_service, get_billing_service, get_admin_service,
    TenantType, MemberRole, InvitationStatus,
    TENANT_PLANS,
)
from src.auth.middleware import get_current_user
from src.auth.models import User


router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# Request/Response Models

class CreateTenantRequest(BaseModel):
    """Request to create a tenant organization."""
    name: str
    email: EmailStr
    tenant_type: TenantType = TenantType.CLINIC
    plan_id: str = "clinic"
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class UpdateTenantRequest(BaseModel):
    """Request to update tenant details."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    billing_email: Optional[EmailStr] = None


class AddMemberRequest(BaseModel):
    """Request to add a member."""
    user_id: str
    role: MemberRole = MemberRole.MEMBER
    team_ids: List[str] = []


class InviteMemberRequest(BaseModel):
    """Request to invite a member."""
    email: EmailStr
    role: MemberRole = MemberRole.MEMBER
    team_ids: List[str] = []
    message: Optional[str] = None


class BulkInviteRequest(BaseModel):
    """Request to bulk invite members."""
    members: List[dict]  # Each dict has email, role


class UpdateMemberRoleRequest(BaseModel):
    """Request to update member role."""
    role: MemberRole


class CreateTeamRequest(BaseModel):
    """Request to create a team."""
    name: str
    description: str = ""


class UpdateBrandingRequest(BaseModel):
    """Request to update branding."""
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class CreateAnnouncementRequest(BaseModel):
    """Request to create announcement."""
    title: str
    message: str
    priority: str = "normal"


# Tenant CRUD Endpoints

@router.post("/")
async def create_tenant(
    request: CreateTenantRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tenant organization.

    Creates organization with current user as owner.
    Starts with 14-day trial period.
    """
    service = get_tenant_service()

    success, message, tenant = service.create_organization(
        name=request.name,
        email=request.email,
        owner_id=current_user.id,
        tenant_type=request.tenant_type,
        plan_id=request.plan_id,
        phone=request.phone,
        website=request.website,
        address_line1=request.address_line1,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "tenant": tenant.to_dict() if tenant else None,
    }


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get tenant details."""
    service = get_tenant_service()
    storage = service.storage

    # Verify user is a member
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    tenant = service.get_organization(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "success": True,
        "tenant": tenant.to_dict(),
    }


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    current_user: User = Depends(get_current_user),
):
    """Update tenant details. Owner only."""
    service = get_tenant_service()

    updates = request.dict(exclude_unset=True)
    success, message, tenant = service.update_organization(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        **updates
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "tenant": tenant.to_dict() if tenant else None,
    }


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete tenant organization. Owner only."""
    service = get_tenant_service()

    success, message = service.delete_organization(
        tenant_id=tenant_id,
        actor_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


# Member Management

@router.post("/{tenant_id}/members")
async def add_member(
    tenant_id: str,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_user),
):
    """Add a member to the organization."""
    service = get_tenant_service()

    success, message, member = service.add_member(
        tenant_id=tenant_id,
        user_id=request.user_id,
        actor_id=current_user.id,
        role=request.role,
        team_ids=request.team_ids,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "member": member.to_dict() if member else None,
    }


@router.get("/{tenant_id}/members")
async def get_members(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get all members of the organization."""
    service = get_tenant_service()
    storage = service.storage

    # Verify user is a member
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    members = service.get_members(tenant_id)

    return {
        "success": True,
        "members": [m.to_dict() for m in members],
    }


@router.delete("/{tenant_id}/members/{member_id}")
async def remove_member(
    tenant_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
):
    """Remove a member from the organization."""
    service = get_tenant_service()

    success, message = service.remove_member(
        tenant_id=tenant_id,
        member_id=member_id,
        actor_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


@router.put("/{tenant_id}/members/{member_id}/role")
async def update_member_role(
    tenant_id: str,
    member_id: str,
    request: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
):
    """Update member role. Owner only."""
    service = get_tenant_service()

    success, message, member = service.update_member_role(
        tenant_id=tenant_id,
        member_id=member_id,
        new_role=request.role,
        actor_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "member": member.to_dict() if member else None,
    }


# Invitations

@router.post("/{tenant_id}/invitations")
async def create_invitation(
    tenant_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
):
    """Send an invitation to join the organization."""
    service = get_tenant_service()

    success, message, invitation = service.create_invitation(
        tenant_id=tenant_id,
        email=request.email,
        role=request.role,
        actor_id=current_user.id,
        team_ids=request.team_ids,
        message=request.message,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "invitation": invitation.to_dict() if invitation else None,
    }


@router.get("/{tenant_id}/invitations")
async def get_invitations(
    tenant_id: str,
    status: Optional[InvitationStatus] = None,
    current_user: User = Depends(get_current_user),
):
    """Get invitations for the organization."""
    service = get_tenant_service()
    storage = service.storage

    # Verify user is admin
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member or not member.can_manage_members():
        raise HTTPException(status_code=403, detail="Admin access required")

    invitations = service.get_invitations(tenant_id, status)

    return {
        "success": True,
        "invitations": [inv.to_dict() for inv in invitations],
    }


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
):
    """Accept an invitation."""
    service = get_tenant_service()

    success, message, member = service.accept_invitation(
        token=token,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "member": member.to_dict() if member else None,
    }


@router.post("/invitations/{token}/decline")
async def decline_invitation(token: str):
    """Decline an invitation."""
    service = get_tenant_service()

    success, message = service.decline_invitation(token)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


# Teams

@router.post("/{tenant_id}/teams")
async def create_team(
    tenant_id: str,
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a team/department."""
    service = get_tenant_service()

    success, message, team = service.create_team(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        actor_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "team": team.to_dict() if team else None,
    }


@router.get("/{tenant_id}/teams")
async def get_teams(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get all teams for the organization."""
    service = get_tenant_service()
    storage = service.storage

    # Verify user is a member
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    teams = service.get_teams(tenant_id)

    return {
        "success": True,
        "teams": [t.to_dict() for t in teams],
    }


@router.delete("/{tenant_id}/teams/{team_id}")
async def delete_team(
    tenant_id: str,
    team_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a team."""
    service = get_tenant_service()

    success, message = service.delete_team(
        tenant_id=tenant_id,
        team_id=team_id,
        actor_id=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


# Billing

@router.get("/{tenant_id}/billing")
async def get_billing_info(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get billing information for the organization."""
    billing_service = get_billing_service()
    storage = get_tenant_service().storage

    # Verify user is admin
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member or not member.can_manage_members():
        raise HTTPException(status_code=403, detail="Admin access required")

    billing_info = billing_service.get_billing_info(tenant_id)

    return {
        "success": True,
        "billing": {
            "plan": billing_info.plan.to_dict() if hasattr(billing_info.plan, 'to_dict') else billing_info.plan.name,
            "current_members": billing_info.current_members,
            "max_members": billing_info.max_members,
            "overage_members": billing_info.overage_members,
            "base_price": billing_info.base_price / 100,  # Convert to rupees
            "overage_price": billing_info.overage_price / 100,
            "total_price": billing_info.total_price / 100,
            "currency": billing_info.currency,
        },
    }


@router.get("/{tenant_id}/usage")
async def get_usage_analytics(
    tenant_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """Get usage analytics for the organization."""
    admin_service = get_admin_service()

    try:
        analytics = admin_service.get_usage_analytics(
            tenant_id=tenant_id,
            actor_id=current_user.id,
        )
        return {
            "success": True,
            "analytics": analytics,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{tenant_id}/usage/members")
async def get_member_analytics(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get per-member usage analytics."""
    admin_service = get_admin_service()

    try:
        analytics = admin_service.get_member_analytics(
            tenant_id=tenant_id,
            actor_id=current_user.id,
        )
        return {
            "success": True,
            "members": analytics,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Admin Operations

@router.post("/{tenant_id}/members/bulk-invite")
async def bulk_invite_members(
    tenant_id: str,
    request: BulkInviteRequest,
    current_user: User = Depends(get_current_user),
):
    """Bulk invite multiple members."""
    admin_service = get_admin_service()

    try:
        success_count, failure_count, errors = admin_service.bulk_invite_members(
            tenant_id=tenant_id,
            actor_id=current_user.id,
            members_data=request.members,
        )
        return {
            "success": True,
            "invited": success_count,
            "failed": failure_count,
            "errors": errors,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{tenant_id}/members/export")
async def export_members(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Export members to CSV."""
    admin_service = get_admin_service()

    try:
        csv_content = admin_service.export_members_to_csv(
            tenant_id=tenant_id,
            actor_id=current_user.id,
        )
        return {
            "success": True,
            "csv": csv_content,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{tenant_id}/branding")
async def update_branding(
    tenant_id: str,
    request: UpdateBrandingRequest,
    current_user: User = Depends(get_current_user),
):
    """Update tenant branding."""
    admin_service = get_admin_service()

    success, message = admin_service.update_branding(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        logo_url=request.logo_url,
        primary_color=request.primary_color,
        secondary_color=request.secondary_color,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


@router.post("/{tenant_id}/announcements")
async def create_announcement(
    tenant_id: str,
    request: CreateAnnouncementRequest,
    current_user: User = Depends(get_current_user),
):
    """Create an announcement for team members."""
    admin_service = get_admin_service()

    success, message = admin_service.create_announcement(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        title=request.title,
        message=request.message,
        priority=request.priority,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
    }


@router.get("/{tenant_id}/audit-logs")
async def get_audit_logs(
    tenant_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """Get audit logs for the organization."""
    service = get_tenant_service()
    storage = service.storage

    # Verify user is admin
    member = storage.get_member_by_user(tenant_id, current_user.id)
    if not member or not member.can_manage_members():
        raise HTTPException(status_code=403, detail="Admin access required")

    logs = service.get_audit_logs(tenant_id, limit, offset)

    return {
        "success": True,
        "logs": [log.to_dict() for log in logs],
    }


@router.get("/{tenant_id}/export")
async def export_tenant_data(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    """Export complete tenant data. Owner only."""
    admin_service = get_admin_service()

    try:
        data = admin_service.export_tenant_data(
            tenant_id=tenant_id,
            actor_id=current_user.id,
        )
        return {
            "success": True,
            "data": data,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Plans

@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    plans = []
    for plan_id, plan in TENANT_PLANS.items():
        plans.append({
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "tenant_type": plan.tenant_type.value,
            "pricing": {
                "monthly": plan.price_monthly / 100,
                "quarterly": plan.price_quarterly / 100,
                "yearly": plan.price_yearly / 100,
                "currency": "INR",
            },
            "limits": {
                "max_members": plan.max_members,
                "storage_gb": plan.storage_gb,
                "daily_queries_per_member": plan.daily_queries_per_member,
            },
            "features": plan.features,
            "overage_price_per_member": plan.overage_price_per_member / 100,
        })

    return {
        "success": True,
        "plans": plans,
    }
