"""
Authentication Service

Central service for all authentication operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets

from .models import User, Session, UserRole, AuthProvider, TokenPair, Organization
from .password import hash_password, verify_password, validate_password_strength, generate_reset_token
from .jwt_handler import JWTHandler, get_jwt_handler
from .sso import SSOManager, SSOUserInfo, GoogleSSO, MicrosoftSSO
from .storage import AuthStorage, get_auth_storage


@dataclass
class AuthResult:
    """Result of authentication operation."""
    success: bool
    user: Optional[User] = None
    tokens: Optional[TokenPair] = None
    error: Optional[str] = None
    requires_mfa: bool = False
    mfa_token: Optional[str] = None


class AuthService:
    """
    Central authentication service.

    Handles:
    - Local authentication (email/password)
    - SSO authentication (Google, Microsoft)
    - Session management
    - Password reset
    - MFA (future)
    """

    def __init__(
        self,
        storage: Optional[AuthStorage] = None,
        jwt_handler: Optional[JWTHandler] = None,
    ):
        self.storage = storage or get_auth_storage()
        self.jwt = jwt_handler or get_jwt_handler()
        self.sso = SSOManager()

        # Configure SSO providers from environment
        self._setup_sso_providers()

    def _setup_sso_providers(self) -> None:
        """Set up SSO providers from environment variables."""
        import os

        # Google SSO
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        if google_client_id and google_client_secret:
            self.sso.register_provider(GoogleSSO(google_client_id, google_client_secret))

        # Microsoft SSO
        ms_client_id = os.environ.get("MICROSOFT_CLIENT_ID")
        ms_client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET")
        ms_tenant_id = os.environ.get("MICROSOFT_TENANT_ID", "common")
        if ms_client_id and ms_client_secret:
            self.sso.register_provider(MicrosoftSSO(ms_client_id, ms_client_secret, ms_tenant_id))

    # Registration
    def register(
        self,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.DOCTOR,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
        registration_number: Optional[str] = None,
    ) -> AuthResult:
        """
        Register a new user with email/password.
        """
        email = email.lower().strip()

        # Check if email exists
        existing = self.storage.get_user_by_email(email)
        if existing:
            return AuthResult(success=False, error="Email already registered")

        # Validate password
        is_valid, issues = validate_password_strength(password)
        if not is_valid:
            return AuthResult(success=False, error="; ".join(issues))

        # Create user
        user = User(
            email=email,
            name=name,
            role=role,
            provider=AuthProvider.LOCAL,
            specialty=specialty,
            institution=institution,
            registration_number=registration_number,
            password_hash=hash_password(password),
            email_verified=False,
        )

        self.storage.create_user(user)

        # TODO: Send verification email

        return AuthResult(success=True, user=user)

    # Login
    def login(
        self,
        email: str,
        password: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResult:
        """
        Authenticate with email/password.
        """
        email = email.lower().strip()

        user = self.storage.get_user_by_email(email)
        if not user:
            return AuthResult(success=False, error="Invalid email or password")

        if user.provider != AuthProvider.LOCAL:
            return AuthResult(
                success=False,
                error=f"Please sign in with {user.provider.value.title()}"
            )

        if not user.password_hash or not verify_password(password, user.password_hash):
            return AuthResult(success=False, error="Invalid email or password")

        if not user.is_active:
            return AuthResult(success=False, error="Account is disabled")

        # Check MFA
        if user.mfa_enabled:
            mfa_token = secrets.token_urlsafe(32)
            # TODO: Store MFA token for verification
            return AuthResult(
                success=True,
                user=user,
                requires_mfa=True,
                mfa_token=mfa_token,
            )

        # Create session and tokens
        tokens = self._create_session(user, device_info, ip_address, user_agent)

        # Update last login
        user.last_login = datetime.utcnow()
        self.storage.update_user(user)

        return AuthResult(success=True, user=user, tokens=tokens)

    # SSO
    def get_sso_url(
        self,
        provider: str,
        redirect_uri: str,
        **kwargs,
    ) -> Optional[Tuple[str, str]]:
        """
        Get SSO authorization URL.

        Returns (url, state) or None.
        """
        return self.sso.get_authorization_url(provider, redirect_uri, **kwargs)

    async def handle_sso_callback(
        self,
        state: str,
        code: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResult:
        """
        Handle SSO callback and create/login user.
        """
        user_info = await self.sso.handle_callback(state, code)
        if not user_info:
            return AuthResult(success=False, error="SSO authentication failed")

        # Check for existing user by provider ID
        user = self.storage.get_user_by_provider(user_info.provider, user_info.provider_id)

        if not user:
            # Check by email
            user = self.storage.get_user_by_email(user_info.email)
            if user:
                # Link account if local user exists
                if user.provider == AuthProvider.LOCAL:
                    user.provider = AuthProvider(user_info.provider)
                    user.provider_id = user_info.provider_id
                    user.email_verified = user_info.email_verified
                    if user_info.picture:
                        user.avatar_url = user_info.picture
                    self.storage.update_user(user)
                else:
                    return AuthResult(
                        success=False,
                        error=f"Email is linked to {user.provider.value.title()} account"
                    )
            else:
                # Create new user
                user = self._create_user_from_sso(user_info)
                self.storage.create_user(user)

        if not user.is_active:
            return AuthResult(success=False, error="Account is disabled")

        # Create session
        tokens = self._create_session(user, device_info, ip_address, user_agent)

        # Update last login
        user.last_login = datetime.utcnow()
        self.storage.update_user(user)

        return AuthResult(success=True, user=user, tokens=tokens)

    def _create_user_from_sso(self, info: SSOUserInfo) -> User:
        """Create a new user from SSO info."""
        # Determine role from domain (enterprise SSO)
        role = UserRole.DOCTOR
        org = None

        if info.hd:
            org = self.storage.get_organization_by_domain(info.hd)
            if org and org.allowed_roles:
                role = org.allowed_roles[0]

        return User(
            email=info.email.lower(),
            name=info.name,
            role=role,
            provider=AuthProvider(info.provider),
            provider_id=info.provider_id,
            avatar_url=info.picture,
            email_verified=info.email_verified,
            organization_id=org.id if org else None,
            license_tier=org.license_tier if org else "FREE",
        )

    # Token refresh
    def refresh_tokens(
        self,
        refresh_token: str,
    ) -> AuthResult:
        """
        Refresh access token using refresh token.
        """
        # Verify refresh token
        user_id = self.jwt.verify_refresh_token(refresh_token)
        if not user_id:
            return AuthResult(success=False, error="Invalid refresh token")

        # Get session
        session = self.storage.get_session_by_refresh_token(refresh_token)
        if not session or not session.is_valid():
            return AuthResult(success=False, error="Session expired or revoked")

        # Get user
        user = self.storage.get_user_by_id(user_id)
        if not user or not user.is_active:
            return AuthResult(success=False, error="User not found or disabled")

        # Create new tokens
        access_token, new_refresh_token, expires_in = self.jwt.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            name=user.name,
            org_id=user.organization_id,
        )

        # Update session
        session.access_token = access_token
        session.refresh_token = new_refresh_token
        session.last_activity = datetime.utcnow()

        # Revoke old session and create new one
        self.storage.revoke_session(session.id)
        new_session = Session(
            user_id=user.id,
            access_token=access_token,
            refresh_token=new_refresh_token,
            device_info=session.device_info,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            expires_at=session.expires_at,
        )
        self.storage.create_session(new_session)

        tokens = TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

        return AuthResult(success=True, user=user, tokens=tokens)

    # Logout
    def logout(self, refresh_token: str) -> bool:
        """
        Logout by revoking the session.
        """
        session = self.storage.get_session_by_refresh_token(refresh_token)
        if session:
            self.storage.revoke_session(session.id)
            return True
        return False

    def logout_all(self, user_id: str, except_current: Optional[str] = None) -> int:
        """
        Logout from all sessions.

        Returns number of sessions revoked.
        """
        return self.storage.revoke_user_sessions(user_id, except_current)

    # Password management
    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> AuthResult:
        """
        Change user's password.
        """
        user = self.storage.get_user_by_id(user_id)
        if not user:
            return AuthResult(success=False, error="User not found")

        if user.provider != AuthProvider.LOCAL:
            return AuthResult(success=False, error="Cannot change password for SSO account")

        if not user.password_hash or not verify_password(current_password, user.password_hash):
            return AuthResult(success=False, error="Current password is incorrect")

        # Validate new password
        is_valid, issues = validate_password_strength(new_password)
        if not is_valid:
            return AuthResult(success=False, error="; ".join(issues))

        # Update password
        user.password_hash = hash_password(new_password)
        self.storage.update_user(user)

        # Revoke all sessions
        self.storage.revoke_user_sessions(user_id)

        return AuthResult(success=True, user=user)

    def request_password_reset(self, email: str) -> Optional[str]:
        """
        Request a password reset.

        Returns the reset token (in production, send via email).
        """
        user = self.storage.get_user_by_email(email.lower())
        if not user or user.provider != AuthProvider.LOCAL:
            # Don't reveal if email exists
            return None

        token = generate_reset_token()
        expires = datetime.utcnow() + timedelta(hours=1)
        self.storage.create_password_reset(token, user.id, expires)

        # TODO: Send email with reset link
        return token

    def reset_password(self, token: str, new_password: str) -> AuthResult:
        """
        Reset password using reset token.
        """
        reset = self.storage.get_password_reset(token)
        if not reset:
            return AuthResult(success=False, error="Invalid or expired reset token")

        if datetime.fromisoformat(reset["expires_at"]) < datetime.utcnow():
            return AuthResult(success=False, error="Reset token has expired")

        user = self.storage.get_user_by_id(reset["user_id"])
        if not user:
            return AuthResult(success=False, error="User not found")

        # Validate new password
        is_valid, issues = validate_password_strength(new_password)
        if not is_valid:
            return AuthResult(success=False, error="; ".join(issues))

        # Update password
        user.password_hash = hash_password(new_password)
        self.storage.update_user(user)

        # Mark token as used
        self.storage.use_password_reset(token)

        # Revoke all sessions
        self.storage.revoke_user_sessions(user.id)

        return AuthResult(success=True, user=user)

    # User management
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.storage.get_user_by_id(user_id)

    def update_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        specialty: Optional[str] = None,
        institution: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> AuthResult:
        """Update user profile."""
        user = self.storage.get_user_by_id(user_id)
        if not user:
            return AuthResult(success=False, error="User not found")

        if name:
            user.name = name
        if specialty is not None:
            user.specialty = specialty
        if institution is not None:
            user.institution = institution
        if phone is not None:
            user.phone = phone

        self.storage.update_user(user)
        return AuthResult(success=True, user=user)

    def verify_email(self, user_id: str) -> bool:
        """Mark email as verified."""
        user = self.storage.get_user_by_id(user_id)
        if user:
            user.email_verified = True
            self.storage.update_user(user)
            return True
        return False

    # Session helpers
    def _create_session(
        self,
        user: User,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenPair:
        """Create a new session and return tokens."""
        access_token, refresh_token, expires_in = self.jwt.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            name=user.name,
            org_id=user.organization_id,
        )

        session = Session(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        self.storage.create_session(session)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify an access token and return the user.
        """
        payload = self.jwt.verify_access_token(token)
        if not payload:
            return None

        return self.storage.get_user_by_id(payload.sub)

    def get_active_sessions(self, user_id: str) -> list[dict]:
        """Get all active sessions for a user."""
        sessions = self.storage.get_user_sessions(user_id, active_only=True)
        return [
            {
                "id": s.id,
                "device_info": s.device_info,
                "ip_address": s.ip_address,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
            }
            for s in sessions
        ]


# Default instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the default auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
