"""
Web Search Service

Queries the cheap search engines in parallel, fuses their ranked results with
reciprocal rank fusion, falls back to the browser engine when results are
short, and extracts page content.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
from .fusion import fuse_results
from .models import SearchResult
from .url_safety import URLGuard

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS = 15.0
FALLBACK_TIMEOUT_SECONDS = 30.0
PREVIEW_CHARS = 500


class WebSearchService:
    def __init__(
        self,
        config: Optional[WebSearchConfig] = None,
        *,
        guard: Optional[URLGuard] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        browser: Optional[BrowserManager] = None,
        engines: Optional[Sequence[SearchEngine]] = None,
        fallback_engine: Optional[SearchEngine] = None,
    ):
        """
        Args:
            config: Web search configuration (read from the environment if omitted)
            guard, http_client, browser: Overrides, for tests
            engines: Engines queried in parallel, for tests
            fallback_engine: Engine used when results are short, for tests. When
                engines is given and this is omitted, there is no fallback.
        """
        config = config or WebSearchConfig()
        self.max_content_length = config.max_content_length
        self.max_concurrent_requests = config.max_concurrent_requests
        self.engine_timeout = config.engine_timeout_seconds
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
        self.engines: List[SearchEngine]
        self.fallback_engine: Optional[SearchEngine]
        if engines is None:
            self.engines = self._build_engines(config)
            self.fallback_engine = fallback_engine or BraveBrowserEngine(self.browser)
        else:
            self.engines = list(engines)
            self.fallback_engine = fallback_engine

    def _random_user_agent(self) -> str:
        return self._ua.random

    def _build_engines(self, config: WebSearchConfig) -> List[SearchEngine]:
        """The cheap engines, queried in parallel on every search"""
        engines: List[SearchEngine] = []
        if config.brave_api_key:
            engines.append(BraveApiEngine(config.brave_api_key, self.http_client))
        engines += [
            DdgsEngine(config.ddgs_backend),
            DuckDuckGoHtmlEngine(self.http_client, self._random_user_agent),
        ]
        return engines

    async def search_and_extract(
        self,
        query: str,
        filters: SearchFilters,
        include_content: bool = True,
        max_content_length: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Full web search with content extraction"""
        logger.info(f"Starting comprehensive web search for: '{query}' with {filters}")

        results = await self._multi_engine_search(query, filters)

        if include_content:
            await self._extract_content_concurrent(results, max_content_length)

        return {
            "query": query,
            "results": [r.to_dict() for r in results],
            "total_results": len(results),
            "status": "success",
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
                    "timestamp": r.timestamp,
                    "engines": r.engines,
                }
                for r in results
            ],
            "total_results": len(results),
            "status": "success",
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
        Query the cheap engines in parallel and fuse their results; run the
        fallback engine only when fewer than filters.limit results come back
        """
        lists = list(
            await asyncio.gather(
                *[
                    self._run_engine(engine, query, filters, self.engine_timeout)
                    for engine in self.engines
                ]
            )
        )
        merged = fuse_results(lists)

        if len(merged) < filters.limit and self.fallback_engine is not None:
            logger.info(
                f"{len(merged)} of {filters.limit} results; trying {self.fallback_engine.name}"
            )
            lists.append(
                await self._run_engine(
                    self.fallback_engine, query, filters, FALLBACK_TIMEOUT_SECONDS
                )
            )
            merged = fuse_results(lists)

        if not merged:
            logger.warning("All search engines failed or returned nothing")
        return merged[: filters.limit]

    @staticmethod
    async def _run_engine(
        engine: SearchEngine, query: str, filters: SearchFilters, timeout: float
    ) -> Tuple[str, List[SearchResult]]:
        """Run one engine under a timeout; failures are logged and give no results"""
        start = time.monotonic()
        try:
            results = await asyncio.wait_for(engine.search(query, filters), timeout)
        except TimeoutError:
            logger.warning(f"Search engine {engine.name} timed out after {timeout:g}s")
            return engine.name, []
        except Exception as e:
            logger.warning(f"Search engine {engine.name} failed: {e!r}")
            return engine.name, []
        logger.info(
            f"Search engine {engine.name}: {len(results)} results "
            f"in {time.monotonic() - start:.2f}s"
        )
        return engine.name, results

    async def _extract_content_concurrent(
        self, results: List[SearchResult], max_content_length: Optional[int]
    ) -> None:
        """Extract content from multiple URLs concurrently"""
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        max_length = max_content_length or self.max_content_length

        async def extract_with_semaphore(result: SearchResult) -> None:
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
