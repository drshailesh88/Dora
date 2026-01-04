"""Text-to-Speech using Chatterbox or Piper."""

from pathlib import Path
from typing import Optional, Literal

import numpy as np


class TextToSpeech:
    """
    Text-to-Speech with multiple backend options.

    Backends:
    - chatterbox: High-quality, needs GPU (recommended)
    - piper: Fast, runs on CPU (fallback)
    """

    def __init__(
        self,
        backend: Literal["chatterbox", "piper", "auto"] = "auto",
        voice_reference: str | Path | None = None,
    ):
        """
        Initialize TTS.

        Args:
            backend: TTS backend to use.
            voice_reference: Path to voice sample for cloning (chatterbox).
        """
        self.backend = backend
        self.voice_reference = voice_reference
        self._engine = None
        self._actual_backend = None

    def _init_engine(self):
        """Initialize the TTS engine."""
        if self._engine is not None:
            return

        if self.backend == "auto":
            # Try chatterbox first, fall back to piper
            try:
                self._init_chatterbox()
                self._actual_backend = "chatterbox"
                return
            except (ImportError, Exception):
                pass

            try:
                self._init_piper()
                self._actual_backend = "piper"
                return
            except (ImportError, Exception):
                pass

            raise ImportError(
                "No TTS backend available. Install chatterbox-tts or piper-tts"
            )

        elif self.backend == "chatterbox":
            self._init_chatterbox()
            self._actual_backend = "chatterbox"

        elif self.backend == "piper":
            self._init_piper()
            self._actual_backend = "piper"

    def _init_chatterbox(self):
        """Initialize Chatterbox TTS."""
        from chatterbox.tts import ChatterboxTTS

        self._engine = ChatterboxTTS.from_pretrained(device="cuda")

    def _init_piper(self):
        """Initialize Piper TTS."""
        # Piper uses a different API
        self._engine = "piper"  # Placeholder

    def synthesize(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """
        Synthesize speech from text.

        Args:
            text: Text to speak.
            output_path: Optional path to save audio.

        Returns:
            Audio as numpy array (16kHz, mono).
        """
        self._init_engine()

        if self._actual_backend == "chatterbox":
            return self._synthesize_chatterbox(text, output_path)
        elif self._actual_backend == "piper":
            return self._synthesize_piper(text, output_path)
        else:
            raise RuntimeError("No TTS backend initialized")

    def _synthesize_chatterbox(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """Synthesize using Chatterbox."""
        import torchaudio

        # Generate audio
        if self.voice_reference:
            wav = self._engine.generate(
                text,
                audio_prompt_path=str(self.voice_reference),
            )
        else:
            wav = self._engine.generate(text)

        # Convert to numpy
        audio = wav.squeeze().cpu().numpy()

        # Save if path provided
        if output_path:
            torchaudio.save(
                str(output_path),
                wav.cpu(),
                self._engine.sr,
            )

        return audio

    def _synthesize_piper(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """Synthesize using Piper (subprocess)."""
        import subprocess
        import tempfile
        import wave

        # Use piper CLI
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        # Run piper
        subprocess.run(
            ["piper", "--model", "en_US-lessac-medium", "--output_file", tmp_path],
            input=text.encode(),
            check=True,
        )

        # Read audio
        with wave.open(tmp_path, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0

        # Copy to output if needed
        if output_path:
            import shutil
            shutil.copy(tmp_path, str(output_path))

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)

        return audio

    def speak(self, text: str):
        """
        Synthesize and play audio immediately.

        Args:
            text: Text to speak.
        """
        import sounddevice as sd

        audio = self.synthesize(text)

        # Play audio (16kHz sample rate)
        sample_rate = 24000 if self._actual_backend == "chatterbox" else 22050
        sd.play(audio, sample_rate)
        sd.wait()

    @property
    def sample_rate(self) -> int:
        """Get sample rate of the TTS engine."""
        if self._actual_backend == "chatterbox":
            return 24000
        else:
            return 22050
