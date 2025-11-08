"""
Web Search feature for the MCP MixSearch

Provides comprehensive web search capabilities with multiple engines and content extraction.
"""

from .service import WebSearchService
from .tool import register_tool

__all__ = ["WebSearchService", "register_tool"]