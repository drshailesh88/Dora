"""
Multi-Tenant / Clinic Mode

Provides comprehensive multi-tenant support for clinics, hospitals,
and healthcare organizations.

Features:
- Organization management
- Team collaboration
- Member roles and permissions
- Tenant-scoped billing
- Data isolation (HIPAA compliant)
- Usage analytics
- Audit logging

Usage:
    from src.tenants import TenantService, get_tenant_context

    # Create organization
    service = TenantService()
    success, msg, tenant = service.create_organization(
        name="City General Hospital",
        email="admin@citygeneral.com",
        owner_id=user_id,
        plan_id="hospital"
    )

    # Set tenant context for requests
    from src.tenants.isolation import set_tenant_context
    ctx = set_tenant_context(tenant_id, user_id, member)

    # Operations are now scoped to tenant
    history = QueryHistory()
    history.save_query(question, answer)
"""

from .models import (
    Tenant,
    Team,
    TenantMember,
    TenantInvitation,
    TenantAuditLog,
    TenantType,
    MemberRole,
    InvitationStatus,
    TenantStatus,
    TenantPlan,
    TENANT_PLANS,
)

from .storage import (
    TenantStorage,
    get_tenant_storage,
)

from .service import (
    TenantService,
    get_tenant_service,
)

from .isolation import (
    TenantContext,
    set_tenant_context,
    get_tenant_context,
    clear_tenant_context,
    get_current_tenant_id,
    get_current_user_id,
    TenantIsolationError,
    require_tenant_context,
    require_permission,
    require_role,
    QueryHistory,
    UsageTracking,
    SharedLibrary,
)

from .billing import (
    TenantBillingService,
    BillingInfo,
    get_billing_service,
)

from .admin import (
    TenantAdminService,
    get_admin_service,
)

__all__ = [
    # Models
    "Tenant",
    "Team",
    "TenantMember",
    "TenantInvitation",
    "TenantAuditLog",
    "TenantType",
    "MemberRole",
    "InvitationStatus",
    "TenantStatus",
    "TenantPlan",
    "TENANT_PLANS",

    # Storage
    "TenantStorage",
    "get_tenant_storage",

    # Services
    "TenantService",
    "get_tenant_service",
    "TenantBillingService",
    "BillingInfo",
    "get_billing_service",
    "TenantAdminService",
    "get_admin_service",

    # Isolation
    "TenantContext",
    "set_tenant_context",
    "get_tenant_context",
    "clear_tenant_context",
    "get_current_tenant_id",
    "get_current_user_id",
    "TenantIsolationError",
    "require_tenant_context",
    "require_permission",
    "require_role",
    "QueryHistory",
    "UsageTracking",
    "SharedLibrary",
]
