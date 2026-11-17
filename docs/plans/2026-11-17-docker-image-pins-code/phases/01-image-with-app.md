---
phase: 1
title: Image with the app built in
status: draft
branch: null
base: null
delivers: [R1, R2, R3, R4, R5, R6]
design_review: { status: none, rounds: 0, last: null }
impl_review: { status: none, rounds: 0, last: null }
approved: null
---

# Phase 01 · Image with the app built in

## Goal

Every published tag runs the code it was built from, with Firefox matching the locked Playwright,
and the publish workflow proves it starts before pushing it.

## Tasks

### 1. Version

- [ ] 1.1 Read the version from package metadata in `server.py` for `/health` and the server info (R3, D6). Verify: a new test in `tests/` asserts `/health` returns `importlib.metadata.version("mcp-mixsearch")`; `uv run pytest`.

### 2. Image

- [ ] 2.1 Add `.dockerignore` excluding `.venv`, `.git`, `docs`, `tests`, caches and `.env*` (R1). Verify: build context in `docker build` output is under ~1 MB.
- [ ] 2.2 Rewrite the `Dockerfile` per notes.md#d1: locked deps, venv Playwright installs Firefox, app installed, entrypoint `mcp-mixsearch` with `CMD --mode http` (R1, R2, R4, D1, D2, D3). Verify: `docker build -t mcp-mixsearch:local .` succeeds.
- [ ] 2.3 Update the `pyproject.toml` comment on the playwright pin and the `README.md` dependency line: the image now takes Playwright from `uv.lock` (D2). Verify: `grep -n playwright pyproject.toml README.md`.

### 3. Compose

- [ ] 3.1 Prod compose: drop `command`; keep the `:main` image and `MCP_AUTH_ENABLED=false` (R5, D3). Verify: `docker compose -f docker/prod/docker-compose.yml config` shows no `command`.
- [ ] 3.2 Dev compose: build the `Dockerfile`, drop the volume, `working_dir`, `command` and `UV_CACHE_DIR` (R5, D4). Verify: `docker compose -f docker/mcp/docker-compose.yml up --build -d`, then `curl localhost:3000/health` answers 200.

### 4. CI

- [ ] 4.1 Add the smoke test to `docker-publish.yml` per notes.md#d5, before the push step (R6, R1, R2, R4, D5). Verify: `actionlint` passes; the workflow passes on the PR.
- [ ] 4.2 Check that the smoke test fails on a broken image: run its script locally against an image built with a wrong `CMD` (R6). Verify: the script exits non-zero and prints the container logs.

### 5. Docs

- [ ] 5.1 `docker/README.md`: the image holds the app; remove the uvx notes; the versioned compose recipe changes only the image tag; describe the dev compose without live reload (R5, D4). Verify: `lychee --offline` link check in ci-gate passes.
- [ ] 5.2 `CHANGELOG.md` `Unreleased`: Changed (image holds the app; entrypoint change with migration step), Fixed (`/health` version) (D3, D6). Verify: read the entry.
- [ ] 5.3 `docs/decision-log.md`: one line for building the app into the image (D1). Verify: read the line.

### 6. Verification

- [ ] 6.1 Run the AGENTS.md checks. Verify: all pass.
- [ ] 6.2 Manual check in `docs/demos/2026-11-17-docker-image-pins-code-p1/`: build the image, start it with `--network none` and fetch `/health` from inside (R1), then start it normally and run a search through `/mcp` (R4). Verify: the record follows docs/demos/README.md.
