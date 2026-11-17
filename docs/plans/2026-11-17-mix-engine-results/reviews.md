# Reviews · Mix results from several search engines

## 2026-11-17 · design-review · whole plan · round 1 · changes-requested
Commit: 5aa300e6cfb54ddf3267aac5810ffc5d329f0cd4 (clean-checkout checks passed before the round)
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅
Raw reports: docs/reviews/2026-11-17-mix-engine-results/raw/design-review-01-*.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | zoom out, fresh reader | Risks says typical latency falls; it rises to max(cheap engines) when the first engine used to succeed; Summary contradicts Risks | open |
| F2 | Major | zoom out | Extra outbound requests per search (DDG HTML, DDGS every time) and rate-limit risk missing from Risks | open |
| F3 | Major | fresh reader | Summary omits the R8 user-visible change (non-web sources lose two engines) | open |
| F4 | Major | fresh reader | Worst case ~40 s (10 s cheap + 30 s fallback) not stated in Summary or Risks | open |
| F5 | Major | fresh reader | R8 has no stated goal in plan.md (why non-web must return nothing) | open |
| F6 | Major | fresh reader | D2 click-id list lives only in notes.md; D2 not implementable from plan.md alone | open |
| F7 | Major | fresh reader | Phases table doesn't say where tasks live or which requirements each phase delivers | open |
| F8 | Major | codebase fit | Task 3.4 misses broken tests: `assess_result_quality` import/test, and `test_results_are_limited` (shared default URL collapses under dedupe) | open |
| F9 | Major | codebase fit, zoom out | D5 doesn't say which fallback is used when only `engines=` is overridden; tests would hit real BraveBrowserEngine on FakeBrowser | open |
| F10 | Nit | codebase fit, zoom out | `search_summaries` builds dicts by hand; no task adds `engines` | open |
| F11 | Nit | codebase fit | Phase 02 1.1: `FakeService` in test_tools lacks `engines`; say `.get` or update fake | open |
| F12 | Nit | codebase fit | Phase 02 2.2 grep misses README:3, README:80, .env.example "first search engine" | open |
| F13 | Nit | codebase fit | `WebSearchConfig` docstring env var list needs ENGINE_TIMEOUT_SECONDS | open |
| F14 | Nit | codebase fit | Task 3.3 verify depends on later 3.4; merge or reorder | open |
| F15 | Nit | codebase fit | `make_service` hard-codes config; timeout test needs it to accept one | open |
| F16 | Nit | codebase fit | Decision-log lines land in phase 02 though phase 01 changes behavior | open |
| F17 | Nit | zoom out | No test for fallback timeout; make 30 s a module constant | open |
| F18 | Nit | zoom out | Per-engine count/duration info logs (notes D4) have no task; Risks relies on them | open |
| F19 | Nit | zoom out | Abandoned ddgs threads share the default executor with extraction's to_thread | open |
| F20 | Nit | zoom out | DDGS `auto` already queries duckduckgo/brave; engine votes may be correlated | open |
| F21 | Nit | zoom out, fresh reader | Empty "Decision log" heading looks unfinished | open |
| F22 | Nit | fresh reader | Summary: diagram splits dedupe/RRF; sentence fragment; "clears" phrasing; tools and ENGINE_TIMEOUT_SECONDS unnamed | open |
| F23 | Nit | fresh reader | Undefined: filters/limit, source, timestamp, `-m live`, instruction files; browser engine has four names | open |
| F24 | Nit | fresh reader | D1 tie-break engine and D3 "lowest rank" ambiguous; no timestamp fallback | open |
| F25 | Nit | fresh reader | Assumptions restate R6, R9 and D5 | open |
| F26 | Nit | fresh reader | R1, R2, R3, R7, R8, R9, R10, R11 each hold more than one rule | open |
| F27 | Nit | fresh reader | R10 vs D6: unclear whether the quality score is exposed in output | open |
| F28 | Nit | fresh reader | D5 cites "the acceptance criterion" with no source | open |
| F29 | Nit | fresh reader | D7: what if the setting exceeds the 15 s HTTP timeout | open |
| F30 | Nit | fresh reader | Links' decision-log vs plan's Decision log not distinguished | open |
