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


@app.command()
def desktop():
    """Launch the desktop application."""
    try:
        from src.desktop.app import run_app

        console.print(Panel("Launching Dora Desktop...", title="🖥️  Desktop App"))
        run_app()
    except ImportError as e:
        console.print(
            "[red]Desktop dependencies not installed.[/red]\n"
            "Install with: pip install 'dora[ui]'"
        )
        raise typer.Exit(1)


@app.command()
def web(
    port: int = typer.Option(8080, "--port", "-p", help="Port for web app"),
):
    """Launch as a web application."""
    try:
        from src.desktop.app import run_web_app

        console.print(Panel(f"Launching Dora Web at http://localhost:{port}", title="🌐 Web App"))
        run_web_app(port=port)
    except ImportError:
        console.print(
            "[red]Desktop dependencies not installed.[/red]\n"
            "Install with: pip install 'dora[ui]'"
        )
        raise typer.Exit(1)


@app.command()
def drugs(
    drug1: str = typer.Argument(..., help="First drug"),
    drug2: str = typer.Argument(..., help="Second drug"),
    more: list[str] = typer.Argument(None, help="Additional drugs"),
):
    """Check drug interactions."""
    from src.drugs import DrugInteractionChecker

    all_drugs = [drug1, drug2] + (more or [])

    console.print(Panel(f"Checking interactions: {', '.join(all_drugs)}", title="💊 Drug Interactions"))

    with console.status("Checking drug database..."):
        checker = DrugInteractionChecker()
        interactions = checker.check_multiple(all_drugs)

    if not interactions:
        console.print("[green]✓ No known interactions found[/green]")
    else:
        for inter in interactions:
            console.print(checker.format_warning(inter))
            console.print("")

    checker.close()


@app.command()
def license_status():
    """Show license status."""
    from src.licensing import LicenseManager

    manager = LicenseManager()
    status = manager.get_status()
    message = manager.get_status_message()
    limit = manager.get_daily_query_limit()

    console.print(Panel.fit(
        f"Status: {status.value}\n"
        f"Daily limit: {limit} queries\n"
        f"{message}",
        title="🔑 License Status",
    ))


@app.command()
def activate(
    key: str = typer.Argument(..., help="License key to activate"),
):
    """Activate a license key."""
    from src.licensing import LicenseManager

    manager = LicenseManager()
    success, message = manager.activate_license(key)

    if success:
        console.print(f"[green]✓ {message}[/green]")
    else:
        console.print(f"[red]✗ {message}[/red]")
        raise typer.Exit(1)


# Knowledge Graph commands
graph_app = typer.Typer(help="Knowledge graph operations")
app.add_typer(graph_app, name="graph")


@graph_app.command("setup")
def graph_setup():
    """Set up the knowledge graph schema."""
    from src.graph import Neo4jClient, KnowledgeGraphBuilder

    console.print(Panel("Setting up knowledge graph schema...", title="🔗 Knowledge Graph"))

    try:
        client = Neo4jClient()
        if not client.verify_connectivity():
            console.print("[red]Cannot connect to Neo4j. Make sure it's running.[/red]")
            raise typer.Exit(1)

        builder = KnowledgeGraphBuilder(client)
        builder.setup_schema()

        console.print("[green]✓ Schema created successfully[/green]")
        client.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@graph_app.command("sample")
def graph_sample():
    """Load sample medical data into the graph."""
    from src.graph import Neo4jClient, KnowledgeGraphBuilder

    console.print(Panel("Loading sample medical data...", title="🔗 Knowledge Graph"))

    try:
        client = Neo4jClient()
        builder = KnowledgeGraphBuilder(client)
        builder.create_sample_data()

        console.print("[green]✓ Sample data loaded successfully[/green]")
        client.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@graph_app.command("stats")
def graph_stats():
    """Show knowledge graph statistics."""
    from src.graph import Neo4jClient, MedicalGraphQueries

    try:
        client = Neo4jClient()
        queries = MedicalGraphQueries(client)
        stats = queries.get_stats()

        console.print(Panel.fit(
            f"Nodes: {stats.get('nodeCount', 0)}\n"
            f"Relationships: {stats.get('relCount', 0)}",
            title="📊 Knowledge Graph Stats",
        ))
        client.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@graph_app.command("disease")
