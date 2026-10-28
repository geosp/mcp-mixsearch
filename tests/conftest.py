"""
Shared test fixtures

Tests run offline: DNS goes through a fake resolver, HTTP through
httpx.MockTransport, and the browser is replaced by FakeBrowser.
"""

from contextlib import asynccontextmanager
from typing import Callable, Dict, List

import httpx
import pytest

from features.web_search.url_safety import URLGuard

PUBLIC_IP = "93.184.215.14"


def make_resolver(hosts: Dict[str, List[str]]) -> Callable:
    """Resolver that maps known hosts to fixed IPs and everything else to a public IP"""
    async def resolve(host: str) -> List[str]:
        return hosts.get(host, [PUBLIC_IP])
    return resolve


@pytest.fixture
def guard() -> URLGuard:
    """URL guard whose resolver maps *.internal hosts to private addresses"""
    return URLGuard(resolver=make_resolver({
        "localhost": ["127.0.0.1", "::1"],
        "intranet.internal": ["10.0.0.5"],
        "metadata.internal": ["169.254.169.254"],
        "mixed.internal": [PUBLIC_IP, "192.168.1.10"],
    }))


def mock_client(handler: Callable[[httpx.Request], httpx.Response], guard: URLGuard) -> httpx.AsyncClient:
    """httpx client wired like the service's, but served by handler"""
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
        event_hooks={"request": [guard.httpx_hook]},
    )


class FakePage:
    """Minimal stand-in for a Playwright page"""

    def __init__(self, html: str = "", evaluate_result=None):
        self.html = html
        self.evaluate_result = evaluate_result
        self.visited: List[str] = []

    async def goto(self, url: str, **kwargs) -> None:
        self.visited.append(url)

    async def wait_for_load_state(self, *args, **kwargs) -> None:
        pass

    async def content(self) -> str:
        return self.html

    async def evaluate(self, script: str):
        return self.evaluate_result


class FakeBrowser:
    """Stand-in for BrowserManager that hands out one FakePage"""

    def __init__(self, page: FakePage = None):
        self.fake_page = page or FakePage()
        self.pages_opened = 0

    @asynccontextmanager
    async def page(self):
        self.pages_opened += 1
        yield self.fake_page

    async def close(self) -> None:
        pass
