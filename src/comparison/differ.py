"""
Document Diffing Engine

Provides text-based document comparison using difflib.
"""

import difflib
import logging
import re
import time
from typing import Optional

from .models import (
    ChangeType,
    ComparisonResult,
    DocumentChange,
    DocumentMetadata,
    LineRange,
)

logger = logging.getLogger(__name__)


class DocumentDiffer:
    """
    Text-based document comparison engine.

    Uses Python's difflib for efficient line-by-line comparison
    with support for context extraction.
    """

    def __init__(
        self,
        context_lines: int = 3,
        ignore_whitespace: bool = True,
        ignore_case: bool = False,
    ):
        """
        Initialize differ.

        Args:
            context_lines: Lines of context around changes
            ignore_whitespace: Normalize whitespace before comparison
            ignore_case: Case-insensitive comparison
        """
        self.context_lines = context_lines
        self.ignore_whitespace = ignore_whitespace
        self.ignore_case = ignore_case

        logger.info(
            f"Initialized DocumentDiffer (context={context_lines}, "
            f"ignore_whitespace={ignore_whitespace})"
        )

    def compare(
        self,
        left_text: str,
        right_text: str,
        left_metadata: DocumentMetadata,
        right_metadata: DocumentMetadata,
    ) -> ComparisonResult:
        """
        Compare two documents.

        Args:
            left_text: Original/left document text
            right_text: New/right document text
            left_metadata: Left document metadata
            right_metadata: Right document metadata

        Returns:
            ComparisonResult with changes
        """
        start_time = time.perf_counter()
        logger.info(
            f"Comparing documents: {left_metadata.title} vs {right_metadata.title}"
        )

        # Normalize text if needed
        left_lines = self._prepare_lines(left_text)
        right_lines = self._prepare_lines(right_text)

        # Get diff operations
        differ = difflib.SequenceMatcher(None, left_lines, right_lines)
        opcodes = differ.get_opcodes()

        # Convert to changes
        changes = self._opcodes_to_changes(
            opcodes, left_lines, right_lines, left_text, right_text
        )

        # Calculate timing
        comparison_time = int((time.perf_counter() - start_time) * 1000)

        # Create result
        result = ComparisonResult(
            left_document=left_metadata,
            right_document=right_metadata,
            changes=changes,
            comparison_time_ms=comparison_time,
        )
        result.update_statistics()

        logger.info(
            f"Comparison complete: {result.total_changes} changes "
            f"(+{result.additions}, -{result.deletions}, ~{result.modifications}) "
            f"in {comparison_time}ms"
        )

        return result

    def _prepare_lines(self, text: str) -> list[str]:
        """
        Prepare text for comparison.

        Args:
            text: Raw text

        Returns:
            List of normalized lines
        """
        lines = text.splitlines(keepends=True)

        if self.ignore_whitespace:
            lines = [self._normalize_whitespace(line) for line in lines]

        if self.ignore_case:
            lines = [line.lower() for line in lines]

        return lines

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        # Strip trailing whitespace
        text = text.rstrip()
        return text

    def _opcodes_to_changes(
        self,
        opcodes: list[tuple],
        left_lines: list[str],
        right_lines: list[str],
        original_left: str,
        original_right: str,
    ) -> list[DocumentChange]:
        """
        Convert difflib opcodes to DocumentChange objects.

        Args:
            opcodes: difflib opcodes
            left_lines: Prepared left lines
            right_lines: Prepared right lines
            original_left: Original left text
            original_right: Original right text

        Returns:
            List of changes
        """
        changes = []
        original_left_lines = original_left.splitlines()
        original_right_lines = original_right.splitlines()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                continue

            change_type = {
                "replace": ChangeType.MODIFIED,
                "delete": ChangeType.REMOVED,
                "insert": ChangeType.ADDED,
            }.get(tag)

            if not change_type:
                continue

            # Get original text (not normalized)
            left_text = (
                "\n".join(original_left_lines[i1:i2]) if i1 < i2 else None
            )
            right_text = (
                "\n".join(original_right_lines[j1:j2]) if j1 < j2 else None
            )

            # Get line ranges (1-indexed)
            left_range = (
                LineRange(start=i1 + 1, end=i2) if i1 < i2 else None
            )
            right_range = (
                LineRange(start=j1 + 1, end=j2) if j1 < j2 else None
            )

            # Get context
            context_before = self._get_context_before(
                original_left_lines, i1
            )
            context_after = self._get_context_after(
                original_left_lines if tag != "insert" else original_right_lines,
                i2 if tag != "insert" else j2,
            )

            change = DocumentChange(
                type=change_type,
                left_text=left_text,
                right_text=right_text,
                left_lines=left_range,
                right_lines=right_range,
                context_before=context_before,
                context_after=context_after,
            )
            changes.append(change)

        return changes

    def _get_context_before(self, lines: list[str], index: int) -> Optional[str]:
        """Get context lines before a change."""
        start = max(0, index - self.context_lines)
        if start >= index:
            return None
        return "\n".join(lines[start:index])

    def _get_context_after(self, lines: list[str], index: int) -> Optional[str]:
        """Get context lines after a change."""
        end = min(len(lines), index + self.context_lines)
        if index >= end:
            return None
        return "\n".join(lines[index:end])

    def get_unified_diff(
        self,
        left_text: str,
        right_text: str,
        left_name: str = "original",
        right_name: str = "modified",
    ) -> str:
        """
        Generate unified diff format.

        Args:
            left_text: Original text
            right_text: Modified text
            left_name: Name for left document
            right_name: Name for right document

        Returns:
            Unified diff string
        """
        left_lines = left_text.splitlines(keepends=True)
        right_lines = right_text.splitlines(keepends=True)

        diff = difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_name,
            tofile=right_name,
            lineterm="",
        )

        return "".join(diff)

    def get_html_diff(
        self,
        left_text: str,
        right_text: str,
        left_name: str = "Original",
        right_name: str = "Modified",
    ) -> str:
        """
        Generate side-by-side HTML diff.

        Args:
            left_text: Original text
            right_text: Modified text
            left_name: Name for left document
            right_name: Name for right document

        Returns:
            HTML string with diff table
        """
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()

        differ = difflib.HtmlDiff(wrapcolumn=80)
        return differ.make_table(
            left_lines,
            right_lines,
            fromdesc=left_name,
            todesc=right_name,
            context=True,
            numlines=self.context_lines,
        )

    def calculate_similarity(self, left_text: str, right_text: str) -> float:
        """
        Calculate similarity ratio between documents.

        Args:
            left_text: First document
            right_text: Second document

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        left_lines = self._prepare_lines(left_text)
        right_lines = self._prepare_lines(right_text)

        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        return matcher.ratio()
