"""Enhanced Text-to-Speech with multiple voices, languages, and SSML support."""

import logging
import re
from pathlib import Path
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Enhanced Text-to-Speech with multiple backend options.

    Features:
    - Multiple voice options (male/female, Hindi/English)
    - Medical term pronunciation optimization
    - Speed/pitch/volume customization
    - SSML (Speech Synthesis Markup Language) support
    - Works offline with Piper
    - High-quality option with cloud fallback
    """

    # Available voices
    VOICES = {
        # English voices
        "en_male_1": "en_US-lessac-medium",  # Piper: calm male
        "en_male_2": "en_GB-alan-medium",  # Piper: British male
        "en_female_1": "en_US-amy-medium",  # Piper: clear female
        "en_female_2": "en_GB-jenny-medium",  # Piper: British female
        # Hindi voices
        "hi_male_1": "hi_IN-male",  # Piper: Hindi male
        "hi_female_1": "hi_IN-female",  # Piper: Hindi female
    }

    def __init__(
        self,
        backend: Literal["piper", "gtts", "elevenlabs", "auto"] = "auto",
        voice: str = "en_male_1",
        language: Literal["en", "hi"] = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0,
    ):
        """
        Initialize TTS.

        Args:
            backend: TTS backend to use.
            voice: Voice name from VOICES dict.
            language: Language code.
            speed: Speech speed multiplier (0.5-2.0).
            pitch: Pitch adjustment (-12 to +12 semitones).
            volume: Volume multiplier (0.0-2.0).
        """
        self.backend = backend
        self.voice = voice
        self.language = language
        self.speed = speed
        self.pitch = pitch
        self.volume = volume
        self._engine = None
        self._actual_backend = None

        # Medical term pronunciation overrides
        self.medical_pronunciations = self._load_medical_pronunciations()

        logger.info(
            f"Initializing TTS: backend={backend}, voice={voice}, "
            f"language={language}, speed={speed}"
        )

    def _load_medical_pronunciations(self) -> dict[str, str]:
        """Load pronunciation overrides for medical terms."""
        return {
            # Drug names (phonetic spellings)
            "metformin": "met-FOR-min",
            "atorvastatin": "ah-TOR-vah-stat-in",
            "amlodipine": "am-LOE-di-peen",
            "azithromycin": "ay-zith-roe-MY-sin",
            # Medical terms
            "hypoglycemia": "high-poe-gly-SEE-mee-ah",
            "arrhythmia": "ah-RITH-mee-ah",
            "dyspnea": "DISP-nee-ah",
            "tachycardia": "tak-ee-KAR-dee-ah",
        }

    def _init_engine(self):
        """Initialize the TTS engine."""
        if self._engine is not None:
            return

        if self.backend == "auto":
            # Try piper first (offline), fall back to gTTS
            try:
                self._init_piper()
                self._actual_backend = "piper"
                return
            except (ImportError, FileNotFoundError, Exception) as e:
                logger.warning(f"Piper init failed: {e}, trying gTTS")

            try:
                self._init_gtts()
                self._actual_backend = "gtts"
                return
            except (ImportError, Exception):
                pass

            raise ImportError("No TTS backend available. Install piper-tts or gtts")

        elif self.backend == "piper":
            self._init_piper()
            self._actual_backend = "piper"

        elif self.backend == "gtts":
            self._init_gtts()
            self._actual_backend = "gtts"

        elif self.backend == "elevenlabs":
            self._init_elevenlabs()
            self._actual_backend = "elevenlabs"

    def _init_piper(self):
        """Initialize Piper TTS."""
        # Piper uses command-line interface
        import shutil

        if not shutil.which("piper"):
            raise FileNotFoundError(
                "Piper not found. Install from: https://github.com/rhasspy/piper"
            )

        self._engine = "piper"  # Marker
        logger.info("Piper TTS initialized")

    def _init_gtts(self):
        """Initialize Google Text-to-Speech."""
        try:
            from gtts import gTTS

            self._engine = gTTS
            logger.info("gTTS initialized")
        except ImportError:
            raise ImportError("gTTS not installed. Run: pip install gtts")

    def _init_elevenlabs(self):
        """Initialize ElevenLabs TTS (premium)."""
        try:
            from elevenlabs import generate, set_api_key
            from src.core.config import settings

            api_key = getattr(settings, "elevenlabs_api_key", None)
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY not set")

            set_api_key(api_key)
            self._engine = generate
            logger.info("ElevenLabs TTS initialized")
        except ImportError:
            raise ImportError("elevenlabs not installed. Run: pip install elevenlabs")

    def synthesize(
        self,
        text: str,
        output_path: str | Path | None = None,
        ssml: bool = False,
    ) -> np.ndarray:
        """
        Synthesize speech from text.

        Args:
            text: Text to speak (can include SSML tags if ssml=True).
            output_path: Optional path to save audio.
            ssml: Whether text contains SSML markup.

        Returns:
            Audio as numpy array.
        """
        self._init_engine()

        # Process SSML if present
        if ssml:
            text = self._process_ssml(text)

        # Apply medical pronunciation
        text = self._apply_pronunciations(text)

        # Route to appropriate backend
        if self._actual_backend == "piper":
            return self._synthesize_piper(text, output_path)
        elif self._actual_backend == "gtts":
            return self._synthesize_gtts(text, output_path)
        elif self._actual_backend == "elevenlabs":
            return self._synthesize_elevenlabs(text, output_path)
        else:
            raise RuntimeError("No TTS backend initialized")

    def _process_ssml(self, text: str) -> str:
        """
        Process SSML tags to plain text with annotations.

        Supported tags:
        - <break time="500ms"/> - pause
        - <emphasis level="strong">text</emphasis> - emphasis
        - <prosody rate="slow">text</prosody> - speed change

        Args:
            text: Text with SSML tags.

        Returns:
            Processed text.
        """
        # Remove speak tag
        text = re.sub(r"</?speak>", "", text)

        # Convert breaks to pauses (approximate with punctuation)
        text = re.sub(r'<break time="\d+m?s"/>', "...", text)

        # Handle emphasis (uppercase for strong emphasis)
        text = re.sub(
            r'<emphasis level="strong">([^<]+)</emphasis>',
            lambda m: m.group(1).upper(),
            text,
        )

        # Remove prosody tags (Piper doesn't support them directly)
        text = re.sub(r"</?prosody[^>]*>", "", text)

        return text.strip()

    def _apply_pronunciations(self, text: str) -> str:
        """Apply medical term pronunciation overrides."""
        for term, pronunciation in self.medical_pronunciations.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub(pronunciation, text)

        return text

    def _synthesize_piper(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """Synthesize using Piper (subprocess)."""
        import subprocess
        import tempfile
        import wave

        # Get voice model
        voice_model = self.VOICES.get(self.voice, self.VOICES["en_male_1"])

        # Use piper CLI
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        # Build command with speed adjustment
        cmd = [
            "piper",
            "--model",
            voice_model,
            "--output_file",
            tmp_path,
        ]

        # Add speed if supported
        if self.speed != 1.0:
            cmd.extend(["--length_scale", str(1.0 / self.speed)])

        # Run piper
        try:
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper synthesis failed: {e.stderr.decode()}")
            raise

        # Read audio
        with wave.open(tmp_path, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0

        # Apply volume adjustment
        if self.volume != 1.0:
            audio = audio * self.volume

        # Copy to output if needed
        if output_path:
            import shutil

            shutil.copy(tmp_path, str(output_path))

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)

        return audio

    def _synthesize_gtts(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """Synthesize using Google Text-to-Speech."""
        import tempfile
        import wave

        from gtts import gTTS

        # Create TTS object
        tts = gTTS(
            text=text,
            lang=self.language,
            slow=(self.speed < 0.9),
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        tts.save(tmp_path)

        # Convert mp3 to wav and load
        import subprocess

        wav_path = tmp_path.replace(".mp3", ".wav")
        subprocess.run(
            ["ffmpeg", "-i", tmp_path, "-ar", "22050", "-ac", "1", wav_path],
            check=True,
            capture_output=True,
        )

        # Read audio
        with wave.open(wav_path, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0

        # Apply volume
        if self.volume != 1.0:
            audio = audio * self.volume

        # Copy to output if needed
        if output_path:
            import shutil

            shutil.copy(wav_path, str(output_path))

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)

        return audio

    def _synthesize_elevenlabs(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> np.ndarray:
        """Synthesize using ElevenLabs (premium)."""
        # Map our voice to ElevenLabs voice ID
        voice_id_map = {
            "en_male_1": "pNInz6obpgDQGcFmaJgB",  # Adam
            "en_female_1": "EXAVITQu4vr4xnSDxMaL",  # Bella
        }

        voice_id = voice_id_map.get(self.voice, voice_id_map["en_male_1"])

        # Generate audio
        audio_bytes = self._engine(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
        )

        # Convert bytes to numpy array
        # ElevenLabs returns mp3, need to decode
        import io
        import tempfile
        import wave

        import subprocess

        # Save to temp mp3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Convert to wav
        wav_path = tmp_path.replace(".mp3", ".wav")
        subprocess.run(
            ["ffmpeg", "-i", tmp_path, "-ar", "22050", "-ac", "1", wav_path],
            check=True,
            capture_output=True,
        )

        # Read audio
        with wave.open(wav_path, "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)

        return audio

    def speak(self, text: str, ssml: bool = False):
        """
        Synthesize and play audio immediately.

        Args:
            text: Text to speak.
            ssml: Whether text contains SSML.
        """
        import sounddevice as sd

        audio = self.synthesize(text, ssml=ssml)

        # Play audio
        sd.play(audio, self.sample_rate)
        sd.wait()

    def speak_async(self, text: str, ssml: bool = False, callback: callable = None):
        """
        Synthesize and play audio asynchronously (non-blocking).

        Args:
            text: Text to speak.
            ssml: Whether text contains SSML.
            callback: Function to call when done.
        """
        import threading

        def _speak():
            try:
                self.speak(text, ssml)
                if callback:
                    callback()
            except Exception as e:
                logger.error(f"Async speak error: {e}")

        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()

    @property
    def sample_rate(self) -> int:
        """Get sample rate of the TTS engine."""
        if self._actual_backend == "elevenlabs":
            return 44100
        else:
            return 22050


class SSMLBuilder:
    """Helper class to build SSML markup for TTS."""

    def __init__(self):
        self.parts = ['<speak>']

    def add_text(self, text: str) -> "SSMLBuilder":
        """Add plain text."""
        self.parts.append(text)
        return self

    def add_break(self, duration_ms: int) -> "SSMLBuilder":
        """Add a pause."""
        self.parts.append(f'<break time="{duration_ms}ms"/>')
        return self

    def add_emphasis(self, text: str, level: str = "strong") -> "SSMLBuilder":
        """Add emphasized text."""
        self.parts.append(f'<emphasis level="{level}">{text}</emphasis>')
        return self

    def add_prosody(
        self,
        text: str,
        rate: str | None = None,
        pitch: str | None = None,
        volume: str | None = None,
    ) -> "SSMLBuilder":
        """Add prosody (rate, pitch, volume) changes."""
        attrs = []
        if rate:
            attrs.append(f'rate="{rate}"')
        if pitch:
            attrs.append(f'pitch="{pitch}"')
        if volume:
            attrs.append(f'volume="{volume}"')

        attr_str = " ".join(attrs)
        self.parts.append(f'<prosody {attr_str}>{text}</prosody>')
        return self

    def build(self) -> str:
        """Build final SSML string."""
        self.parts.append('</speak>')
        return "".join(self.parts)
