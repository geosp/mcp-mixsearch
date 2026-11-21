---
title: Build the app into the Docker image
status: in-progress
created: 2026-11-17
updated: 2026-11-21
design_review: { status: passed, rounds: 2, last: 2026-11-21 }
approved: 2026-11-21
adr_review: null
---

# Build the app into the Docker image

## Summary

A published image tag (`:main`, `:latest`, `:v1.1.0`) pins only Python, uv and Firefox. Each
container downloads the app from the default branch at startup, so a restart can quietly run newer
code. This plan installs the app into the image at build time from `uv.lock`, so a tag pins the
code (R1). Firefox is installed by the Playwright that `uv.lock` locks, replacing the `Dockerfile`
pin, so Dependabot PR #9 can merge safely (R2). The image runs in HTTP mode (R4). As today, it
serves only with `MCP_AUTH_ENABLED=false` behind a gateway, since the server has no auth provider.
`/health` reports the installed version (R3). The compose files run the image as built; the dev
compose loses its source mount (R5, D4). The publish workflow pushes only the image it smoke-tested
(R6), and moves `:main`/`:latest` only to the tip of `main` (R7). The smoke test is not a required
check, so the owner reads it before merging (D5).

```text
build: uv.lock ─► uv sync (app + deps) ─► venv playwright installs Firefox ─► smoke test ─► push
run:   docker run <tag>  ─►  mcp-mixsearch, MCP_TRANSPORT=http   (no download at startup)
```

Main risk: **BREAKING** for running deployments (D3). A compose file that still passes the old
`mcp-mixsearch@git+…` command fails to start on the new `:main` image. See Rollout.

## Why

`docker/prod/docker-compose.yml` runs `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`
on an image whose `ENTRYPOINT` is `uvx`. The code is fetched from the default branch on every
start, so no tag says what code runs, and startup needs GitHub. The `Dockerfile` also pins
`playwright==1.64.1` apart from `uv.lock`. Dependabot PR #9 bumps the lock to 1.65.2. Merging it
today would install Firefox for 1.64.1 next to the 1.65.2 Python package, which can break browser
scraping. Issue #14 has the full report.

## What changes

- The `Dockerfile` copies the source and installs it with `uv sync --locked --no-dev`, then
  installs Firefox with the venv's own `playwright`. The separate `pip install playwright` goes.
- The entrypoint becomes `mcp-mixsearch`, and the image sets `MCP_TRANSPORT=http` (D3).
- Both compose files run the image as built: no `command`, no source mount.
- `/health` and the MCP server info report the installed package version, not a hard-coded `1.0.0`.
- `docker-publish.yml` runs the smoke test on the built image and pushes that same image; a
  per-commit `concurrency` group cancels only stale PR runs, and `main`/`latest` are pushed only
  from the tip of `main` (R7).
- `server.py` gets a test for the reported version (R3).
- A `.dockerignore` keeps local files (`.venv`, `.git`, `docs`, `tests`) out of the build.
- `docker/README.md`, `CHANGELOG.md`, `docs/decision-log.md`, the root `README.md` dependency
  line and the `pyproject.toml` comment on the playwright pin describe the new image.

### Non-goals

- Running as a non-root user, slimming the apt package list, or multi-arch images: separate issues.
- Moving the image build into `ci-ok` or changing the ruleset (D5).
- Pinning the publish workflow's actions by SHA, or removing `ci.yml` (an older workflow that repeats the lint and tests of `ci-gate.yml`).
- Merging PR #9. The owner does that after this lands.

## Terms

- **Image tag:** a name under `ghcr.io/geosp/mcp-mixsearch` that `docker-publish.yml` pushes.
  Today: `main`, `latest` and `sha-<short sha>` on every push to `main`; version tags, `latest`
  and `sha-…` on a `v*` git tag. **Moving tags** are `main` and `latest`.
- **`MCP_AUTH_ENABLED`:** a server setting (default `true`). In HTTP mode with it `true`, the
  server exits at startup, because it has no auth provider; `false` serves without auth.
- **Revision label:** `org.opencontainers.image.revision`, the commit SHA that
  `docker/metadata-action` already writes into each image's labels (`docker-publish.yml`).
- **Smoke test:** `.github/scripts/docker_smoke.sh`, run by `docker-publish.yml` on the built
  image. It checks the Playwright version and a Firefox launch (R2), a start with no network and
  `/health` (R1, R4), and the reported version (R3). Any failure exits non-zero.
- **`ci-ok`:** the one required status check on `main`, a job in the `ci-gate.yml` workflow that
  passes only when lint, types, tests and the other `ci-gate` jobs pass.
- **Ruleset:** the GitHub branch rules on `main` (PR only, `ci-ok` required); only the owner
  changes them.
- **`mcp-service-kit`:** the library the server is built on, installed from a git tag, so the
  build (not startup) needs `git` and GitHub access.
