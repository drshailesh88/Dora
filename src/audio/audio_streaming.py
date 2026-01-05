"""
Audio Streaming Manager for Podcast Delivery

Provides streaming infrastructure for delivering synthesized audio
to clients with support for:
- Progressive streaming as audio is generated
- Resume/seek capabilities
- Multiple concurrent streams
- Caching of generated audio
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Callable, Optional
from uuid import uuid4

from .audio_synthesizer import AudioFormat, AudioSynthesizer, SynthesisResult
from .podcast_generator import PodcastGenerator, PodcastLength, PodcastScript, PodcastStyle

logger = logging.getLogger(__name__)


class StreamStatus(str, Enum):
    """Status of a streaming session."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    STREAMING = "streaming"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class StreamingSession:
    """
    A streaming session for audio delivery.

    Tracks generation progress and provides streaming interface.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    document_id: str = ""
    user_id: str = ""

    # Status
    status: StreamStatus = StreamStatus.PENDING
    progress: float = 0.0  # 0-100
    error_message: Optional[str] = None

    # Audio data
    audio_data: Optional[bytes] = None
    format: AudioFormat = AudioFormat.WAV
    duration_seconds: float = 0.0

    # Metadata
    title: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Streaming state
    bytes_streamed: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "format": self.format.value,
            "duration_seconds": self.duration_seconds,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "size_bytes": len(self.audio_data) if self.audio_data else 0,
        }


class AudioCache:
    """
    Cache for generated audio files.

    Stores audio by document ID + settings hash for reuse.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_size_mb: int = 1000,
        ttl_hours: int = 24,
    ):
        """
        Initialize audio cache.

        Args:
            cache_dir: Directory for cache storage
            max_size_mb: Maximum cache size in MB
            ttl_hours: Time-to-live for cached items
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".dora/audio_cache"
        self.max_size_mb = max_size_mb
        self.ttl = timedelta(hours=ttl_hours)
        self._memory_cache: dict[str, SynthesisResult] = {}

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized AudioCache at {self.cache_dir}")

    def _get_cache_key(
        self,
        document_id: str,
        length: PodcastLength,
        style: PodcastStyle,
        format: AudioFormat,
    ) -> str:
        """Generate cache key from parameters."""
        key_str = f"{document_id}:{length.value}:{style.value}:{format.value}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self,
        document_id: str,
        length: PodcastLength,
        style: PodcastStyle,
        format: AudioFormat,
    ) -> Optional[SynthesisResult]:
        """
        Get cached audio if available.

        Args:
            document_id: Document identifier
            length: Podcast length
            style: Podcast style
            format: Audio format

        Returns:
            SynthesisResult if cached, None otherwise
        """
        key = self._get_cache_key(document_id, length, style, format)

        # Check memory cache first
        if key in self._memory_cache:
            logger.debug(f"Audio cache hit (memory): {key}")
            return self._memory_cache[key]

        # Check disk cache
        cache_path = self.cache_dir / f"{key}.{format.value}"
        meta_path = self.cache_dir / f"{key}.meta"

        if cache_path.exists() and meta_path.exists():
            # Check TTL
            if datetime.fromtimestamp(cache_path.stat().st_mtime) + self.ttl > datetime.utcnow():
                logger.debug(f"Audio cache hit (disk): {key}")
                return self._load_from_disk(cache_path, meta_path, format)

        return None

    def put(
        self,
        document_id: str,
        length: PodcastLength,
        style: PodcastStyle,
        result: SynthesisResult,
    ) -> None:
        """
        Cache synthesis result.

        Args:
            document_id: Document identifier
            length: Podcast length
            style: Podcast style
            result: Synthesis result to cache
        """
        key = self._get_cache_key(document_id, length, style, result.format)

        # Store in memory
        self._memory_cache[key] = result

        # Store on disk
        try:
            cache_path = self.cache_dir / f"{key}.{result.format.value}"
            meta_path = self.cache_dir / f"{key}.meta"

            cache_path.write_bytes(result.audio_data)
            meta_path.write_text(
                f"{result.duration_seconds}\n{result.sample_rate}\n{result.channels}"
            )

            logger.debug(f"Audio cached: {key}")

            # Clean up if over size limit
            self._cleanup_if_needed()

        except Exception as e:
            logger.error(f"Failed to cache audio: {e}")

    def _load_from_disk(
        self,
        cache_path: Path,
        meta_path: Path,
        format: AudioFormat,
    ) -> Optional[SynthesisResult]:
        """Load cached audio from disk."""
        try:
            audio_data = cache_path.read_bytes()
            meta_lines = meta_path.read_text().strip().split("\n")

            return SynthesisResult(
                audio_data=audio_data,
                format=format,
                duration_seconds=float(meta_lines[0]),
                sample_rate=int(meta_lines[1]),
                channels=int(meta_lines[2]),
            )

        except Exception as e:
            logger.error(f"Failed to load cached audio: {e}")
            return None

    def _cleanup_if_needed(self) -> None:
        """Clean up cache if over size limit."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*"))
        max_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_bytes:
            # Delete oldest files
            files = sorted(
                self.cache_dir.glob("*"),
                key=lambda f: f.stat().st_mtime,
            )

            for f in files:
                if total_size <= max_bytes * 0.8:  # Clean to 80%
                    break
                total_size -= f.stat().st_size
                f.unlink()
                logger.debug(f"Removed cached audio: {f.name}")


