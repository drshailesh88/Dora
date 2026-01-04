# Dora - Medical Knowledge Platform
# Multi-stage Docker build for production deployment

# ============================================================================
# Stage 1: Builder - Install dependencies and build wheels
# ============================================================================
FROM python:3.11-slim as builder

LABEL maintainer="DocAssist <dev@docassist.in>"
LABEL description="Dora Medical Knowledge Platform Builder"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="DocAssist <dev@docassist.in>"
LABEL description="Dora Medical Knowledge Platform"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DORA_HOME=/app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For ML libraries
    libgomp1 \
    libglib2.0-0 \
    # For health checks
    curl \
    # For PDF processing
    poppler-utils \
    tesseract-ocr \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r dora && \
    useradd -r -g dora -d /app -s /bin/bash dora

# Create app directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=dora:dora /opt/venv /opt/venv

# Copy application code
COPY --chown=dora:dora . .

# Create necessary directories
RUN mkdir -p \
    /app/data \
    /app/data/qdrant \
    /app/data/chromadb \
    /app/data/uploads \
    /app/logs \
    && chown -R dora:dora /app

# Switch to non-root user
USER dora

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - can be overridden in docker-compose
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
