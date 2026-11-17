import pytest

from features.web_search.fusion import fuse_results, normalize_url
from features.web_search.models import SearchResult


def r(url, title="t", description="", timestamp="ts"):
    return SearchResult(title=title, url=url, description=description, timestamp=timestamp)


@pytest.mark.parametrize(
    "url, key",
    [
        ("https://www.Example.com/a/?utm_source=x#top", "https://example.com/a"),
        ("HTTPS://example.com:443/", "https://example.com/"),
        ("https://example.com", "https://example.com/"),
        ("https://example.com/a?b=2&a=1&fbclid=z", "https://example.com/a?a=1&b=2"),
        ("https://example.com/A", "https://example.com/A"),
        ("http://example.com/a", "http://example.com/a"),
        ("http://example.com:8080/a", "http://example.com:8080/a"),
        ("https://example.com/a?UTM_Medium=x&gclid=1&ref=home", "https://example.com/a?ref=home"),
        ("https://example.com/a?q=", "https://example.com/a?q="),
        ("https://example.com/a//", "https://example.com/a/"),
        ("  mailto:someone@example.com ", "mailto:someone@example.com"),
        ("not a url", "not a url"),
    ],
)
def test_normalize_url(url, key):
    assert normalize_url(url) == key


def test_normalize_url_keeps_distinct_queries_apart():
    assert normalize_url("https://example.com/a?id=1") != normalize_url(
        "https://example.com/a?id=2"
    )


def test_fuse_empty_input():
    assert fuse_results([]) == []
    assert fuse_results([("A", []), ("B", [])]) == []


def test_fuse_worked_example_from_notes():
    a, b, c = "https://a.example/", "https://b.example/", "https://c.example/"
    fused = fuse_results(
        [
            ("BraveAPI", [r(b), r(a)]),
            ("DDGS", [r(c), r(a)]),
            ("DuckDuckGo", [r("https://x.example/"), r("https://y.example/"), r(c)]),
        ]
    )
    assert [f.url for f in fused][:3] == [c, a, b]
    assert fused[0].engines == ["DDGS", "DuckDuckGo"]
    assert fused[1].engines == ["BraveAPI", "DDGS"]


def test_agreement_beats_single_first_place():
    fused = fuse_results(
        [
            ("E1", [r("https://b.example/"), r("https://a.example/")]),
            ("E2", [r("https://c.example/"), r("https://a.example/")]),
        ]
    )
    assert fused[0].url == "https://a.example/"


def test_ties_go_to_best_rank_then_engine_order():
    fused = fuse_results(
        [
            ("E1", [r("https://one.example/"), r("https://two.example/")]),
            ("E2", [r("https://three.example/")]),
        ]
    )
    # one.example and three.example both score 1/61; one.example's engine comes first
    assert [f.url for f in fused] == [
        "https://one.example/",
        "https://three.example/",
        "https://two.example/",
    ]


def test_duplicates_merge_across_and_within_engines():
    fused = fuse_results(
        [
            ("E1", [r("https://www.example.com/a/"), r("https://example.com/a?utm_source=x")]),
            ("E2", [r("https://example.com/a#frag")]),
        ]
    )
    assert len(fused) == 1
    assert fused[0].url == "https://www.example.com/a/"
    assert fused[0].engines == ["E1", "E2"]


def test_same_engine_duplicate_counts_once():
    single = fuse_results([("E1", [r("https://a.example/"), r("https://a.example/")])])
    assert len(single) == 1
    once = fuse_results([("E1", [r("https://a.example/")])])
    assert single[0].url == once[0].url


def test_field_picks():
    fused = fuse_results(
        [
            ("E1", [r("https://x.example/"), r("https://a.example/", title="", timestamp="e1")]),
            (
                "E2",
                [
                    r(
                        "https://a.example/page",
                        title="Second title",
                        description="Full summary",
                        timestamp="e2",
                    )
                ],
            ),
            ("E3", [r("https://a.example", title="Best title", timestamp="e3")]),
        ]
    )
    merged = next(f for f in fused if "a.example" in f.url and "page" not in f.url)
    # best-ranked occurrence of a.example/ is E3 (rank 1); E1 has rank 2
    assert merged.url == "https://a.example"
    assert merged.title == "Best title"
    assert merged.timestamp == "e3"
    assert merged.engines == ["E1", "E3"]


def test_empty_title_falls_back_and_longest_description_wins():
    fused = fuse_results(
        [
            ("E1", [r("https://a.example/", title="", description="", timestamp="e1")]),
            ("E2", [r("https://a.example/", title="Title", description="Full summary")]),
        ]
    )
    assert fused[0].title == "Title"
    assert fused[0].description == "Full summary"
    assert fused[0].timestamp == "e1"


def test_empty_urls_are_dropped():
    fused = fuse_results([("E1", [r(""), r("  "), r("https://a.example/")])])
    assert [f.url for f in fused] == ["https://a.example/"]


def test_search_result_to_dict_includes_engines():
    result = SearchResult(title="t", url="u", description="d", engines=["DDGS"])
    assert result.to_dict()["engines"] == ["DDGS"]
    assert SearchResult(title="t", url="u", description="d").to_dict()["engines"] == []


def test_missing_url_is_dropped():
    fused = fuse_results([("E1", [r(None), r("https://a.example/")])])
    assert [f.url for f in fused] == ["https://a.example/"]


def test_whitespace_title_counts_as_empty():
    fused = fuse_results(
        [
            ("E1", [r("https://a.example/", title="   ")]),
            ("E2", [r("https://a.example/", title="Real title")]),
        ]
    )
    assert fused[0].title == "Real title"


def test_different_query_values_stay_separate_results():
    fused = fuse_results(
        [
            ("E1", [r("https://example.com/a?id=1")]),
            ("E2", [r("https://example.com/a?id=2")]),
        ]
    )
    assert len(fused) == 2
