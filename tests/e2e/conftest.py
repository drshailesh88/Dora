"""
Pytest configuration and fixtures for E2E offline mode tests.

Provides comprehensive fixtures for:
- Network simulation (offline/online transitions)
- Local service setup (Ollama, ChromaDB, SQLite)
- Mock data pre-population
- Cleanup utilities
"""

import pytest
import asyncio
import socket
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sqlite3
import json

# Import offline modules
from src.offline import (
    OfflineStorage,
    CacheManager,
    SyncEngine,
    ActionQueue,
    NetworkMonitor,
    CachedDocument,
    OfflineQuery,
    Priority,
)


# ============================================================================
# Network Simulation Fixtures
# ============================================================================

class NetworkBlocker:
    """Context manager to block all outbound network connections."""

    def __init__(self):
        self.original_socket = None
        self.original_getaddrinfo = None

    def __enter__(self):
        """Block network by patching socket."""
        self.original_socket = socket.socket
        self.original_getaddrinfo = socket.getaddrinfo

        def blocked_socket(*args, **kwargs):
            raise OSError("Network is offline (simulated)")

        def blocked_getaddrinfo(*args, **kwargs):
            raise OSError("Network is offline (simulated)")

        socket.socket = blocked_socket
        socket.getaddrinfo = blocked_getaddrinfo
        return self

    def __exit__(self, *args):
        """Restore network."""
        socket.socket = self.original_socket
        socket.getaddrinfo = self.original_getaddrinfo


@pytest.fixture
def network_blocker():
    """Fixture to block all network connections."""
    return NetworkBlocker()


@pytest.fixture
def offline_mode(network_blocker):
    """Context manager to run tests in offline mode."""
    with network_blocker:
        yield


@pytest.fixture
def mock_network_monitor():
    """Mock network monitor with controllable state."""
    monitor = NetworkMonitor()
    monitor.status.is_online = False
    monitor.status.sync_enabled = True
    return monitor


@pytest.fixture
async def network_transition():
    """Fixture to test network state transitions."""
    class NetworkTransition:
        def __init__(self):
            self.monitor = NetworkMonitor()
            self.callbacks_triggered = []

        async def go_offline(self):
            """Simulate going offline."""
            self.monitor.status.is_online = False
            await self.monitor._notify_callbacks()

        async def go_online(self):
            """Simulate coming online."""
            self.monitor.status.is_online = True
            await self.monitor._notify_callbacks()

        def register_callback(self, callback):
            """Register callback for state changes."""
            self.monitor.register_callback(callback)

    return NetworkTransition()


# ============================================================================
# Local Storage Fixtures
# ============================================================================

@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def offline_storage(temp_db_path):
    """Create offline storage with temporary database."""
    storage = OfflineStorage(db_path=temp_db_path)
    yield storage
    # Cleanup
    storage.close()


@pytest.fixture
def cache_manager(offline_storage):
    """Create cache manager with test storage."""
    return CacheManager(
        storage=offline_storage,
        user_specialty="cardiology",
        compression_threshold_kb=10  # Low threshold for testing
    )


@pytest.fixture
def action_queue(offline_storage):
    """Create action queue for offline operations."""
    return ActionQueue(storage=offline_storage)


@pytest.fixture
def sync_engine(offline_storage, action_queue):
    """Create sync engine with mock API client."""
    api_client = MagicMock()
    engine = SyncEngine(
        storage=offline_storage,
        action_queue=action_queue,
        api_client=api_client
    )
    return engine


# ============================================================================
# Pre-populated Data Fixtures
# ============================================================================

