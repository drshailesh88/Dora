"""
Audio Synthesizer for Podcast Generation

Converts podcast scripts to audio using Piper TTS.
Supports multiple voices for dialogue and seamless concatenation.
"""

import asyncio
import io
import logging
import struct
import tempfile
import wave
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Optional

import numpy as np
from pydantic import BaseModel, Field

from .podcast_generator import DialogueLine, PodcastScript, Speaker

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """Supported audio output formats."""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass
class SynthesisResult:
    """Result of audio synthesis."""

    audio_data: bytes
    format: AudioFormat
    duration_seconds: float
    sample_rate: int
    channels: int
    metadata: dict = field(default_factory=dict)

    @property
    def size_mb(self) -> float:
        """Audio size in megabytes."""
        return len(self.audio_data) / (1024 * 1024)


class VoiceConfig(BaseModel):
    """Configuration for a TTS voice."""

    voice_id: str = Field(..., description="Piper voice ID")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speaking speed multiplier")
    pitch: float = Field(1.0, ge=0.5, le=2.0, description="Pitch adjustment")
    volume: float = Field(1.0, ge=0.0, le=1.0, description="Volume level")


class AudioSynthesizer:
    """
    Synthesize audio from podcast scripts using Piper TTS.

    Supports:
    - Multiple voices for different speakers
    - Configurable speed, pitch, volume
    - Seamless audio concatenation
    - Streaming synthesis
    """

    # Default voice mappings
    DEFAULT_VOICES = {
        "en_female_1": "en_US-amy-medium",
        "en_male_1": "en_US-ryan-medium",
        "en_female_2": "en_US-lessac-medium",
        "en_male_2": "en_US-arctic-medium",
    }

    # Pause durations in seconds
    PAUSE_BETWEEN_SPEAKERS = 0.3
    PAUSE_SENTENCE_END = 0.2
    PAUSE_PARAGRAPH = 0.5

    def __init__(
        self,
        piper_model_path: Optional[str] = None,
        sample_rate: int = 22050,
        output_format: AudioFormat = AudioFormat.WAV,
    ):
        """
        Initialize audio synthesizer.

        Args:
            piper_model_path: Path to Piper model directory
            sample_rate: Audio sample rate
            output_format: Output audio format
        """
        self.piper_model_path = piper_model_path
        self.sample_rate = sample_rate
        self.output_format = output_format
        self._piper_model = None
        self._voice_configs: dict[str, VoiceConfig] = {}

        logger.info(
            f"Initialized AudioSynthesizer (sample_rate={sample_rate}, format={output_format})"
        )

    def _get_piper(self):
        """Lazy load Piper TTS model."""
        if self._piper_model is None:
            try:
                from piper import PiperVoice

                # Load default voice
                model_path = self.piper_model_path or self._get_default_model_path()
                self._piper_model = PiperVoice.load(model_path)
                logger.info(f"Loaded Piper model from {model_path}")
            except ImportError:
                logger.warning("Piper not installed, using fallback synthesis")
                self._piper_model = None
            except Exception as e:
                logger.error(f"Failed to load Piper model: {e}")
                self._piper_model = None

        return self._piper_model

    def _get_default_model_path(self) -> str:
        """Get default Piper model path."""
        # Check common locations
        possible_paths = [
            Path.home() / ".local/share/piper/en_US-amy-medium.onnx",
            Path("/usr/share/piper/voices/en_US-amy-medium.onnx"),
            Path("models/piper/en_US-amy-medium.onnx"),
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return str(possible_paths[0])  # Return first even if not exists

    def configure_voice(self, voice_id: str, config: VoiceConfig) -> None:
        """
        Configure settings for a specific voice.

        Args:
            voice_id: Voice identifier
            config: Voice configuration
        """
        self._voice_configs[voice_id] = config
        logger.debug(f"Configured voice {voice_id}: {config}")

    async def synthesize_script(
        self,
        script: PodcastScript,
        progress_callback: Optional[callable] = None,
    ) -> SynthesisResult:
        """
        Synthesize a complete podcast script to audio.

        Args:
            script: Podcast script to synthesize
            progress_callback: Optional callback(current, total) for progress

        Returns:
            SynthesisResult with audio data
        """
        logger.info(f"Synthesizing script: {script.title} ({len(script.dialogue)} lines)")

        audio_segments = []
        total_lines = len(script.dialogue)

        for i, line in enumerate(script.dialogue):
            # Synthesize line
            segment = await self._synthesize_line(line, script.speakers)
            audio_segments.append(segment)

            # Add pause between speakers
            if i < total_lines - 1:
                next_speaker = script.dialogue[i + 1].speaker
                if next_speaker != line.speaker:
                    pause = self._generate_silence(self.PAUSE_BETWEEN_SPEAKERS)
                    audio_segments.append(pause)

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_lines)

        # Concatenate all segments
        final_audio = self._concatenate_audio(audio_segments)

        # Convert to output format
        audio_bytes = self._encode_audio(final_audio)

        duration = len(final_audio) / self.sample_rate

        return SynthesisResult(
            audio_data=audio_bytes,
            format=self.output_format,
            duration_seconds=duration,
            sample_rate=self.sample_rate,
            channels=1,
            metadata={
                "title": script.title,
                "lines": total_lines,
                "speakers": [s.name for s in script.speakers],
            },
        )

    async def synthesize_streaming(
        self,
        script: PodcastScript,
        chunk_lines: int = 5,
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized audio in chunks.

        Args:
            script: Podcast script to synthesize
            chunk_lines: Number of lines per chunk

        Yields:
            Audio data chunks
        """
        logger.info(f"Streaming synthesis for: {script.title}")

        current_chunk = []

        for i, line in enumerate(script.dialogue):
            segment = await self._synthesize_line(line, script.speakers)
            current_chunk.append(segment)

            # Add speaker pause
            if i < len(script.dialogue) - 1:
                next_speaker = script.dialogue[i + 1].speaker
                if next_speaker != line.speaker:
                    pause = self._generate_silence(self.PAUSE_BETWEEN_SPEAKERS)
                    current_chunk.append(pause)

            # Yield chunk
            if len(current_chunk) >= chunk_lines:
                chunk_audio = self._concatenate_audio(current_chunk)
                yield self._encode_audio(chunk_audio)
                current_chunk = []

        # Yield remaining
        if current_chunk:
            chunk_audio = self._concatenate_audio(current_chunk)
            yield self._encode_audio(chunk_audio)

    async def _synthesize_line(
        self,
        line: DialogueLine,
        speakers: list[Speaker],
    ) -> np.ndarray:
        """
        Synthesize a single dialogue line.

        Args:
            line: Dialogue line to synthesize
            speakers: List of speakers for voice mapping

        Returns:
            Audio samples as numpy array
        """
        # Find speaker's voice
        speaker = next((s for s in speakers if s.name == line.speaker), None)
        voice_id = speaker.voice_id if speaker else "en_female_1"

        # Get voice config
        config = self._voice_configs.get(voice_id, VoiceConfig(voice_id=voice_id))

        # Synthesize with Piper or fallback
        piper = self._get_piper()
        if piper:
            try:
                audio = await self._synthesize_with_piper(line.text, config)
            except Exception as e:
                logger.error(f"Piper synthesis failed: {e}")
                audio = self._synthesize_fallback(line.text)
        else:
            audio = self._synthesize_fallback(line.text)

        return audio

    async def _synthesize_with_piper(
        self,
        text: str,
        config: VoiceConfig,
    ) -> np.ndarray:
        """Synthesize using Piper TTS."""
        piper = self._get_piper()

        # Run in thread pool for async
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None,
            lambda: self._piper_synthesize_sync(text, config),
        )

        return audio

    def _piper_synthesize_sync(self, text: str, config: VoiceConfig) -> np.ndarray:
        """Synchronous Piper synthesis."""
        piper = self._get_piper()

        # Create audio buffer
        audio_buffer = io.BytesIO()

        # Synthesize
        with wave.open(audio_buffer, "wb") as wav_file:
            piper.synthesize(text, wav_file)

        # Read back as numpy array
        audio_buffer.seek(0)
        with wave.open(audio_buffer, "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        # Apply speed adjustment
        if config.speed != 1.0:
            audio = self._adjust_speed(audio, config.speed)

        # Apply volume
        audio = audio * config.volume

        return audio

    def _synthesize_fallback(self, text: str) -> np.ndarray:
        """
        Fallback synthesis when Piper is not available.

        Generates silence with duration based on text length.
        """
        # Estimate duration: ~150 words per minute
        words = len(text.split())
        duration = (words / 150) * 60  # seconds

        return self._generate_silence(duration)

    def _generate_silence(self, duration: float) -> np.ndarray:
        """Generate silence of specified duration."""
        samples = int(duration * self.sample_rate)
        return np.zeros(samples, dtype=np.float32)

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Adjust audio playback speed using resampling."""
        if speed == 1.0:
            return audio

        # Simple resampling for speed adjustment
        new_length = int(len(audio) / speed)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    def _concatenate_audio(self, segments: list[np.ndarray]) -> np.ndarray:
        """Concatenate audio segments."""
        if not segments:
            return np.array([], dtype=np.float32)

        return np.concatenate(segments)

    def _encode_audio(self, audio: np.ndarray) -> bytes:
        """Encode audio to output format."""
        if self.output_format == AudioFormat.WAV:
            return self._encode_wav(audio)
        elif self.output_format == AudioFormat.MP3:
            return self._encode_mp3(audio)
        elif self.output_format == AudioFormat.OGG:
            return self._encode_ogg(audio)
        else:
            return self._encode_wav(audio)

    def _encode_wav(self, audio: np.ndarray) -> bytes:
        """Encode audio to WAV format."""
        buffer = io.BytesIO()

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return buffer.getvalue()

    def _encode_mp3(self, audio: np.ndarray) -> bytes:
        """Encode audio to MP3 format."""
        try:
            from pydub import AudioSegment

            # Convert to WAV first
            wav_bytes = self._encode_wav(audio)

            # Convert to MP3
            wav_segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
            mp3_buffer = io.BytesIO()
            wav_segment.export(mp3_buffer, format="mp3", bitrate="128k")

            return mp3_buffer.getvalue()

        except ImportError:
            logger.warning("pydub not available, returning WAV instead of MP3")
            return self._encode_wav(audio)

    def _encode_ogg(self, audio: np.ndarray) -> bytes:
        """Encode audio to OGG format."""
        try:
            from pydub import AudioSegment

            wav_bytes = self._encode_wav(audio)
            wav_segment = AudioSegment.from_wav(io.BytesIO(wav_bytes))
            ogg_buffer = io.BytesIO()
            wav_segment.export(ogg_buffer, format="ogg")

            return ogg_buffer.getvalue()

        except ImportError:
            logger.warning("pydub not available, returning WAV instead of OGG")
            return self._encode_wav(audio)

    async def get_duration_estimate(self, script: PodcastScript) -> float:
        """
        Estimate audio duration without full synthesis.

        Args:
            script: Podcast script

        Returns:
            Estimated duration in seconds
        """
        total_words = sum(len(line.text.split()) for line in script.dialogue)
        speaking_time = (total_words / 150) * 60  # 150 words per minute

        # Add pauses
        speaker_changes = sum(
            1
            for i in range(len(script.dialogue) - 1)
            if script.dialogue[i].speaker != script.dialogue[i + 1].speaker
        )
        pause_time = speaker_changes * self.PAUSE_BETWEEN_SPEAKERS

        return speaking_time + pause_time