class AudioStreamManager:
    """
    Manager for audio streaming sessions.

    Handles:
    - Creating and tracking streaming sessions
    - Background audio generation
    - Progressive streaming delivery
    - Session cleanup
    """

    def __init__(
        self,
        podcast_generator: Optional[PodcastGenerator] = None,
        audio_synthesizer: Optional[AudioSynthesizer] = None,
        cache: Optional[AudioCache] = None,
        max_concurrent_generations: int = 5,
    ):
        """
        Initialize stream manager.

        Args:
            podcast_generator: Generator for podcast scripts
            audio_synthesizer: Synthesizer for audio
            cache: Audio cache
            max_concurrent_generations: Max concurrent audio generations
        """
        self.podcast_generator = podcast_generator or PodcastGenerator()
        self.audio_synthesizer = audio_synthesizer or AudioSynthesizer()
        self.cache = cache or AudioCache()

        self._sessions: dict[str, StreamingSession] = {}
        self._generation_semaphore = asyncio.Semaphore(max_concurrent_generations)
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(
            f"Initialized AudioStreamManager (max_concurrent={max_concurrent_generations})"
        )

    async def start(self) -> None:
        """Start the stream manager background tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("AudioStreamManager started")

    async def stop(self) -> None:
        """Stop the stream manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("AudioStreamManager stopped")

    async def create_session(
        self,
        document_id: str,
        user_id: str,
        title: str,
        content: str,
        length: PodcastLength = PodcastLength.MEDIUM,
        style: PodcastStyle = PodcastStyle.PROFESSIONAL,
        format: AudioFormat = AudioFormat.WAV,
    ) -> StreamingSession:
        """
        Create a new streaming session.

        Args:
            document_id: Document identifier
            user_id: User identifier
            title: Document title
            content: Document content
            length: Podcast length
            style: Podcast style
            format: Audio format

        Returns:
            Created streaming session
        """
        # Check cache first
        cached = self.cache.get(document_id, length, style, format)
        if cached:
            session = StreamingSession(
                document_id=document_id,
                user_id=user_id,
                status=StreamStatus.READY,
                progress=100.0,
                audio_data=cached.audio_data,
                format=format,
                duration_seconds=cached.duration_seconds,
                title=f"Medical Insight: {title}",
                completed_at=datetime.utcnow(),
            )
            self._sessions[session.id] = session
            logger.info(f"Created session from cache: {session.id}")
            return session

        # Create new session
        session = StreamingSession(
            document_id=document_id,
            user_id=user_id,
            status=StreamStatus.PENDING,
            format=format,
            title=f"Medical Insight: {title}",
        )
        self._sessions[session.id] = session

        # Start background generation
        asyncio.create_task(
            self._generate_audio(session, title, content, length, style)
        )

        logger.info(f"Created streaming session: {session.id}")
        return session

    async def _generate_audio(
        self,
        session: StreamingSession,
        title: str,
        content: str,
        length: PodcastLength,
        style: PodcastStyle,
    ) -> None:
        """Background task to generate audio."""
        async with self._generation_semaphore:
            try:
                session.status = StreamStatus.GENERATING
                logger.info(f"Generating audio for session: {session.id}")

                # Generate podcast script
                script = self.podcast_generator.generate_from_text(
                    title=title,
                    content=content,
                    length=length,
                    style=style,
                )

                # Progress callback
                def update_progress(current: int, total: int):
                    session.progress = (current / total) * 100

                # Synthesize audio
                result = await self.audio_synthesizer.synthesize_script(
                    script,
                    progress_callback=update_progress,
                )

                # Update session
                session.audio_data = result.audio_data
                session.duration_seconds = result.duration_seconds
                session.status = StreamStatus.READY
                session.progress = 100.0
                session.completed_at = datetime.utcnow()

                # Cache result
                self.cache.put(session.document_id, length, style, result)

                logger.info(
                    f"Audio generation complete: {session.id} "
                    f"({result.duration_seconds:.1f}s, {result.size_mb:.2f}MB)"
                )

            except Exception as e:
                logger.error(f"Audio generation failed: {e}")
                session.status = StreamStatus.ERROR
                session.error_message = str(e)

    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session:
            session.last_accessed = datetime.utcnow()
        return session

    def get_session_status(self, session_id: str) -> Optional[dict]:
        """Get session status for API response."""
        session = self.get_session(session_id)
        return session.to_dict() if session else None

    async def stream_audio(
        self,
        session_id: str,
        chunk_size: int = 8192,
        start_byte: int = 0,
    ) -> AsyncIterator[bytes]:
        """
        Stream audio data.

        Args:
            session_id: Session identifier
            chunk_size: Bytes per chunk
            start_byte: Starting byte position (for resume)

        Yields:
            Audio data chunks
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Wait for generation if needed
        while session.status == StreamStatus.GENERATING:
            await asyncio.sleep(0.5)

        if session.status == StreamStatus.ERROR:
            raise RuntimeError(session.error_message or "Audio generation failed")

        if not session.audio_data:
            raise RuntimeError("No audio data available")

        session.status = StreamStatus.STREAMING
        session.bytes_streamed = start_byte

        # Stream chunks
        data = session.audio_data
        pos = start_byte

        while pos < len(data):
            chunk = data[pos : pos + chunk_size]
            yield chunk
            pos += len(chunk)
            session.bytes_streamed = pos

        session.status = StreamStatus.COMPLETED
        logger.debug(f"Streaming complete: {session_id}")

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Deleted session: {session_id}")
            return True
        return False

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                now = datetime.utcnow()
                expired = [
                    sid
                    for sid, session in self._sessions.items()
                    if (now - session.last_accessed) > timedelta(hours=1)
                ]

                for sid in expired:
                    del self._sessions[sid]

                if expired:
                    logger.info(f"Cleaned up {len(expired)} expired sessions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def get_all_sessions(self, user_id: Optional[str] = None) -> list[dict]:
        """Get all sessions, optionally filtered by user."""
        sessions = self._sessions.values()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return [s.to_dict() for s in sessions]
