# Dora Deployment Guide

Complete guide for deploying the Dora Medical Knowledge Platform in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB+ SSD
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Python 3.11+ (for local development)

For Kubernetes:
- kubectl 1.24+
- Helm 3.8+ (optional)
- Access to a Kubernetes cluster (1.24+)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/drshailesh88/Dora.git
cd Dora
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...

# Security
SECRET_KEY=<generate-random-key>

# Database passwords (change defaults!)
NEO4J_PASSWORD=secure_password_here
POSTGRES_PASSWORD=secure_password_here
REDIS_PASSWORD=secure_password_here
```

### 3. Start Services

```bash
# Basic setup (API + Qdrant + Redis)
docker-compose up -d

# Full setup (includes Neo4j, PostgreSQL, Nginx)
docker-compose --profile full up -d
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api
```

Access the services:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Neo4j Browser**: http://localhost:7474

---

## Development Deployment

### Using Docker Compose

```bash
# Start with hot-reload enabled
docker-compose up -d

# View logs
docker-compose logs -f api

# Restart after code changes (if needed)
docker-compose restart api
```

The API container mounts `./src` as read-only, so code changes will be reflected automatically with uvicorn's auto-reload.

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,voice,ui]"

# Start services (Qdrant, Redis, etc.)
docker-compose up qdrant redis -d

# Run API locally
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# In Docker
docker-compose exec api pytest tests/ -v

# Locally
pytest tests/ -v --cov=src
```

---

## Production Deployment

### Option 1: Docker Compose (Single Server)

```bash
# Build production image
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose ps
```

**Important Production Steps:**

1. **Update secrets in `.env`**:
   ```bash
   # Generate secure secret key
   openssl rand -hex 32
   ```

2. **Configure SSL certificates**:
   ```bash
   # Place certificates in deploy/ssl/
   cp your-cert.pem deploy/ssl/cert.pem
   cp your-key.pem deploy/ssl/key.pem
   ```

3. **Setup backup cron job**:
   ```bash
   # Add to crontab
   0 2 * * * /path/to/Dora/deploy/scripts/backup.sh
   ```

4. **Enable monitoring**:
   ```bash
   docker-compose -f docker-compose.yml \
                  -f docker-compose.prod.yml \
                  -f monitoring/docker-compose.monitoring.yml up -d
   ```

### Option 2: AWS ECS

1. **Build and push image**:
   ```bash
   # Login to ECR
   aws ecr get-login-password --region ap-south-1 | \
     docker login --username AWS --password-stdin <account>.dkr.ecr.ap-south-1.amazonaws.com

   # Build and push
   docker build -t dora-api .
   docker tag dora-api:latest <account>.dkr.ecr.ap-south-1.amazonaws.com/dora-api:latest
   docker push <account>.dkr.ecr.ap-south-1.amazonaws.com/dora-api:latest
   ```

2. **Create ECS resources** (using AWS Console or Terraform)
   - Create ECS Cluster
   - Create Task Definition (see production resource limits in docker-compose.prod.yml)
   - Create Service with Application Load Balancer
   - Configure Auto Scaling

3. **Deploy**:
   ```bash
   aws ecs update-service \
     --cluster dora-production \
     --service dora-api \
     --force-new-deployment
   ```

---

## Kubernetes Deployment

### 1. Prepare Cluster

```bash
# Create namespace
kubectl create namespace dora

# Or apply the manifest
kubectl apply -f kubernetes/namespace.yaml
```

### 2. Configure Secrets

```bash
# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Create secrets
kubectl create secret generic dora-secrets \
  --from-literal=SECRET_KEY=$SECRET_KEY \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=COHERE_API_KEY=... \
  --from-literal=NEO4J_PASSWORD=... \
  --from-literal=POSTGRES_PASSWORD=... \
  --namespace=dora

# Verify
kubectl get secrets -n dora
```

### 3. Deploy Resources

```bash
# Apply in order
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml

# Or apply all at once
kubectl apply -f kubernetes/
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n dora

# Check services
kubectl get svc -n dora

# View logs
kubectl logs -f deployment/dora-api -n dora

# Check ingress
kubectl get ingress -n dora
```

### 5. Scale Deployment

```bash
# Manual scaling
kubectl scale deployment dora-api --replicas=5 -n dora

# HPA will automatically scale based on CPU/memory
kubectl get hpa -n dora
```

### 6. Update Deployment

```bash
# Update image
kubectl set image deployment/dora-api \
  api=ghcr.io/drshailesh88/dora:v1.2.0 \
  -n dora

# Or apply updated manifests
kubectl apply -f kubernetes/deployment.yaml

# Monitor rollout
kubectl rollout status deployment/dora-api -n dora
```

---

## Monitoring Setup

### 1. Start Monitoring Stack

```bash
docker-compose -f docker-compose.yml \
               -f monitoring/docker-compose.monitoring.yml up -d
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (change on first login)

- **Prometheus**: http://localhost:9090

- **AlertManager**: http://localhost:9093

### 3. Configure Alerts

Edit `monitoring/alertmanager.yml` with your notification channels:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@docassist.in'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#dora-critical'
```

### 4. View Logs (Loki)

```bash
# Query logs in Grafana
# Add Loki as datasource, then use LogQL:

{job="dora-api"} |= "error"
```

---

## Backup and Restore

### Automated Backups

```bash
# Setup cron job
crontab -e

# Add line for daily backup at 2 AM
0 2 * * * /path/to/Dora/deploy/scripts/backup.sh
```

### Manual Backup

```bash
# Run backup script
./deploy/scripts/backup.sh

# Backups saved to /backup by default
# Configure BACKUP_DIR environment variable to change location
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore volume
docker run --rm \
  -v dora_qdrant_data:/data \
  -v /backup:/backup \
  alpine \
  tar xzf /backup/qdrant_data_20260104_020000.tar.gz -C /data

# Restart services
docker-compose up -d
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Secret key for JWT | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `API_HOST` | API bind host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `QDRANT_HOST` | Qdrant hostname | `qdrant` |
| `NEO4J_URI` | Neo4j connection URI | `bolt://neo4j:7687` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |

See `.env.example` for complete list.

---

## Troubleshooting

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Port already in use
lsof -i :8000
kill -9 <PID>

# 2. Dependencies not ready
docker-compose logs qdrant
docker-compose restart api
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit memory in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Database Connection Errors

```bash
# Check if services are running
docker-compose ps

# Test connectivity
docker-compose exec api curl -f http://qdrant:6333/healthz
docker-compose exec api redis-cli -h redis ping
```

### Slow Queries

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# Enable query profiling in logs
export DEBUG=true
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate secure SECRET_KEY
- [ ] Setup SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable authentication on databases
- [ ] Setup VPC/network isolation (cloud deployments)
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Setup intrusion detection
- [ ] Regular security updates

---

## Performance Tuning

### API Optimization

```yaml
# docker-compose.prod.yml
command: >
  gunicorn src.api.app:app
  --workers 4
  --worker-class uvicorn.workers.UvicornWorker
  --timeout 120
  --keep-alive 5
```

### Database Tuning

**Qdrant**:
```yaml
environment:
  - QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS=4
```

**PostgreSQL**:
```bash
shared_buffers=256MB
effective_cache_size=1GB
```

### Caching

```python
# Enable Redis caching in application
REDIS_URL=redis://redis:6379/0
```

---

## Support

- **Documentation**: https://github.com/drshailesh88/Dora
- **Issues**: https://github.com/drshailesh88/Dora/issues
- **Email**: dev@docassist.in

---

## License

Proprietary - DocAssist © 2026
