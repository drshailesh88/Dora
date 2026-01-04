"""
Push Notification Providers

Supports:
- Firebase Cloud Messaging (FCM)
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    HAS_HTTPX = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False


@dataclass
class PushResult:
    """Result of push notification send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class PushProvider(ABC):
    """Base class for push notification providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def send(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
    ) -> PushResult:
        """Send a push notification to a single device."""
        pass

    @abstractmethod
    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> PushResult:
        """Send a push notification to a topic."""
        pass

    @abstractmethod
    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> list[PushResult]:
        """Send to multiple devices."""
        pass


class FirebasePush(PushProvider):
    """Firebase Cloud Messaging (FCM) provider."""

    FCM_URL = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.credentials_path = credentials_path or os.environ.get("FIREBASE_CREDENTIALS_PATH")
        self.project_id = project_id or os.environ.get("FIREBASE_PROJECT_ID", "")

        self._initialized = False
        if HAS_FIREBASE and self.credentials_path and os.path.exists(self.credentials_path):
            try:
                if not firebase_admin._apps:
                    cred = credentials.Certificate(self.credentials_path)
                    firebase_admin.initialize_app(cred)
                self._initialized = True
            except Exception as e:
                print(f"Firebase init failed: {e}")

    @property
    def name(self) -> str:
        return "firebase"

    async def send(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
    ) -> PushResult:
        """Send a push notification via FCM."""
        if not self._initialized:
            return PushResult(success=False, error="Firebase not initialized")

        try:
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url,
            )

            android = messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_notification",
                    color="#0066CC",
                    sound="default",
                ),
            )

            apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body,
                        ),
                        sound="default",
                        badge=1,
                    ),
                ),
            )

            message = messaging.Message(
                notification=notification,
                android=android,
                apns=apns,
                data=data or {},
                token=token,
            )

            response = messaging.send(message)
            return PushResult(success=True, message_id=response)

        except Exception as e:
            return PushResult(success=False, error=str(e))

    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> PushResult:
        """Send a push notification to a topic."""
        if not self._initialized:
            return PushResult(success=False, error="Firebase not initialized")

        try:
            notification = messaging.Notification(
                title=title,
                body=body,
            )

            message = messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            return PushResult(success=True, message_id=response)

        except Exception as e:
            return PushResult(success=False, error=str(e))

    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> list[PushResult]:
        """Send to multiple devices."""
        if not self._initialized:
            return [PushResult(success=False, error="Firebase not initialized")] * len(tokens)

        try:
            notification = messaging.Notification(
                title=title,
                body=body,
            )

            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
            )

            response = messaging.send_multicast(message)

            results = []
            for i, resp in enumerate(response.responses):
                if resp.success:
                    results.append(PushResult(success=True, message_id=resp.message_id))
                else:
                    results.append(PushResult(success=False, error=str(resp.exception)))

            return results

        except Exception as e:
            return [PushResult(success=False, error=str(e))] * len(tokens)

    async def subscribe_to_topic(self, tokens: list[str], topic: str) -> bool:
        """Subscribe tokens to a topic."""
        if not self._initialized:
            return False

        try:
            messaging.subscribe_to_topic(tokens, topic)
            return True
        except Exception:
            return False

    async def unsubscribe_from_topic(self, tokens: list[str], topic: str) -> bool:
        """Unsubscribe tokens from a topic."""
        if not self._initialized:
            return False

        try:
            messaging.unsubscribe_from_topic(tokens, topic)
            return True
        except Exception:
            return False
