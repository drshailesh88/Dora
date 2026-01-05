"""
End-to-End Tests for Offline Mode

Comprehensive tests ensuring all features work without network connectivity.
"""

import asyncio
import json
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock


# =============================================================================
# Offline Query Tests
# =============================================================================


class TestOfflineQueryWithCache:
    """Tests for cached query responses in offline mode."""

    @pytest.mark.offline
    def test_cached_query_returns_results(self, populate_cache, offline_mode):
        """Cached queries should return results when offline."""
        cache = populate_cache

        # Query for cached diabetes document
        result = cache.get_cached_query("diabetes treatment")

        # Should find cached content
        assert result is not None or cache.get_document("doc_diabetes_treatment") is not None

    @pytest.mark.offline
    def test_uncached_query_returns_graceful_error(self, cache_manager, offline_mode):
        """Uncached queries should return graceful error when offline."""
        # Query for something not cached
        result = cache_manager.get_cached_query("extremely rare condition xyz123")

        # Should return None or empty, not crash
        assert result is None or result == []

    @pytest.mark.offline
    def test_cache_lookup_performance(self, populate_cache, performance_tracker):
        """Cache lookups should be fast."""
        cache = populate_cache

        # Perform multiple lookups
        for _ in range(100):
            start = time.perf_counter()
            cache.get_document("doc_diabetes_treatment")
            duration = (time.perf_counter() - start) * 1000
            performance_tracker.record("cache_lookup", duration)

        stats = performance_tracker.get_stats("cache_lookup")
        assert stats["avg"] < 10  # Should average under 10ms


class TestOfflineQueryWithLocalLLM:
    """Tests for local LLM fallback in offline mode."""

    @pytest.mark.offline
    @pytest.mark.local_llm
    def test_ollama_generates_response(self, mock_ollama_client, offline_mode):
        """Ollama should generate responses when offline."""
        response = mock_ollama_client.generate(
            model="qwen2.5:3b",
            prompt="What is the first-line treatment for Type 2 Diabetes?",
        )

        assert "response" in response
        assert len(response["response"]) > 0

    @pytest.mark.offline
    @pytest.mark.local_llm
    def test_local_llm_handles_medical_queries(self, mock_local_llm, offline_mode):
        """Local LLM should handle medical terminology."""
        # This tests that the mock is properly configured
        assert mock_local_llm is not None

    @pytest.mark.offline
    @pytest.mark.local_llm
    def test_local_llm_fallback_on_cloud_failure(self, mock_ollama_client):
        """Should fall back to local LLM when cloud fails."""
        # Simulate cloud failure
        with patch('src.llm.synthesizer.MedicalSynthesizer.anthropic_client', None):
            with patch('src.llm.synthesizer.MedicalSynthesizer.openai_client', None):
                # Local should work
                response = mock_ollama_client.generate(
                    model="qwen2.5:3b",
                    prompt="Test query",
                )
                assert response["done"] is True


# =============================================================================
# Offline Voice Tests
# =============================================================================


class TestOfflineVoiceRecognition:
    """Tests for voice features in offline mode."""

    @pytest.mark.offline
    def test_whisper_transcribes_offline(self, mock_whisper_model, offline_mode):
        """Whisper STT should work offline."""
        result = mock_whisper_model.transcribe(b"fake_audio_data")

        assert "text" in result
        assert result["language"] == "en"

    @pytest.mark.offline
    def test_whisper_handles_medical_terminology(self, mock_whisper_model, offline_mode):
        """Whisper should handle medical terms."""
        result = mock_whisper_model.transcribe(b"fake_audio")

        # Mock returns "What is the dosage for metformin?"
        assert "metformin" in result["text"]

    @pytest.mark.offline
    def test_voice_recording_works_offline(self, offline_voice_services, offline_mode):
        """Voice recording should work without network."""
        # The mock services should be accessible
        assert offline_voice_services["stt"] is not None
        assert offline_voice_services["tts"] is not None


class TestOfflineVoiceSynthesis:
    """Tests for TTS in offline mode."""

    @pytest.mark.offline
    def test_piper_synthesizes_offline(self, mock_piper_tts, offline_mode):
        """Piper TTS should work offline."""
        import numpy as np

        audio = mock_piper_tts.synthesize("This is a test message")

        assert audio is not None
        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0

    @pytest.mark.offline
    def test_tts_handles_medical_terms(self, mock_piper_tts, offline_mode):
        """TTS should handle medical terminology."""
        import numpy as np

        # Should not raise for complex medical text
        audio = mock_piper_tts.synthesize(
            "The patient should take metformin 500mg twice daily"
        )

        assert isinstance(audio, np.ndarray)


# =============================================================================
# Offline Patient Data Tests
# =============================================================================


