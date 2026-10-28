"""
Readable content extraction from web pages

Fetches the page over HTTP and extracts the main content with trafilatura.
If that yields nothing useful (JavaScript-rendered or bot-blocked pages), the
page is rendered in the shared browser and extracted again.
"""

import asyncio
import logging
from typing import Callable, Optional

import httpx
import trafilatura
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .browser import BrowserManager
from .url_safety import UnsafeURLError, URLGuard

logger = logging.getLogger(__name__)

MIN_CONTENT_CHARS = 100
# Bot-check phrases are only looked for on short pages; long articles may mention them
SHORT_PAGE_CHARS = 2000
BOT_PHRASES = (
    "captcha",
    "access denied",
    "verify you are human",
    "are you a robot",
    "403 forbidden",
    "enable javascript",
)
NETWORK_IDLE_TIMEOUT_MS = 5_000


def is_meaningful_content(content: str) -> bool:
    """Whether extracted content looks like a real page rather than an error or bot check"""
    if len(content) < MIN_CONTENT_CHARS:
        return False
    if len(content) < SHORT_PAGE_CHARS:
        content_lower = content.lower()
        return not any(phrase in content_lower for phrase in BOT_PHRASES)
    return True


def html_to_text(html: str, url: Optional[str] = None) -> str:
    """Extract the main content of an HTML page as markdown"""
    text = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )
    return (text or "").strip()


def truncate(content: str, max_length: Optional[int]) -> str:
    """Truncate content to max_length characters, noting the truncation"""
    if max_length and len(content) > max_length:
        return content[:max_length] + f"\n\n[Content truncated at {max_length} characters]"
    return content


class ContentExtractor:
    """Extracts readable content from URLs"""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        browser: BrowserManager,
        guard: URLGuard,
        user_agent: Callable[[], str],
    ):
        self._http = http_client
        self._browser = browser
        self._guard = guard
        self._user_agent = user_agent

    async def extract(self, url: str, max_length: Optional[int] = None) -> str:
        """
        Extract readable content from a URL

        Raises:
            UnsafeURLError: If the URL, or a redirect, is not a public http(s) URL
        """
        await self._guard.check(url)

        try:
            content = await self._extract_with_http(url)
            if is_meaningful_content(content):
                return truncate(content, max_length)
        except UnsafeURLError:
            raise
        except Exception as e:
            logger.debug(f"HTTP extraction failed for {url}: {e}")

        return truncate(await self._extract_with_browser(url), max_length)

    async def _extract_with_http(self, url: str) -> str:
        response = await self._http.get(url, headers={"User-Agent": self._user_agent()})
        response.raise_for_status()
        return await asyncio.to_thread(html_to_text, response.text, str(response.url))

    async def _extract_with_browser(self, url: str) -> str:
        async with self._browser.page() as page:
            await page.goto(url, wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                pass  # Use whatever has rendered so far
            content = await asyncio.to_thread(html_to_text, await page.content(), url)
            if not content:
                content = await page.evaluate("() => document.body ? document.body.innerText : ''")
            return content.strip()
