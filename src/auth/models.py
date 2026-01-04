"""
Authentication Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    STAFF = "staff"
    RESIDENT = "resident"
    STUDENT = "student"

    @property
    def permissions(self) -> set[str]:
        """Get permissions for role"""
        base = {"query", "history.view", "drugs.check"}

        role_permissions = {
            UserRole.ADMIN: base | {
                "admin.users", "admin.licenses", "admin.analytics",
                "history.all", "settings.all", "patients.all"
            },
            UserRole.DOCTOR: base | {
                "patients.own", "history.own", "prescribe",
                "emr.write", "academic.write"
            },
            UserRole.NURSE: base | {
                "patients.view", "history.own", "vitals.record"
            },
            UserRole.STAFF: base | {
                "appointments", "billing", "patients.demographics"
            },
            UserRole.RESIDENT: base | {
                "patients.supervised", "history.own", "emr.draft"
            },
            UserRole.STUDENT: base | {
                "history.own"
            },
        }
        return role_permissions.get(self, base)


class AuthProvider(str, Enum):
    """Authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    APPLE = "apple"


@dataclass
class User:
    """User model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    role: UserRole = UserRole.DOCTOR
    provider: AuthProvider = AuthProvider.LOCAL
    provider_id: Optional[str] = None

    # Profile
    specialty: Optional[str] = None
    institution: Optional[str] = None
    registration_number: Optional[str] = None  # Medical license number
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    # Status
    is_active: bool = True
    is_verified: bool = False
    email_verified: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Password (hashed, only for local auth)
    password_hash: Optional[str] = None

    # MFA
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None

    # License
    license_tier: str = "FREE"
    organization_id: Optional[str] = None

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        return permission in self.role.permissions

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "provider": self.provider.value,
            "specialty": self.specialty,
            "institution": self.institution,
            "registration_number": self.registration_number,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "mfa_enabled": self.mfa_enabled,
            "license_tier": self.license_tier,
            "organization_id": self.organization_id,
        }

        if include_sensitive:
            data["provider_id"] = self.provider_id

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            email=data.get("email", ""),
            name=data.get("name", ""),
            role=UserRole(data.get("role", "doctor")),
            provider=AuthProvider(data.get("provider", "local")),
            provider_id=data.get("provider_id"),
            specialty=data.get("specialty"),
            institution=data.get("institution"),
            registration_number=data.get("registration_number"),
            phone=data.get("phone"),
            avatar_url=data.get("avatar_url"),
            is_active=data.get("is_active", True),
            is_verified=data.get("is_verified", False),
            email_verified=data.get("email_verified", False),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            password_hash=data.get("password_hash"),
            mfa_enabled=data.get("mfa_enabled", False),
            mfa_secret=data.get("mfa_secret"),
            license_tier=data.get("license_tier", "FREE"),
            organization_id=data.get("organization_id"),
        )


@dataclass
class Session:
    """User session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Tokens
    access_token: str = ""
    refresh_token: str = ""

    # Metadata
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)

    # Status
    is_active: bool = True
    revoked: bool = False
    revoked_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if session is still valid"""
        if not self.is_active or self.revoked:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


@dataclass
class TokenPair:
    """JWT token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # seconds

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
        }


@dataclass
class Organization:
    """Healthcare organization (for enterprise SSO)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: str = ""  # For domain-based SSO

    # SSO Config
    sso_provider: Optional[AuthProvider] = None
    sso_client_id: Optional[str] = None
    sso_tenant_id: Optional[str] = None  # For Microsoft

    # Settings
    max_users: int = 100
    allowed_roles: list[UserRole] = field(default_factory=lambda: [UserRole.DOCTOR, UserRole.NURSE, UserRole.STAFF])
    require_mfa: bool = False

    # License
    license_tier: str = "CLINIC"
    license_key: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