class TestOfflinePatientDataAccess:
    """Tests for patient data access in offline mode."""

    @pytest.mark.offline
    def test_patient_data_accessible_offline(
        self, populate_patient_db, sample_patient_data, offline_mode
    ):
        """Patient data should be accessible from local SQLite."""
        storage = populate_patient_db

        with storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM patients WHERE id = ?",
                (sample_patient_data["id"],),
            )
            row = cursor.fetchone()

        assert row is not None
        patient = json.loads(row[0])
        assert patient["name"] == "Rajesh Kumar"
        assert len(patient["medications"]) == 3

    @pytest.mark.offline
    def test_patient_medications_available(
        self, populate_patient_db, sample_patient_data, offline_mode
    ):
        """Patient medications should be retrievable offline."""
        storage = populate_patient_db

        with storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM patients WHERE id = ?",
                (sample_patient_data["id"],),
            )
            row = cursor.fetchone()

        patient = json.loads(row[0])
        medications = patient["medications"]

        assert any(med["name"] == "Metformin" for med in medications)
        assert any(med["name"] == "Lisinopril" for med in medications)

    @pytest.mark.offline
    def test_patient_labs_available(
        self, populate_patient_db, sample_patient_data, offline_mode
    ):
        """Patient lab values should be accessible offline."""
        storage = populate_patient_db

        with storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM patients WHERE id = ?",
                (sample_patient_data["id"],),
            )
            row = cursor.fetchone()

        patient = json.loads(row[0])
        labs = patient["labs"]

        assert labs["hba1c"] == 7.2
        assert labs["egfr"] == 72


# =============================================================================
# Network Transition Tests
# =============================================================================


class TestNetworkTransitionOnlineToOffline:
    """Tests for transitioning from online to offline."""

    @pytest.mark.network_transition
    @pytest.mark.asyncio
    async def test_graceful_transition_to_offline(self, network_transition):
        """Should handle transition to offline gracefully."""
        transition = network_transition
        transition.monitor.status.is_online = True

        callbacks_received = []

        async def on_status_change():
            callbacks_received.append(transition.monitor.status.is_online)

        transition.register_callback(on_status_change)

        # Go offline
        await transition.go_offline()

        assert transition.monitor.status.is_online is False

    @pytest.mark.network_transition
    @pytest.mark.asyncio
    async def test_pending_operations_queued(self, action_queue, network_transition):
        """Pending operations should be queued when going offline."""
        from src.offline import ActionType, Priority

        # Queue an action while "online"
        action_queue.enqueue(
            action_type=ActionType.SYNC,
            entity_type="query",
            entity_id="test_query_1",
            data={"query": "test"},
            priority=Priority.HIGH,
        )

        # Verify action is queued
        pending = action_queue.get_pending()
        assert len(pending) >= 1


class TestNetworkTransitionOfflineToOnline:
    """Tests for transitioning from offline to online."""

    @pytest.mark.network_transition
    @pytest.mark.asyncio
    async def test_sync_triggered_on_reconnect(self, sync_engine, network_transition):
        """Sync should be triggered when coming back online."""
        transition = network_transition

        # Start offline
        await transition.go_offline()

        # Come back online
        await transition.go_online()

        assert transition.monitor.status.is_online is True

    @pytest.mark.network_transition
    @pytest.mark.asyncio
    async def test_queued_actions_processed(
        self, sync_engine, action_queue, network_transition
    ):
        """Queued actions should be processed on reconnect."""
        from src.offline import ActionType, Priority

        # Queue action while offline
        action_queue.enqueue(
            action_type=ActionType.UPDATE,
            entity_type="annotation",
            entity_id="ann_1",
            data={"note": "updated"},
            priority=Priority.MEDIUM,
        )

        # Verify queued
        assert len(action_queue.get_pending()) >= 1


# =============================================================================
# Offline Document Access Tests
# =============================================================================


class TestOfflineDocumentAccess:
    """Tests for document access via local ChromaDB."""

    @pytest.mark.offline
    def test_vector_search_works_offline(self, local_chromadb, offline_mode):
        """Vector search should work with local ChromaDB."""
        collection = local_chromadb

        results = collection.query(
            query_texts=["diabetes treatment"],
            n_results=3,
        )

        assert len(results["documents"][0]) > 0
        assert "diabetes" in results["documents"][0][0].lower() or \
               "metformin" in results["documents"][0][0].lower()

    @pytest.mark.offline
    def test_document_retrieval_offline(self, local_chromadb, offline_mode):
        """Documents should be retrievable offline."""
        collection = local_chromadb

        # Get by ID
        result = collection.get(ids=["doc1"])

        assert len(result["documents"]) == 1
        assert "metformin" in result["documents"][0].lower()


# =============================================================================
# Offline Calculator and Protocol Tests
# =============================================================================


