#!/usr/bin/env python3
"""Test actual async behavior of opensearchpy."""

import asyncio
from opensearchpy import AsyncOpenSearch

async def test_async_call():
    """Test if AsyncOpenSearch methods are actually async."""
    config = {
        "hosts": [{"host": "localhost", "port": 9200}],
        "http_auth": ("user", "pass"),
        "verify_certs": False,
    }
    
    try:
        client = AsyncOpenSearch(**config)
        print(f"Client: {client}")
        print(f"Client.search type: {type(client.search)}")
        
        # Try to call it and see what we get
        # Note: This will fail because localhost:9200 doesn't exist
        # but we can see what type of object it returns
        try:
            # This should return a coroutine
            result = client.search(index="test", body={"query": {"match_all": {}}})
            print(f"Result type: {type(result)}")
            print(f"Is coroutine: {asyncio.iscoroutine(result)}")
            print(f"Result: {result}")
            
            # If it's a coroutine, try to await it (will fail, but shows the type)
            if asyncio.iscoroutine(result):
                print("✓ It's a coroutine - correct!")
                try:
                    await result
                except Exception as e:
                    print(f"  Error on await (expected): {type(e).__name__}: {e}")
            else:
                print("✗ It's NOT a coroutine - this is the problem!")
                print(f"  Result value: {result}")
                
        except Exception as e:
            print(f"Error calling search: {type(e).__name__}: {e}")
            
    except Exception as e:
        print(f"Error creating client: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_async_call())

