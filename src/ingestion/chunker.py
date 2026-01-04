"""Medical-aware text chunking."""

import re
from typing import Any

from src.core.config import settings
from src.core.models import Chunk


class MedicalChunker:
    """
    Medical-aware text chunking.

    Special handling for:
    - Drug dosing blocks (keep together)
    - Tables (keep together)
    - Clinical protocols (keep steps together)
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum chunk size in characters.
            chunk_overlap: Overlap between chunks.
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Patterns for content that should stay together
        self.dosing_pattern = re.compile(
            r"(?:dosage|dosing|dose|administration)[\s\S]{0,500}?(?:mg|mcg|units?|ml|tablets?|capsules?)",
            re.IGNORECASE,
        )
        self.table_pattern = re.compile(r"\|.*\|.*\n(?:\|.*\|.*\n)+", re.MULTILINE)

    def chunk(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Chunk text with medical awareness.

        Args:
            text: Text to chunk.
            metadata: Metadata to attach to all chunks.

        Returns:
            List of chunks.
        """
        metadata = metadata or {}

        # 1. Protect special blocks
        text, protected = self._protect_blocks(text)

        # 2. Split into sections first
        sections = self._split_by_headers(text)

        # 3. Chunk each section
        chunks = []
        for section in sections:
            section_chunks = self._chunk_text(section)
            chunks.extend(section_chunks)

        # 4. Restore protected blocks
        chunks = [self._restore_protected(c, protected) for c in chunks]

        # 5. Create Chunk objects with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                result.append(
                    Chunk(
                        text=chunk_text.strip(),
                        metadata={
                            **metadata,
                            "chunk_index": i,
                        },
                    )
                )

        return result

    def _protect_blocks(self, text: str) -> tuple[str, dict[str, str]]:
        """Replace special blocks with placeholders."""
        protected = {}
        counter = 0

        # Protect dosing blocks
        for match in self.dosing_pattern.finditer(text):
            placeholder = f"__PROTECTED_{counter}__"
            protected[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
            counter += 1

        # Protect tables
        for match in self.table_pattern.finditer(text):
            placeholder = f"__PROTECTED_{counter}__"
            protected[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
            counter += 1

        return text, protected

    def _restore_protected(self, text: str, protected: dict[str, str]) -> str:
        """Restore protected blocks from placeholders."""
        for placeholder, original in protected.items():
            text = text.replace(placeholder, original)
        return text

    def _split_by_headers(self, text: str) -> list[str]:
        """Split text by markdown headers."""
        # Split on ## or ### headers
        pattern = r"(?=^#{2,3}\s)", re.MULTILINE
        sections = re.split(r"(?=^#{2,3}\s)", text, flags=re.MULTILINE)
        return [s for s in sections if s.strip()]

    def _chunk_text(self, text: str) -> list[str]:
        """Recursively chunk text to target size."""
        if len(text) <= self.chunk_size:
            return [text]

        # Try splitting by different separators
        separators = ["\n\n", "\n", ". ", " "]

        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                chunks = []
                current = ""

                for part in parts:
                    if len(current) + len(part) + len(sep) <= self.chunk_size:
                        current += (sep if current else "") + part
                    else:
                        if current:
                            chunks.append(current)
                        current = part

                if current:
                    chunks.append(current)

                # Add overlap
                if self.chunk_overlap > 0 and len(chunks) > 1:
                    chunks = self._add_overlap(chunks, sep)

                return chunks

        # If no separator works, hard split
        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

    def _add_overlap(self, chunks: list[str], sep: str) -> list[str]:
        """Add overlap between chunks."""
        if len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1][-self.chunk_overlap :] if len(chunks[i - 1]) > self.chunk_overlap else chunks[i - 1]
            result.append(prev_end + sep + chunks[i])

        return result
