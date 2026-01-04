"""
Authentication Middleware

FastAPI middleware and decorators for authentication.
"""

from functools import wraps
from typing import Optional, Callable, Any

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserRole
from .jwt_handler import get_jwt_handler, TokenPayload
from .service import get_auth_service


# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """
    FastAPI middleware for authentication.

    Extracts and validates JWT tokens from Authorization header.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract token from headers
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()

            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                jwt_handler = get_jwt_handler()
                payload = jwt_handler.verify_access_token(token)

                if payload:
                    # Add user info to scope
                    scope["user"] = {
                        "id": payload.sub,
                        "email": payload.email,
                        "role": payload.role,
                        "name": payload.name,
                        "org_id": payload.org_id,
                    }

        await self.app(scope, receive, send)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """
    Dependency to get current user from JWT token.

    Returns None if no valid token provided (for optional auth).
    """
    if not credentials:
        return None

    jwt_handler = get_jwt_handler()
    payload = jwt_handler.verify_access_token(credentials.credentials)

    if not payload:
        return None

    auth_service = get_auth_service()
    return auth_service.get_user(payload.sub)


async def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """
    Dependency to get current user (required).

    Raises 401 if not authenticated.
    """
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[TokenPayload]:
    """
    Dependency to get token payload without database lookup.

    Faster than get_current_user when you only need claims.
    """
    if not credentials:
        return None

    jwt_handler = get_jwt_handler()
    return jwt_handler.verify_access_token(credentials.credentials)


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication.

    Use for route functions where you need the user object.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request") or args[0] if args else None

        if request:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                jwt_handler = get_jwt_handler()
                payload = jwt_handler.verify_access_token(token)

                if payload:
                    auth_service = get_auth_service()
                    user = auth_service.get_user(payload.sub)
                    if user:
                        kwargs["current_user"] = user
                        return await func(*args, **kwargs)

        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return wrapper


def require_role(*roles: UserRole) -> Callable:
    """
    Decorator factory to require specific roles.

    Usage:
        @require_role(UserRole.ADMIN, UserRole.DOCTOR)
        async def my_route(request, current_user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or args[0] if args else None

            if request:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    jwt_handler = get_jwt_handler()
                    payload = jwt_handler.verify_access_token(token)

                    if payload:
                        user_role = UserRole(payload.role)
                        if user_role in roles:
                            auth_service = get_auth_service()
                            user = auth_service.get_user(payload.sub)
                            if user:
                                kwargs["current_user"] = user
                                return await func(*args, **kwargs)

                        raise HTTPException(
                            status_code=403,
                            detail=f"Role {payload.role} not authorized for this action",
                        )

            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return wrapper
    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator factory to require specific permission.

    Usage:
        @require_permission("admin.users")
        async def my_route(request, current_user):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or args[0] if args else None

            if request:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    jwt_handler = get_jwt_handler()
                    payload = jwt_handler.verify_access_token(token)

                    if payload:
                        user_role = UserRole(payload.role)
                        if permission in user_role.permissions:
                            auth_service = get_auth_service()
                            user = auth_service.get_user(payload.sub)
                            if user:
                                kwargs["current_user"] = user
                                return await func(*args, **kwargs)

                        raise HTTPException(
                            status_code=403,
                            detail=f"Permission '{permission}' required",
                        )

            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return wrapper
    return decorator


class RoleChecker:
    """
    Dependency for role-based access control.

    Usage:
        @app.get("/admin")
        async def admin_route(user: User = Depends(RoleChecker(UserRole.ADMIN))):
            ...
    """

    def __init__(self, *allowed_roles: UserRole):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    ) -> User:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_access_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_role = UserRole(payload.role)
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {payload.role} not authorized",
            )

        auth_service = get_auth_service()
        user = auth_service.get_user(payload.sub)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Account is disabled",
            )

        return user


class PermissionChecker:
    """
    Dependency for permission-based access control.

    Usage:
        @app.get("/manage-users")
        async def route(user: User = Depends(PermissionChecker("admin.users"))):
            ...
    """

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    ) -> User:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_access_token(credentials.credentials)

        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_role = UserRole(payload.role)
        if self.permission not in user_role.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{self.permission}' required",
            )

        auth_service = get_auth_service()
        user = auth_service.get_user(payload.sub)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return user
