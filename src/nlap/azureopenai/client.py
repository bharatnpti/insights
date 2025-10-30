"""Azure OpenAI client with Azure AD authentication."""

from typing import Optional, Union

from azure.identity import DefaultAzureCredential
from openai import AsyncOpenAI
from openai._client import AsyncClient

from nlap.config.settings import AzureOpenAISettings, get_settings
from nlap.utils.logger import get_logger

logger = get_logger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI client with Azure AD authentication support."""

    def __init__(self, settings: Optional[Union[dict, AzureOpenAISettings]] = None) -> None:
        """Initialize Azure OpenAI client with Azure AD authentication.

        Args:
            settings: Optional settings override (dict or AzureOpenAISettings object for testing)
        """
        if settings is None:
            self.settings = get_settings().azure_openai
        elif isinstance(settings, dict):
            self.settings = AzureOpenAISettings(**settings)
        else:
            self.settings = settings
        self.credential = DefaultAzureCredential()
        self._client: Optional[AsyncClient] = None

    def _get_token(self) -> str:
        """Get Azure AD token for Azure OpenAI with proper scope.

        Returns:
            Access token string

        Raises:
            Exception: If token acquisition fails
        """
        try:
            token = self.credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            return str(token.token)
        except Exception as e:
            logger.error(
                "Failed to acquire Azure AD token",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def _create_client(self) -> AsyncClient:
        """Create and configure Azure OpenAI async client.

        Returns:
            Configured AsyncOpenAI client instance
        """
        token = self._get_token()

        # Construct base URL - Azure OpenAI endpoint format with API version:
        # https://{resource}.openai.azure.com/openai/deployments/{deployment_name}?api-version={api_version}
        base_url = f"{self.settings.endpoint.rstrip('/')}/openai/deployments/{self.settings.deployment_name}"

        # Create client with Azure AD token
        # Note: api_version is included in the URL when making requests, not as init parameter
        client = AsyncOpenAI(
            api_key=token,  # Azure AD token is used as API key
            base_url=base_url,
            default_query={"api-version": self.settings.api_version},
        )

        logger.info(
            "Azure OpenAI client initialized",
            endpoint=self.settings.endpoint,
            safe_endpoint=self.settings.endpoint.split("/")[2] if "/" in self.settings.endpoint else "***",
            deployment=self.settings.deployment_name,
            api_version=self.settings.api_version,
        )

        return client

    async def get_client(self) -> AsyncClient:
        """Get or create Azure OpenAI client instance.

        Returns:
            AsyncOpenAI client instance
        """
        if self._client is None:
            self._client = await self._create_client()
        return self._client

    async def close(self) -> None:
        """Close the client and clean up resources."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Azure OpenAI client closed")

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> dict:
        """Create a chat completion using Azure OpenAI.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call

        Returns:
            Chat completion response dictionary
        """
        client = await self.get_client()

        try:
            response = await client.chat.completions.create(
                model=self.settings.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            logger.debug(
                "Chat completion created",
                model=self.settings.deployment_name,
                messages_count=len(messages),
            )

            return {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content,
                        },
                        "finish_reason": choice.finish_reason,
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                }
                if response.usage
                else None,
            }
        except Exception as e:
            logger.error(
                "Chat completion failed",
                error=str(e),
                error_type=type(e).__name__,
                model=self.settings.deployment_name,
            )
            raise

    async def __aenter__(self) -> "AzureOpenAIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

