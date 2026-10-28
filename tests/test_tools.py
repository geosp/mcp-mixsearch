import pytest
from fastmcp import Client, FastMCP

from features.web_search.tool import register_tool
from features.web_search.url_safety import UnsafeURLError


class FakeService:
    """Records calls and returns canned results in the real service's shape"""

    def __init__(self):
        self.calls = []

    async def search_and_extract(self, query, filters, include_content=True, max_content_length=None):
        self.calls.append(("search_and_extract", query, filters, include_content, max_content_length))
        return {"query": query, "total_results": 2, "status": "success", "results": [
            {"title": "Good", "url": "https://a.example", "description": "A",
             "full_content": "Body of A", "fetch_status": "success", "error": None},
            {"title": "Broken", "url": "https://b.example", "description": "B",
             "full_content": "", "fetch_status": "error", "error": "timeout"},
        ]}

    async def search_summaries(self, query, filters):
        self.calls.append(("search_summaries", query, filters))
        return {"query": query, "total_results": 1, "status": "success", "results": [
            {"title": "Summary", "url": "https://s.example", "description": "S", "timestamp": "t"},
        ]}

    async def extract_single_page(self, url, max_content_length=None):
        self.calls.append(("extract_single_page", url, max_content_length))
        if url.startswith("file:"):
            raise UnsafeURLError("scheme 'file' is not allowed, only http and https")
        return "one two three"


@pytest.fixture
def service():
    return FakeService()


@pytest.fixture
async def client(service):
    mcp = FastMCP("test")
    register_tool(mcp, service)
    async with Client(mcp) as client:
        yield client


async def test_tools_are_registered_with_parameters(client):
    tools = {tool.name: tool for tool in await client.list_tools()}
    assert set(tools) == {"full_web_search", "get_web_search_summaries", "get_single_web_page_content"}
    assert set(tools["full_web_search"].input_schema["properties"]) == {
        "query", "limit", "include_content", "max_content_length", "top_n",
        "recency_days", "source", "language", "country",
    }
    assert set(tools["get_single_web_page_content"].input_schema["properties"]) == {"url", "max_content_length"}
    assert "summaries" in tools["get_web_search_summaries"].description.lower()


async def test_full_web_search_formats_results_and_errors(client, service):
    result = await client.call_tool("full_web_search", {"query": "q", "limit": 50, "recency_days": 7})

    text = result.content[0].text
    assert text.startswith("Search completed for 'q' with 2 results")
    assert "**1. Good**\nURL: https://a.example" in text
    assert "**Full Content:**\nBody of A" in text
    assert "**Content Extraction Failed:** timeout" in text

    filters = service.calls[0][2]
    assert filters.limit == 10 and filters.time_bucket == "w"


async def test_summaries_top_n_and_filters(client, service):
    result = await client.call_tool("get_web_search_summaries", {
        "query": "q", "top_n": 3, "source": "news", "country": "FR", "language": "fr",
    })

    assert "**1. Summary**\nURL: https://s.example\nDescription: S" in result.content[0].text
    filters = service.calls[0][2]
    assert (filters.limit, filters.source, filters.country, filters.language) == (3, "news", "fr", "fr")


async def test_single_page_content(client):
    result = await client.call_tool("get_single_web_page_content", {"url": "https://example.com"})
    assert result.content[0].text == "**Page Content from: https://example.com**\n\none two three\n\n**Word count:** 3\n"


async def test_single_page_unsafe_url_is_a_tool_error(client):
    result = await client.call_tool(
        "get_single_web_page_content", {"url": "file:///etc/passwd"}, raise_on_error=False
    )
    assert result.is_error
    assert "URL not allowed: scheme 'file' is not allowed" in result.content[0].text
