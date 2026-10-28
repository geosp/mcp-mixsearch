import httpx
import pytest

from features.web_search.engines import (
    BraveApiEngine,
    BraveBrowserEngine,
    DdgsEngine,
    DuckDuckGoHtmlEngine,
    convert_ddgs_result,
    parse_ddg_html,
    strip_tags,
    unwrap_ddg_redirect,
)
from features.web_search.filters import SearchFilters

from .conftest import FakeBrowser, FakePage, mock_client

BRAVE_WEB_RESPONSE = {
    "web": {
        "results": [
            {"title": "Model Context Protocol", "url": "https://modelcontextprotocol.io/",
             "description": "The <strong>Model Context Protocol</strong> &amp; its spec"},
            {"title": "MCP on GitHub", "url": "https://github.com/modelcontextprotocol",
             "description": "Org", "age": "2 days ago"},
        ]
    }
}


async def test_brave_api_web_search(guard):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = request.url
        seen["token"] = request.headers.get("X-Subscription-Token")
        return httpx.Response(200, json=BRAVE_WEB_RESPONSE)

    async with mock_client(handler, guard) as client:
        engine = BraveApiEngine("secret-key", client)
        filters = SearchFilters.from_tool_args(limit=2, recency_days=7, language="en", country="us")
        results = await engine.search("model context protocol", filters)

    assert seen["url"].path == "/res/v1/web/search"
    assert dict(seen["url"].params) == {
        "q": "model context protocol", "count": "2", "country": "US",
        "search_lang": "en", "freshness": "pw",
    }
    assert seen["token"] == "secret-key"
    assert [r.url for r in results] == ["https://modelcontextprotocol.io/", "https://github.com/modelcontextprotocol"]
    assert results[0].description == "The Model Context Protocol & its spec"
    assert results[1].timestamp == "2 days ago"


async def test_brave_api_news_uses_news_endpoint(guard):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/res/v1/news/search"
        return httpx.Response(200, json={"results": [{"title": "Headline", "url": "https://news.example/a",
                                                      "description": "Story"}]})

    async with mock_client(handler, guard) as client:
        results = await BraveApiEngine("k", client).search("q", SearchFilters(source="news"))
    assert [r.title for r in results] == ["Headline"]


async def test_brave_api_skips_images(guard):
    def handler(request):
        raise AssertionError("should not be called")

    async with mock_client(handler, guard) as client:
        assert await BraveApiEngine("k", client).search("q", SearchFilters(source="images")) == []


@pytest.mark.parametrize("status", [401, 429])
async def test_brave_api_errors_raise(guard, status):
    async with mock_client(lambda request: httpx.Response(status), guard) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await BraveApiEngine("k", client).search("q", SearchFilters())


@pytest.mark.parametrize(
    "method, item, url, description",
    [
        ("text", {"title": "T", "href": "https://a.example", "body": "B"}, "https://a.example", "B"),
        ("news", {"title": "T", "url": "https://n.example", "body": "B", "date": "2026-10-01"},
         "https://n.example", "B"),
        ("images", {"title": "T", "url": "https://page.example", "image": "https://img.example/1.png",
                    "source": "Bing"}, "https://page.example", "Bing | https://img.example/1.png"),
        ("videos", {"title": "T", "content": "https://video.example/v", "description": "D"},
         "https://video.example/v", "D"),
    ],
)
def test_convert_ddgs_result(method, item, url, description):
    result = convert_ddgs_result(item, method)
    assert (result.title, result.url, result.description) == ("T", url, description)


def test_convert_ddgs_news_keeps_date():
    assert convert_ddgs_result({"date": "2026-10-01"}, "news").timestamp == "2026-10-01"


class FakeDDGS:
    calls = []

    def text(self, query, **kwargs):
        FakeDDGS.calls.append(("text", query, kwargs))
        return [{"title": "Result", "href": "https://a.example", "body": "Body"}]

    def news(self, query, **kwargs):
        FakeDDGS.calls.append(("news", query, kwargs))
        return [{"title": "News", "url": "https://n.example", "body": "Body", "date": "today"}]


async def test_ddgs_engine_passes_real_ddgs_parameters():
    FakeDDGS.calls = []
    engine = DdgsEngine("auto", ddgs_factory=FakeDDGS)

    await engine.search("climate", SearchFilters.from_tool_args(limit=3, recency_days=30, country="fr"))
    news = await engine.search("headlines", SearchFilters(source="news"))

    assert FakeDDGS.calls[0] == (
        "text", "climate", {"max_results": 3, "backend": "auto", "timelimit": "m", "region": "fr-fr"}
    )
    assert FakeDDGS.calls[1][0] == "news"
    assert news[0].url == "https://n.example"


DDG_HTML = """
<div class="result">
  <h2 class="result__title"><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa%3Fx%3D1&rut=abc">Example A</a></h2>
  <a class="result__snippet">Snippet A</a>
</div>
<div class="result">
  <h2 class="result__title"><a href="https://example.org/b">Example B</a></h2>
  <a class="result__snippet">Snippet B</a>
</div>
<div class="result"><h2 class="result__title"><a href="https://example.net/c">No snippet</a></h2></div>
"""


def test_parse_ddg_html_unwraps_redirects_and_skips_incomplete():
    results = parse_ddg_html(DDG_HTML, limit=10)
    assert [(r.title, r.url, r.description) for r in results] == [
        ("Example A", "https://example.com/a?x=1", "Snippet A"),
        ("Example B", "https://example.org/b", "Snippet B"),
    ]
    assert len(parse_ddg_html(DDG_HTML, limit=1)) == 1


def test_unwrap_ddg_redirect_leaves_plain_links():
    assert unwrap_ddg_redirect("https://example.org/b") == "https://example.org/b"


async def test_duckduckgo_html_engine(guard):
    def handler(request: httpx.Request) -> httpx.Response:
        assert dict(request.url.params) == {"q": "test", "kl": "us-en", "df": "w"}
        return httpx.Response(200, text=DDG_HTML)

    async with mock_client(handler, guard) as client:
        engine = DuckDuckGoHtmlEngine(client, lambda: "test-agent")
        results = await engine.search("test", SearchFilters.from_tool_args(recency_days=7, country="us"))
    assert len(results) == 2


async def test_brave_browser_engine_drops_brave_links():
    page = FakePage(evaluate_result=[
        {"title": "Elaborate", "url": "https://search.brave.com/ask?q=elaborate", "description": "AI"},
        {"title": "Real", "url": "https://example.com/real", "description": "Real result"},
        {"title": "Brave home", "url": "https://brave.com/", "description": "Brave"},
    ])
    engine = BraveBrowserEngine(FakeBrowser(page))

    results = await engine.search("query", SearchFilters.from_tool_args(country="fr", recency_days=1))

    assert [r.url for r in results] == ["https://example.com/real"]
    assert "country=FR" in page.visited[0] and "tf=d" in page.visited[0]


def test_strip_tags():
    assert strip_tags("<b>A</b> &amp; <i>B</i>") == "A & B"
