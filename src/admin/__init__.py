"""
Admin Module

Admin operations, analytics, and audit logging.
"""

from .models import (
    AuditLog,
    AuditAction,
    PlatformStats,
    UserStats,
    AnalyticsDataPoint,
    TopQuery,
    SpecialtyStats,
    SystemHealth,
)
from .storage import AdminStorage, get_admin_storage
from .analytics import AnalyticsService, get_analytics_service
from .service import AdminService, AdminResult, get_admin_service

__all__ = [
    # Models
    "AuditLog",
    "AuditAction",
    "PlatformStats",
    "UserStats",
    "AnalyticsDataPoint",
    "TopQuery",
    "SpecialtyStats",
    "SystemHealth",
    # Storage
    "AdminStorage",
    "get_admin_storage",
    # Analytics
    "AnalyticsService",
    "get_analytics_service",
    # Service
    "AdminService",
    "AdminResult",
    "get_admin_service",
]
