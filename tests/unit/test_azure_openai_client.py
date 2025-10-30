"""Tests for Azure OpenAI client with multiple deployment configurations."""

from typing import Any

import pytest

from nlap.azureopenai.client import AzureOpenAIClient


# Test configurations based on available Azure OpenAI resources
DEPLOYMENT_CONFIGS = [
    # GPT4-UK (UK South) configurations
    {
        "endpoint": "https://gpt4-uk.openai.azure.com/",
        "deployment_name": "GPT4-UK",
        "api_version": "2024-10-21",
        "region": "uksouth",
        "resource": "GPT4-UK",
    },
    {
        "endpoint": "https://gpt4-uk.openai.azure.com/",
        "deployment_name": "GPT4-32k-UK",
        "api_version": "2024-10-21",
        "region": "uksouth",
        "resource": "GPT4-UK",
    },
    {
        "endpoint": "https://gpt4-uk.openai.azure.com/",
        "deployment_name": "GPT35T0301",
        "api_version": "2024-10-21",
        "region": "uksouth",
        "resource": "GPT4-UK",
    },
    {
        "endpoint": "https://gpt4-uk.openai.azure.com/",
        "deployment_name": "GPT35T-1106",
        "api_version": "2024-10-21",
        "region": "uksouth",
        "resource": "GPT4-UK",
    },
    # GPT4-SE-dev (Sweden Central) configurations
    {
        "endpoint": "https://gpt4-se-dev.openai.azure.com/",
        "deployment_name": "GPT-4o",
        "api_version": "2024-10-21",
        "region": "swedencentral",
        "resource": "GPT4-SE-dev",
    },
    {
        "endpoint": "https://gpt4-se-dev.openai.azure.com/",
        "deployment_name": "GPT4-turbo",
        "api_version": "2024-10-21",
        "region": "swedencentral",
        "resource": "GPT4-SE-dev",
    },
    {
        "endpoint": "https://gpt4-se-dev.openai.azure.com/",
        "deployment_name": "gpt-4o-mini-real",
        "api_version": "2024-10-21",
        "region": "swedencentral",
        "resource": "GPT4-SE-dev",
    },
    {
        "endpoint": "https://gpt4-se-dev.openai.azure.com/",
        "deployment_name": "dt-gpt-35-turbo-16k",
        "api_version": "2024-10-21",
        "region": "swedencentral",
        "resource": "GPT4-SE-dev",
    },
    # gpt-us-testenv (East US) configurations
    {
        "endpoint": "https://gpt-us-testenv.openai.azure.com/",
        "deployment_name": "gpt4-0125-us",
        "api_version": "2024-10-21",
        "region": "eastus",
        "resource": "gpt-us-testenv",
    },
    {
        "endpoint": "https://gpt-us-testenv.openai.azure.com/",
        "deployment_name": "gpt-35-t-0301",
        "api_version": "2024-10-21",
        "region": "eastus",
        "resource": "gpt-us-testenv",
    },
    {
        "endpoint": "https://gpt-us-testenv.openai.azure.com/",
        "deployment_name": "gpt-4o-mini",
        "api_version": "2024-10-21",
        "region": "eastus",
        "resource": "gpt-us-testenv",
    },
]

