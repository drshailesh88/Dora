"""Services for Dora Desktop - API client and state management."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import httpx


@dataclass
class QueryHistoryItem:
    """A query history entry."""

    question: str
    answer: str
    confidence: str
    citations: list[dict]
    timestamp: datetime = field(default_factory=datetime.now)
    patient_id: int | None = None


@dataclass
class AppState:
    """Application state."""

    # User/License
    is_licensed: bool = False
    license_tier: str = "free"
    user_email: str = ""

    # API Status
    api_connected: bool = False
    api_url: str = "http://localhost:8000"

    # Current session
    current_patient_id: int | None = None
    current_patient_name: str = ""

    # History
    query_history: list[QueryHistoryItem] = field(default_factory=list)

    # Settings
    dark_mode: bool = False
    voice_enabled: bool = True
    offline_mode: bool = False


class DoraAPIClient:
    """Client for Dora API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,
            )
        return self._client

    async def health_check(self) -> dict:
        """Check API health."""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def query(
        self,
        question: str,
        patient_id: int | None = None,
        top_k: int = 10,
    ) -> dict:
        """Submit a medical query."""
        try:
            response = await self.client.post(
                "/api/v1/query",
                json={
                    "question": question,
                    "patient_id": patient_id,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def check_drug_interactions(
        self,
        drugs: list[str],
        patient_medications: list[str] | None = None,
    ) -> dict:
        """Check drug interactions."""
        try:
            response = await self.client.post(
                "/api/v1/drugs/check",
                json={
                    "drugs": drugs,
                    "patient_medications": patient_medications,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_license_status(self) -> dict:
        """Get license status."""
        try:
            response = await self.client.get("/api/v1/license/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def activate_license(self, license_key: str) -> dict:
        """Activate a license."""
        try:
            response = await self.client.post(
                "/api/v1/license/activate",
                json={"license_key": license_key},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_stats(self) -> dict:
        """Get knowledge base stats."""
        try:
            response = await self.client.get("/api/v1/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class StateManager:
    """Manages application state with observers."""

    def __init__(self):
        self.state = AppState()
        self._observers: list[Callable[[AppState], None]] = []

    def subscribe(self, callback: Callable[[AppState], None]):
        """Subscribe to state changes."""
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[AppState], None]):
        """Unsubscribe from state changes."""
        if callback in self._observers:
            self._observers.remove(callback)

    def notify(self):
        """Notify all observers of state change."""
        for callback in self._observers:
            callback(self.state)

    def update(self, **kwargs):
        """Update state and notify observers."""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.notify()

    def add_query_to_history(self, item: QueryHistoryItem):
        """Add a query to history."""
        self.state.query_history.insert(0, item)
        # Keep last 100 queries
        if len(self.state.query_history) > 100:
            self.state.query_history = self.state.query_history[:100]
        self.notify()

    def set_patient(self, patient_id: int | None, patient_name: str = ""):
        """Set current patient context."""
        self.state.current_patient_id = patient_id
        self.state.current_patient_name = patient_name
        self.notify()

    def clear_patient(self):
        """Clear patient context."""
        self.set_patient(None, "")
