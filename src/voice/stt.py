"""Speech-to-Text using Whisper."""

from pathlib import Path
from typing import Optional

import numpy as np

from src.core.config import settings


class SpeechToText:
    """
    Speech-to-Text using OpenAI Whisper.

    Runs locally for privacy and offline capability.
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):
        """
        Initialize STT.

        Args:
            model_name: Whisper model (tiny, base, small, medium, large).
            device: Device to run on (cuda, cpu).
        """
        self.model_name = model_name or settings.whisper_model
        self.device = device
        self._model = None

    @property
    def model(self):
        """Lazy load Whisper model."""
        if self._model is None:
            import whisper

            self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model

    def transcribe(
        self,
        audio: np.ndarray | str | Path,
        language: str = "en",
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio: Audio as numpy array or path to audio file.
            language: Language code.

        Returns:
            Dict with 'text' and 'segments'.
        """
        if isinstance(audio, (str, Path)):
            audio = str(audio)

        result = self.model.transcribe(
            audio,
            language=language,
            task="transcribe",
        )

        return {
            "text": result["text"].strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", language),
        }

    def transcribe_with_timestamps(
        self,
        audio: np.ndarray | str | Path,
        language: str = "en",
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
            }
            for seg in result.get("segments", [])
        ]


class WakeWordDetector:
    """
    Wake word detection for "Hey DocAssist".

    Uses OpenWakeWord for local, low-latency detection.
    """

    def __init__(
        self,
        wake_word: str | None = None,
        threshold: float = 0.5,
    ):
        """
        Initialize wake word detector.

        Args:
            wake_word: Wake word to detect.
            threshold: Detection threshold (0-1).
        """
        self.wake_word = wake_word or settings.wake_word
        self.threshold = threshold
        self._detector = None

    @property
    def detector(self):
        """Lazy load wake word detector."""
        if self._detector is None:
            try:
                from openwakeword import Model

                self._detector = Model(
                    wakeword_models=[self.wake_word],
                    inference_framework="onnx",
                )
            except ImportError:
                raise ImportError(
                    "openwakeword not installed. Run: pip install openwakeword"
                )
        return self._detector

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Check if wake word is in audio chunk.

        Args:
            audio_chunk: Audio data (16kHz, mono, float32).

        Returns:
            True if wake word detected.
        """
        prediction = self.detector.predict(audio_chunk)

        # Check if any wake word exceeds threshold
        for key, score in prediction.items():
            if score > self.threshold:
                return True

        return False

    def reset(self):
        """Reset detector state."""
        if self._detector:
            self._detector.reset()
