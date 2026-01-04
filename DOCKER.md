# Docker Infrastructure for Dora

This document provides details about the Docker setup for the Dora Medical Knowledge Platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (Reverse Proxy)                │
│                    Port 80/443 → Port 8000                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Dora API (FastAPI)                      │
│                         Port 8000                            │
└─────────────────────────────────────────────────────────────┘
         ↓                ↓                ↓
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│    Qdrant     │  │    Neo4j     │  │    Redis     │
│  Vector DB    │  │   Graph DB   │  │    Cache     │
│   Port 6333   │  │   Port 7687  │  │  Port 6379   │
└───────────────┘  └──────────────┘  └──────────────┘
```

## Files Structure

```
Dora/
├── Dockerfile                          # Multi-stage production image
├── .dockerignore                       # Files to exclude from build
├── requirements.txt                    # Python dependencies
├── docker-compose.yml                  # Development configuration
├── docker-compose.prod.yml            # Production overrides
│
├── deploy/
│   ├── nginx.conf                      # Reverse proxy configuration
│   ├── supervisord.conf               # Process management
│   ├── init.sql                       # Database initialization
│   ├── scripts/
│   │   ├── start.sh                   # Container entrypoint
│   │   ├── healthcheck.sh             # Health check script
│   │   └── backup.sh                  # Backup script
│
├── monitoring/
│   ├── docker-compose.monitoring.yml   # Monitoring stack
│   ├── prometheus.yml                  # Metrics collection
│   ├── grafana/                        # Dashboards
│   └── alertmanager.yml                # Alert routing
│
└── kubernetes/
    ├── deployment.yaml                 # K8s deployments
    ├── service.yaml                    # K8s services
    ├── ingress.yaml                    # K8s ingress
    └── configmap.yaml                  # Configuration
```

## Docker Images

### Base Image Layers

1. **Builder Stage** (`python:3.11-slim`):
   - Installs build dependencies
   - Compiles Python packages
   - Creates optimized wheels

2. **Runtime Stage** (`python:3.11-slim`):
   - Minimal runtime dependencies
   - Non-root user for security
   - Health checks enabled

### Image Sizes

- **Builder**: ~2.5 GB (not pushed)
- **Runtime**: ~1.8 GB (pushed to registry)

## Services

### 1. API Service

**Image**: `dora-api:latest`

**Environment Variables**:
```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
QDRANT_HOST=qdrant
NEO4J_URI=bolt://neo4j:7687
REDIS_URL=redis://redis:6379/0
```

**Volumes**:
- `./data:/app/data` - Persistent data
- `./logs:/app/logs` - Application logs

**Resources** (Production):
- CPU: 2-4 cores
- Memory: 4-8 GB

### 2. Qdrant (Vector Database)

**Image**: `qdrant/qdrant:v1.7.4`

**Ports**:
- 6333 - HTTP API
- 6334 - gRPC

**Volume**: `qdrant_data:/qdrant/storage`

**Resources**:
- CPU: 1-2 cores
- Memory: 2-4 GB

### 3. Neo4j (Graph Database)

**Image**: `neo4j:5-community`

**Ports**:
- 7474 - HTTP
- 7687 - Bolt

**Volume**: `neo4j_data:/data`

**Resources**:
- CPU: 1-2 cores
- Memory: 3-6 GB

### 4. Redis (Cache)

**Image**: `redis:7-alpine`

**Port**: 6379

**Volume**: `redis_data:/data`

**Resources**:
- CPU: 0.5-1 core
- Memory: 1-2 GB

### 5. PostgreSQL (Optional)

**Image**: `postgres:15-alpine`

**Port**: 5432

**Volume**: `postgres_data:/var/lib/postgresql/data`

### 6. Nginx (Reverse Proxy)

**Image**: `nginx:alpine`

**Ports**:
- 80 - HTTP
- 443 - HTTPS

**Volumes**:
- `./deploy/nginx.conf:/etc/nginx/nginx.conf`
- `./deploy/ssl:/etc/nginx/ssl`

## Usage

### Development

```bash
# Start basic stack
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild after code changes
docker-compose build api
docker-compose restart api

