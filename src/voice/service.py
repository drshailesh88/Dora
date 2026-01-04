"""Voice service orchestration - full pipeline from wake word to response."""

import logging
import queue
import threading
from typing import Callable, Literal

import numpy as np

from src.core.pipeline import MedicalQueryPipeline

from .ambient import AmbientDictation
from .commands import VoiceCommandHandler
from .conversation import ConfirmationManager, ConversationManager
from .nlu import NaturalLanguageUnderstanding
from .stt import AudioRecorder, SpeechToText
from .tts import TextToSpeech
from .wake_word import WakeWordDetector

logger = logging.getLogger(__name__)


class VoiceServiceMode:
    """Voice service operating modes."""

    WAKE_WORD = "wake_word"  # Wait for wake word, then process single query
    PUSH_TO_TALK = "push_to_talk"  # Process when button pressed
    CONTINUOUS = "continuous"  # Always listening (ambient mode)


class VoiceService:
    """
    Complete voice service orchestrating all voice components.

    Pipeline:
    1. Wake word detection (optional)
    2. STT (Speech-to-Text)
    3. NLU (Natural Language Understanding)
    4. Command execution
    5. TTS (Text-to-Speech) response

    Features:
    - Multiple operating modes (wake word, push-to-talk, continuous)
    - Streaming responses
    - Offline fallback
    - Error recovery
    - Context persistence
    - Confirmation for critical actions
    """

    def __init__(
        self,
        mode: str = VoiceServiceMode.WAKE_WORD,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        wake_detector: WakeWordDetector | None = None,
        query_pipeline: MedicalQueryPipeline | None = None,
        enable_ambient: bool = False,
    ):
        """
        Initialize voice service.

        Args:
            mode: Operating mode (wake_word, push_to_talk, continuous).
            stt: Speech-to-text engine.
            tts: Text-to-speech engine.
            wake_detector: Wake word detector.
            query_pipeline: Medical query pipeline.
            enable_ambient: Enable ambient dictation mode.
        """
        self.mode = mode
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.wake_detector = wake_detector or WakeWordDetector()
        self.query_pipeline = query_pipeline

        # NLU and conversation management
        self.nlu = NaturalLanguageUnderstanding()
        self.conversation_manager = ConversationManager()
        self.confirmation_manager = ConfirmationManager()

        # Command handler
        self.command_handler = VoiceCommandHandler(
            query_pipeline=query_pipeline,
        )

        # Ambient dictation (optional)
        self.ambient = AmbientDictation(stt=self.stt) if enable_ambient else None

        # State
        self._running = False
        self._current_conversation = None
        self._audio_queue = queue.Queue()
        self._awaiting_confirmation = None

        # Callbacks
        self._callbacks: dict[str, Callable] = {}

        logger.info(f"Voice service initialized in {mode} mode")

    def start(
        self,
        on_wake: Callable[[], None] | None = None,
        on_listening: Callable[[], None] | None = None,
        on_transcription: Callable[[str], None] | None = None,
        on_response: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """
        Start the voice service.

        Args:
            on_wake: Callback when wake word detected.
            on_listening: Callback when listening for input.
            on_transcription: Callback when transcription available.
            on_response: Callback when response ready.
            on_error: Callback on error.
        """
        if self._running:
            logger.warning("Voice service already running")
            return

        self._running = True

        # Set callbacks
        if on_wake:
            self._callbacks["on_wake"] = on_wake
        if on_listening:
            self._callbacks["on_listening"] = on_listening
        if on_transcription:
            self._callbacks["on_transcription"] = on_transcription
        if on_response:
            self._callbacks["on_response"] = on_response
        if on_error:
            self._callbacks["on_error"] = on_error

        # Start conversation
        self._current_conversation = self.conversation_manager.start_conversation()

        # Start mode-specific processing
        if self.mode == VoiceServiceMode.WAKE_WORD:
            self._start_wake_word_mode()
        elif self.mode == VoiceServiceMode.CONTINUOUS:
            self._start_continuous_mode()
        # PUSH_TO_TALK mode waits for explicit process_audio() calls

        logger.info("Voice service started")

    def stop(self):
        """Stop the voice service."""
        if not self._running:
            return

        self._running = False

        # Stop ambient dictation if running
        if self.ambient and hasattr(self.ambient, "_running") and self.ambient._running:
            soap_note = self.ambient.stop()
            logger.info(f"Ambient dictation stopped, SOAP note generated")

        logger.info("Voice service stopped")

    def _start_wake_word_mode(self):
        """Start wake word listening mode."""
        import sounddevice as sd

        def on_wake_detected():
            """Handle wake word detection."""
            logger.info("Wake word detected")

            if "on_wake" in self._callbacks:
                self._callbacks["on_wake"]()

            # Start listening for query
            if "on_listening" in self._callbacks:
                self._callbacks["on_listening"]()

            # Record audio until silence
            recorder = AudioRecorder()
            audio = recorder.record_until_silence(max_duration=30.0)

            if audio is not None:
                self._process_audio(audio)

        # Start wake word listener
        threading.Thread(
            target=self._wake_word_loop,
            args=(on_wake_detected,),
            daemon=True,
        ).start()

    def _wake_word_loop(self, on_wake_detected: Callable):
        """Continuous wake word detection loop."""
        import sounddevice as sd

        sample_rate = 16000
        chunk_duration = 0.5
        chunk_size = int(sample_rate * chunk_duration)

        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            self._audio_queue.put(indata.copy())

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=chunk_size,
        ):
            while self._running:
                try:
                    audio_chunk = self._audio_queue.get(timeout=1.0)

                    if self.wake_detector.detect(audio_chunk.flatten()):
                        on_wake_detected()
                        # Reset detector
                        self.wake_detector.reset()

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Wake word loop error: {e}")

    def _start_continuous_mode(self):
        """Start continuous ambient dictation mode."""
        if not self.ambient:
            logger.error("Ambient dictation not enabled")
            return

        def on_segment(segment):
            """Handle transcribed segment."""
            if "on_transcription" in self._callbacks:
                self._callbacks["on_transcription"](segment.text)

        self.ambient.start(on_segment=on_segment)

    def process_audio(self, audio: np.ndarray) -> str:
        """
        Process audio input (for push-to-talk mode or API).

        Args:
            audio: Audio data.

        Returns:
            Response text.
        """
        return self._process_audio(audio)

    def _process_audio(self, audio: np.ndarray) -> str:
        """
        Process audio through full pipeline.

        Args:
            audio: Audio data.

        Returns:
            Response text.
        """
        try:
            # Step 1: Transcribe
            logger.info("Transcribing audio...")
            transcription_result = self.stt.transcribe(audio)
            transcription_text = transcription_result["text"]

            if not transcription_text.strip():
                return self._handle_empty_transcription()

            logger.info(f"Transcription: {transcription_text}")

            if "on_transcription" in self._callbacks:
                self._callbacks["on_transcription"](transcription_text)

            # Step 2: Understand intent
            logger.info("Understanding intent...")
            nlu_result = self.nlu.understand(
                transcription_text,
                context=self._current_conversation.context if self._current_conversation else None,
            )

            logger.info(f"Intent: {nlu_result['intent']}, Confidence: {nlu_result['confidence']:.2f}")

            # Step 3: Check if clarification needed
            needs_clarification, clarification = self.nlu.needs_clarification(nlu_result)

            if needs_clarification:
                response = clarification
                success = False
            else:
                # Step 4: Execute command
                logger.info("Executing command...")
                command_result = self.command_handler.execute(
                    nlu_result,
                    context=self._current_conversation.context if self._current_conversation else None,
                )

                response = command_result.response
                success = command_result.success

                # Handle confirmation if needed
                if command_result.requires_confirmation:
                    self._awaiting_confirmation = {
                        "command_result": command_result,
                        "nlu_result": nlu_result,
                    }

            # Step 5: Add to conversation
            if self._current_conversation:
                self.conversation_manager.add_turn(
                    conversation_id=self._current_conversation.conversation_id,
                    user_input=transcription_text,
                    nlu_result=nlu_result,
                    system_response=response,
                    success=success,
                )

            # Step 6: Speak response
            logger.info(f"Response: {response}")

            if "on_response" in self._callbacks:
                self._callbacks["on_response"](response)

            self.tts.speak(response)

            return response

        except Exception as e:
            logger.error(f"Error processing audio: {e}")

            error_message = "I encountered an error processing your request."

            if "on_error" in self._callbacks:
                self._callbacks["on_error"](str(e))

            self.tts.speak(error_message)

            return error_message

    def process_text(self, text: str) -> str:
        """
        Process text input (for testing or text interface).

        Args:
            text: Input text.

        Returns:
            Response text.
        """
        try:
            # Skip STT, go directly to NLU
            nlu_result = self.nlu.understand(
                text,
                context=self._current_conversation.context if self._current_conversation else None,
            )

            # Execute command
            command_result = self.command_handler.execute(
                nlu_result,
                context=self._current_conversation.context if self._current_conversation else None,
            )

            response = command_result.response

            # Add to conversation
            if self._current_conversation:
                self.conversation_manager.add_turn(
                    conversation_id=self._current_conversation.conversation_id,
                    user_input=text,
                    nlu_result=nlu_result,
                    system_response=response,
                    success=command_result.success,
                )

            return response

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return f"Error: {str(e)}"

    def _handle_empty_transcription(self) -> str:
        """Handle case when transcription is empty."""
        response = "I didn't catch that. Could you repeat?"
        self.tts.speak(response)
        return response

    def set_mode(self, mode: str):
        """
        Change operating mode.

        Args:
            mode: New mode (wake_word, push_to_talk, continuous).
        """
        was_running = self._running

        if was_running:
            self.stop()

        self.mode = mode
        logger.info(f"Voice service mode changed to: {mode}")

        if was_running:
            self.start()

    def get_status(self) -> dict:
        """
        Get voice service status.

        Returns:
            Status dictionary.
        """
        return {
            "running": self._running,
            "mode": self.mode,
            "active_conversations": self.conversation_manager.get_active_count(),
            "current_conversation_id": (
                self._current_conversation.conversation_id
                if self._current_conversation
                else None
            ),
            "awaiting_confirmation": self._awaiting_confirmation is not None,
        }

    def start_ambient_dictation(self):
        """Start ambient dictation mode."""
        if not self.ambient:
            logger.error("Ambient dictation not enabled")
            return

        if self.ambient._running:
            logger.warning("Ambient dictation already running")
            return

        self.ambient.start()
        logger.info("Ambient dictation started")

    def stop_ambient_dictation(self) -> dict:
        """
        Stop ambient dictation and get SOAP note.

        Returns:
            SOAP note as dictionary.
        """
        if not self.ambient or not self.ambient._running:
            logger.warning("Ambient dictation not running")
            return {}

        soap_note = self.ambient.stop()

        return {
            "subjective": soap_note.subjective,
            "objective": soap_note.objective,
            "assessment": soap_note.assessment,
            "plan": soap_note.plan,
            "text": soap_note.to_text(),
        }
