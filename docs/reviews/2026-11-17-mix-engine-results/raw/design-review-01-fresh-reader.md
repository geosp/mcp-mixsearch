I read only /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-mix-engine-results/plan.md. I didn't open notes.md, the code or anything else. For Pass 1 I read up to line 40, just past the next heading.

## From the Summary

The server is called "mixsearch" but today it returns results from only one engine: the first whose word-overlap quality score reaches 0.3. The plan runs the inexpensive engines (BraveAPI if a key is set, DDGS, DuckDuckGo HTML) at the same time, each with a 10 s timeout. It merges their ranked lists with reciprocal rank fusion, removes duplicate URLs and labels each result with the engines that found it. The browser-based Brave engine is used only to top up when there are too few results, and the quality score is dropped. The main risk is latency: every search now waits for the slowest cheap engine, up to the timeout. There is also a smaller risk from ddgs worker threads that keep running after a timeout.

## From the whole plan

`_multi_engine_search` calls the engines one after another and returns the first list that scores at least 0.3 on `assess_result_quality`. So sources never combine, a slow engine early in the order delays every search, and the score rewards snippets stuffed with the query's words. The plan replaces this with a parallel `asyncio.gather`, wrapping each engine in `wait_for` with a configurable `ENGINE_TIMEOUT_SECONDS` (default 10). A new pure module, `fusion.py`, normalizes URLs, deduplicates, fuses with RRF (k=60, deterministic tie-breaks) and picks each merged result's fields by fixed rules. The Playwright Brave engine has a 30 s timeout and runs only when the fused list is shorter than `limit`. The plan also changes behaviour that the Summary never mentions: DuckDuckGo HTML and the Brave browser engine now return nothing for news, images and videos. Results gain an `engines` field and both tools print an `Engines:` line. The stated reason is that agreement between independent engines is a better relevance signal than keyword overlap.

## How the existing system works, per this plan

`WebSearchService._multi_engine_search` in `features/web_search/service.py` tries BraveAPI (if keyed), DDGS, DuckDuckGo HTML and then the Playwright Brave engine, in that order. It returns the first list whose `assess_result_quality` score (query words found in titles and descriptions) is at least `QUALITY_THRESHOLD` 0.3. Each engine can take up to the 15 s HTTP timeout. ddgs runs in a thread. When every engine fails, the search still succeeds with zero results. For non-web sources, DuckDuckGo HTML and the Brave browser engine currently return ordinary web results, and BraveAPI returns nothing for images and videos. Filters (`recency_days`, `language`, `country`) are turned into engine parameters in `filters.py`, and each engine is asked for `filters.limit` results.

## Summary vs plan

- **Major** (Summary vs What changes / R8 / Risks bullet 3): the Summary leaves out a user-visible change. News, image and video searches lose DuckDuckGo HTML and Brave browser as fallbacks, so they can now come back empty where they used to return web results. The plan treats this as important enough for a Risk and a decision-log entry, so a reader of the Summary alone would miss it.
- **Major** (Summary risks vs Risks bullet 1): the Summary calls the main risk "a slower search", while Risks says "typical latency should fall". The Summary should say which it is, for example a slower best case but a faster typical and worst case.
- **Major** (Summary diagram / risks vs D5): the Summary bounds the wait at the cheap-engine timeout (10 s). It doesn't mention that the fallback adds up to 30 s more, so the worst case is about 40 s. Risks never mentions this either.
- Nit (Summary diagram): it shows "dedupe → RRF" as two steps. D1 scores per normalized URL, which is a single fuse step.
- Nit (Summary): it doesn't say that the timeout is a new setting (`ENGINE_TIMEOUT_SECONDS`), only "its own timeout" and "10 s".
- Nit (Summary): "Both tools" doesn't name the tools. They are named only under Impact (`full_web_search`, `get_web_search_summaries`).

## Sections I couldn't paraphrase (Blockers)

None are Blockers, because every section can be paraphrased. Two sections have no content to paraphrase, though:
- **Major** (Phases): the table shows 0/9 and 0/5 tasks, but the plan neither lists the tasks nor says where they live. A reader can't tell which requirements fall in which phase, or how many PRs the rollback has to revert.
- Nit (Decision log): the heading is empty and doesn't say what is supposed to go there.

## Undefined project-specific terms

