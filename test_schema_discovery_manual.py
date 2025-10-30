#!/usr/bin/env python3
"""Manual test script for Schema Discovery Engine.

This script allows you to quickly test the schema discovery functionality
with different indices and queries.

Usage:
    python test_schema_discovery_manual.py [index_name]
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src directory to Python path to allow imports
project_root = Path(__file__).parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.config.settings import OpenSearchAuthSettings, OpenSearchClusterConfig
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.schema_discovery import SchemaDiscoveryEngine
from nlap.opensearch.schema_models import FieldType

# Note: Logging setup skipped to avoid settings validation issues in test script


async def test_schema_discovery(index_name: str = "logs-*"):
    """Test schema discovery for an index.

    Args:
        index_name: Index name or pattern to discover
    """
    # Test configuration
    config = {
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

    print("Schema Discovery Engine Test")
    print(f"  Host: {config['host']}")
    print(f"  Index: {index_name}")
    print()

    try:
        # Create auth settings
        auth_settings = OpenSearchAuthSettings(**config["auth"])
        cluster_config = OpenSearchClusterConfig(
            name=config["name"],
            host=config["host"],
            port=config["port"],
            use_ssl=config["use_ssl"],
            verify_certs=config["verify_certs"],
            auth=auth_settings,
        )

        # Create OpenSearch manager
        print("Connecting to OpenSearch...")
        opensearch_manager = OpenSearchManager(settings=cluster_config)
        
        # Test connection
        health = await opensearch_manager.test_connection()
        if not health.healthy:
            print(f"❌ Connection failed: {health.error}")
            return
        print(f"✅ Connected to cluster: {health.cluster_name}")
        print()

        # Create schema discovery engine
        print("Initializing Schema Discovery Engine...")
        discovery_engine = SchemaDiscoveryEngine(
            opensearch_manager=opensearch_manager,
            sample_size=50,  # Sample 50 documents
        )
        print("✅ Schema Discovery Engine initialized")
        print()

        # Discover schema for entire index
        print(f"Discovering schema for index: {index_name}")
        print(f"  Sample size: 50 documents")
        print()
        
        schema = await discovery_engine.discover_index_schema(
            index_name=index_name,
            sample_size=50,
            use_cache=True,
        )

        # Display results
        print("=" * 80)
        print("SCHEMA DISCOVERY RESULTS")
        print("=" * 80)
        print(f"Index Name: {schema.index_name}")
        print(f"Version: {schema.version}")
        print(f"Total Documents Analyzed: {schema.total_documents_analyzed}")
        print(f"Sample Size: {schema.sample_size}")
        print(f"Discovered At: {schema.discovered_at}")
        print(f"Total Fields: {len(schema.fields)}")
        print()

        if schema.fields:
            print("DISCOVERED FIELDS:")
            print("-" * 80)
            
            # Group fields by type
            fields_by_type: dict[FieldType, list[str]] = {}
            for field_name, field_info in schema.fields.items():
                field_type = field_info.field_type
                if field_type not in fields_by_type:
                    fields_by_type[field_type] = []
                fields_by_type[field_type].append(field_name)

            # Display fields grouped by type
            for field_type, field_names in sorted(fields_by_type.items()):
                print(f"\n{field_type.value.upper()} Fields ({len(field_names)}):")
                for field_name in sorted(field_names):
                    field_info = schema.fields[field_name]
                    print(f"  • {field_name}")
                    if field_info.sample_values:
                        samples_str = ", ".join(str(v)[:50] for v in field_info.sample_values[:3])
                        print(f"    Sample values: {samples_str}")
                    if field_info.is_array:
                        print(f"    Type: Array")
                    if field_info.is_nested:
                        print(f"    Type: Nested")
        else:
            print("No fields discovered (empty index or no matching documents)")

        print()
        print("=" * 80)

        # Test cache functionality
        print("\nTesting cache functionality...")
        print("  Re-discovering schema (should use cache)...")
        cached_schema = await discovery_engine.discover_index_schema(
            index_name=index_name,
            sample_size=50,
            use_cache=True,
        )
        print(f"  ✅ Cache working: Version {cached_schema.version}")
        print()

        # Test query-based discovery
        print("Testing query-based schema discovery...")
        print("  Query: Match documents with 'error' in message field")
        print()
        
        query = {
            "match": {
                "message": "error"
            }
        }
        
        query_schema = await discovery_engine.discover_document_schema(
            index_name=index_name,
            query=query,
            sample_size=20,
        )
        
        print(f"  ✅ Query-based discovery complete")
        print(f"  Fields discovered: {len(query_schema.fields)}")
        print(f"  Documents analyzed: {query_schema.total_documents_analyzed}")
        print()

        # Close connections
        await opensearch_manager.close()
        print("✅ Test completed successfully")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_field_extraction():
    """Test field extraction with sample documents."""
    print("=" * 80)
    print("TESTING FIELD EXTRACTION")
    print("=" * 80)
    print()

    from nlap.opensearch.field_extractor import FieldExtractor
    from nlap.opensearch.type_identifier import TypeIdentifier

    # Sample documents with nested structures
    sample_documents = [
        {
            "user": {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "profile": {
                    "age": 30,
                    "active": True,
                    "tags": ["admin", "user"],
                },
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "count": 42,
            "metadata": {
                "ip": "192.168.1.1",
                "location": "40.7128,-74.0060",
            },
        },
        {
            "user": {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "profile": {
                    "age": 25,
                    "active": False,
                    "tags": ["user"],
                },
            },
            "timestamp": "2024-01-15T11:00:00Z",
            "count": 99,
            "metadata": {
                "ip": "10.0.0.1",
                "location": "51.5074,-0.1278",
            },
        },
    ]

    # Extract fields
    extractor = FieldExtractor()
    field_values = extractor.extract_fields(sample_documents)

    print("Extracted Fields:")
    print("-" * 80)
    for field_path, values in sorted(field_values.items()):
        print(f"  {field_path}: {len(values)} sample(s)")
        if values:
            samples = ", ".join(str(v)[:40] for v in values[:3])
            print(f"    Samples: {samples}")

    print()
    print("Type Identification:")
    print("-" * 80)

    # Identify types
    type_identifier = TypeIdentifier()
    for field_path, values in sorted(field_values.items()):
        field_type = type_identifier.identify_field_type(field_path, values)
        print(f"  {field_path}: {field_type.value}")

    print()


def main():
    """Main entry point."""
    index_name = sys.argv[1] if len(sys.argv) > 1 else "logs-*"
    
    print("\n" + "=" * 80)
    print("Schema Discovery Engine - Manual Test")
    print("=" * 80)
    print()

    # First test field extraction with sample data
    asyncio.run(test_field_extraction())

    # Then test with real OpenSearch
    print("\n" + "=" * 80)
    print("Testing with OpenSearch Connection")
    print("=" * 80)
    print()

    asyncio.run(test_schema_discovery(index_name))


if __name__ == "__main__":
    main()

