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
from src.drugs import DrugInteractionChecker
from src.licensing import LicenseManager, LicenseStatus
from src.api.auth import router as auth_router
from src.api.payments import router as payments_router
from src.api.personalization import router as personalization_router
from src.api.tenants import router as tenants_router
from src.api.engagement import router as engagement_router
try:
    from src.api.admin import router as admin_router
except ImportError:
    admin_router = None
try:
    from src.api.academic import router as academic_router
except ImportError:
    academic_router = None
try:
    from src.api.whatsapp import router as whatsapp_router
except ImportError:
    whatsapp_router = None
try:
    from src.api.drugs import router as drugs_router
except ImportError:
    drugs_router = None
try:
    from src.api.voice import router as voice_router
except ImportError:
    voice_router = None
try:
    from src.api.learning import router as learning_router
except ImportError:
    learning_router = None
try:
    from src.api.format import router as format_router
except ImportError:
    format_router = None


# Global pipeline instances
query_pipeline: MedicalQueryPipeline | None = None
ingestion_pipeline: IngestionPipeline | None = None
drug_checker: DrugInteractionChecker | None = None
license_manager: LicenseManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipelines on startup."""
    global query_pipeline, ingestion_pipeline, drug_checker, license_manager

    query_pipeline = MedicalQueryPipeline()
    ingestion_pipeline = IngestionPipeline()
    drug_checker = DrugInteractionChecker()
    license_manager = LicenseManager()

    yield

    # Cleanup if needed
    if drug_checker:
        drug_checker.close()
    query_pipeline = None
    ingestion_pipeline = None
    drug_checker = None
    license_manager = None


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

# Tenant context middleware
from src.tenants.middleware import TenantContextMiddleware
app.add_middleware(TenantContextMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(personalization_router)
app.include_router(tenants_router)
app.include_router(engagement_router)
if admin_router:
    app.include_router(admin_router)
if academic_router:
    app.include_router(academic_router)
if whatsapp_router:
    app.include_router(whatsapp_router)
if drugs_router:
    app.include_router(drugs_router)
if voice_router:
    app.include_router(voice_router)
if learning_router:
    app.include_router(learning_router)
if format_router:
    app.include_router(format_router)


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


# Drug interaction endpoints
class DrugInteractionRequest(BaseModel):
    """Request for drug interaction check."""

    drugs: list[str]
    patient_medications: list[str] | None = None


class DrugInteractionResponse(BaseModel):
    """Response with drug interactions."""

    success: bool
    interactions: list[dict] = []
    warnings: list[str] = []
    error: str | None = None


@app.post("/api/v1/drugs/check", response_model=DrugInteractionResponse)
async def check_drug_interactions(request: DrugInteractionRequest):
    """
    Check for drug-drug interactions.

    Provide a list of drugs to check interactions between them.
    Optionally provide patient's current medications to check
    against a new prescription.
    """
    if drug_checker is None:
        raise HTTPException(status_code=503, detail="Drug checker not initialized")

    try:
        interactions = []
        warnings = []

        if request.patient_medications and len(request.drugs) == 1:
            # Check new drug against current medications
            found = drug_checker.check_patient_medications(
                current_medications=request.patient_medications,
                new_medication=request.drugs[0],
            )
        else:
            # Check interactions between provided drugs
            found = drug_checker.check_multiple(request.drugs)

        for interaction in found:
            interactions.append({
                "drug1": interaction.drug1,
                "drug2": interaction.drug2,
                "severity": interaction.severity.value,
                "description": interaction.description,
                "management": interaction.management,
                "source": interaction.source,
            })
            warnings.append(drug_checker.format_warning(interaction))

        return DrugInteractionResponse(
            success=True,
            interactions=interactions,
            warnings=warnings,
        )

    except Exception as e:
        return DrugInteractionResponse(success=False, error=str(e))


@app.get("/api/v1/drugs/normalize/{drug_name}")
async def normalize_drug(drug_name: str):
    """
    Normalize a drug name to RxNorm standard.

    Returns standardized name, RxCUI, and drug classes.
    """
    if drug_checker is None:
        raise HTTPException(status_code=503, detail="Drug checker not initialized")

    try:
        info = drug_checker.normalize_drug(drug_name)

        return {
            "success": True,
            "original_name": info.original_name,
            "normalized_name": info.normalized_name,
            "rxcui": info.rxcui,
            "drug_classes": info.drug_classes,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# License endpoints
class LicenseActivateRequest(BaseModel):
    """Request to activate a license."""

    license_key: str


class LicenseStatusResponse(BaseModel):
    """License status response."""

    status: str
    tier: str | None = None
    message: str
    features: list[str] = []
    daily_limit: int = 0
    expires_at: str | None = None


@app.post("/api/v1/license/activate")
async def activate_license(request: LicenseActivateRequest):
    """Activate a license key."""
    if license_manager is None:
        raise HTTPException(status_code=503, detail="License manager not initialized")

    success, message = license_manager.activate_license(request.license_key)

    if success:
        return {"success": True, "message": message}
    else:
        raise HTTPException(status_code=400, detail=message)


@app.get("/api/v1/license/status", response_model=LicenseStatusResponse)
async def get_license_status():
    """Get current license status."""
    if license_manager is None:
        raise HTTPException(status_code=503, detail="License manager not initialized")

    status = license_manager.get_status()
    license_info = license_manager.get_license()
    message = license_manager.get_status_message()

    return LicenseStatusResponse(
        status=status.value,
        tier=license_info.tier.value if license_info else None,
        message=message,
        features=license_info.features if license_info else [],
        daily_limit=license_manager.get_daily_query_limit(),
        expires_at=license_info.expires_at.isoformat() if license_info else None,
    )


@app.get("/api/v1/license/check/{feature}")
async def check_feature_access(feature: str):
    """Check if a feature is accessible with current license."""
    if license_manager is None:
        raise HTTPException(status_code=503, detail="License manager not initialized")

    has_access = license_manager.check_feature_access(feature)

    return {
        "feature": feature,
        "has_access": has_access,
        "tier": license_manager.get_license().tier.value if license_manager.get_license() else "free",
    }


@app.post("/api/v1/license/verify")
async def verify_license_online():
    """Verify license with online server."""
    if license_manager is None:
        raise HTTPException(status_code=503, detail="License manager not initialized")

    success, message = await license_manager.verify_online()

    return {"success": success, "message": message}


@app.post("/api/v1/license/trial")
async def generate_trial(email: str):
    """Generate a trial license (development only)."""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Trial generation disabled in production")

    if license_manager is None:
        raise HTTPException(status_code=503, detail="License manager not initialized")

    license_key = license_manager.generate_trial_license(email, days=14)

    return {
        "success": True,
        "license_key": license_key,
        "message": "Trial license generated. Valid for 14 days.",
    }


# Serve static files for UI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

static_dir = Path(__file__).parent.parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_ui():
        """Serve the web UI."""
        return FileResponse(static_dir / "index.html")


# Run with: uvicorn src.api.app:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
