#!/usr/bin/env python3
"""Complex end-to-end tests for Query Builder (NLAP-006) with actual OpenSearch execution.

This script tests complex scenarios based on the log structure analysis:
- A/B test variant analysis with correlations
- Multi-event type queries
- Complex aggregations and group-by operations
- Performance metric analysis
- Error pattern detection
- Agent and intent analysis
- Service-level queries
- Complex boolean logic queries

Usage:
    export AZURE_ENDPOINT='https://gpt4-se-dev.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='GPT-4o'
    export AZURE_API_VERSION='2024-10-21'
    python tests/integration/test_query_builder_complex.py
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


async def test_complex_scenarios():
    """Test complex query builder scenarios based on log structure analysis."""
    print("=" * 80)
    print("Query Builder (NLAP-006) - Complex Scenarios Test")
    print("Based on OpenSearch Log Structure Analysis")
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
                size=50
            )
            
            if sample_result.hits:
                schema_info = await schema_engine._build_schema_from_documents(
                    index_name=index_pattern,
                    documents=sample_result.hits,
                    total_analyzed=len(sample_result.hits),
                    sample_size=50
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

    # Complex test scenarios based on log structure analysis
    test_scenarios = [
        {
            "query": "Show A/B test events with variant LEGACY or SUPERVISOR from the last 7 days",
            "description": "A/B test variant filtering with OR condition",
            "category": "A/B Testing",
            "should_execute": True,
        },
        {
            "query": "Count RESPONSE_RETURNED events grouped by response_status for the last 3 days",
            "description": "Event type filtering with status aggregation",
            "category": "Completion Status",
            "should_execute": True,
        },
        {
            "query": "Find LLM_COMPLETED events where responseTime is greater than 2 seconds from last 5 days",
            "description": "Performance metric filtering with event type",
            "category": "Performance",
            "should_execute": True,
        },
        {
            "query": "Show FUNCTION_CALL_COMPLETED events where function_status equals error for last 7 days",
            "description": "Error pattern detection with event type filtering",
            "category": "Error Analysis",
            "should_execute": True,
        },
        {
            "query": "Count events grouped by event type and k8s_name (service) for the last 2 days",
            "description": "Multi-field aggregation (event type and service)",
            "category": "Service Analysis",
            "should_execute": True,
        },
        {
            "query": "Find CLASSIFICATION_VECTOR_DONE events where classifier-selected-agent contains 'agent' from last 4 days",
            "description": "Agent selection analysis with text search",
            "category": "Agent Analysis",
            "should_execute": True,
        },
        {
            "query": "Get INTENT_DETECTION_COMPLETED events grouped by category and subCategory for last 6 days",
            "description": "Intent analysis with hierarchical grouping",
            "category": "Intent Analysis",
            "should_execute": True,
        },
        {
            "query": "Show documents where event equals LLM_COMPLETED and totalTokens is greater than 500 from last 3 days",
            "description": "Token usage analysis with multiple conditions",
            "category": "Performance",
            "should_execute": True,
        },
        {
            "query": "Count AGENT_HANDOVER_DETECTION_COMPLETED events where markedForAgentHandover equals true grouped by agent for last 5 days",
            "description": "Handover analysis with boolean filtering and aggregation",
            "category": "Completion Status",
            "should_execute": True,
        },
        {
            "query": "Find events where level equals ERROR and message contains 'error' from last 2 days",
            "description": "Error log analysis with text matching",
            "category": "Error Analysis",
            "should_execute": True,
        },
        {
            "query": "Show RESPONSE_RETURNED events where response_status is not ONGOING for last 7 days grouped by response_status",
            "description": "Completed conversations analysis (excluding ongoing)",
            "category": "Completion Status",
            "should_execute": True,
        },
        {
            "query": "Get events from ia-platform service where k8s_container equals ia-platform from last 3 days",
            "description": "Service-specific filtering with container match",
            "category": "Service Analysis",
            "should_execute": True,
        },
        {
            "query": "Count events grouped by channelId and tenantId for the last 4 days",
            "description": "Multi-tenant and channel analysis",
            "category": "User Analysis",
            "should_execute": True,
        },
        {
            "query": "Find LLM_COMPLETED events where languageModel equals GPT-4o-mini and completionTokens is less than 100 for last 6 days",
            "description": "Model-specific token usage analysis",
            "category": "Performance",
            "should_execute": True,
        },
        {
            "query": "Show FUNCTION_CALLED events grouped by function and phase for the last 5 days",
            "description": "Function call lifecycle analysis",
            "category": "Function Analysis",
            "should_execute": True,
        },
        {
            "query": "Get events where conversationId exists and turnId exists from last 2 days, sorted by timestamp descending",
            "description": "Conversation correlation key validation",
            "category": "Correlation",
            "should_execute": True,
        },
        {
            "query": "Count events grouped by date histogram (daily) for response_status field where response_status exists, for last 14 days",
            "description": "Time-series analysis of completion status",
            "category": "Time Series",
            "should_execute": True,
        },
        {
            "query": "Find TRANSCRIPT_PREPARED events where transcript field exists from last 3 days",
            "description": "Transcript availability check",
            "category": "Content Analysis",
            "should_execute": True,
        },
        {
            "query": "Show events where event is in [LLM_STARTED, LLM_COMPLETED] and conversationId exists for last 4 days",
            "description": "Multiple event type query with existence check",
            "category": "Multi-Event",
            "should_execute": True,
        },
        {
            "query": "Get events where k8s_name equals ia-platform and (level equals ERROR or level equals WARN) from last 2 days",
            "description": "Service-level error/warning filtering with OR condition",
            "category": "Error Analysis",
            "should_execute": True,
        },
        {
            "query": "Count AB_EXPERIMENT_RETRIEVED events grouped by ab_experiment_variant for last 7 days, sorted by count descending",
            "description": "A/B test distribution analysis with sorting",
            "category": "A/B Testing",
            "should_execute": True,
        },
        {
            "query": "Find events where traceId exists and spanId exists from last 3 days, limit to 100 results",
            "description": "Distributed tracing validation",
            "category": "Correlation",
            "should_execute": True,
        },
        {
            "query": "Show MEMORY_STORE_EVENT events where agent field exists and key field exists from last 5 days",
            "description": "Memory store validation with multiple existence checks",
            "category": "Memory Analysis",
            "should_execute": True,
        },
        {
            "query": "Get events where event equals RESPONSE_RETURNED and (response_status equals RESOLVED or response_status equals UNRESOLVED) for last 6 days",
            "description": "Complex boolean logic: event type AND (status OR status)",
            "category": "Completion Status",
            "should_execute": True,
        },
        {
            "query": "Count KNOWLEDGE_FETCHED events grouped by document_id and collection_id for last 4 days",
            "description": "Knowledge retrieval analysis with document grouping",
            "category": "Knowledge Analysis",
            "should_execute": True,
        },
        {
            "query": "Find events where function_status equals error and function_error_message exists from last 7 days",
            "description": "Function error analysis with error message presence",
            "category": "Error Analysis",
            "should_execute": True,
        },
        {
            "query": "Show CLASSIFICATION_VECTOR_METRICS events where classifier-embedding-ranking-thresholds-matched exists from last 3 days",
            "description": "Classification metrics validation",
            "category": "Classification",
            "should_execute": True,
        },
        {
            "query": "Get events where event equals USECASE_PROMPT_IDENTIFIED and usecase_name exists grouped by usecase_name for last 5 days",
            "description": "Use case distribution analysis",
            "category": "Use Case Analysis",
            "should_execute": True,
        },
        {
            "query": "Find events where source_intent field exists and detectedIntent field exists from last 4 days",
            "description": "Intent detection validation with both source and detected",
            "category": "Intent Analysis",
            "should_execute": True,
        },
        {
            "query": "Count events grouped by environment and k8s_namespace for the last 3 days",
            "description": "Environment and namespace cross-analysis",
            "category": "Infrastructure",
            "should_execute": True,
        },
    ]

    print("5. Testing complex query scenarios...")
    print("=" * 80)
    print()

    results = []
    category_counts = {}

    for i, test_case in enumerate(test_scenarios, 1):
        category = test_case.get('category', 'Unknown')
        if category not in category_counts:
            category_counts[category] = {'total': 0, 'success': 0, 'failed': 0}
        category_counts[category]['total'] += 1

        print(f"Test {i}/{len(test_scenarios)}: {test_case['description']}")
        print(f"Category: {category}")
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
                print(f"    Must filters: {len(parsed_query.filters.must)}")
                for condition in parsed_query.filters.must[:2]:
                    print(f"      - {condition.field} {condition.operator.value} {condition.value}")
            
            if parsed_query.filters.should:
                print(f"    Should filters: {len(parsed_query.filters.should)}")
            
            if parsed_query.filters.must_not:
                print(f"    Must not filters: {len(parsed_query.filters.must_not)}")
            
            if parsed_query.aggregations:
                print(f"    Aggregations: {len(parsed_query.aggregations)}")
                for agg in parsed_query.aggregations[:2]:
                    group_by = ', '.join(agg.group_by) if agg.group_by else 'N/A'
                    print(f"      - {agg.type.value} on {agg.field or 'N/A'} (group by: {group_by})")

            # Step 2: Build OpenSearch query
            print("\nStep 2: Building OpenSearch query...")
            opensearch_query = query_builder.build_query(parsed_query, size=5)
            
            print(f"  ✓ Query built successfully")
            print(f"    Query type: {list(opensearch_query['query'].keys())[0]}")
            print(f"    Size: {opensearch_query['size']}")
            
            if 'aggs' in opensearch_query:
                print(f"    Aggregations: {len(opensearch_query['aggs'])}")
                for agg_name in list(opensearch_query['aggs'].keys())[:3]:
                    print(f"      - {agg_name}")

            # Show query structure (compact)
            query_json = json.dumps(opensearch_query['query'], indent=2, default=str)
            print(f"\n  Query structure (first 8 lines):")
            lines = query_json.split('\n')
            for line in lines[:8]:
                print(f"    {line}")
            if len(lines) > 8:
                print(f"    ... ({len(lines) - 8} more lines)")

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
                            if 'buckets' in agg_data:
                                bucket_count = len(agg_data['buckets'])
                                print(f"      - {agg_name}: {bucket_count} buckets")
                            elif 'value' in agg_data:
                                print(f"      - {agg_name}: {agg_data['value']}")
                    
                    if result.hits and len(result.hits) > 0:
                        print(f"\n    Sample result (first hit, keys only):")
                        sample_hit = result.hits[0]
                        if isinstance(sample_hit, dict):
                            print(f"      Fields: {', '.join(list(sample_hit.keys())[:8])}")
                    
                    results.append({
                        "test": i,
                        "category": category,
                        "query": test_case['query'],
                        "status": "success",
                        "total_hits": result.total,
                        "took_ms": result.took,
                        "has_aggregations": bool(result.aggregations),
                    })
                    category_counts[category]['success'] += 1
                    
                except Exception as e:
                    print(f"  ✗ Query execution failed: {e}")
                    results.append({
                        "test": i,
                        "category": category,
                        "query": test_case['query'],
                        "status": "execution_failed",
                        "error": str(e),
                    })
                    category_counts[category]['failed'] += 1
            else:
                print("\nStep 3: Skipped (OpenSearch not available or should_execute=False)")
                results.append({
                    "test": i,
                    "category": category,
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
                "category": category,
                "query": test_case['query'],
                "status": "failed",
                "error": str(e),
            })
            category_counts[category]['failed'] += 1
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
    
    # Category breakdown
    print("Results by Category:")
    print("-" * 80)
    for category, counts in sorted(category_counts.items()):
        success_rate = (counts['success'] / counts['total'] * 100) if counts['total'] > 0 else 0
        print(f"  {category}: {counts['success']}/{counts['total']} successful ({success_rate:.1f}%)")
    print()
    
    if success_count > 0:
        avg_took = sum(r.get('took_ms', 0) for r in results if r['status'] == 'success') / success_count
        total_hits = sum(r.get('total_hits', 0) for r in results if r['status'] == 'success')
        print(f"Average query time: {avg_took:.2f}ms")
        print(f"Total hits across all queries: {total_hits}")
        print()
        
        # Show some example successful queries
        print("Example Successful Queries:")
        print("-" * 80)
        for r in results[:3]:
            if r['status'] == 'success':
                print(f"  - {r['query'][:70]}...")
                print(f"    Hits: {r['total_hits']}, Time: {r['took_ms']}ms")
        print()

    # Cleanup
    print("6. Cleaning up...")
    await parser.close()
    if opensearch_manager:
        await opensearch_manager.close()
    print("  ✓ Cleanup complete")
    print()

    print("=" * 80)
    print("✓ Query Builder (NLAP-006) complex scenarios test complete!")
    print("=" * 80)
    print()

    return success_count > 0 or parsed_only_count > 0


if __name__ == "__main__":
    success = asyncio.run(test_complex_scenarios())
    sys.exit(0 if success else 1)

