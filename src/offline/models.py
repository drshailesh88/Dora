"""
Offline Data Models for Dora Medical Knowledge Platform

This module defines data models for offline storage and synchronization.
Supports SQLite storage with encryption for sensitive data.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import uuid4


class SyncStatus(str, Enum):
    """Synchronization status for offline entities"""
    PENDING = "pending"  # Waiting to be synced
    SYNCING = "syncing"  # Currently syncing
    SYNCED = "synced"  # Successfully synced
    CONFLICT = "conflict"  # Sync conflict detected
    FAILED = "failed"  # Sync failed


class ActionType(str, Enum):
    """Types of offline actions"""
    QUERY = "query"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    ANNOTATION = "annotation"
    CALCULATION = "calculation"
    DRUG_INTERACTION = "drug_interaction"


class Priority(str, Enum):
    """Sync priority levels"""
    CRITICAL = "critical"  # Medical emergencies, drug interactions
    HIGH = "high"  # Patient-related queries
    MEDIUM = "medium"  # General queries
    LOW = "low"  # Cache updates, non-critical data


class ConflictResolution(str, Enum):
    """Conflict resolution strategies"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MANUAL = "manual"
    MERGE = "merge"
    LATEST_TIMESTAMP = "latest_timestamp"


class OfflineQuery(BaseModel):
    """Model for offline queries"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    query_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: ActionType = ActionType.QUERY
    priority: Priority = Priority.MEDIUM
    sync_status: SyncStatus = SyncStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CachedDocument(BaseModel):
    """Model for cached medical documents"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str  # Original document ID from server
    title: str
    content: str
    specialty: Optional[str] = None
    category: str  # guideline, drug_info, clinical_trial, etc.
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    size_bytes: int = 0
    is_pinned: bool = False  # User-pinned for offline access
    sync_status: SyncStatus = SyncStatus.SYNCED

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OfflineAction(BaseModel):
    """Generic offline action queue item"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: ActionType
    priority: Priority = Priority.MEDIUM
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sync_status: SyncStatus = SyncStatus.PENDING
    scheduled_sync_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    user_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SyncMetadata(BaseModel):
    """Metadata for synchronization tracking"""
    entity_id: str
    entity_type: str  # query, document, action, etc.
    local_version: int = 1
    server_version: Optional[int] = None
    last_sync_time: Optional[datetime] = None
    local_checksum: Optional[str] = None
    server_checksum: Optional[str] = None
    conflict_detected: bool = False
    conflict_resolution: Optional[ConflictResolution] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContentPack(BaseModel):
    """Downloadable content pack for offline use"""
    id: str
    name: str
    description: str
    specialty: str  # cardiology, neurology, etc.
    version: str
    size_mb: float
    document_count: int
    last_updated: datetime
    required: bool = False  # Critical content packs
    downloaded: bool = False
    download_progress: float = 0.0  # 0-100
    file_path: Optional[str] = None
    checksum: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DrugDatabase(BaseModel):
    """Local drug database entry"""
    drug_id: str
    name: str
    generic_name: Optional[str] = None
    brand_names: List[str] = Field(default_factory=list)
    category: str
    interactions: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)
    dosage_info: Dict[str, Any] = Field(default_factory=dict)
    side_effects: List[str] = Field(default_factory=list)
    pregnancy_category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OfflineCalculator(BaseModel):
    """Model for offline medical calculators"""
    calculator_id: str
    name: str
    category: str  # dosage, risk_score, conversion, etc.
    formula: str
    parameters: List[Dict[str, Any]]
    reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NetworkStatus(BaseModel):
    """Network connectivity status"""
    is_online: bool
    connection_type: Optional[str] = None  # wifi, cellular, ethernet
    bandwidth_estimate: Optional[float] = None  # Mbps
    last_online: Optional[datetime] = None
    sync_enabled: bool = True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SyncStats(BaseModel):
    """Statistics for synchronization"""
    total_pending: int = 0
    total_synced: int = 0
    total_conflicts: int = 0
    total_failed: int = 0
    last_successful_sync: Optional[datetime] = None
    next_scheduled_sync: Optional[datetime] = None
    data_uploaded_mb: float = 0.0
    data_downloaded_mb: float = 0.0
    sync_duration_seconds: float = 0.0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StorageQuota(BaseModel):
    """Storage quota management"""
    total_mb: float
    used_mb: float
    available_mb: float
    documents_count: int
    cache_size_mb: float
    database_size_mb: float
    content_packs_mb: float
    threshold_warning_percent: float = 80.0
    threshold_critical_percent: float = 95.0

    @property
    def usage_percent(self) -> float:
        return (self.used_mb / self.total_mb) * 100 if self.total_mb > 0 else 0

    @property
    def is_warning(self) -> bool:
        return self.usage_percent >= self.threshold_warning_percent

    @property
    def is_critical(self) -> bool:
        return self.usage_percent >= self.threshold_critical_percent


class ConflictRecord(BaseModel):
    """Record of a sync conflict"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    entity_id: str
    entity_type: str
    local_data: Dict[str, Any]
    server_data: Dict[str, Any]
    conflict_detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolution_strategy: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # user_id or 'auto'
    resolved_data: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SyncBatch(BaseModel):
    """Batch of items to sync"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    priority: Priority
    items: List[OfflineAction]
    status: SyncStatus = SyncStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
