---
title: Mix results from several search engines
status: draft
created: 2026-11-17
updated: 2026-11-17
design_review: { status: changes-requested, rounds: 1, last: 2026-11-17 }
approved: null
adr_review: null
---

# Mix results from several search engines

## Summary

Despite its name, mcp-mixsearch returns the results of one engine only: the first that clears a
word-overlap score of 0.3. This plan makes it run the cheap engines (BraveAPI when a key is set,
DDGS, DuckDuckGo HTML) in parallel, each with its own timeout. It merges their ranked lists with
reciprocal rank fusion, removes duplicate URLs and tags every result with the engines that
returned it. The Playwright Brave engine runs only when the merged list is shorter than `limit`.
The word-overlap score is removed (D6). Both tools gain an `Engines:` line; existing fields stay.

```text
query ─┬─ BraveAPI ──┐  each with a 10 s timeout; failures logged and skipped
       ├─ DDGS ──────┼─► dedupe by normalized URL ─► RRF ─► fewer than limit? ─yes─► Brave (browser) ─► fuse again
       └─ DuckDuckGo ┘                                                       └─no──► top `limit`
```

Main risks: a slower search, because it waits for the slowest cheap engine up to its timeout. And
ddgs threads that keep running after a timeout. Both are covered under Risks.

## Why

`WebSearchService._multi_engine_search` in `features/web_search/service.py` tries the engines one
at a time and returns the first list whose `assess_result_quality` score is at least 0.3. So results
never combine sources, and a slow or broken engine early in the order delays every search by up to
the 15 s HTTP timeout. The score only counts query words in titles and descriptions, which rewards
keyword-stuffed snippets and ignores rank. Agreement between independent engines is a better
relevance signal, and the cheap engines can run together.

## What changes

- The cheap engines run concurrently. Each has its own timeout (new `ENGINE_TIMEOUT_SECONDS`
  setting).
- Their lists are deduplicated by normalized URL and fused by reciprocal rank fusion, then cut to
  `limit`.
- The Brave browser engine becomes a fallback that runs only when too few results come back.
- DuckDuckGo HTML and the Brave browser engine return nothing for `news`, `images` and `videos`.
  Before, they returned plain web results for those sources.
- Every result carries an `engines` list. Both search tools print it as an `Engines:` line after
  `Description:`.
- `assess_result_quality` and `QUALITY_THRESHOLD` are removed.
- Docs: the two tool instruction files, the README's engine section, `.env.example` and
  `docs/decision-log.md`.

### Non-goals

- No new engines and no changes to how each engine builds its request from the filters.
- No per-engine weighting or learned ranking. RRF treats every engine equally.
- No change to content extraction or `get_single_web_page_content`.
- No caching of engine results.

## Terms

- **Cheap engines**: BraveAPI (only when `BRAVE_API_KEY` is set), DDGS and DuckDuckGo HTML. They
  need only HTTP or the ddgs library, not a browser.
- **Fallback engine**: `BraveBrowserEngine` (name `Brave`), which scrapes search.brave.com in
  headless Firefox through Playwright.
- **RRF (reciprocal rank fusion)**: a URL's score is the sum of `1 / (k + rank)` over every engine
  list that contains it. `rank` starts at 1 and `k = 60`.
- **Normalized URL**: the key used to detect duplicates. The rules are in D2.
- **Occurrence**: one engine's result for one URL, with that engine's rank, title and description.
- **Engine label**: an engine's existing `name`: `BraveAPI`, `DDGS`, `DuckDuckGo` or `Brave`.

## Requirements

### R1 · Cheap engines are queried concurrently

All cheap engines start together, and the search waits at most `ENGINE_TIMEOUT_SECONDS` for them.
- **Given** three cheap engines that each take 1 s, **when** a search runs, **then** it finishes in well under 3 s.
- **Given** no `BRAVE_API_KEY`, **when** a search runs, **then** only DDGS and DuckDuckGo HTML are queried in parallel.

### R2 · A failing engine never sinks the search

An engine that raises an error or times out is logged as a warning with its name, and the results of
the other engines are still returned.
- **Given** one engine raises and another returns results, **when** a search runs, **then** the other engine's results are returned and a warning names the failed engine.
- **Given** one engine is slower than the timeout, **when** a search runs, **then** it returns after about the timeout with the other engines' results, and a warning says it timed out.
- **Given** every engine fails, **when** a search runs, **then** the response is a success with zero results, as it is today.

