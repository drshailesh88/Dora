"""Ambient dictation mode for automatic clinical documentation during consultations."""

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Literal

import numpy as np

from .nlu import MedicalNER
from .stt import SpeechToText

logger = logging.getLogger(__name__)


@dataclass
class ClinicalSegment:
    """Segment of clinical conversation."""

    timestamp: float
    speaker: Literal["doctor", "patient", "unknown"]
    text: str
    confidence: float
    entities: list[dict] = field(default_factory=list)


@dataclass
class SOAPNote:
    """Structured SOAP (Subjective, Objective, Assessment, Plan) note."""

    subjective: list[str] = field(default_factory=list)
    objective: list[str] = field(default_factory=list)
    assessment: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    raw_transcript: list[ClinicalSegment] = field(default_factory=list)

    def to_text(self) -> str:
        """Convert SOAP note to formatted text."""
        sections = []

        if self.subjective:
            sections.append("SUBJECTIVE:\n" + "\n".join(f"- {s}" for s in self.subjective))

        if self.objective:
            sections.append("\nOBJECTIVE:\n" + "\n".join(f"- {o}" for o in self.objective))

        if self.assessment:
            sections.append("\nASSESSMENT:\n" + "\n".join(f"- {a}" for a in self.assessment))

        if self.plan:
            sections.append("\nPLAN:\n" + "\n".join(f"- {p}" for p in self.plan))

        return "\n".join(sections)


class AmbientDictation:
    """
    Ambient dictation for automatic clinical documentation.

    Features:
    - Continuous listening during consultation
    - Auto-detect doctor vs patient speech
    - Extract clinical information
    - Generate SOAP notes automatically
    - Privacy-safe (local processing only)
    """

    def __init__(
        self,
        stt: SpeechToText | None = None,
        sample_rate: int = 16000,
        chunk_duration: float = 5.0,
        min_speech_duration: float = 1.0,
    ):
        """
        Initialize ambient dictation.

        Args:
            stt: Speech-to-text engine.
            sample_rate: Audio sample rate.
            chunk_duration: Duration of each transcription chunk.
            min_speech_duration: Minimum speech duration to process.
        """
        self.stt = stt or SpeechToText()
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.min_speech_duration = min_speech_duration

        # Medical NER for entity extraction
        self.ner = MedicalNER()

        # State
        self._running = False
        self._audio_queue = queue.Queue()
        self._segments: list[ClinicalSegment] = []
        self._callbacks: dict[str, Callable] = {}

        logger.info("Ambient dictation initialized")

    def start(
        self,
        on_segment: Callable[[ClinicalSegment], None] | None = None,
        on_soap_update: Callable[[SOAPNote], None] | None = None,
    ):
        """
        Start ambient dictation.

        Args:
            on_segment: Callback for each transcribed segment.
            on_soap_update: Callback when SOAP note is updated.
        """
        if self._running:
            logger.warning("Ambient dictation already running")
            return

        self._running = True
        self._segments = []

        if on_segment:
            self._callbacks["on_segment"] = on_segment
        if on_soap_update:
            self._callbacks["on_soap_update"] = on_soap_update

        # Start audio capture thread
        self._audio_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self._audio_thread.start()

        # Start transcription thread
        self._transcription_thread = threading.Thread(
            target=self._transcribe_loop, daemon=True
        )
        self._transcription_thread.start()

        logger.info("Ambient dictation started")

    def stop(self) -> SOAPNote:
        """
        Stop ambient dictation and generate final SOAP note.

        Returns:
            Generated SOAP note.
        """
        if not self._running:
            return SOAPNote()

        self._running = False

        # Wait for threads to finish
        time.sleep(0.5)

        # Generate final SOAP note
        soap_note = self._generate_soap_note()

        logger.info(f"Ambient dictation stopped. Generated SOAP note with {len(self._segments)} segments")

        return soap_note

    def _capture_audio(self):
        """Capture audio from microphone."""
        import sounddevice as sd

        chunk_samples = int(self.sample_rate * self.chunk_duration)

        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            self._audio_queue.put(indata.copy())

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=audio_callback,
            blocksize=chunk_samples,
        ):
            while self._running:
                time.sleep(0.1)

    def _transcribe_loop(self):
        """Transcribe audio chunks continuously."""
        while self._running:
            try:
                # Get audio chunk
                audio_chunk = self._audio_queue.get(timeout=1.0)

                # Check if chunk has sufficient speech
                if not self._has_speech(audio_chunk):
                    continue

                # Transcribe
                result = self.stt.transcribe(audio_chunk.flatten())

                if not result["text"].strip():
                    continue

                # Create segment
                segment = ClinicalSegment(
                    timestamp=time.time(),
                    speaker=self._detect_speaker(result["text"]),
                    text=result["text"],
                    confidence=result.get("confidence", 0.0),
                    entities=self.ner.extract(result["text"]),
                )

                # Add to segments
                self._segments.append(segment)

                # Callback
                if "on_segment" in self._callbacks:
                    self._callbacks["on_segment"](segment)

                # Update SOAP note periodically
                if len(self._segments) % 5 == 0:
                    soap_note = self._generate_soap_note()
                    if "on_soap_update" in self._callbacks:
                        self._callbacks["on_soap_update"](soap_note)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Transcription error: {e}")

    def _has_speech(self, audio: np.ndarray) -> bool:
        """
        Check if audio chunk contains speech.

        Args:
            audio: Audio data.

        Returns:
            True if speech detected.
        """
        # Simple energy-based detection
        rms = np.sqrt(np.mean(audio**2))
        return rms > 0.01  # Threshold

    def _detect_speaker(self, text: str) -> Literal["doctor", "patient", "unknown"]:
        """
        Detect whether speaker is doctor or patient.

        This is a simplified heuristic - can be enhanced with:
        - Voice biometrics
        - Language patterns
        - Position/microphone array

        Args:
            text: Transcribed text.

        Returns:
            Speaker label.
        """
        text_lower = text.lower()

        # Doctor indicators
        doctor_patterns = [
            "let me examine",
            "i'll prescribe",
            "your blood pressure",
            "i recommend",
            "the diagnosis",
            "you need to",
        ]

        # Patient indicators
        patient_patterns = [
            "i feel",
            "i have been",
            "it hurts",
            "i'm experiencing",
            "since yesterday",
            "how long",
        ]

        doctor_score = sum(1 for pattern in doctor_patterns if pattern in text_lower)
        patient_score = sum(1 for pattern in patient_patterns if pattern in text_lower)

        if doctor_score > patient_score:
            return "doctor"
        elif patient_score > doctor_score:
            return "patient"
        else:
            return "unknown"

    def _generate_soap_note(self) -> SOAPNote:
        """
        Generate SOAP note from collected segments.

        Returns:
            Generated SOAP note.
        """
        soap = SOAPNote(raw_transcript=self._segments)

        for segment in self._segments:
            text_lower = segment.text.lower()

            # Classify into SOAP categories
            if segment.speaker == "patient" or any(
                word in text_lower
                for word in ["feel", "pain", "symptom", "complaint", "since"]
            ):
                # Subjective (patient symptoms)
                soap.subjective.append(segment.text)

            elif any(
                word in text_lower
                for word in [
                    "blood pressure",
                    "temperature",
                    "heart rate",
                    "examination",
                    "test result",
                ]
            ):
                # Objective (measurements, exam findings)
                soap.objective.append(segment.text)

            elif any(
                word in text_lower
                for word in ["diagnosis", "likely", "rule out", "differential"]
            ):
                # Assessment (diagnosis)
                soap.assessment.append(segment.text)

            elif any(
                word in text_lower
                for word in ["prescribe", "recommend", "plan", "follow-up", "treatment"]
            ):
                # Plan (treatment plan)
                soap.plan.append(segment.text)

        return soap

    def get_transcript(self) -> list[ClinicalSegment]:
        """
        Get full transcript.

        Returns:
            List of clinical segments.
        """
        return self._segments.copy()

    def export_transcript(self, format: Literal["text", "json"] = "text") -> str:
        """
        Export transcript in specified format.

        Args:
            format: Export format.

        Returns:
            Formatted transcript.
        """
        if format == "json":
            import json

            segments_dict = [
                {
                    "timestamp": seg.timestamp,
                    "speaker": seg.speaker,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "entities": seg.entities,
                }
                for seg in self._segments
            ]
            return json.dumps(segments_dict, indent=2)

        else:  # text
            lines = []
            for seg in self._segments:
                timestamp = time.strftime("%H:%M:%S", time.localtime(seg.timestamp))
                speaker = seg.speaker.upper()
                lines.append(f"[{timestamp}] {speaker}: {seg.text}")
            return "\n".join(lines)


