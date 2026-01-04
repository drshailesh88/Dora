"""
Tenant Storage Layer

Handles persistent storage for multi-tenant data using SQLite.
Supports tenant-scoped queries with data isolation.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

from .models import (
    Tenant, Team, TenantMember, TenantInvitation, TenantAuditLog,
    MemberRole, InvitationStatus, TenantStatus
)


class TenantStorage:
    """
    Storage backend for tenant data.

    Uses SQLite with separate tables for:
    - Tenants (organizations)
    - Teams (departments)
    - Members (user-tenant associations)
    - Invitations
    - Audit logs
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize tenant storage.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.dora/tenants.db
        """
        if db_path is None:
            db_path = str(Path.home() / ".dora" / "tenants.db")

        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    tenant_type TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    website TEXT,
                    address_line1 TEXT,
                    address_line2 TEXT,
                    city TEXT,
                    state TEXT,
                    postal_code TEXT,
                    country TEXT DEFAULT 'India',
                    registration_number TEXT,
                    tax_id TEXT,
                    plan_id TEXT NOT NULL DEFAULT 'clinic',
                    billing_email TEXT,
                    settings TEXT DEFAULT '{}',
                    logo_url TEXT,
                    primary_color TEXT,
                    secondary_color TEXT,
                    enabled_features TEXT DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'trial',
                    trial_ends_at TEXT,
                    owner_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    sso_enabled INTEGER DEFAULT 0,
                    sso_provider TEXT,
                    sso_domain TEXT,
                    sso_config TEXT DEFAULT '{}'
                )
            """)

            # Create index on owner_id for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenants_owner
                ON tenants(owner_id)
            """)

            # Teams table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    settings TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_teams_tenant
                ON teams(tenant_id)
            """)

            # Members table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_members (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    team_ids TEXT DEFAULT '[]',
                    custom_permissions TEXT DEFAULT '[]',
                    daily_query_limit INTEGER,
                    storage_quota_gb INTEGER,
                    is_active INTEGER DEFAULT 1,
                    joined_at TEXT NOT NULL,
                    invited_by TEXT,
                    last_activity TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    UNIQUE(tenant_id, user_id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_members_tenant
                ON tenant_members(tenant_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_members_user
                ON tenant_members(user_id)
            """)

            # Invitations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_invitations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    team_ids TEXT DEFAULT '[]',
                    token TEXT UNIQUE NOT NULL,
                    message TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    invited_by TEXT NOT NULL,
                    accepted_at TEXT,
                    declined_at TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_invitations_tenant
                ON tenant_invitations(tenant_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_invitations_email
                ON tenant_invitations(email)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_invitations_token
                ON tenant_invitations(token)
            """)

            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_audit_logs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    target_id TEXT,
                    details TEXT DEFAULT '{}',
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_tenant
                ON tenant_audit_logs(tenant_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_actor
                ON tenant_audit_logs(actor_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_created
                ON tenant_audit_logs(created_at)
            """)

    # Tenant CRUD operations

    def create_tenant(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tenants (
                    id, name, display_name, tenant_type, email, phone, website,
                    address_line1, address_line2, city, state, postal_code, country,
                    registration_number, tax_id, plan_id, billing_email, settings,
                    logo_url, primary_color, secondary_color, enabled_features,
                    status, trial_ends_at, owner_id, created_at, updated_at,
                    sso_enabled, sso_provider, sso_domain, sso_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant.id, tenant.name, tenant.display_name, tenant.tenant_type.value,
                tenant.email, tenant.phone, tenant.website,
                tenant.address_line1, tenant.address_line2, tenant.city,
                tenant.state, tenant.postal_code, tenant.country,
                tenant.registration_number, tenant.tax_id, tenant.plan_id,
                tenant.billing_email, json.dumps(tenant.settings),
                tenant.logo_url, tenant.primary_color, tenant.secondary_color,
                json.dumps(tenant.enabled_features), tenant.status.value,
                tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                tenant.owner_id, tenant.created_at.isoformat(), tenant.updated_at.isoformat(),
                1 if tenant.sso_enabled else 0, tenant.sso_provider,
                tenant.sso_domain, json.dumps(tenant.sso_config)
            ))
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
            row = cursor.fetchone()
            if row:
                return self._tenant_from_row(row)
        return None

    def get_tenant_by_owner(self, owner_id: str) -> Optional[Tenant]:
        """Get tenant by owner user ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants WHERE owner_id = ?", (owner_id,))
            row = cursor.fetchone()
            if row:
                return self._tenant_from_row(row)
        return None

    def update_tenant(self, tenant: Tenant) -> Tenant:
        """Update tenant."""
        tenant.updated_at = datetime.utcnow()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenants SET
                    name = ?, display_name = ?, tenant_type = ?, email = ?,
                    phone = ?, website = ?, address_line1 = ?, address_line2 = ?,
                    city = ?, state = ?, postal_code = ?, country = ?,
                    registration_number = ?, tax_id = ?, plan_id = ?,
                    billing_email = ?, settings = ?, logo_url = ?,
                    primary_color = ?, secondary_color = ?, enabled_features = ?,
                    status = ?, trial_ends_at = ?, updated_at = ?,
                    sso_enabled = ?, sso_provider = ?, sso_domain = ?, sso_config = ?
                WHERE id = ?
            """, (
                tenant.name, tenant.display_name, tenant.tenant_type.value, tenant.email,
                tenant.phone, tenant.website, tenant.address_line1, tenant.address_line2,
                tenant.city, tenant.state, tenant.postal_code, tenant.country,
                tenant.registration_number, tenant.tax_id, tenant.plan_id,
                tenant.billing_email, json.dumps(tenant.settings), tenant.logo_url,
                tenant.primary_color, tenant.secondary_color, json.dumps(tenant.enabled_features),
                tenant.status.value, tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                tenant.updated_at.isoformat(), 1 if tenant.sso_enabled else 0,
                tenant.sso_provider, tenant.sso_domain, json.dumps(tenant.sso_config),
                tenant.id
            ))
        return tenant

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant (cascade deletes members, teams, etc)."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
            return cursor.rowcount > 0

    # Member operations

    def add_member(self, member: TenantMember) -> TenantMember:
        """Add a member to tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tenant_members (
                    id, tenant_id, user_id, role, team_ids, custom_permissions,
                    daily_query_limit, storage_quota_gb, is_active, joined_at,
                    invited_by, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                member.id, member.tenant_id, member.user_id, member.role.value,
                json.dumps(member.team_ids), json.dumps(member.custom_permissions),
                member.daily_query_limit, member.storage_quota_gb,
                1 if member.is_active else 0, member.joined_at.isoformat(),
                member.invited_by, member.last_activity.isoformat() if member.last_activity else None
            ))
        return member

    def get_member(self, member_id: str) -> Optional[TenantMember]:
        """Get member by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenant_members WHERE id = ?", (member_id,))
            row = cursor.fetchone()
            if row:
                return self._member_from_row(row)
        return None

    def get_member_by_user(self, tenant_id: str, user_id: str) -> Optional[TenantMember]:
        """Get member by tenant and user ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tenant_members
                WHERE tenant_id = ? AND user_id = ?
            """, (tenant_id, user_id))
            row = cursor.fetchone()
            if row:
                return self._member_from_row(row)
        return None

    def get_tenant_members(self, tenant_id: str, active_only: bool = True) -> List[TenantMember]:
        """Get all members of a tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("""
                    SELECT * FROM tenant_members
                    WHERE tenant_id = ? AND is_active = 1
                    ORDER BY joined_at
                """, (tenant_id,))
            else:
                cursor.execute("""
                    SELECT * FROM tenant_members
                    WHERE tenant_id = ?
                    ORDER BY joined_at
                """, (tenant_id,))
            return [self._member_from_row(row) for row in cursor.fetchall()]

    def get_user_memberships(self, user_id: str) -> List[TenantMember]:
        """Get all tenant memberships for a user."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tenant_members
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            return [self._member_from_row(row) for row in cursor.fetchall()]

    def update_member(self, member: TenantMember) -> TenantMember:
        """Update member."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenant_members SET
                    role = ?, team_ids = ?, custom_permissions = ?,
                    daily_query_limit = ?, storage_quota_gb = ?,
                    is_active = ?, last_activity = ?
                WHERE id = ?
            """, (
                member.role.value, json.dumps(member.team_ids),
                json.dumps(member.custom_permissions), member.daily_query_limit,
                member.storage_quota_gb, 1 if member.is_active else 0,
                member.last_activity.isoformat() if member.last_activity else None,
                member.id
            ))
        return member

    def remove_member(self, member_id: str) -> bool:
        """Remove member from tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tenant_members WHERE id = ?", (member_id,))
            return cursor.rowcount > 0

    # Team operations

    def create_team(self, team: Team) -> Team:
        """Create a team."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO teams (
                    id, tenant_id, name, description, settings,
                    created_at, created_by, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team.id, team.tenant_id, team.name, team.description,
                json.dumps(team.settings), team.created_at.isoformat(),
                team.created_by, 1 if team.is_active else 0
            ))
        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
            row = cursor.fetchone()
            if row:
                return self._team_from_row(row)
        return None

    def get_tenant_teams(self, tenant_id: str) -> List[Team]:
        """Get all teams for a tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM teams
                WHERE tenant_id = ? AND is_active = 1
                ORDER BY name
            """, (tenant_id,))
            return [self._team_from_row(row) for row in cursor.fetchall()]

    def update_team(self, team: Team) -> Team:
        """Update team."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE teams SET
                    name = ?, description = ?, settings = ?, is_active = ?
                WHERE id = ?
            """, (
                team.name, team.description, json.dumps(team.settings),
                1 if team.is_active else 0, team.id
            ))
        return team

    def delete_team(self, team_id: str) -> bool:
        """Delete team."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
            return cursor.rowcount > 0

    # Invitation operations

    def create_invitation(self, invitation: TenantInvitation) -> TenantInvitation:
        """Create an invitation."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tenant_invitations (
                    id, tenant_id, email, role, team_ids, token, message,
                    status, created_at, expires_at, invited_by,
                    accepted_at, declined_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invitation.id, invitation.tenant_id, invitation.email,
                invitation.role.value, json.dumps(invitation.team_ids),
                invitation.token, invitation.message, invitation.status.value,
                invitation.created_at.isoformat(), invitation.expires_at.isoformat(),
                invitation.invited_by,
                invitation.accepted_at.isoformat() if invitation.accepted_at else None,
                invitation.declined_at.isoformat() if invitation.declined_at else None
            ))
        return invitation

    def get_invitation(self, invitation_id: str) -> Optional[TenantInvitation]:
        """Get invitation by ID."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenant_invitations WHERE id = ?", (invitation_id,))
            row = cursor.fetchone()
            if row:
                return self._invitation_from_row(row)
        return None

    def get_invitation_by_token(self, token: str) -> Optional[TenantInvitation]:
        """Get invitation by token."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenant_invitations WHERE token = ?", (token,))
            row = cursor.fetchone()
            if row:
                return self._invitation_from_row(row)
        return None

    def get_tenant_invitations(self, tenant_id: str, status: Optional[InvitationStatus] = None) -> List[TenantInvitation]:
        """Get invitations for a tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                    SELECT * FROM tenant_invitations
                    WHERE tenant_id = ? AND status = ?
                    ORDER BY created_at DESC
                """, (tenant_id, status.value))
            else:
                cursor.execute("""
                    SELECT * FROM tenant_invitations
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                """, (tenant_id,))
            return [self._invitation_from_row(row) for row in cursor.fetchall()]

    def update_invitation(self, invitation: TenantInvitation) -> TenantInvitation:
        """Update invitation."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenant_invitations SET
                    status = ?, accepted_at = ?, declined_at = ?
                WHERE id = ?
            """, (
                invitation.status.value,
                invitation.accepted_at.isoformat() if invitation.accepted_at else None,
                invitation.declined_at.isoformat() if invitation.declined_at else None,
                invitation.id
            ))
        return invitation

    # Audit log operations

    def add_audit_log(self, log: TenantAuditLog) -> TenantAuditLog:
        """Add audit log entry."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tenant_audit_logs (
                    id, tenant_id, action, actor_id, target_id,
                    details, ip_address, user_agent, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id, log.tenant_id, log.action, log.actor_id,
                log.target_id, json.dumps(log.details), log.ip_address,
                log.user_agent, log.created_at.isoformat()
            ))
        return log

    def get_audit_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None
    ) -> List[TenantAuditLog]:
        """Get audit logs for a tenant."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if action:
                cursor.execute("""
                    SELECT * FROM tenant_audit_logs
                    WHERE tenant_id = ? AND action = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (tenant_id, action, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM tenant_audit_logs
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (tenant_id, limit, offset))
            return [self._audit_log_from_row(row) for row in cursor.fetchall()]

    # Helper methods to convert rows to dataclasses

    def _tenant_from_row(self, row: sqlite3.Row) -> Tenant:
        """Convert database row to Tenant."""
        return Tenant.from_dict({
            "id": row["id"],
            "name": row["name"],
            "display_name": row["display_name"],
            "tenant_type": row["tenant_type"],
            "email": row["email"],
            "phone": row["phone"],
            "website": row["website"],
            "address": {
                "line1": row["address_line1"],
                "line2": row["address_line2"],
                "city": row["city"],
                "state": row["state"],
                "postal_code": row["postal_code"],
                "country": row["country"],
            },
            "registration_number": row["registration_number"],
            "tax_id": row["tax_id"],
            "plan_id": row["plan_id"],
            "billing_email": row["billing_email"],
            "settings": json.loads(row["settings"]),
            "logo_url": row["logo_url"],
            "primary_color": row["primary_color"],
            "secondary_color": row["secondary_color"],
            "enabled_features": json.loads(row["enabled_features"]),
            "status": row["status"],
            "trial_ends_at": row["trial_ends_at"],
            "owner_id": row["owner_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "sso_enabled": bool(row["sso_enabled"]),
            "sso_provider": row["sso_provider"],
            "sso_domain": row["sso_domain"],
            "sso_config": json.loads(row["sso_config"]),
        })

    def _member_from_row(self, row: sqlite3.Row) -> TenantMember:
        """Convert database row to TenantMember."""
        return TenantMember.from_dict({
            "id": row["id"],
            "tenant_id": row["tenant_id"],
            "user_id": row["user_id"],
            "role": row["role"],
            "team_ids": json.loads(row["team_ids"]),
            "custom_permissions": json.loads(row["custom_permissions"]),
            "daily_query_limit": row["daily_query_limit"],
            "storage_quota_gb": row["storage_quota_gb"],
            "is_active": bool(row["is_active"]),
            "joined_at": row["joined_at"],
            "invited_by": row["invited_by"],
            "last_activity": row["last_activity"],
        })

    def _team_from_row(self, row: sqlite3.Row) -> Team:
        """Convert database row to Team."""
        return Team(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            description=row["description"] or "",
            settings=json.loads(row["settings"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            created_by=row["created_by"],
            is_active=bool(row["is_active"]),
        )

    def _invitation_from_row(self, row: sqlite3.Row) -> TenantInvitation:
        """Convert database row to TenantInvitation."""
        return TenantInvitation(
            id=row["id"],
            tenant_id=row["tenant_id"],
            email=row["email"],
            role=MemberRole(row["role"]),
            team_ids=json.loads(row["team_ids"]),
            token=row["token"],
            message=row["message"],
            status=InvitationStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            invited_by=row["invited_by"],
            accepted_at=datetime.fromisoformat(row["accepted_at"]) if row["accepted_at"] else None,
            declined_at=datetime.fromisoformat(row["declined_at"]) if row["declined_at"] else None,
        )

    def _audit_log_from_row(self, row: sqlite3.Row) -> TenantAuditLog:
        """Convert database row to TenantAuditLog."""
        return TenantAuditLog(
            id=row["id"],
            tenant_id=row["tenant_id"],
            action=row["action"],
            actor_id=row["actor_id"],
            target_id=row["target_id"],
            details=json.loads(row["details"]),
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


# Default instance
_tenant_storage: Optional[TenantStorage] = None


def get_tenant_storage() -> TenantStorage:
    """Get the default tenant storage instance."""
    global _tenant_storage
    if _tenant_storage is None:
        _tenant_storage = TenantStorage()
    return _tenant_storage