# Stop services
docker-compose down
```

### Production

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale API service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=3

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### With Monitoring

```bash
# Start full stack with monitoring
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f monitoring/docker-compose.monitoring.yml \
  up -d

# Access Grafana
open http://localhost:3000
```

## Networking

### Default Network

- **Name**: `dora-network`
- **Driver**: bridge
- **Subnet**: 172.28.0.0/16

### Service Discovery

Services can communicate using service names:
```python
# In application code
QDRANT_HOST = "qdrant"  # Not "localhost"
NEO4J_URI = "bolt://neo4j:7687"
REDIS_URL = "redis://redis:6379/0"
```

## Volumes

### Named Volumes

All data is stored in Docker-managed volumes:

```bash
# List volumes
docker volume ls | grep dora

# Inspect volume
docker volume inspect dora_qdrant_data

# Backup volume
docker run --rm -v dora_qdrant_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/qdrant-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v dora_qdrant_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/qdrant-backup.tar.gz -C /data
```

### Bind Mounts

Development uses bind mounts for hot-reload:
```yaml
volumes:
  - ./src:/app/src:ro  # Read-only source code
  - ./data:/app/data   # Persistent data
  - ./logs:/app/logs   # Application logs
```

## Health Checks

### API Health Check

```bash
# Check endpoint
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "version": "0.1.0",
  "has_cloud_llm": true,
  "has_reranker": true
}
```

### Docker Health Checks

All services have built-in health checks:

```bash
# View health status
docker-compose ps

# Service is healthy when status shows "(healthy)"
```

## Resource Limits

### Development

No limits - uses all available resources

### Production

Defined in `docker-compose.prod.yml`:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
```

## Logging

### Log Drivers

Production uses JSON file logging with rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# With timestamps
docker-compose logs -f -t api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Log Aggregation

Use Loki for centralized logging:

```bash
# Start Loki and Promtail
docker-compose -f monitoring/docker-compose.monitoring.yml up -d loki promtail

# Query logs in Grafana
# LogQL: {job="dora-api"} |= "error"
```

## Security

### Non-Root User

API runs as non-root user `dora`:

```dockerfile
RUN groupadd -r dora && useradd -r -g dora dora
USER dora
```

### Secrets Management

Never commit secrets to Git:

```bash
# Generate secure secrets
openssl rand -hex 32

# Use environment files (gitignored)
cp .env.example .env
nano .env
```

### Network Isolation

Services are isolated in a custom network:

```yaml
networks:
  dora-network:
    driver: bridge
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check if port is in use
lsof -i :8000

# Remove old containers
docker-compose down -v
docker-compose up -d
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.prod.yml
# Or increase Docker Desktop memory allocation
```

### Permission Errors

```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) data/ logs/

# Or run container as root temporarily
docker-compose run --user root api bash
```

### Network Issues

```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d

# Test connectivity
docker-compose exec api ping qdrant
docker-compose exec api curl http://qdrant:6333/healthz
```

## Best Practices

1. **Use multi-stage builds** - Reduce image size
2. **Pin image versions** - Ensure reproducibility
3. **Health checks** - Enable auto-recovery
4. **Resource limits** - Prevent resource exhaustion
5. **Log rotation** - Prevent disk fill
6. **Named volumes** - Easier to manage
7. **Environment files** - Never commit secrets
8. **Regular backups** - Automate with cron

## CI/CD Integration

See `.github/workflows/build.yml` for automated builds and deployments.

```bash
# Build and push to registry
docker build -t ghcr.io/drshailesh88/dora:latest .
docker push ghcr.io/drshailesh88/dora:latest
```

## Maintenance

### Updating Images

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Remove old images
docker image prune -a
```

### Cleaning Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (careful!)
docker-compose down -v

# Remove unused images
docker image prune -a

# Full cleanup
docker system prune -a --volumes
```

---

For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).
