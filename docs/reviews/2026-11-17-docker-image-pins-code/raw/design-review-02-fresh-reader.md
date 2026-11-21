Report on /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/plan.md (I read only this file).

## From the Summary
Today a Docker image tag only fixes the Python, uv and Firefox versions. Each container downloads the app's code from the default branch when it starts, so the same tag can run different code after a restart. The plan builds the app into the image from `uv.lock` so the tag fixes the code. It also takes Firefox from the locked Playwright, which unblocks a Dependabot PR, reports the real version, removes source overrides from the compose files, and adds a smoke test before each push. The main risk is that the change breaks running deployments: a compose file that still passes the old `uvx`-style command will not start on the new image.

## From the whole plan
The Dockerfile will install the app and its locked dependencies with `uv sync --locked --no-dev`, using a dependency-only layer first. The venv's own Playwright installs Firefox. The entrypoint becomes `mcp-mixsearch` with the default arguments `--mode http`. Both compose files drop `command` and source mounts. `/health` and the MCP server info read the version from package metadata. `docker-publish.yml` builds the image, smoke-tests it (on PRs too) and pushes only that tested image. The goals are that a tag names the code it runs, startup needs no network, and Firefox can never drift from the Playwright package, which is what makes the PR #9 bump (1.64.1 to 1.65.2) safe. The change is deliberately breaking, so the plan comes with a pin-before-merge, update-on-pull rollout and a v1.1.0 rollback snippet.

## How the existing system works, per this plan
The image's `ENTRYPOINT` is `uvx`. Prod compose runs `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`, so every start fetches the default branch from GitHub. The Dockerfile `pip install`s `playwright==1.64.1` separately from `uv.lock` and installs Firefox with it. The dev compose mounts the source over the image. The server reports a hard-coded version `1.0.0`, even on v1.1.0. The server has no auth provider and refuses to serve unless `MCP_AUTH_ENABLED=false`. Prod runs it that way behind an authenticating gateway. `docker-publish.yml` pushes `main`, `latest` and `sha-…` tags on pushes to `main`, and version tags on `v*` tags, with no smoke test. `ci-ok` in `ci-gate.yml` is the only required check.

## Summary vs plan
- Major (Summary): "serves only with `MCP_AUTH_ENABLED=false`" reads like a limitation, or even as if auth is being turned off. The Assumptions section shows it is a safe default: the variable stays out of the image, the server refuses to serve without it, and prod runs behind a gateway. The Summary needs half a sentence of that context.
- Major (Summary vs D5 / Rollout step 5): "this unblocks Dependabot PR #9" and "pushes only the tested one" leave out that the smoke test is not a required check. A failing smoke test does not block a PR merge, and the owner has to check it by hand. This affects how safe the PR #9 merge really is.
- Nit (Summary): the Main risk line leaves out the pre-merge step (pin auto-pulling deployments to `:v1.1.0`). It only says "See Rollout".
- Nit (Summary): it doesn't say that reverting the merge also breaks deployments unless `command` is restored (Rollout & rollback).
- Nit (Summary): it says startup no longer needs the network but doesn't say the build still needs `git` and GitHub access for `mcp-service-kit`.
- Nit (Summary): the `concurrency` group in What changes isn't mentioned.

## Sections I couldn't paraphrase (Blockers)
None. D1 and D5 point to `notes.md` for details, but each can be understood without it.

## Undefined project-specific terms
- Major (Assumptions, Summary, R1, R4): `MCP_AUTH_ENABLED`. The plan never states what it controls or what "refuses to serve" looks like (exit at startup? 401s?). You can only work it out from two Assumptions bullets.
- Nit (R3, What changes): "MCP server info" is never tied to a concrete field or call.
- Nit (D3, R4): `--mode http` implies other modes, which are never named. It is also never said whether port 3000 is the app's default or set by the image.
- Nit (Phases): "0/14" tasks refers to a phase file that isn't in this plan.
- Nit (frontmatter): `design_review`/`adr_review` statuses aren't explained, and the Decision log section is empty even though one review round is recorded.

## Places where the parts don't connect
- Major (R1, second criterion vs Terms "Smoke test"): the Terms entry says the smoke test covers R1, but it lists only the no-network start and `/health`. Nothing says who checks the `org.opencontainers.image.revision` label, or whether `docker/metadata-action` already sets it today or is being added.
- Major (R6 / What changes): "pushes that same image" has no mechanism. The plan never says how the image is built once, tested, then pushed under several tags without a rebuild. A rebuild would break the guarantee.
- Major (Rollout step 3): "`git pull` the repository" assumes deployments run from a checkout of this repo. That has not been stated before, and deployments that copy the compose file elsewhere are not covered.
- Nit (What changes): the `concurrency` group has no requirement or decision, and out-of-order publishing is not listed in Risks.
- Nit (Risks, last bullet): the "manual check" with a search through `/mcp` is never placed in the Rollout steps, so when it runs is unclear.
- Nit (Rollout, revert paragraph): "the same `command` line" doesn't say whether that means the `@v1.1.0` ref from the snippet or the unpinned default-branch command.
- Nit (Rollout step 4): "minor or major, owner's choice" for a change the plan labels BREAKING. It should state why a minor bump is acceptable, or settle on major.
- Nit (Assumptions, uv pin): "a comment in each file names the other" doesn't name the files. Presumably they are `Dockerfile` and `ci-gate.yml` (Impact lists ci-gate as comment only).
- Nit (Assumptions): it doesn't say whether `python:3.14-slim` is the current base image or a new one.

## Readability
- Nit (Summary): I had to reread "The venv's Playwright, locked in `uv.lock`, installs Firefox, replacing the separate `Dockerfile` pin (R2)", because it is unclear what replaces what.
- Nit (Summary): I had to reread "starts the HTTP server by default (R4) but, as today, serves only with `MCP_AUTH_ENABLED=false`".
- Nit (Risks, bullet 2): about 40 words with two actions joined by "and"; split it.
- Nit (D3): a stray leading space before "Rejected:" (line 141) breaks the paragraph.
- Nit (D1): the source line wraps unevenly (line 126); cosmetic only.
- Nit (repetition): the breaking change appears in Summary, D3, Risks and Rollout. Auth=false appears in Summary, Assumptions (twice), R1 and R4. The smoke test's contents appear in both Terms and What changes.
- Nit (R1): two rules in one requirement: no download at startup, and the revision label names the commit.
- Nit (R5): two rules: no `command`, and no source mount.
- Nit (R6): two rules: push only the tested image, and push nothing on PRs.
- Nit (Assumptions, 4th bullet): two facts in one bullet: compose and the smoke test set the flag, and that is how prod runs behind a gateway.
