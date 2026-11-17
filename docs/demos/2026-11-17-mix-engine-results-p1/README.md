# Manual check · Phase 01 of the engine-mixing plan

Plan: `docs/plans/2026-11-17-mix-engine-results`, phase 01 (parallel engines with rank fusion).

- **Result:** pass. The live tests passed against real engines, and the Brave API test was skipped.
- **Machine:** AMD Ryzen AI Max+ 395 with Radeon 8060S (integrated GPU), Fedora Linux 44, kernel 7.3.3-200.fc44.x86_64.
- **Versions:** commit `24a0ea2` (branch `feat/mix-engine-results-p1`), Python 3.13.17, pytest 9.2.0. The packages, from `uv.lock`: ddgs 9.16.1, httpx 0.28.1, playwright 1.64.1, fastmcp 4.1.4.
- **Who ran it:** the owner.
- **Commands:** `uv run pytest -m live`, with no `BRAVE_API_KEY` set. Input: the fixed queries in `tests/test_live.py`.

## Observations

- 4 live tests selected: 3 passed and 1 skipped, in 3.70 s.
- Passed:
  - `test_search_summaries`: a real `search_summaries("python programming language", limit=3)` call. It goes through the new parallel path (DDGS and DuckDuckGo HTML) and returned results with http(s) URLs.
  - `test_extract_single_page`.
  - `test_unsafe_url_is_blocked`.
- Skipped: `test_brave_api`, because `BRAVE_API_KEY` was not set. The BraveAPI engine was not exercised live.
- Not observed in this run: each result's `engines` list, the per-engine timings, and whether the browser fallback was triggered. The live test asserts only that results exist and that their URLs are http(s). The offline tests in `tests/test_service.py` and `tests/test_fusion.py` cover those behaviours with stubbed engines.
