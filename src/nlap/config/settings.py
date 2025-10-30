"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenSearchSettings(BaseSettings):
    """OpenSearch connection settings."""

    model_config = SettingsConfigDict(env_prefix="OPENSEARCH_", case_sensitive=False)

    host: str = Field(..., description="OpenSearch cluster endpoint")
    port: int = Field(default=9200, description="OpenSearch port")
    username: str = Field(..., description="Basic auth username")
    password: str = Field(..., description="Basic auth password")
    use_ssl: bool = Field(default=True, description="Enable SSL")
    verify_certs: bool = Field(default=True, description="Verify SSL certificates")
    ca_certs: Optional[str] = Field(default=None, description="Path to CA certificates")

    @property
    def url(self) -> str:
        """Construct OpenSearch URL."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"


class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI connection settings."""

    model_config = SettingsConfigDict(env_prefix="AZURE_", case_sensitive=False)

    endpoint: str = Field(..., description="Azure OpenAI endpoint URL")
    deployment_name: str = Field(
        default="gpt-4", description="Model deployment name"
    )
    api_version: str = Field(
        default="2024-10-21", description="API version"
    )


class AppSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    app_name: str = Field(default="NLAP", description="Application name")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    opensearch: OpenSearchSettings = Field(default_factory=OpenSearchSettings)
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    app: AppSettings = Field(default_factory=AppSettings)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

