#!/usr/bin/env python3
"""Test queries with actual date ranges that match available data."""

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.config.settings import (
    OpenSearchAuthSettings,
    OpenSearchClusterConfig,
)
from nlap.opensearch.client import OpenSearchManager


async def test_with_correct_dates():
    """Test with date ranges that match actual data."""
    print("=" * 80)
    print("Testing with actual date range (August 2025)")
    print("=" * 80)
    print()

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
        
        # Data appears to be from August 2025, so use that date range
        august_query = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": "2025-08-01T00:00:00Z",
                                "lte": "2025-08-31T23:59:59Z"
                            }
                        }
                    },
                    {"term": {"event.keyword": "RESPONSE_RETURNED"}}
                ]
            }
        }
        
        print("1. Testing RESPONSE_RETURNED with August date range and @timestamp field...")
        result = await opensearch_manager.execute_query(
            index=index_pattern,
            query=august_query,
            size=5
        )
        print(f"   ✓ Found {result.total} documents")
        if result.hits:
            sample = result.hits[0]
            print(f"   Sample event: {sample.get('event')}")
            print(f"   Sample timestamp: {sample.get('@timestamp')}")
            print(f"   Sample response_status: {sample.get('response_status')}")
        print()
        
        # Test with start_time field
        august_query_start_time = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "start_time": {
                                "gte": "2025-08-01T00:00:00Z",
                                "lte": "2025-08-31T23:59:59Z"
                            }
                        }
                    },
                    {"term": {"event.keyword": "RESPONSE_RETURNED"}}
                ]
            }
        }
        
        print("2. Testing same query but with start_time field instead of @timestamp...")
        result2 = await opensearch_manager.execute_query(
            index=index_pattern,
            query=august_query_start_time,
            size=5
        )
        print(f"   ✓ Found {result2.total} documents")
        print()
        
        # Check what fields exist in event documents
        print("3. Checking fields in RESPONSE_RETURNED events...")
        sample_query = {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "2025-08-01", "lte": "2025-08-31"}}},
                    {"term": {"event.keyword": "RESPONSE_RETURNED"}}
                ]
            }
        }
        sample_result = await opensearch_manager.execute_query(
            index=index_pattern,
            query=sample_query,
            size=1
        )
        
        if sample_result.hits:
            hit = sample_result.hits[0]
            print(f"   Fields in RESPONSE_RETURNED event (first 30):")
            fields = list(hit.keys())[:30]
            for field in fields:
                print(f"      - {field}")
            
            # Check for date fields
            print(f"\n   Date-related fields:")
            date_fields = [f for f in hit.keys() if any(word in f.lower() for word in ['time', 'date', 'stamp', 'timestamp'])]
            for field in date_fields:
                print(f"      - {field}: {hit.get(field)}")
        print()
        
        # Test A/B test query
        ab_query = {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "2025-08-01", "lte": "2025-08-31"}}},
                    {"term": {"event.keyword": "AB_EXPERIMENT_RETRIEVED"}}
                ]
            }
        }
        
        print("4. Testing AB_EXPERIMENT_RETRIEVED with August date range...")
        result3 = await opensearch_manager.execute_query(
            index=index_pattern,
            query=ab_query,
            size=5
        )
        print(f"   ✓ Found {result3.total} documents")
        if result3.hits:
            sample = result3.hits[0]
            print(f"   Sample ab_experiment_variant: {sample.get('ab_experiment_variant')}")
        print()
        
        await opensearch_manager.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_correct_dates())

