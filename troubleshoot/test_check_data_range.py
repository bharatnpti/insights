#!/usr/bin/env python3
"""Quick check for actual data date ranges."""

import asyncio
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nlap.config.settings import OpenSearchAuthSettings, OpenSearchClusterConfig
from nlap.opensearch.client import OpenSearchManager


async def check_data():
    """Check what data is actually available."""
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

        # Get a sample without date filter
        print("Getting sample documents (no date filter)...")
        result = await opensearch_manager.execute_query(
            index=index_pattern,
            query={"match_all": {}},
            size=5,
            sort=[{"@timestamp": {"order": "desc"}}]
        )
        
        print(f"Total documents: {result.total}")
        print(f"Sample documents: {len(result.hits)}")
        
        if result.hits:
            print("\nMost recent documents:")
            for i, doc in enumerate(result.hits[:3], 1):
                if isinstance(doc, dict):
                    ts = doc.get("@timestamp") or doc.get("time") or doc.get("start_time", "N/A")
                    event = doc.get("event", "N/A")
                    print(f"  {i}. @timestamp={ts}, event={event}")
        
        await opensearch_manager.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_data())

