#!/usr/bin/env python3
"""Manual test script for Azure OpenAI client.

This script allows you to quickly test the Azure OpenAI client with different
deployments without running the full test suite.

Usage:
    # Test with GPT4-UK
    export AZURE_ENDPOINT='https://gpt4-uk.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='GPT4-UK'
    export AZURE_API_VERSION='2024-10-21'
    python test_azure_openai_manual.py

    # Test with GPT4-SE-dev
    export AZURE_ENDPOINT='https://gpt4-se-dev.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='GPT-4o'
    export AZURE_API_VERSION='2024-10-21'
    python test_azure_openai_manual.py

    # Test with gpt-us-testenv
    export AZURE_ENDPOINT='https://gpt-us-testenv.openai.azure.com/'
    export AZURE_DEPLOYMENT_NAME='gpt4-0125-us'
    export AZURE_API_VERSION='2024-10-21'
    python test_azure_openai_manual.py
"""

import asyncio
import os
import sys

from nlap.azureopenai.client import AzureOpenAIClient


async def test_chat_completion():
    """Test chat completion with current environment configuration."""
    # Get settings from environment
    endpoint = os.getenv("AZURE_ENDPOINT")
    deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")

    if not endpoint or not deployment_name:
        print("Error: AZURE_ENDPOINT and AZURE_DEPLOYMENT_NAME must be set")
        print("\nExample:")
        print("  export AZURE_ENDPOINT='https://gpt4-uk.openai.azure.com/'")
        print("  export AZURE_DEPLOYMENT_NAME='GPT4-UK'")
        print("  export AZURE_API_VERSION='2024-10-21'")
        sys.exit(1)

    settings = {
        "endpoint": endpoint,
        "deployment_name": deployment_name,
        "api_version": api_version,
    }

    print(f"Testing Azure OpenAI Client")
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {deployment_name}")
    print(f"  API Version: {api_version}")
    print()

    try:
        async with AzureOpenAIClient(settings=settings) as client:
            print("✓ Client initialized successfully")
            print()

            # Simple test
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, World!' and nothing else."},
            ]

            print("Sending test message...")
            response = await client.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=50,
            )

            print("✓ Chat completion successful")
            print()
            print("Response:")
            print(f"  Model: {response['model']}")
            print(f"  ID: {response['id']}")
            print(f"  Content: {response['choices'][0]['message']['content']}")
            if response.get("usage"):
                print(f"  Usage: {response['usage']}")
            print()
            print("✓ Test completed successfully!")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_all_quick_configs():
    """Test all quick test configurations."""
    quick_configs = [
        {
            "endpoint": "https://gpt4-uk.openai.azure.com/",
            "deployment_name": "GPT4-UK",
            "api_version": "2024-10-21",
            "region": "uksouth",
            "resource": "GPT4-UK",
        },
        {
            "endpoint": "https://gpt4-se-dev.openai.azure.com/",
            "deployment_name": "GPT-4o",
            "api_version": "2024-10-21",
            "region": "swedencentral",
            "resource": "GPT4-SE-dev",
        },
        {
            "endpoint": "https://gpt-us-testenv.openai.azure.com/",
            "deployment_name": "gpt4-0125-us",
            "api_version": "2024-10-21",
            "region": "eastus",
            "resource": "gpt-us-testenv",
        },
    ]

    print("Testing all quick configurations...")
    print()

    messages = [
        {"role": "user", "content": "Say 'OK' and nothing else."},
    ]

    results = []
    for config in quick_configs:
        try:
            async with AzureOpenAIClient(
                settings={
                    "endpoint": config["endpoint"],
                    "deployment_name": config["deployment_name"],
                    "api_version": config["api_version"],
                }
            ) as client:
                response = await client.chat_completion(
                    messages=messages,
                    temperature=0.0,
                    max_tokens=10,
                )
                results.append(
                    {
                        "config": config,
                        "status": "success",
                        "content": response["choices"][0]["message"]["content"],
                    }
                )
                print(
                    f"✓ {config['resource']} ({config['region']}) - {config['deployment_name']}"
                )
        except Exception as e:
            results.append(
                {
                    "config": config,
                    "status": "failed",
                    "error": str(e),
                }
            )
            print(
                f"✗ {config['resource']} ({config['region']}) - {config['deployment_name']}: {e}"
            )

    print()
    print("Summary:")
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"  Successful: {success_count}/{len(results)}")
    print(f"  Failed: {len(results) - success_count}/{len(results)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        asyncio.run(test_all_quick_configs())
    else:
        asyncio.run(test_chat_completion())

