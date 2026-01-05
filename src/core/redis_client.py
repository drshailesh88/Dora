"""
Redis Client for Dora

Provides Redis connection and utilities for:
- MFA token storage with TTL
- Session caching
- Rate limiting
- General caching
"""

import os
import json
import logging
from typing import Optional, Any
from datetime import timedelta

try:
    import redis
    from redis import Redis, ConnectionPool
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client wrapper with fallback to in-memory storage.

    For production, ensure Redis is available.
    For development/testing, falls back to dict-based storage.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
    ):
        self.host = host or os.environ.get("REDIS_HOST", "localhost")
        self.port = port or int(os.environ.get("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.environ.get("REDIS_PASSWORD")

        self._client: Optional[Redis] = None
        self._fallback_storage: dict = {}
        self._use_fallback = False

        if HAS_REDIS:
            try:
                pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=decode_responses,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                self._client = Redis(connection_pool=pool)
                # Test connection
                self._client.ping()
                logger.info(f"Redis connected: {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"Redis connection failed, using fallback storage: {e}")
                self._use_fallback = True
        else:
            logger.warning("redis-py not installed, using fallback storage")
            self._use_fallback = True

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set key to value with optional expiration.

        Args:
            key: Key name
            value: Value (will be JSON serialized if dict/list)
            ex: Expiration in seconds
            px: Expiration in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if set, False otherwise
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        try:
            if self._use_fallback:
                if nx and key in self._fallback_storage:
                    return False
                if xx and key not in self._fallback_storage:
                    return False
                self._fallback_storage[key] = value
                return True
            else:
                return bool(self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx))
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.

        Args:
            key: Key name

        Returns:
            Value as string, or None if not found
        """
        try:
            if self._use_fallback:
                return self._fallback_storage.get(key)
            else:
                return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def get_json(self, key: str) -> Optional[Any]:
        """
        Get value and parse as JSON.

        Args:
            key: Key name

        Returns:
            Parsed JSON value, or None if not found
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        try:
            if self._use_fallback:
                count = 0
                for key in keys:
                    if key in self._fallback_storage:
                        del self._fallback_storage[key]
                        count += 1
                return count
            else:
                return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            *keys: Keys to check

        Returns:
            Number of existing keys
        """
        try:
            if self._use_fallback:
                return sum(1 for key in keys if key in self._fallback_storage)
            else:
                return self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on key.

        Args:
            key: Key name
            seconds: Seconds until expiration

        Returns:
            True if successful
        """
        try:
            if self._use_fallback:
                # Fallback doesn't support TTL
                return True
            else:
                return bool(self._client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get time to live for key.

        Args:
            key: Key name

        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            if self._use_fallback:
                return -1  # No TTL support in fallback
            else:
                return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -2

    def ping(self) -> bool:
        """
        Check if Redis is connected.

        Returns:
            True if connected, False otherwise
        """
        try:
            if self._use_fallback:
                return True  # Fallback always "works"
            else:
                return bool(self._client.ping())
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False

    def is_available(self) -> bool:
        """
        Check if real Redis is available (not fallback).

        Returns:
            True if using real Redis, False if using fallback
        """
        return not self._use_fallback and self.ping()


# MFA Token Storage
class MFATokenStore:
    """
    Secure storage for MFA tokens with automatic expiration.
    """

    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis = redis_client or get_redis_client()
        self.prefix = "mfa:token:"
        self.default_ttl = 300  # 5 minutes

    def store_token(
        self,
        token: str,
        user_id: str,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store MFA token for user.

        Args:
            token: MFA token
            user_id: User ID
            ttl_seconds: Time to live in seconds (default: 5 minutes)

        Returns:
            True if stored successfully
        """
        ttl = ttl_seconds or self.default_ttl
        key = f"{self.prefix}{token}"
        return self.redis.set(key, user_id, ex=ttl)

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify MFA token and get user ID.

        Args:
            token: MFA token to verify

        Returns:
            User ID if valid, None otherwise
        """
        key = f"{self.prefix}{token}"
        return self.redis.get(key)

    def consume_token(self, token: str) -> Optional[str]:
        """
        Verify and consume MFA token (one-time use).

        Args:
            token: MFA token

        Returns:
            User ID if valid, None otherwise
        """
        user_id = self.verify_token(token)
        if user_id:
            key = f"{self.prefix}{token}"
            self.redis.delete(key)
        return user_id

    def revoke_token(self, token: str) -> bool:
        """
        Revoke MFA token.

        Args:
            token: MFA token to revoke

        Returns:
            True if revoked
        """
        key = f"{self.prefix}{token}"
        return bool(self.redis.delete(key))


# Global instances
_redis_client: Optional[RedisClient] = None
_mfa_store: Optional[MFATokenStore] = None


def get_redis_client() -> RedisClient:
    """Get global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


def get_mfa_token_store() -> MFATokenStore:
    """Get global MFA token store instance."""
    global _mfa_store
    if _mfa_store is None:
        _mfa_store = MFATokenStore()
    return _mfa_store
