"""REST API routes for natural language query processing."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from nlap.api.dependencies import (
    get_azure_openai_client,
    get_opensearch_manager,
)
from nlap.azureopenai.client import AzureOpenAIClient
from nlap.nlp.parser import NaturalLanguageParser
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for natural language query."""

    query: str = Field(..., description="Natural language query to process")
    index_names: Optional[list[str]] = Field(
        None,
        description="Optional list of OpenSearch index names to query. If not provided, will be inferred from query.",
    )
    discover_fields: bool = Field(
        True,
        description="Whether to discover schema fields before building the query",
    )
    size: Optional[int] = Field(
        None,
        description="Number of results to return (defaults to query builder default)",
    )
    from_: int = Field(
        0,
        alias="from",
        description="Starting offset for pagination",
    )


def _yield_json_chunk(event_type: str, data: dict) -> bytes:
    """Yield a JSON chunk for SSE format.
    
    Args:
        event_type: Event type identifier
        data: Data dictionary to encode
        
    Returns:
        Bytes formatted as SSE message
    """
    chunk = {
        "type": event_type,
        "data": data,
    }
    return f"data: {json.dumps(chunk)}\n\n".encode("utf-8")


@router.post("/stream")
async def process_query_stream(
    request: QueryRequest,
    azure_openai_client: AzureOpenAIClient = Depends(get_azure_openai_client),
    opensearch_manager: OpenSearchManager = Depends(get_opensearch_manager),
) -> StreamingResponse:
    """Process natural language query and stream the results step-by-step.
    
    This endpoint:
    1. Parses the natural language query
    2. Discovers required fields (if enabled)
    3. Builds the OpenSearch query
    4. Returns the final query
    
    All steps are streamed as Server-Sent Events (SSE).
    
    Args:
        request: Query request with natural language input
        azure_openai_client: Azure OpenAI client dependency
        opensearch_manager: OpenSearch manager dependency
        
    Returns:
        StreamingResponse with SSE formatted JSON chunks
    """
    
    async def generate():
        """Generator function for streaming responses."""
        try:
            # Step 1: Initialize components
            yield _yield_json_chunk(
                "status",
                {
                    "step": "initialization",
                    "message": "Initializing query processor...",
                },
            )
            
            parser = NaturalLanguageParser(azure_openai_client=azure_openai_client)
            schema_discovery = SchemaDiscoveryEngine(opensearch_manager)
            query_builder = QueryBuilder()
            
            # Step 2: Parse natural language query
            yield _yield_json_chunk(
                "status",
                {
                    "step": "parsing",
                    "message": "Parsing natural language query...",
                },
            )
            
            parsed_query = await parser.parse(
                query=request.query,
                index_names=request.index_names,
            )
            
            yield _yield_json_chunk(
                "parsed",
                {
                    "parsed_query": {
                        "original_query": parsed_query.original_query,
                        "intent": {
                            "category": parsed_query.intent.category.value if parsed_query.intent else None,
                            "confidence": parsed_query.intent.confidence if parsed_query.intent else None,
                        },
                        "index_names": parsed_query.index_names,
                        "date_range": {
                            "start_date": parsed_query.date_range.start_date.isoformat()
                            if parsed_query.date_range and parsed_query.date_range.start_date
                            else None,
                            "end_date": parsed_query.date_range.end_date.isoformat()
                            if parsed_query.date_range and parsed_query.date_range.end_date
                            else None,
                            "relative_period": parsed_query.date_range.relative_period
                            if parsed_query.date_range
                            else None,
                        }
                        if parsed_query.date_range
                        else None,
                        "filters": {
                            "must": [
                                {
                                    "field": c.field,
                                    "operator": c.operator.value,
                                    "value": c.value,
                                }
                                for c in parsed_query.filters.must
                            ],
                            "should": [
                                {
                                    "field": c.field,
                                    "operator": c.operator.value,
                                    "value": c.value,
                                }
                                for c in parsed_query.filters.should
                            ],
                            "must_not": [
                                {
                                    "field": c.field,
                                    "operator": c.operator.value,
                                    "value": c.value,
                                }
                                for c in parsed_query.filters.must_not
                            ],
                        },
                        "aggregations": [
                            {
                                "type": agg.type.value,
                                "field": agg.field,
                                "group_by": agg.group_by,
                                "alias": agg.alias,
                            }
                            for agg in parsed_query.aggregations
                        ],
                        "fields": parsed_query.fields,
                        "confidence": parsed_query.confidence,
                        "errors": parsed_query.errors,
                    },
                },
            )
            
            # Determine which indices to query
            index_names = parsed_query.index_names or request.index_names
            if not index_names:
                yield _yield_json_chunk(
                    "error",
                    {
                        "message": "No index names specified or inferred from query",
                        "parsed_query": parsed_query.original_query,
                    },
                )
                return
            
            # Step 3: Discover schema if enabled
            schema_info = None
            if request.discover_fields:
                yield _yield_json_chunk(
                    "status",
                    {
                        "step": "field_discovery",
                        "message": f"Discovering schema for indices: {', '.join(index_names)}...",
                    },
                )
                
                try:
                    # Discover schema for the first index (can be extended to handle multiple indices)
                    primary_index = index_names[0] if index_names else None
                    if primary_index:
                        # Handle wildcard indices by trying to discover from a specific match
                        # if "*" in primary_index:
                        #     # For wildcard indices, we'll skip detailed discovery
                        #     # but still use what we can infer from the parsed query
                        #     yield _yield_json_chunk(
                        #         "status",
                        #         {
                        #             "step": "field_discovery",
                        #             "message": "Wildcard index detected, skipping detailed schema discovery",
                        #         },
                        #     )
                        # else:
                        schema_info = await schema_discovery.discover_index_schema(
                            index_name=primary_index,
                            use_cache=True,
                        )

                        yield _yield_json_chunk(
                            "schema_discovered",
                            {
                                "schema": {
                                    "index_name": schema_info.index_name,
                                    "total_fields": len(schema_info.fields),
                                    "field_count_by_type": {
                                        ft.value: sum(
                                            1
                                            for f in schema_info.fields.values()
                                            if f.field_type == ft
                                        )
                                        for ft in [
                                            schema_info.fields[f].field_type
                                            for f in list(schema_info.fields.keys())[:10]
                                        ]
                                    }
                                    if schema_info.fields
                                    else {},
                                },
                            },
                        )
                except Exception as e:
                    logger.warning(
                        "Schema discovery failed, continuing without schema info",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    yield _yield_json_chunk(
                        "warning",
                        {
                            "step": "field_discovery",
                            "message": f"Schema discovery failed: {str(e)}",
                        },
                    )
            
            # Update query builder with schema info
            query_builder.schema_info = schema_info
            
            # Step 4: Build OpenSearch query
            yield _yield_json_chunk(
                "status",
                {
                    "step": "query_building",
                    "message": "Building OpenSearch query...",
                },
            )
            
            opensearch_query = query_builder.build_query(
                parsed_query=parsed_query,
                size=request.size,
                from_=request.from_,
            )
            
            yield _yield_json_chunk(
                "query_built",
                {
                    "opensearch_query": opensearch_query,
                    "metadata": {
                        "index_names": index_names,
                        "query_size": opensearch_query.get("size"),
                        "from": opensearch_query.get("from"),
                        "has_aggregations": bool(opensearch_query.get("aggs")),
                        "has_sort": bool(opensearch_query.get("sort")),
                        "has_source": bool(opensearch_query.get("_source")),
                    },
                },
            )
            
            # Step 5: Final summary
            yield _yield_json_chunk(
                "complete",
                {
                    "message": "Query processing complete",
                    "summary": {
                        "original_query": parsed_query.original_query,
                        "intent_category": parsed_query.intent.category.value if parsed_query.intent else None,
                        "confidence": parsed_query.confidence,
                        "index_names": index_names,
                        "query_built": True,
                        "schema_discovered": schema_info is not None,
                    },
                },
            )
            
        except Exception as e:
            logger.error(
                "Error processing query",
                error=str(e),
                error_type=type(e).__name__,
                query=request.query[:100] if request.query else None,
            )
            yield _yield_json_chunk(
                "error",
                {
                    "message": f"Error processing query: {str(e)}",
                    "error_type": type(e).__name__,
                },
            )
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("")
async def process_query(
    request: QueryRequest,
    azure_openai_client: AzureOpenAIClient = Depends(get_azure_openai_client),
    opensearch_manager: OpenSearchManager = Depends(get_opensearch_manager),
) -> dict:
    """Process natural language query and return the OpenSearch query.
    
    This is a non-streaming version that returns all results at once.
    
    Args:
        request: Query request with natural language input
        azure_openai_client: Azure OpenAI client dependency
        opensearch_manager: OpenSearch manager dependency
        
    Returns:
        Dictionary with parsed query and OpenSearch query
    """
    try:
        # Initialize components
        parser = NaturalLanguageParser(azure_openai_client=azure_openai_client)
        schema_discovery = SchemaDiscoveryEngine(opensearch_manager)
        query_builder = QueryBuilder()
        
        # Parse query
        parsed_query = await parser.parse(
            query=request.query,
            index_names=request.index_names,
        )
        
        # Determine indices
        index_names = parsed_query.index_names or request.index_names
        if not index_names:
            raise HTTPException(
                status_code=400,
                detail="No index names specified or inferred from query",
            )
        
        # Discover schema if enabled
        schema_info = None
        if request.discover_fields:
            try:
                primary_index = index_names[0] if index_names else None
                if primary_index and "*" not in primary_index:
                    schema_info = await schema_discovery.discover_index_schema(
                        index_name=primary_index,
                        use_cache=True,
                    )
            except Exception as e:
                logger.warning(
                    "Schema discovery failed, continuing without schema info",
                    error=str(e),
                )
        
        # Update query builder
        query_builder.schema_info = schema_info
        
        # Build query
        opensearch_query = query_builder.build_query(
            parsed_query=parsed_query,
            size=request.size,
            from_=request.from_,
        )
        
        return {
            "success": True,
            "parsed_query": {
                "original_query": parsed_query.original_query,
                "intent": {
                    "category": parsed_query.intent.category.value if parsed_query.intent else None,
                    "confidence": parsed_query.intent.confidence if parsed_query.intent else None,
                },
                "index_names": parsed_query.index_names,
                "date_range": {
                    "start_date": parsed_query.date_range.start_date.isoformat()
                    if parsed_query.date_range and parsed_query.date_range.start_date
                    else None,
                    "end_date": parsed_query.date_range.end_date.isoformat()
                    if parsed_query.date_range and parsed_query.date_range.end_date
                    else None,
                    "relative_period": parsed_query.date_range.relative_period
                    if parsed_query.date_range
                    else None,
                }
                if parsed_query.date_range
                else None,
                "filters": {
                    "must": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value,
                        }
                        for c in parsed_query.filters.must
                    ],
                    "should": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value,
                        }
                        for c in parsed_query.filters.should
                    ],
                    "must_not": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value,
                        }
                        for c in parsed_query.filters.must_not
                    ],
                },
                "aggregations": [
                    {
                        "type": agg.type.value,
                        "field": agg.field,
                        "group_by": agg.group_by,
                        "alias": agg.alias,
                    }
                    for agg in parsed_query.aggregations
                ],
                "fields": parsed_query.fields,
                "confidence": parsed_query.confidence,
                "errors": parsed_query.errors,
            },
            "opensearch_query": opensearch_query,
            "metadata": {
                "index_names": index_names,
                "query_size": opensearch_query.get("size"),
                "from": opensearch_query.get("from"),
                "has_aggregations": bool(opensearch_query.get("aggs")),
                "has_sort": bool(opensearch_query.get("sort")),
                "has_source": bool(opensearch_query.get("_source")),
                "schema_discovered": schema_info is not None,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error processing query",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )
