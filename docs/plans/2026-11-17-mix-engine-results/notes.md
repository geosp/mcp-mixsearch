# Notes · Mix results from several search engines

## D1 · RRF mechanics

For each engine list `L_e` (after empty URLs are dropped), the result at position `i` (0-based)
has rank `r = i + 1`. Its contribution to its normalized URL is `1 / (60 + r)`.

Worked example (k = 60):

| URL | BraveAPI rank | DDGS rank | DuckDuckGo rank | Score |
| --- | --- | --- | --- | --- |
| A | 2 | 2 | – | 1/62 + 1/62 = 0.03226 |
| B | 1 | – | – | 1/61 = 0.01639 |
| C | – | 1 | 3 | 1/61 + 1/63 = 0.03227 |

Order: C, A, B. Sort key: `(-score, best_rank, engine_index_of_best_rank)`.

If an engine returns the same normalized URL twice, only its first (best) position counts, and the
duplicate is ignored. That way one engine can't score a URL twice.

`k = 60` is the value from the original RRF paper (Cormack, Clarke and Büttcher, SIGIR 2009) and
the common default. With at most 10 results per engine, `k` mostly sets how much agreement
outweighs rank. At 60, two mid-list hits always beat one first-place hit.

## D2 · URL normalization rules

Applied with `urllib.parse` (standard library) only:

1. `urlsplit`. If the scheme isn't `http` or `https`, or the host is empty, the key is the raw
   string stripped of whitespace.
2. Lowercase the scheme and the host. Drop a leading `www.` from the host.
3. Drop the port when it's the scheme's default (80 for http, 443 for https).
4. Treat `http` and `https` as different keys. Merging them could merge pages that really differ,
   and engines rarely disagree on the scheme.
5. Path: keep the case. Strip a trailing `/` unless the path is just `/`, and treat an empty path
   as `/`.
6. Query: `parse_qsl(keep_blank_values=True)`. Drop every key that starts with `utm_`, and these
   keys: `gclid`, `dclid`, `fbclid`, `msclkid`, `yclid`, `mc_cid`, `mc_eid`, `_ga`, `_gl`,
   `igshid`, `ref_src`. Sort the remaining pairs, then `urlencode`.
7. Drop the fragment.

Keys are matched case-insensitively, so `UTM_Source` and `GCLID` are dropped too.
`ref` is deliberately kept, because some sites use it for content. The list lives in one constant
in `fusion.py`.

Test cases for the phase 01 task:

| Input | Key |
| --- | --- |
| `https://www.Example.com/a/?utm_source=x#top` | `https://example.com/a` |
| `HTTPS://example.com:443/` | `https://example.com/` |
| `https://example.com` | `https://example.com/` |
| `https://example.com/a?b=2&a=1&fbclid=z` | `https://example.com/a?a=1&b=2` |
| `https://example.com/A` | `https://example.com/A` (case kept) |
| `http://example.com/a` | `http://example.com/a` (differs from https) |

## D4 · Concurrency and timeouts

```python
async def _run(engine, timeout):
    try:
        return engine.name, await asyncio.wait_for(engine.search(query, filters), timeout)
    except TimeoutError:
        logger.warning("Search engine %s timed out after %ss", engine.name, timeout)
    except Exception as e:
        logger.warning("Search engine %s failed: %s", engine.name, e)
    return engine.name, []
```

- On Python 3.11+, `asyncio.wait_for` raises the built-in `TimeoutError`. Check the version in
  `.python-version` during apply.
- Cancelling `BraveApiEngine` and `DuckDuckGoHtmlEngine` cancels their httpx request cleanly.
- `DdgsEngine` uses `asyncio.to_thread`. Cancellation stops the await, but the thread runs until
  ddgs returns. Its result is discarded.
- Each engine also logs a count and duration at info level when it succeeds (task 01 3.3). This
  makes slow engines visible in logs when tuning `ENGINE_TIMEOUT_SECONDS`.
- The fallback uses the same wrapper with `FALLBACK_TIMEOUT_SECONDS` (30 s), a module constant
  that tests monkeypatch.

## Current code, for reference

- `service.py` `_multi_engine_search`: a sequential loop that returns the first list with an
  `assess_result_quality` score of at least 0.3, or else the best-scoring list.
- `_build_engines`: `[BraveAPI?] + [DDGS, Brave, DuckDuckGo]`. `tests/test_service.py`
  (`test_engine_order_depends_on_brave_api_key`) pins this order and will change.
- `tests/test_service.py`:
  - `test_first_good_engine_wins`, `test_best_effort_results_when_no_engine_meets_threshold` and
    `test_assess_result_quality` (along with its import) test the old selection. They are
    removed.
  - The `result()` helper defaults every URL to `https://example.com/`. Deduplication would
    collapse `test_results_are_limited` to one result, so each result needs its own URL.
- `search_summaries` builds its result dicts by hand, so `engines` must be added there explicitly.
- `tests/test_tools.py` `FakeService` returns dicts without `engines`, which is why `tool.py`
  reads the list with `.get`.

## Rollback

Reverting leaves `ENGINE_TIMEOUT_SECONDS` possibly set in a deployment's environment. That is
harmless, because `WebSearchConfig` uses `extra="ignore"`. No client depends on `engines` yet, so
dropping it breaks nothing.

## Risks

- **Latency:** today the loop returns at the first engine scoring at least 0.3
  (`service.py` `_multi_engine_search`). With a Brave key, a typical search is one BraveAPI call;
  without one, a single DDGS call. DDGS `auto` runs several providers in batches with its own
  per-batch timeout (5 s by default), so it is likely the slowest cheap engine.
- **Worst case today:** BraveAPI, DDGS and DuckDuckGo HTML can each take up to the 15 s HTTP
  timeout, plus the browser engine's page load and 5 s network-idle wait.
- **Request load:** DuckDuckGo HTML was last in the order and rarely reached. It is now called on
  every web search.
- **Threads:** the default executor has at least 5 workers (`min(32, cpu + 4)`). Content extraction
  also uses it, through `asyncio.to_thread(html_to_text, …)` in `extraction.py`. A DDGS call holds
  its thread until ddgs's internal pool finishes.
- **Correlation:** ddgs's `auto` backend includes the duckduckgo and brave providers, so the same
  underlying index can count more than once in RRF.
