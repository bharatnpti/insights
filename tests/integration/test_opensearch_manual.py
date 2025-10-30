#!/usr/bin/env python3
"""Manual test script for OpenSearch client.

This script allows you to quickly test the OpenSearch client with different
configurations without running the full test suite.

Usage:
    python test_opensearch_manual.py
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path to allow imports
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from nlap.config.settings import OpenSearchAuthSettings, OpenSearchClusterConfig
from nlap.opensearch.client import OpenSearchManager

# Note: Logging setup skipped to avoid settings validation issues in test script


async def test_opensearch_connection():
    """Test OpenSearch connection with provided credentials."""
    # Test configuration - using the working configuration from provided code
    config = {
        "name": "test-cluster",
        "host": "os-dashboard.oneai.yo-digital.com",
        "port": 443,  # Port 443 works with RequestsHttpConnection
        "use_ssl": True,
        "verify_certs": True,  # As in the working code
        "auth": {
            "username": "oneai_bharat",
            "password": "Z#Stp6$(qIyKaSGV",
        },
    }

    print("Testing OpenSearch Client")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Username: {config['auth']['username']}")
    print(f"  Use SSL: {config['use_ssl']}")
    print()

    try:
        # Create auth settings
        auth = OpenSearchAuthSettings(**config["auth"])
        
        # Create cluster config
        cluster_config = OpenSearchClusterConfig(
            name=config["name"],
            host=config["host"],
            port=config["port"],
            use_ssl=config["use_ssl"],
            verify_certs=config["verify_certs"],
            auth=auth,
        )

        async with OpenSearchManager(settings=cluster_config) as manager:
            print("✓ Client initialized successfully")
            print()

            # Test connection
            # print("Testing connection...")
            # health = await manager.test_connection()
            #
            # if health.healthy:
            #     print("✓ Connection test successful")
            #     print(f"  Cluster: {health.cluster_name}")
            #     print(f"  Version: {health.version}")
            #     print()
            # else:
            #     print(f"✗ Connection test failed: {health.error}")
            #     await manager.close()
            #     return False

            # Test query
            index = "ia-platform-prod-*"
            print(f"Testing query on index: {index}")
            query = {"match_all": {}}
            
            result = await manager.execute_query(
                index=index,
                query=query,
                size=5,
            )
            
            print("✓ Query executed successfully")
            print(f"  Total hits: {result.total}")
            print(f"  Query time: {result.took}ms")
            print(f"  Results returned: {len(result.hits)}")
            
            if result.hits:
                print()
                print("Sample result (first hit):")
                import json
                print(json.dumps(result.hits[0], indent=2))
            
            print()

            # Test metrics
            metrics = manager.get_metrics()
            print("Connection Metrics:")
            print(f"  Total queries: {metrics.get('total_queries', 0)}")
            print(f"  Success rate: {metrics.get('success_rate', 100.0):.2f}%")
            print(f"  Average latency: {metrics.get('average_latency_ms', 0.0):.2f}ms")
            print()

            print("✓ All tests completed successfully!")
            return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scroll_query():
    """Test scroll query functionality."""
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

    print("\nTesting Scroll Query...")
    
    try:
        auth = OpenSearchAuthSettings(**config["auth"])
        cluster_config = OpenSearchClusterConfig(
            name=config["name"],
            host=config["host"],
            port=config["port"],
            use_ssl=config["use_ssl"],
            verify_certs=config["verify_certs"],
            auth=auth,
        )

        async with OpenSearchManager(settings=cluster_config) as manager:
            index = "ia-platform-prod-*"
            query = {"match_all": {}}
            
            total_hits = 0
            batch_count = 0
            
            async for batch in manager.scroll_query(
                index=index,
                query=query,
                scroll="1m",
                size=100,
            ):
                batch_count += 1
                hits_in_batch = len(batch["hits"])
                total_hits += hits_in_batch
                print(f"  Batch {batch_count}: {hits_in_batch} hits (Total: {total_hits})")
                
                # Only process first few batches for testing
                if batch_count >= 3:
                    print("  (Stopping after 3 batches for testing)")
                    break
            
            print(f"✓ Scroll query test completed: {batch_count} batches, {total_hits} total hits")
            return True
            
    except Exception as e:
        print(f"✗ Scroll query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_opensearch_connection())
    
    if success and len(sys.argv) > 1 and sys.argv[1] == "--scroll":
        asyncio.run(test_scroll_query())
    
    sys.exit(0 if success else 1)
