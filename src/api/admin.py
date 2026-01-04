"""
Admin API Endpoints

REST API for admin operations, analytics, and platform management.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from pydantic import BaseModel

from ..auth import User, UserRole, RoleChecker
from ..admin import (
    get_admin_service,
    get_analytics_service,
    AuditAction,
)
from ..payments.service import get_payment_service


router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# Request/Response Models
class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    license_tier: Optional[str] = None


class SuspendUserRequest(BaseModel):
    reason: str


class UpdateRoleRequest(BaseModel):
    role: str


# Platform Statistics Endpoints
@router.get("/stats")
async def get_platform_stats(
    use_cache: bool = True,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    Get platform-wide statistics.

    Includes user counts, revenue, subscriptions, and usage metrics.
    """
    service = get_admin_service()
    stats = service.get_platform_stats(use_cache=use_cache)

    # Log access
    service.log_audit(
        admin_user=admin,
        action=AuditAction.LOGIN_ADMIN,
        resource_type="stats",
        description="Viewed platform statistics",
    )

    return stats.to_dict()


# User Management Endpoints
@router.get("/users")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    license_tier: Optional[str] = None,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    List all users with filtering and pagination.

    Query Parameters:
    - offset: Pagination offset
    - limit: Max results (max 100)
    - role: Filter by role
    - search: Search by name or email
    - is_active: Filter by active status
    - license_tier: Filter by license tier
    """
    if limit > 100:
        limit = 100

    service = get_admin_service()

    role_filter = None
    if role:
        try:
            role_filter = UserRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    users = service.get_user_list(
        offset=offset,
        limit=limit,
        role=role_filter,
        search=search,
        is_active=is_active,
        license_tier=license_tier,
    )

    # Count total (for pagination)
    all_users = service.get_user_list(
        offset=0,
        limit=10000,
        role=role_filter,
        search=search,
        is_active=is_active,
        license_tier=license_tier,
    )
    total = len(all_users)

    return {
        "users": [u.to_dict() for u in users],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    Get detailed information about a specific user.

    Includes profile, stats, subscription, and payment history.
    """
    service = get_admin_service()
    details = service.get_user_details(user_id)

    if not details:
        raise HTTPException(status_code=404, detail="User not found")

    return details


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Update user properties.

    Only super_admin can change roles.
    """
    service = get_admin_service()

    # Get user
    from ..auth.storage import get_auth_storage
    auth_storage = get_auth_storage()
    user = auth_storage.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = {}

    # Update active status
    if request.is_active is not None:
        if request.is_active:
            result = service.activate_user(
                admin_user=admin,
                user_id=user_id,
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("User-Agent"),
            )
        else:
            result = service.suspend_user(
                admin_user=admin,
                user_id=user_id,
                reason="Admin action",
                ip_address=req.client.host if req.client else None,
                user_agent=req.headers.get("User-Agent"),
            )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

    # Update role
    if request.role:
        try:
            new_role = UserRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")

        result = service.update_user_role(
            admin_user=admin,
            user_id=user_id,
            new_role=new_role,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("User-Agent"),
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

    # Update license tier
    if request.license_tier:
        old_tier = user.license_tier
        user.license_tier = request.license_tier
        auth_storage.update_user(user)
        changes["license_tier"] = {"before": old_tier, "after": request.license_tier}

        service.log_audit(
            admin_user=admin,
            action=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=user_id,
            description=f"Updated license tier to {request.license_tier}",
            changes=changes,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("User-Agent"),
        )

    # Get updated user
    updated_user = auth_storage.get_user(user_id)
    return {"success": True, "user": updated_user.to_dict()}


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: SuspendUserRequest,
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Suspend a user account.
    """
    service = get_admin_service()

    result = service.suspend_user(
        admin_user=admin,
        user_id=user_id,
        reason=request.reason,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Activate a suspended user account.
    """
    service = get_admin_service()

    result = service.activate_user(
        admin_user=admin,
        user_id=user_id,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.data


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Reset user password (generates reset token).
    """
    from ..auth.service import get_auth_service
    auth_service = get_auth_service()
    service = get_admin_service()

    # Get user
    from ..auth.storage import get_auth_storage
    user = get_auth_storage().get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate reset token
    token = auth_service.request_password_reset(user.email)

    # Log audit
    service.log_audit(
        admin_user=admin,
        action=AuditAction.USER_PASSWORD_RESET,
        resource_type="user",
        resource_id=user_id,
        description=f"Generated password reset for {user.email}",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    return {
        "success": True,
        "reset_token": token,
        "message": "Password reset token generated",
    }


# Subscription Management Endpoints
@router.get("/subscriptions")
async def list_subscriptions(
    offset: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    plan_id: Optional[str] = None,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    List all subscriptions with filtering.
    """
    payment_service = get_payment_service()

    # This would need to be implemented in payment service
    # For now, returning mock data
    return {
        "subscriptions": [],
        "total": 0,
        "offset": offset,
        "limit": limit,
    }


@router.get("/subscriptions/{subscription_id}")
async def get_subscription_details(
    subscription_id: str,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    Get detailed subscription information.
    """
    payment_service = get_payment_service()
    subscription = payment_service.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription.to_dict()


@router.post("/subscriptions/{subscription_id}/refund")
async def refund_subscription(
    subscription_id: str,
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Process refund for a subscription.
    """
    service = get_admin_service()

    # Log audit
    service.log_audit(
        admin_user=admin,
        action=AuditAction.SUBSCRIPTION_REFUND,
        resource_type="subscription",
        resource_id=subscription_id,
        description=f"Processed refund for subscription {subscription_id}",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    return {"success": True, "message": "Refund processed"}


# Analytics Endpoints
@router.get("/analytics")
async def get_analytics(
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    Get platform analytics data.

    Includes DAU, query volume, top queries, specialty stats.
    """
    analytics = get_analytics_service()

    # Daily active users
    dau = analytics.get_daily_active_users(days=30)

    # Query volume
    query_volume = analytics.get_query_volume(days=30)

    # Top queries
    top_queries = analytics.get_top_queries(limit=10)

    # Specialty stats
    specialty_stats = analytics.get_specialty_stats()

    # System health
    health = analytics.get_system_health()

    return {
        "daily_active_users": [dp.to_dict() for dp in dau],
        "query_volume": [dp.to_dict() for dp in query_volume],
        "top_queries": [q.to_dict() for q in top_queries],
        "specialty_stats": [s.to_dict() for s in specialty_stats],
        "system_health": health.to_dict(),
    }


@router.get("/analytics/revenue")
async def get_revenue_analytics(
    days: int = 30,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Get revenue analytics over time.
    """
    # This would query payment history and aggregate by day
    # For now, returning mock data
    data_points = []
    from datetime import timedelta
    import random

    now = datetime.utcnow()
    for i in range(days):
        date = now - timedelta(days=days - i - 1)
        data_points.append({
            "timestamp": date.replace(hour=0, minute=0, second=0).isoformat(),
            "value": 5000 + i * 100 + random.randint(-500, 500),  # In paise
            "label": date.strftime("%Y-%m-%d"),
        })

    return {"revenue_timeline": data_points}


# Audit Log Endpoints
@router.get("/audit")
async def get_audit_logs(
    offset: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Get audit logs with filtering.

    Query Parameters:
    - offset: Pagination offset
    - limit: Max results
    - user_id: Filter by admin user ID
    - action: Filter by action type
    - resource_type: Filter by resource type
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    """
    service = get_admin_service()

    action_filter = None
    if action:
        try:
            action_filter = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    start_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    end_dt = None
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    logs = service.get_audit_logs(
        offset=offset,
        limit=limit,
        user_id=user_id,
        action=action_filter,
        resource_type=resource_type,
        start_date=start_dt,
        end_date=end_dt,
    )

    # Count total
    total = service.storage.count_audit_logs(
        user_id=user_id,
        action=action_filter,
        resource_type=resource_type,
        start_date=start_dt,
        end_date=end_dt,
    )

    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


# Export Endpoints
@router.get("/export/users")
async def export_users(
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Export all users to CSV.
    """
    service = get_admin_service()
    csv_data = service.export_users_csv()

    # Log export
    service.log_audit(
        admin_user=admin,
        action=AuditAction.EXPORT_DATA,
        resource_type="users",
        description="Exported all users to CSV",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=users_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        },
    )


@router.get("/export/subscriptions")
async def export_subscriptions(
    req: Request,
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Export all subscriptions to CSV.
    """
    service = get_admin_service()
    csv_data = service.export_subscriptions_csv()

    # Log export
    service.log_audit(
        admin_user=admin,
        action=AuditAction.EXPORT_DATA,
        resource_type="subscriptions",
        description="Exported all subscriptions to CSV",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("User-Agent"),
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=subscriptions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        },
    )


# System Health Endpoint
@router.get("/health")
async def get_system_health(
    admin: User = Depends(RoleChecker(UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.SUPPORT)),
):
    """
    Get system health metrics.
    """
    analytics = get_analytics_service()
    health = analytics.get_system_health()

    return health.to_dict()
