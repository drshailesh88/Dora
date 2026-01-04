"""
Tests for voice interface module.
Tests wake word detection, STT, TTS, NLU, and voice commands.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
from io import BytesIO


class TestWakeWordDetection:
    """Tests for 'Hey DocAssist' wake word detection."""

    @pytest.fixture
    def wake_word_detector(self):
        """Create wake word detector instance."""
        from src.voice.wake_word import WakeWordDetector
        return WakeWordDetector()

    @pytest.fixture
    def audio_samples(self):
        """Generate sample audio data."""
        # Generate 1 second of audio at 16kHz
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        return {
            "silence": np.zeros(int(sample_rate * duration), dtype=np.float32),
            "noise": np.random.randn(int(sample_rate * duration)).astype(np.float32) * 0.1,
            "speech": np.sin(2 * np.pi * 440 * t).astype(np.float32),  # Simple tone
        }

    def test_detector_initialization(self, wake_word_detector):
        """Detector should initialize properly."""
        assert wake_word_detector is not None
        assert wake_word_detector.is_ready()

    @pytest.mark.asyncio
    async def test_wake_word_detected(self, wake_word_detector):
        """Should detect wake word 'Hey DocAssist'."""
        # Mock audio containing wake word
        with patch.object(
            wake_word_detector,
            "_process_audio",
            return_value={"detected": True, "confidence": 0.95},
        ):
            audio = np.random.randn(16000).astype(np.float32)
            result = await wake_word_detector.detect(audio)

            assert result["detected"]
            assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_no_false_positive_on_silence(self, wake_word_detector, audio_samples):
        """Should not trigger on silence."""
        result = await wake_word_detector.detect(audio_samples["silence"])

        assert not result["detected"]

    @pytest.mark.asyncio
    async def test_no_false_positive_on_noise(self, wake_word_detector, audio_samples):
        """Should not trigger on random noise."""
        result = await wake_word_detector.detect(audio_samples["noise"])

        assert not result["detected"]

    def test_sensitivity_adjustment(self, wake_word_detector):
        """Should allow sensitivity adjustment."""
        wake_word_detector.set_sensitivity(0.8)  # More sensitive
        assert wake_word_detector.sensitivity == 0.8

        wake_word_detector.set_sensitivity(0.3)  # Less sensitive
        assert wake_word_detector.sensitivity == 0.3


class TestSpeechToText:
    """Tests for speech-to-text transcription."""

    @pytest.fixture
    def stt_engine(self):
        """Create STT engine instance."""
        from src.voice.stt import SpeechToTextEngine
        return SpeechToTextEngine()

    @pytest.fixture
    def sample_audio(self):
        """Sample audio data."""
        sample_rate = 16000
        duration = 3.0
        return np.random.randn(int(sample_rate * duration)).astype(np.float32)

    @pytest.mark.asyncio
    async def test_transcription_returns_text(self, stt_engine, sample_audio):
        """Should return transcribed text."""
        with patch.object(
            stt_engine,
            "_transcribe",
            return_value={"text": "What is the dosage for metformin?", "confidence": 0.92},
        ):
            result = await stt_engine.transcribe(sample_audio)

            assert "text" in result
            assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_medical_terms_recognized(self, stt_engine, sample_audio):
        """Should correctly recognize medical terminology."""
        medical_terms = [
            "metformin",
            "lisinopril",
            "hypertension",
            "tachycardia",
            "pneumonia",
        ]

        with patch.object(
            stt_engine,
            "_transcribe",
            return_value={"text": "Patient has hypertension and tachycardia", "confidence": 0.95},
        ):
            result = await stt_engine.transcribe(sample_audio)

            # Should contain medical terms
            text_lower = result["text"].lower()
            assert any(term in text_lower for term in medical_terms)

    @pytest.mark.asyncio
    async def test_timestamps_provided(self, stt_engine, sample_audio):
        """Should provide word-level timestamps."""
        with patch.object(
            stt_engine,
            "_transcribe",
            return_value={
                "text": "Test transcription",
                "words": [
                    {"word": "Test", "start": 0.0, "end": 0.5},
                    {"word": "transcription", "start": 0.5, "end": 1.2},
                ],
            },
        ):
            result = await stt_engine.transcribe(sample_audio, timestamps=True)

            assert "words" in result
            for word_info in result["words"]:
                assert "start" in word_info
                assert "end" in word_info

    @pytest.mark.asyncio
    async def test_language_detection(self, stt_engine, sample_audio):
        """Should detect language of speech."""
        with patch.object(
            stt_engine,
            "_transcribe",
            return_value={"text": "यह हिंदी में है", "language": "hi", "confidence": 0.88},
        ):
            result = await stt_engine.transcribe(sample_audio, detect_language=True)

            assert "language" in result
            assert result["language"] in ["en", "hi", "ta", "te", "kn", "bn", "mr"]

    @pytest.mark.asyncio
    async def test_streaming_transcription(self, stt_engine):
        """Should support streaming transcription."""
        chunks = [np.random.randn(4000).astype(np.float32) for _ in range(5)]

        results = []
        async for partial in stt_engine.transcribe_stream(chunks):
            results.append(partial)

        # Should get partial results
        assert len(results) >= 1
        # Final result should be complete
        assert results[-1].get("is_final", True)


class TestTextToSpeech:
    """Tests for text-to-speech synthesis."""

    @pytest.fixture
    def tts_engine(self):
        """Create TTS engine instance."""
        from src.voice.tts import TextToSpeechEngine
        return TextToSpeechEngine()

    @pytest.mark.asyncio
    async def test_synthesis_returns_audio(self, tts_engine):
        """Should return synthesized audio."""
        text = "The recommended dosage is 500 milligrams twice daily."

        result = await tts_engine.synthesize(text)

        assert "audio" in result
        assert len(result["audio"]) > 0
        assert result["sample_rate"] in [16000, 22050, 44100, 48000]

    @pytest.mark.asyncio
    async def test_voice_selection(self, tts_engine):
        """Should support different voices."""
        text = "Test message"

        female_result = await tts_engine.synthesize(text, voice="female_1")
        male_result = await tts_engine.synthesize(text, voice="male_1")

        # Audio should be different
        assert not np.array_equal(female_result["audio"], male_result["audio"])

    @pytest.mark.asyncio
    async def test_speech_rate_adjustment(self, tts_engine):
        """Should adjust speech rate."""
        text = "The quick brown fox jumps over the lazy dog."

        normal = await tts_engine.synthesize(text, rate=1.0)
        slow = await tts_engine.synthesize(text, rate=0.7)
        fast = await tts_engine.synthesize(text, rate=1.3)

        # Slower speech = longer audio
        assert len(slow["audio"]) > len(normal["audio"])
        assert len(fast["audio"]) < len(normal["audio"])

    @pytest.mark.asyncio
    async def test_medical_pronunciation(self, tts_engine):
        """Should correctly pronounce medical terms."""
        # Test complex medical terms
        medical_texts = [
            "Prescribe azithromycin 500mg",
            "Patient has pneumothorax",
            "Administer epinephrine immediately",
        ]

        for text in medical_texts:
            result = await tts_engine.synthesize(text)
            assert result["audio"] is not None
            assert len(result["audio"]) > 0

    @pytest.mark.asyncio
    async def test_ssml_support(self, tts_engine):
        """Should support SSML for pronunciation control."""
        ssml = """
        <speak>
            Take <say-as interpret-as="cardinal">500</say-as> milligrams
            <break time="300ms"/>
            twice daily.
        </speak>
        """

        result = await tts_engine.synthesize(ssml, format="ssml")

        assert result["audio"] is not None


class TestNaturalLanguageUnderstanding:
    """Tests for NLU - intent and entity extraction."""

    @pytest.fixture
    def nlu_engine(self):
        """Create NLU engine instance."""
        from src.voice.nlu import NLUEngine
        return NLUEngine()

    @pytest.mark.asyncio
    async def test_intent_classification(self, nlu_engine):
        """Should classify user intent."""
        queries = [
            ("What is the dosage for metformin?", "drug_dosage"),
            ("Show me drug interactions for aspirin", "drug_interaction"),
            ("Calculate BMI for 70kg and 175cm", "calculator"),
            ("What are the symptoms of meningitis?", "symptoms"),
        ]

        for query, expected_intent in queries:
            result = await nlu_engine.parse(query)

            assert "intent" in result
            assert result["intent"]["name"] == expected_intent or \
                   expected_intent in result["intent"]["name"]

    @pytest.mark.asyncio
    async def test_entity_extraction(self, nlu_engine):
        """Should extract medical entities."""
        query = "What is the dosage of metformin 500mg for a 70kg diabetic patient?"

        result = await nlu_engine.parse(query)

        assert "entities" in result
        entity_types = [e["type"] for e in result["entities"]]

        # Should extract drug, dose, weight, condition
        assert "drug" in entity_types or "medication" in entity_types
        assert "dosage" in entity_types or "dose" in entity_types

    @pytest.mark.asyncio
    async def test_context_handling(self, nlu_engine):
        """Should handle contextual queries."""
        # First query establishes context
        await nlu_engine.parse("Tell me about metformin")

        # Follow-up query uses context
        result = await nlu_engine.parse(
            "What are its side effects?",
            context={"last_drug": "metformin"},
        )

        assert "metformin" in result.get("resolved_query", "") or \
               result["entities"][0].get("value") == "metformin"

    @pytest.mark.asyncio
    async def test_multi_intent_handling(self, nlu_engine):
        """Should handle queries with multiple intents."""
        query = "Show me interactions for aspirin and calculate the creatinine clearance"

        result = await nlu_engine.parse(query)

        # Should detect multiple intents
        if isinstance(result["intent"], list):
            assert len(result["intent"]) >= 2
        else:
            assert "multi" in result.get("flags", []) or \
                   result.get("secondary_intent") is not None

    @pytest.mark.asyncio
    async def test_command_parsing(self, nlu_engine):
        """Should parse voice commands."""
        commands = [
            ("open calculator", "open", "calculator"),
            ("search for hypertension guidelines", "search", "hypertension guidelines"),
            ("go back", "navigate", "back"),
            ("read aloud", "accessibility", "read"),
        ]

        for query, expected_action, expected_target in commands:
            result = await nlu_engine.parse(query)

            assert result["intent"]["action"] == expected_action or \
                   expected_action in result["intent"]["name"]


class TestVoiceCommands:
    """Tests for voice command execution."""

    @pytest.fixture
    def voice_controller(self):
        """Create voice controller instance."""
        from src.voice.controller import VoiceController
        return VoiceController()

    @pytest.mark.asyncio
    async def test_query_command_execution(self, voice_controller):
        """Should execute query commands."""
        result = await voice_controller.execute(
            intent="query",
            entities={"drug": "metformin"},
            raw_text="What is metformin?",
        )

        assert result["success"]
        assert "response" in result
        assert result["action_taken"] == "query_executed"

    @pytest.mark.asyncio
    async def test_calculator_command(self, voice_controller):
        """Should execute calculator commands."""
        result = await voice_controller.execute(
            intent="calculator",
            entities={
                "calculator_type": "bmi",
                "weight": 70,
                "height": 175,
            },
            raw_text="Calculate BMI for 70kg and 175cm",
        )

        assert result["success"]
        assert "result" in result
        assert "bmi" in str(result["result"]).lower()

    @pytest.mark.asyncio
    async def test_navigation_command(self, voice_controller):
        """Should handle navigation commands."""
        result = await voice_controller.execute(
            intent="navigate",
            entities={"target": "settings"},
            raw_text="Go to settings",
        )

        assert result["success"]
        assert result["action_taken"] == "navigation"
        assert result["destination"] == "settings"

    @pytest.mark.asyncio
    async def test_dictation_mode(self, voice_controller):
        """Should handle dictation mode."""
        result = await voice_controller.execute(
            intent="dictation",
            entities={},
            raw_text="Start dictation",
        )

        assert result["success"]
        assert result["mode"] == "dictation"

        # Stop dictation
        stop_result = await voice_controller.execute(
            intent="dictation_stop",
            entities={},
            raw_text="Stop dictation",
        )

        assert stop_result["success"]
        assert "dictated_text" in stop_result or stop_result["mode"] == "normal"


class TestAmbientDictation:
    """Tests for ambient (continuous) dictation mode."""

    @pytest.fixture
    def ambient_service(self):
        """Create ambient dictation service."""
        from src.voice.ambient import AmbientDictationService
        return AmbientDictationService()

    @pytest.mark.asyncio
    async def test_continuous_listening(self, ambient_service):
        """Should listen continuously in ambient mode."""
        # Start ambient mode
        await ambient_service.start()
        assert ambient_service.is_listening()

        # Stop ambient mode
        await ambient_service.stop()
        assert not ambient_service.is_listening()

    @pytest.mark.asyncio
    async def test_clinical_note_extraction(self, ambient_service):
        """Should extract clinical notes from conversation."""
        transcript = """
        Doctor: How are you feeling today?
        Patient: I've been having chest pain for the past 3 days.
        Doctor: Can you describe the pain?
        Patient: It's a sharp pain that gets worse when I breathe.
        Doctor: I see. Let me examine you. Your blood pressure is 140 over 90.
        """

        with patch.object(
            ambient_service,
            "process_transcript",
            return_value={
                "chief_complaint": "chest pain for 3 days",
                "hpi": "Sharp chest pain, pleuritic in nature, 3 day duration",
                "vitals": {"bp": "140/90"},
                "plan": [],
            },
        ):
            result = await ambient_service.extract_notes(transcript)

            assert "chief_complaint" in result or "cc" in result
            assert "hpi" in result or "history" in result
            assert "vitals" in result

    @pytest.mark.asyncio
    async def test_speaker_diarization(self, ambient_service):
        """Should distinguish between speakers."""
        audio = np.random.randn(160000).astype(np.float32)  # 10 seconds

        with patch.object(
            ambient_service,
            "process_with_diarization",
            return_value={
                "segments": [
                    {"speaker": "doctor", "text": "How are you?", "start": 0.0, "end": 1.5},
                    {"speaker": "patient", "text": "I have pain.", "start": 1.5, "end": 3.0},
                ]
            },
        ):
            result = await ambient_service.transcribe_with_diarization(audio)

            assert "segments" in result
            speakers = set(s["speaker"] for s in result["segments"])
            assert len(speakers) >= 2


class TestVoiceAccessibility:
    """Tests for voice accessibility features."""

    @pytest.fixture
    def accessibility_service(self):
        """Create accessibility service."""
        from src.voice.accessibility import VoiceAccessibilityService
        return VoiceAccessibilityService()

    @pytest.mark.asyncio
    async def test_screen_reader_mode(self, accessibility_service):
        """Should read screen content aloud."""
        screen_content = {
            "title": "Drug Information: Metformin",
            "sections": [
                {"heading": "Dosage", "content": "500mg twice daily"},
                {"heading": "Warnings", "content": "Monitor renal function"},
            ],
        }

        result = await accessibility_service.read_screen(screen_content)

        assert result["audio"] is not None
        assert result["text_read"] is not None
        assert "metformin" in result["text_read"].lower()

    @pytest.mark.asyncio
    async def test_audio_feedback(self, accessibility_service):
        """Should provide audio feedback for actions."""
        result = await accessibility_service.announce("Search completed. 5 results found.")

        assert result["audio"] is not None
        assert result["announced"]