def graph_disease(
    identifier: str = typer.Argument(..., help="Disease name, CUI, or ICD-10 code"),
):
    """Get disease information from knowledge graph."""
    from src.graph import Neo4jClient, MedicalGraphQueries

    try:
        client = Neo4jClient()
        queries = MedicalGraphQueries(client)

        # Get disease
        disease = queries.get_disease(identifier)
        if not disease:
            console.print(f"[yellow]Disease not found: {identifier}[/yellow]")
            client.close()
            return

        console.print(Panel(
            f"Name: {disease.get('name', 'N/A')}\n"
            f"CUI: {disease.get('cui', 'N/A')}\n"
            f"ICD-10: {disease.get('icd10', 'N/A')}",
            title=f"🏥 {disease.get('name', identifier)}",
        ))

        # Get symptoms
        symptoms = queries.get_disease_symptoms(identifier)
        if symptoms:
            console.print("\n[bold]Symptoms:[/bold]")
            for s in symptoms[:10]:
                console.print(f"  • {s['symptom']} ({s.get('frequency', 'unknown')})")

        # Get treatments
        treatments = queries.get_disease_treatments(identifier)
        if treatments:
            console.print("\n[bold]Treatments:[/bold]")
            for t in treatments[:10]:
                console.print(f"  • {t['drug']} (Line {t.get('treatment_line', '?')})")

        client.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# Analytics commands
analytics_app = typer.Typer(help="Analytics operations")
app.add_typer(analytics_app, name="analytics")


@analytics_app.command("summary")
def analytics_summary(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to include"),
):
    """Show analytics summary."""
    from src.analytics import AnalyticsDashboard

    dashboard = AnalyticsDashboard()
    console.print(dashboard.format_summary_text())


@analytics_app.command("daily")
def analytics_daily(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to show"),
):
    """Show daily analytics."""
    from src.analytics import AnalyticsStorage
    from datetime import datetime, timedelta, timezone

    storage = AnalyticsStorage()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    metrics = storage.get_daily_metrics(start_date=start_date, end_date=end_date)

    if not metrics:
        console.print("[yellow]No data for the specified period[/yellow]")
        return

    console.print(Panel("Daily Analytics", title="📊"))

    for m in metrics[:days]:
        console.print(
            f"[bold]{m['date']}[/bold]: "
            f"Queries: {m['total_queries']}, "
            f"Drug Checks: {m['drug_checks']}, "
            f"Errors: {m['errors']}, "
            f"Avg Latency: {m['avg_latency']:.0f}ms"
        )


@analytics_app.command("popular")
def analytics_popular(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of queries to show"),
):
    """Show popular queries."""
    from src.analytics import AnalyticsStorage

    storage = AnalyticsStorage()
    queries = storage.get_popular_queries(limit=limit)

    if not queries:
        console.print("[yellow]No query data available[/yellow]")
        return

    console.print(Panel("Popular Queries", title="🔥"))

    for i, q in enumerate(queries, 1):
        console.print(
            f"[bold]{i}.[/bold] ({q['count']}x) {q['query'][:60]}... "
            f"[dim]({q['avg_latency']:.0f}ms avg)[/dim]"
        )


@analytics_app.command("health")
def analytics_health():
    """Check system health based on analytics."""
    from src.analytics import AnalyticsDashboard

    dashboard = AnalyticsDashboard()
    health = dashboard.get_health_status()

    status_colors = {
        "healthy": "green",
        "warning": "yellow",
        "degraded": "red",
    }
    color = status_colors.get(health["status"], "white")

    console.print(Panel(
        f"Status: [{color}]{health['status'].upper()}[/{color}]\n"
        f"Error Rate: {health['metrics']['error_rate']*100:.1f}%\n"
        f"Avg Latency: {health['metrics']['avg_latency_ms']:.0f}ms\n"
        f"High Confidence: {health['metrics']['high_confidence_rate']*100:.1f}%",
        title="🏥 System Health",
    ))

    if health["issues"]:
        console.print("\n[bold]Issues:[/bold]")
        for issue in health["issues"]:
            console.print(f"  ⚠️  {issue}")


@analytics_app.command("export")
def analytics_export(
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export analytics data."""
    from src.analytics import AnalyticsStorage
    from datetime import datetime, timezone

    storage = AnalyticsStorage()

    if output is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output = Path(f"dora_analytics_{timestamp}.json")

    count = storage.export_to_json(output)

    console.print(f"[green]✓ Exported {count} records to {output}[/green]")


if __name__ == "__main__":
    app()
