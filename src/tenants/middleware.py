"""
Tenant Middleware

FastAPI middleware for extracting and setting tenant context
from JWT tokens and request headers.
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .isolation import set_tenant_context, clear_tenant_context
from .storage import get_tenant_storage
from ..auth.jwt_handler import get_jwt_handler


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from request and set it.

    Extracts tenant_id from:
    1. JWT token claims (tenant_id)
    2. X-Tenant-ID header (for multi-tenant users)
    3. User's default tenant (if user belongs to only one)

    Sets tenant context for the duration of the request.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and set tenant context."""
        try:
            # Extract tenant context
            tenant_id, user_id = await self._extract_tenant_context(request)

            if tenant_id and user_id:
                # Get member details
                storage = get_tenant_storage()
                member = storage.get_member_by_user(tenant_id, user_id)
                tenant = storage.get_tenant(tenant_id)

                # Set context for request
                set_tenant_context(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    member=member,
                    tenant=tenant,
                )

            # Process request
            response = await call_next(request)

            return response

        finally:
            # Always clear context after request
            clear_tenant_context()

    async def _extract_tenant_context(
        self,
        request: Request,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract tenant_id and user_id from request.

        Returns:
            (tenant_id, user_id) or (None, None)
        """
        # Get JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, None

        token = auth_header.replace("Bearer ", "")

        # Verify and decode token
        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_access_token(token)
        if not payload:
            return None, None

        user_id = payload.sub

        # 1. Check for tenant_id in JWT claims (added by updated JWT handler)
        tenant_id = payload.org_id

        # 2. Check for X-Tenant-ID header (for multi-tenant users)
        header_tenant_id = request.headers.get("X-Tenant-ID")
        if header_tenant_id:
            # Verify user has access to this tenant
            storage = get_tenant_storage()
            member = storage.get_member_by_user(header_tenant_id, user_id)
            if member:
                tenant_id = header_tenant_id

        # 3. If no tenant_id yet, try to get user's default tenant
        if not tenant_id:
            storage = get_tenant_storage()
            memberships = storage.get_user_memberships(user_id)
            if len(memberships) == 1:
                # User belongs to only one tenant
                tenant_id = memberships[0].tenant_id
            elif len(memberships) > 1:
                # User belongs to multiple tenants but didn't specify
                # Could return None and require X-Tenant-ID header
                # Or default to first membership
                tenant_id = memberships[0].tenant_id

        return tenant_id, user_id


def get_tenant_id_from_request(request: Request) -> Optional[str]:
    """
    Helper function to get tenant_id from request.

    Can be used as a FastAPI dependency.
    """
    # Check header first
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Check JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    jwt_handler = get_jwt_handler()
    payload = jwt_handler.verify_access_token(token)

    if payload:
        return payload.org_id

    return None


def require_tenant(request: Request) -> str:
    """
    FastAPI dependency that requires a tenant context.

    Raises HTTPException if no tenant context is available.

    Usage:
        @app.get("/api/something")
        async def endpoint(tenant_id: str = Depends(require_tenant)):
            # tenant_id is guaranteed to be set
            ...
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant ID required. Set X-Tenant-ID header or ensure JWT contains tenant context."
        )
    return tenant_id
