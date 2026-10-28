import pytest

from features.web_search.filters import SearchFilters


@pytest.mark.parametrize(
    "days, bucket",
    [(None, None), (-1, None), (0, None), (1, "d"), (2, "w"), (7, "w"), (8, "m"),
     (30, "m"), (31, "y"), (365, "y"), (366, None)],
)
def test_time_bucket(days, bucket):
    assert SearchFilters(recency_days=days).time_bucket == bucket


def test_top_n_overrides_limit():
    assert SearchFilters.from_tool_args(limit=3, top_n=7).limit == 7


@pytest.mark.parametrize("requested, expected", [(0, 1), (-5, 1), (5, 5), (10, 10), (50, 10)])
def test_limit_is_clamped(requested, expected):
    assert SearchFilters.from_tool_args(limit=requested).limit == expected


def test_source_normalized_and_unknown_falls_back_to_web():
    assert SearchFilters.from_tool_args(source=" NEWS ").source == "news"
    assert SearchFilters.from_tool_args(source="podcasts").source == "web"
    assert SearchFilters.from_tool_args().source == "web"


def test_language_and_country_lowercased():
    filters = SearchFilters.from_tool_args(language="FR", country="FR")
    assert (filters.language, filters.country) == ("fr", "fr")


@pytest.mark.parametrize(
    "country, language, region",
    [(None, "fr", None), ("us", None, "us-en"), ("fr", None, "fr-fr"),
     ("gb", None, "uk-en"), ("ca", "fr", "ca-fr"), ("br", None, "br-pt")],
)
def test_region(country, language, region):
    assert SearchFilters(country=country, language=language).region == region


def test_ddgs_kwargs():
    filters = SearchFilters.from_tool_args(limit=4, recency_days=7, country="DE")
    assert filters.ddgs_kwargs("auto") == {
        "max_results": 4, "backend": "auto", "timelimit": "w", "region": "de-de",
    }
    assert SearchFilters().ddgs_kwargs("bing") == {"max_results": 5, "backend": "bing"}


def test_brave_api_params():
    filters = SearchFilters.from_tool_args(limit=3, recency_days=1, language="es", country="mx")
    assert filters.brave_api_params() == {
        "count": 3, "country": "MX", "search_lang": "es", "freshness": "pd",
    }


def test_brave_web_and_ddg_html_params():
    filters = SearchFilters.from_tool_args(recency_days=30, language="fr", country="fr")
    assert filters.brave_web_params() == {"country": "FR", "lang": "fr", "tf": "m"}
    assert filters.ddg_html_params() == {"kl": "fr-fr", "df": "m"}
    assert SearchFilters().ddg_html_params() == {}
