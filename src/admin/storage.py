"""
Admin Storage Layer

Persistent storage for audit logs and admin data.
"""

import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from .models import AuditLog, AuditAction


class AdminStorage:
    """
    Storage for admin operations.

    Uses JSON files for simplicity. In production, use PostgreSQL.
    """

    def __init__(self, data_dir: str = "data/admin"):
        """Initialize storage"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.audit_log_file = self.data_dir / "audit_logs.jsonl"
        self.stats_cache_file = self.data_dir / "stats_cache.json"

        # Ensure files exist
        self.audit_log_file.touch(exist_ok=True)

    def log_audit(self, log: AuditLog) -> bool:
        """
        Save audit log entry.

        Args:
            log: Audit log entry

        Returns:
            True if successful
        """
        try:
            with open(self.audit_log_file, "a") as f:
                f.write(json.dumps(log.to_dict()) + "\n")
            return True
        except Exception as e:
            print(f"Error saving audit log: {e}")
            return False

    def get_audit_logs(
        self,
        offset: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """
        Get audit logs with filtering.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of audit logs
        """
        logs = []

        try:
            with open(self.audit_log_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        log = AuditLog.from_dict(data)

                        # Apply filters
                        if user_id and log.user_id != user_id:
                            continue
                        if action and log.action != action:
                            continue
                        if resource_type and log.resource_type != resource_type:
                            continue
                        if start_date and log.timestamp < start_date:
                            continue
                        if end_date and log.timestamp > end_date:
                            continue

                        logs.append(log)
                    except Exception as e:
                        print(f"Error parsing audit log: {e}")
                        continue

            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x.timestamp, reverse=True)

            # Apply pagination
            return logs[offset : offset + limit]

        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading audit logs: {e}")
            return []

    def count_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count audit logs matching filters.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Count of matching logs
        """
        count = 0

        try:
            with open(self.audit_log_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        log = AuditLog.from_dict(data)

                        # Apply filters
                        if user_id and log.user_id != user_id:
                            continue
                        if action and log.action != action:
                            continue
                        if resource_type and log.resource_type != resource_type:
                            continue
                        if start_date and log.timestamp < start_date:
                            continue
                        if end_date and log.timestamp > end_date:
                            continue

                        count += 1
                    except:
                        continue

            return count

        except FileNotFoundError:
            return 0
        except Exception as e:
            print(f"Error counting audit logs: {e}")
            return 0

    def cache_stats(self, stats: dict) -> bool:
        """
        Cache platform statistics.

        Args:
            stats: Statistics dictionary

        Returns:
            True if successful
        """
        try:
            with open(self.stats_cache_file, "w") as f:
                json.dump(
                    {
                        "stats": stats,
                        "cached_at": datetime.utcnow().isoformat(),
                    },
                    f,
                    indent=2,
                )
            return True
        except Exception as e:
            print(f"Error caching stats: {e}")
            return False

    def get_cached_stats(
        self, max_age_minutes: int = 5
    ) -> Optional[dict]:
        """
        Get cached statistics if fresh.

        Args:
            max_age_minutes: Maximum age of cache in minutes

        Returns:
            Cached stats or None if stale/missing
        """
        try:
            if not self.stats_cache_file.exists():
                return None

            with open(self.stats_cache_file, "r") as f:
                data = json.load(f)

            cached_at = datetime.fromisoformat(data["cached_at"])
            age = datetime.utcnow() - cached_at

            if age.total_seconds() / 60 > max_age_minutes:
                return None

            return data["stats"]

        except Exception as e:
            print(f"Error reading cached stats: {e}")
            return None


# Global instance
_storage: Optional[AdminStorage] = None


def get_admin_storage() -> AdminStorage:
    """Get admin storage instance"""
    global _storage
    if _storage is None:
        _storage = AdminStorage()
    return _storage
