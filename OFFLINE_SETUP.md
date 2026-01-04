# Offline-First Architecture Setup Guide

## Overview

Dora implements a comprehensive offline-first architecture designed for rural India where 40% of users have unreliable internet connectivity. This guide covers setup, configuration, and usage of offline features.

## Architecture Components

### Backend (Python)
- **Storage**: SQLite with encryption for local data
- **Cache**: Intelligent LRU and specialty-based caching
- **Sync**: Priority-based bidirectional synchronization
- **Conflict Resolution**: Automated and manual strategies
- **Local RAG**: Ollama + ChromaDB for offline queries

### Mobile (Flutter/Dart)
- **SQLite + Hive**: Local data persistence
- **Connectivity Monitoring**: Real-time network detection
- **Background Sync**: Automatic when online
- **Encrypted Storage**: Secure medical data

### Desktop (Flet/Python)
- **Offline Manager**: Coordinates all offline operations
- **Local RAG**: Full offline query answering
- **Sync Manager**: UI-friendly sync operations

---

## Installation

### 1. Backend Dependencies

```bash
# Core dependencies
pip install pydantic sqlalchemy cryptography aiohttp

# Vector database
pip install chromadb qdrant-client

# Optional: Local LLM (Ollama)
# Install Ollama: https://ollama.ai
ollama pull qwen2.5:3b
```

### 2. Mobile Dependencies (Flutter)

Add to `pubspec.yaml`:

```yaml
dependencies:
  sqflite: ^2.3.0
  hive: ^2.2.3
  connectivity_plus: ^5.0.2
  path_provider: ^2.1.1
  encrypt: ^5.0.3
  http: ^1.1.0
```

Install:
```bash
cd mobile
flutter pub get
```

### 3. Desktop Dependencies

```bash
pip install flet ollama chromadb
```

---

## Configuration

### Backend Configuration

Create `.env` file:

```env
# Database
OFFLINE_DB_PATH=~/.dora/offline.db
ENCRYPTION_KEY_PATH=~/.dora/encryption.key

# Sync settings
AUTO_SYNC_ENABLED=true
AUTO_SYNC_INTERVAL_MINUTES=15
MAX_BATCH_SIZE=50

# Storage quota (MB)
DEFAULT_STORAGE_QUOTA_MB=10240

# API endpoint
API_BASE_URL=https://api.dora.docassist.in
```

### Initialize Offline Storage

```python
from src.offline import OfflineStorage, CacheManager, SyncEngine, ActionQueue

# Initialize storage
storage = OfflineStorage(
    db_path="~/.dora/offline.db",
    encrypt_sensitive=True
)

# Initialize cache manager
cache = CacheManager(
    storage=storage,
    user_specialty="cardiology"  # Optional: prioritize specialty
)

# Initialize sync
action_queue = ActionQueue(storage)
sync_engine = SyncEngine(storage, action_queue)

# Start background sync
await sync_engine.start_background_sync()
```

### Mobile Configuration

Initialize services in `main.dart`:

```dart
import 'package:dora/services/offline_service.dart';
import 'package:dora/services/sync_service.dart';
import 'package:dora/services/local_storage.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize local storage
  await LocalStorage().initialize();

  // Configure sync service
  SyncService().configure(
    baseUrl: 'https://api.dora.docassist.in',
    authToken: 'your_auth_token',
  );

  // Start background sync
  SyncService().startBackgroundSync();

  runApp(MyApp());
}
```

---

## Usage

### 1. Offline Query Handling

#### Backend (Desktop)

```python
from src.desktop.offline_manager import OfflineManager

# Initialize
offline_manager = OfflineManager(
    user_id="user123",
    specialty="cardiology"
)
await offline_manager.initialize()

# Handle query (automatically detects online/offline)
result = await offline_manager.handle_query(
    "What is the treatment for atrial fibrillation?",
    priority=Priority.HIGH
)

print(result['answer'])
print(result['sources'])
print(f"Mode: {result['mode']}")  # 'online' or 'offline'
```

#### Mobile (Flutter)

```dart
// Check if online
if (OfflineService().isOnline) {
  // Online query
  await queryCloud(queryText);
} else {
  // Offline query from cache
  final results = await LocalStorage().searchDocuments(
    query: queryText,
    limit: 10,
  );
}
```

### 2. Document Caching

#### Backend

