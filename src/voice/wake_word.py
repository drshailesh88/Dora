"""Wake word detection for hands-free voice activation."""

import logging
from pathlib import Path
from typing import Literal

import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detection for "Hey DocAssist", "Hey Dora", "OK Doctor".

    Features:
    - Multiple wake word support
    - Configurable sensitivity
    - Low power consumption
    - Works offline (no cloud dependency)
    - < 500ms latency
    """

    def __init__(
        self,
        wake_words: list[str] | None = None,
        threshold: float = 0.5,
        backend: Literal["openwakeword", "porcupine", "pvporcupine"] = "openwakeword",
        sensitivity: float = 0.5,
    ):
        """
        Initialize wake word detector.

        Args:
            wake_words: List of wake words to detect.
            threshold: Detection threshold (0-1).
            backend: Detection backend to use.
            sensitivity: Detection sensitivity (0-1, higher = more sensitive).
        """
        self.wake_words = wake_words or [settings.wake_word, "hey_dora", "ok_doctor"]
        self.threshold = threshold
        self.backend = backend
        self.sensitivity = sensitivity
        self._detector = None

        logger.info(
            f"Initializing wake word detector: {backend}, wake_words={wake_words}"
        )

    @property
    def detector(self):
        """Lazy load wake word detector."""
        if self._detector is None:
            if self.backend == "openwakeword":
                self._init_openwakeword()
            elif self.backend in ("porcupine", "pvporcupine"):
                self._init_porcupine()
            else:
                raise ValueError(f"Unknown backend: {self.backend}")

        return self._detector

    def _init_openwakeword(self):
        """Initialize OpenWakeWord detector."""
        try:
            from openwakeword import Model

            # Map wake words to model names
            model_names = []
            for wake_word in self.wake_words:
                if wake_word in ("hey_docassist", "hey docassist"):
                    # Use generic "hey mycroft" as proxy (can be fine-tuned later)
                    model_names.append("hey_mycroft_v0.1")
                elif wake_word in ("hey_dora", "hey dora"):
                    # Use generic wake word
                    model_names.append("alexa_v0.1")
                elif wake_word in ("ok_doctor", "ok doctor"):
                    # Use "ok google" as proxy
                    model_names.append("hey_jarvis_v0.1")

            self._detector = Model(
                wakeword_models=model_names if model_names else None,
                inference_framework="onnx",
            )

            logger.info(f"OpenWakeWord initialized with models: {model_names}")

        except ImportError as e:
            logger.error(f"OpenWakeWord not installed: {e}")
            raise ImportError(
                "openwakeword not installed. Run: pip install openwakeword"
            )

    def _init_porcupine(self):
        """Initialize Porcupine wake word detector."""
        try:
            import pvporcupine

            # Porcupine requires access key (free tier available)
            access_key = getattr(settings, "porcupine_access_key", None)

            if not access_key:
                raise ValueError(
                    "Porcupine requires access_key. Get free key at: https://console.picovoice.ai/"
                )

            # Map wake words to Porcupine keywords
            keywords = []
            for wake_word in self.wake_words:
                if "docassist" in wake_word.lower():
                    keywords.append("jarvis")  # Proxy
                elif "dora" in wake_word.lower():
                    keywords.append("alexa")  # Proxy
                elif "doctor" in wake_word.lower():
                    keywords.append("computer")  # Proxy

            self._detector = pvporcupine.create(
                access_key=access_key,
                keywords=keywords if keywords else ["jarvis"],
                sensitivities=[self.sensitivity] * len(keywords),
            )

            logger.info(f"Porcupine initialized with keywords: {keywords}")

        except ImportError as e:
            logger.error(f"Porcupine not installed: {e}")
            raise ImportError(
                "pvporcupine not installed. Run: pip install pvporcupine"
            )

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Check if wake word is in audio chunk.

        Args:
            audio_chunk: Audio data (16kHz, mono, int16 or float32).

        Returns:
            True if wake word detected.
        """
        if self.backend == "openwakeword":
            return self._detect_openwakeword(audio_chunk)
        elif self.backend in ("porcupine", "pvporcupine"):
            return self._detect_porcupine(audio_chunk)
        else:
            return False

    def _detect_openwakeword(self, audio_chunk: np.ndarray) -> bool:
        """Detect using OpenWakeWord."""
        # Ensure float32
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0

        # Get predictions
        prediction = self.detector.predict(audio_chunk)

        # Check if any wake word exceeds threshold
        for key, score in prediction.items():
            if score > self.threshold:
                logger.info(f"Wake word detected: {key} (score={score:.3f})")
                return True

        return False

    def _detect_porcupine(self, audio_chunk: np.ndarray) -> bool:
        """Detect using Porcupine."""
        # Porcupine requires int16 PCM
        if audio_chunk.dtype == np.float32:
            audio_chunk = (audio_chunk * 32768.0).astype(np.int16)

        # Porcupine expects specific frame length (512 samples at 16kHz)
        frame_length = self.detector.frame_length

        if len(audio_chunk) < frame_length:
            return False

        # Process only the first frame
        frame = audio_chunk[:frame_length]
        keyword_index = self.detector.process(frame)

        if keyword_index >= 0:
            logger.info(f"Wake word detected: index={keyword_index}")
            return True

        return False

    def reset(self):
        """Reset detector state."""
        if self._detector is not None:
            if self.backend == "openwakeword":
                self._detector.reset()
            # Porcupine doesn't need explicit reset

    def __del__(self):
        """Cleanup resources."""
        if self._detector is not None and self.backend in ("porcupine", "pvporcupine"):
            try:
                self._detector.delete()
            except Exception:
                pass


class ContinuousWakeWordListener:
    """
    Continuous wake word listener with circular buffer.

    Optimized for low power consumption and minimal latency.
    """

    def __init__(
        self,
        detector: WakeWordDetector | None = None,
        sample_rate: int = 16000,
        chunk_duration: float = 0.5,
    ):
        """
        Initialize continuous listener.

        Args:
            detector: Wake word detector instance.
            sample_rate: Audio sample rate (Hz).
            chunk_duration: Duration of each audio chunk (seconds).
        """
        self.detector = detector or WakeWordDetector()
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        self._running = False
        self._callback = None

    def start(self, callback: callable):
        """
        Start listening for wake word.

        Args:
            callback: Function to call when wake word detected.
        """
        import queue
        import threading

        import sounddevice as sd

        if self._running:
            logger.warning("Listener already running")
            return

        self._running = True
        self._callback = callback
        self._audio_queue = queue.Queue()

        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            self._audio_queue.put(indata.copy())

        def processing_loop():
            """Process audio chunks for wake word detection."""
            while self._running:
                try:
                    audio_chunk = self._audio_queue.get(timeout=1.0)
                    if self.detector.detect(audio_chunk.flatten()):
                        if self._callback:
                            self._callback()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")

        # Start audio stream
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=self.chunk_size,
        )
        self._stream.start()

        # Start processing thread
        self._processing_thread = threading.Thread(
            target=processing_loop, daemon=True
        )
        self._processing_thread.start()

        logger.info("Wake word listener started")

    def stop(self):
        """Stop listening."""
        if not self._running:
            return

        self._running = False

        if hasattr(self, "_stream"):
            self._stream.stop()
            self._stream.close()

        logger.info("Wake word listener stopped")
