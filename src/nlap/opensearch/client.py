"""OpenSearch client manager with connection pooling and health checks."""

import asyncio
import time
from typing import Any, AsyncIterator, Optional, Union

try:
    from opensearchpy import AsyncOpenSearch, OpenSearch
    from opensearchpy.connection import RequestsHttpConnection
    HAS_ASYNC = True
except ImportError:
    # Fallback: opensearch-py may not have AsyncOpenSearch
    from opensearchpy import OpenSearch
    try:
        from opensearchpy.connection import RequestsHttpConnection
    except ImportError:
        RequestsHttpConnection = None  # type: ignore
    AsyncOpenSearch = None  # type: ignore
    HAS_ASYNC = False

from opensearchpy.exceptions import (
    AuthenticationException,
    ConnectionError,
    RequestError,
)

from nlap.config.settings import (
    OpenSearchClusterConfig,
    OpenSearchSettings,
    get_settings,
)
from nlap.opensearch.models import ConnectionHealth, QueryResult
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class OpenSearchManager:
    """OpenSearch connection manager with basic authentication and connection pooling."""

    def __init__(
        self,
        settings: Optional[Union[OpenSearchClusterConfig, OpenSearchSettings, dict]] = None,
    ) -> None:
        """Initialize OpenSearch manager.

        Args:
            settings: Optional settings override (for testing). Can be OpenSearchClusterConfig,
                     OpenSearchSettings, or a dict.
        """
        config = get_settings().opensearch if settings is None else settings
        self.config = config
        self._client: Optional[Any] = None  # Can be AsyncOpenSearch or None
        self._sync_client: Optional[OpenSearch] = None
        self._use_async = HAS_ASYNC and AsyncOpenSearch is not None
        self._metrics: dict[str, Any] = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0.0,
        }

    def _get_client_config(self) -> dict[str, Any]:
        """Get OpenSearch client configuration.

        Returns:
            Dictionary with client configuration
        """
        # Use host dict format with scheme (works better with RequestsHttpConnection)
        scheme = "https" if self.config.use_ssl else "http"
        hosts = [{
            "host": self.config.host,
            "port": self.config.port,
            "scheme": scheme
        }]

        config: dict[str, Any] = {
            "hosts": hosts,
            "http_auth": (self.config.username, self.config.password),
            "use_ssl": self.config.use_ssl,
            "verify_certs": self.config.verify_certs,
            "timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True,
            "http_compress": True,
        }

        # Use RequestsHttpConnection if available (fixes connection issues)
        if RequestsHttpConnection is not None:
            config["connection_class"] = RequestsHttpConnection
            config["pool_maxsize"] = 20
            config["sniff_on_start"] = False
            config["sniff_on_connection_fail"] = False
            config["sniff_timeout"] = None

        if self.config.ca_certs:
            config["ca_certs"] = self.config.ca_certs

        return config

    def get_client(self) -> Any:
        """Get or create async OpenSearch client instance.

        Returns:
            AsyncOpenSearch client instance if available, otherwise sync client wrapped
        """
        if self._use_async:
            if self._client is None:
                config = self._get_client_config()
                self._client = AsyncOpenSearch(**config)
                logger.info(
                    "OpenSearch async client initialized",
                    host=self.config.host,
                    port=self.config.port,
                    use_ssl=self.config.use_ssl,
                )
            return self._client
        else:
            # Use sync client with asyncio wrapper
            return self.get_sync_client()

    def get_sync_client(self) -> OpenSearch:
        """Get or create sync OpenSearch client instance (for testing/debugging).

        Returns:
            OpenSearch client instance
        """
        if self._sync_client is None:
            config = self._get_client_config()
            logger.debug(
                "Creating OpenSearch sync client",
                config_keys=list(config.keys()),
                connection_class=config.get("connection_class"),
                hosts=config.get("hosts"),
            )
            self._sync_client = OpenSearch(**config)
            logger.info(
                "OpenSearch sync client initialized",
                host=self.config.host,
                port=self.config.port,
                connection_class=config.get("connection_class"),
            )
        return self._sync_client

    async def test_connection(self) -> ConnectionHealth:
        """Test OpenSearch connection and return health status.

        Returns:
            ConnectionHealth object with status information
        """
        try:
            client = self.get_client()
            if self._use_async:
                info = await client.info()
            else:
                # Run sync operation in thread pool
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, client.info)

            logger.info(
                "OpenSearch connection test successful",
                cluster_name=info.get("cluster_name"),
                version=info.get("version", {}).get("number"),
            )

            return ConnectionHealth(
                healthy=True,
                cluster_name=info.get("cluster_name"),
                version=info.get("version", {}).get("number"),
            )
        except AuthenticationException as e:
            logger.error(
                "OpenSearch authentication failed",
                error=str(e),
                host=self.config.host,
            )
            return ConnectionHealth(healthy=False, error=f"Authentication failed: {str(e)}")
        except ConnectionError as e:
            logger.error(
                "OpenSearch connection failed",
                error=str(e),
                host=self.config.host,
            )
            return ConnectionHealth(healthy=False, error=f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(
                "OpenSearch health check failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return ConnectionHealth(healthy=False, error=f"Unexpected error: {str(e)}")

    async def execute_query(
        self,
        index: str,
        query: dict[str, Any],
        size: int = 10,
        from_: int = 0,
        **kwargs: Any,
    ) -> QueryResult:
        """Execute a search query against OpenSearch.

        Args:
            index: Index name to search
            query: OpenSearch query DSL dictionary
            size: Number of hits to return
            from_: Starting offset for pagination
            **kwargs: Additional search parameters

        Returns:
            QueryResult object with hits and metadata

        Raises:
            RequestError: If query execution fails
        """
        client = self.get_client()

        try:
            body = {
                "query": query,
                "size": size,
                "from": from_,
            }

            start_time = time.time()
            if self._use_async:
                response = await client.search(index=index, body=body, **kwargs)
            else:
                # Run sync operation in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: client.search(index=index, body=body, **kwargs)
                )
            latency = (time.time() - start_time) * 1000

            self._metrics["total_queries"] += 1
            self._metrics["successful_queries"] += 1
            self._metrics["total_latency_ms"] += latency

            logger.debug(
                "OpenSearch query executed",
                index=index,
                hits_count=response["hits"]["total"].get("value", 0)
                if isinstance(response["hits"]["total"], dict)
                else response["hits"]["total"],
                took=response.get("took", 0),
            )

            return QueryResult(
                hits=[hit["_source"] for hit in response["hits"]["hits"]],
                total=response["hits"]["total"].get("value", 0)
                if isinstance(response["hits"]["total"], dict)
                else response["hits"]["total"],
                took=response.get("took", 0),
                aggregations=response.get("aggregations"),
            )
        except RequestError as e:
            if "start_time" in locals():
                latency = (time.time() - start_time) * 1000
                self._metrics["failed_queries"] += 1
                self._metrics["total_latency_ms"] += latency
            logger.error(
                "OpenSearch query failed",
                error=str(e),
                error_type=type(e).__name__,
                index=index,
            )
            raise
        except Exception as e:
            if "start_time" in locals():
                latency = (time.time() - start_time) * 1000
                self._metrics["failed_queries"] += 1
                self._metrics["total_latency_ms"] += latency
            logger.error(
                "Unexpected error during query execution",
                error=str(e),
                error_type=type(e).__name__,
                index=index,
            )
            raise

    async def scroll_query(
        self,
        index: str,
        query: dict[str, Any],
        scroll: str = "1m",
        size: int = 100,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute a scroll query to retrieve large result sets.

        Args:
            index: Index name to search
            query: OpenSearch query DSL dictionary
            scroll: How long to keep the scroll context alive (e.g., "1m")
            size: Number of hits per batch
            **kwargs: Additional search parameters

        Yields:
            Dictionary containing hits and scroll_id for each batch
        """
        client = self.get_client()
        start_time = time.time()

        try:
            # Initial search with scroll
            self._metrics["total_queries"] += 1
            scroll_body = {
                "query": query,
            }
            if self._use_async:
                response = await client.search(
                    index=index,
                    body=scroll_body,
                    scroll=scroll,
                    size=size,
                    **kwargs,
                )
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.search(
                        index=index, body=scroll_body, scroll=scroll, size=size, **kwargs
                    ),
                )

            scroll_id = response.get("_scroll_id")
            hits = response["hits"]["hits"]

            while hits:
                yield {
                    "hits": [hit["_source"] for hit in hits],
                    "scroll_id": scroll_id,
                    "total": response["hits"]["total"].get("value", 0)
                    if isinstance(response["hits"]["total"], dict)
                    else response["hits"]["total"],
                }

                # Continue scrolling
                if scroll_id:
                    if self._use_async:
                        response = await client.scroll(
                            scroll_id=scroll_id,
                            scroll=scroll,
                        )
                    else:
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            lambda: client.scroll(scroll_id=scroll_id, scroll=scroll),
                        )
                    scroll_id = response.get("_scroll_id")
                    hits = response["hits"]["hits"]
                else:
                    break

            # Clear scroll context
            if scroll_id:
                try:
                    if self._use_async:
                        await client.clear_scroll(scroll_id=scroll_id)
                    else:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None, lambda: client.clear_scroll(scroll_id=scroll_id)
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to clear scroll context",
                        error=str(e),
                        scroll_id=scroll_id,
                    )

            latency = (time.time() - start_time) * 1000
            self._metrics["successful_queries"] += 1
            self._metrics["total_latency_ms"] += latency

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self._metrics["failed_queries"] += 1
            self._metrics["total_latency_ms"] += latency
            logger.error(
                "OpenSearch scroll query failed",
                error=str(e),
                error_type=type(e).__name__,
                index=index,
            )
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get connection and query metrics.

        Returns:
            Dictionary with metrics including total queries, success rate, and average latency
        """
        total = self._metrics["total_queries"]
        if total == 0:
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "success_rate": 100.0,
                "average_latency_ms": 0.0,
            }

        success_rate = (
            (self._metrics["successful_queries"] / total) * 100.0
            if total > 0
            else 100.0
        )
        avg_latency = (
            self._metrics["total_latency_ms"] / total if total > 0 else 0.0
        )

        return {
            "total_queries": total,
            "successful_queries": self._metrics["successful_queries"],
            "failed_queries": self._metrics["failed_queries"],
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
        }

    async def close(self) -> None:
        """Close OpenSearch client connections."""
        if self._client and self._use_async:
            await self._client.close()
            self._client = None
            logger.info("OpenSearch async client closed")

        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
            logger.info("OpenSearch sync client closed")

    async def __aenter__(self) -> "OpenSearchManager":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

