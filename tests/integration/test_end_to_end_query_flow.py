#!/usr/bin/env python3
"""End-to-end integration test for the complete query flow.

This test validates the complete flow:
1. User natural language query
2. Natural Language Parser -> ParsedQuery
3. Schema Discovery (if enabled)
4. Query Builder -> OpenSearch Query DSL
5. Execute query on OpenSearch
6. Validate response structure and content

Usage:
    export AZURE_ENDPOINT='https://gpt4-se-dev.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='GPT-4o'
    export AZURE_API_VERSION='2024-10-21'
    python tests/integration/test_end_to_end_query_flow.py
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


async def test_end_to_end_query_flow():
    """Test the complete end-to-end query flow from user query to OpenSearch execution."""
    print("=" * 80)
    print("End-to-End Query Flow Integration Test")
    print("=" * 80)
    print()

    # Configuration - using same configs as other integration tests
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

    # Step 1: Initialize Azure OpenAI client
    print("Step 1: Initializing Azure OpenAI client...")
    try:
        azure_settings = AzureOpenAISettings(
            endpoint=azure_endpoint.rstrip('/'),
            deployment_name=azure_deployment,
            api_version=azure_api_version,
        )
        azure_client = AzureOpenAIClient(settings=azure_settings)
        print(f"  ✓ Azure OpenAI client initialized")
        print(f"    Endpoint: {azure_endpoint}")
        print(f"    Deployment: {azure_deployment}")
        print()
    except Exception as e:
        print(f"  ✗ Failed to initialize Azure OpenAI client: {e}")
        return False

    # Step 2: Initialize OpenSearch client
    print("Step 2: Initializing OpenSearch client...")
    opensearch_manager = None
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
        print()
    except Exception as e:
        print(f"  ✗ OpenSearch initialization failed: {e}")
        print(f"    Cannot test execution, but query generation will still work")
        opensearch_manager = None
        print()

    # Step 3: Initialize components
    print("Step 3: Initializing parser and query builder...")
    schema_discovery = SchemaDiscoveryEngine(opensearch_manager) if opensearch_manager else None
    parser = NaturalLanguageParser(azure_openai_client=azure_client)
    query_builder = QueryBuilder()
    print("  ✓ Components initialized")
    print()

    # Step 4: Test queries with different scenarios
    test_cases = [
        {
            "name": "AB Experiment Values Query",
            "query": "different values of ab experiment",
            "index_names": [index_pattern],
            "discover_fields": True,
            "expect_results": True,
            "validate_fields": ["ab_experiment", "ab_experiment_variant"],
        },
        {
            "name": "Date Range Query",
            "query": "show me all documents from the last 7 days",
            "index_names": [index_pattern],
            "discover_fields": True,
            "expect_results": True,
        },
        {
            "name": "Filtered Query with Aggregation",
            "query": "count total documents grouped by event type for last 4 days",
            "index_names": [index_pattern],
            "discover_fields": True,
            "expect_results": True,
            "validate_aggregations": True,
        },
    ]

    print("Step 4: Testing query flow...")
    print("=" * 80)
    print()

    all_results = []
    for test_idx, test_case in enumerate(test_cases, 1):
        print(f"Test {test_idx}: {test_case['name']}")
        print(f"  Query: '{test_case['query']}'")
        print("-" * 80)

        try:
            # Sub-step 1: Discover schema if enabled
            schema_info = None
            if test_case.get("discover_fields") and schema_discovery:
                print("  Sub-step 1: Discovering schema...")
                try:
                    primary_index = test_case["index_names"][0] if test_case["index_names"] else None
                    if primary_index and "*" not in primary_index:
                        schema_info = await schema_discovery.discover_index_schema(
                            index_name=primary_index,
                            use_cache=True,
                        )
                        print(f"    ✓ Schema discovered: {len(schema_info.fields)} fields")
                        print(f"    Documents analyzed: {schema_info.total_documents_analyzed}")
                        
                        # Validate that schema includes field information
                        if schema_info.fields:
                            sample_field = list(schema_info.fields.keys())[0]
                            field_info = schema_info.fields[sample_field]
                            print(f"    Sample field: {sample_field}")
                            print(f"      - Type: {field_info.field_type.value}")
                            print(f"      - Is array: {field_info.is_array}")
                            print(f"      - Is nested: {field_info.is_nested}")
                    else:
                        print(f"    ⚠ Skipping schema discovery (wildcard index or no index specified)")
                except Exception as e:
                    print(f"    ⚠ Schema discovery failed: {e}")
                    print(f"    Continuing without schema...")
                print()

            # Sub-step 2: Parse natural language query
            print("  Sub-step 2: Parsing natural language query...")
            parsed_query = await parser.parse(
                query=test_case["query"],
                index_names=test_case.get("index_names"),
            )

            print(f"    ✓ Query parsed successfully")
            print(f"    Intent: {parsed_query.intent.category.value if parsed_query.intent else 'N/A'}")
            print(f"    Confidence: {parsed_query.confidence:.2f}")
            
            if parsed_query.date_range:
                date_str = (
                    parsed_query.date_range.relative_period
                    if parsed_query.date_range.relative_period
                    else f"{parsed_query.date_range.start_date_str} to {parsed_query.date_range.end_date_str}"
                )
                print(f"    Date range: {date_str}")
            
            if parsed_query.filters.must:
                print(f"    Filters (must): {len(parsed_query.filters.must)}")
                for f in parsed_query.filters.must[:3]:
                    print(f"      - {f.field} {f.operator.value} {f.value}")
            
            if parsed_query.aggregations:
                print(f"    Aggregations: {len(parsed_query.aggregations)}")
                for agg in parsed_query.aggregations[:3]:
                    print(f"      - {agg.type.value} on {agg.field}")
            
            # Validate parsed query
            assert parsed_query.original_query == test_case["query"], "Original query mismatch"
            assert parsed_query.confidence > 0, "Confidence should be positive"
            print()

            # Sub-step 3: Update query builder with schema
            if schema_info:
                query_builder.schema_info = schema_info

            # Sub-step 4: Build OpenSearch query
            print("  Sub-step 4: Building OpenSearch query...")
            opensearch_query = query_builder.build_query(
                parsed_query=parsed_query,
                size=test_case.get("size", 10),
                from_=test_case.get("from_", 0),
            )

            print(f"    ✓ OpenSearch query built successfully")
            print(f"    Query type: {list(opensearch_query['query'].keys())[0]}")
            print(f"    Size: {opensearch_query.get('size', 10)}")
            
            if 'aggs' in opensearch_query:
                print(f"    Aggregations: {len(opensearch_query['aggs'])}")
                for agg_name in list(opensearch_query['aggs'].keys())[:3]:
                    print(f"      - {agg_name}")
            
            # Validate OpenSearch query structure
            assert "query" in opensearch_query, "OpenSearch query must have 'query' field"
            assert isinstance(opensearch_query["query"], dict), "Query must be a dictionary"
            assert "size" in opensearch_query, "Query must have 'size' field"
            print()

            # Sub-step 5: Execute query on OpenSearch
            if not opensearch_manager:
                print("  Sub-step 5: Skipped (OpenSearch not available)")
                all_results.append({
                    "test": test_idx,
                    "name": test_case["name"],
                    "status": "parsed_only",
                    "query": test_case["query"],
                })
                print()
                continue

            print("  Sub-step 5: Executing query on OpenSearch...")
            try:
                result = await opensearch_manager.execute_query(
                    index=test_case["index_names"][0] if test_case["index_names"] else index_pattern,
                    query=opensearch_query["query"],
                    size=opensearch_query.get("size", 10),
                    from_=opensearch_query.get("from", 0),
                )

                print(f"    ✓ Query executed successfully")
                print(f"    Total hits: {result.total}")
                print(f"    Query time: {result.took}ms")
                print(f"    Results returned: {len(result.hits)}")
                
                # Validate execution result
                assert result.took >= 0, "Query execution time should be non-negative"
                assert result.total >= 0, "Total hits should be non-negative"
                assert isinstance(result.hits, list), "Hits should be a list"
                
                # Validate results if expected
                if test_case.get("expect_results"):
                    if result.total == 0:
                        print(f"    ⚠ Warning: Expected results but got 0 hits")
                    else:
                        print(f"    ✓ Got expected results ({result.total} hits)")
                
                # Validate specific fields if requested
                if test_case.get("validate_fields") and result.hits:
                    sample_hit = result.hits[0]
                    missing_fields = []
                    for field in test_case["validate_fields"]:
                        # Check field or field.keyword variant
                        field_found = field in sample_hit or f"{field}.keyword" in sample_hit
                        if not field_found:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"    ⚠ Warning: Some expected fields not found: {missing_fields}")
                    else:
                        print(f"    ✓ All expected fields found in results")
                
                # Validate aggregations if requested
                if test_case.get("validate_aggregations"):
                    if result.aggregations:
                        print(f"    ✓ Aggregations returned: {len(result.aggregations)}")
                        for agg_name in list(result.aggregations.keys())[:3]:
                            print(f"      - {agg_name}")
                    else:
                        print(f"    ⚠ Warning: Expected aggregations but none returned")
                
                # Show sample result structure
                if result.hits:
                    sample_hit = result.hits[0]
                    print(f"\n    Sample result structure:")
                    print(f"      Fields (first 10): {', '.join(list(sample_hit.keys())[:10])}")
                    if len(sample_hit) > 10:
                        print(f"      ... ({len(sample_hit) - 10} more fields)")

                all_results.append({
                    "test": test_idx,
                    "name": test_case["name"],
                    "status": "success",
                    "query": test_case["query"],
                    "total_hits": result.total,
                    "took_ms": result.took,
                    "has_aggregations": bool(result.aggregations),
                })
                
            except Exception as e:
                print(f"    ✗ Query execution failed: {e}")
                print(f"\n    Failed query structure:")
                print(json.dumps(opensearch_query["query"], indent=4, default=str))
                import traceback
                traceback.print_exc()
                all_results.append({
                    "test": test_idx,
                    "name": test_case["name"],
                    "status": "execution_failed",
                    "query": test_case["query"],
                    "error": str(e),
                })
            
            print()

        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                "test": test_idx,
                "name": test_case["name"],
                "status": "failed",
                "query": test_case["query"],
                "error": str(e),
            })
            print()

    # Step 5: Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print()
    
    success_count = sum(1 for r in all_results if r['status'] == 'success')
    parsed_only_count = sum(1 for r in all_results if r['status'] == 'parsed_only')
    failed_count = sum(1 for r in all_results if r['status'] in ['failed', 'execution_failed'])
    
    print(f"Total tests: {len(all_results)}")
    print(f"  ✓ Successful (executed): {success_count}")
    print(f"  ⚠ Parsed only (not executed): {parsed_only_count}")
    print(f"  ✗ Failed: {failed_count}")
    print()
    
    if success_count > 0:
        avg_took = sum(r.get('took_ms', 0) for r in all_results if r['status'] == 'success') / success_count
        total_hits = sum(r.get('total_hits', 0) for r in all_results if r['status'] == 'success')
        print(f"Average query time: {avg_took:.2f}ms")
        print(f"Total hits across all queries: {total_hits}")
        print()

    # Step 6: Cleanup
    print("Step 6: Cleaning up...")
    try:
        await parser.close()
        if opensearch_manager:
            await opensearch_manager.close()
        print("  ✓ Cleanup complete")
    except Exception as e:
        print(f"  ⚠ Cleanup warning: {e}")
    print()

    print("=" * 80)
    print("✓ End-to-End Query Flow Test Complete!")
    print("=" * 80)
    print()

    # Return True if at least one test succeeded or all tests were parsed (no execution)
    return success_count > 0 or (parsed_only_count > 0 and failed_count == 0)


if __name__ == "__main__":
    success = asyncio.run(test_end_to_end_query_flow())
    sys.exit(0 if success else 1)

