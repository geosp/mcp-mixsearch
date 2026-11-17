File read: /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/plan.md. For Pass 1 I read only lines 1-40, which cover the Summary. I read the rest for Pass 2. The file ends at an empty "## Decision log" heading.

## From the Summary
Right now a published Docker image fixes only the toolchain: Python, uv and Firefox. Each container downloads the app from the default branch when it starts, so a tag doesn't tell you what code runs, and a restart can quietly pick up newer code. The plan installs the app into the image at build time from `uv.lock`, takes Firefox from the locked Playwright version, starts the HTTP server by default, has `/health` report the real version, and has the publish workflow start each image before pushing it. This also unblocks a Dependabot PR (#9). The main risk is that it breaks running deployments: a compose file that still passes the old `mcp-mixsearch@git+…` command will fail to start on the new `:main` image.

## From the whole plan
The `Dockerfile` will run `uv sync --locked --no-dev`, dependencies first and then the app, and will install Firefox with the venv's own `playwright` instead of a separate `pip install playwright==1.64.1`. The entrypoint changes from `uvx` to `mcp-mixsearch` with a default `--mode http`. Both compose files stop overriding the command and stop mounting source. `/health` and the MCP server info will read the version from package metadata. `docker-publish.yml` will smoke-test the image on PRs and pushes, and push only if that test passes. The goals are images whose tags pin the code, startup that needs no network or GitHub, and Playwright and Firefox that can't drift apart, which is what makes PR #9 (playwright 1.64.1 → 1.65.2) safe to merge.

## How the existing system works, per this plan
The image's `ENTRYPOINT` is `uvx`, and the prod compose runs `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`, so every start fetches the default branch from GitHub. The `Dockerfile` pins `playwright==1.64.1` separately from `uv.lock` and installs Firefox for that version. The dev compose mounts source over the container. `server.py` reports a hard-coded version `1.0.0`, even on v1.1.0. `docker-publish.yml` pushes the `:main`, `:latest`, `sha-…` and version tags without starting the image first. The image runs as root on `python:3.14-slim`.

## Summary vs plan
- Major · Summary: it doesn't mention R5. The dev compose changes too: the source mount goes away, and live editing moves to `uv run` on the host (D4). That changes the developer workflow, but the Summary only describes the prod/deployment break.
- Major · Summary: it doesn't say that the image refuses to serve unless `MCP_AUTH_ENABLED=false` is set (Assumptions). Someone reading "the image starts the HTTP server by default" would expect `docker run <tag>` to just work.
- Nit · Summary: it lists R1, R2, R4, R3, R6 out of order and skips R5.
- Nit · Summary: it says `/health` reports the version, but R3 and D6 also cover the MCP server info.
- Nit · Summary: "starts every image before pushing it" hides two things: on PRs nothing is pushed, and the smoke test doesn't block PR merges (D5).

## Sections I couldn't paraphrase (Blockers)
None. Every section could be paraphrased. The Phases table says "0/13" tasks but lists none. That reads as a status pointer, not a section with content to paraphrase.

## Undefined project-specific terms
- Major · Non-goals / D5: `ci-ok` and "the ruleset". It's never said what `ci-ok` is (a required check? a job?) or what the ruleset enforces. The D5 trade-off depends on both.
- Major · D5 "Rejected: a `ci-gate` job" vs Assumptions "`ci-gate.yml`". It's unclear whether `ci-gate` is a workflow file, a job, or the same thing as `ci-ok`.
- Nit · Assumptions: `mcp-service-kit` "git dependency" isn't explained.
- Nit · Assumptions: `<UV_VERSION>` (build arg? where is it defined?) isn't explained, and neither is how it stays in sync with `ci-gate.yml`.
- Nit · Risks: "the manual check runs a search through `/mcp`". No manual check is introduced anywhere else.
- Nit · Non-goals: "the duplicate `ci.yml`" isn't explained.
- Nit · Rollout: the `sha-…` tags. The Terms section points to the `docker/README.md` table instead of saying when each tag is pushed.
- Nit · Links: "RRF" and ADR-0001 aren't explained (harmless, since the plan says they're unaffected).
- Nit · Throughout: "the owner" and "one deployment" (D3). How many deployments exist and who runs them isn't stated.

