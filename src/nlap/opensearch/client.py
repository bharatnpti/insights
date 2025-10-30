"""OpenSearch client manager with connection pooling and health checks."""

from typing import Any, Optional

from opensearchpy import AsyncOpenSearch, OpenSearch
from opensearchpy.exceptions import (
    AuthenticationException,
    ConnectionError,
    RequestError,
)

from nlap.config.settings import get_settings
from nlap.opensearch.models import ConnectionHealth, QueryResult
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class OpenSearchManager:
    """OpenSearch connection manager with basic authentication and connection pooling."""

    def __init__(self, settings: Optional[dict] = None) -> None:
        """Initialize OpenSearch manager.

        Args:
            settings: Optional settings override (for testing)
        """
        config = get_settings().opensearch if settings is None else settings
        self.config = config
        self._client: Optional[AsyncOpenSearch] = None
        self._sync_client: Optional[OpenSearch] = None

    def _get_client_config(self) -> dict[str, Any]:
        """Get OpenSearch client configuration.

        Returns:
            Dictionary with client configuration
        """
        config: dict[str, Any] = {
            "hosts": [self.config.url],
            "http_auth": (self.config.username, self.config.password),
            "use_ssl": self.config.use_ssl,
            "verify_certs": self.config.verify_certs,
            "timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True,
        }

        if self.config.ca_certs:
            config["ca_certs"] = self.config.ca_certs

        return config

    def get_client(self) -> AsyncOpenSearch:
        """Get or create async OpenSearch client instance.

        Returns:
            AsyncOpenSearch client instance
        """
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

    def get_sync_client(self) -> OpenSearch:
        """Get or create sync OpenSearch client instance (for testing/debugging).

        Returns:
            OpenSearch client instance
        """
        if self._sync_client is None:
            config = self._get_client_config()
            self._sync_client = OpenSearch(**config)
            logger.info(
                "OpenSearch sync client initialized",
                host=self.config.host,
                port=self.config.port,
            )
        return self._sync_client

    async def test_connection(self) -> ConnectionHealth:
        """Test OpenSearch connection and return health status.

        Returns:
            ConnectionHealth object with status information
        """
        try:
            client = self.get_client()
            info = await client.info()

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
                **query,
                "size": size,
                "from": from_,
            }

            response = await client.search(index=index, body=body, **kwargs)

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
            logger.error(
                "OpenSearch query failed",
                error=str(e),
                error_type=type(e).__name__,
                index=index,
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during query execution",
                error=str(e),
                error_type=type(e).__name__,
                index=index,
            )
            raise

    async def close(self) -> None:
        """Close OpenSearch client connections."""
        if self._client:
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

