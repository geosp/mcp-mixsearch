"""
Web Search Service

Runs the search engines in order of preference and extracts page content.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

import httpx
from fake_useragent import UserAgent

from config import WebSearchConfig

from .browser import BrowserManager
from .engines import (
    BraveApiEngine,
    BraveBrowserEngine,
    DdgsEngine,
    DuckDuckGoHtmlEngine,
    SearchEngine,
)
from .extraction import ContentExtractor
from .filters import SearchFilters
from .models import SearchResult
from .url_safety import URLGuard

logger = logging.getLogger(__name__)

QUALITY_THRESHOLD = 0.3
HTTP_TIMEOUT_SECONDS = 15.0
PREVIEW_CHARS = 500


def assess_result_quality(results: List[SearchResult], query: str) -> float:
    """Average share of query words found in each result's title or description (0.0 to 1.0)"""
    query_words = set(query.lower().split())
    if not results or not query_words:
        return 0.0

    total_score = 0.0
    for result in results:
        result_words = set(result.title.lower().split()) | set(result.description.lower().split())
        total_score += len(query_words & result_words) / len(query_words)

    return min(total_score / len(results), 1.0)


class WebSearchService:
    def __init__(
        self,
        config: Optional[WebSearchConfig] = None,
        *,
        guard: Optional[URLGuard] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        browser: Optional[BrowserManager] = None,
        engines: Optional[Sequence[SearchEngine]] = None,
    ):
        """
        Args:
            config: Web search configuration (read from the environment if omitted)
            guard, http_client, browser, engines: Overrides, for tests
        """
        config = config or WebSearchConfig()
        self.max_content_length = config.max_content_length
        self.max_concurrent_requests = config.max_concurrent_requests
        self._ua = UserAgent()

        self.guard = guard or URLGuard(allow_private=config.allow_private_urls)
        self.http_client = http_client or httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
            event_hooks={"request": [self.guard.httpx_hook]},
        )
        self.browser = browser or BrowserManager(self.guard, self._random_user_agent)
        self.extractor = ContentExtractor(
            self.http_client, self.browser, self.guard, self._random_user_agent
        )
        self.engines: List[SearchEngine] = (
            list(engines) if engines is not None else self._build_engines(config)
        )

    def _random_user_agent(self) -> str:
        return self._ua.random

    def _build_engines(self, config: WebSearchConfig) -> List[SearchEngine]:
        engines: List[SearchEngine] = []
        if config.brave_api_key:
            engines.append(BraveApiEngine(config.brave_api_key, self.http_client))
        engines += [
            DdgsEngine(config.ddgs_backend),
            BraveBrowserEngine(self.browser),
            DuckDuckGoHtmlEngine(self.http_client, self._random_user_agent),
        ]
        return engines

    async def search_and_extract(self, query: str, filters: SearchFilters,
                                 include_content: bool = True,
                                 max_content_length: Optional[int] = None) -> Dict[str, Any]:
        """Full web search with content extraction"""
        logger.info(f"Starting comprehensive web search for: '{query}' with {filters}")

        results = await self._multi_engine_search(query, filters)

        if include_content:
            await self._extract_content_concurrent(results, max_content_length)

        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "total_results": len(results),
            "status": "success"
        }

    async def search_summaries(self, query: str, filters: SearchFilters) -> Dict[str, Any]:
        """Lightweight search returning only summaries"""
        logger.info(f"Starting multi-engine search for summaries: '{query}' with {filters}")

        results = await self._multi_engine_search(query, filters)

        return {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "description": r.description,
                    "timestamp": r.timestamp
                } for r in results
            ],
            "total_results": len(results),
            "status": "success"
        }

    async def extract_single_page(self, url: str, max_content_length: Optional[int] = None) -> str:
        """
        Extract content from a single webpage

        Raises:
            UnsafeURLError: If the URL is not a public http(s) URL
        """
        logger.info(f"Extracting content from: {url}")
        return await self.extractor.extract(url, max_content_length or self.max_content_length)

    async def aclose(self) -> None:
        """Close the HTTP client and the browser"""
        await self.http_client.aclose()
        await self.browser.close()

    async def _multi_engine_search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        """
        Try each engine in order and return the first result set that passes the
        quality threshold, or else the best non-empty one
        """
        best_results: List[SearchResult] = []
        best_score = -1.0
        best_engine = None

        for engine in self.engines:
            try:
                logger.info(f"Trying {engine.name} search engine")
                results = await engine.search(query, filters)
            except Exception as e:
                logger.warning(f"Search engine {engine.name} failed: {e}")
                continue

            if not results:
                continue

            score = assess_result_quality(results, query)
            if score >= QUALITY_THRESHOLD:
                logger.info(f"Using results from {engine.name}: {len(results)} results")
                return results[:filters.limit]
            if score > best_score:
                best_results, best_score, best_engine = results, score, engine.name

        if best_results:
            logger.info(f"No engine met the quality threshold; using {best_engine} (score {best_score:.2f})")
            return best_results[:filters.limit]

        logger.warning("All search engines failed, returning empty results")
        return []

    async def _extract_content_concurrent(self, results: List[SearchResult],
                                          max_content_length: Optional[int]) -> None:
        """Extract content from multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        max_length = max_content_length or self.max_content_length

        async def extract_with_semaphore(result: SearchResult):
            async with semaphore:
                try:
                    content = await self.extractor.extract(result.url, max_length)
                    result.full_content = content
                    result.content_preview = (
                        content[:PREVIEW_CHARS] + "..." if len(content) > PREVIEW_CHARS else content
                    )
                    result.word_count = len(content.split())
                    result.fetch_status = "success"
                except Exception as e:
                    result.fetch_status = "error"
                    result.error = str(e)
                    logger.warning(f"Content extraction failed for {result.url}: {e}")

        await asyncio.gather(*[extract_with_semaphore(r) for r in results])
