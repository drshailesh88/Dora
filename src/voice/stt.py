"""Enhanced Speech-to-Text using Whisper with medical vocabulary and multilingual support."""

import logging
import queue
import threading
from pathlib import Path
from typing import Generator, Literal

import numpy as np
import noisereduce as nr

from src.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Enhanced Speech-to-Text using OpenAI Whisper.

    Features:
    - Medical vocabulary optimization
    - Hindi + English bilingual support
    - Hinglish (code-switched) recognition
    - Real-time streaming transcription
    - Noise cancellation for clinic environments
    - Cloud fallback when offline model struggles
    - < 2s latency for queries
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        language: Literal["en", "hi", "auto"] = "auto",
        enable_noise_reduction: bool = True,
        cloud_fallback: bool = True,
    ):
        """
        Initialize STT.

        Args:
            model_name: Whisper model (tiny, base, small, medium, large).
            device: Device to run on (cuda, cpu).
            language: Language code (en=English, hi=Hindi, auto=detect).
            enable_noise_reduction: Apply noise reduction preprocessing.
            cloud_fallback: Use cloud API if local model fails.
        """
        self.model_name = model_name or settings.whisper_model
        self.device = device
        self.language = language
        self.enable_noise_reduction = enable_noise_reduction
        self.cloud_fallback = cloud_fallback
        self._model = None

        # Medical vocabulary for better recognition
        self.medical_terms = self._load_medical_vocabulary()

        logger.info(
            f"Initializing STT: model={self.model_name}, language={language}, "
            f"noise_reduction={enable_noise_reduction}"
        )

    def _load_medical_vocabulary(self) -> list[str]:
        """Load medical terms for improved recognition."""
        # Common medical terms that need accurate transcription
        terms = [
            # Medications
            "metformin", "aspirin", "atorvastatin", "amlodipine", "omeprazole",
            "paracetamol", "ibuprofen", "amoxicillin", "azithromycin",
            # Conditions
            "diabetes", "hypertension", "pneumonia", "asthma", "tuberculosis",
            "dengue", "malaria", "typhoid", "gastritis", "arthritis",
            # Procedures
            "ecg", "echo", "ultrasound", "x-ray", "ct scan", "mri",
            "endoscopy", "colonoscopy", "biopsy",
            # Measurements
            "blood pressure", "heart rate", "temperature", "oxygen saturation",
            "blood sugar", "hemoglobin", "creatinine", "urea",
        ]
        return terms

    @property
    def model(self):
        """Lazy load Whisper model."""
        if self._model is None:
            import whisper

            self._model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"Whisper model loaded: {self.model_name}")
        return self._model

    def transcribe(
        self,
        audio: np.ndarray | str | Path,
        language: str | None = None,
        initial_prompt: str | None = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio: Audio as numpy array or path to audio file.
            language: Language code (overrides instance default).
            initial_prompt: Context prompt for better accuracy.

        Returns:
            Dict with 'text', 'segments', 'language', 'confidence'.
        """
        # Load audio if path provided
        if isinstance(audio, (str, Path)):
            audio = str(audio)

        # Apply noise reduction for numpy arrays
        if isinstance(audio, np.ndarray) and self.enable_noise_reduction:
            audio = self._reduce_noise(audio)

        # Determine language
        lang = language or self.language
        if lang == "auto":
            lang = None  # Let Whisper detect

        # Build initial prompt with medical context
        if initial_prompt is None and self.medical_terms:
            initial_prompt = f"Medical consultation. Common terms: {', '.join(self.medical_terms[:10])}"

        try:
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio,
                language=lang,
                task="transcribe",
                initial_prompt=initial_prompt,
                word_timestamps=True,
                condition_on_previous_text=True,
            )

            # Calculate confidence score
            confidence = self._calculate_confidence(result)

            return {
                "text": result["text"].strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", lang or "en"),
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Local transcription failed: {e}")

            # Try cloud fallback if enabled
            if self.cloud_fallback and isinstance(audio, str):
                return self._transcribe_cloud(audio, lang)

            raise

    def _reduce_noise(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Apply noise reduction for clinic environments.

        Args:
            audio: Audio signal.
            sample_rate: Sample rate.

        Returns:
            Cleaned audio.
        """
        try:
            # Use noisereduce library
            reduced = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                stationary=False,  # Non-stationary noise (clinic environment)
                prop_decrease=0.8,
            )
            return reduced
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}, using original audio")
            return audio

    def _calculate_confidence(self, result: dict) -> float:
        """
        Calculate overall confidence score from segments.

        Args:
            result: Whisper transcription result.

        Returns:
            Confidence score (0-1).
        """
        segments = result.get("segments", [])
        if not segments:
            return 0.0

        # Average no_speech_prob across segments (inverted)
        confidences = [1.0 - seg.get("no_speech_prob", 0.5) for seg in segments]
        return sum(confidences) / len(confidences)

    def _transcribe_cloud(self, audio_path: str, language: str | None) -> dict:
        """
        Fallback to cloud API (OpenAI Whisper API).

        Args:
            audio_path: Path to audio file.
            language: Language code.

        Returns:
            Transcription result.
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)

            with open(audio_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                )

            logger.info("Cloud transcription successful")

            return {
                "text": result.text.strip(),
                "segments": [],
                "language": language or "en",
                "confidence": 0.9,  # Cloud API doesn't provide confidence
            }

        except Exception as e:
            logger.error(f"Cloud transcription failed: {e}")
            raise

    def transcribe_with_timestamps(
        self,
        audio: np.ndarray | str | Path,
        language: str | None = None,
    ) -> list[dict]:
        """
        Transcribe with word-level timestamps.

        Args:
            audio: Audio input.
            language: Language code.

        Returns:
            List of segments with timestamps.
        """
        result = self.transcribe(audio, language)

        return [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
                "confidence": 1.0 - seg.get("no_speech_prob", 0.5),
            }
            for seg in result.get("segments", [])
        ]

    def transcribe_streaming(
        self,
        audio_stream: queue.Queue,
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
    ) -> Generator[str, None, None]:
        """
        Real-time streaming transcription.

        Args:
            audio_stream: Queue of audio chunks.
            sample_rate: Audio sample rate.
            chunk_duration: Duration of each chunk to transcribe.

        Yields:
            Transcribed text for each chunk.
        """
        buffer = []
        chunk_samples = int(sample_rate * chunk_duration)

        while True:
            try:
                # Get audio chunk from queue
                chunk = audio_stream.get(timeout=1.0)

                if chunk is None:  # Sentinel value to stop
                    break

                buffer.append(chunk)
                current_samples = sum(len(c) for c in buffer)

                # Transcribe when we have enough samples
                if current_samples >= chunk_samples:
                    audio = np.concatenate(buffer)
                    result = self.transcribe(audio[:chunk_samples])

                    if result["text"].strip():
                        yield result["text"]

                    # Keep overlap for context
                    overlap_samples = chunk_samples // 4
                    buffer = [audio[chunk_samples - overlap_samples:]]

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Streaming transcription error: {e}")
                break

    def transcribe_hinglish(
        self,
        audio: np.ndarray | str | Path,
    ) -> dict:
        """
        Transcribe code-switched Hindi-English (Hinglish).

        Args:
            audio: Audio input.

        Returns:
            Transcription result with detected language segments.
        """
        # Use language detection mode
        result = self.transcribe(audio, language=None)

        # Post-process to identify language switches
        # This is a simple heuristic - can be improved with language detection
        segments = result.get("segments", [])

        for seg in segments:
            text = seg.get("text", "")
            # Simple heuristic: if contains Devanagari script, mark as Hindi
            if any("\u0900" <= char <= "\u097F" for char in text):
                seg["detected_language"] = "hi"
            else:
                seg["detected_language"] = "en"

        return result


class AudioRecorder:
    """
    Audio recorder with Voice Activity Detection (VAD).

    Features:
    - Automatic silence detection
    - Background noise suppression
    - Configurable recording duration
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
    ):
        """
        Initialize audio recorder.

        Args:
            sample_rate: Sample rate (Hz).
            channels: Number of channels.
            silence_threshold: RMS threshold for silence detection.
            silence_duration: Seconds of silence to stop recording.
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

    def record_until_silence(
        self,
        max_duration: float = 30.0,
        start_on_speech: bool = True,
    ) -> np.ndarray | None:
        """
        Record audio until silence detected.

        Args:
            max_duration: Maximum recording duration (seconds).
            start_on_speech: Wait for speech before starting.

        Returns:
            Recorded audio or None.
        """
        import time

        import sounddevice as sd

        chunks = []
        silence_start = None
        recording_started = False
        start_time = time.time()

        def callback(indata, frames, time_info, status):
            nonlocal silence_start, recording_started

            if status:
                logger.warning(f"Recording status: {status}")

            # Calculate RMS
            rms = np.sqrt(np.mean(indata**2))

            # Wait for speech to start if required
            if start_on_speech and not recording_started:
                if rms > self.silence_threshold:
                    recording_started = True
                    logger.info("Speech detected, recording started")
                else:
                    return

            # Add chunk if recording
            if recording_started or not start_on_speech:
                chunks.append(indata.copy())

                # Check for silence
                if rms < self.silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                else:
                    silence_start = None

        # Start recording stream
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            callback=callback,
        ):
            while time.time() - start_time < max_duration:
                # Stop if silence detected for long enough
                if (
                    silence_start is not None
                    and time.time() - silence_start > self.silence_duration
                ):
                    logger.info("Silence detected, stopping recording")
                    break

                time.sleep(0.1)

        if not chunks:
            return None

        return np.concatenate(chunks, axis=0).flatten()