@pytest.fixture
def cached_medical_documents():
    """Generate pre-cached medical documents."""
    from datetime import datetime

    documents = [
        CachedDocument(
            doc_id="doc_diabetes_treatment",
            content="""
            Type 2 Diabetes Treatment Guidelines

            First-line therapy:
            - Metformin 500mg BD, titrate to 1000mg BD
            - Lifestyle modifications (diet, exercise)

            Second-line options (if HbA1c > 7.5% after 3 months):
            - SGLT2 inhibitors (empagliflozin, dapagliflozin)
            - GLP-1 agonists (semaglutide, liraglutide)
            - DPP-4 inhibitors (sitagliptin)

            Contraindications:
            - eGFR < 30 mL/min for metformin
            - Active liver disease
            """,
            category="guidelines",
            specialty="endocrinology",
            size_bytes=512,
            is_pinned=True,
            access_count=10,
            last_accessed=datetime.utcnow(),
            metadata={
                "source": "ADA Guidelines 2024",
                "page": 45,
                "version": "2024.1"
            }
        ),
        CachedDocument(
            doc_id="doc_hypertension",
            content="""
            Hypertension Management

            Target BP: < 130/80 mmHg for most patients

            First-line agents:
            - ACE inhibitors (lisinopril 10-40mg daily)
            - ARBs (losartan 50-100mg daily)
            - Calcium channel blockers (amlodipine 5-10mg daily)
            - Thiazide diuretics (hydrochlorothiazide 12.5-25mg daily)

            Lifestyle modifications:
            - DASH diet
            - Exercise 150min/week
            - Sodium restriction < 2g/day
            """,
            category="guidelines",
            specialty="cardiology",
            size_bytes=423,
            is_pinned=False,
            access_count=5,
            last_accessed=datetime.utcnow() - timedelta(days=2),
            metadata={
                "source": "JNC 8 Guidelines",
                "page": 12
            }
        ),
        CachedDocument(
            doc_id="doc_drug_metformin",
            content="""
            Metformin (Glucophage)

            Class: Biguanide

            Dosing:
            - Initial: 500mg once or twice daily with meals
            - Titrate: Increase by 500mg weekly
            - Maximum: 2000mg daily (divided doses)

            Side Effects:
            - GI upset (nausea, diarrhea) - most common
            - Lactic acidosis (rare but serious)
            - Vitamin B12 deficiency with long-term use

            Contraindications:
            - eGFR < 30 mL/min
            - Acute/chronic metabolic acidosis
            - Severe hepatic impairment

            Monitoring:
            - Renal function at baseline and annually
            - HbA1c every 3-6 months
            - Vitamin B12 annually if long-term use
            """,
            category="drug_monograph",
            specialty="all",
            size_bytes=678,
            is_pinned=True,
            access_count=25,
            last_accessed=datetime.utcnow(),
            metadata={
                "drug_name": "metformin",
                "source": "Lexicomp",
                "last_updated": "2024-01-01"
            }
        ),
    ]

    return documents


@pytest.fixture
def populate_cache(cache_manager, cached_medical_documents):
    """Pre-populate cache with medical documents."""
    for doc in cached_medical_documents:
        cache_manager.cache_document(doc, force=True)

    return cache_manager


@pytest.fixture
def sample_patient_data():
    """Generate sample patient data for offline access."""
    return {
        "id": "patient_offline_001",
        "mrn": "MRN-OFFLINE-001",
        "name": "Rajesh Kumar",
        "age": 55,
        "sex": "male",
        "weight_kg": 82.0,
        "height_cm": 170,
        "allergies": [
            {"drug": "Penicillin", "reaction": "Rash", "severity": "moderate"}
        ],
        "medications": [
            {"name": "Metformin", "dose": "1000mg", "frequency": "BID"},
            {"name": "Lisinopril", "dose": "10mg", "frequency": "QD"},
            {"name": "Atorvastatin", "dose": "20mg", "frequency": "QHS"}
        ],
        "conditions": [
            {"name": "Type 2 Diabetes Mellitus", "icd10": "E11.9", "onset": "2019-03-15"},
            {"name": "Hypertension", "icd10": "I10", "onset": "2018-11-20"},
            {"name": "Hyperlipidemia", "icd10": "E78.5", "onset": "2020-06-10"}
        ],
        "labs": {
            "creatinine": 1.1,
            "egfr": 72,
            "hba1c": 7.2,
            "ldl": 95,
            "hdl": 42,
            "triglycerides": 165,
            "glucose_fasting": 125
        },
        "vitals": {
            "bp_systolic": 135,
            "bp_diastolic": 85,
            "heart_rate": 76,
            "temperature": 98.6,
            "oxygen_saturation": 98
        }
    }


@pytest.fixture
def populate_patient_db(offline_storage, sample_patient_data):
    """Pre-populate SQLite with patient data."""
    with offline_storage.get_connection() as conn:
        cursor = conn.cursor()

        # Create patients table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                mrn TEXT UNIQUE,
                data TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert patient data
        cursor.execute(
            "INSERT OR REPLACE INTO patients (id, mrn, data) VALUES (?, ?, ?)",
            (
                sample_patient_data["id"],
                sample_patient_data["mrn"],
                json.dumps(sample_patient_data)
            )
        )

        conn.commit()

    return offline_storage


