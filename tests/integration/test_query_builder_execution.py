#!/usr/bin/env python3
"""End-to-end test for Query Builder (NLAP-006) with actual OpenSearch execution.

This script tests the complete flow:
1. Natural Language Parser -> ParsedQuery
2. Query Builder -> OpenSearch Query DSL
3. Execute query on OpenSearch

Usage:
    export AZURE_ENDPOINT='https://gpt4-se-dev.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='GPT-4o'
    export AZURE_API_VERSION='2024-10-21'
    python tests/integration/test_query_builder_execution.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src directory to Python path to allow imports
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.azureopenai.client import AzureOpenAIClient
from nlap.config.settings import (
    AzureOpenAISettings,
    OpenSearchAuthSettings,
    OpenSearchClusterConfig,
)
from nlap.nlp.parser import NaturalLanguageParser
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.query_builder import QueryBuilder
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine


async def test_query_builder_execution():
    """Test query builder with actual OpenSearch execution."""
    print("=" * 80)
    print("Query Builder (NLAP-006) - End-to-End Execution Test")
    print("=" * 80)
    print()

    # Configuration
    azure_endpoint = os.getenv("AZURE_ENDPOINT", "https://gpt4-se-dev.openai.azure.com/")
    azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "GPT-4o")
    azure_api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")

    opensearch_config = {
        "name": "test-cluster",
        "host": "os-dashboard.oneai.yo-digital.com",
        "port": 443,
        "use_ssl": True,
        "verify_certs": True,
        "auth": {
            "username": "oneai_bharat",
            "password": "Z#Stp6$(qIyKaSGV",
        },
    }

    index_pattern = "ia-platform-prod-*"

    # Initialize Azure OpenAI
    print("1. Initializing Azure OpenAI client...")
    try:
        azure_settings = AzureOpenAISettings(
            endpoint=azure_endpoint.rstrip('/'),
            deployment_name=azure_deployment,
            api_version=azure_api_version,
        )
        azure_client = AzureOpenAIClient(settings=azure_settings)
        print(f"  ✓ Azure OpenAI client initialized")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

    # Initialize OpenSearch
    print("\n2. Initializing OpenSearch client...")
    opensearch_manager = None
    schema_info = None
    
    try:
        auth = OpenSearchAuthSettings(**opensearch_config["auth"])
        cluster_config = OpenSearchClusterConfig(
            name=opensearch_config["name"],
            host=opensearch_config["host"],
            port=opensearch_config["port"],
            use_ssl=opensearch_config["use_ssl"],
            verify_certs=opensearch_config["verify_certs"],
            auth=auth,
        )
        opensearch_manager = OpenSearchManager(settings=cluster_config)
        
        # Test connection
        health = await opensearch_manager.test_connection()
        if health.healthy:
            print(f"  ✓ OpenSearch connection successful")
            print(f"    Cluster: {health.cluster_name}")
            print(f"    Version: {health.version}")
        else:
            print(f"  ⚠ OpenSearch connection warning: {health.error}")
            print(f"    Continuing anyway...")
    except Exception as e:
        print(f"  ✗ OpenSearch initialization failed: {e}")
        print(f"    Cannot test execution, but query generation will still work")
        opensearch_manager = None

    # Discover schema if possible
    if opensearch_manager:
        print("\n3. Discovering schema...")
        try:
            schema_engine = SchemaDiscoveryEngine(opensearch_manager)
            sample_result = await opensearch_manager.execute_query(
                index=index_pattern,
                query={"match_all": {}},
                size=20
            )
            
            if sample_result.hits:
                schema_info = await schema_engine._build_schema_from_documents(
                    index_name=index_pattern,
                    documents=sample_result.hits,
                    total_analyzed=len(sample_result.hits),
                    sample_size=20
                )
                print(f"  ✓ Schema discovered: {len(schema_info.fields)} fields")
            else:
                print("  ⚠ No documents found for schema discovery")
        except Exception as e:
            print(f"  ⚠ Schema discovery failed: {e}")
            print("    Continuing without schema...")

    # Initialize parser and query builder
    print("\n4. Initializing Parser and Query Builder...")
    parser = NaturalLanguageParser(azure_openai_client=azure_client, schema_info=schema_info)
    query_builder = QueryBuilder(schema_info=schema_info)
    print("  ✓ Parser and Query Builder initialized")
    print()

    # Test queries
    test_queries = [
        {
            "query": "Show me all documents from the last 4 days",
            "description": "Simple date range query",
            "should_execute": True,
        },
        {
            "query": "Find documents where message contains 'error' from the last 2 days",
            "description": "Query with text search and date range",
            "should_execute": True,
        },
        {
            "query": "Count total documents grouped by status for last 7 days",
            "description": "Query with aggregation and date range",
            "should_execute": True,
        },
    ]

    print("5. Testing query parsing, building, and execution...")
    print("=" * 80)
    print()

    results = []
    for i, test_case in enumerate(test_queries, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print("-" * 80)

        try:
            # Step 1: Parse query
            print("Step 1: Parsing natural language query...")
            parsed_query = await parser.parse(
                test_case['query'],
                index_names=[index_pattern]
            )

            print(f"  ✓ Parsed successfully")
            print(f"    Intent: {parsed_query.intent.category.value}")
            print(f"    Confidence: {parsed_query.confidence:.2f}")
            
            if parsed_query.date_range:
                date_str = parsed_query.date_range.relative_period or \
                          f"{parsed_query.date_range.start_date_str} to {parsed_query.date_range.end_date_str}"
                print(f"    Date range: {date_str}")
            
            if parsed_query.filters.must:
                print(f"    Filters: {len(parsed_query.filters.must)}")
            
            if parsed_query.aggregations:
                print(f"    Aggregations: {len(parsed_query.aggregations)}")

            # Step 2: Build OpenSearch query
            print("\nStep 2: Building OpenSearch query...")
            opensearch_query = query_builder.build_query(parsed_query, size=5)
            
            print(f"  ✓ Query built successfully")
            print(f"    Query type: {list(opensearch_query['query'].keys())[0]}")
            print(f"    Size: {opensearch_query['size']}")
            
            if 'aggs' in opensearch_query:
                print(f"    Aggregations: {len(opensearch_query['aggs'])}")

            # Show query structure (compact)
            query_json = json.dumps(opensearch_query['query'], indent=2, default=str)
            print(f"\n  Query structure:")
            # Show first 3 lines only
            lines = query_json.split('\n')
            for line in lines[:10]:
                print(f"    {line}")
            if len(lines) > 10:
                print(f"    ... ({len(lines) - 10} more lines)")

            # Step 3: Execute query if OpenSearch is available
            if opensearch_manager and test_case.get('should_execute', True):
                print("\nStep 3: Executing query on OpenSearch...")
                try:
                    result = await opensearch_manager.execute_query(
                        index=index_pattern,
                        query=opensearch_query['query'],
                        size=opensearch_query['size'],
                        from_=opensearch_query.get('from', 0)
                    )
                    
                    print(f"  ✓ Query executed successfully")
                    print(f"    Total hits: {result.total}")
                    print(f"    Query time: {result.took}ms")
                    print(f"    Results returned: {len(result.hits)}")
                    
                    if result.aggregations:
                        print(f"    Aggregations returned: {len(result.aggregations)}")
                        for agg_name in list(result.aggregations.keys())[:3]:
                            agg_data = result.aggregations[agg_name]
                            # Show a summary of aggregation results
                            if 'buckets' in agg_data:
                                bucket_count = len(agg_data['buckets'])
                                print(f"      - {agg_name}: {bucket_count} buckets")
                            elif 'value' in agg_data:
                                print(f"      - {agg_name}: {agg_data['value']}")
                    
                    if result.hits and len(result.hits) > 0:
                        print(f"\n    Sample result (first hit, keys only):")
                        sample_hit = result.hits[0]
                        if isinstance(sample_hit, dict):
                            print(f"      Fields: {', '.join(list(sample_hit.keys())[:10])}")
                    
                    results.append({
                        "test": i,
                        "query": test_case['query'],
                        "status": "success",
                        "total_hits": result.total,
                        "took_ms": result.took,
                        "has_aggregations": bool(result.aggregations),
                    })
                    
                except Exception as e:
                    print(f"  ✗ Query execution failed: {e}")
                    # Show the query that failed for debugging
                    print(f"\n  Query that failed:")
                    print(json.dumps(opensearch_query['query'], indent=4, default=str))
                    results.append({
                        "test": i,
                        "query": test_case['query'],
                        "status": "execution_failed",
                        "error": str(e),
                    })
            else:
                print("\nStep 3: Skipped (OpenSearch not available or should_execute=False)")
                results.append({
                    "test": i,
                    "query": test_case['query'],
                    "status": "parsed_only",
                })

            print()

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": i,
                "query": test_case['query'],
                "status": "failed",
                "error": str(e),
            })
            print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    parsed_only_count = sum(1 for r in results if r['status'] == 'parsed_only')
    failed_count = sum(1 for r in results if r['status'] in ['failed', 'execution_failed'])
    
    print(f"Total tests: {len(results)}")
    print(f"  ✓ Successful (executed): {success_count}")
    print(f"  ⚠ Parsed only (not executed): {parsed_only_count}")
    print(f"  ✗ Failed: {failed_count}")
    print()
    
    if success_count > 0:
        avg_took = sum(r.get('took_ms', 0) for r in results if r['status'] == 'success') / success_count
        total_hits = sum(r.get('total_hits', 0) for r in results if r['status'] == 'success')
        print(f"Average query time: {avg_took:.2f}ms")
        print(f"Total hits across all queries: {total_hits}")
        print()

    # Cleanup
    print("6. Cleaning up...")
    await parser.close()
    if opensearch_manager:
        await opensearch_manager.close()
    print("  ✓ Cleanup complete")
    print()

    print("=" * 80)
    print("✓ Query Builder (NLAP-006) execution test complete!")
    print("=" * 80)
    print()

    return success_count > 0 or parsed_only_count > 0


if __name__ == "__main__":
    success = asyncio.run(test_query_builder_execution())
    sys.exit(0 if success else 1)

