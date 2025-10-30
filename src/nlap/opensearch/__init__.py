"""OpenSearch client module."""

from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.models import ConnectionHealth, QueryResult

__all__ = ["OpenSearchManager", "ConnectionHealth", "QueryResult"]

