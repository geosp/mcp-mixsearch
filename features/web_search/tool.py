"""
Web Search Tool Implementation

Provides web search tools through the MCP protocol.
"""

import logging
from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp_service_kit.utils import inject_docstring, load_instruction

from .filters import SearchFilters
from .service import WebSearchService
from .url_safety import UnsafeURLError

logger = logging.getLogger(__name__)


def register_tool(mcp: FastMCP, web_search_service: WebSearchService) -> None:
    """
    Register web search tools with the MCP server

    Args:
        mcp: FastMCP server instance
        web_search_service: WebSearchService instance
    """

    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions.md", __file__))
    async def full_web_search(
        query: str,
        limit: int = 5,
        include_content: bool = True,
        max_content_length: Optional[int] = None,
        top_n: Optional[int] = None,  # Alternative name for limit (for compatibility)
        recency_days: Optional[int] = None,
        source: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> str:
        """Comprehensive web search with full content extraction"""
        filters = SearchFilters.from_tool_args(limit, top_n, recency_days, source, language, country)
        logger.info(f"MCP tool full_web_search: query='{query}', {filters}")

        result = await web_search_service.search_and_extract(
            query=query,
            filters=filters,
            include_content=include_content,
            max_content_length=max_content_length,
        )

        # Format for MCP response
        response_text = f"Search completed for '{result['query']}' with {result['total_results']} results:\n\n"

        for i, search_result in enumerate(result['results'], 1):
            response_text += f"**{i}. {search_result['title']}**\n"
            response_text += f"URL: {search_result['url']}\n"
            response_text += f"Description: {search_result['description']}\n"

            if search_result.get('full_content'):
                response_text += f"\n**Full Content:**\n{search_result['full_content']}\n"
            elif search_result.get('fetch_status') == 'error':
                response_text += f"\n**Content Extraction Failed:** {search_result.get('error') or 'Unknown error'}\n"

            response_text += "\n---\n\n"

        logger.info(f"MCP tool full_web_search completed: {result['total_results']} results")
        return response_text

    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions_summaries.md", __file__))
    async def get_web_search_summaries(
        query: str,
        limit: int = 5,
        top_n: Optional[int] = None,  # Alternative name for limit (for compatibility)
        recency_days: Optional[int] = None,
        source: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> str:
        """Lightweight web search returning only summaries"""
        filters = SearchFilters.from_tool_args(limit, top_n, recency_days, source, language, country)
        logger.info(f"MCP tool get_web_search_summaries: query='{query}', {filters}")

        result = await web_search_service.search_summaries(query=query, filters=filters)

        # Format for MCP response
        response_text = f"Search summaries for '{result['query']}' with {result['total_results']} results:\n\n"

        for i, summary in enumerate(result['results'], 1):
            response_text += f"**{i}. {summary['title']}**\n"
            response_text += f"URL: {summary['url']}\n"
            response_text += f"Description: {summary['description']}\n\n---\n\n"

        logger.info(f"MCP tool get_web_search_summaries completed: {result['total_results']} results")
        return response_text

    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions_single_page.md", __file__))
    async def get_single_web_page_content(url: str, max_content_length: Optional[int] = None) -> str:
        """Extract content from a single webpage"""
        logger.info(f"MCP tool get_single_web_page_content: url='{url}'")

        try:
            content = await web_search_service.extract_single_page(
                url=url,
                max_content_length=max_content_length
            )
        except UnsafeURLError as e:
            logger.warning(f"Blocked get_single_web_page_content for {url}: {e}")
            raise ToolError(f"URL not allowed: {e}") from e

        word_count = len(content.split())

        response_text = f"**Page Content from: {url}**\n\n{content}\n\n"
        response_text += f"**Word count:** {word_count}\n"

        logger.info(f"MCP tool get_single_web_page_content completed: {word_count} words")
        return response_text
