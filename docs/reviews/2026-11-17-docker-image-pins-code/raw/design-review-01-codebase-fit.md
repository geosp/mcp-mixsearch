Review of docs/plans/2026-11-17-docker-image-pins-code at 76a0581 (plan.md, phases/01-image-with-app.md, notes.md)

I found no Blockers, one Major and seven Nits. Most of what the plan says about the code is accurate, and I checked it against the code:
- `Dockerfile`: `pip install playwright==1.64.1` and `ENTRYPOINT ["uvx"]`.
- Both compose files: the `command`, the volume, `working_dir` and `UV_CACHE_DIR`.
- `server.py:24`: `SERVICE_VERSION = "1.0.0"`, used at lines 52 and 74, while `pyproject.toml` says 1.1.0.
- The `pyproject.toml` comment on the Playwright pin, and the hatch `only-include`.
- `ci-gate.yml`: `UV_VERSION: "0.13.5"`, and the lychee `--offline` job.
- In mcp_service_kit, `BaseServerConfig` defaults to host 0.0.0.0 and port 3000, and `auth_enabled` defaults to True. The server refuses to start in HTTP mode when no auth provider is set (`server.py:183-190`). The CLI flag `--mode` overrides the env var, and the `--help` argparse behaviour matches what the plan expects.
- `browser.py:44` launches Firefox through Playwright.
- `docs/demos/README.md` exists, and so does the git tag `v1.1.0`.
- ADR-0001 is accepted and nothing supersedes it. The plan does not touch search, so there is no conflict.

## Major

**M1 · plan.md › Rollout & rollback (rollback paragraph): the rollback recipe does not restore v1.1.0's code, and as written it may not start.**
The plan says: "Rollback: run `ghcr.io/geosp/mcp-mixsearch:v1.1.0` with the v1.1.0 compose file (it still has the `uvx` command)". The repo has no "v1.1.0 compose file". `docker/prod/` holds only `docker-compose.yml`, and at tag v1.1.0 that file has two problems:
- It sets `image: ghcr.io/geosp/mcp-mixsearch:main`, which after the merge is the new image whose entrypoint is `mcp-mixsearch`. Combined with the `uvx`-style `command`, that is exactly the failure the Risks section describes.
- Its command is `mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git` with no ref. Even after the image tag is changed by hand, it downloads the new `main` code at startup, not v1.1.0's.

`docker/README.md`, in "Creating Versioned Compose Files", shows that a real v1.1.0 rollback needs both `sed` edits: the image tag and `.git@v1.1.0`. This is the safety net for a change the plan itself labels BREAKING, so the steps should be written out exactly. Either give the two-line compose (`image: …:v1.1.0` plus `command: ["mcp-mixsearch@git+…mcp-mixsearch.git@v1.1.0", "--mode", "http"]`) or point to that recipe as it exists at v1.1.0. Task 5.1 rewrites that recipe, so the docs must keep a way to roll back to the old pinned setup.

## Nits

- **phases/01 › Task 4.2, and plan.md › Impact:** 4.2 says to "run its script locally", but notes.md#d5 describes the smoke test as inline workflow steps, and Impact names no script file (no `.github/scripts/…`). As written, R6's first scenario ("job fails before the push step") has no runnable script to test. Name a script file and add it to Impact.
- **notes.md › D1, step 3:** `README.md` and `LICENSE` are copied before `uv sync --no-install-project`, which does not build the project. So any README edit invalidates the dependency layer and the Firefox layer, the slow ~3–5 min part, which goes against D1's aim that "code changes reuse the dependency layer". Copy them in step 6 instead.
- **notes.md › D1, step 2:** the new ENV list drops `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true`, which the current `Dockerfile` sets, and the plan doesn't say so. With `--with-deps` it is probably not needed, but the removal should be stated.
- **notes.md › D5, final paragraph:** the image that gets pushed comes from a second build, not the one the smoke test checked. The two match only if the cache hits fully. Building once with all tags plus `load: true`, smoke-testing that, then `docker push` would make R6's "must not push an image whose smoke test failed" hold by construction.
- **plan.md › Assumptions (uv pin):** `uv==0.13.5` would be a second hand-maintained copy of the `ci-gate.yml` `UV_VERSION`, the same kind of drift D2 rejects for Playwright. Neither copy is visible to Dependabot. At least add a "keep in sync" comment on both.
- **phases/01 › Task 5.1:** `docker/README.md` has more stale text than the task names:
  - the `UV_CACHE_DIR` env-var bullet;
  - "the compose files pass `--mode http`" (now the image's CMD does);
  - "The container uses uv for Python package management";
  - "Git (for cloning dependencies)" under Prerequisites;
  - "Production versioned mode" in the LXC section.

  List them so they get fixed.
- **phases/01 › Task 1.1 vs R3:** R3 also covers the MCP server info version (`service_version`, `server.py:73-74`), but the planned test checks only `/health`.
- **phases/01 › Task 5.3:** the decision-log line covers only D1. D3 changes a public interface (the image's entrypoint and default command), and AGENTS.md says interface changes go in `docs/decision-log.md`.

Relevant files:
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/plan.md
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/phases/01-image-with-app.md
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/notes.md
- /home/geo/develop/mcp-mixsearch/Dockerfile
- /home/geo/develop/mcp-mixsearch/docker/prod/docker-compose.yml
- /home/geo/develop/mcp-mixsearch/docker/mcp/docker-compose.yml
- /home/geo/develop/mcp-mixsearch/docker/README.md
- /home/geo/develop/mcp-mixsearch/.github/workflows/docker-publish.yml
- /home/geo/develop/mcp-mixsearch/.github/workflows/ci-gate.yml
- /home/geo/develop/mcp-mixsearch/server.py
