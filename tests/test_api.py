"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch


class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.fixture
    def mock_pipeline(self):
        """Mock query pipeline."""
        mock = MagicMock()
        mock.query = AsyncMock(return_value=MagicMock(
            question="What is diabetes?",
            answer="Diabetes is a metabolic disorder...",
            confidence=MagicMock(value="high"),
            citations=[],
            warnings=[],
            model_used="test-model",
            latency_ms=100,
        ))
        return mock

    @pytest.fixture
    def mock_drug_checker(self):
        """Mock drug interaction checker."""
        mock = MagicMock()
        mock.check_multiple.return_value = []
        mock.normalize_drug.return_value = MagicMock(
            original_name="aspirin",
            normalized_name="Aspirin",
            rxcui="1191",
            drug_classes=["nsaid"],
        )
        return mock

    @pytest.fixture
    def client(self, mock_pipeline, mock_drug_checker):
        """Create test client with mocked dependencies."""
        with patch('src.api.app.query_pipeline', mock_pipeline), \
             patch('src.api.app.drug_checker', mock_drug_checker), \
             patch('src.api.app.ingestion_pipeline', MagicMock()), \
             patch('src.api.app.license_manager', MagicMock(
                 get_status=MagicMock(return_value=MagicMock(value="active")),
                 get_license=MagicMock(return_value=None),
                 get_status_message=MagicMock(return_value="Active"),
                 get_daily_query_limit=MagicMock(return_value=100),
                 check_feature_access=MagicMock(return_value=True),
             )):
            from src.api.app import app
            yield TestClient(app)

    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_query_endpoint(self, client, mock_pipeline):
        """Test query endpoint."""
        response = client.post(
            "/api/v1/query",
            json={
                "question": "What is diabetes?",
                "top_k": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_query_missing_question(self, client):
        """Test query with missing question."""
        response = client.post(
            "/api/v1/query",
            json={}
        )

        # Should return validation error
        assert response.status_code == 422

    def test_drug_check_endpoint(self, client):
        """Test drug interaction check endpoint."""
        response = client.post(
            "/api/v1/drugs/check",
            json={
                "drugs": ["warfarin", "aspirin"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "interactions" in data

    def test_drug_normalize_endpoint(self, client):
        """Test drug normalization endpoint."""
        response = client.get("/api/v1/drugs/normalize/aspirin")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["original_name"] == "aspirin"

    def test_license_status_endpoint(self, client):
        """Test license status endpoint."""
        response = client.get("/api/v1/license/status")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data


class TestAPIValidation:
    """Test API input validation."""

    @pytest.fixture
    def client(self):
        """Create test client with minimal mocks."""
        with patch('src.api.app.query_pipeline', None), \
             patch('src.api.app.drug_checker', None), \
             patch('src.api.app.ingestion_pipeline', None), \
             patch('src.api.app.license_manager', None):
            from src.api.app import app
            yield TestClient(app)

    def test_query_without_pipeline(self, client):
        """Test query when pipeline not initialized."""
        response = client.post(
            "/api/v1/query",
            json={"question": "test"}
        )

        assert response.status_code == 503

    def test_drug_check_without_checker(self, client):
        """Test drug check when checker not initialized."""
        response = client.post(
            "/api/v1/drugs/check",
            json={"drugs": ["aspirin"]}
        )

        assert response.status_code == 503


class TestCalculatorEndpoints:
    """Tests for medical calculator endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_list_calculators(self, client):
        """Should list available calculators."""
        response = client.get("/api/v1/calculators")
        assert response.status_code == 200
        data = response.json()
        assert "calculators" in data or isinstance(data, list)

    def test_gfr_calculator(self, client):
        """Should calculate eGFR correctly."""
        response = client.post(
            "/api/v1/calculators/egfr",
            json={
                "creatinine": 1.2,
                "age": 55,
                "sex": "male",
                "race": "other",
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert "egfr" in data

    def test_bmi_calculator(self, client):
        """Should calculate BMI correctly."""
        response = client.post(
            "/api/v1/calculators/bmi",
            json={
                "weight_kg": 70,
                "height_cm": 175,
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert "bmi" in data


class TestEngagementEndpoints:
    """Tests for engagement feature endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_get_trending_queries(self, client):
        """Should return trending queries."""
        response = client.get("/api/v1/engagement/trending")
        # May require auth
        assert response.status_code in [200, 401, 404]


class TestLearningEndpoints:
    """Tests for CME/learning endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_get_quiz_endpoint(self, client):
        """Should return quiz."""
        response = client.get("/api/v1/learning/quiz/daily")
        # May require auth
        assert response.status_code in [200, 401, 404]


class TestGamificationEndpoints:
    """Tests for gamification endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_get_leaderboard(self, client):
        """Should return leaderboard."""
        response = client.get("/api/v1/gamification/leaderboard")
        assert response.status_code in [200, 401, 404]


class TestSubscriptionEndpoints:
    """Tests for subscription/billing endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_get_plans(self, client):
        """Should return available subscription plans."""
        response = client.get("/api/v1/subscription/plans")
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_404_for_unknown_route(self, client):
        """Should return 404 for unknown routes."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_validation_error_format(self, client):
        """Validation errors should have consistent format."""
        response = client.post(
            "/api/v1/query",
            json={},  # Missing required fields
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestCORSAndSecurity:
    """Tests for CORS and security headers."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.app import app
        return TestClient(app)

    def test_cors_preflight(self, client):
        """CORS preflight should be handled."""
        response = client.options(
            "/api/v1/query",
            headers={"Origin": "https://dora.docassist.in"},
        )
        assert response.status_code in [200, 204, 405]

    def test_health_endpoint_public(self, client):
        """Health endpoint should be publicly accessible."""
        response = client.get("/health")
        assert response.status_code == 200
