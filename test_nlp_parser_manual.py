"""Manual test script for Natural Language Parser (NLAP-004)."""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to Python path to allow imports
project_root = Path(__file__).parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.azureopenai.client import AzureOpenAIClient
from nlap.config.settings import AzureOpenAISettings
from nlap.nlp.parser import NaturalLanguageParser
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine


async def test_nlp_parser():
    """Test the natural language parser with sample queries."""
    print("Testing Natural Language Parser (NLAP-004)\n")

    # Initialize clients
    print("1. Initializing clients...")
    
    # Azure OpenAI settings
    azure_endpoint = os.getenv("AZURE_ENDPOINT", "https://gpt4-se-dev.openai.azure.com/")
    azure_deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "GPT-4o")
    azure_api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")
    
    # Create Azure OpenAI client with provided settings
    azure_settings = AzureOpenAISettings(
        endpoint=azure_endpoint.rstrip('/'),  # Remove trailing slash
        deployment_name=azure_deployment,
        api_version=azure_api_version,
    )
    azure_client = AzureOpenAIClient(settings=azure_settings)
    print(f"   ✓ Azure OpenAI client initialized (endpoint: {azure_endpoint}, deployment: {azure_deployment})")
    
    # OpenSearch settings
    from nlap.config.settings import OpenSearchAuthSettings, OpenSearchClusterConfig
    
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
    
    # Initialize OpenSearch
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
        await opensearch_manager.test_connection()
        print(f"   ✓ OpenSearch connection successful (host: {opensearch_config['host']})")
    except Exception as e:
        print(f"   ⚠ OpenSearch connection failed: {e}")
        print("   ⚠ Continuing without OpenSearch (schema validation will be limited)\n")

    # Initialize parser
    parser = NaturalLanguageParser(azure_openai_client=azure_client)
    print("   ✓ NLP Parser initialized\n")

    # Sample queries to test
    test_queries = [
        "Show me all documents from the last 4 days",
        "A/B test analysis for last 4 days showing variant vs completion status",
        "User engagement metrics by channel for this month",
        "Error rates grouped by service and date",
        "Find all documents where status equals 'completed' from yesterday",
        "Count total users grouped by country for October 27-30, 2024",
    ]

    # Get schema for the index to improve parsing
    schema_info = None
    if opensearch_manager:
        try:
            print("   Discovering schema for index...")
            schema_engine = SchemaDiscoveryEngine(opensearch_manager)
            index_pattern = "ia-platform-prod-*"
            
            # Try to get a sample document from the index pattern to discover schema
            # We'll query a few documents to understand the structure
            sample_query = {"match_all": {}}
            sample_result = await opensearch_manager.execute_query(
                index=index_pattern,
                query=sample_query,
                size=10
            )
            
            if sample_result.hits:
                # Use document-based schema discovery
                schema_info = await schema_engine._build_schema_from_documents(
                    index_name=index_pattern,
                    documents=sample_result.hits,
                    total_analyzed=len(sample_result.hits),
                    sample_size=10
                )
                parser.schema_info = schema_info
                print(f"   ✓ Schema discovered: {len(schema_info.fields)} fields found from sample documents")
            else:
                print("   ⚠ No documents found in index pattern for schema discovery")
        except Exception as e:
            print(f"   ⚠ Schema discovery failed: {e}")
            print("   ⚠ Continuing without schema information\n")

    print("2. Testing query parsing...\n")
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 80)
        
        try:
            # Parse the query with index pattern
            parsed = await parser.parse(
                query,
                index_names=["ia-platform-prod-*"]  # Specify the index pattern
            )
            
            print(f"Intent: {parsed.intent.category.value} (confidence: {parsed.intent.confidence:.2f})")
            print(f"Overall Confidence: {parsed.confidence:.2f}")
            
            if parsed.intent.description:
                print(f"Description: {parsed.intent.description}")
            
            if parsed.date_range:
                print(f"Date Range: {parsed.date_range.relative_period or f'{parsed.date_range.start_date_str} to {parsed.date_range.end_date_str}'}")
            
            if parsed.index_names:
                print(f"Indices: {', '.join(parsed.index_names)}")
            
            if parsed.filters.must:
                print("Filters (must):")
                for condition in parsed.filters.must:
                    print(f"  - {condition.field} {condition.operator.value} {condition.value}")
            
            if parsed.aggregations:
                print("Aggregations:")
                for agg in parsed.aggregations:
                    print(f"  - {agg.type.value} on {agg.field or 'N/A'}")
                    if agg.group_by:
                        print(f"    Group by: {', '.join(agg.group_by)}")
            
            if parsed.fields:
                print(f"Fields to retrieve: {', '.join(parsed.fields)}")
            
            if parsed.entities:
                print(f"Entities extracted: {len(parsed.entities)} items")
                if "field_names" in parsed.entities and parsed.entities["field_names"]:
                    print(f"  Field names: {', '.join(parsed.entities['field_names'][:5])}")
            
            if parsed.errors:
                print(f"Warnings/Errors: {', '.join(parsed.errors)}")
            
            print()
            
        except Exception as e:
            print(f"   ✗ Error parsing query: {e}")
            print()
            import traceback
            traceback.print_exc()
            print()

    # Cleanup
    print("3. Cleaning up...")
    await parser.close()
    if opensearch_manager:
        await opensearch_manager.close()
    print("   ✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_nlp_parser())