### R3 · Results are ranked by RRF and cut to the limit

The response lists merged results in descending RRF score and holds at most `filters.limit` of them.
- **Given** URL A ranked 2nd by two engines and URL B ranked 1st by one engine, **when** the lists are fused, **then** A comes before B.
- **Given** 3 engines returning 5 distinct URLs each and `limit` 5, **when** a search runs, **then** exactly 5 results are returned.

### R4 · No two results share a normalized URL

Results whose URLs normalize to the same key are merged into one result.
- **Given** `https://www.Example.com/a/?utm_source=x#top` from one engine and `https://example.com/a` from another, **when** a search runs, **then** one result is returned.
- **Given** `https://example.com/a?id=1` and `https://example.com/a?id=2`, **when** a search runs, **then** both are returned.

### R5 · A merged result keeps the best title and description

A merged result's title, description, URL and timestamp come from its occurrences by the rules in D3.
- **Given** occurrences with descriptions `""` and `"Full summary"`, **when** they merge, **then** the description is `"Full summary"`.

### R6 · Every result lists the engines that returned it

Each result has an `engines` list with the label of every engine that returned its URL, in the order
the engines are configured.
- **Given** BraveAPI and DDGS both return a URL, **when** a search runs, **then** that result's `engines` is `["BraveAPI", "DDGS"]`.

### R7 · The browser engine runs only when results are short

The fallback engine runs only when the fused cheap-engine results number fewer than `filters.limit`.
- **Given** the cheap engines return at least `limit` distinct URLs, **when** a search runs, **then** no browser page is opened.
- **Given** they return fewer, **when** a search runs, **then** the fallback runs and its results are fused with the rest.
- **Given** the fallback fails or times out, **when** a search runs, **then** the cheap engines' results are returned and a warning is logged.

### R8 · An engine that can't handle a source returns nothing

DuckDuckGo HTML and the Brave browser engine return an empty list for any source other than `web`.
BraveAPI keeps returning an empty list for `images` and `videos`.
- **Given** `source="news"`, **when** a search runs, **then** DuckDuckGo HTML and Brave browser return `[]` without making a request.

### R9 · Filters reach every engine as before

`recency_days`, `language` and `country` map to each engine's parameters exactly as `filters.py`
does today, and each engine is asked for `filters.limit` results.
- **Given** `recency_days=7`, **when** a search runs, **then** every engine gets the same request parameters it gets today.

### R10 · The tools show engines without changing existing fields

Both search tools print `Engines: <labels, comma-separated>` after each result's `Description:`
line. Every existing line and dict key stays as it is.
- **Given** a result from BraveAPI and DDGS, **when** `get_web_search_summaries` runs, **then** its text has `Engines: BraveAPI, DDGS`, and the service dict has `"engines": ["BraveAPI", "DDGS"]`.

### R11 · Tests run offline

Every new or changed test uses stubbed engines and needs no network. Live checks stay under
`-m live`.
- **Given** no network, **when** `uv run pytest` runs, **then** every test passes.

## Decisions

### D1 · Fuse with reciprocal rank fusion, k = 60

Score each normalized URL by RRF and sort descending. Ties go to the better best rank, then to the
earlier engine in configured order, so the output is deterministic. RRF needs only ranks, which
every engine provides, and rewards agreement between engines. Rejected: round-robin interleaving
(ignores agreement); score normalization (the engines expose no scores); per-engine weights
(nothing to tune them on yet). Details: notes.md#d1

### D2 · Normalized URLs are a dedupe key only

Normalize by lowercasing the scheme and host, dropping a leading `www.`, the default port, the
fragment, tracking parameters (`utm_*` and a fixed list of click ids) and a trailing `/` on the
path. Keep the remaining query parameters, sorted. The returned `url` is the original URL from the
best-ranked occurrence. Rejected: returning the normalized URL (dropping `www.` or `/` can change
what some servers serve). Details: notes.md#d2

### D3 · How a merged result picks its fields

The URL, title and timestamp come from the best-ranked occurrence, which is the lowest rank, with
ties going to engine order. If that title is empty, the next non-empty title is used. The
description is the longest non-empty one, because engines often truncate snippets. Rejected:
always preferring BraveAPI (it isn't always configured); merging descriptions (duplicated text).

### D4 · `asyncio.gather` with a per-engine `asyncio.wait_for`

Each engine call is wrapped in `wait_for(timeout)` and caught. The calls are gathered, so no engine
can cancel or block another. Rejected: `asyncio.TaskGroup` (one error cancels the siblings);
sequential calls (today's latency problem). ddgs runs in `asyncio.to_thread`, so a timeout
abandons its thread rather than stopping it. Details: notes.md#d4

### D5 · The browser engine as a separate fallback

`WebSearchService` holds `engines` (cheap, parallel) and `fallback_engine` (optional). Both can be
overridden in tests. The fallback gets a fixed 30 s timeout. Its list is fused as one more ranked
list, so it can fill gaps and add its label to existing results. Rejected: running it on every
search (a Firefox page load per query); running it only on zero results (the acceptance criterion
is "below the limit").

### D6 · Remove `assess_result_quality`

With fusion, nothing selects one engine's list, so the score has no decision left to make. Using
it as a tie-break or a filter would favor snippets that repeat the query words. It would also drop
image and video results, whose titles rarely contain the query. Cross-engine agreement in RRF is
the relevance signal now. Rejected: keeping it as a filter (drops valid non-text results); keeping
it as a tie-break (D1 already breaks ties).

### D7 · `ENGINE_TIMEOUT_SECONDS` setting, default 10 s

A new `WebSearchConfig.engine_timeout_seconds` field, read from the environment. Ten seconds
covers a normal API or ddgs call and stays under the 15 s HTTP timeout. Rejected: a hard-coded
constant (slow networks need a way to raise it without a code change).

### D8 · Fusion lives in a new `fusion.py`

`normalize_url` and `fuse_results` go in `features/web_search/fusion.py` as pure functions, so they
can be tested without the service. `SearchResult` gains `engines: List[str]`, defaulting to empty,
and `to_dict` already includes every field. Rejected: putting them in `service.py` (it mixes
orchestration and pure logic).

## Assumptions

- Each engine is still asked for `filters.limit` results, not more (R9). Asking for more could
  improve fusion, but it would change engine requests and quota use.
- Engine labels stay as they are (`DDGS`, not `ddgs`), because logs and tests already use them.
- The order of `engines` follows the configured order (BraveAPI, DDGS, DuckDuckGo, Brave), not the
  order in which engines happened to answer.
- A result with an empty URL is dropped before fusion, because it can't be deduplicated or fetched.
- The 30 s fallback timeout is a code constant. It can become a setting if anyone needs it.

## Risks

- A search waits for its slowest cheap engine, up to 10 s. Today it can stop after the first good
  engine. → Every engine already had to finish before the next started, so typical latency should
  fall. The timeout is configurable (D7).
- ddgs threads abandoned after a timeout keep running and hold executor workers. → Each one ends
  when its ddgs call returns. The default executor has at least 5 workers, and the server answers
  only a few searches at a time. Revisit if logs show repeated ddgs timeouts.
- News, image and video searches lose DuckDuckGo HTML as a last resort (R8). If DDGS fails, they
  return empty instead of off-type web pages. → An empty answer is more honest than results of
  the wrong type. This is recorded in the decision log.
- RRF can rank a URL that only one engine returned above others. → That is the expected behavior;
  tests pin the ordering on known inputs (R3).

## Rollout & rollback

No data or migrations. Ships in the next release and Docker image; the response change only adds
fields. Rollback: revert the PRs (details: notes.md#rollback).

## Open questions

- None

## Impact

- Packages / directories: `features/web_search/` (`service.py`, `engines.py`, `models.py`, new
  `fusion.py`, `tool.py`, `instructions.md`, `instructions_summaries.md`), `config.py`, `tests/`,
  `README.md`, `.env.example`, `docs/decision-log.md`
- Data: none
- Jobs / APIs: MCP tools `full_web_search` and `get_web_search_summaries` (additive output change)

## Links

- `docs/decision-log.md`: project-wide decisions. This plan adds one line on the response shape
  and one on non-web sources.

## Phases

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | Parallel engines with rank fusion | draft | 0/9 |
| 02 | Show engines in tool output and docs | draft | 0/5 |

## Decision log
