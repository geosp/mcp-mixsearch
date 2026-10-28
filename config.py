"""
Configuration for MCP MixSearch Server

Each section is a pydantic-settings model that reads its own environment
variables when instantiated. Loading .env is handled by mcp-service-kit.
"""

from typing import Optional

from mcp_service_kit import BaseServerConfig
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSearchConfig(BaseSettings):
    """
    Web search configuration

    Environment variables: BRAVE_API_KEY, MAX_CONTENT_LENGTH, MAX_CONCURRENT_REQUESTS,
    ALLOW_PRIVATE_URLS, DDGS_BACKEND
    """
    model_config = SettingsConfigDict(extra="ignore")

    brave_api_key: Optional[str] = Field(default=None, description="Brave Search API key; enables the Brave API engine")
    max_content_length: int = Field(default=500000, description="Max content length for extraction")
    max_concurrent_requests: int = Field(default=5, description="Max concurrent content extraction requests")
    allow_private_urls: bool = Field(
        default=False,
        description="Allow fetching loopback, private and link-local addresses (only for trusted networks)"
    )
    ddgs_backend: str = Field(default="auto", description="ddgs backend(s), e.g. 'auto' or 'duckduckgo,bing'")


class AppConfig(BaseModel):
    """
    Application configuration

    The server section goes to the server; the rest goes to the service.
    """
    server: BaseServerConfig = Field(default_factory=BaseServerConfig)
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
