"""
Sync API Endpoints for Offline-First Architecture

FastAPI endpoints for synchronization between client and server.

Endpoints:
- POST /api/sync/push - Push local changes to server
- GET /api/sync/pull - Pull server updates
- GET /api/sync/status - Get sync status
- POST /api/sync/resolve - Resolve conflicts manually
- GET /api/sync/conflicts - Get pending conflicts
- POST /api/sync/batch - Batch sync operations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..offline import (
    SyncEngine, OfflineStorage, ActionQueue,
    OfflineAction, ConflictResolver, ConflictResolution,
    Priority, SyncStatus
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/sync", tags=["sync"])

# Global instances (in production, use dependency injection)
storage = OfflineStorage()
action_queue = ActionQueue(storage)
sync_engine = SyncEngine(storage, action_queue)


# ===== Request/Response Models =====

class PushRequest(BaseModel):
    """Request to push local changes"""
    actions: List[Dict[str, Any]]
    priority: Optional[Priority] = Priority.MEDIUM
    user_id: Optional[str] = None


class PushResponse(BaseModel):
    """Response from push operation"""
    success: bool
    total_pushed: int
    succeeded: int
    failed: int
    errors: List[str] = Field(default_factory=list)


class PullRequest(BaseModel):
    """Request to pull server updates"""
    since: Optional[datetime] = None
    entity_types: Optional[List[str]] = None
    limit: Optional[int] = 100


class PullResponse(BaseModel):
    """Response from pull operation"""
    success: bool
    total_pulled: int
    updates: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    next_cursor: Optional[str] = None


class SyncStatusResponse(BaseModel):
    """Sync status information"""
    is_syncing: bool
    is_online: bool
    last_sync_time: Optional[datetime]
    pending_actions: int
    failed_actions: int
    pending_conflicts: int
    storage_quota: Dict[str, Any]
    network_status: Dict[str, Any]


class ResolveConflictRequest(BaseModel):
    """Request to resolve conflict"""
    conflict_id: str
    resolution: str  # "local", "server", "custom"
    custom_data: Optional[Dict[str, Any]] = None


class ResolveConflictResponse(BaseModel):
    """Response from conflict resolution"""
    success: bool
    message: str


class BatchSyncRequest(BaseModel):
    """Request for batch sync"""
    push_actions: Optional[List[Dict[str, Any]]] = None
    pull_since: Optional[datetime] = None
    auto_resolve_conflicts: bool = False


class BatchSyncResponse(BaseModel):
    """Response from batch sync"""
    success: bool
    push_results: Optional[Dict[str, Any]] = None
    pull_results: Optional[Dict[str, Any]] = None
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    duration_seconds: float


# ===== Helper Functions =====

def get_sync_engine() -> SyncEngine:
    """Dependency to get sync engine instance"""
    return sync_engine


def get_conflict_resolver() -> ConflictResolver:
    """Dependency to get conflict resolver instance"""
    return ConflictResolver(storage)


# ===== API Endpoints =====

@router.post("/push", response_model=PushResponse)
async def push_changes(
    request: PushRequest,
    background_tasks: BackgroundTasks,
    engine: SyncEngine = Depends(get_sync_engine)
) -> PushResponse:
    """
    Push local changes to server

    This endpoint receives batched offline actions from clients and
    processes them on the server side.
    """
    try:
        results = {
            "total_pushed": 0,
            "succeeded": 0,
            "failed": 0,
            "errors": []
        }

        # Process each action
        for action_data in request.actions:
            try:
                # Convert to OfflineAction
                action = OfflineAction(**action_data)

                # Enqueue action
                success = action_queue.enqueue(action)

                if success:
                    results["total_pushed"] += 1
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Failed to enqueue action {action.id}"
                    )

            except Exception as e:
                logger.error(f"Error processing action: {e}")
                results["failed"] += 1
                results["errors"].append(str(e))

        # Process queue in background
        background_tasks.add_task(
            action_queue.process_batch,
            action_queue.get_next_batch(),
            online=True
        )

        return PushResponse(
            success=results["failed"] == 0,
            **results
        )

    except Exception as e:
        logger.error(f"Push error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pull", response_model=PullResponse)
async def pull_updates(
    since: Optional[str] = None,
    entity_types: Optional[str] = None,
    limit: int = 100,
    engine: SyncEngine = Depends(get_sync_engine)
) -> PullResponse:
    """
    Pull server updates to client

    Supports delta sync by providing 'since' timestamp.
    Returns updates and any detected conflicts.
    """
    try:
        # Parse parameters
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)

        types = []
        if entity_types:
            types = entity_types.split(',')

        # Fetch updates from database
        # In production, this would query actual data
        updates = await _fetch_updates(
            since=since_dt,
            entity_types=types,
            limit=limit
        )

        # Check for conflicts
        conflicts = []
        for update in updates:
            conflict = await engine._check_conflict(update)
            if conflict:
                conflicts.append(conflict)

        return PullResponse(
            success=True,
            total_pulled=len(updates),
            updates=updates,
            conflicts=conflicts
        )

    except Exception as e:
        logger.error(f"Pull error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    engine: SyncEngine = Depends(get_sync_engine)
) -> SyncStatusResponse:
    """
    Get current sync status

    Returns information about:
    - Sync progress
    - Network connectivity
    - Pending actions
    - Storage quota
    - Conflicts
    """
    try:
        # Get sync status
        status = engine.get_sync_status()

        # Get storage quota
        quota = storage.get_storage_quota()

        # Get conflict count
        resolver = ConflictResolver(storage)
        pending_conflicts = len(resolver.get_pending_conflicts())

        return SyncStatusResponse(
            is_syncing=status["is_syncing"],
            is_online=status["is_online"],
            last_sync_time=datetime.fromisoformat(status["last_sync_time"]) if status["last_sync_time"] else None,
            pending_actions=status["queue_stats"]["total_pending"],
            failed_actions=status["queue_stats"]["total_failed"],
            pending_conflicts=pending_conflicts,
            storage_quota=quota.dict(),
            network_status=status["network_status"]
        )

    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve", response_model=ResolveConflictResponse)
async def resolve_conflict(
    request: ResolveConflictRequest,
    resolver: ConflictResolver = Depends(get_conflict_resolver)
) -> ResolveConflictResponse:
    """
    Manually resolve a sync conflict

    Allows user to choose which version to keep or provide custom merged data.
    """
    try:
        success = await resolver.resolve_manual_conflict(
            conflict_id=request.conflict_id,
            chosen_version=request.resolution,
            custom_data=request.custom_data
        )

        if success:
            return ResolveConflictResponse(
                success=True,
                message=f"Conflict {request.conflict_id} resolved successfully"
            )
        else:
            return ResolveConflictResponse(
                success=False,
                message=f"Failed to resolve conflict {request.conflict_id}"
            )

    except Exception as e:
        logger.error(f"Resolve conflict error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts")
async def get_conflicts(
    resolver: ConflictResolver = Depends(get_conflict_resolver)
) -> Dict[str, Any]:
    """
    Get all pending conflicts

    Returns list of conflicts awaiting manual resolution.
    """
    try:
        conflicts = resolver.get_pending_conflicts()

        return {
            "total": len(conflicts),
            "conflicts": [c.dict() for c in conflicts]
        }

    except Exception as e:
        logger.error(f"Get conflicts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchSyncResponse)
async def batch_sync(
    request: BatchSyncRequest,
    background_tasks: BackgroundTasks,
    engine: SyncEngine = Depends(get_sync_engine)
) -> BatchSyncResponse:
    """
    Perform batch synchronization

    Combines push and pull operations in a single request.
    Optionally auto-resolves conflicts using default strategy.
    """
    try:
        start_time = datetime.utcnow()

        results = {
            "push_results": None,
            "pull_results": None,
            "conflicts": []
        }

        # Push changes if provided
        if request.push_actions:
            push_req = PushRequest(actions=request.push_actions)
            push_resp = await push_changes(push_req, background_tasks, engine)
            results["push_results"] = push_resp.dict()

        # Pull updates
        pull_resp = await pull_updates(
            since=request.pull_since.isoformat() if request.pull_since else None,
            engine=engine
        )
        results["pull_results"] = pull_resp.dict()

        # Handle conflicts
        if pull_resp.conflicts and request.auto_resolve_conflicts:
            resolver = ConflictResolver(storage)
            for conflict_data in pull_resp.conflicts:
                conflict = await resolver.resolve_conflict(conflict_data)
                results["conflicts"].append(conflict.dict())
        else:
            results["conflicts"] = pull_resp.conflicts

        duration = (datetime.utcnow() - start_time).total_seconds()

        return BatchSyncResponse(
            success=True,
            push_results=results["push_results"],
            pull_results=results["pull_results"],
            conflicts=results["conflicts"],
            duration_seconds=duration
        )

    except Exception as e:
        logger.error(f"Batch sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-sync")
async def force_full_sync(
    engine: SyncEngine = Depends(get_sync_engine)
) -> Dict[str, Any]:
    """
    Force a full synchronization (not delta)

    Useful for recovering from sync issues or initial sync.
    """
    try:
        results = await engine.force_full_sync()

        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Force sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-failed")
async def clear_failed_actions() -> Dict[str, Any]:
    """
    Clear all failed actions from queue

    Use with caution - removes permanently failed actions.
    """
    try:
        deleted = action_queue.clear_failed_actions()

        return {
            "success": True,
            "deleted": deleted,
            "message": f"Cleared {deleted} failed actions"
        }

    except Exception as e:
        logger.error(f"Clear failed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-failed")
async def retry_failed_actions() -> Dict[str, Any]:
    """
    Retry all failed actions

    Resets failed actions to pending status for another attempt.
    """
    try:
        updated = action_queue.retry_failed_actions()

        return {
            "success": True,
            "retried": updated,
            "message": f"Reset {updated} failed actions for retry"
        }

    except Exception as e:
        logger.error(f"Retry failed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_sync_stats() -> Dict[str, Any]:
    """
    Get detailed synchronization statistics

    Returns metrics about sync performance, conflicts, and queue status.
    """
    try:
        # Queue stats
        queue_stats = action_queue.get_queue_stats()

        # Conflict stats
        resolver = ConflictResolver(storage)
        conflict_stats = resolver.get_conflict_stats()

        # Storage quota
        quota = storage.get_storage_quota()

        # Sync status
        status = sync_engine.get_sync_status()

        return {
            "queue": queue_stats,
            "conflicts": conflict_stats,
            "storage": quota.dict(),
            "sync": status["sync_stats"]
        }

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Helper Functions =====

async def _fetch_updates(
    since: Optional[datetime] = None,
    entity_types: Optional[List[str]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch updates from database

    In production, this would query actual data with proper filtering.
    """
    updates = []

    # Example: Fetch document updates
    if not entity_types or "document" in entity_types:
        docs = storage.search_documents(limit=limit)
        for doc in docs:
            if since and doc.updated_at < since:
                continue

            updates.append({
                "type": "document",
                "id": doc.doc_id,
                "data": doc.dict(),
                "version": 1,
                "updated_at": doc.updated_at.isoformat(),
                "checksum": _calculate_checksum(doc.dict())
            })

    return updates[:limit]


def _calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate checksum for data"""
    import hashlib
    import json
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
