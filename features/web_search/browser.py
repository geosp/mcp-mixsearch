"""
Shared headless Firefox for search scraping and content extraction

One browser is launched lazily per process and reused; each page gets its
own browser context, so concurrent calls don't share cookies or state.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, Optional

from playwright.async_api import Browser, Page, Playwright, async_playwright

from .url_safety import URLGuard

logger = logging.getLogger(__name__)

NAVIGATION_TIMEOUT_MS = 15_000
VIEWPORT = {"width": 1920, "height": 1080}


class BrowserManager:
    """Lazily launches and reuses a single headless Firefox"""

    def __init__(self, guard: URLGuard, user_agent: Callable[[], str]):
        """
        Args:
            guard: URL guard applied to every request the browser makes
            user_agent: Returns the user agent for a new page
        """
        self._guard = guard
        self._user_agent = user_agent
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()

    async def _get_browser(self) -> Browser:
        async with self._lock:
            if self._browser is None or not self._browser.is_connected():
                if self._playwright is None:
                    self._playwright = await async_playwright().start()
                logger.info("Launching headless Firefox")
                self._browser = await self._playwright.firefox.launch(headless=True)
            return self._browser

    @asynccontextmanager
    async def page(self) -> AsyncIterator[Page]:
        """Open a page in a fresh browser context, closed on exit"""
        browser = await self._get_browser()
        context = await browser.new_context(user_agent=self._user_agent(), viewport=VIEWPORT)
        try:
            context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
            await context.route("**/*", self._guard.route_handler)
            yield await context.new_page()
        finally:
            await context.close()

    async def close(self) -> None:
        """Close the browser and stop Playwright"""
        async with self._lock:
            if self._browser is not None:
                await self._browser.close()
                self._browser = None
            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None
