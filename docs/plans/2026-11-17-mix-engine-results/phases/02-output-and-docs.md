---
phase: 2
title: Show engines in tool output and docs
status: draft
branch: null
base: null
delivers: [R10, R11]
design_review: { status: changes-requested, rounds: 1, last: 2026-11-17 }
impl_review: { status: none, rounds: 0, last: null }
approved: null
---

# Phase 02 · Show engines in tool output and docs

## Goal

Both search tools print each result's engines. The tool instructions, README and `.env.example`
describe parallel fusion. The decision log records the response-shape change and the non-web
source change.

## Tasks

### 1. Tool output

- [ ] 1.1 In `tool.py`, add `Engines: <labels>` after `Description:` in `full_web_search` and
  `get_web_search_summaries`. Omit the line when the list is empty (R10). Verify: tests in
  `tests/test_tools.py` assert the line for both tools, and that every existing line is unchanged.

### 2. Docs

- [ ] 2.1 Update `instructions.md` and `instructions_summaries.md`: describe the `Engines:` line
  under Returns, and state that results are merged from several engines (R10). Verify: the
  docstring tests in `tests/test_tools.py`, if any, still pass. Read both files and confirm that
  nothing says only one engine is used.
- [ ] 2.2 Rewrite the README's "Multi-Engine Architecture" section for parallel fusion and the
  fallback, and add `ENGINE_TIMEOUT_SECONDS` to the README config block and `.env.example` (D7).
  Verify: `grep -n "quality\|tried in order" README.md` finds nothing stale.
- [ ] 2.3 Add two lines to `docs/decision-log.md`. One: search results merge engines by RRF and
  each result gains `engines` (dict key and `Engines:` text line); existing fields are unchanged.
  Two: DuckDuckGo HTML and the Brave browser engine answer `web` only. Verify: the lines are present.
- [ ] 2.4 Run the AGENTS.md checks from a clean checkout. Verify: `uv sync --locked`, `ruff check`,
  `ruff format --check`, `mypy`, `pytest` and `sync_agents.py --check` all pass.
