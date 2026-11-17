## Phase 01 implementation review: the contract lens

**Scope:** `git diff aa0407cd..4f7d578` in /home/geo/develop/mcp-mixsearch, judged against plan.md (R1–R9, R11, R12, D1–D8) and phases/01-parallel-fusion.md (tasks 1.1–4.1).

**Verdict:** no Blocker or Major findings. The code keeps each delivered promise everywhere it applies. Most gaps are scenarios that only an indirect test covers, plus a few small normalization mismatches against the notes.md rules. All are listed below as Nits.

### Promise map (where it's enforced / which test fails without it)

All production code is under /home/geo/develop/mcp-mixsearch/features/web_search/. Test names refer to files under /home/geo/develop/mcp-mixsearch/tests/.

- **R1, running in parallel:** `asyncio.gather` over `_run_engine` (service.py `_multi_engine_search`). Test: `test_engines_run_concurrently` (three 0.2 s engines must finish in under 0.5 s).
- **R1, no key means only DDGS and DuckDuckGo:** `_build_engines`. Test: `test_engine_order_depends_on_brave_api_key`. This checks how the service is built, not which engines are called during a search. That is acceptable.
- **R2, raise or timeout:** `_run_engine` uses `wait_for`, catches `TimeoutError` and `Exception`, and logs a warning that names the engine. Test: `test_failing_and_slow_engines_are_logged_and_skipped`. Without the timeout, "too late" would show up in the results, so the test would fail.
- **R2, every engine fails:** `test_no_results_when_every_engine_fails`.
- **R3:** `fuse_results` sort plus `merged[: filters.limit]`. Tests: `test_fuse_worked_example_from_notes`, `test_agreement_beats_single_first_place`, `test_results_are_limited`.
- **R4:** `normalize_url` and the group key. Tests: `test_normalize_url` (every row of the notes table, plus non-http input), `test_duplicates_merge_across_and_within_engines`, `test_normalize_url_keeps_distinct_queries_apart`.
- **R5 / D3:** `_merge`. Tests: `test_field_picks`, `test_empty_title_falls_back_and_longest_description_wins`.
- **R6:** engine indexes are sorted in `_merge`, and `gather` keeps the configured order. Tests: the fusion tests, and service tests where `engines` is `["first","second"]` or `["cheap","Brave"]`.
- **R7:** `len(merged) < filters.limit and self.fallback_engine is not None`. Tests: `test_fallback_not_used_when_results_reach_limit`, `test_fallback_fills_short_results`.
- **R8:** an early `return []` in `BraveBrowserEngine.search` and `DuckDuckGoHtmlEngine.search`, before the URL is built or any request or page is made (engines.py around lines 159 and 222). Test: `test_scraping_engines_answer_web_only`, parametrized over news, images and videos; it asserts no HTTP request and no page opened.
- **R9:** the same `filters` object goes to the gather calls and to the fallback. Test: `test_every_engine_gets_the_same_filters`, which includes the fallback.
- **R11:** every new test uses `FakeEngine`, `FakeBrowser` or `mock_client`. `test_engine_timeout_from_environment` calls `WebSearchService()`, the same way the existing `test_allow_private_urls_from_environment` does. Nothing there opens a network connection.
- **R12:** the fallback also goes through `_run_engine`, with the module global `FALLBACK_TIMEOUT_SECONDS` read when the call runs, so a monkeypatch takes effect. Tests: `test_failing_fallback_keeps_cheap_results`, `test_slow_fallback_times_out`.
- **D1:** sort key `(-score, best.rank, best.engine_index)`, with `RRF_K = 60`.
- **D2:** fusion.py `normalize_url`.
- **D4:** a per-engine `wait_for` inside `gather`, a warning on each failure, and an info log of count and duration.
- **D5:** the `__init__` branch. Tests: `test_engines_override_has_no_fallback_by_default` and the engine-order test.
- **D6:** the function and the constant are removed; grep finds no references.
- **D7:** `config.py` `engine_timeout_seconds` (`gt=0`). Test: `test_engine_timeout_from_environment`.
- **D8:** fusion.py exists, and `SearchResult.engines` defaults to an empty list. Test: `test_search_result_to_dict_includes_engines`.

