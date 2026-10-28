import httpx
import pytest

from features.web_search.extraction import (
    ContentExtractor,
    html_to_text,
    is_meaningful_content,
    truncate,
)
from features.web_search.url_safety import UnsafeURLError

from .conftest import FakeBrowser, FakePage, mock_client

ARTICLE = " ".join(["This is a sentence about the robot uprising in modern fiction."] * 40)
ARTICLE_HTML = f"""
<html><head><title>Robots</title></head><body>
<nav>Home | About | Contact</nav>
<article><h1>Robots in fiction</h1><p>{ARTICLE}</p><p>{ARTICLE}</p></article>
<footer>Copyright</footer>
</body></html>
"""


@pytest.mark.parametrize(
    "content, meaningful",
    [
        ("too short", False),
        ("Please complete the CAPTCHA to continue. " * 5, False),
        ("Access denied. You don't have permission to access this page on this server. " * 2, False),
        ("A long article that merely mentions a robot and a 403 status code. " * 40, True),
        ("A normal page about gardening, soil, water and the right time to plant. " * 3, True),
    ],
)
def test_is_meaningful_content(content, meaningful):
    assert is_meaningful_content(content) is meaningful


def test_html_to_text_keeps_main_content_and_drops_boilerplate():
    text = html_to_text(ARTICLE_HTML, "https://example.com/robots")
    assert "robot uprising" in text
    assert "Home | About" not in text


def test_truncate():
    assert truncate("abcdef", None) == "abcdef"
    assert truncate("abcdef", 10) == "abcdef"
    assert truncate("abcdef", 3) == "abc\n\n[Content truncated at 3 characters]"


async def test_extract_uses_http_when_content_is_meaningful(guard):
    browser = FakeBrowser()
    async with mock_client(lambda request: httpx.Response(200, text=ARTICLE_HTML), guard) as client:
        extractor = ContentExtractor(client, browser, guard, lambda: "agent")
        content = await extractor.extract("https://example.com/robots")
    assert "robot uprising" in content
    assert browser.pages_opened == 0


async def test_extract_falls_back_to_browser(guard):
    shell = "<html><body><div id='root'></div><noscript>Please enable JavaScript</noscript></body></html>"
    browser = FakeBrowser(FakePage(html=ARTICLE_HTML))
    async with mock_client(lambda request: httpx.Response(200, text=shell), guard) as client:
        extractor = ContentExtractor(client, browser, guard, lambda: "agent")
        content = await extractor.extract("https://spa.example/", max_length=50)
    assert browser.pages_opened == 1
    assert content.endswith("[Content truncated at 50 characters]")


async def test_extract_falls_back_to_browser_on_http_error(guard):
    browser = FakeBrowser(FakePage(html=ARTICLE_HTML))
    async with mock_client(lambda request: httpx.Response(403), guard) as client:
        extractor = ContentExtractor(client, browser, guard, lambda: "agent")
        content = await extractor.extract("https://blocked.example/")
    assert "robot uprising" in content


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://169.254.169.254/"])
async def test_extract_rejects_unsafe_urls_before_any_fetch(guard, url):
    browser = FakeBrowser()

    def handler(request):
        raise AssertionError("should not fetch")

    async with mock_client(handler, guard) as client:
        with pytest.raises(UnsafeURLError):
            await ContentExtractor(client, browser, guard, lambda: "agent").extract(url)
    assert browser.pages_opened == 0


async def test_extract_redirect_to_private_does_not_fall_back_to_browser(guard):
    browser = FakeBrowser()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "http://intranet.internal/"})

    async with mock_client(handler, guard) as client:
        with pytest.raises(UnsafeURLError):
            await ContentExtractor(client, browser, guard, lambda: "agent").extract("https://public.example/")
    assert browser.pages_opened == 0
