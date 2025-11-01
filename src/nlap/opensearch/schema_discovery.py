"""Schema discovery engine for OpenSearch indices."""

import json
from typing import Any, Optional

from nlap.azureopenai.client import AzureOpenAIClient
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.field_extractor import FieldExtractor
from nlap.opensearch.schema_cache import SchemaCache
from nlap.opensearch.schema_models import FieldInfo, FieldType, SchemaInfo
from nlap.opensearch.type_identifier import TypeIdentifier
from nlap.utils.logger import get_logger
from nlap.utils.prompt_loader import load_prompt

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

    async def _identify_id_fields(
        self,
        index_mapping: dict[str, Any],
        conv_id: Optional[str],
        turn_id: Optional[str],
        azure_client: AzureOpenAIClient,
    ) -> list[str]:
        """Use LLM to identify which fields in the mapping correspond to conv_id/turn_id.

        Args:
            index_mapping: Index mapping from OpenSearch
            conv_id: Optional conversation ID value
            turn_id: Optional turn ID value
            azure_client: Azure OpenAI client for LLM calls

        Returns:
            List of field names that should be queried
        """
        # Build the system prompt
        system_prompt = load_prompt("schema_id_fields.txt")

        # Build user prompt
        user_prompt_parts = [
            "Index mapping:",
            json.dumps(index_mapping, indent=2),
        ]
        if conv_id:
            user_prompt_parts.append(f"\nConversation ID to match: {conv_id}")
        if turn_id:
            user_prompt_parts.append(f"Turn ID to match: {turn_id}")

        user_prompt = "\n".join(user_prompt_parts)
        user_prompt += "\n\nReturn a JSON array of field names that should be queried for these IDs."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await azure_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=1000,
            )

            content = response["choices"][0]["message"]["content"]
            logger.debug("LLM field identification response received", content_length=len(content))

            # Parse JSON response
            try:
                # Try to extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                field_names = json.loads(content)
                if isinstance(field_names, list):
                    logger.info(
                        "Fields identified for IDs",
                        conv_id=conv_id,
                        turn_id=turn_id,
                        field_count=len(field_names),
                        fields=field_names,
                    )
                    return field_names
                else:
                    logger.warning("LLM returned non-list field names", response_type=type(field_names).__name__)
                    return []

            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse LLM JSON response for field identification",
                    error=str(e),
                    content=content[:500],
                )
                return []

        except Exception as e:
            logger.error(
                "LLM field identification failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    async def _generate_query_by_ids(
        self,
        index_mapping: dict[str, Any],
        conv_id: Optional[str],
        turn_id: Optional[str],
        azure_client: AzureOpenAIClient,
    ) -> dict[str, Any]:
        """Use LLM to generate a complete OpenSearch query to fetch documents by conv_id/turn_id.

        Args:
            index_mapping: Index mapping from OpenSearch
            conv_id: Optional conversation ID value
            turn_id: Optional turn ID value
            azure_client: Azure OpenAI client for LLM calls

        Returns:
            Complete OpenSearch query DSL dictionary
        """
        # Build the system prompt
        system_prompt = load_prompt("schema_query_generation.txt")

        # Build user prompt
        user_prompt_parts = [
            "Index mapping:",
            json.dumps(index_mapping, indent=2),
        ]
        if conv_id:
            user_prompt_parts.append(f"\nConversation ID to match: {conv_id}")
        if turn_id:
            user_prompt_parts.append(f"\nTurn ID to match: {turn_id}")

        user_prompt = "\n".join(user_prompt_parts)
        user_prompt += "\n\nCreate a complete OpenSearch query DSL query that will fetch all documents matching these IDs. Return only the JSON query object."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await azure_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=2000,  # Increased for complete query
            )

            content = response["choices"][0]["message"]["content"]
            logger.debug(
                "LLM query generation response received",
                content_length=len(content),
                content_preview=content[:200] if len(content) > 200 else content,
            )

            # Parse JSON response
            try:
                # Try to extract JSON if it's wrapped in markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                query = json.loads(content)
                if isinstance(query, dict):
                    # Validate that it's a valid query DSL (should have query type keys)
                    valid_query_types = [
                        "match_all", "match", "match_phrase", "term", "terms",
                        "range", "bool", "should", "must", "must_not", "filter",
                        "wildcard", "prefix", "regexp", "exists", "nested"
                    ]
                    
                    # Check if the query has any valid query type at the top level
                    has_valid_query_type = any(key in query for key in valid_query_types)
                    
                    # If it doesn't have a valid query type and has a "query" key, unwrap it
                    # This handles cases where LLM wrapped it like {"query": {"bool": {...}}}
                    if not has_valid_query_type and "query" in query:
                        logger.debug(
                            "Query wrapped in 'query' key, unwrapping",
                            outer_keys=list(query.keys()),
                        )
                        query = query["query"]
                        # Re-check after unwrapping
                        if isinstance(query, dict):
                            has_valid_query_type = any(key in query for key in valid_query_types)
                    
                    # If still no valid query type, it might be a nested structure
                    if not has_valid_query_type and isinstance(query, dict):
                        logger.warning(
                            "Query doesn't have expected query type structure",
                            query_keys=list(query.keys()),
                        )
                        # Last attempt: if there's a "query" key anywhere, use it
                        if "query" in query:
                            query = query["query"]
                            if isinstance(query, dict):
                                has_valid_query_type = any(key in query for key in valid_query_types)
                        elif len(query) == 1:
                            # If only one key, use its value (might be the actual query)
                            single_key = list(query.keys())[0]
                            if isinstance(query[single_key], dict):
                                query = query[single_key]
                                has_valid_query_type = any(key in query for key in valid_query_types)
                    
                    # Final validation: if still no valid query type, fall back to match_all
                    if not has_valid_query_type or not isinstance(query, dict):
                        logger.warning(
                            "Generated query is not valid OpenSearch query DSL, falling back to match_all",
                            original_query_type=type(query).__name__,
                            original_keys=list(query.keys()) if isinstance(query, dict) else None,
                        )
                        return {"match_all": {}}
                    
                    logger.info(
                        "Generated OpenSearch query from LLM",
                        conv_id=conv_id,
                        turn_id=turn_id,
                        query_keys=list(query.keys()) if isinstance(query, dict) else "not_dict",
                    )
                    return query
                else:
                    logger.warning(
                        "LLM returned non-dict query",
                        response_type=type(query).__name__,
                    )
                    # Fallback: use match_all
                    return {"match_all": {}}

            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse LLM JSON response for query generation",
                    error=str(e),
                    content=content[:500],
                )
                # Fallback: use match_all
                return {"match_all": {}}

        except Exception as e:
            logger.error(
                "LLM query generation failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Fallback: use match_all
            return {"match_all": {}}

    async def discover_schema_by_ids(
        self,
        index_name: str,
        conv_id: Optional[str],
        turn_id: Optional[str],
        azure_client: AzureOpenAIClient,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> SchemaInfo:
        """Discover schema from all documents matching conv_id/turn_id.

        This method:
        1. Fetches the index mapping
        2. Uses LLM to generate a complete OpenSearch query to fetch documents by conv_id/turn_id
        3. Fetches ALL documents using scroll API
        4. Builds schema from all fetched documents

        Args:
            index_name: Index name to search
            conv_id: Optional conversation ID to match
            turn_id: Optional turn ID to match
            azure_client: Azure OpenAI client for LLM calls
            use_cache: Whether to use cached schema if available
            cache_ttl: Cache TTL in seconds (None = use cache default)

        Returns:
            SchemaInfo with discovered fields from matching documents
        """
        # Generate cache key
        cache_key = self.cache.generate_cache_key(
            index_name, conv_id=conv_id, turn_id=turn_id, sample_size=None
        )

        # Check cache first
        if use_cache:
            cached_schema = self.cache.get(cache_key)
            if cached_schema:
                logger.info(
                    "Using cached schema for IDs",
                    index_name=index_name,
                    conv_id=conv_id,
                    turn_id=turn_id,
                    cache_key=cache_key,
                )
                return cached_schema

        logger.info(
            "Discovering schema from IDs",
            index_name=index_name,
            conv_id=conv_id,
            turn_id=turn_id,
        )

        # Step 1: Fetch index mapping
        try:
            index_mapping = await self.opensearch_manager.get_index_mapping(index_name)
            logger.debug("Index mapping retrieved", index_name=index_name)
        except Exception as e:
            logger.error(
                "Failed to retrieve index mapping",
                error=str(e),
                error_type=type(e).__name__,
                index_name=index_name,
            )
            raise

        # Step 2: Use LLM to generate complete query
        query = await self._generate_query_by_ids(index_mapping, conv_id, turn_id, azure_client)

        logger.info(
            "Generated query for ID-based schema discovery",
            index_name=index_name,
            query=query,
        )

        # Step 3: Fetch ALL documents using scroll API
        all_documents: list[dict[str, Any]] = []
        total_documents = 0

        try:
            async for batch in self.opensearch_manager.scroll_query(
                index=index_name,
                query=query,
                scroll="5m",  # 5 minute scroll duration
                size=1000,  # Batch size
            ):
                batch_hits = batch.get("hits", [])
                all_documents.extend(batch_hits)
                total_documents += len(batch_hits)
                logger.debug(
                    "Scrolled batch",
                    index_name=index_name,
                    batch_size=len(batch_hits),
                    total_accumulated=len(all_documents),
                )
        except Exception as e:
            logger.error(
                "Failed to scroll documents",
                error=str(e),
                error_type=type(e).__name__,
                index_name=index_name,
            )
            raise

        logger.info(
            "Finished scrolling documents",
            index_name=index_name,
            total_documents=total_documents,
        )

        # Step 4: Build schema from all documents
        schema = await self._build_schema_from_documents(
            index_name=index_name,
            documents=all_documents,
            total_analyzed=total_documents,
            sample_size=total_documents,  # No limit for ID-based discovery
        )

        # Cache the schema
        self.cache.set(cache_key, schema, ttl_seconds=cache_ttl)

        return schema

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

