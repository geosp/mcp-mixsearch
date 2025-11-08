"""
Standalone MCP MixSearch Server

This is a standalone server that demonstrates the web search functionality.
"""

import sys
import os
import argparse
# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from core import BaseServerConfig, BaseMCPServer, BaseService
from features.web_search.service import WebSearchService
from features.web_search.tool import register_tool
import logging

logger = logging.getLogger(__name__)


class MixSearchService(BaseService):
    """Main service for MCP MixSearch"""
    
    def __init__(self):
        self.web_search_service = WebSearchService()
    
    def get_service_name(self) -> str:
        """Get the service name"""
        return "mixsearch"
    
    def initialize(self):
        """Initialize the service"""
        logger.info("Initializing MixSearch service")
    
    def register_mcp_tools(self, mcp):
        """Register MCP tools"""
        register_tool(mcp, self.web_search_service)
    
    def cleanup(self):
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
        return "1.0.0"
    
    @property
    def allowed_cors_origins(self):
        cors_origins = os.getenv("MCP_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        if cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in cors_origins.split(",")]
    
    def create_router(self):
        """Create REST API router"""
        from features.web_search.routes import create_router
        return create_router(self.service.web_search_service)
    
    def create_auth_provider(self):
        """Create authentication provider"""
        return None
    
    def register_exception_handlers(self, app):
        """Register custom exception handlers and middleware"""
        from fastapi import Request
        from fastapi.responses import JSONResponse
        import json
        import urllib.parse
        
        @app.middleware("http")
        async def convert_mcp_parameters(request: Request, call_next):
            """Convert MCP-style parameters to simple values for REST endpoints"""
            
            # Only process GET requests to /search endpoints
            if request.method == "GET" and request.url.path.startswith("/search/"):
                # Parse query parameters
                query_params = dict(request.query_params)
                converted_params = {}
                
                for key, value in query_params.items():
                    # Check if value looks like "[object Object]" (URL encoded or not)
                    decoded_value = urllib.parse.unquote_plus(value)
                    
                    if decoded_value == "[object Object]":
                        # This is a JavaScript object that wasn't serialized properly by Open WebUI
                        # Set reasonable defaults based on parameter name
                        if key == "query":
                            converted_params[key] = "test query"  # Default search query
                            logger.warning(f"Parameter '{key}' has invalid value '[object Object]', using default: 'test query'")
                        elif key == "limit":
                            converted_params[key] = "5"  # Default limit
                            logger.warning(f"Parameter '{key}' has invalid value '[object Object]', using default: 5")
                        elif key == "recency_days":
                            converted_params[key] = "1"  # Default recency
                            logger.warning(f"Parameter '{key}' has invalid value '[object Object]', using default: 1")
                        else:
                            logger.warning(f"Parameter '{key}' has invalid value '[object Object]', skipping")
                            continue
                    else:
                        # Try to parse as JSON in case it's a serialized MCP parameter
                        try:
                            parsed = json.loads(decoded_value)
                            if isinstance(parsed, dict) and "type" in parsed and "value" in parsed:
                                # This is an MCP-style parameter, extract the value
                                converted_params[key] = str(parsed["value"])
                                logger.info(f"Converted MCP parameter '{key}': {parsed} -> {parsed['value']}")
                            else:
                                converted_params[key] = decoded_value
                        except (json.JSONDecodeError, TypeError):
                            # Not JSON, use as-is
                            converted_params[key] = decoded_value
                
                # Reconstruct the query string with converted parameters
                if converted_params != query_params:
                    new_query_string = urllib.parse.urlencode(converted_params)
                    new_url = str(request.url).split('?')[0] + ('?' + new_query_string if new_query_string else '')
                    
                    # Create a new request with converted parameters
                    from starlette.requests import Request as StarletteRequest
                    
                    # Modify the request scope to use new query string
                    scope = request.scope.copy()
                    scope["query_string"] = new_query_string.encode()
                    
                    # Create new request with modified scope
                    modified_request = StarletteRequest(scope, request.receive)
                    
                    logger.info(f"Converted MCP request: {request.url} -> {new_url}")
                    response = await call_next(modified_request)
                    return response
            
            # For all other requests, proceed normally
            return await call_next(request)

    def run_mcp_only(self) -> None:
        """
        Run server in MCP-only mode (stdio or HTTP)
        
        This method handles both stdio and HTTP MCP-only modes based on transport configuration.
        """
        import os
        import uvicorn
        import anyio
        from functools import partial
        
        # Determine transport
        transport = self.get_config("server.transport", self.get_config("transport", "stdio"))
        
        if transport == "stdio":
            # Run MCP in stdio mode
            logger.info(f"Starting {self.service_title} in MCP stdio mode")
            logger.info("=" * 70)
            
            # Create MCP app
            self._mcp_app = self.create_mcp_app()
            
            # Run in stdio mode
            anyio.run(
                partial(
                    self._mcp_app.run_async,
                    transport="stdio",
                    show_banner=False
                )
            )
            
        else:
            # Pure MCP protocol over HTTP
            host = self.get_config("server.host", self.get_config("host", "0.0.0.0"))
            port = self.get_config("server.port", self.get_config("port", 3000))
            
            logger.info(f"Starting {self.service_title} in MCP-only HTTP mode")
            logger.info("=" * 70)
            logger.info(f"MCP Endpoint: http://{host}:{port}/mcp")
            logger.info("=" * 70)
            
            # Create MCP app
            self._mcp_app = self.create_mcp_app()
            
            # Run HTTP with MCP only
            asgi_app = self._mcp_app.http_app()
            self._fastapi_app = None
            
            uvicorn.run(
                asgi_app,
                host=host,
                port=port,
                log_level="info"
            )

    def run_rest_and_mcp(self) -> None:
        """
        Run server with both REST API and MCP protocol over HTTP
        
        This mode provides REST endpoints for direct API access and MCP endpoints
        for MCP clients, all served over HTTP.
        """
        import uvicorn
        
        # REST API + MCP protocol (always HTTP)
        host = self.get_config("server.host", self.get_config("host", "0.0.0.0"))
        port = self.get_config("server.port", self.get_config("port", 3000))
        
        logger.info(f"Starting {self.service_title} with REST API + MCP")
        logger.info("=" * 70)
        logger.info(f"Server: http://{host}:{port}")
        logger.info(f"API Docs: http://{host}:{port}/docs")
        logger.info(f"Health Check: http://{host}:{port}/health")
        logger.info(f"MCP Endpoint: http://{host}:{port}/mcp")
        logger.info("=" * 70)
        
        # Create MCP app
        self._mcp_app = self.create_mcp_app()
        
        # Create FastAPI app with MCP mounted
        self._fastapi_app = self.create_fastapi_app(self._mcp_app)
        
        uvicorn.run(
            self._fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )


def main():
    """Main entry point for the standalone MCP MixSearch server"""
    parser = argparse.ArgumentParser(description="MCP MixSearch Server")
    parser.add_argument(
        "--mode",
        choices=["mcp", "stdio", "rest"],
        default=None,
        help="Server mode: mcp/stdio (MCP over stdio), rest (HTTP with REST API + MCP)"
    )
    
    args = parser.parse_args()
    
    # Set environment variables based on mode to work with core framework
    if args.mode == "mcp":
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MCP_ONLY"] = "true"  # Use core framework's config key
    elif args.mode == "stdio":
        os.environ["MCP_TRANSPORT"] = "stdio"
        os.environ["MCP_MCP_ONLY"] = "true"  # Use core framework's config key
    elif args.mode == "rest":
        os.environ["MCP_TRANSPORT"] = "http"
        os.environ["MCP_MCP_ONLY"] = "false"  # Use core framework's config key
    # If no mode specified, use defaults from environment or BaseServerConfig
    
    # Load configuration using core framework
    config = BaseServerConfig.from_env(env_prefix="MCP_")

    # Create service
    service = MixSearchService()

    # Create and run server using core framework's run() method
    server = MixSearchServer(config, service)
    server.run()  # This now uses the core framework's mode handling


if __name__ == "__main__":
    main()