- **Manual check:** a run by the owner on real input, recorded in `docs/demos/` (task 6.2). Part
  of it runs before merge, and the revision-label read runs after.
- **Prod compose / dev compose:** `docker/prod/docker-compose.yml` (published image) and
  `docker/mcp/docker-compose.yml` (built locally).

## Requirements

### R1 · An image runs the code it was built from

Starting the image must never download code: the app and its Python dependencies are in the image.
The commit an image holds is named by its `org.opencontainers.image.revision` label, which
`docker/metadata-action` sets.
- **Given** a built image, **when** it starts with `--network none` and `MCP_AUTH_ENABLED=false`, and `/health` is fetched from inside the container, **then** it answers 200.
- **Given** an image pushed from commit C, **when** the manual check reads its revision label with `docker inspect`, **then** it is C.

### R2 · Playwright and Firefox come from uv.lock

The `playwright` package in the image must be the version `uv.lock` locks, and Firefox must be the
build that version installs.
- **Given** `uv.lock` locks playwright V, **when** the image is built, **then** `playwright` in the image reports V.
- **Given** the built image, **when** a script launches headless Firefox through Playwright, **then** it opens a blank page and exits 0.

### R3 · The server reports its installed version

`/health` and the MCP server info must report the version of the installed `mcp-mixsearch` package.
- **Given** the installed package is version X, **when** `/health` is fetched, **then** its `version` is X.
- **Given** the installed package is version X, **when** the MCP server info is read, **then** its version is X.

### R4 · The image serves HTTP

The image must start the server in HTTP mode, on port 3000 unless an option changes it, whether or
not options are passed.
- **Given** `docker run -e MCP_AUTH_ENABLED=false -p 3000:3000 <image>`, **when** `/health` is fetched, **then** it answers 200.
- **Given** `docker run -e MCP_AUTH_ENABLED=false -p 3001:3001 <image> --port 3001`, **when** `/health` is fetched on 3001, **then** it answers 200.
- **Given** `docker run <image> --help`, **when** it runs, **then** it prints the server's usage and exits 0.

### R5 · Compose files run the image as built

Neither compose file may override the command or mount source code.
- **Given** either compose file, **when** `docker compose config` renders it, **then** it has no `command` and no source volume.

### R6 · An image is pushed only after its smoke test passes

`docker-publish.yml` must push only the image its smoke test passed; on pull requests it runs the
smoke test and pushes nothing.
- **Given** an image whose server fails to start, **when** the workflow runs, **then** the job fails before the push step.
- **Given** a pull request, **when** the workflow runs, **then** the smoke test runs and nothing is pushed.

### R7 · Moving tags point only at the tip of main

`docker-publish.yml` must push `main` and `latest` only from a run whose commit is still the tip of
`main`. Commit and version tags are always pushed.
- **Given** commit B is on `main`, **when** the run for an older commit A is re-run and passes, **then** it pushes `sha-A` but not `main` or `latest`.
- **Given** a `v*` tag on any commit, **when** its run passes, **then** it pushes the version tags and `sha-…`, but not `latest`.

## Decisions

### D1 · Build the app into the image

Install the source with `uv sync --locked --no-dev` at build time. A first sync with
`--no-install-project` installs only the dependencies, so code changes reuse that layer. Startup then needs no network and runs what CI
built. Rejected: pinning the git ref in the compose command (still downloads at startup, and the
image and code pins can drift). Details: notes.md#d1

### D2 · Install Firefox with the venv's Playwright

