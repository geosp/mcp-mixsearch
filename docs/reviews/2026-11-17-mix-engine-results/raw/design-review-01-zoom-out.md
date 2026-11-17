Review of /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-mix-engine-results (plan.md, phases/01-parallel-fusion.md, phases/02-output-and-docs.md, notes.md)

Summary: The plan fixes the root cause. The sequential first-good-engine loop and the word-overlap gate (features/web_search/service.py:156-190, 31-47) are replaced, not patched around. Putting the fusion logic in a new pure module, `fusion.py`, fits how the code is already split (filters.py and url_safety.py are pure helpers next to service.py). Rollout is simple and accurately described: it adds fields only, needs no data, and is undone by a revert. I found one Major and some Nits. The Major is that the latency and request-load reasoning under Risks is wrong for the common case.

## Major

**M1. Risks, bullet 1 (latency) is wrong for the common case, and the outbound load increase is missing from Risks.**
- Location: plan.md › Risks, bullet 1; plan.md › Summary ("Main risks: a slower search…").
- What is wrong:
  - The plan says: "Every engine already had to finish before the next started, so typical latency should fall."
  - Today the engine order is `[BraveAPI?, DDGS, Brave, DuckDuckGo]` (service.py:87-96), and the loop returns at the first engine scoring 0.3 or more (service.py:176-179). With a `BRAVE_API_KEY`, a typical search is one BraveAPI call. Without a key, it is one DDGS call. DuckDuckGo HTML is last, so it is almost never reached.
  - After the change, every search waits for max(BraveAPI, DDGS, DuckDuckGo HTML). So typical latency goes up, not down, whenever the first engine used to succeed. Latency only falls when early engines were failing or slow.
  - DDGS `auto` is itself a slow call. It runs several providers in batches and waits up to its own `timeout` (default 5 s) per batch (.venv/lib/python3.13/site-packages/ddgs/ddgs.py:183-209). That makes it the likely slowest engine on most searches.
  - Request volume also changes. DuckDuckGo HTML and DDGS are now hit on every search instead of rarely, so outbound requests per search roughly double or triple. DuckDuckGo HTML is the endpoint most likely to rate-limit or serve a block page. Risks does not mention this at all.
- Fix: rewrite the bullet to say plainly that latency rises when the first engine used to succeed, and why that is accepted. Add a risk for the extra per-search requests and rate limiting, with a mitigation, for example:
  - the configurable timeout (D7), or
  - logging per-engine failure counts. notes.md › D4 already proposes per-engine info logs, but no task implements them (see N4).

## Nits

- **N1.** phases/01 › 3.3 / plan.md › R10: `search_summaries` builds its dicts by hand with four keys (service.py:128-136), so `engines` will not appear unless that code changes. No task says to change it; only the 3.4 test would catch it. Add it explicitly to 3.3.
- **N2.** plan.md › D5 / phases/01 › 3.2: the plan does not say what an omitted `fallback_engine` means when `engines=` is passed.
  - The existing `make_service` (tests/test_service.py:33-41) passes only `engines=`, and most of its tests return fewer than the default limit of 5 results.
  - If an omitted override means "build the default", the real `BraveBrowserEngine` runs against `FakeBrowser`. Its `evaluate_result` is None (tests/conftest.py:57-72), so the engine raises TypeError and logs a stray "Brave failed" warning. That pollutes the `caplog` assertions in 3.4.
  - Specify a way to turn the fallback off, such as a sentinel or `fallback_engine=None` meaning none.
- **N3.** phases/01 › 3.4 vs plan.md › R7 (third Given, "fails or times out"): the tests cover fallback failure but not a fallback timeout. The 30 s value is a code constant (Assumptions), so make it a module constant the tests can monkeypatch, and add the timeout case.
- **N4.** notes.md › D4: "Each engine also logs a count and duration at info level" has no task in phase 01. Either add it to 3.3, or drop it from the notes, because Risks bullet 2 ("Revisit if logs show repeated ddgs timeouts") relies on those logs.
- **N5.** plan.md › Risks, bullet 2 (abandoned ddgs threads): the "at least 5 workers" claim is right but incomplete.
  - The abandoned threads share the default executor with content extraction's `asyncio.to_thread(html_to_text, …)` (features/web_search/extraction.py:104, 113).
  - A DDGS call lasts until its internal `ThreadPoolExecutor` context exits, and that waits for all submitted providers (ddgs.py:184).
  - Mention that a stuck DDGS call can slow extraction, or pass a DDGS `timeout` no larger than `engine_timeout_seconds` through `ddgs_factory` (engines.py:104).
- **N6.** plan.md › Why / D1: the premise "agreement between independent engines" is weaker than stated. DDGS `auto` already queries the duckduckgo and brave providers and ranks the results itself (ddgs.py:90-97; ddgs/engines/duckduckgo.py, brave.py). So the DDGS, DuckDuckGo HTML and BraveAPI votes can be correlated. Acknowledge this under Risks; it does not change the design.
- **N7.** plan.md › "## Decision log" is an empty trailing heading, which makes the plan look unfinished. Fill it in or remove it.

No findings on placement or rollout beyond the above.

Relevant files:
- /home/geo/develop/mcp-mixsearch/features/web_search/service.py
- /home/geo/develop/mcp-mixsearch/features/web_search/engines.py
- /home/geo/develop/mcp-mixsearch/features/web_search/extraction.py
- /home/geo/develop/mcp-mixsearch/features/web_search/browser.py
- /home/geo/develop/mcp-mixsearch/tests/test_service.py
- /home/geo/develop/mcp-mixsearch/tests/conftest.py
- /home/geo/develop/mcp-mixsearch/.venv/lib/python3.13/site-packages/ddgs/ddgs.py