```python
# Cache document for offline access
document = {
    "id": "doc_001",
    "doc_id": "cardio_guideline_001",
    "title": "Atrial Fibrillation Guidelines",
    "content": "Full guideline text...",
    "specialty": "cardiology",
    "category": "guideline",
    "metadata": {"source": "AHA/ACC"}
}

success, error = cache.cache_document(document)

# Pin important documents (never evict)
cache.pin_document("cardio_guideline_001")

# Search cached documents
results = storage.search_documents(
    query="atrial fibrillation",
    specialty="cardiology",
    pinned_only=False,
    limit=50
)
```

#### Mobile

```dart
// Cache document
await CacheManager().cacheDocument(document);

// Pin document
await CacheManager().pinDocument(docId);

// Get cache stats
final stats = await CacheManager().getCacheStats();
print('Cached: ${stats['total_documents']} documents');
print('Usage: ${stats['storage_quota']['usage_percent']}%');
```

### 3. Synchronization

#### Backend

```python
# Manual sync
result = await sync_engine.sync()

# Priority sync (critical items only)
result = await sync_engine.sync(priority_filter=Priority.CRITICAL)

# Force full sync
result = await sync_engine.force_full_sync()

# Get sync status
status = sync_engine.get_sync_status()
print(f"Pending: {status['queue_stats']['total_pending']}")
print(f"Last sync: {status['last_sync_time']}")
```

#### Mobile

```dart
// Manual sync
final result = await SyncService().sync();

// Get sync status
final status = await SyncService().getSyncStatus();

// Retry failed actions
await SyncService().retryFailedActions();
```

### 4. Offline Action Queue

```python
from src.offline import OfflineAction, ActionType, Priority

# Enqueue action for later sync
action = OfflineAction(
    action_type=ActionType.QUERY,
    priority=Priority.HIGH,
    payload={
        "query": "drug interaction check",
        "drugs": ["aspirin", "warfarin"]
    },
    user_id="user123"
)

action_queue.enqueue(action)

# Actions will be synced when online
```

### 5. Conflict Resolution

```python
# Get pending conflicts
conflicts = conflict_resolver.get_pending_conflicts()

for conflict in conflicts:
    print(f"Conflict: {conflict.entity_type} {conflict.entity_id}")
    print(f"Local: {conflict.local_data}")
    print(f"Server: {conflict.server_data}")

    # Resolve manually
    await conflict_resolver.resolve_manual_conflict(
        conflict_id=conflict.id,
        chosen_version="local",  # or "server" or "custom"
        custom_data=None
    )
```

---

## Content Packs

Download specialty-specific content for offline use:

```python
from src.offline.cache import ContentPackManager

pack_manager = ContentPackManager(storage)

# Get available packs
packs = pack_manager.get_available_packs()

# Estimate download size
pack_ids = ["cardiology-essentials", "drug-interactions"]
estimate = pack_manager.estimate_download_size(pack_ids)

print(f"Total: {estimate['total_mb']} MB")
print(f"Space available: {estimate['sufficient_space']}")

# Download would be implemented in actual API
```

---

## Local RAG with Ollama

### Setup

1. **Install Ollama**:
   ```bash
   curl https://ollama.ai/install.sh | sh
   ```

2. **Download Model**:
   ```bash
   ollama pull qwen2.5:3b
   ```

3. **Verify**:
   ```bash
   ollama list
   ```

### Usage

```python
from src.desktop.local_rag import LocalRAG

# Initialize
local_rag = LocalRAG(storage)
await local_rag.initialize()

# Query
result = await local_rag.query(
    "What are the contraindications for beta blockers?"
)

print(result['answer'])
print(f"Confidence: {result['confidence']}")
print(f"Sources: {len(result['sources'])}")

# Add document to RAG
await local_rag.add_document(
    doc_id="doc_001",
    content="Beta blockers are contraindicated in...",
    metadata={"title": "Beta Blocker Guidelines", "specialty": "cardiology"}
)
```

---

## Storage Management

### Check Quota

```python
# Get storage quota
quota = storage.get_storage_quota()

print(f"Total: {quota.total_mb} MB")
print(f"Used: {quota.used_mb} MB ({quota.usage_percent:.1f}%)")
print(f"Available: {quota.available_mb} MB")

if quota.is_warning:
    print("⚠️ Storage usage above 80%")

if quota.is_critical:
    print("🔴 Storage usage above 95% - cleanup needed")
```

### Cleanup

```python
# Remove old cached documents (not accessed in 30 days)
deleted = storage.cleanup_old_cache(days=30)
print(f"Deleted {deleted} old documents")

# Optimize database
storage.vacuum_database()

# Or use cache manager
results = cache.optimize_cache()
print(f"Freed {results['space_freed_mb']:.1f} MB")
```

