"""FastAPI dependencies for dependency injection."""

from nlap.azureopenai.client import AzureOpenAIClient
from nlap.opensearch.client import OpenSearchManager

# Global instances (initialized at startup)
_azure_openai_client: AzureOpenAIClient | None = None
_opensearch_manager: OpenSearchManager | None = None


def get_azure_openai_client() -> AzureOpenAIClient:
    """Get Azure OpenAI client instance."""
    if _azure_openai_client is None:
        raise RuntimeError("Azure OpenAI client not initialized")
    return _azure_openai_client


def get_opensearch_manager() -> OpenSearchManager:
    """Get OpenSearch manager instance."""
    if _opensearch_manager is None:
        raise RuntimeError("OpenSearch manager not initialized")
    return _opensearch_manager


async def initialize_clients() -> None:
    """Initialize global client instances."""
    global _azure_openai_client, _opensearch_manager

    _azure_openai_client = AzureOpenAIClient()
    _opensearch_manager = OpenSearchManager()

    # Test connections
    try:
        health = await _opensearch_manager.test_connection()
        if not health.healthy:
            raise RuntimeError(f"OpenSearch connection failed: {health.error}")
    except Exception as e:
        raise RuntimeError(f"Failed to initialize clients: {str(e)}") from e


async def close_clients() -> None:
    """Close global client instances."""
    global _azure_openai_client, _opensearch_manager

    if _azure_openai_client:
        await _azure_openai_client.close()
        _azure_openai_client = None

    if _opensearch_manager:
        await _opensearch_manager.close()
        _opensearch_manager = None

