---
phase: 2
title: Show engines in tool output and docs
status: in-progress
branch: feat/mix-engine-results-p1
base: 6e49df85c83f9fbe41f96327b7378e8ebe4e43ac
delivers: [R10, R11]
design_review: { status: passed, rounds: 1, last: 2026-11-17 }
impl_review: { status: none, rounds: 0, last: null }
approved: 2026-11-17
---

# Phase 02 · Show engines in tool output and docs

## Goal

Both search tools print each result's engines. The tool instructions, README and `.env.example`
describe parallel fusion. The decision log notes the new `Engines:` text line.

## Tasks

### 1. Tool output

- [ ] 1.1 In `tool.py`, add `Engines: <labels>` after `Description:` in `full_web_search` and
  `get_web_search_summaries`. Read the list with `.get("engines")` and omit the line when it is
  empty or missing (R10). Verify:
  - tests in `tests/test_tools.py` assert the line for both tools, with `FakeService` updated to
    return `engines`;
  - a result without `engines` prints no line;
  - every existing line is unchanged.

### 2. Docs

- [ ] 2.1 Update `instructions.md` and `instructions_summaries.md`. Describe the `Engines:` line
  under Returns, and say that results are merged from several engines (R10). Verify: the tests in
  `tests/test_tools.py` still pass. Read both files and confirm that nothing says only one engine
  is used.
- [ ] 2.2 Update the README and `.env.example` (D7):
  - rewrite the README's "Multi-Engine Architecture" section for parallel fusion and the fallback;
  - replace "intelligent backend selection" (README lines 3 and 80);
  - add `ENGINE_TIMEOUT_SECONDS` to the README config block and `.env.example`;
  - fix ".env.example"'s "as the first search engine" comment on `BRAVE_API_KEY`.

  Verify: `grep -n -i "quality\|tried in order\|backend selection\|first search engine" README.md .env.example`
  finds nothing stale.
- [ ] 2.3 Add a line to `docs/decision-log.md` saying that both search tools print an `Engines:`
  line after `Description:`. Then run the AGENTS.md checks from a clean checkout. Verify: the line
  is present and `uv sync --locked`, `ruff check`, `ruff format --check`, `mypy`, `pytest` and
  `sync_agents.py --check` all pass.