class ClinicalInformationExtractor:
    """
    Extract structured clinical information from ambient dictation.

    Extracts:
    - Chief complaint
    - History of present illness
    - Past medical history
    - Medications
    - Allergies
    - Physical exam findings
    - Diagnostic impressions
    - Treatment plan
    """

    def __init__(self):
        """Initialize clinical information extractor."""
        self.ner = MedicalNER()

    def extract(self, segments: list[ClinicalSegment]) -> dict:
        """
        Extract structured clinical information.

        Args:
            segments: List of clinical segments.

        Returns:
            Structured clinical data.
        """
        clinical_data = {
            "chief_complaint": [],
            "hpi": [],  # History of present illness
            "pmh": [],  # Past medical history
            "medications": [],
            "allergies": [],
            "physical_exam": [],
            "assessment": [],
            "plan": [],
        }

        for segment in segments:
            text_lower = segment.text.lower()

            # Chief complaint (usually first patient statement)
            if (
                segment.speaker == "patient"
                and any(word in text_lower for word in ["complain", "problem", "issue"])
            ):
                clinical_data["chief_complaint"].append(segment.text)

            # Medications
            if "medication" in text_lower or "taking" in text_lower:
                # Extract drug entities
                for entity in segment.entities:
                    if entity["type"] == "DRUG":
                        clinical_data["medications"].append(entity["text"])

            # Allergies
            if "allerg" in text_lower:
                clinical_data["allergies"].append(segment.text)

            # Physical exam
            if (
                segment.speaker == "doctor"
                and any(
                    word in text_lower
                    for word in ["examination", "exam", "auscult", "palpat"]
                )
            ):
                clinical_data["physical_exam"].append(segment.text)

            # Assessment
            if "diagnosis" in text_lower or "assessment" in text_lower:
                clinical_data["assessment"].append(segment.text)

            # Plan
            if "plan" in text_lower or "treatment" in text_lower:
                clinical_data["plan"].append(segment.text)

        return clinical_data
