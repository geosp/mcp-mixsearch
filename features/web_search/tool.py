"""
Web Search Tool Implementation

Provides web search tools through the MCP protocol.
"""

import logging
from typing import Dict, Any

from fastmcp import FastMCP

from core.utils import inject_docstring, load_instruction
from .service import WebSearchService

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
        max_content_length: int = None,
        top_n: int = None,  # Alternative name for limit (for compatibility)
        recency_days: int = None,  # Days to look back (now supported!)
        source: str = None,  # Source type filter (partially supported)
        language: str = None,  # Language filter (now supported!)
        country: str = None  # Country filter (now supported!)
    ) -> Dict[str, Any]:
        """Comprehensive web search with full content extraction"""
        try:
            # Handle alternative parameter names
            actual_limit = top_n if top_n is not None else limit
            
            # Prepare supported parameters
            search_params = {}
            if recency_days is not None:
                search_params['recency_days'] = recency_days
                logger.info(f"Using recency_days filter: {recency_days} days")
            if source is not None:
                search_params['source'] = source
                logger.info(f"Using source filter: '{source}'")
            if language is not None:
                search_params['language'] = language
                logger.info(f"Using language filter: '{language}'")
            if country is not None:
                search_params['country'] = country
                logger.info(f"Using country filter: '{country}'")
                
            logger.info(f"MCP tool full_web_search: query='{query}', limit={actual_limit}")

            result = await web_search_service.search_and_extract(
                query=query,
                limit=min(actual_limit, 10),  # Cap at 10
                max_content_length=max_content_length,
                include_content=include_content,
                **search_params  # Pass all supported parameters to service
            )

            # Format for MCP response
            response_text = f"Search completed for '{result['query']}' with {result['total_results']} results:\n\n"

            for i, search_result in enumerate(result['results'], 1):
                response_text += f"**{i}. {search_result['title']}**\n"
                response_text += f"URL: {search_result['url']}\n"
                response_text += f"Description: {search_result['description']}\n"

                if search_result.get('full_content'):
                    content = search_result['full_content']
                    if max_content_length and len(content) > max_content_length:
                        content = content[:max_content_length] + f"\n\n[Content truncated at {max_content_length} characters]"
                    response_text += f"\n**Full Content:**\n{content}\n"
                elif search_result.get('content_preview'):
                    response_text += f"\n**Content Preview:**\n{search_result['content_preview']}\n"
                elif search_result.get('fetch_status') == 'error':
                    response_text += f"\n**Content Extraction Failed:** {search_result.get('error', 'Unknown error')}\n"

                response_text += "\n---\n\n"

            logger.info(f"MCP tool full_web_search completed: {result['total_results']} results")

            return {
                "content": [{"type": "text", "text": response_text}]
            }

        except Exception as e:
            logger.error(f"MCP tool full_web_search error: {e}")
            raise

    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions_summaries.md", __file__))
    async def get_web_search_summaries(
        query: str, 
        limit: int = 5,
        top_n: int = None,  # Alternative name for limit (for compatibility)
        recency_days: int = None,  # Days to look back (now supported!)
        source: str = None,  # Source type filter (partially supported)
        language: str = None,  # Language filter (now supported!)
        country: str = None  # Country filter (now supported!)
    ) -> Dict[str, Any]:
        """Lightweight web search returning only summaries"""
        try:
            # Handle alternative parameter names
            actual_limit = top_n if top_n is not None else limit
            
            # Prepare supported parameters
            search_params = {}
            if recency_days is not None:
                search_params['recency_days'] = recency_days
                logger.info(f"Using recency_days filter: {recency_days} days")
            if source is not None:
                search_params['source'] = source
                logger.info(f"Using source filter: '{source}'")
            if language is not None:
                search_params['language'] = language
                logger.info(f"Using language filter: '{language}'")
            if country is not None:
                search_params['country'] = country
                logger.info(f"Using country filter: '{country}'")
                
            logger.info(f"MCP tool get_web_search_summaries: query='{query}', limit={actual_limit}")

            result = await web_search_service.search_summaries(
                query=query,
                limit=min(actual_limit, 10),  # Cap at 10
                **search_params  # Pass all supported parameters to service
            )

            # Format for MCP response
            response_text = f"Search summaries for '{result['query']}' with {result['total_results']} results:\n\n"

            for i, summary in enumerate(result['results'], 1):
                response_text += f"**{i}. {summary['title']}**\n"
                response_text += f"URL: {summary['url']}\n"
                response_text += f"Description: {summary['description']}\n\n---\n\n"

            logger.info(f"MCP tool get_web_search_summaries completed: {result['total_results']} results")

            return {
                "content": [{"type": "text", "text": response_text}]
            }

        except Exception as e:
            logger.error(f"MCP tool get_web_search_summaries error: {e}")
            raise

    @mcp.tool()
    @inject_docstring(lambda: load_instruction("instructions_single_page.md", __file__))
    async def get_single_web_page_content(url: str, max_content_length: int = None) -> Dict[str, Any]:
        """Extract content from a single webpage"""
        try:
            logger.info(f"MCP tool get_single_web_page_content: url='{url}'")

            content = await web_search_service.extract_single_page(
                url=url,
                max_content_length=max_content_length
            )

            word_count = len(content.split())

            response_text = f"**Page Content from: {url}**\n\n{content}\n\n"
            response_text += f"**Word count:** {word_count}\n"

            logger.info(f"MCP tool get_single_web_page_content completed: {word_count} words")

            return {
                "content": [{"type": "text", "text": response_text}]
            }

        except Exception as e:
            logger.error(f"MCP tool get_single_web_page_content error: {e}")
            raise