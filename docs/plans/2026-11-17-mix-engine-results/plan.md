---
title: Mix results from several search engines
status: draft
created: 2026-11-17
updated: 2026-11-17
design_review: { status: passed, rounds: 1, last: 2026-11-17 }
approved: null
adr_review: null
---

# Mix results from several search engines

## Summary

Despite its name, mcp-mixsearch returns one engine's results only: the first list scoring at least
0.3 on a word-overlap check. This plan runs the cheap engines (BraveAPI when a key is set, DDGS,
DuckDuckGo HTML) in parallel under a new `ENGINE_TIMEOUT_SECONDS` (10 s). It fuses their ranked
lists with reciprocal rank fusion, merges duplicate URLs and tags each result with its engines. The
Playwright Brave engine runs only when fewer than `limit` results come back. The word-overlap
check is removed (D6). `full_web_search` and `get_web_search_summaries` gain an `Engines:` line.
DuckDuckGo HTML and the browser engine stop answering news, image and video searches (R8).

```text
query ─┬─ BraveAPI ──┐  10 s each; failures logged and skipped
       ├─ DDGS ──────┼─► fuse (dedupe + RRF) ─► fewer than limit? ─yes─► Brave browser (30 s) ─► fuse again
       └─ DuckDuckGo ┘                                            └─no──► top `limit`
```

Main costs: a typical search gets slower, because it waits for the slowest cheap engine (worst
case ~40 s with the fallback). Each search also sends 2–3× more outbound requests. See Risks.

## Why

`WebSearchService._multi_engine_search` in `features/web_search/service.py` tries the engines one
at a time and returns the first list whose `assess_result_quality` score is at least 0.3. So results
never combine sources, and a slow or broken engine early in the order delays every search by up to
the 15 s HTTP timeout. The score only counts query words in titles and descriptions, which rewards
keyword-stuffed snippets and ignores rank. Agreement between engines is a better relevance signal,
and the cheap engines can run together.

## What changes

- The cheap engines run concurrently, each under `ENGINE_TIMEOUT_SECONDS`.
- Their lists are fused (dedupe by normalized URL, then RRF) and cut to `limit`.
- The Brave browser engine becomes a fallback for short result lists.
- DuckDuckGo HTML and the Brave browser engine return nothing for non-web sources (R8).
- Every result carries an `engines` list, shown in both tools' text as an `Engines:` line.
- `assess_result_quality` and `QUALITY_THRESHOLD` are removed.
- Docs: the tool descriptions (`instructions*.md`), README, `.env.example`, `docs/decision-log.md`.

### Non-goals

- No new engines, no change to how engines build requests, and no per-engine weighting.
- No change to content extraction, and no caching or rate limiting of our own.

## Terms

- **Filters**: the `SearchFilters` object built from the tool arguments `limit` (1–10 results),
  `source` (`web`, `news`, `images` or `videos`), `recency_days`, `language` and `country`.
- **Cheap engines**: BraveAPI (only with `BRAVE_API_KEY`), DDGS (ddgs metasearch library) and
  DuckDuckGo HTML (scrapes html.duckduckgo.com). None needs a browser.
- **Fallback engine** ("the browser engine"): `BraveBrowserEngine`, labeled `Brave`, scraping
  search.brave.com in headless Firefox through Playwright.
- **Engine label**: an engine's existing `name`: `BraveAPI`, `DDGS`, `DuckDuckGo` or `Brave`.
- **RRF (reciprocal rank fusion)**: a URL's score is the sum of `1 / (k + rank)` over every engine
  list that contains it. `rank` starts at 1 and `k = 60`.
- **Normalized URL**: the key used to detect duplicates (D2).
- **Occurrence**: one engine's result for one URL: rank, title, description, timestamp.
- **Live tests**: tests marked `live` that hit real engines; skipped unless run with `-m live`.

## Requirements

### R1 · Cheap engines are queried concurrently

All cheap engines start together, and the search waits at most `ENGINE_TIMEOUT_SECONDS` for them.
- **Given** three cheap engines that each take 1 s, **when** a search runs, **then** it finishes in well under 3 s.
- **Given** no `BRAVE_API_KEY`, **when** a search runs, **then** only DDGS and DuckDuckGo HTML are queried.

### R2 · A failing engine never sinks the search

