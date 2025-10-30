"""OpenSearch client module."""

from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.field_extractor import FieldExtractor
from nlap.opensearch.models import ConnectionHealth, QueryResult
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_cache import SchemaCache
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.opensearch.schema_models import CachedSchema, FieldInfo, FieldType, SchemaInfo
from nlap.opensearch.type_identifier import TypeIdentifier

__all__ = [
    "OpenSearchManager",
    "ConnectionHealth",
    "QueryResult",
    "QueryBuilder",
    "SchemaDiscoveryEngine",
    "SchemaCache",
    "SchemaInfo",
    "FieldInfo",
    "FieldType",
    "CachedSchema",
    "FieldExtractor",
    "TypeIdentifier",
]

