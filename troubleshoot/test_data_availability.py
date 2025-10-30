#!/usr/bin/env python3
"""Diagnostic script to check data availability and date field usage."""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
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
    """Check what data is available in OpenSearch."""
    print("=" * 80)
    print("Data Availability Diagnostic")
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
        
        # Test connection
        health = await opensearch_manager.test_connection()
        if not health.healthy:
            print(f"⚠ OpenSearch connection warning: {health.error}")
            return
        print(f"✓ Connected to: {health.cluster_name}")
        print()

        # Check 1: Get sample documents without date filter
        print("1. Checking sample documents (no date filter)...")
        sample_result = await opensearch_manager.execute_query(
            index=index_pattern,
            query={"match_all": {}},
            size=5
        )
        print(f"   Total documents in index: {sample_result.total}")
        print(f"   Sample documents returned: {len(sample_result.hits)}")
        
        if sample_result.hits:
            print("\n   Sample document fields:")
            sample = sample_result.hits[0]
            if isinstance(sample, dict):
                # Look for date fields
                date_fields = [k for k in sample.keys() if any(d in k.lower() for d in ['time', 'date', 'timestamp', 'start'])]
                print(f"   Date-related fields found: {date_fields}")
                print(f"   All fields: {', '.join(list(sample.keys())[:20])}")
                
                # Show actual date values
                for field in date_fields[:3]:
                    if field in sample:
                        print(f"   {field}: {sample[field]}")
        print()

        # Check 2: Check documents with @timestamp in last 30 days
        print("2. Checking documents with @timestamp field (last 30 days)...")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        now_str = datetime.now().isoformat()
        
        query_with_timestamp = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": thirty_days_ago,
                                "lte": now_str
                            }
                        }
                    }
                ]
            }
        }
        
        result_timestamp = await opensearch_manager.execute_query(
            index=index_pattern,
            query=query_with_timestamp,
            size=5
        )
        print(f"   Documents with @timestamp in last 30 days: {result_timestamp.total}")
        
        if result_timestamp.hits:
            sample = result_timestamp.hits[0]
            if isinstance(sample, dict) and "@timestamp" in sample:
                print(f"   Sample @timestamp value: {sample['@timestamp']}")
        print()

        # Check 3: Check documents with "start_time" field (what the test is using)
        print("3. Checking documents with start_time field (last 30 days)...")
        query_with_start_time = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "start_time": {
                                "gte": thirty_days_ago,
                                "lte": now_str
                            }
                        }
                    }
                ]
            }
        }
        
        result_start_time = await opensearch_manager.execute_query(
            index=index_pattern,
            query=query_with_start_time,
            size=5
        )
        print(f"   Documents with start_time in last 30 days: {result_start_time.total}")
        
        if result_start_time.hits:
            sample = result_start_time.hits[0]
            if isinstance(sample, dict) and "start_time" in sample:
                print(f"   Sample start_time value: {sample['start_time']}")
        print()

        # Check 4: Check what date fields actually exist
        print("4. Checking what date/timestamp fields exist...")
        # Get a document and list all fields
        if sample_result.hits:
            doc = sample_result.hits[0]
            if isinstance(doc, dict):
                all_fields = list(doc.keys())
                time_fields = [f for f in all_fields if any(t in f.lower() for t in ['time', 'date', 'stamp', 'when'])]
                print(f"   Fields that might be dates: {time_fields}")
                
                # Show actual values
                print("\n   Sample values for date-like fields:")
                for field in time_fields[:5]:
                    if field in doc:
                        print(f"     {field}: {doc[field]}")
        print()

        # Check 5: Check most recent documents
        print("5. Checking most recent documents (sorted by @timestamp desc)...")
        recent_query = {
            "match_all": {}
        }
        
        recent_result = await opensearch_manager.execute_query(
            index=index_pattern,
            query=recent_query,
            size=3,
            sort=[{"@timestamp": {"order": "desc"}}]
        )
        
        print(f"   Recent documents: {len(recent_result.hits)}")
        for i, doc in enumerate(recent_result.hits[:3], 1):
            if isinstance(doc, dict):
                timestamp = doc.get("@timestamp") or doc.get("time") or doc.get("start_time")
                event = doc.get("event", "N/A")
                print(f"   Doc {i}: @timestamp={timestamp}, event={event}")
        print()

        # Check 6: Date range from the docs (Oct 27-30, 2025)
        print("6. Checking data from documented date range (Oct 27-30, 2025)...")
        doc_start = "2025-10-27T00:00:00"
        doc_end = "2025-10-30T23:59:59"
        
        query_doc_range = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": doc_start,
                                "lte": doc_end
                            }
                        }
                    }
                ]
            }
        }
        
        result_doc_range = await opensearch_manager.execute_query(
            index=index_pattern,
            query=query_doc_range,
            size=5
        )
        print(f"   Documents in documented range (Oct 27-30, 2025): {result_doc_range.total}")
        
        if result_doc_range.hits:
            sample = result_doc_range.hits[0]
            print(f"   Sample document from that range:")
            if isinstance(sample, dict):
                print(f"     @timestamp: {sample.get('@timestamp')}")
                print(f"     event: {sample.get('event')}")
        print()

        await opensearch_manager.close()

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_data_availability())

