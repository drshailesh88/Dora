"""
Pytest configuration and shared fixtures for Dora test suite.
Provides comprehensive fixtures for unit and integration testing.
"""

import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

pytest_plugins = ['pytest_asyncio']


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Sample Medical Content
# ============================================================================

@pytest.fixture
def sample_text():
    """Sample medical text for testing."""
    return """
    Diabetes Mellitus Management

    Type 2 Diabetes Treatment:
    - First-line therapy: Metformin 500mg BD, titrate to 1000mg BD
    - If HbA1c > 7.5% after 3 months, add second agent
    - Options: SGLT2 inhibitors, GLP-1 agonists, DPP-4 inhibitors

    Monitoring:
    - HbA1c every 3 months until stable, then every 6 months
    - Fasting glucose target: 80-130 mg/dL
    - Post-prandial glucose: <180 mg/dL

    Contraindications for Metformin:
    - eGFR < 30 mL/min
    - Active liver disease
    - History of lactic acidosis
    """


@pytest.fixture
def sample_chunks(sample_text):
    """Create sample chunks for testing."""
    from src.core.models import Chunk

    return [
        Chunk(
            text=sample_text,
            metadata={
                "source": "Test Textbook",
                "page": 1,
                "doc_type": "textbook",
            },
        )
    ]


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create test FastAPI application."""
    from src.api.app import app
    return app


@pytest.fixture
def client(app) -> Generator:
    """Create synchronous test client."""
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user():
    """Sample test user data."""
    return {
        "id": "user_test_123",
        "email": "test@example.com",
        "name": "Dr. Test User",
        "specialty": "cardiology",
        "license_number": "MCI-12345",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def test_credentials():
    """Test user credentials."""
    return {"email": "test@example.com", "password": "SecureTestPass123!"}


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers with test token."""
    try:
        from src.auth.jwt_handler import create_access_token
        token = create_access_token(data={"sub": test_user["id"], "email": test_user["email"]})
        return {"Authorization": f"Bearer {token}"}
    except Exception:
        return {"Authorization": "Bearer test_token_123"}


# ============================================================================
# Patient & Medical Data Fixtures
# ============================================================================

@pytest.fixture
def sample_patient():
    """Sample patient data for testing."""
    return {
        "id": "patient_123",
        "mrn": "MRN-2024-001",
        "name": "Rahul Sharma",
        "age": 45,
        "sex": "male",
        "weight_kg": 75.0,
        "allergies": [{"drug": "Penicillin", "reaction": "Anaphylaxis", "severity": "severe"}],
        "medications": [
            {"name": "Metformin", "dose": "500mg", "frequency": "BID"},
            {"name": "Lisinopril", "dose": "10mg", "frequency": "QD"},
        ],
        "conditions": [{"name": "Type 2 Diabetes", "icd10": "E11.9"}, {"name": "Hypertension", "icd10": "I10"}],
        "labs": {"creatinine": 1.2, "egfr": 65, "hba1c": 7.5},
    }


@pytest.fixture
def sample_drug():
    """Sample drug data."""
    return {
        "id": "drug_metformin",
        "generic_name": "Metformin",
        "brand_names": ["Glycomet", "Glucophage"],
        "drug_class": "Biguanide",
        "pregnancy_category": "B",
    }


@pytest.fixture
def sample_query():
    """Sample medical query."""
    return {"query": "What is the first-line treatment for hypertension?", "specialty": "cardiology"}


# ============================================================================
# Mock Services
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    mock = AsyncMock()
    mock.generate.return_value = {"content": "Based on guidelines...", "citations": []}
    return mock


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    mock = AsyncMock()
    mock.search.return_value = [{"id": "doc1", "content": "Test content", "score": 0.95}]
    return mock


@pytest.fixture
def mock_razorpay():
    """Mock Razorpay client."""
    mock = MagicMock()
    mock.order.create.return_value = {"id": "order_123", "amount": 99900, "status": "created"}
    return mock


# ============================================================================
# Calculator Test Cases
# ============================================================================

@pytest.fixture
def calculator_test_cases():
    """Test cases for medical calculators."""
    return {
        "gfr": [
            {"creatinine": 1.0, "age": 40, "sex": "male", "expected_range": (85, 95)},
            {"creatinine": 1.5, "age": 65, "sex": "female", "expected_range": (35, 45)},
        ],
        "bmi": [
            {"weight": 70, "height": 175, "expected": 22.9},
            {"weight": 90, "height": 170, "expected": 31.1},
        ],
    }


# ============================================================================
# Subscription Fixtures
# ============================================================================

@pytest.fixture
def sample_subscription():
    """Sample subscription data."""
    return {
        "id": "sub_123",
        "user_id": "user_test_123",
        "plan_id": "professional",
        "status": "active",
        "amount": 1999,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def assert_valid_response(response, expected_status=200):
    """Assert response has expected status."""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"


def assert_contains_keys(data: dict, keys: list):
    """Assert dict contains required keys."""
    for key in keys:
        assert key in data, f"Missing key: {key}"