# ============================================================================
# Local LLM Fixtures (Ollama)
# ============================================================================

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for local LLM testing."""
    mock_client = MagicMock()

    # Mock generate method
    mock_client.generate.return_value = {
        "response": "Based on the guidelines, metformin 500mg BD is the first-line treatment for Type 2 Diabetes.",
        "model": "qwen2.5:3b",
        "done": True
    }

    # Mock chat method
    mock_client.chat.return_value = {
        "message": {
            "content": "The recommended dosage is 500-1000mg twice daily with meals.",
            "role": "assistant"
        },
        "done": True
    }

    # Mock list method (available models)
    mock_client.list.return_value = {
        "models": [
            {"name": "qwen2.5:3b", "size": 2_000_000_000},
            {"name": "qwen2.5:7b", "size": 4_500_000_000},
        ]
    }

    return mock_client


@pytest.fixture
def mock_local_llm(mock_ollama_client):
    """Patch LLM synthesizer to use mock Ollama."""
    with patch('src.llm.synthesizer.MedicalSynthesizer.ollama_client',
               new_callable=lambda: mock_ollama_client):
        yield mock_ollama_client


# ============================================================================
# Voice Service Fixtures
# ============================================================================

@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for offline STT."""
    mock = MagicMock()

    mock.transcribe.return_value = {
        "text": "What is the dosage for metformin?",
        "segments": [
            {
                "text": "What is the dosage for metformin?",
                "start": 0.0,
                "end": 2.5,
                "no_speech_prob": 0.05
            }
        ],
        "language": "en"
    }

    return mock


@pytest.fixture
def mock_piper_tts():
    """Mock Piper TTS for offline speech synthesis."""
    import numpy as np

    mock = MagicMock()

    # Return sample audio data
    mock.synthesize.return_value = np.random.randn(22050).astype(np.float32)

    return mock


@pytest.fixture
def offline_voice_services(mock_whisper_model, mock_piper_tts):
    """Setup all offline voice services."""
    services = {
        "stt": mock_whisper_model,
        "tts": mock_piper_tts,
        "wake_word": MagicMock(detect=AsyncMock(return_value={"detected": True, "confidence": 0.95}))
    }

    return services


# ============================================================================
# Vector Store Fixtures (ChromaDB Local)
# ============================================================================

@pytest.fixture
def temp_chromadb_path():
    """Create temporary ChromaDB directory."""
    temp_dir = tempfile.mkdtemp(prefix="chromadb_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def local_chromadb(temp_chromadb_path):
    """Create local ChromaDB instance."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=temp_chromadb_path)
        collection = client.get_or_create_collection(
            name="medical_knowledge",
            metadata={"description": "Offline medical knowledge base"}
        )

        # Add sample documents
        collection.add(
            documents=[
                "Metformin is first-line treatment for Type 2 Diabetes",
                "Lisinopril is an ACE inhibitor for hypertension",
                "Atorvastatin is used for hyperlipidemia management"
            ],
            metadatas=[
                {"source": "ADA Guidelines", "category": "treatment"},
                {"source": "JNC 8", "category": "treatment"},
                {"source": "ACC Guidelines", "category": "treatment"}
            ],
            ids=["doc1", "doc2", "doc3"]
        )

        yield collection

    except ImportError:
        pytest.skip("ChromaDB not installed")


# ============================================================================
# Cleanup Utilities
# ============================================================================

@pytest.fixture
def cleanup_offline_data():
    """Fixture to clean up all offline data after tests."""
    paths_to_clean = []

    yield paths_to_clean

    # Cleanup all tracked paths
    for path in paths_to_clean:
        if Path(path).exists():
            if Path(path).is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                Path(path).unlink(missing_ok=True)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
async def offline_system(
    offline_storage,
    cache_manager,
    action_queue,
    sync_engine,
    populate_cache,
    populate_patient_db,
    local_chromadb
):
    """Complete offline system integration."""
    system = {
        "storage": offline_storage,
        "cache": cache_manager,
        "queue": action_queue,
        "sync": sync_engine,
        "vector_store": local_chromadb,
    }

    # Ensure offline mode
    sync_engine.network_monitor.status.is_online = False

    yield system

    # Cleanup
    offline_storage.close()


# ============================================================================
# Performance Monitoring Fixtures
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}

        def record(self, operation: str, duration_ms: float):
            """Record operation duration."""
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration_ms)

        def get_stats(self, operation: str) -> Dict[str, float]:
            """Get statistics for operation."""
            if operation not in self.metrics:
                return {}

            durations = self.metrics[operation]
            return {
                "count": len(durations),
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "total": sum(durations)
            }

    return PerformanceTracker()


# ============================================================================
# Pytest Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "offline: marks tests that require offline mode"
    )
    config.addinivalue_line(
        "markers", "network_transition: marks tests for online/offline transitions"
    )
    config.addinivalue_line(
        "markers", "local_llm: marks tests requiring local LLM (Ollama)"
    )