**Universal claims checked:**
- **"Every engine" receives the filters (R9):** both call sites (the cheap-engine gather and the fallback) pass the same object. No gap.
- **"Never sinks the search" (R2/R12):** both engine call sites go through `_run_engine`. Code that runs after those calls is not protected (see the `fuse_results` Nit below).
- **"Before making a request" (R8):** both engines return before building the URL. No gap.
- **"Every result lists its engines" (R6):** covered on both paths. `search_summaries` builds its dicts by hand and now adds `engines`. `search_and_extract` uses `to_dict()` and changes the fused results in place, so `engines` survives. Covered by `test_search_and_extract_results_include_engines`.

### Findings

No Blocker or Major findings.

### Nits (one line each)

- **test_service.py, R6:** No service test has engines answering out of configured order (for example, the first engine delayed). The R6 scenario "DDGS answers before BraveAPI" is therefore unobserved. A switch to `as_completed` would still pass every test, because the test engines finish in list order with no delays.
- **test_service.py, R3:** The scenario "3 engines × 5 distinct URLs, limit 5 gives exactly 5" is tested only with one engine of 8 results (`test_results_are_limited`). The cut after fusing several engines is the same line of code, so the risk is low.
- **test_fusion.py, R4:** The scenario that `?id=1` and `?id=2` are both returned is checked only at `normalize_url` level, not through `fuse_results`. Low risk.
- **test_service.py, R2:** `test_failing_and_slow_engines_are_logged_and_skipped` doesn't check elapsed time, so "returns after about the timeout" is only implied by the missing "too late" result. A wall-clock bound (for example, under 0.5 s) would observe it directly.
- **fusion.py, D1:** `test_ties_go_to_best_rank_then_engine_order` only exercises the engine-order tie-break; nothing checks the best-rank tie-break on its own. Equal float scores with different best ranks are practically unreachable, so the tie-break is close to dead and very hard to test.
- **service.py `_run_engine`, D4:** Nothing checks the info log of count and duration (`caplog` is set to WARNING in every test). A test at INFO level could check it.
- **fusion.py `normalize_url`, D2 / notes.md rule 5:** `path.rstrip("/")` strips every trailing slash, so `/a//` becomes `/a`. The notes say "Strip a trailing `/`". The effect is only a looser dedupe key.
- **fusion.py `normalize_url`, D2:** The key is built from `parts.hostname`, which drops any `user:pass@` part. As a result, `https://u@example.com/x` and `https://example.com/x` merge. The notes don't cover this; it's rare.
- **fusion.py `normalize_url`, D2:** An IPv6 host loses its brackets: `http://[::1]:8080/` gives host `::1:8080`, which reads the same as the bare host `::1:8080`. In theory two different URLs could share a key; this is only a dedupe key.
- **fusion.py `_is_tracking_param`, D2:** Tracking keys are matched case-insensitively (`UTM_Medium`, `GCLID` are dropped), while the notes list lowercase keys and say "starts with `utm_`". This goes beyond the notes, and the test (`UTM_Medium`) pins it. It's arguably fine, but it isn't in the contract.
- **fusion.py `_merge`, D3:** A title made only of whitespace counts as "non-empty", so it would win over a real title from a lower-ranked occurrence. The contract says "non-empty", which is ambiguous here.
- **fusion.py `fuse_results` line 124, R2:** `result.url.strip()` runs outside any per-engine `try`. engines.py uses `item.get("url", "")` (lines 72, 86, 92, 95, 97), which returns `None` when the JSON has `"url": null`. Such an item would raise `AttributeError` and fail the whole search, not just skip one engine. This needs a malformed engine payload, so it's unlikely, but R2 says "never". A test: a `FakeEngine` returning `SearchResult(url=None)` next to a good engine.
- **service.py `_run_engine`, D4:** `except TimeoutError` also catches a builtin `TimeoutError` raised inside an engine and logs it as "timed out after Ns". This only makes the log misleading, and none of the current engines' libraries raise the builtin, as far as I checked.
- **service.py `_multi_engine_search`, R7/R8:** For a short news, image or video search, the fallback is still "run" and logs "trying Brave", even though it returns `[]` right away. It's harmless, but the log is noise.
- **README.md:96, scope:** It still says "Engines are tried in order …". Docs belong to phase 02 (R10), so this is expected for now and listed so it isn't lost.

No other mismatches found. The decision-log lines (task 4.1) are present, the docstrings (task 3.4) are updated, and all 9 tasks are ticked, matching the plan table's 9/9.
