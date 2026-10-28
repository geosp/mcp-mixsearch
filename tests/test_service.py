from typing import List

import httpx
import pytest

from config import WebSearchConfig
from features.web_search.engines import BraveApiEngine, DdgsEngine
from features.web_search.filters import SearchFilters
from features.web_search.models import SearchResult
from features.web_search.service import WebSearchService, assess_result_quality

from .conftest import FakeBrowser, mock_client


class FakeEngine:
    def __init__(self, name, results: List[SearchResult] = None, error: Exception = None):
        self.name = name
        self._results = results or []
        self._error = error
        self.calls = 0

    async def search(self, query, filters):
        self.calls += 1
        if self._error:
            raise self._error
        return list(self._results)


def result(title, url="https://example.com/", description=""):
    return SearchResult(title=title, url=url, description=description)


def make_service(guard, engines, handler=None, browser=None):
    client = mock_client(handler or (lambda request: httpx.Response(404)), guard)
    return WebSearchService(
        WebSearchConfig(brave_api_key=None),
        guard=guard, http_client=client, browser=browser or FakeBrowser(), engines=engines,
    )


def test_assess_result_quality():
    assert assess_result_quality([], "query") == 0.0
    assert assess_result_quality([result("x")], "   ") == 0.0
    assert assess_result_quality([result("python release")], "python release") == 1.0
    assert assess_result_quality([result("python"), result("other")], "python release") == 0.25


async def test_first_good_engine_wins(guard):
    first = FakeEngine("first", [result("python release notes")])
    second = FakeEngine("second", [result("python release")])
    service = make_service(guard, [first, second])

    summaries = await service.search_summaries("python release", SearchFilters())

    assert summaries["results"][0]["title"] == "python release notes"
    assert second.calls == 0


async def test_failing_and_empty_engines_are_skipped(guard):
    engines = [
        FakeEngine("broken", error=RuntimeError("boom")),
        FakeEngine("empty"),
        FakeEngine("good", [result("python release")]),
    ]
    summaries = await make_service(guard, engines).search_summaries("python release", SearchFilters())
    assert summaries["total_results"] == 1


async def test_best_effort_results_when_no_engine_meets_threshold(guard):
    engines = [
        FakeEngine("weak", [result("unrelated")]),
        FakeEngine("less weak", [result("python snakes"), result("zoo")]),
    ]
    summaries = await make_service(guard, engines).search_summaries("python release notes", SearchFilters())
    assert [r["title"] for r in summaries["results"]] == ["python snakes", "zoo"]


async def test_no_results_when_every_engine_fails(guard):
    engines = [FakeEngine("a", error=RuntimeError("x")), FakeEngine("b")]
    summaries = await make_service(guard, engines).search_summaries("query", SearchFilters())
    assert summaries == {"query": "query", "results": [], "total_results": 0, "status": "success"}


async def test_results_are_limited(guard):
    engine = FakeEngine("many", [result(f"python {i}") for i in range(8)])
    summaries = await make_service(guard, [engine]).search_summaries("python", SearchFilters(limit=3))
    assert summaries["total_results"] == 3


async def test_search_and_extract_marks_blocked_urls_as_errors(guard):
    article = "<html><body><article><p>" + "Readable python content. " * 30 + "</p></article></body></html>"
    engine = FakeEngine("engine", [
        result("python good", url="https://example.com/good"),
        result("python internal", url="http://intranet.internal/admin"),
    ])
    service = make_service(guard, [engine], handler=lambda request: httpx.Response(200, text=article))

    response = await service.search_and_extract("python", SearchFilters())

    good, blocked = response["results"]
    assert good["fetch_status"] == "success" and "Readable python content" in good["full_content"]
    assert good["word_count"] > 0
    assert blocked["fetch_status"] == "error" and "not a public address" in blocked["error"]
    assert blocked["full_content"] == ""


async def test_extract_single_page_applies_configured_max_length(guard):
    article = "<html><body><article><p>" + "Readable content here. " * 100 + "</p></article></body></html>"
    service = make_service(guard, [], handler=lambda request: httpx.Response(200, text=article))
    service.max_content_length = 100

    content = await service.extract_single_page("https://example.com/")

    assert content.endswith("[Content truncated at 100 characters]")


def test_engine_order_depends_on_brave_api_key(guard):
    client = mock_client(lambda request: httpx.Response(404), guard)
    without_key = WebSearchService(WebSearchConfig(brave_api_key=None), guard=guard, http_client=client)
    with_key = WebSearchService(WebSearchConfig(brave_api_key="key", ddgs_backend="bing"),
                                guard=guard, http_client=client)

    assert [e.name for e in without_key.engines] == ["DDGS", "Brave", "DuckDuckGo"]
    assert [e.name for e in with_key.engines] == ["BraveAPI", "DDGS", "Brave", "DuckDuckGo"]
    assert isinstance(with_key.engines[0], BraveApiEngine)
    assert isinstance(with_key.engines[1], DdgsEngine) and with_key.engines[1]._backend == "bing"


@pytest.mark.parametrize("env, expected", [({}, False), ({"ALLOW_PRIVATE_URLS": "true"}, True)])
def test_allow_private_urls_from_environment(monkeypatch, env, expected):
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert WebSearchService().guard.allow_private is expected
