"""License management for offline-capable subscriptions."""

import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .crypto import LicenseValidator


class LicenseTier(str, Enum):
    """License subscription tiers."""

    FREE = "free"
    ESSENTIAL = "essential"
    PROFESSIONAL = "professional"
    CLINIC = "clinic"
    ENTERPRISE = "enterprise"


class LicenseStatus(str, Enum):
    """Current license status."""

    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class LicenseInfo(BaseModel):
    """License information."""

    license_id: str
    user_id: str
    user_email: str
    tier: LicenseTier
    issued_at: datetime
    expires_at: datetime
    grace_period_days: int = 30
    features: list[str] = []
    max_queries_per_day: int = 100
    offline_allowed: bool = True
    machine_id: str | None = None


class LicenseManager:
    """
    Manage offline-capable license validation.

    Features:
    - Local license caching for offline use
    - 30-day grace period for network issues
    - Machine binding for piracy prevention
    - Periodic online verification
    """

    GRACE_PERIOD_DAYS = 30
    VERIFICATION_INTERVAL_DAYS = 7

    def __init__(
        self,
        license_dir: Path | None = None,
        api_url: str | None = None,
    ):
        """
        Initialize license manager.

        Args:
            license_dir: Directory to store license files.
            api_url: License server URL.
        """
        self.license_dir = license_dir or Path.home() / ".dora" / "license"
        self.license_dir.mkdir(parents=True, exist_ok=True)

        self.api_url = api_url or "https://api.docassist.in/v1/license"
        self.validator = LicenseValidator()

        self._cached_license: LicenseInfo | None = None
        self._cached_status: LicenseStatus | None = None

    @property
    def license_file(self) -> Path:
        """Path to license file."""
        return self.license_dir / "license.json"

    @property
    def verification_file(self) -> Path:
        """Path to last verification timestamp."""
        return self.license_dir / "last_verified.txt"

    def activate_license(self, license_key: str) -> tuple[bool, str]:
        """
        Activate a license key.

        Args:
            license_key: License key from purchase.

        Returns:
            Tuple of (success, message).
        """
        # Validate the license signature
        is_valid, license_data = self.validator.validate_license(license_key)

        if not is_valid:
            return False, "Invalid license key"

        # Check machine binding
        if license_data.get("machine_id"):
            current_machine = self.validator.get_machine_id()
            if license_data["machine_id"] != current_machine:
                return False, "License is bound to a different machine"

        # Check expiry
        if self.validator.is_license_expired(license_data):
            return False, "License has expired"

        # Save license locally
        try:
            with open(self.license_file, "w") as f:
                json.dump(
                    {
                        "key": license_key,
                        "data": license_data,
                        "activated_at": datetime.now(timezone.utc).isoformat(),
                        "machine_id": self.validator.get_machine_id(),
                    },
                    f,
                    indent=2,
                )

            # Update verification timestamp
            self._update_verification_time()

            # Clear cache
            self._cached_license = None
            self._cached_status = None

            return True, f"License activated successfully. Tier: {license_data.get('tier', 'unknown')}"

        except Exception as e:
            return False, f"Failed to save license: {e}"

    def get_license(self) -> LicenseInfo | None:
        """
        Get current license info.

        Returns:
            LicenseInfo if valid license exists.
        """
        if self._cached_license:
            return self._cached_license

        if not self.license_file.exists():
            return None

        try:
            with open(self.license_file) as f:
                stored = json.load(f)

            license_data = stored.get("data", {})

            self._cached_license = LicenseInfo(
                license_id=license_data.get("license_id", ""),
                user_id=license_data.get("user_id", ""),
                user_email=license_data.get("user_email", ""),
                tier=LicenseTier(license_data.get("tier", "free")),
                issued_at=datetime.fromisoformat(
                    license_data.get("issued_at", datetime.now(timezone.utc).isoformat())
                ),
                expires_at=datetime.fromisoformat(
                    license_data.get("expires_at", datetime.now(timezone.utc).isoformat())
                ),
                grace_period_days=license_data.get(
                    "grace_period_days", self.GRACE_PERIOD_DAYS
                ),
                features=license_data.get("features", []),
                max_queries_per_day=license_data.get("max_queries_per_day", 100),
                offline_allowed=license_data.get("offline_allowed", True),
                machine_id=stored.get("machine_id"),
            )

            return self._cached_license

        except Exception:
            return None

    def get_status(self) -> LicenseStatus:
        """
        Get current license status.

        Returns:
            Current license status.
        """
        if self._cached_status:
            return self._cached_status

        license_info = self.get_license()

        if not license_info:
            self._cached_status = LicenseStatus.NOT_FOUND
            return self._cached_status

        now = datetime.now(timezone.utc)

        # Check if license is within validity period
        if now <= license_info.expires_at:
            self._cached_status = LicenseStatus.ACTIVE
            return self._cached_status

        # Check grace period
        grace_end = license_info.expires_at + timedelta(
            days=license_info.grace_period_days
        )
        if now <= grace_end:
            self._cached_status = LicenseStatus.GRACE_PERIOD
            return self._cached_status

        self._cached_status = LicenseStatus.EXPIRED
        return self._cached_status

    def check_feature_access(self, feature: str) -> bool:
        """
        Check if a feature is accessible.

        Args:
            feature: Feature name.

        Returns:
            True if feature is accessible.
        """
        status = self.get_status()

        if status == LicenseStatus.INVALID or status == LicenseStatus.NOT_FOUND:
            return False

        if status == LicenseStatus.EXPIRED:
            return False

        license_info = self.get_license()
        if not license_info:
            return False

        # Define tier features
        tier_features = {
            LicenseTier.FREE: [
                "basic_query",
                "limited_citations",
            ],
            LicenseTier.ESSENTIAL: [
                "basic_query",
                "full_citations",
                "offline_mode",
                "query_history",
            ],
            LicenseTier.PROFESSIONAL: [
                "basic_query",
                "full_citations",
                "offline_mode",
                "query_history",
                "voice_interface",
                "drug_interactions",
                "emr_integration",
            ],
            LicenseTier.CLINIC: [
                "basic_query",
                "full_citations",
                "offline_mode",
                "query_history",
                "voice_interface",
                "drug_interactions",
                "emr_integration",
                "multi_user",
                "custom_content",
                "api_access",
            ],
            LicenseTier.ENTERPRISE: [
                "all",
            ],
        }

        allowed = tier_features.get(license_info.tier, [])

        if "all" in allowed:
            return True

        return feature in allowed or feature in license_info.features

    def get_daily_query_limit(self) -> int:
        """
        Get remaining daily query limit.

        Returns:
            Number of queries allowed today.
        """
        status = self.get_status()
        license_info = self.get_license()

        if status == LicenseStatus.EXPIRED or status == LicenseStatus.INVALID:
            return 0

        if status == LicenseStatus.NOT_FOUND:
            return 5  # Free tier limit

        if not license_info:
            return 5

        # Tier limits
        tier_limits = {
            LicenseTier.FREE: 10,
            LicenseTier.ESSENTIAL: 100,
            LicenseTier.PROFESSIONAL: 500,
            LicenseTier.CLINIC: 2000,
            LicenseTier.ENTERPRISE: 10000,
        }

        return tier_limits.get(license_info.tier, license_info.max_queries_per_day)

    def needs_verification(self) -> bool:
        """
        Check if online verification is needed.

        Returns:
            True if should verify online.
        """
        if not self.verification_file.exists():
            return True

        try:
            with open(self.verification_file) as f:
                last_verified_str = f.read().strip()
                last_verified = datetime.fromisoformat(last_verified_str)

            days_since = (datetime.now(timezone.utc) - last_verified).days
            return days_since >= self.VERIFICATION_INTERVAL_DAYS

        except Exception:
            return True

    async def verify_online(self) -> tuple[bool, str]:
        """
        Verify license with online server.

        Returns:
            Tuple of (success, message).
        """
        import httpx

        license_info = self.get_license()
        if not license_info:
            return False, "No license found"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/verify",
                    json={
                        "license_id": license_info.license_id,
                        "machine_id": self.validator.get_machine_id(),
                    },
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("valid"):
                        self._update_verification_time()

                        # Update license if server sent new data
                        if "license" in data:
                            await self._update_license_data(data["license"])

                        return True, "License verified"
                    else:
                        return False, data.get("message", "License invalid")

                elif response.status_code == 404:
                    return False, "License not found on server"
                else:
                    return False, f"Server error: {response.status_code}"

        except httpx.NetworkError:
            # Network unavailable - use grace period
            if self.get_status() in [LicenseStatus.ACTIVE, LicenseStatus.GRACE_PERIOD]:
                return True, "Offline mode - using cached license"
            return False, "Cannot verify license offline"

        except Exception as e:
            return False, f"Verification failed: {e}"

    async def _update_license_data(self, new_data: dict):
        """Update stored license with new data from server."""
        if not self.license_file.exists():
            return

        try:
            with open(self.license_file) as f:
                stored = json.load(f)

            stored["data"] = new_data
            stored["updated_at"] = datetime.now(timezone.utc).isoformat()

            with open(self.license_file, "w") as f:
                json.dump(stored, f, indent=2)

            # Clear cache
            self._cached_license = None
            self._cached_status = None

        except Exception:
            pass

    def _update_verification_time(self):
        """Update last verification timestamp."""
        with open(self.verification_file, "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())

    def deactivate(self) -> bool:
        """
        Deactivate and remove license.

        Returns:
            True if successful.
        """
        try:
            if self.license_file.exists():
                self.license_file.unlink()

            if self.verification_file.exists():
                self.verification_file.unlink()

            self._cached_license = None
            self._cached_status = None

            return True
        except Exception:
            return False

    def get_status_message(self) -> str:
        """
        Get human-readable status message.

        Returns:
            Status message string.
        """
        status = self.get_status()
        license_info = self.get_license()

        if status == LicenseStatus.NOT_FOUND:
            return "No license activated. Using free tier (10 queries/day)."

        if status == LicenseStatus.INVALID:
            return "Invalid license. Please reactivate."

        if status == LicenseStatus.EXPIRED:
            return "License expired. Please renew to continue using Dora."

        if status == LicenseStatus.GRACE_PERIOD:
            if license_info:
                grace_end = license_info.expires_at + timedelta(
                    days=license_info.grace_period_days
                )
                days_left = (grace_end - datetime.now(timezone.utc)).days
                return f"License expired. Grace period: {days_left} days remaining. Please renew."
            return "License in grace period. Please renew."

        if status == LicenseStatus.ACTIVE and license_info:
            days_left = self.validator.days_until_expiry(
                {"expires_at": license_info.expires_at.isoformat()}
            )
            return f"License active ({license_info.tier.value}). Expires in {days_left} days."

        return "License status unknown."

    def generate_trial_license(self, email: str, days: int = 14) -> str:
        """
        Generate a trial license (for development/testing).

        Args:
            email: User email.
            days: Trial duration.

        Returns:
            License key string.
        """
        import uuid

        license_data = {
            "license_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "user_email": email,
            "tier": LicenseTier.PROFESSIONAL.value,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(days=days)
            ).isoformat(),
            "grace_period_days": 7,
            "features": ["trial"],
            "max_queries_per_day": 50,
            "offline_allowed": True,
            "is_trial": True,
        }

        return self.validator.create_license(license_data)
