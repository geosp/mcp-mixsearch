"""
REST API routes for web_search feature
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from core.utils import load_instruction
from features.web_search.service import WebSearchService
from features.web_search.models import SearchResultModel, SearchSummaryModel

logger = logging.getLogger(__name__)


def create_router(web_search_service: WebSearchService) -> APIRouter:
    """
    Create router for web search REST endpoints

    Args:
        web_search_service: Web search service instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/search", tags=["Web Search"])

    @router.get(
        "/full_web_search",
        response_model=list[SearchResultModel],
        summary="Full Web Search",
        description=load_instruction("instructions.md", __file__)
    )
    async def full_web_search(
        query: str = Query(..., description="Search query"),
        limit: int = Query(10, description="Maximum number of results", ge=1, le=20),
        include_content: bool = Query(True, description="Include full page content"),
        max_content_length: int = Query(500000, description="Maximum content length per page", ge=0, le=2000000),
        # Standard compatibility parameters - now supported!
        top_n: Optional[int] = Query(None, description="Alternative name for limit (for compatibility)", ge=1, le=20),
        recency_days: Optional[int] = Query(None, description="Days to look back (now supported!)"),
        source: Optional[str] = Query(None, description="Source type filter (partially supported)"),
        language: Optional[str] = Query(None, description="Language filter (now supported!)"),
        country: Optional[str] = Query(None, description="Country filter (now supported!)")
    ):
        """
        Perform a full web search with content extraction

        Returns search results with titles, URLs, descriptions, and optionally full content.
        Accepts standard web search API parameters for compatibility.
        """
        try:
            # Handle alternative parameter names
            actual_limit = top_n if top_n is not None else limit
            
            # Prepare supported parameters
            search_params = {}
            if recency_days is not None:
                search_params['recency_days'] = recency_days
                logger.info(f"REST API: Using recency_days filter: {recency_days} days")
            if source is not None:
                search_params['source'] = source
                logger.info(f"REST API: Using source filter: '{source}'")
            if language is not None:
                search_params['language'] = language
                logger.info(f"REST API: Using language filter: '{language}'")
            if country is not None:
                search_params['country'] = country
                logger.info(f"REST API: Using country filter: '{country}'")
                
            logger.info(f"REST API full search: query='{query}', limit={actual_limit}")

            results = await web_search_service.search_and_extract(
                query=query,
                limit=actual_limit,
                include_content=include_content,
                max_content_length=max_content_length,
                **search_params  # Pass all supported parameters to service
            )
            return results["results"]
        except Exception as e:
            logger.error(f"Full search error: {e}")
            raise HTTPException(status_code=500, detail="Search failed")

    @router.get(
        "/get_web_search_summaries",
        response_model=list[SearchSummaryModel],
        summary="Search Summaries",
        description=load_instruction("instructions_summaries.md", __file__)
    )
    async def get_web_search_summaries(
        query: str = Query(..., description="Search query"),
        limit: int = Query(10, description="Maximum number of results", ge=1, le=20),
        # Standard compatibility parameters - now supported!
        top_n: Optional[int] = Query(None, description="Alternative name for limit (for compatibility)", ge=1, le=20),
        recency_days: Optional[int] = Query(None, description="Days to look back (now supported!)"),
        source: Optional[str] = Query(None, description="Source type filter (partially supported)"),
        language: Optional[str] = Query(None, description="Language filter (now supported!)"),
        country: Optional[str] = Query(None, description="Country filter (now supported!)")
    ):
        """
        Perform a lightweight search returning only titles, URLs, and descriptions.
        Accepts standard web search API parameters for compatibility.
        """
        try:
            # Handle alternative parameter names
            actual_limit = top_n if top_n is not None else limit
            
            # Prepare supported parameters
            search_params = {}
            if recency_days is not None:
                search_params['recency_days'] = recency_days
                logger.info(f"REST API: Using recency_days filter: {recency_days} days")
            if source is not None:
                search_params['source'] = source
                logger.info(f"REST API: Using source filter: '{source}'")
            if language is not None:
                search_params['language'] = language
                logger.info(f"REST API: Using language filter: '{language}'")
            if country is not None:
                search_params['country'] = country
                logger.info(f"REST API: Using country filter: '{country}'")
                
            logger.info(f"REST API summaries search: query='{query}', limit={actual_limit}")

            results = await web_search_service.search_summaries(
                query=query,
                limit=actual_limit,
                **search_params  # Pass all supported parameters to service
            )
            return results["results"]
        except Exception as e:
            logger.error(f"Summary search error: {e}")
            raise HTTPException(status_code=500, detail="Search failed")

    @router.get(
        "/get_single_web_page_content",
        summary="Extract Page Content",
        description=load_instruction("instructions_single_page.md", __file__)
    )
    async def get_single_web_page_content(
        url: str = Query(..., description="URL to extract content from"),
        max_content_length: int = Query(500000, description="Maximum content length", ge=0, le=2000000)
    ):
        """
        Extract readable content from a specific web page.
        """
        try:
            result = await web_search_service.extract_single_page(
                url=url,
                max_content_length=max_content_length
            )
            return result
        except Exception as e:
            logger.error(f"Page extraction error: {e}")
            raise HTTPException(status_code=500, detail="Content extraction failed")

    return router