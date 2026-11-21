"""
MCP MixSearch Server

Exposes the web search tools over MCP (stdio or streamable HTTP) using mcp-service-kit.

Run it with:
    mcp-mixsearch --mode stdio
    mcp-mixsearch --mode http --port 3000 --no-auth
"""

import logging
from importlib.metadata import version

from fastmcp import FastMCP
from mcp_service_kit import BaseMCPServer, BaseService, create_main_with_modes
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import AppConfig
from features.web_search.service import WebSearchService
from features.web_search.tool import register_tool

logger = logging.getLogger(__name__)

# Installed package version; running server.py without installing the package is unsupported
SERVICE_VERSION = version("mcp-mixsearch")


class MixSearchService(BaseService):
    """Main service for MCP MixSearch"""

    def __init__(self, config: AppConfig):
        self.web_search_service = WebSearchService(config.web_search)

    def get_service_name(self) -> str:
        """Get the service name"""
        return "mixsearch"

    def initialize(self) -> None:
        """Initialize the service"""
        logger.info("Initializing MixSearch service")

    def register_mcp_tools(self, mcp: FastMCP) -> None:
        """Register MCP tools and the HTTP health check"""
        register_tool(mcp, self.web_search_service)

        @mcp.custom_route("/health", methods=["GET"])
        async def health(request: Request) -> JSONResponse:
            """Health check endpoint (HTTP transport only)"""
            return JSONResponse(
                {
                    "status": "healthy",
                    "service": self.get_service_name(),
                    "version": SERVICE_VERSION,
                }
            )

    def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("Cleaning up MixSearch service")


class MixSearchServer(BaseMCPServer):
    """MCP server for web search functionality"""

    @property
    def service_title(self) -> str:
        return "MCP MixSearch"

    @property
    def service_description(self) -> str:
        return "Comprehensive web search with content extraction"

    @property
    def service_version(self) -> str:
        return SERVICE_VERSION


main = create_main_with_modes(
    MixSearchServer,
    service_factory=MixSearchService,
    config_factory=AppConfig,
    service_name="mcp-mixsearch",
    description="MCP MixSearch - Comprehensive web search with content extraction",
)


if __name__ == "__main__":
    main()