An engine that raises or times out is logged as a warning with its name, and the other engines'
results are still returned.
- **Given** one engine raises and another returns results, **when** a search runs, **then** the other engine's results are returned and a warning names the failed engine.
- **Given** one engine is slower than the timeout, **when** a search runs, **then** it returns after about the timeout with the other engines' results, and a warning says it timed out.
- **Given** every engine fails, **when** a search runs, **then** the response is a success with zero results, as it is today.

### R3 · Results are ranked by RRF and cut to the limit

The response lists merged results in descending RRF score, at most `limit` of them.
- **Given** URL A ranked 2nd by two engines and URL B ranked 1st by one engine, **when** the lists are fused, **then** A comes before B.
- **Given** 3 engines returning 5 distinct URLs each and `limit` 5, **when** a search runs, **then** exactly 5 results are returned.

### R4 · No two results share a normalized URL

Results whose URLs normalize to the same key are merged into one result.
- **Given** `https://www.Example.com/a/?utm_source=x#top` from one engine and `https://example.com/a` from another, **when** a search runs, **then** one result is returned.
- **Given** `https://example.com/a?id=1` and `https://example.com/a?id=2`, **when** a search runs, **then** both are returned.

### R5 · A merged result keeps the best title and description

A merged result's URL, title, description and timestamp are picked from its occurrences by D3.
- **Given** occurrences with descriptions `""` and `"Full summary"`, **when** they merge, **then** the description is `"Full summary"`.

### R6 · Every result lists the engines that returned it

Each result's `engines` holds the label of every engine that returned its URL, in configured
engine order (BraveAPI, DDGS, DuckDuckGo, Brave), not in order of response.
- **Given** DDGS answers before BraveAPI and both return a URL, **when** a search runs, **then** that result's `engines` is `["BraveAPI", "DDGS"]`.

### R7 · The browser engine runs only when results are short

The fallback engine runs only when the fused cheap-engine results number fewer than `limit`.
- **Given** the cheap engines return at least `limit` distinct URLs, **when** a search runs, **then** no browser page is opened.
- **Given** they return fewer, **when** a search runs, **then** the fallback runs and its results are fused with the rest.

### R8 · An engine that can't handle a source returns nothing

DuckDuckGo HTML and the browser engine return `[]` for any source other than `web`, before making
a request, because they can't search other types and their web pages would pollute fused results.
- **Given** `source="news"`, **when** a search runs, **then** DuckDuckGo HTML and the browser engine return `[]` without a request or page load.

### R9 · Filters reach every engine as before

Every engine receives the same request parameters from the filters as it does today, including a
request for `limit` results.
- **Given** `recency_days=7` and `limit=3`, **when** a search runs, **then** every engine gets the same parameters it gets today.

### R10 · The tools show engines without changing existing fields

Both tools print `Engines: <labels, comma-separated>` after each result's `Description:` line,
and every existing line and result key stays as it is.
- **Given** a result from BraveAPI and DDGS, **when** `get_web_search_summaries` runs, **then** its text has `Engines: BraveAPI, DDGS` and the service result has `"engines": ["BraveAPI", "DDGS"]`.

### R11 · Tests run offline

Every new or changed test uses stubbed engines and needs no network; live tests stay opt-in.
- **Given** no network, **when** `uv run pytest` runs, **then** every test passes.

### R12 · A failing fallback never sinks the search

If the browser engine raises or exceeds its 30 s timeout, the cheap engines' results are returned
and a warning is logged.
- **Given** the cheap engines return 2 results, `limit` is 5 and the fallback times out, **when** a search runs, **then** the 2 results are returned and a warning names `Brave`.

## Decisions

### D1 · Fuse with reciprocal rank fusion, k = 60

Score each normalized URL by RRF and sort descending. Ties go to the URL with the better best rank,
then to the URL whose best-ranked occurrence came from the earlier configured engine. RRF needs
only ranks, which every engine gives, and rewards agreement. Rejected: round-robin interleaving
(ignores agreement); score normalization (engines expose no scores); per-engine weights (nothing to
tune them on yet). Details: notes.md#d1

### D2 · Normalized URLs are a dedupe key only

