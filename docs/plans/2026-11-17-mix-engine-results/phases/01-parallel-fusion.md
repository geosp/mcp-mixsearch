---
phase: 1
title: Parallel engines with rank fusion
status: in-progress
branch: feat/mix-engine-results-p1
base: aa0407cd3bc4a6ead460697ed6216f60c3142fb3
delivers: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R11, R12]
design_review: { status: passed, rounds: 1, last: 2026-11-17 }
impl_review: { status: none, rounds: 0, last: null }
approved: 2026-11-17
---

# Phase 01 · Parallel engines with rank fusion

## Goal

The service queries the cheap engines in parallel, fuses their lists with RRF, removes duplicates
and tags each result with its engines. The browser engine runs only as a fallback. All tests are
offline.

## Tasks

### 1. Pure fusion logic

- [x] 1.1 Add `engines: List[str]` (default empty) to `SearchResult` (R6, D8). Verify: `to_dict()`
  includes `engines`, and the existing tests in `tests/test_engines.py` still pass.
- [x] 1.2 Add `features/web_search/fusion.py` with `normalize_url(url) -> str` by the rules in D2
  (notes.md#d2). Verify: `tests/test_fusion.py` covers every row of the notes table, plus a
  non-http URL.
- [x] 1.3 Add `fuse_results(lists: Sequence[Tuple[str, List[SearchResult]]]) -> List[SearchResult]`:
  drop empty URLs, dedupe within and across lists, score by RRF, pick fields by D3, fill `engines`
  in list order and sort by D1 (R3, R4, R5, R6). Verify: tests for the notes.md#d1 worked example,
  a tie-break, a same-engine duplicate, the D3 title and description picks, and empty input.

### 2. Engines

- [x] 2.1 `DuckDuckGoHtmlEngine` and `BraveBrowserEngine` return `[]` for a source other than `web`,
  before any request or page load (R8). Verify: tests in `tests/test_engines.py` for `news`,
  `images` and `videos` assert no HTTP call and no page opened.

### 3. Service

- [x] 3.1 Add `engine_timeout_seconds: float = 10.0` to `WebSearchConfig` and list
  `ENGINE_TIMEOUT_SECONDS` in its docstring (D7). Verify: `ENGINE_TIMEOUT_SECONDS=2` in the
  environment gives `2.0`.
- [x] 3.2 Split `_build_engines` into cheap `engines` and `fallback_engine`. Add a
  `fallback_engine` override to `WebSearchService.__init__`. When `engines=` is passed without it,
  there is no fallback (D5). Verify: an updated `test_engine_order_depends_on_brave_api_key`
  asserts `engines` are `[BraveAPI?, DDGS, DuckDuckGo]` and the fallback is `Brave`. A service
  built with only `engines=` has no fallback.
- [x] 3.3 Rewrite `_multi_engine_search` and its tests together (R1, R2, R3, R6, R7, R9, R11, R12,
  D4, D5, D6):
  - Service:
    - Gather the cheap engines with a per-engine `wait_for`, a warning for each failure or timeout,
      and an info log of count and duration (D4).
    - Fuse the lists. Run the fallback only when there are fewer than `limit` results, under a
      module constant `FALLBACK_TIMEOUT_SECONDS = 30.0`, then fuse again and cut to `limit`.
    - Add `"engines"` to the dicts that `search_summaries` builds by hand.
    - Remove `assess_result_quality` and `QUALITY_THRESHOLD`.
  - Tests in `tests/test_service.py`:
    - Remove `test_assess_result_quality`, its import, `test_first_good_engine_wins` and
      `test_best_effort_results_when_no_engine_meets_threshold`.
    - Make `result()` give each result its own URL (no shared default), so that
      `test_results_are_limited` still tests the limit under dedupe.
    - Let `make_service` accept a config and a `fallback_engine`.
  - New stubbed-engine tests:
    - Overlapping results are merged in RRF order with no duplicate URLs.
    - A raising engine and a slow engine (timeout 0.05 s) are skipped, and `caplog` shows the
      warnings.
    - Three 0.2 s engines finish in under 0.5 s.
    - The fallback isn't called at `limit` results, but is called below it.
    - A raising fallback, and a fallback past a monkeypatched timeout, are tolerated (R12).
    - All engines failing gives zero results.
    - `search_summaries` dicts include `engines`.
    - Each engine receives the same `SearchFilters` object (R9).

  Verify: `uv run pytest`.
- [x] 3.4 Update the module docstrings in `service.py` and `engines.py`, which still describe the
  sequential order. Verify: `grep -n "in order\|tries them" features/web_search/*.py` finds nothing
  stale.

### 4. Record and check

- [x] 4.1 Add two lines to `docs/decision-log.md`:
  - Search results are fused from several engines by RRF, and each result gains an `engines`
    list. Existing fields are unchanged.
  - DuckDuckGo HTML and the Brave browser engine answer `web` searches only.

  Then run the AGENTS.md checks (`uv sync --locked`, `ruff check`, `ruff format --check`, `mypy`,
  `pytest`, `sync_agents.py --check`). Verify: the lines are present and every check passes.
