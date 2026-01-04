"""Document ingestion pipeline."""

from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, TaskID

from src.core.models import Chunk, Document
from src.retrieval import HybridRetriever

from .chunker import MedicalChunker
from .parser import DocumentParser

console = Console()


class IngestionPipeline:
    """
    Full document ingestion pipeline.

    Pipeline:
    1. Parse document (PDF, TXT, etc.)
    2. Chunk with medical awareness
    3. Generate embeddings
    4. Store in vector database + BM25 index
    """

    def __init__(
        self,
        collection_name: str = "medical_knowledge",
        use_unstructured: bool = False,
    ):
        """
        Initialize ingestion pipeline.

        Args:
            collection_name: Vector collection to store documents.
            use_unstructured: Use unstructured for PDF parsing.
        """
        self.parser = DocumentParser(use_unstructured=use_unstructured)
        self.chunker = MedicalChunker()
        self.retriever = HybridRetriever(collection_name=collection_name)
        self.collection_name = collection_name

    def ingest_file(
        self,
        file_path: str | Path,
        doc_type: str = "textbook",
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """
        Ingest a single document.

        Args:
            file_path: Path to the document.
            doc_type: Type of document (textbook, guideline, paper).
            metadata: Additional metadata.

        Returns:
            Document record.
        """
        file_path = Path(file_path)
        metadata = metadata or {}

        console.print(f"[bold blue]Ingesting:[/bold blue] {file_path.name}")

        # 1. Parse document
        with console.status("Parsing document..."):
            parsed = self.parser.parse(file_path)

        console.print(f"  ✓ Parsed ({parsed['metadata'].get('num_pages', 'N/A')} pages)")

        # 2. Chunk document
        with console.status("Chunking..."):
            chunk_metadata = {
                **metadata,
                **parsed["metadata"],
                "doc_type": doc_type,
            }

            # If we have pages, chunk each page separately to preserve page numbers
            chunks = []
            if parsed.get("pages"):
                for page_data in parsed["pages"]:
                    page_chunks = self.chunker.chunk(
                        page_data["text"],
                        metadata={**chunk_metadata, "page": page_data["page"]},
                    )
                    chunks.extend(page_chunks)
            else:
                chunks = self.chunker.chunk(parsed["text"], metadata=chunk_metadata)

        console.print(f"  ✓ Created {len(chunks)} chunks")

        # 3. Add to retriever (handles embedding + storage)
        with console.status("Indexing..."):
            self.retriever.add_chunks(chunks)

        console.print(f"  ✓ Indexed in {self.collection_name}")

        # 4. Create document record
        doc = Document(
            title=file_path.stem,
            doc_type=doc_type,
            source=file_path.name,
            file_path=str(file_path),
            file_hash=parsed["metadata"]["file_hash"],
            chunk_count=len(chunks),
            metadata=metadata,
        )

        console.print(f"[bold green]✓ Complete:[/bold green] {doc.title}")

        return doc

    def ingest_directory(
        self,
        directory: str | Path,
        doc_type: str = "textbook",
        pattern: str = "*.pdf",
        recursive: bool = True,
    ) -> list[Document]:
        """
        Ingest all matching documents in a directory.

        Args:
            directory: Directory to scan.
            doc_type: Type of documents.
            pattern: Glob pattern for files.
            recursive: Search subdirectories.

        Returns:
            List of Document records.
        """
        directory = Path(directory)

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        if not files:
            console.print(f"[yellow]No files matching {pattern} found in {directory}[/yellow]")
            return []

        console.print(f"[bold]Found {len(files)} files to ingest[/bold]")

        documents = []
        for file_path in files:
            try:
                doc = self.ingest_file(
                    file_path,
                    doc_type=doc_type,
                )
                documents.append(doc)
            except Exception as e:
                console.print(f"[red]Error ingesting {file_path}: {e}[/red]")

        console.print(f"\n[bold green]Ingested {len(documents)}/{len(files)} documents[/bold green]")

        return documents

    def ingest_text(
        self,
        text: str,
        title: str,
        doc_type: str = "note",
        metadata: dict[str, Any] | None = None,
    ) -> Document:
        """
        Ingest raw text directly.

        Args:
            text: Text content.
            title: Title for the document.
            doc_type: Type of document.
            metadata: Additional metadata.

        Returns:
            Document record.
        """
        metadata = metadata or {}

        chunks = self.chunker.chunk(
            text,
            metadata={
                **metadata,
                "source": title,
                "doc_type": doc_type,
            },
        )

        self.retriever.add_chunks(chunks)

        return Document(
            title=title,
            doc_type=doc_type,
            source=title,
            chunk_count=len(chunks),
            metadata=metadata,
        )
