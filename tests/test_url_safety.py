import httpx
import pytest

from features.web_search.url_safety import UnsafeURLError, URLGuard, is_public_ip

from .conftest import make_resolver, mock_client


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "javascript:alert(1)",
        "example.com/no-scheme",
        "http:///no-host",
        "http://localhost/",
        "http://127.0.0.1:3000/health",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.1.2.3/",
        "http://192.168.0.1/",
        "http://[::ffff:127.0.0.1]/",
        "http://0.0.0.0/",
        "http://intranet.internal/",
        "http://metadata.internal/",
        "http://mixed.internal/",  # one private address is enough to block
    ],
)
async def test_unsafe_urls_are_rejected(guard, url):
    with pytest.raises(UnsafeURLError):
        await guard.check(url)


@pytest.mark.parametrize("url", ["https://example.com/page", "http://93.184.215.14/", "https://[2606:4700::1111]/"])
async def test_public_urls_are_allowed(guard, url):
    await guard.check(url)


async def test_allow_private_still_enforces_scheme():
    guard = URLGuard(allow_private=True, resolver=make_resolver({"intranet.internal": ["10.0.0.5"]}))
    await guard.check("http://intranet.internal/")
    await guard.check("http://127.0.0.1/")
    with pytest.raises(UnsafeURLError):
        await guard.check("file:///etc/passwd")


async def test_unresolvable_host_is_rejected():
    async def failing_resolver(host):
        raise OSError("Name or service not known")

    with pytest.raises(UnsafeURLError, match="could not resolve"):
        await URLGuard(resolver=failing_resolver).check("https://nope.invalid/")


async def test_resolution_is_cached():
    calls = []

    async def counting_resolver(host):
        calls.append(host)
        return ["93.184.215.14"]

    guard = URLGuard(resolver=counting_resolver)
    await guard.check("https://example.com/a")
    await guard.check("https://example.com/b")
    assert calls == ["example.com"]


async def test_redirect_to_private_address_is_blocked(guard):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "public.example":
            return httpx.Response(302, headers={"Location": "http://intranet.internal/secret"})
        return httpx.Response(200, text="secret")

    async with mock_client(handler, guard) as client:
        with pytest.raises(UnsafeURLError):
            await client.get("https://public.example/")


@pytest.mark.parametrize(
    "address, public",
    [("8.8.8.8", True), ("10.0.0.1", False), ("100.64.0.1", False), ("224.0.0.1", False),
     ("::ffff:10.0.0.1", False), ("2606:4700::1111", True), ("fe80::1", False)],
)
def test_is_public_ip(address, public):
    assert is_public_ip(address) is public


class FakeRoute:
    def __init__(self, url):
        self.request = type("Request", (), {"url": url})()
        self.outcome = None

    async def continue_(self):
        self.outcome = "continued"

    async def abort(self, error_code=None):
        self.outcome = "aborted"


@pytest.mark.parametrize(
    "url, outcome",
    [("https://example.com/app.js", "continued"), ("http://169.254.169.254/", "aborted"),
     ("data:image/png;base64,AAAA", "continued"), ("blob:https://example.com/1", "continued")],
)
async def test_browser_route_handler(guard, url, outcome):
    route = FakeRoute(url)
    await guard.route_handler(route)
    assert route.outcome == outcome
