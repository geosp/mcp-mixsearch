import asyncio
import itertools
import logging
from typing import List

import httpx
import pytest

from config import WebSearchConfig
from features.web_search import service as service_module
from features.web_search.engines import BraveApiEngine, DdgsEngine
from features.web_search.filters import SearchFilters
from features.web_search.models import SearchResult
from features.web_search.service import WebSearchService

from .conftest import FakeBrowser, mock_client

_urls = itertools.count()


class FakeEngine:
    def __init__(
        self,
        name,
        results: List[SearchResult] = None,
        error: Exception = None,
        delay: float = 0.0,
    ):
        self.name = name
        self._results = results or []
        self._error = error
        self._delay = delay
        self.calls = 0
        self.filters_seen = []

    async def search(self, query, filters):
        self.calls += 1
        self.filters_seen.append(filters)
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error:
            raise self._error
        return list(self._results)


def result(title, url=None, description=""):
    """A search result; each gets its own URL unless one is given"""
    return SearchResult(
        title=title, url=url or f"https://example.com/{next(_urls)}", description=description
    )


def make_service(guard, engines, handler=None, browser=None, config=None, fallback_engine=None):
    client = mock_client(handler or (lambda request: httpx.Response(404)), guard)
    return WebSearchService(
        config or WebSearchConfig(brave_api_key=None),
        guard=guard,
        http_client=client,
        browser=browser or FakeBrowser(),
        engines=engines,
        fallback_engine=fallback_engine,
    )


async def test_overlapping_results_are_fused_by_rrf_without_duplicates(guard):
    shared = "https://shared.example/page"
    first = FakeEngine(
        "first",
        [result("only first"), result("shared", url=shared)],
    )
    second = FakeEngine(
        "second",
        [result("only second"), result("shared again", url="https://www.shared.example/page/")],
    )
    summaries = await make_service(guard, [first, second]).search_summaries(
        "query", SearchFilters(limit=5)
    )

    urls = [r["url"] for r in summaries["results"]]
    assert urls[0] == shared
    assert summaries["results"][0]["engines"] == ["first", "second"]
    assert summaries["results"][0]["title"] == "shared"
    assert [r["title"] for r in summaries["results"][1:]] == ["only first", "only second"]
    assert summaries["total_results"] == 3


async def test_failing_and_slow_engines_are_logged_and_skipped(guard, caplog):
    engines = [
        FakeEngine("broken", error=RuntimeError("boom")),
        FakeEngine("slow", [result("too late")], delay=1.0),
        FakeEngine("empty"),
        FakeEngine("good", [result("python release")]),
    ]
    config = WebSearchConfig(brave_api_key=None, engine_timeout_seconds=0.05)
    caplog.set_level(logging.INFO)
    loop = asyncio.get_running_loop()
    start = loop.time()

    summaries = await make_service(guard, engines, config=config).search_summaries(
        "python release", SearchFilters()
    )

    assert loop.time() - start < 0.5

    assert [r["title"] for r in summaries["results"]] == ["python release"]
    assert summaries["results"][0]["engines"] == ["good"]
    messages = caplog.text
    assert "broken failed" in messages and "boom" in messages
    assert "slow timed out" in messages
    assert "Search engine good: 1 results in" in messages


async def test_engines_run_concurrently(guard):
    engines = [FakeEngine(f"e{i}", [result(f"r{i}")], delay=0.2) for i in range(3)]
    loop = asyncio.get_running_loop()
    start = loop.time()
    summaries = await make_service(guard, engines).search_summaries("q", SearchFilters(limit=3))
    assert loop.time() - start < 0.5
    assert summaries["total_results"] == 3


async def test_no_results_when_every_engine_fails(guard):
    engines = [FakeEngine("a", error=RuntimeError("x")), FakeEngine("b")]
    summaries = await make_service(guard, engines).search_summaries("query", SearchFilters())
    assert summaries == {"query": "query", "results": [], "total_results": 0, "status": "success"}


async def test_results_are_limited(guard):
    engine = FakeEngine("many", [result(f"python {i}") for i in range(8)])
    summaries = await make_service(guard, [engine]).search_summaries(
        "python", SearchFilters(limit=3)
    )
    assert summaries["total_results"] == 3


async def test_fallback_not_used_when_results_reach_limit(guard):
    fallback = FakeEngine("Brave", [result("from browser")])
    engine = FakeEngine("cheap", [result(f"r{i}") for i in range(3)])
    summaries = await make_service(guard, [engine], fallback_engine=fallback).search_summaries(
        "q", SearchFilters(limit=3)
    )
    assert fallback.calls == 0
    assert summaries["total_results"] == 3


async def test_fallback_fills_short_results(guard):
    shared = "https://shared.example/"
    fallback = FakeEngine("Brave", [result("shared", url=shared), result("browser only")])
    engine = FakeEngine("cheap", [result("shared", url=shared)])
    summaries = await make_service(guard, [engine], fallback_engine=fallback).search_summaries(
        "q", SearchFilters(limit=5)
    )
    assert fallback.calls == 1
    assert [r["engines"] for r in summaries["results"]] == [["cheap", "Brave"], ["Brave"]]


async def test_failing_fallback_keeps_cheap_results(guard, caplog):
    fallback = FakeEngine("Brave", error=RuntimeError("no browser"))
    engine = FakeEngine("cheap", [result("a"), result("b")])
    caplog.set_level(logging.WARNING)
    summaries = await make_service(guard, [engine], fallback_engine=fallback).search_summaries(
        "q", SearchFilters(limit=5)
    )
    assert summaries["total_results"] == 2
    assert "Brave failed" in caplog.text


