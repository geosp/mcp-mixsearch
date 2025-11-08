"""
Models for the web search feature
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchResultModel(BaseModel):
    """Individual search result"""
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    description: str = Field(..., description="Search result description")
    full_content: Optional[str] = Field(None, description="Full extracted content")
    content_preview: Optional[str] = Field(None, description="Content preview")
    word_count: Optional[int] = Field(None, description="Word count of content")
    timestamp: Optional[str] = Field(None, description="Timestamp")
    fetch_status: str = Field(default="success", description="Content extraction status")
    error: Optional[str] = Field(None, description="Error message if extraction failed")


class WebSearchRequest(BaseModel):
    """Request model for web search"""
    query: str = Field(..., min_length=1, max_length=200,
                      description="Search query")
    limit: Optional[int] = Field(default=5, ge=1, le=10,
                                description="Number of results (1-10)")
    include_content: Optional[bool] = Field(default=True,
                                          description="Whether to extract full content")
    max_content_length: Optional[int] = Field(default=None, ge=0,
                                            description="Maximum content length per result")


class WebSearchResponse(BaseModel):
    """Response model for web search"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResultModel] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    status: str = Field(..., description="Search status")


class SearchSummaryModel(BaseModel):
    """Search result summary (no content)"""
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Page URL")
    description: str = Field(..., description="Search result description")
    timestamp: Optional[str] = Field(None, description="Timestamp")


class SearchSummariesRequest(BaseModel):
    """Request model for search summaries"""
    query: str = Field(..., min_length=1, max_length=200,
                      description="Search query")
    limit: Optional[int] = Field(default=5, ge=1, le=10,
                                description="Number of results (1-10)")


class SearchSummariesResponse(BaseModel):
    """Response model for search summaries"""
    query: str = Field(..., description="Original search query")
    results: List[SearchSummaryModel] = Field(..., description="Search result summaries")
    total_results: int = Field(..., description="Total number of results")
    status: str = Field(..., description="Search status")


class SinglePageRequest(BaseModel):
    """Request model for single page content extraction"""
    url: str = Field(..., description="URL to extract content from")
    max_content_length: Optional[int] = Field(default=None, ge=0,
                                            description="Maximum content length")


class SinglePageResponse(BaseModel):
    """Response model for single page content"""
    url: str = Field(..., description="Original URL")
    content: str = Field(..., description="Extracted content")
    word_count: int = Field(..., description="Word count")
    timestamp: str = Field(..., description="Extraction timestamp")
    fetch_status: str = Field(..., description="Extraction status")
    error: Optional[str] = Field(None, description="Error message if extraction failed")