# Representative samples for quick testing (one from each resource)
QUICK_TEST_CONFIGS = [
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


@pytest.fixture
def test_messages() -> list[dict[str, str]]:
    """Provide test messages for chat completion."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello, World!' and nothing else."},
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("config", DEPLOYMENT_CONFIGS)
async def test_azure_openai_client_initialization(config: dict[str, Any]) -> None:
    """Test Azure OpenAI client initialization with different deployments."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    client = AzureOpenAIClient(settings=settings)
    assert client.settings.endpoint == config["endpoint"]
    assert client.settings.deployment_name == config["deployment_name"]
    assert client.settings.api_version == config["api_version"]
    assert client._client is None  # Client not yet created

    # Clean up
    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_client_context_manager(config: dict[str, Any]) -> None:
    """Test Azure OpenAI client as async context manager."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    async with AzureOpenAIClient(settings=settings) as client:
        assert client.settings.endpoint == config["endpoint"]
        assert client.settings.deployment_name == config["deployment_name"]

    # Client should be closed after context exit
    assert client._client is None


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_chat_completion(
    config: dict[str, Any], test_messages: list[dict[str, str]]
) -> None:
    """Test chat completion with different Azure OpenAI deployments."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    async with AzureOpenAIClient(settings=settings) as client:
        response = await client.chat_completion(
            messages=test_messages,
            temperature=0.0,
            max_tokens=50,
        )

        # Verify response structure
        assert "id" in response
        assert "model" in response
        assert "choices" in response
        assert len(response["choices"]) > 0

        # Verify choice structure
        choice = response["choices"][0]
        assert "message" in choice
        assert "role" in choice["message"]
        assert "content" in choice["message"]
        assert choice["message"]["role"] == "assistant"
        assert len(choice["message"]["content"]) > 0

        # Verify usage if available
        if response.get("usage"):
            assert "prompt_tokens" in response["usage"]
            assert "completion_tokens" in response["usage"]
            assert "total_tokens" in response["usage"]

        # Verify model matches deployment
        assert response["model"] == config["deployment_name"]

        # Verify content contains expected text
        content = choice["message"]["content"]
        assert "Hello" in content or "hello" in content.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_client_reuse(config: dict[str, Any]) -> None:
    """Test that client instance is reused on multiple calls."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    client = AzureOpenAIClient(settings=settings)

    # First call should create client
    client1 = await client.get_client()
    assert client1 is not None

    # Second call should return same client
    client2 = await client.get_client()
    assert client1 is client2

    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_different_temperatures(
    config: dict[str, Any], test_messages: list[dict[str, str]]
) -> None:
    """Test chat completion with different temperature settings."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    async with AzureOpenAIClient(settings=settings) as client:
        # Test with low temperature (deterministic)
        response_low = await client.chat_completion(
            messages=test_messages,
            temperature=0.0,
            max_tokens=50,
        )

        # Test with high temperature (creative)
        response_high = await client.chat_completion(
            messages=test_messages,
            temperature=1.0,
            max_tokens=50,
        )

        assert response_low["choices"][0]["message"]["content"]
        assert response_high["choices"][0]["message"]["content"]


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_max_tokens(config: dict[str, Any]) -> None:
    """Test chat completion with max_tokens parameter."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    messages = [
        {"role": "user", "content": "Count from 1 to 100."},
    ]

    async with AzureOpenAIClient(settings=settings) as client:
        response = await client.chat_completion(
            messages=messages,
            temperature=0.0,
            max_tokens=20,  # Limit tokens to ensure parameter works
        )

        assert response["choices"][0]["finish_reason"] in ["stop", "length"]
        if response.get("usage"):
            assert response["usage"]["completion_tokens"] <= 20


@pytest.mark.asyncio
@pytest.mark.parametrize("config", QUICK_TEST_CONFIGS)
async def test_azure_openai_error_handling(config: dict[str, Any]) -> None:
    """Test error handling with invalid messages."""
    settings = {
        "endpoint": config["endpoint"],
        "deployment_name": config["deployment_name"],
        "api_version": config["api_version"],
    }

    async with AzureOpenAIClient(settings=settings) as client:
        # Empty messages should fail
        with pytest.raises(Exception):
            await client.chat_completion(messages=[])


@pytest.mark.asyncio
async def test_azure_openai_all_gpt4o_deployments() -> None:
    """Test all GPT-4o deployments across regions."""
    gpt4o_configs = [
        {
            "endpoint": "https://gpt4-uk.openai.azure.com/",
            "deployment_name": "GPT4-UK",
            "api_version": "2024-10-21",
        },
        {
            "endpoint": "https://gpt4-se-dev.openai.azure.com/",
            "deployment_name": "GPT-4o",
            "api_version": "2024-10-21",
        },
        {
            "endpoint": "https://gpt-us-testenv.openai.azure.com/",
            "deployment_name": "gpt4-0125-us",
            "api_version": "2024-10-21",
        },
    ]

    messages = [
        {"role": "user", "content": "What is 2+2? Answer with just the number."},
    ]

    for config in gpt4o_configs:
        async with AzureOpenAIClient(settings=config) as client:
            response = await client.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=10,
            )

            assert response["model"] == config["deployment_name"]
            assert "4" in response["choices"][0]["message"]["content"]


@pytest.mark.asyncio
async def test_azure_openai_gpt4o_mini_deployments() -> None:
    """Test GPT-4o-mini deployments for cost-effective testing."""
    gpt4o_mini_configs = [
        {
            "endpoint": "https://gpt4-se-dev.openai.azure.com/",
            "deployment_name": "gpt-4o-mini-real",
            "api_version": "2024-10-21",
        },
        {
            "endpoint": "https://gpt-us-testenv.openai.azure.com/",
            "deployment_name": "gpt-4o-mini",
            "api_version": "2024-10-21",
        },
    ]

    messages = [
        {"role": "user", "content": "Say 'test' in one word."},
    ]

    for config in gpt4o_mini_configs:
        async with AzureOpenAIClient(settings=config) as client:
            response = await client.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=10,
            )

            assert response["model"] == config["deployment_name"]
            assert len(response["choices"][0]["message"]["content"]) > 0


@pytest.mark.asyncio
async def test_azure_openai_gpt35_turbo_deployments() -> None:
    """Test GPT-3.5 Turbo deployments."""
    gpt35_configs = [
        {
            "endpoint": "https://gpt4-uk.openai.azure.com/",
            "deployment_name": "GPT35T0301",
            "api_version": "2024-10-21",
        },
        {
            "endpoint": "https://gpt4-se-dev.openai.azure.com/",
            "deployment_name": "dt-gpt-35-turbo-16k",
            "api_version": "2024-10-21",
        },
        {
            "endpoint": "https://gpt-us-testenv.openai.azure.com/",
            "deployment_name": "gpt-35-t-0301",
            "api_version": "2024-10-21",
        },
    ]

    messages = [
        {"role": "user", "content": "Respond with 'OK'."},
    ]

    for config in gpt35_configs:
        async with AzureOpenAIClient(settings=config) as client:
            response = await client.chat_completion(
                messages=messages,
                temperature=0.0,
                max_tokens=10,
            )

            assert response["model"] == config["deployment_name"]
            assert len(response["choices"][0]["message"]["content"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

