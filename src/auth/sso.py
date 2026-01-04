"""
SSO (Single Sign-On) Providers

Supports:
- Google OAuth 2.0
- Microsoft Azure AD / Entra ID
- Apple Sign In (future)
"""

import json
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

# Try to import httpx for async HTTP
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False


@dataclass
class SSOUserInfo:
    """User info from SSO provider"""
    provider: str
    provider_id: str
    email: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False
    locale: Optional[str] = None
    hd: Optional[str] = None  # Hosted domain (Google Workspace)


class SSOProvider(ABC):
    """Base class for SSO providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get the authorization URL to redirect the user to."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Exchange authorization code for tokens."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Optional[SSOUserInfo]:
        """Get user info from the provider."""
        pass

    @staticmethod
    def generate_state() -> str:
        """Generate a random state for CSRF protection."""
        return secrets.token_urlsafe(32)


class GoogleSSO(SSOProvider):
    """Google OAuth 2.0 SSO provider."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def name(self) -> str:
        return "google"

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
        hd: Optional[str] = None,  # Restrict to domain
    ) -> str:
        """Get Google OAuth authorization URL."""
        if scopes is None:
            scopes = ["openid", "email", "profile"]

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }

        if hd:
            params["hd"] = hd

        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.TOKEN_URL,
                        data=data,
                        headers={"Accept": "application/json"},
                    )
                    if response.status_code == 200:
                        return response.json()
            else:
                # Sync fallback
                req = urllib.request.Request(
                    self.TOKEN_URL,
                    data=urlencode(data).encode(),
                    headers={"Accept": "application/json"},
                )
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read())
        except Exception as e:
            print(f"Google token exchange failed: {e}")
            return None

        return None

    async def get_user_info(self, access_token: str) -> Optional[SSOUserInfo]:
        """Get user info from Google."""
        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.USERINFO_URL,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return SSOUserInfo(
                            provider="google",
                            provider_id=data.get("sub", ""),
                            email=data.get("email", ""),
                            name=data.get("name", ""),
                            given_name=data.get("given_name"),
                            family_name=data.get("family_name"),
                            picture=data.get("picture"),
                            email_verified=data.get("email_verified", False),
                            locale=data.get("locale"),
                            hd=data.get("hd"),
                        )
            else:
                req = urllib.request.Request(
                    self.USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read())
                    return SSOUserInfo(
                        provider="google",
                        provider_id=data.get("sub", ""),
                        email=data.get("email", ""),
                        name=data.get("name", ""),
                        given_name=data.get("given_name"),
                        family_name=data.get("family_name"),
                        picture=data.get("picture"),
                        email_verified=data.get("email_verified", False),
                        locale=data.get("locale"),
                        hd=data.get("hd"),
                    )
        except Exception as e:
            print(f"Google user info failed: {e}")
            return None

        return None


class MicrosoftSSO(SSOProvider):
    """Microsoft Azure AD / Entra ID SSO provider."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str = "common",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

        self.auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"

    @property
    def name(self) -> str:
        return "microsoft"

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """Get Microsoft OAuth authorization URL."""
        if scopes is None:
            scopes = ["openid", "email", "profile", "User.Read"]

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "response_mode": "query",
        }

        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": "openid email profile User.Read",
        }

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.token_url,
                        data=data,
                        headers={"Accept": "application/json"},
                    )
                    if response.status_code == 200:
                        return response.json()
            else:
                req = urllib.request.Request(
                    self.token_url,
                    data=urlencode(data).encode(),
                    headers={"Accept": "application/json"},
                )
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read())
        except Exception as e:
            print(f"Microsoft token exchange failed: {e}")
            return None

        return None

    async def get_user_info(self, access_token: str) -> Optional[SSOUserInfo]:
        """Get user info from Microsoft Graph."""
        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.userinfo_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return SSOUserInfo(
                            provider="microsoft",
                            provider_id=data.get("id", ""),
                            email=data.get("mail") or data.get("userPrincipalName", ""),
                            name=data.get("displayName", ""),
                            given_name=data.get("givenName"),
                            family_name=data.get("surname"),
                            picture=None,  # Requires separate Graph API call
                            email_verified=True,  # Microsoft verifies emails
                        )
            else:
                req = urllib.request.Request(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read())
                    return SSOUserInfo(
                        provider="microsoft",
                        provider_id=data.get("id", ""),
                        email=data.get("mail") or data.get("userPrincipalName", ""),
                        name=data.get("displayName", ""),
                        given_name=data.get("givenName"),
                        family_name=data.get("surname"),
                        picture=None,
                        email_verified=True,
                    )
        except Exception as e:
            print(f"Microsoft user info failed: {e}")
            return None

        return None


class SSOManager:
    """
    Manages multiple SSO providers.
    """

    def __init__(self):
        self.providers: dict[str, SSOProvider] = {}
        self._states: dict[str, dict] = {}  # state -> {provider, redirect_uri, created_at}

    def register_provider(self, provider: SSOProvider) -> None:
        """Register an SSO provider."""
        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[SSOProvider]:
        """Get a provider by name."""
        return self.providers.get(name)

    def get_authorization_url(
        self,
        provider_name: str,
        redirect_uri: str,
        **kwargs,
    ) -> Optional[tuple[str, str]]:
        """
        Get authorization URL for a provider.

        Returns: (url, state) or None if provider not found
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None

        state = SSOProvider.generate_state()
        self._states[state] = {
            "provider": provider_name,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow(),
        }

        url = provider.get_authorization_url(redirect_uri, state, **kwargs)
        return url, state

    async def handle_callback(
        self,
        state: str,
        code: str,
    ) -> Optional[SSOUserInfo]:
        """
        Handle OAuth callback.

        Returns user info if successful.
        """
        state_data = self._states.pop(state, None)
        if not state_data:
            return None

        provider = self.get_provider(state_data["provider"])
        if not provider:
            return None

        tokens = await provider.exchange_code(code, state_data["redirect_uri"])
        if not tokens:
            return None

        access_token = tokens.get("access_token")
        if not access_token:
            return None

        return await provider.get_user_info(access_token)

    def cleanup_expired_states(self, max_age_seconds: int = 600) -> int:
        """Remove expired states. Returns count removed."""
        now = datetime.utcnow()
        expired = [
            state for state, data in self._states.items()
            if (now - data["created_at"]).total_seconds() > max_age_seconds
        ]
        for state in expired:
            del self._states[state]
        return len(expired)
