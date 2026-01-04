"""
Password Hashing Utilities

Uses bcrypt for secure password hashing.
"""

import hashlib
import secrets
import string
from typing import Tuple


# Use passlib with bcrypt if available, fallback to hashlib
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_BCRYPT = True
except ImportError:
    USE_BCRYPT = False


def hash_password(password: str) -> str:
    """
    Hash a password securely.

    Uses bcrypt if available, otherwise PBKDF2-SHA256.
    """
    if USE_BCRYPT:
        return pwd_context.hash(password)
    else:
        # Fallback to PBKDF2
        salt = secrets.token_hex(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"pbkdf2:sha256:100000${salt}${hash_bytes.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    """
    if USE_BCRYPT and not password_hash.startswith("pbkdf2:"):
        return pwd_context.verify(password, password_hash)
    else:
        # PBKDF2 verification
        try:
            parts = password_hash.split("$")
            if len(parts) != 3:
                return False

            _, salt, stored_hash = parts
            hash_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return secrets.compare_digest(hash_bytes.hex(), stored_hash)
        except Exception:
            return False


def generate_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(password: str) -> Tuple[bool, list[str]]:
    """
    Validate password strength.

    Returns (is_valid, list of issues)
    """
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters")

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")

    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        issues.append("Password must contain at least one special character")

    return len(issues) == 0, issues


def generate_verification_code(length: int = 6) -> str:
    """Generate a numeric verification code."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_reset_token() -> str:
    """Generate a password reset token."""
    return secrets.token_urlsafe(32)
