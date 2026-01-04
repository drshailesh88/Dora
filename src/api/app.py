"""FastAPI application for Dora API."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.config import settings
from src.core.models import MedicalAnswer, PatientContext
from src.core.pipeline import MedicalQueryPipeline
from src.ingestion import IngestionPipeline


# Global pipeline instances
query_pipeline: MedicalQueryPipeline | None = None
ingestion_pipeline: IngestionPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipelines on startup."""
    global query_pipeline, ingestion_pipeline

    query_pipeline = MedicalQueryPipeline()
    ingestion_pipeline = IngestionPipeline()

    yield

    # Cleanup if needed
    query_pipeline = None
    ingestion_pipeline = None


app = FastAPI(
    title="Dora - Medical Knowledge API",
    description="DocAssist Medical Knowledge Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """Request for medical query."""

    question: str
    patient_id: int | None = None
    patient_context: PatientContext | None = None
    top_k: int = 10
    use_multi_query: bool = True
    use_hyde: bool = True


class QueryResponse(BaseModel):
    """Response from medical query."""

    success: bool
    answer: MedicalAnswer | None = None
    error: str | None = None


class IngestTextRequest(BaseModel):
    """Request to ingest text content."""

    text: str
    title: str
    doc_type: str = "note"
    metadata: dict | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    has_cloud_llm: bool
    has_reranker: bool


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and configuration."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        has_cloud_llm=settings.has_cloud_llm,
        has_reranker=settings.has_reranker,
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the medical knowledge base.

    Returns evidence-based answers with citations.
    """
    if query_pipeline is None:
        raise HTTPException(status_code=503, detail="Query pipeline not initialized")

    try:
        answer = await query_pipeline.query(
            question=request.question,
            patient_context=request.patient_context,
            top_k=request.top_k,
        )

        return QueryResponse(success=True, answer=answer)

    except Exception as e:
        return QueryResponse(success=False, error=str(e))


@app.post("/api/v1/ingest/text")
async def ingest_text(request: IngestTextRequest):
    """Ingest raw text content."""
    if ingestion_pipeline is None:
        raise HTTPException(status_code=503, detail="Ingestion pipeline not initialized")

    try:
        doc = ingestion_pipeline.ingest_text(
            text=request.text,
            title=request.title,
            doc_type=request.doc_type,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "document_id": doc.id,
            "title": doc.title,
            "chunk_count": doc.chunk_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    doc_type: str = Form("textbook"),
    title: str | None = Form(None),
):
    """Upload and ingest a document file."""
    if ingestion_pipeline is None:
        raise HTTPException(status_code=503, detail="Ingestion pipeline not initialized")

    import tempfile
    from pathlib import Path

    # Save uploaded file temporarily
    suffix = Path(file.filename).suffix if file.filename else ".pdf"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc = ingestion_pipeline.ingest_file(
            file_path=tmp_path,
            doc_type=doc_type,
            metadata={"original_filename": file.filename, "title": title},
        )

        return {
            "success": True,
            "document_id": doc.id,
            "title": doc.title,
            "chunk_count": doc.chunk_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp file
        import os

        os.unlink(tmp_path)


@app.get("/api/v1/stats")
async def get_stats():
    """Get statistics about the knowledge base."""
    if query_pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    stats = query_pipeline.retriever.index_stats()

    return {
        "success": True,
        "stats": stats,
    }


# Run with: uvicorn src.api.app:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