Normalize by lowercasing the scheme and host and dropping a leading `www.`, the default port, the
fragment, tracking parameters and a trailing `/`. The remaining query parameters are kept, sorted.
The returned `url` is the original URL from the best-ranked occurrence. Rejected: returning the
normalized URL (dropping `www.` or `/` can change what some servers serve). The exact rules and
the tracking-parameter list: notes.md#d2

### D3 · How a merged result picks its fields

The best-ranked occurrence is the one with the smallest rank number, with ties going to configured
engine order. URL and timestamp come from it. The title comes from it too, or from the next
occurrence with a non-empty title. The description is the longest non-empty one, because engines
often truncate snippets. Rejected: always preferring BraveAPI (it isn't always configured);
concatenating descriptions (duplicate text).

### D4 · `asyncio.gather` with a per-engine `asyncio.wait_for`

Each engine call is wrapped in `wait_for(timeout)` and caught, then all are gathered, so no engine
can cancel or block another; each logs its count and duration. A DDGS timeout abandons its thread.
Rejected: `asyncio.TaskGroup` (one error cancels the siblings); sequential calls (today's latency
problem). Details: notes.md#d4

### D5 · The browser engine as a separate fallback

`WebSearchService` holds `engines` (cheap, parallel) and `fallback_engine`. Tests that pass
`engines=` without `fallback_engine=` get no fallback, so stubs never reach the real browser
engine. Its timeout is a module constant (30 s), and its list is fused as one more. Rejected:
running it on every search (a Firefox page load per query); only on zero results (the goal is a
full `limit`).

### D6 · Remove `assess_result_quality`

Fusion never selects one engine's list, so the score has no decision left to make; agreement in
RRF replaces it. It never appeared in tool output. Rejected: keeping it as a filter (drops image and
video results, whose titles rarely contain the query); as a tie-break (favors keyword-stuffed snippets).

### D7 · `ENGINE_TIMEOUT_SECONDS` setting, default 10 s

A new `WebSearchConfig.engine_timeout_seconds` field; 10 s covers a normal API or DDGS call. Above
15 s only DDGS benefits, since the HTTP client times out at 15 s. Rejected: a hard-coded constant
(slow networks need a way to raise it without a code change).

### D8 · Fusion lives in a new `fusion.py`

`normalize_url` and `fuse_results` go in `features/web_search/fusion.py` as pure functions, next to
the other pure helpers (`filters.py`, `url_safety.py`). `SearchResult` gains `engines: List[str]`,
default empty. Rejected: putting them in `service.py` (it mixes orchestration and pure logic).

## Assumptions

- Each engine is asked for `limit` results, not more (R9). Asking for more could improve fusion,
  but it would change engine requests and quota use.
- Engine labels stay as they are (`DDGS`, not `ddgs`), because logs and tests already use them.
- A result with an empty URL is dropped before fusion, because it can't be deduplicated or fetched.

## Risks

Evidence: notes.md#risks.
- **A typical search gets slower:** it waits for the slowest cheap engine, up to 10 s, instead of
  stopping at the first good one. → Accepted for mixed results; a failing engine no longer delays
  the next. The timeout is configurable (D7), and durations are logged (D4).
- **The worst case is ~40 s** (10 s plus 30 s for the fallback). → The fallback runs only on short
  lists (R7). Today's worst case is four engines in sequence, up to 15 s each.
- **2–3× more outbound requests per search,** and DuckDuckGo HTML may rate-limit. → A blocked
  engine is logged and skipped (R2). Failure counts in the logs show when to drop it.
- **Abandoned DDGS threads hold workers** that content extraction shares. → Each ends when ddgs's
  own timeouts fire. Revisit if logs show repeated DDGS timeouts.
- **Correlated votes:** DDGS `auto` queries DuckDuckGo and Brave too. → Still filters outliers.
- **News, image and video searches lose two last-resort engines (R8).** → An empty answer is more
  honest than off-type pages. Recorded in the project decision log.

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

- `docs/decision-log.md`: the project-wide log; this plan adds lines there. Changes to this plan
  after approval go in its own Decision log below.

## Phases

Tasks live in `phases/NN-*.md`. Phase 01: search behavior (R1–R9, R11, R12). Phase 02: tool text, docs (R10).

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | Parallel engines with rank fusion | draft | 0/9 |
| 02 | Show engines in tool output and docs | draft | 0/4 |

## Decision log
