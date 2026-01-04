"""
Migration: Add Tenant Support to Existing Database

This migration adds tenant_id columns to existing tables to support
multi-tenant data isolation.

IMPORTANT: Run this on existing databases to add tenant support.
New databases will have this schema from the start.
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str):
    """
    Add tenant support to existing database.

    Adds:
    - tenant_id column to user-scoped tables
    - Indexes for tenant-based queries
    - Default tenant for existing users
    """
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Add tenant_id to users table (if not exists)
        print("Adding tenant_id to users table...")
        cursor.execute("""
            SELECT COUNT(*) FROM pragma_table_info('users')
            WHERE name='tenant_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN tenant_id TEXT
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_tenant
                ON users(tenant_id)
            """)
            print("  ✓ Added tenant_id to users")
        else:
            print("  ℹ tenant_id already exists in users")

        # 2. Create default "individual" tenant for existing users
        print("Creating individual tenants for existing users...")
        cursor.execute("""
            SELECT id, email, name FROM users WHERE tenant_id IS NULL
        """)
        users_without_tenant = cursor.fetchall()

        for user_id, email, name in users_without_tenant:
            # Create individual tenant
            import uuid
            tenant_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO tenants (
                    id, name, display_name, tenant_type, email,
                    plan_id, status, owner_id, created_at, updated_at,
                    country
                )
                VALUES (?, ?, ?, 'individual', ?, 'free', 'active', ?,
                        datetime('now'), datetime('now'), 'India')
            """, (
                tenant_id,
                f"{name}'s Workspace",
                f"{name}'s Workspace",
                email,
                user_id,
            ))

            # Add user as owner member
            member_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO tenant_members (
                    id, tenant_id, user_id, role, is_active, joined_at
                )
                VALUES (?, ?, ?, 'owner', 1, datetime('now'))
            """, (member_id, tenant_id, user_id))

            # Update user's tenant_id
            cursor.execute("""
                UPDATE users SET tenant_id = ? WHERE id = ?
            """, (tenant_id, user_id))

            print(f"  ✓ Created tenant for user {email}")

        # 3. Add tenant_id to query_history table (if exists)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='query_history'
        """)
        if cursor.fetchone():
            print("Adding tenant_id to query_history...")
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('query_history')
                WHERE name='tenant_id'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE query_history ADD COLUMN tenant_id TEXT
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_history_tenant
                    ON query_history(tenant_id)
                """)

                # Set tenant_id for existing queries based on user
                cursor.execute("""
                    UPDATE query_history
                    SET tenant_id = (
                        SELECT tenant_id FROM users
                        WHERE users.id = query_history.user_id
                    )
                    WHERE tenant_id IS NULL
                """)
                print("  ✓ Added tenant_id to query_history")
            else:
                print("  ℹ tenant_id already exists in query_history")

        # 4. Add tenant_id to documents table (if exists)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='documents'
        """)
        if cursor.fetchone():
            print("Adding tenant_id to documents...")
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('documents')
                WHERE name='tenant_id'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE documents ADD COLUMN tenant_id TEXT
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_tenant
                    ON documents(tenant_id)
                """)
                print("  ✓ Added tenant_id to documents")
            else:
                print("  ℹ tenant_id already exists in documents")

        # 5. Add tenant_id to subscriptions table (if exists)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='subscriptions'
        """)
        if cursor.fetchone():
            print("Adding organization_id to subscriptions...")
            cursor.execute("""
                SELECT COUNT(*) FROM pragma_table_info('subscriptions')
                WHERE name='organization_id'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE subscriptions ADD COLUMN organization_id TEXT
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_subscriptions_org
                    ON subscriptions(organization_id)
                """)
                print("  ✓ Added organization_id to subscriptions")
            else:
                print("  ℹ organization_id already exists in subscriptions")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def verify_migration(db_path: str):
    """Verify that migration was successful."""
    print(f"\nVerifying migration for: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check tenants table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='tenants'
        """)
        if cursor.fetchone():
            print("  ✓ tenants table exists")
        else:
            print("  ❌ tenants table missing")

        # Check tenant_members table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='tenant_members'
        """)
        if cursor.fetchone():
            print("  ✓ tenant_members table exists")
        else:
            print("  ❌ tenant_members table missing")

        # Check users have tenant_id
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE tenant_id IS NULL
        """)
        null_tenant_count = cursor.fetchone()[0]
        if null_tenant_count == 0:
            print("  ✓ All users have tenant_id")
        else:
            print(f"  ⚠ {null_tenant_count} users without tenant_id")

        # Count tenants
        cursor.execute("SELECT COUNT(*) FROM tenants")
        tenant_count = cursor.fetchone()[0]
        print(f"  ℹ Total tenants: {tenant_count}")

        # Count members
        cursor.execute("SELECT COUNT(*) FROM tenant_members")
        member_count = cursor.fetchone()[0]
        print(f"  ℹ Total members: {member_count}")

        print("\n✅ Verification completed!")

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Default database path
    default_db = str(Path.home() / ".dora" / "dora.db")

    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db

    print("=" * 60)
    print("Dora Tenant Migration Tool")
    print("=" * 60)
    print()

    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("   The tenant tables will be created automatically on first use.")
        sys.exit(0)

    # Run migration
    migrate_database(db_path)

    # Verify
    verify_migration(db_path)

    print()
    print("=" * 60)
    print("Next steps:")
    print("1. Restart your Dora application")
    print("2. Existing users will have individual workspaces")
    print("3. Users can create/join organizations via the API")
    print("=" * 60)
