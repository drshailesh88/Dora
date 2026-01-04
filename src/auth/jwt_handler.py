"""
JWT Token Handler

Handles JWT token creation, validation, and refresh.
"""

import json
import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

# Try to use PyJWT if available
try:
    import jwt
    USE_PYJWT = True
except ImportError:
    USE_PYJWT = False


@dataclass
class TokenPayload:
    """JWT token payload"""
    sub: str  # Subject (user ID)
    email: str
    role: str
    name: str
    iat: int  # Issued at
    exp: int  # Expiration
    jti: str  # JWT ID
    type: str  # "access" or "refresh"

    # Optional claims
    org_id: Optional[str] = None
    permissions: Optional[list[str]] = None


class JWTHandler:
    """
    JWT token handler with support for access and refresh tokens.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
        issuer: str = "dora-auth",
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
        self.issuer = issuer

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        name: str,
        org_id: Optional[str] = None,
        permissions: Optional[list[str]] = None,
    ) -> str:
        """Create an access token."""
        now = datetime.utcnow()
        expire = now + self.access_token_expire

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "name": name,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": secrets.token_hex(16),
            "type": "access",
            "iss": self.issuer,
        }

        if org_id:
            payload["org_id"] = org_id
        if permissions:
            payload["permissions"] = permissions

        return self._encode(payload)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire

        payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": secrets.token_hex(16),
            "type": "refresh",
            "iss": self.issuer,
        }

        return self._encode(payload)

    def create_token_pair(
        self,
        user_id: str,
        email: str,
        role: str,
        name: str,
        org_id: Optional[str] = None,
    ) -> tuple[str, str, int]:
        """
        Create both access and refresh tokens.

        Returns: (access_token, refresh_token, expires_in_seconds)
        """
        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            name=name,
            org_id=org_id,
        )
        refresh_token = self.create_refresh_token(user_id)

        return access_token, refresh_token, int(self.access_token_expire.total_seconds())

    def decode_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Decode and validate a token.

        Returns the payload if valid, None otherwise.
        """
        try:
            payload = self._decode(token)

            # Verify expiration
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                return None

            # Verify issuer
            if payload.get("iss") != self.issuer:
                return None

            return payload
        except Exception:
            return None

    def verify_access_token(self, token: str) -> Optional[TokenPayload]:
        """
        Verify an access token and return the payload.
        """
        payload = self.decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        return TokenPayload(
            sub=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("role", "doctor"),
            name=payload.get("name", ""),
            iat=payload["iat"],
            exp=payload["exp"],
            jti=payload["jti"],
            type="access",
            org_id=payload.get("org_id"),
            permissions=payload.get("permissions"),
        )

    def verify_refresh_token(self, token: str) -> Optional[str]:
        """
        Verify a refresh token and return the user ID.
        """
        payload = self.decode_token(token)
        if not payload or payload.get("type") != "refresh":
            return None

        return payload.get("sub")

    def _encode(self, payload: dict) -> str:
        """Encode a payload to JWT."""
        if USE_PYJWT:
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        else:
            return self._manual_encode(payload)

    def _decode(self, token: str) -> dict:
        """Decode a JWT token."""
        if USE_PYJWT:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # We verify manually
            )
        else:
            return self._manual_decode(token)

    def _manual_encode(self, payload: dict) -> str:
        """Manual JWT encoding without PyJWT."""
        header = {"alg": self.algorithm, "typ": "JWT"}

        # Base64url encode header and payload
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))

        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = self._base64url_encode_bytes(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _manual_decode(self, token: str) -> dict:
        """Manual JWT decoding without PyJWT."""
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        actual_sig = self._base64url_decode_bytes(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid signature")

        # Decode payload
        payload_json = self._base64url_decode(payload_b64)
        return json.loads(payload_json)

    @staticmethod
    def _base64url_encode(data: str) -> str:
        """Base64url encode a string."""
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    @staticmethod
    def _base64url_encode_bytes(data: bytes) -> str:
        """Base64url encode bytes."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    @staticmethod
    def _base64url_decode(data: str) -> str:
        """Base64url decode to string."""
        # Add padding
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()

    @staticmethod
    def _base64url_decode_bytes(data: str) -> bytes:
        """Base64url decode to bytes."""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)


# Default instance
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get the default JWT handler instance."""
    global _jwt_handler
    if _jwt_handler is None:
        import os
        secret = os.environ.get("DORA_JWT_SECRET", secrets.token_hex(32))
        _jwt_handler = JWTHandler(secret_key=secret)
    return _jwt_handler


def set_jwt_handler(handler: JWTHandler) -> None:
    """Set the default JWT handler instance."""
    global _jwt_handler
    _jwt_handler = handler
