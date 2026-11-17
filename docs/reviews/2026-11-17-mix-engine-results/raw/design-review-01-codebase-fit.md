## Design review: plan `2026-11-17-mix-engine-results` (plan.md, phases 01 and 02, notes.md)

The plan's claims about the code mostly hold. These all match the descriptions:
- `_multi_engine_search`, `assess_result_quality`, `QUALITY_THRESHOLD` and `_build_engines` (`features/web_search/service.py:33-49, 88-97, 159-191`), including the order `[BraveAPI?, DDGS, Brave, DuckDuckGo]` and the 15 s HTTP timeout.
- The engine names in `engines.py` (`"BraveAPI"`, `"DDGS"`, `"Brave"`, `"DuckDuckGo"`) and BraveAPI's early return for images and videos (`engines.py:55-56`).
- `SearchResult.to_dict` uses `asdict` (`models.py:29-31`).
- `WebSearchConfig` uses `extra="ignore"` (`config.py:23`).
- `.python-version` is 3.13, so `wait_for` raises the built-in `TimeoutError`.
- DDGS uses `asyncio.to_thread` (`engines.py:121`).
- The README section "Multi-Engine Architecture" exists (`README.md:95`), and `test_engine_order_depends_on_brave_api_key` exists (`tests/test_service.py:139`).
- The RRF example in the notes is arithmetically correct: C 0.032266 beats A 0.032258.

No ADRs were given, so ADR conformance was not checked.

### Major

**M1 · Phase 01 › Task 3.4 and notes.md "Current code, for reference": the plan undercounts the existing tests the change breaks.**
The notes say only `test_first_good_engine_wins` and `test_best_effort_results_when_no_engine_meets_threshold` are replaced. Two more break:
- **The module stops importing.** `tests/test_service.py:10` imports `assess_result_quality`, and `test_assess_result_quality` (`tests/test_service.py:44-48`) tests it. Task 3.3 removes the function, so the whole module fails at import.
- **`test_results_are_limited` fails under dedupe.** The test helper `result()` defaults every URL to `"https://example.com/"` (`tests/test_service.py:29-30`). `test_results_are_limited` (`:91-96`) returns 8 results with that one URL and asserts `total_results == 3`. After R4 dedupe they collapse to one result, so the test fails.

Task 3.4 should name these two tests, and either change the helper's default URL to be unique or delete the default.

**M2 · Decisions › D5 and Phase 01 › Task 3.2: the plan doesn't say which fallback is built when only `engines` is overridden.**
D5 says "Both can be overridden in tests", but not what happens when `engines=` is passed without `fallback_engine=`. If `_build_engines` still creates `BraveBrowserEngine(self.browser)` in that case, every existing `make_service` test runs the browser fallback against `FakeBrowser`:
- `make_service` passes only `engines` (`tests/test_service.py:33-41`).
- Most of these tests return fewer than the default limit of 5 (`filters.py:36`).
- `FakePage.evaluate_result` defaults to `None` (`tests/conftest.py:57-59`), so `BraveBrowserEngine.search` iterates `None` (`engines.py:169-173`), raises `TypeError` and logs a warning.

The tests still pass, but they exercise the fallback by accident, emit spurious warnings, and clash with `caplog` assertions on warnings. They also make "no browser page is opened" (R7) depend on the stub. The plan should state the rule. One option: when `engines` is given, `fallback_engine` defaults to `None` unless it is passed explicitly.

### Nits

- Phase 01 › Task 3.3: `search_summaries` builds its result dicts by hand (`service.py:126-135`), so `engines` is not added automatically. No task tells the implementer to add the key, although Task 3.4 tests it ("`search_summaries` dicts include `engines`") and R10 requires it.
- Phase 02 › Task 1.1: `FakeService` in `tests/test_tools.py:8-58` returns dicts without `engines`. `tool.py` should read the key with `.get("engines")`, or the fake must be updated; the task should say which.
- Phase 02 › Task 2.2: the stale-text check `grep -n "quality\|tried in order"` misses three spots that still describe single-engine selection:
  - `README.md:3`: "intelligent backend selection"
  - `README.md:80`: "Multi-engine search with intelligent backend selection"
  - `.env.example`: "as the first search engine"
- Phase 01 › Task 3.1: the `WebSearchConfig` docstring lists its environment variables (`config.py:17-20`) and should gain `ENGINE_TIMEOUT_SECONDS`. No task covers it.
- Phase 01 › Task 3.3: its verify step is "the tests in 3.4 pass", but 3.4 comes after it. AGENTS.md says "Tick a task only after its tests pass", so 3.3 and 3.4 have to land together; they should be merged or reordered.
- Phase 01 › Task 3.4: the "timeout set to 0.05 s" test needs `make_service` to accept a config. Today it hard-codes `WebSearchConfig(brave_api_key=None)` (`tests/test_service.py:36`). This is a small helper change the task doesn't mention.
- AGENTS.md "Record changes to … interfaces … in docs/decision-log.md": Phase 01 already changes behaviour (R8 drops non-web results, and the `engines` field is added). The decision-log lines only arrive in Phase 02 › Task 2.3, so if the phases ship as separate PRs, Phase 01 merges without its log entry.

Files referenced:
- /home/geo/develop/mcp-mixsearch/features/web_search/service.py
- /home/geo/develop/mcp-mixsearch/features/web_search/engines.py
- /home/geo/develop/mcp-mixsearch/features/web_search/models.py
- /home/geo/develop/mcp-mixsearch/features/web_search/tool.py
- /home/geo/develop/mcp-mixsearch/features/web_search/filters.py
- /home/geo/develop/mcp-mixsearch/config.py
- /home/geo/develop/mcp-mixsearch/tests/test_service.py
- /home/geo/develop/mcp-mixsearch/tests/test_tools.py
- /home/geo/develop/mcp-mixsearch/tests/conftest.py
- /home/geo/develop/mcp-mixsearch/README.md
- /home/geo/develop/mcp-mixsearch/.env.example
