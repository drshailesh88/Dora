"""Pytest configuration and fixtures."""

import pytest


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
