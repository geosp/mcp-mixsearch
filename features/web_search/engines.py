"""
Search engines

Each engine turns a query and SearchFilters into SearchResults. The service
tries them in order: Brave Search API (when a key is configured), the ddgs
metasearch library, then scraping search.brave.com and DuckDuckGo HTML.
"""

import asyncio
import html
import logging
import re
from typing import Any, Callable, Dict, List, Protocol
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .browser import BrowserManager
from .filters import SearchFilters
from .models import SearchResult, utc_now_iso

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(text: str) -> str:
    """Remove HTML tags and unescape entities"""
    return html.unescape(_TAG_RE.sub("", text or "")).strip()


class SearchEngine(Protocol):
    """A search backend"""
    name: str

    async def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        ...


class BraveApiEngine:
    """Official Brave Search API (https://api.search.brave.com)"""
    name = "BraveAPI"
    WEB_URL = "https://api.search.brave.com/res/v1/web/search"
    NEWS_URL = "https://api.search.brave.com/res/v1/news/search"

    def __init__(self, api_key: str, http_client: httpx.AsyncClient):
        self._api_key = api_key
        self._http = http_client

    async def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        if filters.source not in ("web", "news"):
            return []  # Images and videos are left to the next engine

        is_news = filters.source == "news"
        response = await self._http.get(
            self.NEWS_URL if is_news else self.WEB_URL,
            params={"q": query, **filters.brave_api_params()},
            headers={"Accept": "application/json", "X-Subscription-Token": self._api_key},
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("results", []) if is_news else data.get("web", {}).get("results", [])
        return [
            SearchResult(
                title=strip_tags(item.get("title", "")),
                url=item.get("url", ""),
                description=strip_tags(item.get("description", "")),
                timestamp=item.get("age") or utc_now_iso(),
            )
            for item in items[: filters.limit]
        ]


def convert_ddgs_result(item: Dict[str, Any], method: str) -> SearchResult:
    """Convert a ddgs result dict to a SearchResult; the fields differ per method"""
    title = item.get("title", "")
    if method == "news":
        return SearchResult(
            title=title,
            url=item.get("url", ""),
            description=item.get("body", ""),
            timestamp=item.get("date") or utc_now_iso(),
        )
    if method == "images":
        description = " | ".join(part for part in (item.get("source"), item.get("image")) if part)
        return SearchResult(title=title, url=item.get("url", ""), description=description)
    if method == "videos":
        return SearchResult(title=title, url=item.get("content", ""), description=item.get("description", ""))
    return SearchResult(title=title, url=item.get("href", ""), description=item.get("body", ""))


class DdgsEngine:
    """ddgs metasearch library"""
    name = "DDGS"

    def __init__(self, backend: str = "auto", ddgs_factory: Callable[[], Any] = DDGS):
        """
        Args:
            backend: ddgs backend(s), e.g. "auto" or "duckduckgo,bing"
            ddgs_factory: Creates the DDGS client, for tests
        """
        self._backend = backend
        self._ddgs_factory = ddgs_factory

    async def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        method = "text" if filters.source == "web" else filters.source
        kwargs = filters.ddgs_kwargs(self._backend)
        logger.info(f"DDGS {method} search: {kwargs}")

        def run() -> List[Dict[str, Any]]:
            return list(getattr(self._ddgs_factory(), method)(query, **kwargs))

        raw_results = await asyncio.to_thread(run)
        return [convert_ddgs_result(item, method) for item in raw_results]


def is_brave_url(url: str) -> bool:
    """Whether a URL points back at Brave itself (e.g. its AI answer links)"""
    host = (urlsplit(url).hostname or "").lower()
    return host == "brave.com" or host.endswith(".brave.com")


class BraveBrowserEngine:
    """Scrapes search.brave.com in the shared browser"""
    name = "Brave"
    SEARCH_URL = "https://search.brave.com/search"
    EXTRACT_JS = """
        () => {
            const results = [];
            document.querySelectorAll('.snippet').forEach(el => {
                const titleEl = el.querySelector('a');
                const descEl = el.querySelector('.snippet-description, .snippet-content');
                if (titleEl && descEl) {
                    results.push({
                        title: titleEl.textContent.trim(),
                        url: titleEl.href,
                        description: descEl.textContent.trim()
                    });
                }
            });
            return results;
        }
    """

    def __init__(self, browser: BrowserManager):
        self._browser = browser

    async def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        url = f"{self.SEARCH_URL}?{urlencode({'q': query, 'spellcheck': '1', **filters.brave_web_params()})}"
        logger.info(f"Browser-based Brave search URL: {url}")

        async with self._browser.page() as page:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=5_000)
            except PlaywrightTimeoutError:
                pass
            results_data = await page.evaluate(self.EXTRACT_JS)

        results = [
            SearchResult(title=r["title"], url=r["url"], description=r["description"])
            for r in results_data
            if not is_brave_url(r["url"])
        ]
        return results[: filters.limit]


def unwrap_ddg_redirect(href: str) -> str:
    """Return the target of a DuckDuckGo //duckduckgo.com/l/?uddg=... redirect link"""
    parts = urlsplit(href)
    if parts.path.startswith("/l/"):
        target = parse_qs(parts.query).get("uddg")
        if target:
            return target[0]
    return href


def parse_ddg_html(page: str, limit: int) -> List[SearchResult]:
    """Parse results from a DuckDuckGo HTML results page"""
    soup = BeautifulSoup(page, "lxml")
    results = []
    for result in soup.select(".result"):
        title_el = result.select_one(".result__title a")
        snippet_el = result.select_one(".result__snippet")
        if title_el and snippet_el and title_el.get("href"):
            results.append(SearchResult(
                title=title_el.get_text().strip(),
                url=unwrap_ddg_redirect(title_el["href"]),
                description=snippet_el.get_text().strip(),
            ))
        if len(results) >= limit:
            break
    return results


class DuckDuckGoHtmlEngine:
    """Scrapes the DuckDuckGo HTML results page"""
    name = "DuckDuckGo"
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, http_client: httpx.AsyncClient, user_agent: Callable[[], str]):
        self._http = http_client
        self._user_agent = user_agent

    async def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        response = await self._http.get(
            self.SEARCH_URL,
            params={"q": query, **filters.ddg_html_params()},
            headers={"User-Agent": self._user_agent()},
        )
        response.raise_for_status()
        return parse_ddg_html(response.text, filters.limit)
