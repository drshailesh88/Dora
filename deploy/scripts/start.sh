#!/bin/bash
# Dora API Container Entrypoint Script
set -e

echo "Starting Dora Medical Knowledge Platform..."

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service ($host:$port)..."

    while ! nc -z "$host" "$port"; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: $service not available after $max_attempts attempts"
            exit 1
        fi
        echo "Attempt $attempt/$max_attempts: $service not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "$service is ready!"
}

# Wait for dependencies
if [ -n "$QDRANT_HOST" ]; then
    wait_for_service "${QDRANT_HOST:-qdrant}" "${QDRANT_PORT:-6333}" "Qdrant"
fi

if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's/redis:\/\/([^:]+).*/\1/')
    wait_for_service "${REDIS_HOST:-redis}" 6379 "Redis"
fi

if [ -n "$NEO4J_URI" ]; then
    NEO4J_HOST=$(echo "$NEO4J_URI" | sed -E 's/bolt:\/\/([^:]+).*/\1/')
    wait_for_service "${NEO4J_HOST:-neo4j}" 7687 "Neo4j"
fi

if [ -n "$POSTGRES_HOST" ]; then
    wait_for_service "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
fi

# Download embedding models if not present
echo "Checking embedding models..."
python -c "
from sentence_transformers import SentenceTransformer
import os

model_name = os.getenv('EMBEDDING_MODEL', 'pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb')
print(f'Loading model: {model_name}')
try:
    model = SentenceTransformer(model_name)
    print('Model loaded successfully!')
except Exception as e:
    print(f'Warning: Could not load model: {e}')
"

# Run database migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Create necessary directories
mkdir -p /app/data/uploads /app/logs

# Set permissions
chown -R dora:dora /app/data /app/logs 2>/dev/null || true

echo "Starting application..."

# Execute the main command
exec "$@"
