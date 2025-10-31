"""Schema discovery engine for OpenSearch indices."""

from typing import Any, Optional

from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.field_extractor import FieldExtractor
from nlap.opensearch.schema_cache import SchemaCache
from nlap.opensearch.schema_models import FieldInfo, FieldType, SchemaInfo
from nlap.opensearch.type_identifier import TypeIdentifier
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaDiscoveryEngine:
    """Main schema discovery engine orchestrating all components."""

    DEFAULT_SAMPLE_SIZE = 100

    def __init__(
        self,
        opensearch_manager: OpenSearchManager,
        cache: Optional[SchemaCache] = None,
        sample_size: int = DEFAULT_SAMPLE_SIZE,
    ):
        """Initialize schema discovery engine.

        Args:
            opensearch_manager: OpenSearchManager instance for querying
            cache: Optional SchemaCache instance (creates new one if not provided)
            sample_size: Default sample size for document analysis
        """
        self.opensearch_manager = opensearch_manager
        self.cache = cache or SchemaCache(default_ttl_seconds=3600)  # 1 hour default TTL
        self.field_extractor = FieldExtractor()
        self.type_identifier = TypeIdentifier()
        self.sample_size = sample_size

    async def discover_index_schema(
        self,
        index_name: str,
        sample_size: Optional[int] = 500,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> SchemaInfo:
        """Discover schema for an entire index.

        Args:
            index_name: Index name to analyze
            sample_size: Number of documents to sample (uses default if not provided)
            use_cache: Whether to use cached schema if available
            cache_ttl: Cache TTL in seconds (None = use cache default)

        Returns:
            SchemaInfo with discovered fields
        """
        size = sample_size or self.sample_size
        cache_key = self.cache.generate_cache_key(index_name, sample_size=size)

        # Check cache first
        if use_cache:
            cached_schema = self.cache.get(cache_key)
            if cached_schema:
                logger.info("Using cached schema", index_name=index_name, cache_key=cache_key)
                return cached_schema

        logger.info("Discovering schema", index_name=index_name, sample_size=size)

        # Query all documents (match_all) to get sample
        query = {"match_all": {}}
        query_result = await self.opensearch_manager.execute_query(
            index=index_name,
            query=query,
            size=size,
        )

        documents = query_result.hits
        schema = await self._build_schema_from_documents(
            index_name=index_name,
            documents=documents,
            total_analyzed=len(documents),
            sample_size=size,
        )

        # Cache the schema
        self.cache.set(cache_key, schema, ttl_seconds=cache_ttl)

        return schema

    async def discover_document_schema(
        self,
        index_name: str,
        query: dict[str, Any],
        sample_size: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> SchemaInfo:
        """Discover schema from documents matching query criteria.

        Args:
            index_name: Index name to search
            query: OpenSearch query DSL to filter documents
            sample_size: Number of documents to sample
            use_cache: Whether to use cached schema if available
            cache_ttl: Cache TTL in seconds (None = use cache default)

        Returns:
            SchemaInfo with discovered fields
        """
        size = sample_size or self.sample_size
        cache_key = self.cache.generate_cache_key(index_name, query=query, sample_size=size)

        # Check cache first
        if use_cache:
            cached_schema = self.cache.get(cache_key)
            if cached_schema:
                logger.info(
                    "Using cached schema for query",
                    index_name=index_name,
                    cache_key=cache_key,
                )
                return cached_schema

        logger.info(
            "Discovering schema from query",
            index_name=index_name,
            sample_size=size,
        )

        # Query documents matching criteria
        query_result = await self.opensearch_manager.execute_query(
            index=index_name,
            query=query,
            size=size,
        )

        documents = query_result.hits
        schema = await self._build_schema_from_documents(
            index_name=index_name,
            documents=documents,
            total_analyzed=len(documents),
            sample_size=size,
        )

        # Cache the schema
        self.cache.set(cache_key, schema, ttl_seconds=cache_ttl)

        return schema

    async def _build_schema_from_documents(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        total_analyzed: int,
        sample_size: int,
    ) -> SchemaInfo:
        """Build schema information from a list of documents.

        Args:
            index_name: Index name
            documents: List of documents to analyze
            total_analyzed: Total number of documents analyzed
            sample_size: Sample size used

        Returns:
            SchemaInfo with discovered fields
        """
        if not documents:
            logger.warning("No documents to analyze", index_name=index_name)
            return SchemaInfo(
                index_name=index_name,
                fields={},
                version=1,
                total_documents_analyzed=0,
                sample_size=sample_size,
            )

        # Extract all fields recursively
        field_values = self.field_extractor.extract_fields(documents)

        # Build FieldInfo for each field
        fields: dict[str, FieldInfo] = {}
        for field_path, sample_values in field_values.items():
            field_type = self.type_identifier.identify_field_type(field_path, sample_values)

            # Determine if field is array or nested
            is_array = field_type == FieldType.ARRAY or any(
                isinstance(v, list) for v in sample_values if v is not None
            )
            is_nested = field_type == FieldType.OBJECT or "." in field_path

            fields[field_path] = FieldInfo(
                name=field_path,
                field_type=field_type,
                sample_values=sample_values[:10],  # Limit to 10 sample values
                is_array=is_array,
                is_nested=is_nested,
            )

        # Get next version number
        version = self.cache._get_next_version(index_name)

        logger.info(
            "Schema discovery complete",
            index_name=index_name,
            fields_count=len(fields),
            version=version,
            documents_analyzed=total_analyzed,
        )

        return SchemaInfo(
            index_name=index_name,
            fields=fields,
            version=version,
            total_documents_analyzed=total_analyzed,
            sample_size=sample_size,
        )

    def invalidate_cache(self, index_name: Optional[str] = None, cache_key: Optional[str] = None) -> int:
        """Invalidate cached schemas.

        Args:
            index_name: Optional index name to invalidate (invalidates all schemas for index)
            cache_key: Optional specific cache key to invalidate

        Returns:
            Number of cache entries invalidated
        """
        if cache_key:
            return 1 if self.cache.invalidate(cache_key) else 0
        elif index_name:
            return self.cache.invalidate_index(index_name)
        else:
            self.cache.clear()
            return 0

