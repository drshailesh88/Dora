"""
Digital signature system for e-prescriptions.

Implements:
- Digital certificate management
- Signature generation and verification
- Audit trail
- Regulatory compliance
"""

import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
import json

from .models import DigitalSignature, Prescription, EPrescription


class DigitalCertificate:
    """Digital certificate for doctor."""

    def __init__(
        self,
        certificate_id: str,
        doctor_id: str,
        doctor_name: str,
        registration_number: str,
        issuer: str,
        issued_at: datetime,
        expires_at: datetime,
        public_key: str,
        private_key: Optional[str] = None,
    ):
        """
        Initialize certificate.

        Args:
            certificate_id: Unique certificate ID
            doctor_id: Doctor's ID
            doctor_name: Doctor's name
            registration_number: Medical registration number
            issuer: Certificate authority (e.g., "India Digital Health Authority")
            issued_at: Issue date
            expires_at: Expiry date
            public_key: Public key for verification
            private_key: Private key for signing (keep secure)
        """
        self.certificate_id = certificate_id
        self.doctor_id = doctor_id
        self.doctor_name = doctor_name
        self.registration_number = registration_number
        self.issuer = issuer
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.public_key = public_key
        self.private_key = private_key  # Should be stored securely

    def is_valid(self) -> bool:
        """Check if certificate is still valid."""
        now = datetime.utcnow()
        return self.issued_at <= now <= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes private key)."""
        return {
            'certificate_id': self.certificate_id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor_name,
            'registration_number': self.registration_number,
            'issuer': self.issuer,
            'issued_at': self.issued_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'public_key': self.public_key,
        }


class SignatureService:
    """Service for creating and verifying digital signatures."""

    def __init__(self, certificate_store=None):
        """
        Initialize signature service.

        Args:
            certificate_store: Storage for digital certificates
        """
        self.certificate_store = certificate_store or {}

    def sign_prescription(
        self,
        prescription: Prescription,
        doctor_certificate: DigitalCertificate,
        pin: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> DigitalSignature:
        """
        Digitally sign a prescription.

        Args:
            prescription: Prescription to sign
            doctor_certificate: Doctor's digital certificate
            pin: PIN for authentication (optional)
            ip_address: IP address of signing device
            device_info: Device information

        Returns:
            Digital signature

        Raises:
            ValueError: If certificate invalid or doctor mismatch
        """
        # Validate certificate
        if not doctor_certificate.is_valid():
            raise ValueError("Digital certificate has expired")

        # Verify doctor matches
        if prescription.doctor.doctor_id != doctor_certificate.doctor_id:
            raise ValueError("Certificate does not belong to prescribing doctor")

        # Generate signature data
        signature_data = self._generate_signature(
            prescription,
            doctor_certificate.private_key or "DEMO_KEY"
        )

        # Create signature object
        signature = DigitalSignature(
            signature_id=f"SIG-{uuid4().hex[:16].upper()}",
            doctor_id=doctor_certificate.doctor_id,
            signature_data=signature_data,
            signature_method="digital_certificate",
            timestamp=datetime.utcnow(),
            certificate_id=doctor_certificate.certificate_id,
            verified=True,  # Auto-verified on creation
            verification_timestamp=datetime.utcnow(),
            ip_address=ip_address,
            device_info=device_info,
        )

        return signature

    def verify_signature(
        self,
        signature: DigitalSignature,
        prescription: Prescription,
    ) -> bool:
        """
        Verify a digital signature.

        Args:
            signature: Signature to verify
            prescription: Prescription that was signed

        Returns:
            True if valid, False otherwise
        """
        # Get certificate
        if signature.certificate_id:
            certificate = self.certificate_store.get(signature.certificate_id)
            if not certificate:
                return False

            # Check certificate validity
            if not certificate.is_valid():
                return False

            # Verify signature data
            expected_signature = self._generate_signature(
                prescription,
                certificate.private_key or "DEMO_KEY"
            )

            return expected_signature == signature.signature_data

        return False

    def _generate_signature(
        self,
        prescription: Prescription,
        private_key: str
    ) -> str:
        """
        Generate signature hash for prescription.

        In production, this would use proper cryptographic signing (RSA, etc.).
        For demo, we use SHA-256 hash.

        Args:
            prescription: Prescription to sign
            private_key: Private key for signing

        Returns:
            Base64-encoded signature
        """
        # Create canonical representation of prescription
        canonical = self._canonicalize_prescription(prescription)

        # Combine with private key
        data = f"{canonical}|{private_key}".encode('utf-8')

        # Generate hash
        signature_hash = hashlib.sha256(data).digest()

        # Encode as base64
        return base64.b64encode(signature_hash).decode('ascii')

    def _canonicalize_prescription(self, prescription: Prescription) -> str:
        """
        Create canonical string representation for signing.

        Only includes fields that should not change.
        """
        fields = {
            'prescription_id': prescription.prescription_id,
            'patient_id': prescription.patient.patient_id,
            'doctor_id': prescription.doctor.doctor_id,
            'date_prescribed': prescription.date_prescribed.isoformat(),
            'items': [
                {
                    'drug': item.drug_name,
                    'strength': item.strength,
                    'quantity': item.quantity,
                    'dosage': {
                        'dose': item.dosage.dose,
                        'frequency': item.dosage.frequency,
                        'duration': item.dosage.duration_days,
                    }
                }
                for item in prescription.items
            ],
        }

        # Convert to stable JSON (sorted keys)
        return json.dumps(fields, sort_keys=True)

    def register_certificate(self, certificate: DigitalCertificate):
        """Register a digital certificate."""
        self.certificate_store[certificate.certificate_id] = certificate

    def get_certificate(self, certificate_id: str) -> Optional[DigitalCertificate]:
        """Get certificate by ID."""
        return self.certificate_store.get(certificate_id)

    def revoke_certificate(self, certificate_id: str, reason: str):
        """
        Revoke a certificate.

        In production, this would add to CRL (Certificate Revocation List).
        """
        certificate = self.certificate_store.get(certificate_id)
        if certificate:
            # Mark as expired
            certificate.expires_at = datetime.utcnow()


class SignatureAuditTrail:
    """Audit trail for signature events."""

    def __init__(self, storage=None):
        """Initialize audit trail."""
        self.storage = storage or []

    def log_signature_creation(
        self,
        signature: DigitalSignature,
        prescription_id: str,
        success: bool,
        error: Optional[str] = None,
    ):
        """Log signature creation event."""
        event = {
            'event_type': 'signature_created',
            'timestamp': datetime.utcnow().isoformat(),
            'signature_id': signature.signature_id,
            'prescription_id': prescription_id,
            'doctor_id': signature.doctor_id,
            'success': success,
            'error': error,
            'ip_address': signature.ip_address,
            'device_info': signature.device_info,
        }
        self.storage.append(event)

    def log_signature_verification(
        self,
        signature_id: str,
        prescription_id: str,
        verified: bool,
        verified_by: Optional[str] = None,
    ):
        """Log signature verification event."""
        event = {
            'event_type': 'signature_verified',
            'timestamp': datetime.utcnow().isoformat(),
            'signature_id': signature_id,
            'prescription_id': prescription_id,
            'verified': verified,
            'verified_by': verified_by,
        }
        self.storage.append(event)

    def get_audit_log(
        self,
        prescription_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
    ) -> list:
        """Get audit log with optional filters."""
        logs = self.storage

        if prescription_id:
            logs = [e for e in logs if e.get('prescription_id') == prescription_id]

        if doctor_id:
            logs = [e for e in logs if e.get('doctor_id') == doctor_id]

        return logs


class PINAuthentication:
    """PIN-based authentication for digital signing."""

    def __init__(self, pin_store=None):
        """Initialize PIN authentication."""
        self.pin_store = pin_store or {}

    def set_pin(self, doctor_id: str, pin: str):
        """
        Set/update PIN for doctor.

        In production, PIN should be hashed and salted.
        """
        # Hash PIN
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        self.pin_store[doctor_id] = pin_hash

    def verify_pin(self, doctor_id: str, pin: str) -> bool:
        """Verify doctor's PIN."""
        stored_hash = self.pin_store.get(doctor_id)
        if not stored_hash:
            return False

        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        return pin_hash == stored_hash

    def reset_pin(self, doctor_id: str, old_pin: str, new_pin: str) -> bool:
        """Reset PIN (requires old PIN)."""
        if not self.verify_pin(doctor_id, old_pin):
            return False

        self.set_pin(doctor_id, new_pin)
        return True