## Places where parts don't connect
- Major · Rollout & rollback: the first rollback option doesn't actually roll back the code. The plan's own premise is that the v1.1.0 image plus the v1.1.0 compose downloads the app from the default branch at startup. After this merge, that means the new code. So "run `:v1.1.0`" brings back the old packaging, not the old code.
- Major · Rollout & rollback: the "revert the merge commit" option doesn't address the compose file. In Rollout step 2, deployments switched to the new compose with no `command`. If `:main` is rebuilt from the revert, the `uvx` entrypoint comes back with no arguments and the container fails. The rollback needs to say to restore the old compose as well.
- Major · R1: the goal is that a tag pins the commit's code, but the test only checks "that commit's package version". The package version doesn't change between commits within a release, so the check can't tell commits apart. Also, R1's test doesn't set `MCP_AUTH_ENABLED=false`. Per the Assumptions, the server would then refuse to serve, so `/health` may not return 200.
- Major · R6 / Terms "Smoke test": it never says what the smoke test checks. It could be `/health` only, the R2 headless-Firefox launch, the R1 `--network none` run, or the R4 `--help` run. R2's second criterion has no named place where it runs.
- Major · Assumptions: "the compose files … set [`MCP_AUTH_ENABLED=false`]". That implies the prod compose runs with auth disabled. It's unclear whether that's intended, or whether prod sets real auth config instead. The plan doesn't say.
- Major · Rollout step 1 vs Summary risk: if `:latest` is pushed on merge (step 1), any deployment on `:latest` breaks at its next pull, before step 2 happens. Ordering or timing for deployments isn't covered. Step 2 also doesn't say where deployments get the "new prod compose" from.
- Major · D5 / Rollout step 4: the PR smoke test isn't a required check, so "must pass before the owner merges it" depends on a person checking. The plan presents this as unblocking PR #9, but nothing enforces it.
- Major · R3: the requirement covers `/health` and the MCP server info, but the acceptance criterion only checks `/health`.
- Nit · D3: it promises a "one-line migration" in the changelog, but the plan never gives that line.
- Nit · D1 / D5: both end with "Details: notes.md#…". Both decisions are still understandable without notes.md, but D1's "dependencies first, then the app" doesn't name the mechanism used to do it.
- Nit · Impact: it lists `README.md` (root), `tests/` and `pyproject.toml (comment only)`, but What changes never mentions a root README change, new tests, or what the pyproject comment says.
- Nit · R4: it requires "port 3000", but the test only maps `-p 3000:3000` and checks for 200. It doesn't check that the server listens on 3000 by default and not because of config.

## Readability
- Nit · Summary: I had to reread "Firefox is installed with the Playwright that `uv.lock` locks, not a second pin in the `Dockerfile`" (the "not a second pin" part reads awkwardly).
- Nit · D5: I had to reread "Rejected: a `ci-gate` job (every PR waits for a ~3–5 min Firefox image build); no CI change (a broken image would be pushed)". It packs two rejected options into one line, separated only by a semicolon.
- Nit · Assumptions (MCP_AUTH_ENABLED bullet): at about 30 words it isn't over the 40-word limit, but it holds three facts: where the variable lives, how the image behaves without it, and who sets it.
- Nit · The breaking-change fact is stated four times in different words (Summary, What changes, D3, Risks).
- Nit · R1 holds two rules: the image holds the app and its dependencies, and startup never downloads.
- Nit · R2 holds two rules: the package version matches the lock, and Firefox matches that package.
- Nit · R3 holds two rules: `/health` and the server info.
- Nit · R5 holds two rules: no command, and no source mount.
- Nit · R6 holds two rules: run on every build, and don't push on failure.
- Nit · R4's second criterion puts the reason inside the "then" clause ("because arguments replace `--mode http`").
- No sentences over about 40 words.
