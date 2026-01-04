"""
Admin Data Models

Models for admin operations, analytics, and audit logging.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class AuditAction(str, Enum):
    """Audit log action types"""
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"
    USER_DELETE = "user_delete"
    USER_PASSWORD_RESET = "user_password_reset"

    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    SUBSCRIPTION_REFUND = "subscription_refund"

    CONTENT_CREATE = "content_create"
    CONTENT_UPDATE = "content_update"
    CONTENT_DELETE = "content_delete"

    NOTIFICATION_SEND = "notification_send"
    NOTIFICATION_CREATE_TEMPLATE = "notification_create_template"

    SETTINGS_UPDATE = "settings_update"
    SYSTEM_CONFIG = "system_config"

    LOGIN_ADMIN = "login_admin"
    EXPORT_DATA = "export_data"


@dataclass
class AuditLog:
    """Audit log entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Who
    user_id: str = ""
    user_email: str = ""
    user_role: str = ""

    # What
    action: AuditAction = AuditAction.LOGIN_ADMIN
    resource_type: str = ""  # "user", "subscription", "content", etc.
    resource_id: Optional[str] = None

    # Details
    description: str = ""
    changes: Optional[dict] = None  # Before/after for updates
    metadata: Optional[dict] = None

    # When/Where
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Result
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "description": self.description,
            "changes": self.changes,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditLog":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            user_email=data.get("user_email", ""),
            user_role=data.get("user_role", ""),
            action=AuditAction(data.get("action", "login_admin")),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id"),
            description=data.get("description", ""),
            changes=data.get("changes"),
            metadata=data.get("metadata"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            success=data.get("success", True),
            error=data.get("error"),
        )


@dataclass
class PlatformStats:
    """Platform-wide statistics"""
    # Users
    total_users: int = 0
    active_users: int = 0
    inactive_users: int = 0
    trial_users: int = 0
    paid_users: int = 0
    new_users_today: int = 0
    new_users_this_week: int = 0
    new_users_this_month: int = 0

    # Revenue
    total_revenue: int = 0  # All time in paise/cents
    revenue_today: int = 0
    revenue_this_week: int = 0
    revenue_this_month: int = 0
    mrr: int = 0  # Monthly Recurring Revenue
    arr: int = 0  # Annual Recurring Revenue

    # Subscriptions
    active_subscriptions: int = 0
    trial_subscriptions: int = 0
    cancelled_subscriptions: int = 0
    failed_payments: int = 0

    # Usage
    queries_today: int = 0
    queries_this_week: int = 0
    queries_this_month: int = 0
    total_queries: int = 0

    # System
    storage_used_mb: float = 0
    api_requests_today: int = 0
    error_rate_percent: float = 0
    avg_response_time_ms: float = 0

    # Timestamp
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total_users": self.total_users,
            "active_users": self.active_users,
            "inactive_users": self.inactive_users,
            "trial_users": self.trial_users,
            "paid_users": self.paid_users,
            "new_users_today": self.new_users_today,
            "new_users_this_week": self.new_users_this_week,
            "new_users_this_month": self.new_users_this_month,
            "total_revenue": self.total_revenue,
            "revenue_today": self.revenue_today,
            "revenue_this_week": self.revenue_this_week,
            "revenue_this_month": self.revenue_this_month,
            "mrr": self.mrr,
            "arr": self.arr,
            "active_subscriptions": self.active_subscriptions,
            "trial_subscriptions": self.trial_subscriptions,
            "cancelled_subscriptions": self.cancelled_subscriptions,
            "failed_payments": self.failed_payments,
            "queries_today": self.queries_today,
            "queries_this_week": self.queries_this_week,
            "queries_this_month": self.queries_this_month,
            "total_queries": self.total_queries,
            "storage_used_mb": self.storage_used_mb,
            "api_requests_today": self.api_requests_today,
            "error_rate_percent": self.error_rate_percent,
            "avg_response_time_ms": self.avg_response_time_ms,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class UserStats:
    """User-specific statistics"""
    user_id: str

    # Activity
    total_queries: int = 0
    queries_this_week: int = 0
    queries_this_month: int = 0
    last_query_at: Optional[datetime] = None

    # Subscription
    subscription_status: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_started_at: Optional[datetime] = None
    total_paid: int = 0  # Lifetime value in paise/cents

    # Engagement
    login_count: int = 0
    last_login_at: Optional[datetime] = None
    session_count: int = 0
    avg_session_duration_minutes: float = 0

    # Features
    drug_checks: int = 0
    documents_uploaded: int = 0
    favorites_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "total_queries": self.total_queries,
            "queries_this_week": self.queries_this_week,
            "queries_this_month": self.queries_this_month,
            "last_query_at": self.last_query_at.isoformat() if self.last_query_at else None,
            "subscription_status": self.subscription_status,
            "subscription_plan": self.subscription_plan,
            "subscription_started_at": self.subscription_started_at.isoformat() if self.subscription_started_at else None,
            "total_paid": self.total_paid,
            "login_count": self.login_count,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "session_count": self.session_count,
            "avg_session_duration_minutes": self.avg_session_duration_minutes,
            "drug_checks": self.drug_checks,
            "documents_uploaded": self.documents_uploaded,
            "favorites_count": self.favorites_count,
        }


@dataclass
class AnalyticsDataPoint:
    """Time-series data point for analytics"""
    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass
class TopQuery:
    """Popular query statistics"""
    query: str
    count: int
    avg_response_time_ms: float
    success_rate: float
    last_queried_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "count": self.count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "success_rate": self.success_rate,
            "last_queried_at": self.last_queried_at.isoformat(),
        }


@dataclass
class SpecialtyStats:
    """Specialty-wise usage statistics"""
    specialty: str
    user_count: int
    query_count: int
    avg_queries_per_user: float

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "specialty": self.specialty,
            "user_count": self.user_count,
            "query_count": self.query_count,
            "avg_queries_per_user": self.avg_queries_per_user,
        }


@dataclass
class SystemHealth:
    """System health metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Services
    api_status: str = "healthy"  # healthy, degraded, down
    database_status: str = "healthy"
    vector_db_status: str = "healthy"
    llm_status: str = "healthy"
    payment_status: str = "healthy"

    # Resources
    cpu_usage_percent: float = 0
    memory_usage_percent: float = 0
    disk_usage_percent: float = 0

    # Performance
    avg_query_latency_ms: float = 0
    p95_query_latency_ms: float = 0
    error_rate_percent: float = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "api_status": self.api_status,
            "database_status": self.database_status,
            "vector_db_status": self.vector_db_status,
            "llm_status": self.llm_status,
            "payment_status": self.payment_status,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "disk_usage_percent": self.disk_usage_percent,
            "avg_query_latency_ms": self.avg_query_latency_ms,
            "p95_query_latency_ms": self.p95_query_latency_ms,
            "error_rate_percent": self.error_rate_percent,
        }
