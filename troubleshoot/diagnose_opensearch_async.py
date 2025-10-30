#!/usr/bin/env python3
"""Diagnostic script to identify the async issue with OpenSearch client."""

import asyncio
import inspect
from opensearchpy import AsyncOpenSearch, OpenSearch

# Check AsyncOpenSearch client
print("=== AsyncOpenSearch Analysis ===")
print(f"AsyncOpenSearch class: {AsyncOpenSearch}")
print()

# Check search method
if hasattr(AsyncOpenSearch, 'search'):
    search_method = getattr(AsyncOpenSearch, 'search')
    print(f"search method: {search_method}")
    print(f"Type: {type(search_method)}")
    print(f"Is coroutine function: {inspect.iscoroutinefunction(search_method)}")
    print(f"Is coroutine: {asyncio.iscoroutine(search_method)}")
    
    try:
        sig = inspect.signature(search_method)
        print(f"Signature: {sig}")
    except Exception as e:
        print(f"Could not get signature: {e}")
    print()

# Check info method  
if hasattr(AsyncOpenSearch, 'info'):
    info_method = getattr(AsyncOpenSearch, 'info')
    print(f"info method: {info_method}")
    print(f"Type: {type(info_method)}")
    print(f"Is coroutine function: {inspect.iscoroutinefunction(info_method)}")
    print()

# Try to create an instance and check the actual method
try:
    # Create a dummy config to see how the method works
    config = {
        "hosts": [{"host": "localhost", "port": 9200}],
        "http_auth": ("user", "pass"),
    }
    print("=== Creating AsyncOpenSearch instance ===")
    client = AsyncOpenSearch(**config)
    print(f"Client instance: {client}")
    print(f"Client search method: {client.search}")
    print(f"Client search type: {type(client.search)}")
    print(f"Is coroutine function (instance method): {inspect.iscoroutinefunction(client.search)}")
    
    # Check if it's a bound method
    if hasattr(client.search, '__self__'):
        print("It's a bound method")
    if hasattr(client.search, '__func__'):
        print("It has __func__ attribute")
        
except Exception as e:
    print(f"Error creating client: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== Checking actual method call ===")
# Check what happens when we try to call it (without actually calling)
try:
    if hasattr(AsyncOpenSearch, 'search'):
        # Try to see what the actual method signature is
        import inspect
        source = inspect.getsource(AsyncOpenSearch.search) if inspect.isfunction(AsyncOpenSearch.search) else None
        if source:
            print("Source code (first 200 chars):")
            print(source[:200])
except Exception as e:
    print(f"Could not get source: {e}")

