# Dora Support Runbook

**Version:** 1.0
**Last Updated:** January 2026
**Audience:** Support Staff, System Administrators, DevOps

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Health Checks](#health-checks)
3. [Log Locations](#log-locations)
4. [Common Issues & Solutions](#common-issues--solutions)
5. [Database Operations](#database-operations)
6. [Emergency Procedures](#emergency-procedures)
7. [Performance Troubleshooting](#performance-troubleshooting)
8. [Security Incidents](#security-incidents)

---

## System Overview

### Architecture Summary

Dora is a medical knowledge platform with the following core components:

```
┌─────────────────────────────────────────────────────┐
│                   NGINX (Port 80/443)               │
│                  (Reverse Proxy)                    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              FastAPI App (Port 8000)                │
│           (Medical Query Pipeline)                  │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼───┐  ┌───▼────┐  ┌──▼────┐
    │ Qdrant │  │ Redis  │  │Neo4j  │
    │ :6333  │  │ :6379  │  │ :7687 │
    └────────┘  └────────┘  └───────┘
```

### Key Components

| Component | Purpose | Default Port | Health Check |
|-----------|---------|--------------|--------------|
| **FastAPI API** | Main application server | 8000 | `GET /health` |
| **Qdrant** | Vector database for medical embeddings | 6333 (HTTP), 6334 (gRPC) | `GET http://localhost:6333/` |
| **Neo4j** | Graph database for medical relationships (UMLS) | 7474 (HTTP), 7687 (Bolt) | `http://localhost:7474` |
| **Redis** | Cache and session storage | 6379 | `redis-cli ping` |
| **PostgreSQL** | User data, analytics (production) | 5432 | `pg_isready` |
| **Nginx** | Reverse proxy and load balancer | 80, 443 | Check process status |

### Service Dependencies

- **API** depends on: Qdrant (required), Redis (required), Neo4j (optional)
- **Qdrant** depends on: None (standalone)
- **Neo4j** depends on: None (standalone)
- **Redis** depends on: None (standalone)

---

## Health Checks

### 1. API Health Endpoint

**Endpoint:** `GET /health`

**Command:**
```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "has_cloud_llm": true,
  "has_reranker": true
}
```

**What to check:**
- `status`: Should be `"healthy"`
- `has_cloud_llm`: `true` if OpenAI/Anthropic API keys are configured
- `has_reranker`: `true` if Cohere API key is configured

**If unhealthy:**
1. Check Docker container: `docker ps | grep dora-api`
2. Check API logs: `docker logs dora-api --tail 100`
3. Verify environment variables in `.env`

### 2. Qdrant Vector Database

**Web UI:** `http://localhost:6333/dashboard`

**Command:**
```bash
curl http://localhost:6333/
```

**Expected Output:**
```json
{
  "title": "qdrant - vector search engine",
  "version": "1.7.4"
}
```

**List Collections:**
```bash
curl http://localhost:6333/collections
```

**If unhealthy:**
1. Check container: `docker ps | grep dora-qdrant`
2. Check logs: `docker logs dora-qdrant --tail 100`
3. Verify storage: `docker volume inspect dora_qdrant_data`
4. Restart: `docker restart dora-qdrant`

### 3. Neo4j Graph Database

**Web UI:** `http://localhost:7474`

**Login:**
- Username: `neo4j`
- Password: `docassist123` (default, change in production!)

**Command:**
```bash
# Check connection via Cypher shell
docker exec -it dora-neo4j cypher-shell -u neo4j -p docassist123 "RETURN 'OK' AS status;"
```

**Expected Output:**
```
+----------+
| status   |
+----------+
| "OK"     |
+----------+
```

**If unhealthy:**
1. Check container: `docker ps | grep dora-neo4j`
2. Check logs: `docker logs dora-neo4j --tail 100`
3. Check memory: Neo4j requires minimum 2GB heap
4. Restart: `docker restart dora-neo4j`

### 4. Redis Cache

**Command:**
```bash
docker exec -it dora-redis redis-cli ping
```

**Expected Output:**
```
PONG
```

**Check memory usage:**
```bash
docker exec -it dora-redis redis-cli INFO memory | grep used_memory_human
```

**If unhealthy:**
1. Check container: `docker ps | grep dora-redis`
2. Check logs: `docker logs dora-redis --tail 100`
3. Check memory: `docker stats dora-redis`
4. Clear cache if needed: `docker exec -it dora-redis redis-cli FLUSHALL`

### 5. PostgreSQL Database (Production)

**Command:**
```bash
docker exec -it dora-postgres pg_isready -U dora
```

**Expected Output:**
```
/var/run/postgresql:5432 - accepting connections
```

**Test connection:**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c "SELECT version();"
```

**If unhealthy:**
1. Check container: `docker ps | grep dora-postgres`
2. Check logs: `docker logs dora-postgres --tail 100`
3. Check disk space: `df -h`
4. Check connections:
```bash
docker exec -it dora-postgres psql -U dora -d dora -c "SELECT count(*) FROM pg_stat_activity;"
```

### 6. All Services Status

**Quick check all Docker services:**
```bash
docker-compose ps
```

**Expected Output:**
```
NAME                IMAGE               STATUS
dora-api            dora-api:latest     Up
dora-qdrant         qdrant/qdrant       Up (healthy)
dora-redis          redis:7-alpine      Up (healthy)
dora-neo4j          neo4j:5-community   Up
dora-postgres       postgres:15-alpine  Up (healthy)
dora-nginx          nginx:alpine        Up
```

### Monitoring Dashboard

If Grafana is configured:
- **URL:** `http://localhost:3000`
- **Default login:** admin / admin

**Key metrics to monitor:**
- API response times (p50, p95, p99)
- Query success rate
- Qdrant query latency
- Redis cache hit rate
- CPU and memory usage per container

---

## Log Locations

### 1. API Logs

**Docker container logs:**
```bash
# Last 100 lines
docker logs dora-api --tail 100

# Follow in real-time
docker logs dora-api -f

# Since last 1 hour
docker logs dora-api --since 1h

# Save to file
docker logs dora-api > /tmp/dora-api.log 2>&1
```

**Application logs (if mounted volume):**
```bash
# FastAPI application logs
tail -f /app/logs/dora.log

# Error logs only
grep ERROR /app/logs/dora.log

# Query logs
grep "query=" /app/logs/dora.log
```

**Log format:**
```
2026-01-05 10:30:45 INFO [src.api.app] Query received: What is diabetes?
2026-01-05 10:30:47 INFO [src.retrieval.hybrid] Retrieved 20 chunks
2026-01-05 10:30:48 INFO [src.llm.synthesizer] Generated answer (confidence: high)
```

### 2. Nginx Logs

**Access logs:**
```bash
docker exec dora-nginx tail -f /var/log/nginx/access.log
```

**Error logs:**
```bash
docker exec dora-nginx tail -f /var/log/nginx/error.log
```

**If using volume mount:**
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

**Search for specific client IP:**
```bash
docker exec dora-nginx grep "192.168.1.100" /var/log/nginx/access.log
```

### 3. Database Logs

**Qdrant logs:**
```bash
docker logs dora-qdrant --tail 100
```

**Neo4j logs:**
```bash
docker logs dora-neo4j --tail 100

# Or inside container
docker exec dora-neo4j tail -f /logs/query.log
docker exec dora-neo4j tail -f /logs/debug.log
```

**PostgreSQL logs:**
```bash
docker logs dora-postgres --tail 100

# Slow query log
docker exec -it dora-postgres psql -U dora -d dora -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Redis logs:**
```bash
docker logs dora-redis --tail 100
```

### 4. Log Analysis Examples

**Find all errors in last hour:**
```bash
docker logs dora-api --since 1h 2>&1 | grep -i error
```

**Count queries by hour:**
```bash
docker logs dora-api | grep "query=" | awk '{print $1" "$2}' | cut -d: -f1 | sort | uniq -c
```

**Find slow queries (>5 seconds):**
```bash
docker logs dora-api | grep "latency=" | awk '$NF > 5000'
```

---

## Common Issues & Solutions

### Authentication Issues

#### Issue 1: "Token expired" errors

**Symptoms:**
- Users get 401 Unauthorized errors
- Error message: `"Token has expired"`

**Diagnosis:**
```bash
# Check JWT configuration
docker exec dora-api env | grep JWT

# Check token expiry setting
docker exec dora-api env | grep ACCESS_TOKEN_EXPIRE_MINUTES
```

**Solution:**
1. Tokens expire after 30 minutes (default). This is expected behavior.
2. Frontend should automatically refresh tokens or prompt re-login.
3. To extend token lifetime (not recommended):
```bash
# Edit .env file
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Restart API
docker restart dora-api
```

**Prevention:**
- Implement token refresh mechanism in frontend
- Use refresh tokens for long-lived sessions

---

#### Issue 2: Login failures

**Symptoms:**
- User enters correct credentials but login fails
- Error: `"Invalid email or password"`

**Diagnosis:**
```bash
# Check if user exists
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT email, created_at FROM users WHERE email='user@example.com';"

# Check authentication logs
docker logs dora-api --tail 100 | grep "login"
```

**Common causes:**
1. **Password mismatch:** User forgot password
2. **Email typo:** Check for trailing spaces
3. **Account not activated:** Check user status
4. **Database connection issue:** Check PostgreSQL

**Solution:**

**Reset password manually:**
```bash
# Generate password hash
docker exec -it dora-api python3 -c "
from src.auth.password import hash_password
print(hash_password('NewPassword123'))
"

# Update in database
docker exec -it dora-postgres psql -U dora -d dora -c \
  "UPDATE users SET password_hash='<hash>' WHERE email='user@example.com';"
```

---

#### Issue 3: Password reset problems

**Symptoms:**
- Password reset email not received
- Reset link expired

**Diagnosis:**
```bash
# Check email service configuration
docker exec dora-api env | grep SENDGRID

# Check notification logs
docker logs dora-api | grep "password_reset"
```

**Solution:**
1. **Email not configured:**
```bash
# Verify SENDGRID_API_KEY in .env
cat .env | grep SENDGRID_API_KEY

# Test email service
docker exec dora-api python3 -c "
from src.notifications.email import EmailService
service = EmailService()
service.send_test_email('admin@example.com')
"
```

2. **Reset token expired (default: 1 hour):**
- Generate new reset link
- User must request new password reset

---

### Query Issues

#### Issue 4: Slow query responses

**Symptoms:**
- Queries take >10 seconds to respond
- Users complain about timeout

**Diagnosis:**
```bash
# Check API response times
docker logs dora-api | grep "latency=" | tail -20

# Check Qdrant query performance
curl http://localhost:6333/metrics | grep query_duration

# Check CPU and memory
docker stats dora-api dora-qdrant
```

**Common causes:**
1. **Qdrant overloaded:** Too many concurrent queries
2. **Large result set:** Retrieving too many documents
3. **LLM API slow:** External API (OpenAI/Anthropic) timeout
4. **Cold start:** First query after restart is slow

**Solution:**

**1. Reduce top_k parameter:**
```bash
# Default is 20, try reducing to 10
# Users can adjust in query request:
# "top_k": 10
```

**2. Check Qdrant collection size:**
```bash
curl http://localhost:6333/collections/medical_knowledge | jq '.result.vectors_count'
```

**3. Enable Redis caching:**
```bash
# Verify Redis is working
docker exec dora-redis redis-cli INFO stats | grep keyspace

# Check cache hit rate
docker exec dora-redis redis-cli INFO stats | grep hit_rate
```

**4. Switch to local LLM for faster responses:**
```bash
# Edit .env
USE_CLOUD_LLM=false
USE_LOCAL_LLM=true

# Requires Ollama running
curl http://localhost:11434/api/tags

# Restart API
docker restart dora-api
```

---

#### Issue 5: Empty results / No answers returned

**Symptoms:**
- Query returns: `"No relevant information found"`
- Empty citations array

**Diagnosis:**
```bash
# Check if Qdrant has indexed documents
curl http://localhost:6333/collections/medical_knowledge

# Check collection count
curl http://localhost:6333/collections/medical_knowledge | jq '.result.points_count'

# Test query directly on Qdrant
curl -X POST http://localhost:6333/collections/medical_knowledge/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 5}'
```

**Common causes:**
1. **No documents ingested:** Knowledge base is empty
2. **Wrong collection name:** Check collection exists
3. **Embedding mismatch:** Query embedding doesn't match indexed embeddings
4. **Too restrictive threshold:** Similarity threshold too high

**Solution:**

**1. Check if documents are indexed:**
```bash
# List all collections
curl http://localhost:6333/collections

# Check specific collection
curl http://localhost:6333/collections/medical_knowledge | jq '.result.points_count'
```

**If count is 0:**
```bash
# Ingest documents
docker exec dora-api python3 -c "
from src.ingestion.pipeline import IngestionPipeline
pipeline = IngestionPipeline()
# Ingest sample text
pipeline.ingest_text('Diabetes mellitus is...', title='Diabetes Overview')
"
```

**2. Test embedding generation:**
```bash
docker exec dora-api python3 -c "
from src.embeddings.medical_embeddings import MedicalEmbeddings
embedder = MedicalEmbeddings()
vec = embedder.embed_query('What is diabetes?')
print(f'Embedding dimension: {len(vec)}')
"
```

**3. Lower similarity threshold (if configurable):**
- Check application code for threshold settings
- Default should work for most cases

---

#### Issue 6: LLM timeout errors

**Symptoms:**
- Error: `"Request to LLM timed out"`
- Error: `"Connection timeout"`

**Diagnosis:**
```bash
# Check LLM configuration
docker exec dora-api env | grep -E "OPENAI|ANTHROPIC|OLLAMA"

# Test LLM connection
docker exec dora-api python3 -c "
import os
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
print(openai.Model.list())
"
```

**Solution:**

**1. Verify API keys:**
```bash
# Check if keys are set
docker exec dora-api env | grep API_KEY

# Keys should start with 'sk-' (OpenAI) or 'sk-ant-' (Anthropic)
```

**2. Check internet connectivity:**
```bash
docker exec dora-api ping -c 3 api.openai.com
docker exec dora-api ping -c 3 api.anthropic.com
```

**3. Switch to local LLM:**
```bash
# Install Ollama first
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5:7b

# Update .env
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Restart API
docker restart dora-api
```

---

### Voice Issues

#### Issue 7: Wake word not detected

**Symptoms:**
- "Hey DocAssist" doesn't trigger voice assistant
- No response from voice agent

**Diagnosis:**
```bash
# Check if voice is enabled
docker exec dora-api env | grep VOICE_ENABLED

# Check logs for wake word detection
docker logs dora-api | grep "wake_word"

# Check microphone access (desktop app)
arecord -l  # Linux
```

**Solution:**

**1. Enable voice feature:**
```bash
# Edit .env
VOICE_ENABLED=true

# Restart
docker restart dora-api
```

**2. Adjust wake word threshold:**
```python
# In src/voice/agent.py, adjust threshold
wake_detector = WakeWordDetector(
    wake_words=["hey_docassist"],
    threshold=0.3  # Lower = more sensitive (default: 0.5)
)
```

**3. Test microphone:**
```bash
# Record test audio
arecord -d 5 -f cd test.wav

# Check if Whisper can transcribe
docker exec dora-api python3 -c "
import whisper
model = whisper.load_model('base.en')
result = model.transcribe('test.wav')
print(result['text'])
"
```

---

#### Issue 8: Poor transcription accuracy

**Symptoms:**
- Whisper STT transcribes medical terms incorrectly
- "Metformin" → "met for min"

**Diagnosis:**
```bash
# Check Whisper model size
docker exec dora-api env | grep WHISPER_MODEL

# Test transcription
docker exec dora-api python3 -c "
import whisper
model = whisper.load_model('base.en')
# Test with sample audio
"
```

**Solution:**

**1. Upgrade to larger Whisper model:**
```bash
# Edit .env
WHISPER_MODEL=medium.en  # or large

# Requires more RAM (medium: 5GB, large: 10GB)

# Restart
docker restart dora-api
```

**2. Add medical vocabulary fine-tuning:**
- Fine-tune Whisper on medical terminology
- Use post-processing to correct common medical terms

**3. Check audio quality:**
- Use noise-cancelling microphone
- Minimize background noise
- Speak clearly and closer to mic

---

#### Issue 9: TTS not working / No audio output

**Symptoms:**
- Voice agent doesn't speak response
- Silent response

**Diagnosis:**
```bash
# Check TTS configuration
docker logs dora-api | grep "tts"

# Test Piper TTS
docker exec dora-api python3 -c "
from src.voice.agent import DoraVoiceAgent
agent = DoraVoiceAgent()
agent.tts.say('This is a test')
"
```

**Solution:**

**1. Check audio output device:**
```bash
# List audio devices
aplay -l  # Linux
```

**2. Verify Piper installation:**
```bash
docker exec dora-api which piper
docker exec dora-api piper --version
```

**3. Test TTS manually:**
```bash
echo "Test message" | piper --model en_US-lessac-medium --output_file test.wav
aplay test.wav
```

---

### Offline Mode Issues

#### Issue 10: Sync not completing

**Symptoms:**
- Data not syncing between online/offline modes
- Sync stuck at "Syncing..."

**Diagnosis:**
```bash
# Check sync status
docker logs dora-api | grep "sync"

# Check Redis queue
docker exec dora-redis redis-cli LLEN sync_queue

# Check local SQLite database
sqlite3 /app/data/dora.db "SELECT COUNT(*) FROM sync_queue;"
```

**Solution:**

**1. Clear stuck sync queue:**
```bash
# Redis queue
docker exec dora-redis redis-cli DEL sync_queue

# SQLite queue
sqlite3 /app/data/dora.db "DELETE FROM sync_queue WHERE status='pending';"
```

**2. Force full re-sync:**
```bash
# Trigger full sync via API
curl -X POST http://localhost:8000/api/v1/sync/full \
  -H "Authorization: Bearer <token>"
```

**3. Check network connectivity:**
```bash
docker exec dora-api ping -c 3 api.dora.docassist.in
```

---

#### Issue 11: Data not available offline

**Symptoms:**
- App shows "No internet connection" error
- Queries fail in offline mode

**Diagnosis:**
```bash
# Check if ChromaDB has local data
ls -la /app/data/chroma/

# Check SQLite cache
sqlite3 /app/data/dora.db "SELECT COUNT(*) FROM query_cache;"

# Check local LLM
curl http://localhost:11434/api/tags
```

**Solution:**

**1. Pre-download data for offline use:**
```bash
# Run offline preparation script
docker exec dora-api python3 -c "
from src.offline import prepare_offline_data
prepare_offline_data(collections=['medical_knowledge'])
"
```

**2. Ensure Ollama is running:**
```bash
# Start Ollama
systemctl start ollama

# Pull required model
ollama pull qwen2.5:7b
```

**3. Populate local cache:**
```bash
# Trigger cache warming
curl -X POST http://localhost:8000/api/v1/cache/warm
```

---

#### Issue 12: Cache corruption

**Symptoms:**
- Queries return corrupted data
- Error: `"Database malformed"`

**Diagnosis:**
```bash
# Check SQLite integrity
sqlite3 /app/data/dora.db "PRAGMA integrity_check;"

# Check ChromaDB
ls -la /app/data/chroma/
```

**Solution:**

**1. Rebuild cache:**
```bash
# Backup first!
cp /app/data/dora.db /app/data/dora.db.backup

# Delete corrupted database
rm /app/data/dora.db

# Restart API (will recreate)
docker restart dora-api

# Re-sync data
curl -X POST http://localhost:8000/api/v1/sync/full
```

**2. Clear ChromaDB and re-index:**
```bash
# Backup
cp -r /app/data/chroma /app/data/chroma.backup

# Delete
rm -rf /app/data/chroma/*

# Re-ingest documents
docker exec dora-api python3 src/ingestion/reingest.py
```

---

### Mobile App Issues

#### Issue 13: Push notifications not working

**Symptoms:**
- Users not receiving notifications
- No alerts for guideline updates

**Diagnosis:**
```bash
# Check notification service
docker logs dora-api | grep "notification"

# Check FCM/APNS configuration
docker exec dora-api env | grep -E "FCM|APNS"

# Check user device tokens
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT device_token FROM device_tokens WHERE user_id='<user_id>';"
```

**Solution:**

**1. Verify FCM/APNS credentials:**
```bash
# Android (FCM)
docker exec dora-api env | grep FCM_SERVER_KEY

# iOS (APNS)
docker exec dora-api env | grep APNS_CERT_PATH
ls -la /app/certs/apns.p8
```

**2. Test notification sending:**
```bash
docker exec dora-api python3 -c "
from src.notifications.push import PushNotificationService
service = PushNotificationService()
service.send_test_notification('<device_token>')
"
```

**3. Check notification permissions:**
- User must grant notification permissions in mobile app
- Re-install app and accept permissions

---

#### Issue 14: App crashes on launch

**Symptoms:**
- Mobile app crashes immediately after opening
- Error logs show crash report

**Common causes:**
1. Corrupted local database
2. Missing permissions
3. Outdated app version
4. Backend API unreachable

**Solution:**

**1. Clear app data:**
- Android: Settings → Apps → Dora → Clear Data
- iOS: Uninstall and reinstall

**2. Check API reachability:**
```bash
# From mobile device, test API
curl https://api.dora.docassist.in/health
```

**3. Check app version compatibility:**
```bash
# API version
curl https://api.dora.docassist.in/health | jq '.version'

# Compare with minimum supported version in app
```

**4. Review crash logs:**
- Android: `adb logcat | grep Dora`
- iOS: Xcode → Devices → View Device Logs

---

#### Issue 15: Sync failures between mobile and server

**Symptoms:**
- Changes on mobile not reflected on web
- Error: "Sync failed"

**Diagnosis:**
```bash
# Check sync endpoint
curl -X GET http://localhost:8000/api/v1/sync/status \
  -H "Authorization: Bearer <token>"

# Check sync logs
docker logs dora-api | grep "sync.*mobile"
```

**Solution:**

**1. Force manual sync:**
```bash
# Trigger sync from API
curl -X POST http://localhost:8000/api/v1/sync/trigger \
  -H "Authorization: Bearer <token>" \
  -d '{"device_id": "<device_id>"}'
```

**2. Check authentication:**
- Ensure user is logged in on mobile
- Token might have expired → Re-login required

**3. Resolve conflicts:**
```bash
# Check for sync conflicts
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT * FROM sync_conflicts WHERE resolved=false;"

# Manually resolve (keep server version)
docker exec -it dora-postgres psql -U dora -d dora -c \
  "UPDATE sync_conflicts SET resolved=true, resolution='server' WHERE id=<conflict_id>;"
```

---

### Payment Issues

#### Issue 16: Razorpay webhook failures

**Symptoms:**
- Payment successful but subscription not activated
- Error: `"Webhook signature verification failed"`

**Diagnosis:**
```bash
# Check webhook logs
docker logs dora-api | grep "webhook"

# Check Razorpay configuration
docker exec dora-api env | grep RAZORPAY

# Check webhook endpoint accessibility
curl -X POST http://localhost:8000/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

**Solution:**

**1. Verify webhook secret:**
```bash
# Check secret in .env matches Razorpay dashboard
cat .env | grep RAZORPAY_WEBHOOK_SECRET

# Update if needed
RAZORPAY_WEBHOOK_SECRET=<secret_from_dashboard>

# Restart
docker restart dora-api
```

**2. Check webhook URL configuration:**
- Login to Razorpay Dashboard
- Go to Settings → Webhooks
- Verify URL: `https://api.dora.docassist.in/api/v1/payments/webhook`
- Ensure events are enabled: `payment.captured`, `payment.failed`, `subscription.activated`

**3. Manually activate subscription (temporary fix):**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "UPDATE subscriptions SET status='active' WHERE payment_id='<razorpay_payment_id>';"
```

---

#### Issue 17: Subscription not activating

**Symptoms:**
- User paid but still sees "Free tier" in app
- Features locked despite payment

**Diagnosis:**
```bash
# Check subscription status
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT * FROM subscriptions WHERE user_id='<user_id>' ORDER BY created_at DESC LIMIT 1;"

# Check payment status
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT * FROM payments WHERE user_id='<user_id>' ORDER BY created_at DESC LIMIT 1;"
```

**Solution:**

**1. Verify payment received in Razorpay:**
- Login to Razorpay Dashboard
- Check payment status

**2. Manually activate subscription:**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "UPDATE users SET subscription_tier='premium' WHERE id='<user_id>';"

docker exec -it dora-postgres psql -U dora -d dora -c \
  "INSERT INTO subscriptions (user_id, plan, status, start_date, end_date)
   VALUES ('<user_id>', 'premium', 'active', NOW(), NOW() + INTERVAL '1 month');"
```

**3. Trigger cache refresh:**
```bash
# Clear user cache
docker exec dora-redis redis-cli DEL "user:<user_id>"
```

---

#### Issue 18: Invoice generation errors

**Symptoms:**
- User doesn't receive invoice email
- Error downloading invoice PDF

**Diagnosis:**
```bash
# Check invoice generation logs
docker logs dora-api | grep "invoice"

# Check if invoice exists
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT * FROM invoices WHERE user_id='<user_id>';"
```

**Solution:**

**1. Regenerate invoice:**
```bash
docker exec dora-api python3 -c "
from src.payments.invoice import InvoiceGenerator
generator = InvoiceGenerator()
invoice_path = generator.generate('<payment_id>')
print(f'Invoice saved to: {invoice_path}')
"
```

**2. Resend invoice email:**
```bash
docker exec dora-api python3 -c "
from src.notifications.email import EmailService
from src.payments.invoice import InvoiceGenerator

email_service = EmailService()
invoice_gen = InvoiceGenerator()

invoice_path = invoice_gen.get_invoice_path('<payment_id>')
email_service.send_invoice('<user_email>', invoice_path)
"
```

---

## Database Operations

### PostgreSQL Operations

#### Connect to Database

```bash
# Using psql in container
docker exec -it dora-postgres psql -U dora -d dora

# From host (if psql installed)
psql -h localhost -U dora -d dora
```

#### Common Queries

**List all tables:**
```sql
\dt
```

**Check user count:**
```sql
SELECT COUNT(*) FROM users;
```

**Find user by email:**
```sql
SELECT id, email, name, subscription_tier, created_at
FROM users
WHERE email = 'user@example.com';
```

**Check active subscriptions:**
```sql
SELECT u.email, s.plan, s.status, s.start_date, s.end_date
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.status = 'active';
```

**Query usage statistics:**
```sql
SELECT DATE(created_at) as date, COUNT(*) as query_count
FROM queries
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

**Find slow queries:**
```sql
SELECT question, latency_ms, created_at
FROM queries
WHERE latency_ms > 5000
ORDER BY latency_ms DESC
LIMIT 10;
```

#### Database Maintenance

**Vacuum (reclaim space):**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c "VACUUM ANALYZE;"
```

**Check database size:**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT pg_size_pretty(pg_database_size('dora'));"
```

**Check table sizes:**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

### Qdrant Vector Database

#### Check Collection Info

```bash
# Get collection details
curl http://localhost:6333/collections/medical_knowledge | jq

# Count points
curl http://localhost:6333/collections/medical_knowledge | jq '.result.points_count'

# Collection configuration
curl http://localhost:6333/collections/medical_knowledge | jq '.result.config'
```

#### Search Vectors

```bash
# Search by ID
curl http://localhost:6333/collections/medical_knowledge/points/<point_id>

# Scroll through all points
curl -X POST http://localhost:6333/collections/medical_knowledge/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "with_payload": true, "with_vector": false}'
```

#### Delete Points

```bash
# Delete specific points
curl -X POST http://localhost:6333/collections/medical_knowledge/points/delete \
  -H "Content-Type: application/json" \
  -d '{"points": ["<uuid1>", "<uuid2>"]}'

# Delete by filter
curl -X POST http://localhost:6333/collections/medical_knowledge/points/delete \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "must": [
        {"key": "doc_type", "match": {"value": "outdated"}}
      ]
    }
  }'
```

#### Create Collection

```bash
curl -X PUT http://localhost:6333/collections/new_collection \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'
```

#### Delete Collection

```bash
curl -X DELETE http://localhost:6333/collections/medical_knowledge
```

---

### Redis Cache Management

#### Connect to Redis

```bash
docker exec -it dora-redis redis-cli
```

#### Common Commands

**Check all keys:**
```bash
docker exec dora-redis redis-cli KEYS "*"
```

**Get value:**
```bash
docker exec dora-redis redis-cli GET "user:123"
```

**Set value with expiry:**
```bash
docker exec dora-redis redis-cli SETEX "cache:query:abc" 3600 "cached_result"
```

**Delete key:**
```bash
docker exec dora-redis redis-cli DEL "cache:query:abc"
```

**Flush all data:**
```bash
docker exec dora-redis redis-cli FLUSHALL
```

**Check memory usage:**
```bash
docker exec dora-redis redis-cli INFO memory
```

**Monitor commands in real-time:**
```bash
docker exec -it dora-redis redis-cli MONITOR
```

---

### Neo4j Graph Database

#### Connect to Cypher Shell

```bash
docker exec -it dora-neo4j cypher-shell -u neo4j -p docassist123
```

#### Common Queries

**Count nodes:**
```cypher
MATCH (n) RETURN count(n);
```

**Count relationships:**
```cypher
MATCH ()-[r]->() RETURN count(r);
```

**Find drug interactions:**
```cypher
MATCH (d1:Drug)-[i:INTERACTS_WITH]->(d2:Drug)
WHERE d1.name = 'Warfarin'
RETURN d1.name, d2.name, i.severity, i.description
LIMIT 10;
```

**Find disease treatments:**
```cypher
MATCH (disease:Disease)-[:TREATS]-(treatment:Treatment)
WHERE disease.name = 'Diabetes Mellitus'
RETURN treatment.name, treatment.efficacy
ORDER BY treatment.efficacy DESC;
```

**Check UMLS concepts:**
```cypher
MATCH (c:Concept)
WHERE c.cui = 'C0011849'  # Diabetes Mellitus CUI
RETURN c;
```

#### Database Maintenance

**Delete all data:**
```cypher
MATCH (n) DETACH DELETE n;
```

**Create index:**
```cypher
CREATE INDEX drug_name IF NOT EXISTS FOR (d:Drug) ON (d.name);
```

**Check constraints:**
```cypher
SHOW CONSTRAINTS;
```

**Database size:**
```cypher
CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Store file sizes")
YIELD attributes
RETURN attributes.TotalStoreSize.value;
```

---

## Emergency Procedures

### Service Restart

#### Restart Individual Service

```bash
# Restart API only
docker restart dora-api

# Restart Qdrant
docker restart dora-qdrant

# Restart Redis
docker restart dora-redis

# Restart Neo4j
docker restart dora-neo4j

# Restart PostgreSQL
docker restart dora-postgres

# Restart Nginx
docker restart dora-nginx
```

#### Restart All Services

```bash
# Graceful restart
docker-compose restart

# Force restart
docker-compose down && docker-compose up -d
```

#### Restart with Specific Profile

```bash
# Full stack (including Neo4j, PostgreSQL, Nginx)
docker-compose --profile full up -d

# Minimal stack
docker-compose up -d
```

---

### Database Backup & Restore

#### PostgreSQL Backup

**Full database backup:**
```bash
# Backup to file
docker exec dora-postgres pg_dump -U dora dora > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec dora-postgres pg_dump -U dora dora | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Automated daily backup:**
```bash
# Add to crontab
0 2 * * * docker exec dora-postgres pg_dump -U dora dora | gzip > /backups/dora_$(date +\%Y\%m\%d).sql.gz
```

#### PostgreSQL Restore

```bash
# From SQL file
docker exec -i dora-postgres psql -U dora -d dora < backup.sql

# From compressed backup
gunzip < backup.sql.gz | docker exec -i dora-postgres psql -U dora -d dora
```

#### Qdrant Backup

**Backup entire collection:**
```bash
# Create snapshot
curl -X POST http://localhost:6333/collections/medical_knowledge/snapshots

# Download snapshot
curl http://localhost:6333/collections/medical_knowledge/snapshots/<snapshot_name> \
  --output qdrant_backup.snapshot
```

**Restore from snapshot:**
```bash
# Upload snapshot
curl -X PUT http://localhost:6333/collections/medical_knowledge/snapshots/upload \
  -H "Content-Type: application/octet-stream" \
  --data-binary @qdrant_backup.snapshot
```

#### Redis Backup

**Manual backup:**
```bash
# Trigger save
docker exec dora-redis redis-cli BGSAVE

# Copy RDB file
docker cp dora-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

**Restore:**
```bash
# Stop Redis
docker stop dora-redis

# Replace RDB file
docker cp redis_backup.rdb dora-redis:/data/dump.rdb

# Start Redis
docker start dora-redis
```

#### Neo4j Backup

**Backup:**
```bash
# Stop Neo4j first (required for safe backup)
docker stop dora-neo4j

# Backup data directory
docker run --rm -v dora_neo4j_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/neo4j_backup_$(date +%Y%m%d).tar.gz /data

# Restart Neo4j
docker start dora-neo4j
```

**Restore:**
```bash
# Stop Neo4j
docker stop dora-neo4j

# Restore data
docker run --rm -v dora_neo4j_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/neo4j_backup.tar.gz -C /

# Start Neo4j
docker start dora-neo4j
```

---

### Rollback Deployment

#### Rollback to Previous Docker Image

**Check current version:**
```bash
docker images | grep dora-api
```

**Tag current version:**
```bash
docker tag dora-api:latest dora-api:backup
```

**Pull previous version:**
```bash
# If using Docker registry
docker pull registry.example.com/dora-api:v1.2.3

# Tag as latest
docker tag registry.example.com/dora-api:v1.2.3 dora-api:latest
```

**Restart with previous version:**
```bash
docker-compose down
docker-compose up -d
```

#### Rollback Database Migration

**Check migration history:**
```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "SELECT * FROM alembic_version;"
```

**Rollback to specific migration:**
```bash
docker exec dora-api alembic downgrade <revision_id>
```

---

### Escalation Contacts

| Issue Type | Contact | Method | SLA |
|------------|---------|--------|-----|
| **Critical outage** | DevOps Team | emergency@docassist.in, +91-XXX-XXX-XXXX | 15 min |
| **Database issues** | Database Admin | dba@docassist.in | 30 min |
| **Security incident** | Security Team | security@docassist.in | Immediate |
| **Payment issues** | Finance Team | finance@docassist.in | 1 hour |
| **Medical content** | Clinical Team | clinical@docassist.in | 2 hours |

**Escalation Matrix:**
1. **Level 1:** Support team attempts resolution (30 min)
2. **Level 2:** Senior engineer on-call (1 hour)
3. **Level 3:** DevOps/Engineering lead (2 hours)
4. **Level 4:** CTO/Technical director (Critical only)

---

## Performance Troubleshooting

### Identifying Slow Queries

#### API Performance

**Check request latency distribution:**
```bash
# Extract latency from logs
docker logs dora-api | grep "latency_ms" | \
  awk '{print $NF}' | \
  sort -n | \
  awk '{sum+=$1; count++; latencies[count]=$1}
       END {
         print "Count:", count;
         print "Mean:", sum/count;
         print "P50:", latencies[int(count*0.5)];
         print "P95:", latencies[int(count*0.95)];
         print "P99:", latencies[int(count*0.99)];
       }'
```

**Find slowest endpoints:**
```bash
docker logs dora-api | grep -E "POST|GET" | \
  awk '{print $4, $NF}' | \
  sort -k2 -nr | \
  head -20
```

#### Database Query Performance

**PostgreSQL slow queries:**
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1 second
SELECT pg_reload_conf();

-- View slow queries
SELECT
  query,
  mean_time,
  calls,
  total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Qdrant query performance:**
```bash
# Check metrics
curl http://localhost:6333/metrics | grep query_duration
```

**Neo4j query performance:**
```cypher
-- Enable query logging
CALL dbms.setConfigValue('dbms.logs.query.enabled', 'true');

-- View query log
:play query-logging
```

---

### Memory Issues

#### Check Container Memory Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats dora-api --no-stream

# Check memory limits
docker inspect dora-api | jq '.[0].HostConfig.Memory'
```

#### Identify Memory Leaks

**API memory usage over time:**
```bash
# Monitor for 5 minutes
for i in {1..60}; do
  docker stats dora-api --no-stream --format "{{.MemUsage}}"
  sleep 5
done
```

**Python memory profiling:**
```bash
docker exec dora-api python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### Solutions

**Increase memory limit:**
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

**Restart service to clear memory:**
```bash
docker restart dora-api
```

**Enable memory monitoring:**
```bash
# Add to monitoring dashboard
docker logs dora-api | grep "MemoryError"
```

---

### CPU Spikes

#### Identify High CPU Usage

```bash
# Check current CPU usage
docker stats --no-stream

# Find processes using high CPU
docker top dora-api

# Application-level profiling
docker exec dora-api python3 -m cProfile -s cumtime src/api/app.py
```

#### Common Causes

1. **High query volume:** Too many concurrent requests
2. **Inefficient algorithms:** Poor code performance
3. **Embedding generation:** PubMedBERT is CPU-intensive
4. **LLM inference:** Local LLM using CPU instead of GPU

#### Solutions

**Scale horizontally:**
```bash
# Add more API replicas
docker-compose up -d --scale api=3
```

**Use GPU for embeddings:**
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Implement rate limiting:**
```python
# In API code
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/query")
@limiter.limit("10/minute")
async def query(request: Request):
    ...
```

---

### Connection Pool Exhaustion

#### Symptoms
- Error: `"Too many connections"`
- Error: `"Connection pool exhausted"`

#### Diagnosis

**PostgreSQL connections:**
```sql
SELECT count(*) FROM pg_stat_activity;

-- Check max connections
SHOW max_connections;
```

**Qdrant connections:**
```bash
curl http://localhost:6333/metrics | grep connection
```

#### Solutions

**Increase max connections:**
```sql
-- PostgreSQL
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
```

**Configure connection pooling:**
```python
# In application code
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

**Close idle connections:**
```sql
-- PostgreSQL - terminate idle connections older than 5 minutes
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < NOW() - INTERVAL '5 minutes';
```

---

## Security Incidents

### Unauthorized Access Detection

#### Monitor Authentication Logs

```bash
# Failed login attempts
docker logs dora-api | grep "authentication failed" | tail -20

# Multiple failed attempts from same IP
docker logs dora-api | grep "authentication failed" | \
  awk '{print $5}' | sort | uniq -c | sort -nr | head -10

# Successful logins
docker logs dora-api | grep "login successful"
```

#### Check for Brute Force Attacks

```bash
# Count failed attempts per IP
docker logs dora-api --since 1h | grep "401 Unauthorized" | \
  awk '{print $1}' | sort | uniq -c | sort -nr

# Block suspicious IPs (if using fail2ban or firewall)
iptables -A INPUT -s <suspicious_ip> -j DROP
```

---

### Audit Log Review

#### View All Admin Actions

```sql
SELECT
  user_id,
  action,
  resource,
  ip_address,
  created_at
FROM audit_logs
WHERE action IN ('DELETE', 'UPDATE', 'CREATE')
ORDER BY created_at DESC
LIMIT 50;
```

#### Check for Privilege Escalation

```sql
SELECT
  u.email,
  al.action,
  al.details,
  al.created_at
FROM audit_logs al
JOIN users u ON al.user_id = u.id
WHERE al.action = 'ROLE_CHANGE'
ORDER BY al.created_at DESC;
```

#### Export Audit Log

```bash
docker exec -it dora-postgres psql -U dora -d dora -c \
  "COPY (SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '30 days')
   TO STDOUT CSV HEADER" > audit_export.csv
```

---

### Account Lockout Procedures

#### Lock User Account

```sql
UPDATE users
SET is_active = false,
    locked_reason = 'Suspicious activity detected',
    locked_at = NOW()
WHERE email = 'suspicious@example.com';
```

#### Unlock User Account

```sql
UPDATE users
SET is_active = true,
    locked_reason = NULL,
    locked_at = NULL
WHERE email = 'user@example.com';
```

#### Force Password Reset

```sql
UPDATE users
SET password_must_change = true
WHERE email = 'user@example.com';
```

---

### Incident Reporting

#### Security Incident Report Template

```markdown
# Security Incident Report

**Incident ID:** SEC-2026-001
**Date/Time:** 2026-01-05 14:30 IST
**Severity:** Critical / High / Medium / Low
**Status:** Open / Under Investigation / Resolved

## Summary
Brief description of the incident.

## Timeline
- 14:30 - Incident detected
- 14:35 - DevOps notified
- 14:40 - Investigation started
- 15:00 - Mitigation applied

## Impact
- Number of users affected:
- Data compromised:
- Service downtime:

## Root Cause
Description of what caused the incident.

## Mitigation Steps Taken
1. Step 1
2. Step 2

## Prevention Measures
1. Future prevention step 1
2. Future prevention step 2

## Follow-up Actions
- [ ] Action item 1
- [ ] Action item 2
```

#### Report Incident

```bash
# Send incident report via email
mail -s "SECURITY INCIDENT: SEC-2026-001" security@docassist.in < incident_report.md

# Log to security system
curl -X POST https://security-dashboard.docassist.in/api/incidents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @incident_report.json
```

---

### Contact Information for Security Issues

| Issue | Contact | Response Time |
|-------|---------|---------------|
| **Active attack** | security@docassist.in | Immediate |
| **Data breach** | security@docassist.in, legal@docassist.in | Immediate |
| **Vulnerability report** | security@docassist.in | 24 hours |
| **Suspicious activity** | security@docassist.in | 1 hour |

**Security Hotline:** +91-XXX-XXX-XXXX (24/7)

---

## Appendix

### Environment Variables Reference

See `.env.example` for full list. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `QDRANT_URL` | Qdrant endpoint | `http://localhost:6333` |
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `COHERE_API_KEY` | Cohere reranker key | - |

### Useful Commands Cheatsheet

```bash
# Docker
docker-compose ps                    # List services
docker-compose logs -f api           # Follow API logs
docker-compose restart api           # Restart API
docker stats                         # Monitor resources

# Database
psql -h localhost -U dora -d dora   # Connect to PostgreSQL
redis-cli                            # Connect to Redis
cypher-shell -u neo4j               # Connect to Neo4j

# Health checks
curl localhost:8000/health           # API health
curl localhost:6333/                 # Qdrant health
redis-cli ping                       # Redis health

# Logs
docker logs dora-api --tail 100     # Last 100 lines
docker logs -f dora-api             # Follow logs
docker logs --since 1h dora-api     # Last hour

# Cleanup
docker system prune -a              # Clean up everything
docker volume prune                 # Remove unused volumes
```

---

**Document Version:** 1.0
**Last Reviewed:** January 2026
**Next Review:** February 2026

**Maintainer:** DevOps Team (devops@docassist.in)

---

*For additional support, contact: support@docassist.in*
