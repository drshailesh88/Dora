"""Document parsing for various formats."""

import hashlib
from pathlib import Path
from typing import Any


class DocumentParser:
    """
    Parse documents from various formats.

    Supported formats:
    - PDF (via pypdf or unstructured)
    - TXT (plain text)
    - Markdown
    """

    def __init__(self, use_unstructured: bool = False):
        """
        Initialize parser.

        Args:
            use_unstructured: Use unstructured library for better PDF parsing.
        """
        self.use_unstructured = use_unstructured

    def parse(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse a document file.

        Args:
            file_path: Path to the document.

        Returns:
            Dict with 'text', 'metadata', and 'pages' (if applicable).
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._parse_pdf(file_path)
        elif suffix in [".txt", ".md", ".markdown"]:
            return self._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _parse_pdf(self, file_path: Path) -> dict[str, Any]:
        """Parse PDF file."""
        if self.use_unstructured:
            return self._parse_pdf_unstructured(file_path)
        else:
            return self._parse_pdf_pypdf(file_path)

    def _parse_pdf_pypdf(self, file_path: Path) -> dict[str, Any]:
        """Parse PDF using pypdf."""
        from pypdf import PdfReader

        reader = PdfReader(file_path)

        pages = []
        full_text = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({"page": i + 1, "text": text})
            full_text.append(text)

        return {
            "text": "\n\n".join(full_text),
            "pages": pages,
            "metadata": {
                "source": file_path.name,
                "file_path": str(file_path),
                "file_hash": self._hash_file(file_path),
                "num_pages": len(pages),
                "parser": "pypdf",
            },
        }

    def _parse_pdf_unstructured(self, file_path: Path) -> dict[str, Any]:
        """Parse PDF using unstructured for better extraction."""
        from unstructured.partition.pdf import partition_pdf

        elements = partition_pdf(str(file_path))

        pages = {}
        for element in elements:
            page_num = element.metadata.page_number or 1
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(str(element))

        page_list = [
            {"page": num, "text": "\n".join(texts)} for num, texts in sorted(pages.items())
        ]

        full_text = "\n\n".join(p["text"] for p in page_list)

        return {
            "text": full_text,
            "pages": page_list,
            "metadata": {
                "source": file_path.name,
                "file_path": str(file_path),
                "file_hash": self._hash_file(file_path),
                "num_pages": len(page_list),
                "parser": "unstructured",
            },
        }

    def _parse_text(self, file_path: Path) -> dict[str, Any]:
        """Parse plain text or markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        return {
            "text": text,
            "pages": None,
            "metadata": {
                "source": file_path.name,
                "file_path": str(file_path),
                "file_hash": self._hash_file(file_path),
                "parser": "text",
            },
        }

    def _hash_file(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()
