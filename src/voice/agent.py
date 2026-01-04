"""Voice agent orchestrating STT, query, and TTS."""

import queue
import threading
from typing import Callable, Optional

import numpy as np

from src.core.config import settings
from src.core.pipeline import MedicalQueryPipeline

from .stt import SpeechToText, WakeWordDetector
from .tts import TextToSpeech


class VoiceAgent:
    """
    Voice-first interface for Dora.

    Flow:
    1. Listen for wake word ("Hey DocAssist")
    2. Record user query
    3. Transcribe with Whisper
    4. Query medical knowledge base
    5. Speak response with Chatterbox/Piper
    """

    def __init__(
        self,
        query_pipeline: MedicalQueryPipeline | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        wake_detector: WakeWordDetector | None = None,
        on_wake: Callable[[], None] | None = None,
        on_query: Callable[[str], None] | None = None,
        on_response: Callable[[str], None] | None = None,
    ):
        """
        Initialize voice agent.

        Args:
            query_pipeline: Medical query pipeline.
            stt: Speech-to-text engine.
            tts: Text-to-speech engine.
            wake_detector: Wake word detector.
            on_wake: Callback when wake word detected.
            on_query: Callback when query transcribed.
            on_response: Callback when response ready.
        """
        self.pipeline = query_pipeline or MedicalQueryPipeline(prefer_local_llm=True)
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.wake_detector = wake_detector or WakeWordDetector()

        # Callbacks
        self.on_wake = on_wake
        self.on_query = on_query
        self.on_response = on_response

        # State
        self._running = False
        self._audio_queue: queue.Queue = queue.Queue()

    def start(self):
        """Start the voice agent loop."""
        if self._running:
            return

        self._running = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

    def stop(self):
        """Stop the voice agent."""
        self._running = False

    def _listen_loop(self):
        """Main listening loop."""
        import sounddevice as sd

        sample_rate = 16000
        chunk_duration = 0.5  # seconds
        chunk_size = int(sample_rate * chunk_duration)

        def audio_callback(indata, frames, time, status):
            self._audio_queue.put(indata.copy())

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=chunk_size,
        ):
            while self._running:
                self._process_audio_chunk()

    def _process_audio_chunk(self):
        """Process one audio chunk."""
        try:
            audio_chunk = self._audio_queue.get(timeout=1.0)
        except queue.Empty:
            return

        # Check for wake word
        if self.wake_detector.detect(audio_chunk.flatten()):
            self._handle_wake()

    def _handle_wake(self):
        """Handle wake word detection."""
        if self.on_wake:
            self.on_wake()

        # Record query (with silence detection)
        audio = self._record_query(timeout=10.0)

        if audio is None or len(audio) < 1600:  # Too short
            return

        # Transcribe
        result = self.stt.transcribe(audio)
        query_text = result["text"]

        if not query_text.strip():
            return

        if self.on_query:
            self.on_query(query_text)

        # Query pipeline
        answer = self.pipeline.query_sync(query_text)

        if self.on_response:
            self.on_response(answer.answer)

        # Speak response
        self._speak_response(answer.answer)

        # Reset wake detector
        self.wake_detector.reset()

    def _record_query(
        self,
        timeout: float = 10.0,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
    ) -> np.ndarray | None:
        """
        Record audio until silence detected.

        Args:
            timeout: Maximum recording time.
            silence_threshold: RMS threshold for silence.
            silence_duration: Seconds of silence to stop.

        Returns:
            Recorded audio or None.
        """
        import time

        chunks = []
        silence_start = None
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self._audio_queue.get(timeout=0.5)
                chunks.append(chunk)

                # Check for silence
                rms = np.sqrt(np.mean(chunk**2))
                if rms < silence_threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_duration:
                        break
                else:
                    silence_start = None

            except queue.Empty:
                continue

        if not chunks:
            return None

        return np.concatenate(chunks, axis=0).flatten()

    def _speak_response(self, text: str):
        """Speak the response text."""
        # Truncate very long responses
        if len(text) > 500:
            text = text[:500] + "... For more details, please see the full response on screen."

        self.tts.speak(text)

    def process_text(self, text: str) -> str:
        """
        Process a text query (for testing without voice).

        Args:
            text: Query text.

        Returns:
            Response text.
        """
        answer = self.pipeline.query_sync(text)
        return answer.answer

    def speak(self, text: str):
        """
        Speak arbitrary text.

        Args:
            text: Text to speak.
        """
        self.tts.speak(text)
