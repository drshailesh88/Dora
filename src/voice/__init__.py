"""Voice agent module for Dora - complete voice interface with wake word, STT, TTS, NLU, and ambient dictation."""

# Core components
from .stt import SpeechToText, AudioRecorder
from .tts import TextToSpeech, SSMLBuilder
from .wake_word import WakeWordDetector, ContinuousWakeWordListener

# NLU and conversation
from .nlu import NaturalLanguageUnderstanding, MedicalNER, Intent
from .conversation import (
    ConversationManager,
    ConfirmationManager,
    ClarificationHandler,
    Conversation,
    ConversationTurn,
)

# Ambient dictation
from .ambient import AmbientDictation, ClinicalSegment, SOAPNote, ClinicalInformationExtractor

# Commands and service
from .commands import VoiceCommandHandler, VoiceCommandResult
from .service import VoiceService, VoiceServiceMode

# Legacy agent (for backward compatibility)
from .agent import VoiceAgent

__all__ = [
    # STT
    "SpeechToText",
    "AudioRecorder",
    # TTS
    "TextToSpeech",
    "SSMLBuilder",
    # Wake word
    "WakeWordDetector",
    "ContinuousWakeWordListener",
    # NLU
    "NaturalLanguageUnderstanding",
    "MedicalNER",
    "Intent",
    # Conversation
    "ConversationManager",
    "ConfirmationManager",
    "ClarificationHandler",
    "Conversation",
    "ConversationTurn",
    # Ambient
    "AmbientDictation",
    "ClinicalSegment",
    "SOAPNote",
    "ClinicalInformationExtractor",
    # Commands
    "VoiceCommandHandler",
    "VoiceCommandResult",
    # Service
    "VoiceService",
    "VoiceServiceMode",
    # Legacy
    "VoiceAgent",
]
