"""Cryptographic license validation."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Using HMAC-SHA256 for license validation
# In production, use RSA or Ed25519 asymmetric signing


class LicenseValidator:
    """
    Validate license signatures.

    Uses HMAC-SHA256 for offline validation.
    Production should use asymmetric keys.
    """

    def __init__(self, public_key: str | None = None):
        """
        Initialize validator.

        Args:
            public_key: Validation key (in production, actual public key).
        """
        # In production, this would be an RSA/Ed25519 public key
        # For now, using a shared secret approach
        self._key = (public_key or "dora-license-key-v1").encode()

    def create_license(
        self,
        license_data: dict,
        secret_key: str | None = None,
    ) -> str:
        """
        Create a signed license (server-side operation).

        Args:
            license_data: License details.
            secret_key: Signing secret.

        Returns:
            Base64-encoded signed license.
        """
        key = (secret_key or "dora-license-key-v1").encode()

        # Serialize license data
        data_json = json.dumps(license_data, sort_keys=True, default=str)
        data_bytes = data_json.encode()

        # Create HMAC signature
        signature = hmac.new(key, data_bytes, hashlib.sha256).digest()

        # Combine data + signature
        license_blob = {
            "data": base64.b64encode(data_bytes).decode(),
            "sig": base64.b64encode(signature).decode(),
            "v": 1,  # License format version
        }

        return base64.b64encode(json.dumps(license_blob).encode()).decode()

    def validate_license(self, license_str: str) -> tuple[bool, dict | None]:
        """
        Validate a signed license.

        Args:
            license_str: Base64-encoded signed license.

        Returns:
            Tuple of (is_valid, license_data).
        """
        try:
            # Decode outer envelope
            license_blob = json.loads(base64.b64decode(license_str))

            if license_blob.get("v") != 1:
                return False, None

            data_bytes = base64.b64decode(license_blob["data"])
            signature = base64.b64decode(license_blob["sig"])

            # Verify signature
            expected_sig = hmac.new(self._key, data_bytes, hashlib.sha256).digest()

            if not hmac.compare_digest(signature, expected_sig):
                return False, None

            # Parse license data
            license_data = json.loads(data_bytes)

            return True, license_data

        except Exception:
            return False, None

    def get_machine_id(self) -> str:
        """
        Get unique machine identifier.

        Returns:
            Machine ID hash.
        """
        identifiers = []

        # Try various system identifiers
        try:
            # Linux machine ID
            machine_id_path = Path("/etc/machine-id")
            if machine_id_path.exists():
                identifiers.append(machine_id_path.read_text().strip())
        except Exception:
            pass

        try:
            # macOS hardware UUID
            import subprocess

            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
            )
            if "IOPlatformUUID" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        uuid = line.split("=")[-1].strip().strip('"')
                        identifiers.append(uuid)
                        break
        except Exception:
            pass

        try:
            # Windows machine GUID
            import subprocess

            result = subprocess.run(
                ["reg", "query",
                 "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography",
                 "/v", "MachineGuid"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.split("\n"):
                if "MachineGuid" in line:
                    guid = line.split()[-1]
                    identifiers.append(guid)
                    break
        except Exception:
            pass

        # Fallback to hostname
        if not identifiers:
            import socket
            identifiers.append(socket.gethostname())

        # Hash all identifiers
        combined = "|".join(identifiers)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def is_license_expired(self, license_data: dict) -> bool:
        """
        Check if license has expired.

        Args:
            license_data: Validated license data.

        Returns:
            True if expired.
        """
        expiry_str = license_data.get("expires_at")
        if not expiry_str:
            return True

        try:
            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return now > expiry
        except Exception:
            return True

    def days_until_expiry(self, license_data: dict) -> int:
        """
        Get days until license expires.

        Args:
            license_data: Validated license data.

        Returns:
            Days remaining (negative if expired).
        """
        expiry_str = license_data.get("expires_at")
        if not expiry_str:
            return -999

        try:
            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = expiry - now
            return delta.days
        except Exception:
            return -999