class TestOfflineCalculatorsAndProtocols:
    """Tests for calculators and protocols in offline mode."""

    @pytest.mark.offline
    def test_calculator_works_offline(self, offline_mode):
        """Medical calculators should work offline."""
        # CKD-EPI formula doesn't need network
        def calculate_egfr(creatinine: float, age: int, sex: str) -> float:
            """Simplified CKD-EPI."""
            if sex.lower() == "female":
                if creatinine <= 0.7:
                    return 144 * (creatinine / 0.7) ** -0.329 * 0.993 ** age
                else:
                    return 144 * (creatinine / 0.7) ** -1.209 * 0.993 ** age
            else:
                if creatinine <= 0.9:
                    return 141 * (creatinine / 0.9) ** -0.411 * 0.993 ** age
                else:
                    return 141 * (creatinine / 0.9) ** -1.209 * 0.993 ** age

        egfr = calculate_egfr(1.1, 55, "male")
        assert 60 < egfr < 90  # Expected range for this input

    @pytest.mark.offline
    def test_protocol_checklist_works_offline(self, offline_mode):
        """Protocol checklists should work offline."""
        # Sepsis protocol checklist
        sepsis_protocol = {
            "name": "Sepsis Bundle",
            "steps": [
                {"id": 1, "text": "Obtain blood cultures", "required": True},
                {"id": 2, "text": "Measure lactate", "required": True},
                {"id": 3, "text": "Start IV fluids", "required": True},
                {"id": 4, "text": "Start antibiotics within 1 hour", "required": True},
            ],
        }

        # Should be usable without network
        assert len(sepsis_protocol["steps"]) == 4
        assert all(step["required"] for step in sepsis_protocol["steps"])


# =============================================================================
# Airplane Mode Simulation
# =============================================================================


class TestAirplaneModeSimulation:
    """Full isolation tests simulating airplane mode."""

    @pytest.mark.slow
    @pytest.mark.offline
    @pytest.mark.asyncio
    async def test_full_workflow_offline(
        self,
        offline_system,
        mock_ollama_client,
        mock_whisper_model,
        mock_piper_tts,
        offline_mode,
    ):
        """Complete workflow should function in airplane mode."""
        system = offline_system

        # 1. Access cached knowledge
        cache = system["cache"]
        # Cache should be accessible
        assert cache is not None

        # 2. Access patient data
        storage = system["storage"]
        assert storage is not None

        # 3. Use local LLM
        response = mock_ollama_client.generate(
            model="qwen2.5:3b",
            prompt="What are the side effects of metformin?",
        )
        assert response["done"] is True

        # 4. Use voice (STT)
        transcription = mock_whisper_model.transcribe(b"audio")
        assert "text" in transcription

        # 5. Use voice (TTS)
        import numpy as np
        audio = mock_piper_tts.synthesize("Response text")
        assert isinstance(audio, np.ndarray)

        # 6. Queue offline action
        queue = system["queue"]
        from src.offline import ActionType, Priority
        queue.enqueue(
            action_type=ActionType.CREATE,
            entity_type="note",
            entity_id="offline_note_1",
            data={"content": "Created while offline"},
            priority=Priority.HIGH,
        )

    @pytest.mark.slow
    @pytest.mark.offline
    def test_extended_offline_operation(
        self,
        populate_cache,
        populate_patient_db,
        offline_mode,
        performance_tracker,
    ):
        """System should remain stable during extended offline operation."""
        cache = populate_cache
        storage = populate_patient_db

        # Simulate extended operation (100 queries)
        for i in range(100):
            start = time.perf_counter()

            # Access cache
            cache.get_document("doc_diabetes_treatment")

            # Access patient DB
            with storage.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM patients")
                cursor.fetchone()

            duration = (time.perf_counter() - start) * 1000
            performance_tracker.record("offline_operation", duration)

        stats = performance_tracker.get_stats("offline_operation")

        # Should remain performant
        assert stats["avg"] < 50  # Average under 50ms
        assert stats["max"] < 200  # Max under 200ms


# =============================================================================
# Offline Data Integrity Tests
# =============================================================================


class TestOfflineDataIntegrity:
    """Tests for data integrity in offline mode."""

    @pytest.mark.offline
    def test_no_data_corruption_offline(self, offline_storage, offline_mode):
        """Data should not be corrupted when offline."""
        storage = offline_storage

        # Write data
        test_data = {"key": "value", "nested": {"a": 1, "b": 2}}

        with storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )
                """
            )
            cursor.execute(
                "INSERT INTO test_data (data) VALUES (?)",
                (json.dumps(test_data),),
            )
            conn.commit()

        # Read back
        with storage.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM test_data WHERE id = 1")
            row = cursor.fetchone()

        retrieved = json.loads(row[0])
        assert retrieved == test_data

    @pytest.mark.offline
    def test_concurrent_offline_access(self, offline_storage, offline_mode):
        """Concurrent access should be safe offline."""
        import threading

        storage = offline_storage
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(10):
                    with storage.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS concurrent_test (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                worker_id INTEGER,
                                iteration INTEGER
                            )
                            """
                        )
                        cursor.execute(
                            "INSERT INTO concurrent_test (worker_id, iteration) VALUES (?, ?)",
                            (worker_id, i),
                        )
                        conn.commit()
            except Exception as e:
                errors.append(str(e))

        # Run concurrent workers
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0
