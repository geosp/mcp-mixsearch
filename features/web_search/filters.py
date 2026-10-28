"""
Search filters shared by all search engines

Normalizes the tool arguments once and maps them to each engine's parameters.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

MAX_LIMIT = 10
SOURCES = ("web", "news", "images", "videos")

# DuckDuckGo regions are "<country>-<language>"; used when only a country is given
_DEFAULT_REGION_LANGUAGE = {
    "br": "pt", "cn": "zh", "de": "de", "es": "es", "fr": "fr", "it": "it", "jp": "jp",
    "kr": "kr", "mx": "es", "nl": "nl", "pl": "pl", "pt": "pt", "ru": "ru", "se": "sv",
}


@dataclass(frozen=True)
class SearchFilters:
    """Normalized search filters"""
    limit: int = 5
    recency_days: Optional[int] = None
    source: str = "web"
    language: Optional[str] = None
    country: Optional[str] = None

    @classmethod
    def from_tool_args(
        cls,
        limit: int = 5,
        top_n: Optional[int] = None,
        recency_days: Optional[int] = None,
        source: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
    ) -> "SearchFilters":
        """
        Build filters from MCP tool arguments

        top_n is an alias for limit and wins when given. The limit is clamped
        to 1-10, and unknown sources fall back to "web".
        """
        requested = top_n if top_n is not None else limit
        source = (source or "web").strip().lower()
        return cls(
            limit=max(1, min(requested, MAX_LIMIT)),
            recency_days=recency_days,
            source=source if source in SOURCES else "web",
            language=language.strip().lower() if language else None,
            country=country.strip().lower() if country else None,
        )

    @property
    def time_bucket(self) -> Optional[str]:
        """Recency as d/w/m/y, or None for no time filter (None, <= 0 or > 365 days)"""
        days = self.recency_days
        if days is None or days <= 0 or days > 365:
            return None
        if days == 1:
            return "d"
        if days <= 7:
            return "w"
        if days <= 30:
            return "m"
        return "y"

    @property
    def region(self) -> Optional[str]:
        """DuckDuckGo-style region such as "fr-fr" or "us-en", when a country is set"""
        if not self.country:
            return None
        country = "uk" if self.country == "gb" else self.country
        language = self.language or _DEFAULT_REGION_LANGUAGE.get(country, "en")
        return f"{country}-{language}"

    def ddgs_kwargs(self, backend: str) -> Dict[str, Any]:
        """Keyword arguments for ddgs DDGS.text/news/images/videos"""
        kwargs: Dict[str, Any] = {"max_results": self.limit, "backend": backend}
        if self.time_bucket:
            kwargs["timelimit"] = self.time_bucket
        if self.region:
            kwargs["region"] = self.region
        return kwargs

    def brave_api_params(self) -> Dict[str, Any]:
        """Query parameters for the Brave Search API (without q)"""
        params: Dict[str, Any] = {"count": self.limit}
        if self.country:
            params["country"] = self.country.upper()
        if self.language:
            params["search_lang"] = self.language
        if self.time_bucket:
            params["freshness"] = f"p{self.time_bucket}"
        return params

    def brave_web_params(self) -> Dict[str, Any]:
        """Query parameters for the search.brave.com results page (without q)"""
        params: Dict[str, Any] = {}
        if self.country:
            params["country"] = self.country.upper()
        if self.language:
            params["lang"] = self.language
        if self.time_bucket:
            params["tf"] = self.time_bucket
        return params

    def ddg_html_params(self) -> Dict[str, Any]:
        """Query parameters for the DuckDuckGo HTML results page (without q)"""
        params: Dict[str, Any] = {}
        if self.region:
            params["kl"] = self.region
        if self.time_bucket:
            params["df"] = self.time_bucket
        return params