class BiometricAuthentication:
    """Biometric authentication for digital signing (future)."""

    def __init__(self):
        """Initialize biometric authentication."""
        self.registered_biometrics = {}

    def register_fingerprint(self, doctor_id: str, fingerprint_data: str):
        """Register fingerprint for doctor."""
        # In production, use proper biometric SDK
        self.registered_biometrics[doctor_id] = {
            'type': 'fingerprint',
            'data': fingerprint_data,
        }

    def verify_fingerprint(self, doctor_id: str, fingerprint_data: str) -> bool:
        """Verify fingerprint."""
        stored = self.registered_biometrics.get(doctor_id)
        if not stored or stored['type'] != 'fingerprint':
            return False

        # In production, use proper biometric matching
        return stored['data'] == fingerprint_data


# Example usage
if __name__ == "__main__":
    from datetime import timedelta
    from .models import (
        Prescription, PrescriptionItem, PatientInfo, DoctorInfo,
        Dosage, DosageForm, Frequency, RouteOfAdministration
    )

    # Create digital certificate
    certificate = DigitalCertificate(
        certificate_id="CERT-001",
        doctor_id="DOC-001",
        doctor_name="Dr. Shailesh Kumar",
        registration_number="MCI-12345",
        issuer="India Digital Health Authority",
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        public_key="PUBLIC_KEY_DATA",
        private_key="PRIVATE_KEY_DATA",
    )

    # Create sample prescription
    patient = PatientInfo(
        patient_id="PAT-001",
        name="Test Patient",
        age=45,
        gender="M",
    )

    doctor = DoctorInfo(
        doctor_id="DOC-001",
        name="Dr. Shailesh Kumar",
        qualifications="MD, MBBS",
        registration_number="MCI-12345",
    )

    item = PrescriptionItem(
        drug_name="Metformin",
        strength="500mg",
        dosage_form=DosageForm.TABLET,
        dosage=Dosage(
            dose="1 tablet",
            frequency=Frequency.BD,
            duration_days=30,
            route=RouteOfAdministration.ORAL,
        ),
        quantity=60,
        quantity_unit="tablets",
        item_sequence=1,
    )

    prescription = Prescription(
        prescription_id="RX-001",
        patient=patient,
        doctor=doctor,
        items=[item],
        created_by="doctor",
    )

    # Sign prescription
    signature_service = SignatureService()
    signature_service.register_certificate(certificate)

    signature = signature_service.sign_prescription(
        prescription,
        certificate,
        ip_address="192.168.1.1",
        device_info="Desktop - Chrome",
    )

    print(f"Created signature: {signature.signature_id}")
    print(f"Signature data: {signature.signature_data[:50]}...")
    print(f"Verified: {signature.verified}")

    # Verify signature
    is_valid = signature_service.verify_signature(signature, prescription)
    print(f"Signature valid: {is_valid}")
