---
phase: 1
title: Parallel engines with rank fusion
status: draft
branch: null
base: null
delivers: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R11]
design_review: { status: changes-requested, rounds: 1, last: 2026-11-17 }
impl_review: { status: none, rounds: 0, last: null }
approved: null
---

# Phase 01 · Parallel engines with rank fusion

## Goal

The service queries the cheap engines in parallel, fuses their lists with RRF, removes duplicates
and tags each result with its engines. The browser engine runs only as a fallback. All tests are
offline.

## Tasks

### 1. Pure fusion logic

- [ ] 1.1 Add `engines: List[str]` (default empty) to `SearchResult` (R6, D8). Verify: `to_dict()`
  includes `engines`, and the existing tests in `tests/test_engines.py` still pass.
- [ ] 1.2 Add `features/web_search/fusion.py` with `normalize_url(url) -> str` by the rules in D2
  (notes.md#d2). Verify: `tests/test_fusion.py` covers every row of the notes table, plus a
  non-http URL.
- [ ] 1.3 Add `fuse_results(lists: Sequence[Tuple[str, List[SearchResult]]]) -> List[SearchResult]`:
  drop empty URLs, dedupe within and across lists, score by RRF, pick fields by D3, fill `engines`
  in list order and sort by D1 (R3, R4, R5, R6). Verify: tests for the notes.md#d1 worked example,
  a tie-break, a same-engine duplicate, the D3 title and description picks, and empty input.

### 2. Engines

- [ ] 2.1 `DuckDuckGoHtmlEngine` and `BraveBrowserEngine` return `[]` for a source other than `web`,
  before any request or page load (R8). Verify: tests in `tests/test_engines.py` for `news`,
  `images` and `videos` assert no HTTP call and no page opened.

### 3. Service

- [ ] 3.1 Add `engine_timeout_seconds: float = 10.0` to `WebSearchConfig` (D7). Verify:
  `ENGINE_TIMEOUT_SECONDS=2` in the environment gives `2.0`.
- [ ] 3.2 Split `_build_engines` into cheap `engines` and `fallback_engine`, and add a
  `fallback_engine` override to `WebSearchService.__init__` (D5). Verify: an updated
  `test_engine_order_depends_on_brave_api_key` asserts `engines` are `[BraveAPI?, DDGS, DuckDuckGo]`
  and the fallback is `Brave`.
- [ ] 3.3 Rewrite `_multi_engine_search`: gather the cheap engines with per-engine `wait_for` and
  logging (D4), fuse them, run the fallback with a 30 s timeout only when there are fewer than
  `limit` results, fuse again and cut to `limit`. Remove `assess_result_quality` and
  `QUALITY_THRESHOLD` (R1, R2, R3, R7, D5, D6). Verify: the tests in 3.4 pass.
- [ ] 3.4 Replace the selection tests in `tests/test_service.py` with stubbed-engine tests:
  overlapping results merged in RRF order with no duplicate URLs; a raising engine and a slow
  engine (timeout set to 0.05 s) are logged and skipped, checked with `caplog`; engines run
  concurrently (three 0.2 s engines finish in under 0.5 s); the fallback is not called at `limit`
  results but is called below it, and its failure is tolerated; all engines failing gives zero
  results; `search_summaries` dicts include `engines`; filters reach each engine unchanged (R9)
  (R1–R7, R9, R11). Verify: `uv run pytest`.
- [ ] 3.5 Update the module docstrings in `service.py` and `engines.py`, which still describe the
  sequential order. Verify: run the AGENTS.md checks (`ruff check`, `ruff format --check`, `mypy`,
  `pytest`, `sync_agents.py --check`). All pass.
