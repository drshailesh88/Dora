"""
Authentication Storage

SQLite-based storage for users and sessions.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator

from .models import User, Session, UserRole, AuthProvider, Organization


class AuthStorage:
    """SQLite storage for authentication data."""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'doctor',
                    provider TEXT NOT NULL DEFAULT 'local',
                    provider_id TEXT,

                    specialty TEXT,
                    institution TEXT,
                    registration_number TEXT,
                    phone TEXT,
                    avatar_url TEXT,

                    is_active INTEGER DEFAULT 1,
                    is_verified INTEGER DEFAULT 0,
                    email_verified INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login TEXT,

                    password_hash TEXT,
                    mfa_enabled INTEGER DEFAULT 0,
                    mfa_secret TEXT,

                    license_tier TEXT DEFAULT 'FREE',
                    organization_id TEXT,

                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,

                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,

                    device_info TEXT,
                    ip_address TEXT,
                    user_agent TEXT,

                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_activity TEXT NOT NULL,

                    is_active INTEGER DEFAULT 1,
                    revoked INTEGER DEFAULT 0,
                    revoked_at TEXT,

                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Organizations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT UNIQUE,

                    sso_provider TEXT,
                    sso_client_id TEXT,
                    sso_tenant_id TEXT,

                    max_users INTEGER DEFAULT 100,
                    allowed_roles TEXT,
                    require_mfa INTEGER DEFAULT 0,

                    license_tier TEXT DEFAULT 'CLINIC',
                    license_key TEXT,

                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Password reset tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,

                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Email verification tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_verifications (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,

                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(refresh_token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orgs_domain ON organizations(domain)")

            conn.commit()

    # User operations
    def create_user(self, user: User) -> User:
        """Create a new user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (
                    id, email, name, role, provider, provider_id,
                    specialty, institution, registration_number, phone, avatar_url,
                    is_active, is_verified, email_verified,
                    created_at, updated_at, last_login,
                    password_hash, mfa_enabled, mfa_secret,
                    license_tier, organization_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id, user.email, user.name, user.role.value, user.provider.value,
                user.provider_id, user.specialty, user.institution, user.registration_number,
                user.phone, user.avatar_url, user.is_active, user.is_verified,
                user.email_verified, user.created_at.isoformat(), user.updated_at.isoformat(),
                user.last_login.isoformat() if user.last_login else None,
                user.password_hash, user.mfa_enabled, user.mfa_secret,
                user.license_tier, user.organization_id,
            ))
            conn.commit()
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
        return None

    def get_user_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by SSO provider and ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE provider = ? AND provider_id = ?",
                (provider, provider_id)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
        return None

    def update_user(self, user: User) -> User:
        """Update a user."""
        user.updated_at = datetime.utcnow()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET
                    email = ?, name = ?, role = ?, provider = ?, provider_id = ?,
                    specialty = ?, institution = ?, registration_number = ?, phone = ?, avatar_url = ?,
                    is_active = ?, is_verified = ?, email_verified = ?,
                    updated_at = ?, last_login = ?,
                    password_hash = ?, mfa_enabled = ?, mfa_secret = ?,
                    license_tier = ?, organization_id = ?
                WHERE id = ?
            """, (
                user.email, user.name, user.role.value, user.provider.value, user.provider_id,
                user.specialty, user.institution, user.registration_number, user.phone, user.avatar_url,
                user.is_active, user.is_verified, user.email_verified,
                user.updated_at.isoformat(), user.last_login.isoformat() if user.last_login else None,
                user.password_hash, user.mfa_enabled, user.mfa_secret,
                user.license_tier, user.organization_id,
                user.id,
            ))
            conn.commit()
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_users(
        self,
        offset: int = 0,
        limit: int = 50,
        role: Optional[UserRole] = None,
        organization_id: Optional[str] = None,
    ) -> list[User]:
        """List users with optional filtering."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM users WHERE 1=1"
            params = []

            if role:
                query += " AND role = ?"
                params.append(role.value)
            if organization_id:
                query += " AND organization_id = ?"
                params.append(organization_id)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [self._row_to_user(row) for row in cursor.fetchall()]

    # Session operations
    def create_session(self, session: Session) -> Session:
        """Create a new session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    id, user_id, access_token, refresh_token,
                    device_info, ip_address, user_agent,
                    created_at, expires_at, last_activity,
                    is_active, revoked, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id, session.user_id, session.access_token, session.refresh_token,
                session.device_info, session.ip_address, session.user_agent,
                session.created_at.isoformat(),
                session.expires_at.isoformat() if session.expires_at else None,
                session.last_activity.isoformat(),
                session.is_active, session.revoked,
                session.revoked_at.isoformat() if session.revoked_at else None,
            ))
            conn.commit()
        return session

    def get_session_by_refresh_token(self, refresh_token: str) -> Optional[Session]:
        """Get session by refresh token."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE refresh_token = ? AND revoked = 0",
                (refresh_token,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)
        return None

    def get_user_sessions(self, user_id: str, active_only: bool = True) -> list[Session]:
        """Get all sessions for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM sessions WHERE user_id = ?"
            if active_only:
                query += " AND is_active = 1 AND revoked = 0"
            cursor.execute(query, (user_id,))
            return [self._row_to_session(row) for row in cursor.fetchall()]

    def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET last_activity = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), session_id)
            )
            conn.commit()

    def revoke_session(self, session_id: str) -> None:
        """Revoke a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET revoked = 1, revoked_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), session_id)
            )
            conn.commit()

    def revoke_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user, optionally except one."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()

            if except_session_id:
                cursor.execute(
                    "UPDATE sessions SET revoked = 1, revoked_at = ? WHERE user_id = ? AND id != ?",
                    (now, user_id, except_session_id)
                )
            else:
                cursor.execute(
                    "UPDATE sessions SET revoked = 1, revoked_at = ? WHERE user_id = ?",
                    (now, user_id)
                )
            conn.commit()
            return cursor.rowcount

    # Password reset operations
    def create_password_reset(self, token: str, user_id: str, expires_at: datetime) -> None:
        """Create a password reset token."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO password_resets (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (token, user_id, datetime.utcnow().isoformat(), expires_at.isoformat()))
            conn.commit()

    def get_password_reset(self, token: str) -> Optional[dict]:
        """Get password reset by token."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM password_resets WHERE token = ? AND used = 0",
                (token,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def use_password_reset(self, token: str) -> None:
        """Mark password reset as used."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token,))
            conn.commit()

    # Organization operations
    def create_organization(self, org: Organization) -> Organization:
        """Create an organization."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO organizations (
                    id, name, domain, sso_provider, sso_client_id, sso_tenant_id,
                    max_users, allowed_roles, require_mfa, license_tier, license_key,
                    created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                org.id, org.name, org.domain, org.sso_provider.value if org.sso_provider else None,
                org.sso_client_id, org.sso_tenant_id, org.max_users,
                json.dumps([r.value for r in org.allowed_roles]), org.require_mfa,
                org.license_tier, org.license_key, org.created_at.isoformat(), org.is_active,
            ))
            conn.commit()
        return org

    def get_organization_by_domain(self, domain: str) -> Optional[Organization]:
        """Get organization by domain."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE domain = ?", (domain,))
            row = cursor.fetchone()
            if row:
                return self._row_to_organization(row)
        return None

    # Helper methods
    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User."""
        return User(
            id=row["id"],
            email=row["email"],
            name=row["name"],
            role=UserRole(row["role"]),
            provider=AuthProvider(row["provider"]),
            provider_id=row["provider_id"],
            specialty=row["specialty"],
            institution=row["institution"],
            registration_number=row["registration_number"],
            phone=row["phone"],
            avatar_url=row["avatar_url"],
            is_active=bool(row["is_active"]),
            is_verified=bool(row["is_verified"]),
            email_verified=bool(row["email_verified"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
            password_hash=row["password_hash"],
            mfa_enabled=bool(row["mfa_enabled"]),
            mfa_secret=row["mfa_secret"],
            license_tier=row["license_tier"],
            organization_id=row["organization_id"],
        )

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert database row to Session."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            device_info=row["device_info"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            last_activity=datetime.fromisoformat(row["last_activity"]),
            is_active=bool(row["is_active"]),
            revoked=bool(row["revoked"]),
            revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
        )

    def _row_to_organization(self, row: sqlite3.Row) -> Organization:
        """Convert database row to Organization."""
        return Organization(
            id=row["id"],
            name=row["name"],
            domain=row["domain"],
            sso_provider=AuthProvider(row["sso_provider"]) if row["sso_provider"] else None,
            sso_client_id=row["sso_client_id"],
            sso_tenant_id=row["sso_tenant_id"],
            max_users=row["max_users"],
            allowed_roles=[UserRole(r) for r in json.loads(row["allowed_roles"] or "[]")],
            require_mfa=bool(row["require_mfa"]),
            license_tier=row["license_tier"],
            license_key=row["license_key"],
            created_at=datetime.fromisoformat(row["created_at"]),
            is_active=bool(row["is_active"]),
        )


# Default instance
_storage: Optional[AuthStorage] = None


def get_auth_storage() -> AuthStorage:
    """Get the default storage instance."""
    global _storage
    if _storage is None:
        _storage = AuthStorage()
    return _storage
