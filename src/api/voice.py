"""Voice API endpoints for Dora."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.voice.service import VoiceService, VoiceServiceMode
from src.voice.stt import SpeechToText
from src.voice.tts import TextToSpeech

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/voice", tags=["voice"])

# Global voice service instance
_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """Get or create voice service instance."""
    global _voice_service

    if _voice_service is None:
        _voice_service = VoiceService(
            mode=VoiceServiceMode.PUSH_TO_TALK,
            enable_ambient=True,
        )

    return _voice_service


# Request/Response models
class TranscribeRequest(BaseModel):
    """Request for text transcription."""

    language: str = "en"
    enable_noise_reduction: bool = True


class TranscribeResponse(BaseModel):
    """Response from transcription."""

    text: str
    language: str
    confidence: float
    segments: list[dict] = []


class VoiceQueryRequest(BaseModel):
    """Request for voice query (text input for testing)."""

    text: str
    conversation_id: Optional[str] = None


class VoiceQueryResponse(BaseModel):
    """Response from voice query."""

    response: str
    intent: str
    confidence: float
    conversation_id: str
    requires_confirmation: bool = False


class SynthesizeRequest(BaseModel):
    """Request for speech synthesis."""

    text: str
    voice: str = "en_male_1"
    speed: float = 1.0
    volume: float = 1.0
    ssml: bool = False


class VoiceStatusResponse(BaseModel):
    """Voice system status."""

    running: bool
    mode: str
    active_conversations: int
    stt_available: bool
    tts_available: bool
    ambient_enabled: bool


class AmbientDictationRequest(BaseModel):
    """Request to control ambient dictation."""

    action: str  # "start" or "stop"


class SOAPNoteResponse(BaseModel):
    """SOAP note response."""

    subjective: list[str]
    objective: list[str]
    assessment: list[str]
    plan: list[str]
    text: str


# API Endpoints
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "en",
    enable_noise_reduction: bool = True,
):
    """
    Transcribe audio file to text.

    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Language code (en, hi, auto)
        enable_noise_reduction: Apply noise reduction

    Returns:
        Transcription result
    """
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe
        stt = SpeechToText(
            language=language,
            enable_noise_reduction=enable_noise_reduction,
        )

        result = stt.transcribe(tmp_path, language=language)

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)

        return TranscribeResponse(
            text=result["text"],
            language=result.get("language", language),
            confidence=result.get("confidence", 0.0),
            segments=result.get("segments", []),
        )

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(request: VoiceQueryRequest):
    """
    Process voice query (text input for testing).

    Args:
        request: Voice query request

    Returns:
        Voice query response
    """
    try:
        service = get_voice_service()

        # Process text query
        response = service.process_text(request.text)

        # Get current conversation
        conversation = service._current_conversation

        return VoiceQueryResponse(
            response=response,
            intent="query",  # Would need to get from NLU result
            confidence=0.8,  # Would need to get from NLU result
            conversation_id=conversation.conversation_id if conversation else "",
            requires_confirmation=False,
        )

    except Exception as e:
        logger.error(f"Voice query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/audio", response_model=VoiceQueryResponse)
async def voice_query_audio(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = None,
):
    """
    Process voice query from audio file.

    Args:
        audio: Audio file
        conversation_id: Optional conversation ID

    Returns:
        Voice query response
    """
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Load audio as numpy array
        import soundfile as sf

        audio_data, sample_rate = sf.read(tmp_path)

        # Ensure mono and float32
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        audio_data = audio_data.astype(np.float32)

        # Process through voice service
        service = get_voice_service()
        response = service.process_audio(audio_data)

        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)

        # Get current conversation
        conversation = service._current_conversation

        return VoiceQueryResponse(
            response=response,
            intent="query",
            confidence=0.8,
            conversation_id=conversation.conversation_id if conversation else "",
            requires_confirmation=False,
        )

    except Exception as e:
        logger.error(f"Voice query audio error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text.

    Args:
        request: Synthesis request

    Returns:
        Audio file (WAV)
    """
    try:
        from fastapi.responses import FileResponse

        # Create TTS engine
        tts = TextToSpeech(
            voice=request.voice,
            speed=request.speed,
            volume=request.volume,
        )

        # Generate audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name

        audio = tts.synthesize(
            request.text,
            output_path=tmp_path,
            ssml=request.ssml,
        )

        return FileResponse(
            tmp_path,
            media_type="audio/wav",
            filename="speech.wav",
        )

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=VoiceStatusResponse)
async def get_voice_status():
    """
    Get voice system status.

    Returns:
        Voice system status
    """
    try:
        service = get_voice_service()
        status = service.get_status()

        return VoiceStatusResponse(
            running=status["running"],
            mode=status["mode"],
            active_conversations=status["active_conversations"],
            stt_available=True,  # Check if STT is available
            tts_available=True,  # Check if TTS is available
            ambient_enabled=service.ambient is not None,
        )

    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ambient", response_model=SOAPNoteResponse)
async def control_ambient_dictation(request: AmbientDictationRequest):
    """
    Control ambient dictation mode.

    Args:
        request: Ambient dictation control request

    Returns:
        SOAP note if stopping, empty if starting
    """
    try:
        service = get_voice_service()

        if request.action == "start":
            service.start_ambient_dictation()
            return SOAPNoteResponse(
                subjective=[],
                objective=[],
                assessment=[],
                plan=[],
                text="",
            )

        elif request.action == "stop":
            soap_note_dict = service.stop_ambient_dictation()
            return SOAPNoteResponse(**soap_note_dict)

        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")

    except Exception as e:
        logger.error(f"Ambient dictation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming.

    Protocol:
    - Client sends: audio chunks (binary)
    - Server sends: JSON messages with transcription and responses
    """
    await websocket.accept()
    logger.info("Voice WebSocket connected")

    service = get_voice_service()
    audio_buffer = []

    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()

            # Convert to numpy array (assuming float32 PCM)
            audio_chunk = np.frombuffer(data, dtype=np.float32)
            audio_buffer.append(audio_chunk)

            # Process when we have enough audio (e.g., 2 seconds)
            if len(audio_buffer) >= 40:  # 40 chunks @ 50ms each = 2s
                # Concatenate buffer
                audio = np.concatenate(audio_buffer)

                try:
                    # Transcribe
                    result = service.stt.transcribe(audio)

                    # Send transcription
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result["text"],
                        "confidence": result.get("confidence", 0.0),
                    })

                    # Process if we have text
                    if result["text"].strip():
                        response = service.process_text(result["text"])

                        # Send response
                        await websocket.send_json({
                            "type": "response",
                            "text": response,
                        })

                except Exception as e:
                    logger.error(f"WebSocket processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })

                # Clear buffer (keep small overlap)
                audio_buffer = audio_buffer[-5:]

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Health check
@router.get("/health")
async def voice_health():
    """Voice service health check."""
    return {"status": "ok", "service": "voice"}
