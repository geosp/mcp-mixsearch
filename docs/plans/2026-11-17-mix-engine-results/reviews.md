# Reviews · Mix results from several search engines

## 2026-11-17 · design-review · whole plan · round 1 · changes-requested
Commit: 5aa300e6cfb54ddf3267aac5810ffc5d329f0cd4 (clean-checkout checks passed before the round)
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅
Raw reports: docs/reviews/2026-11-17-mix-engine-results/raw/design-review-01-*.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | zoom out, fresh reader | Risks says typical latency falls; it rises to max(cheap engines) when the first engine used to succeed; Summary contradicts Risks | fixed: Summary, Risks 1 |
| F2 | Major | zoom out | Extra outbound requests per search (DDG HTML, DDGS every time) and rate-limit risk missing from Risks | fixed: Risks 3, notes.md#risks |
| F3 | Major | fresh reader | Summary omits the R8 user-visible change (non-web sources lose two engines) | fixed: Summary |
| F4 | Major | fresh reader | Worst case ~40 s (10 s cheap + 30 s fallback) not stated in Summary or Risks | fixed: Summary, Risks 2 |
| F5 | Major | fresh reader | R8 has no stated goal in plan.md (why non-web must return nothing) | fixed: R8 |
| F6 | Major | fresh reader | D2 click-id list lives only in notes.md; D2 not implementable from plan.md alone | contested: mechanics belong in notes.md (writing.md); D2 links it and task 1.2 cites it |
| F7 | Major | fresh reader | Phases table doesn't say where tasks live or which requirements each phase delivers | fixed: Phases intro |
| F8 | Major | codebase fit | Task 3.4 misses broken tests: `assess_result_quality` import/test, and `test_results_are_limited` (shared default URL collapses under dedupe) | fixed: phase 01 task 3.3, notes.md current code |
| F9 | Major | codebase fit, zoom out | D5 doesn't say which fallback is used when only `engines=` is overridden; tests would hit real BraveBrowserEngine on FakeBrowser | fixed: D5, phase 01 task 3.2 |
| F10 | Nit | codebase fit, zoom out | `search_summaries` builds dicts by hand; no task adds `engines` | fixed: phase 01 task 3.3 |
| F11 | Nit | codebase fit | Phase 02 1.1: `FakeService` in test_tools lacks `engines`; say `.get` or update fake | fixed: phase 02 task 1.1 |
| F12 | Nit | codebase fit | Phase 02 2.2 grep misses README:3, README:80, .env.example "first search engine" | fixed: phase 02 task 2.2 |
| F13 | Nit | codebase fit | `WebSearchConfig` docstring env var list needs ENGINE_TIMEOUT_SECONDS | fixed: phase 01 task 3.1 |
| F14 | Nit | codebase fit | Task 3.3 verify depends on later 3.4; merge or reorder | fixed: phase 01 tasks 3.3+3.4 merged |
| F15 | Nit | codebase fit | `make_service` hard-codes config; timeout test needs it to accept one | fixed: phase 01 task 3.3 |
| F16 | Nit | codebase fit | Decision-log lines land in phase 02 though phase 01 changes behavior | fixed: phase 01 task 4.1 (phase 02 task 2.3 adds the text-line entry) |
| F17 | Nit | zoom out | No test for fallback timeout; make 30 s a module constant | fixed: D5, R12, phase 01 task 3.3 |
| F18 | Nit | zoom out | Per-engine count/duration info logs (notes D4) have no task; Risks relies on them | fixed: D4, phase 01 task 3.3 |
| F19 | Nit | zoom out | Abandoned ddgs threads share the default executor with extraction's to_thread | fixed: Risks 4, notes.md#risks |
| F20 | Nit | zoom out | DDGS `auto` already queries duckduckgo/brave; engine votes may be correlated | fixed: Risks 5 |
| F21 | Nit | zoom out, fresh reader | Empty "Decision log" heading looks unfinished | contested: template convention; filled after approval (Links now says so) |
| F22 | Nit | fresh reader | Summary: diagram splits dedupe/RRF; sentence fragment; "clears" phrasing; tools and ENGINE_TIMEOUT_SECONDS unnamed | fixed: Summary |
| F23 | Nit | fresh reader | Undefined: filters/limit, source, timestamp, `-m live`, instruction files; browser engine has four names | fixed: Terms |
| F24 | Nit | fresh reader | D1 tie-break engine and D3 "lowest rank" ambiguous; no timestamp fallback | fixed: D1, D3 |
| F25 | Nit | fresh reader | Assumptions restate R6, R9 and D5 | fixed: Assumptions |
| F26 | Nit | fresh reader | R1, R2, R3, R7, R8, R9, R10, R11 each hold more than one rule | accepted: split only R7 (new R12); others are one behavior with edge cases |
| F27 | Nit | fresh reader | R10 vs D6: unclear whether the quality score is exposed in output | contested: score never in tool output (D6 says so) |
| F28 | Nit | fresh reader | D5 cites "the acceptance criterion" with no source | fixed: D5 |
| F29 | Nit | fresh reader | D7: what if the setting exceeds the 15 s HTTP timeout | fixed: D7 |
| F30 | Nit | fresh reader | Links' decision-log vs plan's Decision log not distinguished | fixed: Links |