- Nit (R3/R7/R9, `filters` / `filters.limit`): the filters object and its fields are never introduced. `limit` first appears in the Summary with no explanation.
- Nit (What changes / R8, "source" `web`/`news`/`images`/`videos`): the plan never says that the tools take a source parameter.
- Nit (D3/R5, "timestamp"): a result field that is never introduced.
- Nit (D5, "the acceptance criterion is 'below the limit'"): it's unclear whose acceptance criterion this is (an issue? a ticket?), and the source isn't given.
- Nit (Why/D7, "the 15 s HTTP timeout"): the plan doesn't say where it is set or whether it covers ddgs.
- Nit (R11, `-m live`): the pytest marker is never explained.
- Nit (What changes, "the two tool instruction files"): they are named only later, in Impact.
- Nit (Terms/throughout): the browser engine has four names: "Brave browser engine", `BraveBrowserEngine`, label `Brave`, and "Brave (browser)". Next to `DuckDuckGo` / DDGS / "DuckDuckGo HTML", these are easy to mix up.

## Places where the parts don't connect

- **Major** (R8): R8 is a mechanism without a stated goal. Why, Summary and Non-goals never explain why this change needs the source behaviour to change. The reason is probably that fusion would mix web pages of the wrong type into news or image results, but only Risks justifies it, after the fact.
- **Major** (D2 / R4): the "fixed list of click ids" is needed to implement and test normalization, but it lives only in notes.md#d2. Other decisions also send their details to notes.md (D1, D4, Rollout). Those decisions still make sense without the notes, but D2 can't be implemented from this file alone.
- **Major** (Risks bullet 1): the mitigation doesn't follow. "Every engine already had to finish before the next started" doesn't show that typical latency falls, because today a search stops after the first good engine. It only helps if early engines are often slow or failing, and the plan gives no data on that.
- Nit (D7): the 10 s default is justified as staying under the 15 s HTTP timeout. The plan doesn't say what happens if someone raises the setting above 15 s, or whether that bound applies to ddgs at all.
- Nit (D1): "then to the earlier engine in configured order" doesn't say which engine is meant when a URL has several occurrences, for example the engine of its best-ranked occurrence.
- Nit (D3): "lowest rank" could mean the lowest number or the worst position. Also, unlike the title, the timestamp has no rule for when the best occurrence's timestamp is empty.
- Nit (R10 vs D6): it isn't stated whether the current output exposes the quality score anywhere. If it does, "every existing line and dict key stays" conflicts with removing it.
- Nit (Assumptions bullet 1): it cites R9, so it is a requirement restated, not an assumption.
- Nit (Links vs Decision log): two different "decision logs" (`docs/decision-log.md` and this plan's empty section) appear with no explanation of how they differ.

## Readability

- Nit (Summary, line 28-29): "And ddgs threads that keep running after a timeout." is a sentence fragment.
- Nit (Summary, line 15-16): I had to reread "the first that clears a word-overlap score of 0.3", because it isn't clear what clears what.
- Nit (Risks bullet 1): I had to reread the mitigation sentence, for the non-sequitur noted above.
- Nit (D5): I had to reread "(the acceptance criterion is 'below the limit')", because it relies on an outside source.
- Nit: no sentence is over about 40 words.
- Nit (repetition): R6 and Assumptions bullet 3 both say engine labels follow the configured order.
- Nit (repetition): D5 and Assumptions bullet 5 both state the 30 s fallback timeout.
- Nit (repetition): R9 and Assumptions bullet 1 both say each engine is asked for `filters.limit` results.
- Nit (repetition): "the fallback runs only below the limit" appears in the Summary, What changes, R7 and D5.
- Nit (multi-rule requirement, R1): it holds three rules: start together, a timeout cap, and BraveAPI only when keyed.
- Nit (multi-rule requirement, R2): it holds three rules: log a warning with the engine name, return the other engines' results, and succeed with zero results when every engine fails.
- Nit (multi-rule requirement, R3): it holds two rules: RRF order and a cap at `limit`.
- Nit (multi-rule requirement, R7): it holds two rules: the run condition and fallback failure handling.
- Nit (multi-rule requirement, R8): it holds three rules: two engines return nothing for non-web, BraveAPI returns nothing for images and videos, and no request is made.
- Nit (multi-rule requirement, R9): it holds two rules: filter mapping and the per-engine limit.
- Nit (multi-rule requirement, R10): it holds four rules: line position, format, existing fields unchanged, and the dict key.
- Nit (multi-rule requirement, R11): it holds two rules: tests run offline and live checks stay under `-m live`.
