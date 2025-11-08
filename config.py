"""
Configuration for MCP MixSearch Server
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ServerConfig(BaseModel):
    """
    Server configuration
    """
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables"""
        return cls(
            host=os.getenv("MCP_HOST", "localhost"),
            port=int(os.getenv("MCP_PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )


class WebSearchConfig(BaseModel):
    """
    Web search configuration
    """
    brave_api_key: Optional[str] = Field(default=None, description="Brave Search API key")
    max_content_length: int = Field(default=500000, description="Max content length for extraction")
    max_concurrent_requests: int = Field(default=5, description="Max concurrent content extraction requests")

    @classmethod
    def from_env(cls) -> "WebSearchConfig":
        """Load web search configuration from environment variables"""
        return cls(
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", "500000")),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        )


class AppConfig(BaseModel):
    """
    Application configuration
    """
    server: ServerConfig
    web_search: WebSearchConfig

    @classmethod
    def load(cls) -> "AppConfig":
        """Load complete application configuration"""
        return cls(
            server=ServerConfig.from_env(),
            web_search=WebSearchConfig.from_env()
        )