## 2026-11-17 · approved · whole plan (phases 01, 02)

## 2026-11-17 · impl-review · phase 01 · round 1 · passed
Diff: aa0407cd3bc4a6ead460697ed6216f60c3142fb3..4f7d578b94c92400a468a1cb26b8e18cc11d113f
Reviewers: contract ✅ (profile `small`: contract lens only)
Raw report: docs/reviews/2026-11-17-mix-engine-results/raw/impl-review-01-r1-contract.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| I1 | Nit | contract | R2: an engine result with `url=None` raises in `fuse_results`, outside the per-engine try, and sinks the search | fixed: test_missing_url_is_dropped, test_engine_with_missing_url_does_not_sink_search; fusion.py |
| I2 | Nit | contract | R6: no service test has engines answering out of configured order | fixed: test_engines_listed_in_configured_order_not_response_order (catches an as_completed mutant) |
| I3 | Nit | contract | R3: "3 engines × 5 URLs, limit 5" scenario only tested with one engine | fixed: test_three_engines_cut_to_limit |
| I4 | Nit | contract | R4: `?id=1`/`?id=2` kept apart only tested at `normalize_url`, not through fusion | fixed: test_different_query_values_stay_separate_results |
| I5 | Nit | contract | R2: timeout test doesn't bound elapsed time | fixed: elapsed bound in test_failing_and_slow_engines_are_logged_and_skipped |
| I6 | Nit | contract | D4: per-engine count/duration info log untested | fixed: info-log assertion in the same test |
| I7 | Nit | contract | D2: `rstrip("/")` strips every trailing slash, notes say one | fixed: normalize_url row `/a//`; fusion.py strips one slash |
| I8 | Nit | contract | D3: a whitespace-only title counts as non-empty | fixed: test_whitespace_title_counts_as_empty; fusion.py |
| I9 | Nit | contract | D1: best-rank tie-break not tested on its own (near-unreachable with float scores) | accepted: equal float scores with different best ranks are near-unreachable |
| I10 | Nit | contract | D2: userinfo dropped from key; IPv6 brackets lost | accepted: dedupe key only; rare inputs |
| I11 | Nit | contract | D2: tracking keys matched case-insensitively, beyond notes | accepted: desirable; recorded in notes.md#d2 |
| I12 | Nit | contract | D4: an engine-raised builtin TimeoutError is logged as "timed out" | accepted: no current engine library raises builtin TimeoutError |
| I13 | Nit | contract | R7/R8: fallback "runs" and logs for non-web short searches though it returns [] at once | fixed: test_fallback_skipped_for_non_web_sources; service.py; D5 + plan Decision log |
| I14 | Nit | contract | README still says engines are tried in order (phase 02 scope) | accepted: phase 02 task 2.2 |

## 2026-11-17 · done · phase 01
Manual check: docs/demos/2026-11-17-mix-engine-results-p1/README.md (owner ran `uv run pytest -m live`: 3 passed, 1 skipped for no BRAVE_API_KEY).

## 2026-11-17 · impl-review · phase 02 · round 1 · passed
Diff: 6e49df85c83f9fbe41f96327b7378e8ebe4e43ac..215b063ba2a0dc21be5492649836b477032458a2
Reviewers: contract ✅ (profile `small`: contract lens only)
Raw report: docs/reviews/2026-11-17-mix-engine-results/raw/impl-review-02-r1-contract.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| J1 | Nit | contract | README says URL case is ignored in dedupe; only scheme and host are lowercased (D2) | open |
| J2 | Nit | contract | R10: missing `engines` key tested only for summaries, not `full_web_search` | open |
| J3 | Nit | contract | Task 2.3: clean-checkout check has no evidence in the diff | open |
| J4 | Nit | contract | instructions.md `source` section doesn't say non-web searches use fewer engines (R8) | open |
| J5 | Nit | contract | Phase status still in-progress with 4/4 tasks | open |
