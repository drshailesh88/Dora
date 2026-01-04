"""
API Middleware Package.

Security, monitoring, and utility middleware for Dora API.
"""

from .security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    InputValidationMiddleware,
    AuditLogMiddleware,
    CORSSecurityMiddleware,
    setup_security_middleware,
)
from .error_monitoring import (
    ErrorSeverity,
    ErrorEvent,
    ErrorAggregator,
    AlertManager,
    ErrorMonitoringMiddleware,
    HealthCheckService,
    setup_error_monitoring,
    error_aggregator,
    alert_manager,
    health_service,
)

__all__ = [
    # Security
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "InputValidationMiddleware",
    "AuditLogMiddleware",
    "CORSSecurityMiddleware",
    "setup_security_middleware",
    # Error Monitoring
    "ErrorSeverity",
    "ErrorEvent",
    "ErrorAggregator",
    "AlertManager",
    "ErrorMonitoringMiddleware",
    "HealthCheckService",
    "setup_error_monitoring",
    "error_aggregator",
    "alert_manager",
    "health_service",
]
