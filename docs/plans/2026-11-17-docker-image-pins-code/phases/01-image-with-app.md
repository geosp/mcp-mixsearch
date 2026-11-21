---
phase: 1
title: Image with the app built in
status: in-progress
branch: feat/14-docker-image-pins-code
base: 3057bac1dabfe64b7511a7cd52bc6bb5eb45a51b
delivers: [R1, R2, R3, R4, R5, R6, R7]
design_review: { status: passed, rounds: 2, last: 2026-11-21 }
impl_review: { status: none, rounds: 0, last: null }
approved: 2026-11-21
---

# Phase 01 · Image with the app built in

## Goal

Every published tag runs the code it was built from, with Firefox matching the locked Playwright,
and the publish workflow proves it starts before pushing it.

## Tasks

### 1. Version

- [x] 1.1 Read the version from package metadata in `server.py` for `/health` and the server info (R3, D6). Verify: a new test in `tests/` asserts that `/health` and `MixSearchServer.service_version` both return `importlib.metadata.version("mcp-mixsearch")`; `uv run pytest`.

### 2. Image

- [ ] 2.1 Add `.dockerignore` excluding `.venv`, `.git`, `docs`, `tests`, caches and `.env*` (R1). Verify: build context in `docker build` output is under ~1 MB.
- [ ] 2.2 Rewrite the `Dockerfile` per notes.md#d1: locked deps, venv Playwright installs Firefox, app installed, entrypoint `mcp-mixsearch` with `ENV MCP_TRANSPORT=http` and no `CMD`; add the uv-version comment to the `ci-gate.yml` header (R1, R2, R4, D1, D2, D3). Verify: `docker build -t mcp-mixsearch:local .` succeeds.
- [ ] 2.3 Update the `pyproject.toml` comment on the playwright pin and the `README.md` dependency line: the image now takes Playwright from `uv.lock` (D2). Verify: `grep -n playwright pyproject.toml README.md`.

### 3. Compose

- [ ] 3.1 Prod compose: drop `command`; keep the `:main` image and `MCP_AUTH_ENABLED=false` (R5, D3). Verify: `docker compose -f docker/prod/docker-compose.yml config` shows no `command`.
- [ ] 3.2 Dev compose: build the `Dockerfile`, drop the volume, `working_dir`, `command` and `UV_CACHE_DIR` (R5, D4). Verify: `docker compose -f docker/mcp/docker-compose.yml up --build -d`, then `curl localhost:3000/health` answers 200.

### 4. CI

- [ ] 4.1 Write `.github/scripts/docker_smoke.sh` per notes.md#d5 (R1, R2, R3, R4). Verify: `.github/scripts/docker_smoke.sh mcp-mixsearch:local` exits 0; `docker run -e MCP_AUTH_ENABLED=false -p 3001:3001 mcp-mixsearch:local --port 3001` answers `/health` on 3001 (R4).
- [ ] 4.2 Check that the smoke test fails on a broken image: build one whose `Dockerfile` adds `CMD ["--no-such-flag"]` and run the script on it (R6). Verify: the script exits non-zero and prints the container logs.
- [ ] 4.3 Rework `docker-publish.yml` per notes.md#d5: concurrency group, `latest` only on the default branch, one build with `load: true`, smoke test, `docker push` of the tested tags on non-PR events only, moving tags only from the tip of `main` (R6, R7, D5, D7). Verify: `actionlint` passes; the workflow passes on the PR without pushing.

### 5. Docs

- [ ] 5.1 `docker/README.md`: the image holds the app; the versioned compose recipe changes only the image tag; add the v1.1.0 rollback snippet; describe the dev compose without live reload (R5, D4). Remove or fix the stale text: the uvx notes in Production Mode and Troubleshooting, "Git (for cloning dependencies)", "Mount the project directory" and "Use uvx" under Configuration, "The container uses uv…", "the compose files pass `--mode http`", the `UV_CACHE_DIR` variable, and the LXC "Production versioned mode" file name. Update the tag table: `latest` only on pushes to `main` (R7). Verify: `grep -n -i 'uvx\|UV_CACHE_DIR' docker/README.md` finds nothing; the ci-gate link check passes.
- [ ] 5.2 `CHANGELOG.md` `Unreleased`: Changed (image holds the app; entrypoint change with migration step), Fixed (`/health` version) (D3, D6). Verify: read the entry.
- [ ] 5.3 `docs/decision-log.md`: one line for building the app into the image (D1) and one for the new entrypoint and `MCP_TRANSPORT=http` (D3), and one for moving tags (D7). Verify: read the lines.

### 6. Verification

- [ ] 6.1 Run the AGENTS.md checks. Verify: all pass.
- [ ] 6.2 Manual check in `docs/demos/2026-11-17-docker-image-pins-code-p1/`: build the image, before merge, start it with `--network none` and fetch `/health` from inside (R1), then start it normally and run a search through `/mcp` (R4); after merge, read the pushed `:main` image's revision label (R1). Verify: the record follows docs/demos/README.md.
