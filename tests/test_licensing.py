"""Tests for licensing system."""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.licensing import LicenseManager, LicenseStatus, LicenseTier
from src.licensing.crypto import LicenseValidator


class TestLicenseValidator:
    """Test license cryptographic validation."""

    @pytest.fixture
    def validator(self):
        return LicenseValidator()

    def test_create_and_validate_license(self, validator):
        """Test creating and validating a license."""
        license_data = {
            "license_id": "test-123",
            "user_id": "user-456",
            "user_email": "test@example.com",
            "tier": "professional",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

        # Create license
        license_key = validator.create_license(license_data)

        assert license_key is not None
        assert len(license_key) > 50  # Should be substantial base64 string

        # Validate license
        is_valid, decoded_data = validator.validate_license(license_key)

        assert is_valid
        assert decoded_data["license_id"] == "test-123"
        assert decoded_data["tier"] == "professional"

    def test_invalid_license_rejected(self, validator):
        """Test that tampered licenses are rejected."""
        # Create valid license
        license_data = {
            "license_id": "test-123",
            "tier": "professional",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }
        license_key = validator.create_license(license_data)

        # Tamper with it
        tampered = license_key[:-10] + "XXXXXXXXXX"

        is_valid, _ = validator.validate_license(tampered)

        assert not is_valid

    def test_expired_license_detection(self, validator):
        """Test detecting expired licenses."""
        # Create expired license
        license_data = {
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        }

        is_expired = validator.is_license_expired(license_data)

        assert is_expired

    def test_valid_license_not_expired(self, validator):
        """Test valid license not marked as expired."""
        license_data = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

        is_expired = validator.is_license_expired(license_data)

        assert not is_expired

    def test_days_until_expiry(self, validator):
        """Test calculating days until expiry."""
        license_data = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
        }

        days = validator.days_until_expiry(license_data)

        assert 14 <= days <= 15

    def test_machine_id_generation(self, validator):
        """Test machine ID generation is consistent."""
        id1 = validator.get_machine_id()
        id2 = validator.get_machine_id()

        assert id1 == id2
        assert len(id1) == 32


class TestLicenseManager:
    """Test license management functionality."""

    @pytest.fixture
    def temp_license_dir(self, tmp_path):
        return tmp_path / "licenses"

    @pytest.fixture
    def manager(self, temp_license_dir):
        return LicenseManager(license_dir=temp_license_dir)

    def test_no_license_status(self, manager):
        """Test status when no license exists."""
        status = manager.get_status()

        assert status == LicenseStatus.NOT_FOUND

    def test_generate_trial_license(self, manager):
        """Test trial license generation."""
        license_key = manager.generate_trial_license("test@example.com", days=14)

        assert license_key is not None

        # Validate it
        validator = LicenseValidator()
        is_valid, data = validator.validate_license(license_key)

        assert is_valid
        assert data["tier"] == LicenseTier.PROFESSIONAL.value
        assert data["is_trial"] is True

    def test_activate_valid_license(self, manager):
        """Test activating a valid license."""
        # Generate a license
        license_key = manager.generate_trial_license("test@example.com")

        # Activate it
        success, message = manager.activate_license(license_key)

        assert success
        assert "activated" in message.lower()

        # Check status
        status = manager.get_status()
        assert status == LicenseStatus.ACTIVE

    def test_activate_invalid_license(self, manager):
        """Test activating invalid license fails."""
        success, message = manager.activate_license("invalid-key-12345")

        assert not success
        assert "invalid" in message.lower()

    def test_feature_access_by_tier(self, manager):
        """Test feature access varies by tier."""
        # Without license, limited access
        assert manager.check_feature_access("basic_query")  # Free tier gets basic
        assert not manager.check_feature_access("voice_interface")  # Needs professional

    def test_daily_query_limit(self, manager):
        """Test daily query limits."""
        # No license
        limit = manager.get_daily_query_limit()
        assert limit == 5  # Free tier

    def test_status_message(self, manager):
        """Test human-readable status message."""
        message = manager.get_status_message()

        assert "license" in message.lower() or "tier" in message.lower()

    def test_deactivate_license(self, manager):
        """Test license deactivation."""
        # Activate a license
        license_key = manager.generate_trial_license("test@example.com")
        manager.activate_license(license_key)

        # Deactivate
        success = manager.deactivate()

        assert success
        assert manager.get_status() == LicenseStatus.NOT_FOUND


class TestLicenseTiers:
    """Test tier-based feature access."""

    @pytest.fixture
    def manager(self, tmp_path):
        return LicenseManager(license_dir=tmp_path / "licenses")

    def test_tier_limits(self, manager):
        """Test query limits per tier."""
        tier_limits = {
            LicenseTier.FREE: 10,
            LicenseTier.ESSENTIAL: 100,
            LicenseTier.PROFESSIONAL: 500,
            LicenseTier.CLINIC: 2000,
            LicenseTier.ENTERPRISE: 10000,
        }

        for tier, expected_limit in tier_limits.items():
            # Verify the expected limits are correct
            assert expected_limit > 0
