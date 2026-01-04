"""
Dora Authentication Module

Provides secure authentication with:
- JWT token-based auth
- SSO (Google, Microsoft)
- Role-based access control
- Session management
"""

from .models import User, UserRole, Session, TokenPair
from .service import AuthService
from .jwt_handler import JWTHandler
from .sso import SSOProvider, GoogleSSO, MicrosoftSSO
from .middleware import AuthMiddleware, require_auth, require_role

__all__ = [
    "User",
    "UserRole",
    "Session",
    "TokenPair",
    "AuthService",
    "JWTHandler",
    "SSOProvider",
    "GoogleSSO",
    "MicrosoftSSO",
    "AuthMiddleware",
    "require_auth",
    "require_role",
]
