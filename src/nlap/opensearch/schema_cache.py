"""Schema caching and versioning management."""

from datetime import datetime, timedelta
from typing import Optional

from nlap.opensearch.schema_models import CachedSchema, SchemaInfo
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaCache:
    """Manages schema caching and versioning following Single Responsibility Principle."""

    def __init__(self, default_ttl_seconds: Optional[int] = None):
        """Initialize schema cache.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (None = no expiration)
        """
        self._cache: dict[str, CachedSchema] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, cache_key: str) -> Optional[SchemaInfo]:
        """Get schema from cache if available and not expired.

        Args:
            cache_key: Cache key identifier

        Returns:
            SchemaInfo if found and valid, None otherwise
        """
        if cache_key not in self._cache:
            return None

        cached = self._cache[cache_key]

        # Check expiration
        if cached.expires_at and datetime.utcnow() > cached.expires_at:
            logger.debug("Cache entry expired", cache_key=cache_key)
            del self._cache[cache_key]
            return None

        logger.debug("Cache hit", cache_key=cache_key, version=cached.schema_info.version)
        return cached.schema_info

    def set(
        self,
        cache_key: str,
        schema: SchemaInfo,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store schema in cache.

        Args:
            cache_key: Cache key identifier
            schema: SchemaInfo to cache
            ttl_seconds: Time-to-live in seconds (None = use default, 0 = no expiration)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = None

        if ttl and ttl > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        cached_schema = CachedSchema(
            schema_info=schema,
            cache_key=cache_key,
            cached_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        self._cache[cache_key] = cached_schema
        logger.info(
            "Schema cached",
            cache_key=cache_key,
            index=schema.index_name,
            version=schema.version,
            expires_at=expires_at,
        )

    def invalidate(self, cache_key: str) -> bool:
        """Invalidate a cached schema.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if schema was found and removed, False otherwise
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info("Schema cache invalidated", cache_key=cache_key)
            return True
        return False

    def invalidate_index(self, index_name: str) -> int:
        """Invalidate all cached schemas for an index.

        Args:
            index_name: Index name to invalidate

        Returns:
            Number of cache entries invalidated
        """
        keys_to_remove = [
            key
            for key, cached in self._cache.items()
            if cached.schema_info.index_name == index_name
        ]

        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            logger.info(
                "Index schemas invalidated",
                index_name=index_name,
                count=len(keys_to_remove),
            )

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cached schemas."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("Schema cache cleared", entries_cleared=count)

    def get_cached_keys(self) -> list[str]:
        """Get all valid cache keys.

        Returns:
            List of cache keys
        """
        # Remove expired entries
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, cached in self._cache.items()
            if cached.expires_at and now > cached.expires_at
        ]

        for key in expired_keys:
            del self._cache[key]

        return list(self._cache.keys())

    def generate_cache_key(
        self,
        index_name: str,
        query: Optional[dict] = None,
        sample_size: Optional[int] = None,
    ) -> str:
        """Generate a cache key for a schema.

        Args:
            index_name: Index name
            query: Optional query criteria (for document-based discovery)
            sample_size: Optional sample size

        Returns:
            Cache key string
        """
        import hashlib
        import json

        key_parts = [index_name]

        if query:
            # Normalize query for consistent key generation
            key_parts.append(json.dumps(query, sort_keys=True))

        if sample_size:
            key_parts.append(str(sample_size))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_next_version(self, index_name: str) -> int:
        """Get next version number for an index schema.

        Args:
            index_name: Index name

        Returns:
            Next version number
        """
        existing_versions = [
            cached.schema_info.version
            for cached in self._cache.values()
            if cached.schema_info.index_name == index_name
        ]

        return max(existing_versions, default=0) + 1