Run `playwright install --with-deps firefox` from the venv, so the browser build always matches the
locked package. The exact `playwright==` pin stays in `pyproject.toml`; Dependabot bumps it and
the lock together. Rejected: a second pin in the `Dockerfile` (it drifts, as PR #9 shows).

### D3 · Entrypoint is the app; clean break

`ENTRYPOINT ["mcp-mixsearch"]`, `ENV MCP_TRANSPORT=http`, no `CMD`. Options passed as a command
keep HTTP mode, because `--mode` defaults to `MCP_TRANSPORT`. **BREAKING:** old `uvx`-style commands
fail. The changelog's migration line: "Remove `command:` from your compose file, or keep only the
server's options, for example `--port 3001`." Rejected: `CMD ["--mode", "http"]`, because any
custom command replaces it and falls back to stdio. Rejected: a shim that drops old `uvx`
arguments (code to maintain for one deployment).

### D4 · Dev compose builds and runs the image

The dev compose builds the `Dockerfile` and runs it with no mount, so it tests the image CI
publishes. Live editing uses `uv run mcp-mixsearch` on the host. Rejected: keeping the source mount
(it hides the installed venv, so it would not test the image).

### D5 · Smoke test in the publish workflow, not in ci-ok

The smoke test runs in `docker-publish.yml` on PRs and pushes, and gates the push. The workflow
builds the image once, tests it, then pushes those same tags with `docker push`. `ci-ok` and the
ruleset stay unchanged, so a failing smoke test on a PR does not block its merge; the owner checks
it. Rejected: a `ci-gate` job, because every PR would wait ~3–5 min for a Firefox image build.
Rejected: no CI change, because a broken image would be pushed. Details: notes.md#d5

### D6 · Version from package metadata

`server.py` reads the version with `importlib.metadata.version("mcp-mixsearch")`. Running
`server.py` without the package installed is not supported; `uv run` always installs it. Rejected:
keeping a hard-coded constant (it already drifted: `1.0.0` on v1.1.0).

### D7 · Move `main` and `latest` only from the tip of main

Before pushing the moving tags, the workflow compares its commit with `git ls-remote origin
refs/heads/main` and skips them if they differ. `latest` is set only on `main` pushes, as
`docker/README.md` already describes it ("`latest` follows `main`"). Rejected: relying on the
`concurrency` group alone (a re-run of an old run starts alone and passes it).

## Assumptions

- Every runtime dependency installs on `python:3.14-slim` (amd64), the current base image. `git` stays in the image for the `mcp-service-kit` git dependency.
- uv is installed with `pip install uv==0.13.5`, the `UV_VERSION` that `ci-gate.yml` pins. A comment in the `Dockerfile` names `ci-gate.yml`, and the `ci-gate.yml` header names the `Dockerfile`.
- `MCP_AUTH_ENABLED=false` stays out of the image, so an image started without it exits: the safe default.
- The compose files and the smoke test set `MCP_AUTH_ENABLED=false`, as prod does today.
- Prod sits behind an authenticating gateway, as `docker/README.md` advises.
- The image builds and runs as root, as it does today.

## Risks

- A running deployment pulls the new `:main` with the old compose command and fails to start → Rollout updates the compose file in the same step as the pull; the changelog says so.
- A deployment that pulls `:main` or `:latest` automatically breaks at its next pull → before merging, pin it to the v1.1.0 rollback compose below.
- That pinned deployment stays on v1.1.0 → after the merge, move it to the new compose (Rollout step 3).
- The image grows by the venv (~100–200 MB) → accepted: startup no longer downloads the same packages.
- A dependency without a Python 3.14 wheel needs compilers → `build-essential` stays in the apt list.
- The smoke test passes but a real search fails → the manual check runs a search through `/mcp` before the merge.

## Rollout & rollback

1. Before merging: pin any auto-pulling deployment to the v1.1.0 rollback compose below.
2. Merge. `docker-publish.yml` pushes the new `:main`, `:latest` and `sha-…` tags.
3. On each deployment, in one step: get the new `docker/prod/docker-compose.yml` (no `command`).
   In a checkout: `git checkout -- docker/prod/docker-compose.yml && git pull`. Elsewhere: copy the
   file from `main`. Then `docker compose pull && docker compose up -d`.
4. The owner tags a release when ready. Minor or major is the owner's call: only image
   deployments break, and MCP clients see no change.
5. Rebase PR #9 (`@dependabot rebase`). Its smoke test is not a required check (D5), so the owner
   confirms it passed before merging.

Rollback to v1.1.0: in `docker/prod/docker-compose.yml`, set both the image and the code ref, then
`docker compose up -d`:

```yaml
    image: ghcr.io/geosp/mcp-mixsearch:v1.1.0
    command: ["mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git@v1.1.0", "--mode", "http"]
```

Reverting the merge commit republishes `:main` with the `uvx` entrypoint. Every deployment on
`:main` must then get the v1.1.0 compose's `command` line back
(`["mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git", "--mode", "http"]`) in the
same step.

## Open questions

- None

## Impact

- Packages / directories: `Dockerfile`, `.dockerignore` (new), `docker/`, `.github/workflows/docker-publish.yml`, `.github/workflows/ci-gate.yml` (comment only), `.github/scripts/docker_smoke.sh` (new), `server.py`, `tests/`, `pyproject.toml` (comment only), `CHANGELOG.md`, `docs/decision-log.md`, `README.md`
- Data: none
- Jobs / APIs: the published image's entrypoint and default command; `/health` `version`; MCP server info version

## Links

- Issue #14: build the app into the image so tags pin the code; lists the acceptance criteria.
- PR #9: Dependabot bump of playwright 1.64.1 → 1.65.2, blocked by the separate `Dockerfile` pin.
- ADR-0001: search merges parallel engines' results by reciprocal rank fusion; unaffected.

## Phases

| Phase | Title | Status | Tasks |
| --- | --- | --- | --- |
| 01 | Image with the app built in | in-progress | 12/14 |

## Decision log

2026-11-21 · notes.md#d5 step 1 changed: the concurrency group is per commit on `main` and tags, not per ref, because a shared group keeps only one pending run and cancels the rest, which would skip their `sha-…` tags (R7). Found by impl review I1.
