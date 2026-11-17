## Review of phase 02 (R10, R11) for `6e49df85..215b063`

**I found no Blocker or Major findings.** The phase keeps its contract: both tools print the `Engines:` line, existing lines are unchanged, and the new tests run offline. There are 5 Nits at the end.

### Promises checked

**R10: both tools print `Engines: <labels>` after `Description:`; existing lines and result keys stay the same.**
- **Enforced at:**
  - `/home/geo/develop/mcp-mixsearch/features/web_search/tool.py:28-31` has the `engines_line` helper. It uses `.get("engines")` and returns `""` when the list is empty or missing, as task 1.1 asks.
  - `tool.py:78` adds the line in `full_web_search`.
  - `tool.py:117-119` adds it in `get_web_search_summaries`.
- **Universal claim ("both tools", "every existing line"):** these are the only two places that format search results. `get_single_web_page_content` prints no results, so it doesn't apply.
  - In summaries, `Description: …\n\n---\n\n` was split into `Description: …\n` + `""` + `\n---\n\n`. With no engines this gives the same bytes as before.
  - In `full_web_search`, the line goes before the content and error block, so the existing lines are unchanged.
- **Tests that would fail without it:**
  - `/home/geo/develop/mcp-mixsearch/tests/test_tools.py:121` checks the exact `Description: A\nEngines: BraveAPI, DDGS\n` sequence.
  - `:122` covers an empty list: no line, and the original `Description: B\n\n` stays.
  - `:123` checks `count("Engines:") == 1`.
  - `:144-147` checks the summaries line.
  - `:148` checks a missing key, where the original `Description: N\n\n---` is kept.
- **The service side of the R10 scenario (`"engines": ["BraveAPI","DDGS"]` in the service result):**
  - Enforced at `/home/geo/develop/mcp-mixsearch/features/web_search/service.py:134` for summaries, and through `to_dict()` at `service.py:115` for `search_and_extract`.
  - Tested in `/home/geo/develop/mcp-mixsearch/tests/test_service.py:258` and `:188-191`.
- **Observability:** the tool tests go through a real FastMCP `Client`, so they see the actual text output. The service and tool shapes are tested separately, joined by the `"engines"` key, so a stale key on either side would show up.

**R11: tests run offline.**
- `test_tools.py` uses `FakeService` with no network, and live tests stay behind the `live` marker.
- No other test file changed in this diff.

**D7 docs (task 2.2):**
- `ENGINE_TIMEOUT_SECONDS=10` was added to `/home/geo/develop/mcp-mixsearch/.env.example` and to the README config block.
- The `BRAVE_API_KEY` comment no longer says "first search engine".
- "intelligent backend selection" was removed (README lines 3 and 81).
- The Multi-Engine Architecture section was rewritten for parallel fusion and the fallback.
- I ran the grep from task 2.2 on the committed README and `.env.example`: no stale matches.

**Task 2.1 (instructions):** both `instructions.md` and `instructions_summaries.md` describe merged results and the `Engines:` line under Returns. Neither says that only one engine is used.

**Task 2.3:** the line is in `/home/geo/develop/mcp-mixsearch/docs/decision-log.md:7`.

### Findings

No Blocker or Major findings.

### Nits

- **`/home/geo/develop/mcp-mixsearch/README.md:105-107` (D2):** "Duplicates are merged by normalized URL (case, `www.`, …are ignored)" overstates the rule. D2 and `fusion.py:57` lowercase only the scheme and host, so `https://example.com/A` and `https://example.com/a` stay separate results, against what the README tells readers.
- **`tests/test_tools.py` (R10, task 1.1):** "a result without `engines` prints no line" is tested only through summaries, and the `full_web_search` fixture tests only an empty list (`"engines": []`). Both tools share `engines_line`, so the risk is low, but a later inline change in `full_web_search` that uses `result["engines"]` would raise `KeyError` and no test would catch it.
- **Task 2.3, clean-checkout check run:** the claim that `uv sync --locked`, ruff, mypy, pytest and `sync_agents --check` passed from a clean checkout can't be checked from the diff, and this review is read-only. The checkbox is ticked with no evidence.
- **`features/web_search/instructions.md` `source` section (R8 side effect, outside R10):** it still lists news, images and videos as plainly supported. It doesn't say that only DDGS (and BraveAPI for news) answer them, so non-web searches may return fewer results. This isn't required by the phase tasks.
- **`docs/plans/.../plan.md` and the phase frontmatter:** the phase status is `in-progress` with 4/4 tasks ticked. That is probably intended until the implementation review passes; I mention it only for completeness.

### Files reviewed
- /home/geo/develop/mcp-mixsearch/features/web_search/tool.py
- /home/geo/develop/mcp-mixsearch/tests/test_tools.py
- /home/geo/develop/mcp-mixsearch/features/web_search/service.py
- /home/geo/develop/mcp-mixsearch/features/web_search/fusion.py
- /home/geo/develop/mcp-mixsearch/tests/test_service.py
- /home/geo/develop/mcp-mixsearch/features/web_search/instructions.md
- /home/geo/develop/mcp-mixsearch/features/web_search/instructions_summaries.md
- /home/geo/develop/mcp-mixsearch/README.md
- /home/geo/develop/mcp-mixsearch/.env.example
- /home/geo/develop/mcp-mixsearch/docs/decision-log.md
