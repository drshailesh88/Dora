"""
Tests for Authentication Module
"""

import pytest
from datetime import datetime, timedelta

from src.auth.models import User, UserRole, AuthProvider, Session
from src.auth.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_password,
    generate_verification_code,
)
from src.auth.jwt_handler import JWTHandler
from src.auth.storage import AuthStorage
from src.auth.service import AuthService, AuthResult


class TestPassword:
    """Tests for password utilities."""

    def test_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "SecureP@ss123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_validate_password_strength(self):
        """Test password strength validation."""
        # Weak passwords
        is_valid, issues = validate_password_strength("short")
        assert not is_valid
        assert len(issues) > 0

        is_valid, issues = validate_password_strength("alllowercase")
        assert not is_valid

        is_valid, issues = validate_password_strength("ALLUPPERCASE")
        assert not is_valid

        is_valid, issues = validate_password_strength("NoNumbers!")
        assert not is_valid

        is_valid, issues = validate_password_strength("NoSpecial123")
        assert not is_valid

        # Strong password
        is_valid, issues = validate_password_strength("SecureP@ss123")
        assert is_valid
        assert len(issues) == 0

    def test_generate_password(self):
        """Test password generation."""
        password = generate_password(16)
        assert len(password) == 16

        # Should be unique
        password2 = generate_password(16)
        assert password != password2

    def test_generate_verification_code(self):
        """Test verification code generation."""
        code = generate_verification_code(6)
        assert len(code) == 6
        assert code.isdigit()


