"""
Live tests against real search engines and websites

Skipped by default; run with: uv run pytest -m live
"""

import os

import pytest

from config import WebSearchConfig
from features.web_search.engines import BraveApiEngine
from features.web_search.filters import SearchFilters
from features.web_search.service import WebSearchService

pytestmark = pytest.mark.live


@pytest.fixture
async def service():
    service = WebSearchService(WebSearchConfig())
    yield service
    await service.aclose()


async def test_search_summaries(service):
    summaries = await service.search_summaries("python programming language", SearchFilters(limit=3))
    assert summaries["total_results"] > 0
    assert all(r["url"].startswith("http") for r in summaries["results"])


async def test_extract_single_page(service):
    content = await service.extract_single_page("https://example.com/")
    assert "Example Domain" in content or "documentation examples" in content


async def test_unsafe_url_is_blocked(service):
    with pytest.raises(ValueError):
        await service.extract_single_page("file:///etc/os-release")


@pytest.mark.skipif(not os.getenv("BRAVE_API_KEY"), reason="BRAVE_API_KEY not set")
async def test_brave_api(service):
    engine = BraveApiEngine(os.environ["BRAVE_API_KEY"], service.http_client)
    results = await engine.search("model context protocol", SearchFilters(limit=3))
    assert results and all(r.url.startswith("http") for r in results)
