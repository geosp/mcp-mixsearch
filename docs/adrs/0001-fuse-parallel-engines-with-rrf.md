---
status: accepted
date: 2026-11-17
supersedes: null
plan: docs/plans/2026-11-17-mix-engine-results
---

# ADR-0001: Search fuses parallel engines with reciprocal rank fusion

## Context

mcp-mixsearch used to try its search engines one at a time and return the first result list that
passed a word-overlap check. Results never combined sources. A slow or broken engine early in the
order also delayed every search by up to the 15 s HTTP timeout, and the check rewarded snippets
stuffed with keywords.

The engines differ in cost:
- The Brave Search API (with a key), the ddgs library and DuckDuckGo HTML are cheap HTTP calls.
- Scraping search.brave.com needs a headless Firefox page load.

None of the engines exposes a relevance score, but all of them give a rank.

We considered:
- interleaving the lists round-robin, which ignores agreement between engines;
- normalizing scores, which the engines don't provide;
- weighting engines, which has no data to tune it.

Reciprocal rank fusion needs only ranks and rewards results that several engines rank highly.

## Decision

The cheap engines are queried in parallel, each under its own timeout (`ENGINE_TIMEOUT_SECONDS`).
An engine that fails or times out is logged and skipped. The ranked lists are deduplicated by
normalized URL and fused by reciprocal rank fusion (k = 60). The browser-based engine runs only as
a fallback when a web search returns fewer results than requested. Every result lists the engines
that returned it (`engines` in the service results, and an `Engines:` line in the tool text).

## Consequences

- Results mix sources, and one bad engine no longer sinks or stalls a search.
- A typical search waits for the slowest cheap engine, up to its timeout, so it can be slower than
  stopping at the first good engine.
- Every search hits every cheap engine, so outbound requests and the risk of rate limiting grow
  with each engine added.
- An engine that can't serve a source (for example news or images) must return nothing rather
  than results of another type. Otherwise those results would pollute the fused list.
- `engines` is part of the tool output contract. Engine labels (`BraveAPI`, `DDGS`, `DuckDuckGo`,
  `Brave`) are visible to clients, so renaming an engine is a visible change.
- A new engine joins by implementing the engine protocol and being added to the cheap list or as
  the fallback. Weighting engines would need a new ADR that supersedes this one.
