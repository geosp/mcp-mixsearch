"""
Result fusion

Merges the ranked result lists of several engines into one list with
reciprocal rank fusion (RRF). Results are deduplicated by normalized URL, and
each merged result records every engine that returned it.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import SearchResult

RRF_K = 60

TRACKING_PARAMS = frozenset(
    {
        "gclid",
        "dclid",
        "fbclid",
        "msclkid",
        "yclid",
        "mc_cid",
        "mc_eid",
        "_ga",
        "_gl",
        "igshid",
        "ref_src",
    }
)

_DEFAULT_PORTS = {"http": 80, "https": 443}


def _is_tracking_param(key: str) -> bool:
    key = key.lower()
    return key.startswith("utm_") or key in TRACKING_PARAMS


def normalize_url(url: str) -> str:
    """
    Key used to detect duplicate URLs; never returned to clients

    Lowercases the scheme and host, drops a leading "www.", the default port,
    the fragment, tracking parameters and a trailing "/", and sorts the
    remaining query parameters. Non-http(s) URLs are only stripped of whitespace.
    """
    url = url.strip()
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return url

    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if scheme not in _DEFAULT_PORTS or not host:
        return url

    if host.startswith("www."):
        host = host[4:]
    netloc = host if port is None or port == _DEFAULT_PORTS[scheme] else f"{host}:{port}"

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not _is_tracking_param(key)
        )
    )
    return urlunsplit((scheme, netloc, path, query, ""))


@dataclass
class _Occurrence:
    rank: int  # 1-based position in its engine's list
    engine_index: int  # position of the engine in the fused lists
    result: SearchResult


@dataclass
class _Group:
    score: float = 0.0
    occurrences: List[_Occurrence] = field(default_factory=list)

    def best(self) -> _Occurrence:
        return min(self.occurrences, key=lambda o: (o.rank, o.engine_index))


def _merge(group: _Group, engine_names: Sequence[str]) -> SearchResult:
    ordered = sorted(group.occurrences, key=lambda o: (o.rank, o.engine_index))
    best = ordered[0].result
    title = next((o.result.title for o in ordered if o.result.title.strip()), "")
    description = max((o.result.description for o in ordered), key=len, default="")
    engine_indexes = sorted({o.engine_index for o in group.occurrences})
    return SearchResult(
        title=title,
        url=best.url,
        description=description,
        timestamp=best.timestamp,
        engines=[engine_names[i] for i in engine_indexes],
    )


def fuse_results(lists: Sequence[Tuple[str, List[SearchResult]]]) -> List[SearchResult]:
    """
    Fuse ranked result lists with reciprocal rank fusion

    Args:
        lists: (engine label, results in rank order) pairs, in configured engine order

    Returns:
        Merged results, best first: by RRF score, then best rank, then engine order.
        Results with an empty URL are dropped; within one list only the first
        occurrence of a normalized URL counts.
    """
    engine_names = [name for name, _ in lists]
    groups: Dict[str, _Group] = {}

    for engine_index, (_, results) in enumerate(lists):
        seen = set()
        rank = 0
        for result in results:
            # Engines build URLs from untrusted payloads; one may be missing
            if not isinstance(result.url, str) or not result.url.strip():
                continue
            rank += 1
            key = normalize_url(result.url)
            if key in seen:
                continue
            seen.add(key)
            group = groups.setdefault(key, _Group())
            group.score += 1.0 / (RRF_K + rank)
            group.occurrences.append(_Occurrence(rank, engine_index, result))

    def sort_key(group: _Group) -> Tuple[float, int, int]:
        best = group.best()
        return (-group.score, best.rank, best.engine_index)

    return [_merge(group, engine_names) for group in sorted(groups.values(), key=sort_key)]