class TestJWTHandler:
    """Tests for JWT token handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.jwt = JWTHandler(
            secret_key="test_secret_key_12345",
            access_token_expire_minutes=60,
            refresh_token_expire_days=7,
        )

    def test_create_access_token(self):
        """Test access token creation."""
        token = self.jwt.create_access_token(
            user_id="user123",
            email="test@example.com",
            role="doctor",
            name="Dr. Test",
        )

        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format

    def test_verify_access_token(self):
        """Test access token verification."""
        token = self.jwt.create_access_token(
            user_id="user123",
            email="test@example.com",
            role="doctor",
            name="Dr. Test",
            org_id="org123",
        )

        payload = self.jwt.verify_access_token(token)

        assert payload is not None
        assert payload.sub == "user123"
        assert payload.email == "test@example.com"
        assert payload.role == "doctor"
        assert payload.name == "Dr. Test"
        assert payload.org_id == "org123"
        assert payload.type == "access"

    def test_verify_invalid_token(self):
        """Test verification of invalid tokens."""
        payload = self.jwt.verify_access_token("invalid_token")
        assert payload is None

        # Tampered token
        valid_token = self.jwt.create_access_token(
            user_id="user123",
            email="test@example.com",
            role="doctor",
            name="Dr. Test",
        )
        tampered = valid_token[:-10] + "tampered12"
        payload = self.jwt.verify_access_token(tampered)
        assert payload is None

    def test_create_and_verify_refresh_token(self):
        """Test refresh token creation and verification."""
        token = self.jwt.create_refresh_token("user123")

        assert isinstance(token, str)
        assert len(token) > 0

        user_id = self.jwt.verify_refresh_token(token)
        assert user_id == "user123"

    def test_create_token_pair(self):
        """Test creating access and refresh tokens together."""
        access, refresh, expires_in = self.jwt.create_token_pair(
            user_id="user123",
            email="test@example.com",
            role="doctor",
            name="Dr. Test",
        )

        assert access is not None
        assert refresh is not None
        assert expires_in == 3600  # 60 minutes

        # Verify both tokens
        access_payload = self.jwt.verify_access_token(access)
        assert access_payload.sub == "user123"

        user_id = self.jwt.verify_refresh_token(refresh)
        assert user_id == "user123"


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """Test user model creation."""
        user = User(
            email="test@example.com",
            name="Dr. Test",
            role=UserRole.DOCTOR,
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.DOCTOR
        assert user.provider == AuthProvider.LOCAL
        assert user.is_active

    def test_user_permissions(self):
        """Test role-based permissions."""
        doctor = User(email="doc@test.com", name="Doctor", role=UserRole.DOCTOR)
        admin = User(email="admin@test.com", name="Admin", role=UserRole.ADMIN)
        student = User(email="student@test.com", name="Student", role=UserRole.STUDENT)

        # Doctor permissions
        assert doctor.has_permission("query")
        assert doctor.has_permission("prescribe")
        assert not doctor.has_permission("admin.users")

        # Admin permissions
        assert admin.has_permission("query")
        assert admin.has_permission("admin.users")
        assert admin.has_permission("admin.analytics")

        # Student permissions
        assert student.has_permission("query")
        assert not student.has_permission("prescribe")

    def test_user_serialization(self):
        """Test user to/from dict."""
        user = User(
            email="test@example.com",
            name="Dr. Test",
            role=UserRole.DOCTOR,
            specialty="Cardiology",
        )

        data = user.to_dict()
        assert data["email"] == "test@example.com"
        assert data["role"] == "doctor"
        assert data["specialty"] == "Cardiology"

        # Reconstruct
        user2 = User.from_dict(data)
        assert user2.email == user.email
        assert user2.role == user.role


class TestAuthStorage:
    """Tests for auth storage."""

    def setup_method(self):
        """Set up test fixtures with in-memory DB."""
        import tempfile
        import os

        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_auth.db")
        self.storage = AuthStorage(db_path=self.db_path)

    def teardown_method(self):
        """Clean up."""
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_create_and_get_user(self):
        """Test user creation and retrieval."""
        user = User(
            email="test@example.com",
            name="Dr. Test",
            role=UserRole.DOCTOR,
        )

        created = self.storage.create_user(user)
        assert created.id == user.id

        # Get by ID
        fetched = self.storage.get_user_by_id(user.id)
        assert fetched is not None
        assert fetched.email == user.email

        # Get by email
        fetched = self.storage.get_user_by_email("test@example.com")
        assert fetched is not None
        assert fetched.id == user.id

    def test_update_user(self):
        """Test user update."""
        user = User(
            email="test@example.com",
            name="Dr. Test",
            role=UserRole.DOCTOR,
        )
        self.storage.create_user(user)

        user.specialty = "Cardiology"
        user.is_verified = True
        self.storage.update_user(user)

        fetched = self.storage.get_user_by_id(user.id)
        assert fetched.specialty == "Cardiology"
        assert fetched.is_verified

    def test_create_and_get_session(self):
        """Test session creation and retrieval."""
        user = User(email="test@example.com", name="Test", role=UserRole.DOCTOR)
        self.storage.create_user(user)

        session = Session(
            user_id=user.id,
            access_token="access123",
            refresh_token="refresh123",
            device_info="Chrome on Windows",
        )
        self.storage.create_session(session)

        # Get by refresh token
        fetched = self.storage.get_session_by_refresh_token("refresh123")
        assert fetched is not None
        assert fetched.user_id == user.id

        # Get user sessions
        sessions = self.storage.get_user_sessions(user.id)
        assert len(sessions) == 1

    def test_revoke_session(self):
        """Test session revocation."""
        user = User(email="test@example.com", name="Test", role=UserRole.DOCTOR)
        self.storage.create_user(user)

        session = Session(
            user_id=user.id,
            access_token="access123",
            refresh_token="refresh123",
        )
        self.storage.create_session(session)

        self.storage.revoke_session(session.id)

        # Should not be found by refresh token
        fetched = self.storage.get_session_by_refresh_token("refresh123")
        assert fetched is None


class TestAuthService:
    """Tests for auth service."""

    def setup_method(self):
        """Set up test fixtures."""
        import tempfile
        import os

        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_auth.db")
        self.storage = AuthStorage(db_path=self.db_path)
        self.jwt = JWTHandler(secret_key="test_secret")
        self.auth = AuthService(storage=self.storage, jwt_handler=self.jwt)

    def teardown_method(self):
        """Clean up."""
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_register(self):
        """Test user registration."""
        result = self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
            specialty="Internal Medicine",
        )

        assert result.success
        assert result.user is not None
        assert result.user.email == "doctor@hospital.com"
        assert not result.user.email_verified

    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        result = self.auth.register(
            email="doctor@hospital.com",
            password="AnotherP@ss456",
            name="Dr. Jones",
        )

        assert not result.success
        assert "already registered" in result.error.lower()

    def test_register_weak_password(self):
        """Test registration with weak password."""
        result = self.auth.register(
            email="doctor@hospital.com",
            password="weak",
            name="Dr. Smith",
        )

        assert not result.success
        assert result.error is not None

    def test_login(self):
        """Test login."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        result = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )

        assert result.success
        assert result.user is not None
        assert result.tokens is not None
        assert result.tokens.access_token

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        result = self.auth.login(
            email="doctor@hospital.com",
            password="WrongP@ss456",
        )

        assert not result.success
        assert "invalid" in result.error.lower()

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        result = self.auth.login(
            email="nobody@example.com",
            password="AnyP@ss123",
        )

        assert not result.success

    def test_refresh_tokens(self):
        """Test token refresh."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        login_result = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )

        refresh_result = self.auth.refresh_tokens(login_result.tokens.refresh_token)

        assert refresh_result.success
        assert refresh_result.tokens is not None
        assert refresh_result.tokens.access_token != login_result.tokens.access_token

    def test_logout(self):
        """Test logout."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        login_result = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )

        success = self.auth.logout(login_result.tokens.refresh_token)
        assert success

        # Token should no longer work
        refresh_result = self.auth.refresh_tokens(login_result.tokens.refresh_token)
        assert not refresh_result.success

    def test_change_password(self):
        """Test password change."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        login_result = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )

        change_result = self.auth.change_password(
            user_id=login_result.user.id,
            current_password="SecureP@ss123",
            new_password="NewSecureP@ss456",
        )

        assert change_result.success

        # Old password should not work
        old_login = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )
        assert not old_login.success

        # New password should work
        new_login = self.auth.login(
            email="doctor@hospital.com",
            password="NewSecureP@ss456",
        )
        assert new_login.success

    def test_password_reset_flow(self):
        """Test password reset flow."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        # Request reset
        token = self.auth.request_password_reset("doctor@hospital.com")
        assert token is not None

        # Reset password
        result = self.auth.reset_password(token, "ResetP@ss789")
        assert result.success

        # Login with new password
        login = self.auth.login(
            email="doctor@hospital.com",
            password="ResetP@ss789",
        )
        assert login.success

    def test_verify_token(self):
        """Test token verification."""
        self.auth.register(
            email="doctor@hospital.com",
            password="SecureP@ss123",
            name="Dr. Smith",
        )

        login_result = self.auth.login(
            email="doctor@hospital.com",
            password="SecureP@ss123",
        )

        user = self.auth.verify_token(login_result.tokens.access_token)
        assert user is not None
        assert user.email == "doctor@hospital.com"

        # Invalid token
        user = self.auth.verify_token("invalid_token")
        assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
