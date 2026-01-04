"""
Tenant Data Models

Models for multi-tenant organization support including clinics,
hospitals, and enterprise healthcare organizations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class TenantType(str, Enum):
    """Type of tenant organization."""
    INDIVIDUAL = "individual"  # Single doctor
    CLINIC = "clinic"  # Small clinic/group practice
    HOSPITAL = "hospital"  # Hospital or large practice
    ENTERPRISE = "enterprise"  # Healthcare system/network


class MemberRole(str, Enum):
    """Member role within organization."""
    OWNER = "owner"  # Organization owner (full control)
    ADMIN = "admin"  # Administrator (manage members, settings)
    MEMBER = "member"  # Regular member (access features)
    VIEWER = "viewer"  # Read-only access


class InvitationStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TenantStatus(str, Enum):
    """Tenant organization status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


@dataclass
class TenantPlan:
    """Subscription plan for tenant organizations."""
    id: str
    name: str
    description: str
    tenant_type: TenantType

    # Pricing (in paise for INR)
    price_monthly: int
    price_quarterly: int
    price_yearly: int

    # Limits
    max_members: int
    storage_gb: int
    daily_queries_per_member: int

    # Features
    features: list[str] = field(default_factory=list)

    # Overage pricing (per additional member per month)
    overage_price_per_member: int = 0

    # Status
    is_active: bool = True


# Pre-defined tenant plans
TENANT_PLANS = {
    "clinic": TenantPlan(
        id="clinic",
        name="Clinic Plan",
        description="For small clinics and group practices (up to 5 doctors)",
        tenant_type=TenantType.CLINIC,
        price_monthly=499900,  # ₹4,999
        price_quarterly=1349700,  # ₹4,499 x 3
        price_yearly=4799900,  # ₹3,999.91 x 12
        max_members=5,
        storage_gb=100,
        daily_queries_per_member=500,
        overage_price_per_member=99900,  # ₹999 per additional member
        features=[
            "unlimited_queries",
            "drug_interactions",
            "voice_input",
            "offline_mode",
            "emr_integration",
            "priority_support",
            "academic_writing",
            "team_library",
            "usage_analytics",
        ],
    ),
    "hospital": TenantPlan(
        id="hospital",
        name="Hospital Plan",
        description="For hospitals and large practices (up to 25 doctors)",
        tenant_type=TenantType.HOSPITAL,
        price_monthly=1499900,  # ₹14,999
        price_quarterly=4049700,  # ₹13,499 x 3
        price_yearly=14399900,  # ₹11,999.91 x 12
        max_members=25,
        storage_gb=500,
        daily_queries_per_member=1000,
        overage_price_per_member=59900,  # ₹599 per additional member
        features=[
            "unlimited_queries",
            "drug_interactions",
            "voice_input",
            "offline_mode",
            "emr_integration",
            "priority_support",
            "academic_writing",
            "team_library",
            "usage_analytics",
            "custom_branding",
            "api_access",
            "sso",
            "advanced_analytics",
            "dedicated_support",
        ],
    ),
    "enterprise": TenantPlan(
        id="enterprise",
        name="Enterprise Plan",
        description="For healthcare systems and networks (unlimited users)",
        tenant_type=TenantType.ENTERPRISE,
        price_monthly=0,  # Custom pricing
        price_quarterly=0,
        price_yearly=0,
        max_members=-1,  # Unlimited
        storage_gb=-1,  # Unlimited
        daily_queries_per_member=-1,  # Unlimited
        overage_price_per_member=0,
        features=[
            "unlimited_queries",
            "drug_interactions",
            "voice_input",
            "offline_mode",
            "emr_integration",
            "priority_support",
            "academic_writing",
            "team_library",
            "usage_analytics",
            "custom_branding",
            "api_access",
            "sso",
            "advanced_analytics",
            "dedicated_support",
            "custom_integrations",
            "on_premise",
            "white_label",
            "sla",
        ],
    ),
}