---

## API Endpoints

### Sync API

```bash
# Push local changes
POST /api/sync/push
{
  "actions": [...],
  "priority": "high"
}

# Pull server updates
GET /api/sync/pull?since=2024-01-01T00:00:00Z

# Get sync status
GET /api/sync/status

# Resolve conflict
POST /api/sync/resolve
{
  "conflict_id": "conf_123",
  "resolution": "local",
  "custom_data": null
}

# Get conflicts
GET /api/sync/conflicts

# Batch sync
POST /api/sync/batch
{
  "push_actions": [...],
  "pull_since": "2024-01-01T00:00:00Z",
  "auto_resolve_conflicts": true
}
```

---

## Monitoring & Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('src.offline')
logger.setLevel(logging.DEBUG)
```

### Get Statistics

```python
# Cache stats
cache_stats = cache.get_cache_stats()

# Sync stats
sync_status = sync_engine.get_sync_status()

# Queue stats
queue_stats = action_queue.get_queue_stats()

# Conflict stats
conflict_stats = conflict_resolver.get_conflict_stats()
```

---

## Best Practices

### 1. Cache Strategy
- Pin critical documents (guidelines, drug database)
- Set appropriate storage quota for user's device
- Configure specialty-based prioritization
- Regular cleanup of old cache

### 2. Sync Strategy
- Use priority levels appropriately:
  - **CRITICAL**: Medical emergencies, drug interactions
  - **HIGH**: Patient-related queries
  - **MEDIUM**: General queries
  - **LOW**: Cache updates, non-critical data

### 3. Conflict Resolution
- Use LATEST_TIMESTAMP for most medical data
- Use SERVER_WINS for guidelines/references
- Use CLIENT_WINS for user preferences
- Use MANUAL for critical medical records

### 4. Performance
- Limit batch size (50-100 items)
- Use delta sync (only changes since last sync)
- Compress large documents (>100KB)
- Index frequently accessed documents

### 5. Security
- Always enable encryption for medical data
- Secure encryption keys properly
- Use HTTPS for all API calls
- Validate data before sync

---

## Troubleshooting

### Issue: Sync Failing

```python
# Check network
is_online = await sync_engine.network_monitor.check_connectivity()

# Check pending actions
stats = action_queue.get_queue_stats()
print(f"Failed: {stats['total_failed']}")

# Retry failed
retry_count = action_queue.retry_failed_actions()

# Clear failed (if irrecoverable)
cleared = action_queue.clear_failed_actions()
```

### Issue: Storage Full

```python
# Check quota
quota = storage.get_storage_quota()

if quota.is_critical:
    # Aggressive cleanup
    deleted = storage.cleanup_old_cache(days=7)

    # Evict non-pinned, low-access documents
    cache.evict_candidates(required_mb=1000)

    # Vacuum database
    storage.vacuum_database()
```

### Issue: Local RAG Not Working

```bash
# Check Ollama
ollama list

# Pull model if missing
ollama pull qwen2.5:3b

# Test Ollama
ollama run qwen2.5:3b "Hello"

# Check ChromaDB
python -c "import chromadb; print('ChromaDB OK')"
```

---

## Testing

### Unit Tests

```bash
pytest tests/test_offline/ -v
pytest tests/test_sync/ -v
pytest tests/test_cache/ -v
```

### Integration Tests

```bash
# Test offline->online transition
pytest tests/integration/test_offline_online.py -v

# Test sync with conflicts
pytest tests/integration/test_sync_conflicts.py -v
```

### Mobile Tests

```bash
cd mobile
flutter test
```

---

## Performance Benchmarks

Expected performance metrics:

- **Sync Speed**: 100-200 items/minute (good connection)
- **Cache Hit Rate**: >80% for frequently accessed content
- **Local RAG Query**: 2-5 seconds (depending on model)
- **Storage Efficiency**: 5-10 GB for typical medical practice

---

## Roadmap

### Phase 1 (Current)
- ✅ Basic offline storage
- ✅ Sync infrastructure
- ✅ Conflict resolution
- ✅ Local RAG (Ollama)

### Phase 2 (Next)
- [ ] Voice queries offline
- [ ] Image caching
- [ ] P2P sync between devices
- [ ] Offline ML model updates

### Phase 3 (Future)
- [ ] Differential privacy
- [ ] Federated learning
- [ ] Edge computing integration

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/drshailesh88/Dora/issues
- Documentation: https://docs.dora.docassist.in
- Email: support@docassist.in

---

*Last Updated: January 2026*
*Version: 1.0.0*
