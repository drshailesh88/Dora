"""Command-line interface for Dora."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer(
    name="dora",
    help="Dora - DocAssist Medical Knowledge Platform",
)
console = Console()


@app.command()
def query(
    question: str = typer.Argument(..., help="Medical question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    local: bool = typer.Option(False, "--local", "-l", help="Use local LLM only"),
):
    """Query the medical knowledge base."""
    from src.core.pipeline import MedicalQueryPipeline

    console.print(Panel(f"[bold]Question:[/bold] {question}", title="Dora Query"))

    with console.status("Searching knowledge base..."):
        pipeline = MedicalQueryPipeline(prefer_local_llm=local)
        answer = pipeline.query_sync(question, top_k=top_k)

    console.print("\n")
    console.print(Panel(Markdown(answer.answer), title="Answer", border_style="green"))
    console.print(f"\n[dim]Confidence: {answer.confidence.value} | Model: {answer.model_used} | Latency: {answer.latency_ms}ms[/dim]")

    if answer.citations:
        console.print("\n[bold]Sources:[/bold]")
        for i, cite in enumerate(answer.citations[:5], 1):
            console.print(f"  [{i}] {cite.source} - {cite.title}")


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="File or directory to ingest"),
    doc_type: str = typer.Option("textbook", "--type", "-t", help="Document type"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r", help="Recursive directory scan"),
):
    """Ingest documents into the knowledge base."""
    from src.ingestion import IngestionPipeline

    pipeline = IngestionPipeline()

    if path.is_file():
        doc = pipeline.ingest_file(path, doc_type=doc_type)
        console.print(f"[green]✓ Ingested {doc.title} ({doc.chunk_count} chunks)[/green]")
    elif path.is_dir():
        docs = pipeline.ingest_directory(path, doc_type=doc_type, recursive=recursive)
        console.print(f"[green]✓ Ingested {len(docs)} documents[/green]")
    else:
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the API server."""
    import uvicorn

    console.print(Panel(f"Starting Dora API at http://{host}:{port}", title="🚀 Dora Server"))
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


@app.command()
def stats():
    """Show knowledge base statistics."""
    from src.retrieval import HybridRetriever

    retriever = HybridRetriever()
    stats = retriever.index_stats()

    console.print(Panel.fit(
        f"Sparse index size: {stats.get('sparse_size', 0)} documents\n"
        f"Collection: {stats.get('collection', 'N/A')}",
        title="📊 Knowledge Base Stats",
    ))


@app.command()
def version():
    """Show version information."""
    from src import __version__

    console.print(f"Dora version {__version__}")


if __name__ == "__main__":
    app()