@dataclass
class Tenant:
    """Healthcare organization (clinic, hospital, enterprise)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Basic info
    name: str = ""
    display_name: str = ""  # For custom branding
    tenant_type: TenantType = TenantType.CLINIC

    # Contact
    email: str = ""
    phone: Optional[str] = None
    website: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"

    # Business info
    registration_number: Optional[str] = None  # Business registration
    tax_id: Optional[str] = None  # GSTIN for India

    # Plan and billing
    plan_id: str = "clinic"
    billing_email: Optional[str] = None

    # Settings
    settings: dict = field(default_factory=dict)

    # Branding
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    # Features
    enabled_features: list[str] = field(default_factory=list)

    # Status
    status: TenantStatus = TenantStatus.TRIAL
    trial_ends_at: Optional[datetime] = None

    # Owner
    owner_id: str = ""  # User ID of organization owner

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # SSO Configuration (enterprise)
    sso_enabled: bool = False
    sso_provider: Optional[str] = None
    sso_domain: Optional[str] = None
    sso_config: dict = field(default_factory=dict)

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        plan = TENANT_PLANS.get(self.plan_id)
        if not plan:
            return False
        return feature in plan.features or feature in self.enabled_features

    def get_plan(self) -> Optional[TenantPlan]:
        """Get the tenant's plan."""
        return TENANT_PLANS.get(self.plan_id)

    def is_active(self) -> bool:
        """Check if tenant is active."""
        if self.status == TenantStatus.ACTIVE:
            return True
        if self.status == TenantStatus.TRIAL:
            if self.trial_ends_at and datetime.utcnow() < self.trial_ends_at:
                return True
        return False

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "tenant_type": self.tenant_type.value,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "plan_id": self.plan_id,
            "status": self.status.value,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "enabled_features": self.enabled_features,
            "settings": self.settings,
        }

        if include_sensitive:
            data["registration_number"] = self.registration_number
            data["tax_id"] = self.tax_id
            data["billing_email"] = self.billing_email
            data["sso_enabled"] = self.sso_enabled
            data["sso_config"] = self.sso_config

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Tenant":
        """Create from dictionary."""
        address = data.get("address", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            display_name=data.get("display_name", data.get("name", "")),
            tenant_type=TenantType(data.get("tenant_type", "clinic")),
            email=data.get("email", ""),
            phone=data.get("phone"),
            website=data.get("website"),
            address_line1=address.get("line1"),
            address_line2=address.get("line2"),
            city=address.get("city"),
            state=address.get("state"),
            postal_code=address.get("postal_code"),
            country=address.get("country", "India"),
            registration_number=data.get("registration_number"),
            tax_id=data.get("tax_id"),
            plan_id=data.get("plan_id", "clinic"),
            billing_email=data.get("billing_email"),
            settings=data.get("settings", {}),
            logo_url=data.get("logo_url"),
            primary_color=data.get("primary_color"),
            secondary_color=data.get("secondary_color"),
            enabled_features=data.get("enabled_features", []),
            status=TenantStatus(data.get("status", "trial")),
            trial_ends_at=datetime.fromisoformat(data["trial_ends_at"]) if data.get("trial_ends_at") else None,
            owner_id=data.get("owner_id", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            sso_enabled=data.get("sso_enabled", False),
            sso_provider=data.get("sso_provider"),
            sso_domain=data.get("sso_domain"),
            sso_config=data.get("sso_config", {}),
        )


@dataclass
class Team:
    """Team/Department within organization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""

    # Basic info
    name: str = ""
    description: str = ""

    # Settings
    settings: dict = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""  # User ID

    # Status
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "is_active": self.is_active,
        }


@dataclass
class TenantMember:
    """Member of a tenant organization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    user_id: str = ""

    # Role
    role: MemberRole = MemberRole.MEMBER

    # Team assignments
    team_ids: list[str] = field(default_factory=list)

    # Permissions
    custom_permissions: list[str] = field(default_factory=list)

    # Quota overrides (None = use plan defaults)
    daily_query_limit: Optional[int] = None
    storage_quota_gb: Optional[int] = None

    # Status
    is_active: bool = True

    # Timestamps
    joined_at: datetime = field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None  # User ID of inviter
    last_activity: Optional[datetime] = None

    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        # Owner and Admin have all permissions
        if self.role in [MemberRole.OWNER, MemberRole.ADMIN]:
            return True

        # Check custom permissions
        return permission in self.custom_permissions

    def can_manage_members(self) -> bool:
        """Check if member can manage other members."""
        return self.role in [MemberRole.OWNER, MemberRole.ADMIN]

    def can_manage_billing(self) -> bool:
        """Check if member can manage billing."""
        return self.role == MemberRole.OWNER

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "team_ids": self.team_ids,
            "custom_permissions": self.custom_permissions,
            "daily_query_limit": self.daily_query_limit,
            "storage_quota_gb": self.storage_quota_gb,
            "is_active": self.is_active,
            "joined_at": self.joined_at.isoformat(),
            "invited_by": self.invited_by,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TenantMember":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            user_id=data.get("user_id", ""),
            role=MemberRole(data.get("role", "member")),
            team_ids=data.get("team_ids", []),
            custom_permissions=data.get("custom_permissions", []),
            daily_query_limit=data.get("daily_query_limit"),
            storage_quota_gb=data.get("storage_quota_gb"),
            is_active=data.get("is_active", True),
            joined_at=datetime.fromisoformat(data["joined_at"]) if "joined_at" in data else datetime.utcnow(),
            invited_by=data.get("invited_by"),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
        )


@dataclass
class TenantInvitation:
    """Invitation to join a tenant organization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""

    # Invitee
    email: str = ""
    role: MemberRole = MemberRole.MEMBER
    team_ids: list[str] = field(default_factory=list)

    # Invitation
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: Optional[str] = None

    # Status
    status: InvitationStatus = InvitationStatus.PENDING

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    invited_by: str = ""  # User ID

    # Response
    accepted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if invitation is still valid."""
        if self.status != InvitationStatus.PENDING:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "role": self.role.value,
            "team_ids": self.team_ids,
            "token": self.token,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "invited_by": self.invited_by,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
        }


@dataclass
class TenantAuditLog:
    """Audit log entry for tenant operations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""

    # Action
    action: str = ""  # e.g., "member.added", "settings.updated", "billing.changed"
    actor_id: str = ""  # User ID who performed action
    target_id: Optional[str] = None  # ID of affected resource

    # Details
    details: dict = field(default_factory=dict)

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamp
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }


from datetime import timedelta
