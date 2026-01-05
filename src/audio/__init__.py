"""
Audio Module for Dora Medical Knowledge Platform

Provides NotebookLM-style audio overview generation:
- Podcast script generation from documents
- Audio synthesis using Piper TTS
- Audio streaming to clients
"""

from .podcast_generator import (
    PodcastGenerator,
    PodcastScript,
    PodcastLength,
    PodcastStyle,
    Speaker,
    DialogueLine,
)
from .audio_synthesizer import AudioSynthesizer, SynthesisResult
from .audio_streaming import AudioStreamManager, StreamingSession

__all__ = [
    # Podcast Generation
    "PodcastGenerator",
    "PodcastScript",
    "PodcastLength",
    "PodcastStyle",
    "Speaker",
    "DialogueLine",
    # Audio Synthesis
    "AudioSynthesizer",
    "SynthesisResult",
    # Streaming
    "AudioStreamManager",
    "StreamingSession",
]
