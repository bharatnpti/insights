#!/usr/bin/env python3
"""Quick diagnostic script to check data availability in OpenSearch."""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.config.settings import (
    OpenSearchAuthSettings,
    OpenSearchClusterConfig,
)
from nlap.opensearch.client import OpenSearchManager


async def check_data_availability():
    """Check what data is actually available."""
    print("=" * 80)
    print("OpenSearch Data Availability Check")
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
        
        health = await opensearch_manager.test_connection()
        if not health.healthy:
            print(f"⚠ Connection warning: {health.error}")
        
        print("1. Checking total document count (match_all)...")
        result = await opensearch_manager.execute_query(
            index=index_pattern,
            query={"match_all": {}},
            size=0
        )
        print(f"   Total documents: {result.total}")
        print()

        print("2. Checking date range of actual data...")
        # Get a sample to see timestamps
        sample_result = await opensearch_manager.execute_query(
            index=index_pattern,
            query={"match_all": {}},
            size=5
        )
        
        if sample_result.hits:
            print(f"   Found {len(sample_result.hits)} sample documents")
            for i, hit in enumerate(sample_result.hits[:3], 1):
                if isinstance(hit, dict):
                    timestamp = hit.get('@timestamp') or hit.get('time') or hit.get('timestamp')
                    event = hit.get('event', 'N/A')
                    print(f"   Sample {i}: event={event}, timestamp={timestamp}")
        else:
            print("   ⚠ No documents found in sample query")
        print()

        print("3. Checking what event types exist...")
        aggs_query = {
            "query": {"match_all": {}},
            "size": 0,
            "aggs": {
                "event_types": {
                    "terms": {
                        "field": "event.keyword",
                        "size": 20
                    }
                }
            }
        }
        result = await opensearch_manager.execute_query(
            index=index_pattern,
            query=aggs_query["query"],
            size=0
        )
        
        # Check aggregations
        if result.aggregations and "event_types" in result.aggregations:
            buckets = result.aggregations["event_types"].get("buckets", [])
            print(f"   Top {len(buckets)} event types:")
            for bucket in buckets[:10]:
                print(f"      {bucket['key']}: {bucket['doc_count']} documents")
        else:
            print("   ⚠ Could not get event type aggregation")
        print()

        print("4. Checking documents with date filter (last 30 days)...")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        now = datetime.now().isoformat()
        
        range_query = {
            "range": {
                "@timestamp": {
                    "gte": thirty_days_ago,
                    "lte": now
                }
            }
        }
        
        result = await opensearch_manager.execute_query(
            index=index_pattern,
            query=range_query,
            size=0
        )
        print(f"   Documents in last 30 days: {result.total}")
        print(f"   Date range used: {thirty_days_ago[:10]} to {now[:10]}")
        print()

        print("5. Checking specific event types...")
        test_events = [
            "LLM_COMPLETED",
            "RESPONSE_RETURNED", 
            "AB_EXPERIMENT_RETRIEVED",
            "FUNCTION_CALL_COMPLETED",
            "AGENT_HANDOVER_DETECTION_COMPLETED"
        ]
        
        for event in test_events:
            event_query = {
                "bool": {
                    "must": [
                        {"term": {"event.keyword": event}},
                        {"range": {
                            "@timestamp": {
                                "gte": thirty_days_ago,
                                "lte": now
                            }
                        }}
                    ]
                }
            }
            result = await opensearch_manager.execute_query(
                index=index_pattern,
                query=event_query,
                size=0
            )
            print(f"   {event}: {result.total} documents in last 30 days")
        print()

        print("6. Checking field names in sample documents...")
        sample = await opensearch_manager.execute_query(
            index=index_pattern,
            query={"match_all": {}},
            size=1
        )
        
        if sample.hits and len(sample.hits) > 0:
            hit = sample.hits[0]
            if isinstance(hit, dict):
                print(f"   Sample document fields (first 20):")
                fields = list(hit.keys())[:20]
                for field in fields:
                    print(f"      - {field}")
        print()

        await opensearch_manager.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_data_availability())

