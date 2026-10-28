"""
URL safety checks for content extraction

Only public http(s) URLs may be fetched. This blocks local file reads
(file://) and requests to loopback, private, link-local and other
non-public addresses, including cloud metadata endpoints. The check
runs before a fetch, on every httpx redirect hop and on every request
the browser makes.

DNS rebinding between the check and the connection is not prevented.
"""

import asyncio
import ipaddress
import logging
import socket
import time
from typing import Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = ("http", "https")
# Browser-internal schemes that never reach the network
BROWSER_LOCAL_SCHEMES = ("data", "blob", "about")

CACHE_TTL_SECONDS = 60.0
CACHE_MAX_HOSTS = 1024

Resolver = Callable[[str], Awaitable[List[str]]]


class UnsafeURLError(ValueError):
    """Raised when a URL is not a public http(s) URL"""


async def resolve_host(host: str) -> List[str]:
    """Resolve a hostname to its IP addresses"""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return [info[4][0].split("%", 1)[0] for info in infos]


def is_public_ip(address: str) -> bool:
    """Whether an IP address is globally routable (not private, loopback, link-local, ...)"""
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


class URLGuard:
    """Checks that URLs point at public http(s) hosts"""

    def __init__(self, allow_private: bool = False, resolver: Optional[Resolver] = None):
        """
        Args:
            allow_private: Skip the address check (scheme is still enforced)
            resolver: Hostname resolver, for tests. Defaults to DNS.
        """
        self.allow_private = allow_private
        self._resolver = resolver or resolve_host
        self._cache: Dict[str, Tuple[bool, float]] = {}

    async def check(self, url: str) -> None:
        """
        Raise UnsafeURLError unless url is a public http(s) URL
        """
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme not in ALLOWED_SCHEMES:
            raise UnsafeURLError(f"scheme '{scheme or '(none)'}' is not allowed, only http and https")

        host = parts.hostname
        if not host:
            raise UnsafeURLError(f"URL has no host: {url}")

        if self.allow_private:
            return

        if not await self._is_public_host(host):
            raise UnsafeURLError(f"host '{host}' is not a public address")

    async def _is_public_host(self, host: str) -> bool:
        try:
            return is_public_ip(host)
        except ValueError:
            pass  # Not an IP literal, resolve it

        now = time.monotonic()
        cached = self._cache.get(host)
        if cached and now - cached[1] < CACHE_TTL_SECONDS:
            return cached[0]

        try:
            addresses = await self._resolver(host)
        except OSError as e:
            raise UnsafeURLError(f"could not resolve host '{host}': {e}") from e
        if not addresses:
            raise UnsafeURLError(f"could not resolve host '{host}'")

        public = all(is_public_ip(address) for address in addresses)
        if len(self._cache) >= CACHE_MAX_HOSTS:
            self._cache.clear()
        self._cache[host] = (public, now)
        return public

    async def httpx_hook(self, request: httpx.Request) -> None:
        """httpx request event hook: runs for the first request and every redirect"""
        await self.check(str(request.url))

    async def route_handler(self, route) -> None:
        """Playwright route handler: aborts browser requests to non-public hosts"""
        url = route.request.url
        if urlsplit(url).scheme.lower() in BROWSER_LOCAL_SCHEMES:
            await route.continue_()
            return
        try:
            await self.check(url)
        except UnsafeURLError as e:
            logger.warning(f"Blocked browser request to {url}: {e}")
            await route.abort("blockedbyclient")
            return
        await route.continue_()
