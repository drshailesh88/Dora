"""
Security middleware for Dora API.
Implements rate limiting, input validation, security headers, and audit logging.
"""

import time
import hashlib
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with per-user and per-IP limits."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self._request_counts: Dict[str, list] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()

        # Clean old entries
        self._request_counts[client_id] = [
            ts for ts in self._request_counts[client_id] if now - ts < 3600
        ]

        # Check limits
        recent_requests = self._request_counts[client_id]
        minute_count = sum(1 for ts in recent_requests if now - ts < 60)
        hour_count = len(recent_requests)

        # Burst check (last 1 second)
        burst_count = sum(1 for ts in recent_requests if now - ts < 1)

        if burst_count >= self.burst_limit:
            logger.warning(f"Burst limit exceeded for {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "detail": "Please slow down",
                    "retry_after": 1,
                },
                headers={"Retry-After": "1"},
            )

        if minute_count >= self.requests_per_minute:
            logger.warning(f"Minute rate limit exceeded for {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.requests_per_minute} requests per minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        if hour_count >= self.requests_per_hour:
            logger.warning(f"Hour rate limit exceeded for {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.requests_per_hour} requests per hour",
                    "retry_after": 3600,
                },
                headers={"Retry-After": "3600"},
            )

        # Record request
        self._request_counts[client_id].append(now)

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - minute_count - 1
        )
        response.headers["X-RateLimit-Reset"] = str(int(now) + 60)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from auth or IP."""
        # Try to get user ID from auth
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=()"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.docassist.in wss://api.docassist.in; "
            "frame-ancestors 'none';"
        )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data."""

    BLOCKED_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onclick=",
        "onload=",
        "eval(",
        "document.cookie",
        "window.location",
    ]

    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"error": "Request body too large"},
            )

        # Check for malicious patterns in query params
        for key, value in request.query_params.items():
            if self._contains_malicious_pattern(value):
                logger.warning(f"Blocked malicious input in query param: {key}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input detected"},
                )

        return await call_next(request)

    def _contains_malicious_pattern(self, value: str) -> bool:
        """Check if value contains XSS or injection patterns."""
        value_lower = value.lower()
        return any(pattern in value_lower for pattern in self.BLOCKED_PATTERNS)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all API requests for audit trail."""

    SENSITIVE_PATHS = ["/auth/login", "/auth/register", "/subscription/payment"]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        request_id = self._generate_request_id(request)

        # Add request ID to request state
        request.state.request_id = request_id

        # Log request
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
        }

        # Add user ID if authenticated
        if hasattr(request.state, "user") and request.state.user:
            log_data["user_id"] = request.state.user.id

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            log_data["status_code"] = response.status_code
            log_data["duration_ms"] = round(duration * 1000, 2)

            # Log level based on status
            if response.status_code >= 500:
                logger.error(f"API Request: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"API Request: {log_data}")
            else:
                logger.info(f"API Request: {log_data}")

            # Add request ID to response
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            log_data["error"] = str(e)
            log_data["status_code"] = 500
            logger.error(f"API Request Error: {log_data}")
            raise

    def _generate_request_id(self, request: Request) -> str:
        """Generate unique request ID."""
        data = f"{time.time()}{request.client.host if request.client else ''}{request.url.path}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from headers or connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS with origin validation."""

    ALLOWED_ORIGINS = [
        "https://dora.docassist.in",
        "https://app.docassist.in",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        origin = request.headers.get("origin")

        if request.method == "OPTIONS":
            response = Response()
            if origin in self.ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, X-Request-ID"
                )
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"
            return response

        response = await call_next(request)

        if origin in self.ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


def require_auth(func: Callable):
    """Decorator to require authentication."""

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.state, "user") or not request.state.user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return await func(request, *args, **kwargs)

    return wrapper


def require_role(roles: list):
    """Decorator to require specific roles."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "user") or not request.state.user:
                raise HTTPException(status_code=401, detail="Authentication required")

            user_role = getattr(request.state.user, "role", None)
            if user_role not in roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def setup_security_middleware(app):
    """Add all security middleware to FastAPI app."""
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(CORSSecurityMiddleware)