async def test_slow_fallback_times_out(guard, caplog, monkeypatch):
    monkeypatch.setattr(service_module, "FALLBACK_TIMEOUT_SECONDS", 0.05)
    fallback = FakeEngine("Brave", [result("late")], delay=1.0)
    engine = FakeEngine("cheap", [result("a"), result("b")])
    caplog.set_level(logging.WARNING)
    summaries = await make_service(guard, [engine], fallback_engine=fallback).search_summaries(
        "q", SearchFilters(limit=5)
    )
    assert [r["title"] for r in summaries["results"]] == ["a", "b"]
    assert "Brave timed out" in caplog.text


async def test_every_engine_gets_the_same_filters(guard):
    filters = SearchFilters.from_tool_args(limit=3, recency_days=7, language="fr", country="ca")
    engines = [FakeEngine("a"), FakeEngine("b")]
    fallback = FakeEngine("Brave")
    await make_service(guard, engines, fallback_engine=fallback).search_summaries("q", filters)
    assert [e.filters_seen for e in [*engines, fallback]] == [[filters]] * 3


async def test_search_and_extract_results_include_engines(guard):
    engine = FakeEngine("cheap", [result("a", url="http://intranet.internal/x")])
    response = await make_service(guard, [engine]).search_and_extract("q", SearchFilters(limit=1))
    assert response["results"][0]["engines"] == ["cheap"]


async def test_search_and_extract_marks_blocked_urls_as_errors(guard):
    article = (
        "<html><body><article><p>"
        + "Readable python content. " * 30
        + "</p></article></body></html>"
    )
    engine = FakeEngine(
        "engine",
        [
            result("python good", url="https://example.com/good"),
            result("python internal", url="http://intranet.internal/admin"),
        ],
    )
    service = make_service(
        guard, [engine], handler=lambda request: httpx.Response(200, text=article)
    )

    response = await service.search_and_extract("python", SearchFilters())

    good, blocked = response["results"]
    assert good["fetch_status"] == "success" and "Readable python content" in good["full_content"]
    assert good["word_count"] > 0
    assert blocked["fetch_status"] == "error" and "not a public address" in blocked["error"]
    assert blocked["full_content"] == ""


async def test_extract_single_page_applies_configured_max_length(guard):
    article = (
        "<html><body><article><p>"
        + "Readable content here. " * 100
        + "</p></article></body></html>"
    )
    service = make_service(guard, [], handler=lambda request: httpx.Response(200, text=article))
    service.max_content_length = 100

    content = await service.extract_single_page("https://example.com/")

    assert content.endswith("[Content truncated at 100 characters]")


async def test_engine_with_missing_url_does_not_sink_search(guard):
    bad = FakeEngine("bad", [SearchResult(title="no url", url=None, description="")])
    good = FakeEngine("good", [result("kept")])
    summaries = await make_service(guard, [bad, good]).search_summaries("q", SearchFilters())
    assert [r["title"] for r in summaries["results"]] == ["kept"]


async def test_fallback_skipped_for_non_web_sources(guard):
    fallback = FakeEngine("Brave", [result("browser")])
    engine = FakeEngine("cheap", [result("one news story")])
    summaries = await make_service(guard, [engine], fallback_engine=fallback).search_summaries(
        "q", SearchFilters(source="news")
    )
    assert fallback.calls == 0
    assert summaries["total_results"] == 1


async def test_engines_listed_in_configured_order_not_response_order(guard):
    shared = "https://shared.example/"
    slow_first = FakeEngine("BraveAPI", [result("a", url=shared)], delay=0.1)
    fast_second = FakeEngine("DDGS", [result("b", url=shared)])
    summaries = await make_service(guard, [slow_first, fast_second]).search_summaries(
        "q", SearchFilters()
    )
    assert summaries["results"][0]["engines"] == ["BraveAPI", "DDGS"]


async def test_three_engines_cut_to_limit(guard):
    engines = [FakeEngine(f"e{i}", [result(f"e{i} r{j}") for j in range(5)]) for i in range(3)]
    summaries = await make_service(guard, engines).search_summaries("q", SearchFilters(limit=5))
    assert summaries["total_results"] == 5
    assert len({r["url"] for r in summaries["results"]}) == 5


def test_engine_order_depends_on_brave_api_key(guard):
    client = mock_client(lambda request: httpx.Response(404), guard)
    without_key = WebSearchService(
        WebSearchConfig(brave_api_key=None), guard=guard, http_client=client
    )
    with_key = WebSearchService(
        WebSearchConfig(brave_api_key="key", ddgs_backend="bing"), guard=guard, http_client=client
    )

    assert [e.name for e in without_key.engines] == ["DDGS", "DuckDuckGo"]
    assert [e.name for e in with_key.engines] == ["BraveAPI", "DDGS", "DuckDuckGo"]
    assert without_key.fallback_engine is not None and without_key.fallback_engine.name == "Brave"
    assert isinstance(with_key.engines[0], BraveApiEngine)
    assert isinstance(with_key.engines[1], DdgsEngine) and with_key.engines[1]._backend == "bing"


def test_engines_override_has_no_fallback_by_default(guard):
    assert make_service(guard, [FakeEngine("a")]).fallback_engine is None


def test_engine_timeout_from_environment(monkeypatch):
    monkeypatch.setenv("ENGINE_TIMEOUT_SECONDS", "2")
    assert WebSearchService().engine_timeout == 2.0
    assert WebSearchConfig().engine_timeout_seconds == 2.0


@pytest.mark.parametrize("env, expected", [({}, False), ({"ALLOW_PRIVATE_URLS": "true"}, True)])
def test_allow_private_urls_from_environment(monkeypatch, env, expected):
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert WebSearchService().guard.allow_private is expected
