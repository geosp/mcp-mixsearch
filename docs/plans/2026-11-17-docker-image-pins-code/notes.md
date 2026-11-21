# Notes · Build the app into the Docker image

## D1 · Build layout

Current `Dockerfile` (on `main` at plan time): `python:3.14-slim`, an apt list with Playwright's
system libraries and fonts, `pip install uv`, `pip install playwright==1.64.1`,
`playwright install firefox` and `install-deps firefox`, `ENTRYPOINT ["uvx"]`.

Planned order, so a code-only or README change rebuilds only the last layers:

1. Base image and the existing apt list (unchanged).
2. `pip install --no-cache-dir uv==0.13.5`, with a comment naming `UV_VERSION` in `ci-gate.yml`
   (and that file's header names the `Dockerfile`).
   `ENV UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`.
   `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true` is dropped: `--with-deps` installs the host
   libraries Playwright checks for.
3. `WORKDIR /app`; copy only `pyproject.toml` and `uv.lock`.
4. `uv sync --locked --no-dev --no-install-project` (dependencies only).
5. `/app/.venv/bin/playwright install --with-deps firefox && rm -rf /var/lib/apt/lists/*` (D2);
   `--with-deps` runs `apt-get`, so its lists are removed in the same layer.
6. Copy `README.md`, `LICENSE` (hatchling reads both), `server.py`, `config.py`, `features/`;
   `uv sync --locked --no-dev --no-editable`.
7. `ENV PATH=/app/.venv/bin:$PATH MCP_TRANSPORT=http`; `EXPOSE 3000`; `ENTRYPOINT ["mcp-mixsearch"]`;
   no `CMD` (D3).

The server binds `0.0.0.0:3000` by default (`mcp_service_kit.config.BaseServerConfig`: `host`
default `"0.0.0.0"`, `port` default `3000`), so no host flag is needed. With auth enabled (the
default) and no auth provider, the server refuses to start; that is why `MCP_AUTH_ENABLED=false`
is set by the compose files and the smoke test, not by the image.

The wheel ships only `server.py`, `config.py` and `features/` (`[tool.hatch.build.targets.wheel]`),
which includes the tool instruction `.md` files under `features/web_search/`.

## D5 · Smoke test mechanics

`docker-publish.yml` after this plan:

1. `concurrency`: the same pattern as `ci-gate.yml`, one group per PR and one per commit
   otherwise, cancelling only on PRs. A group shared by every `main` push would keep only one
   pending run and cancel the others, so their `sha-…` tags would never be pushed. Ordering of
   the moving tags comes from the tip check in step 4.
2. Metadata tags: replace the bare `latest` with `type=raw,value=latest,enable={{is_default_branch}}`
   (R7). Build once with `docker/build-push-action`, `load: true`, `push: false`, and the tags and
   labels from `docker/metadata-action` (which include `org.opencontainers.image.revision`).
3. Run `.github/scripts/docker_smoke.sh <first tag>`. The script:
   - R2: runs `docker run --entrypoint python <image> -c …` (the entrypoint is the server) to print the `playwright` version and compares it with the
     version in `uv.lock` on the runner; then launches headless Firefox, opens `about:blank` and
     exits;
   - R1, R4: `docker run -d --network none -e MCP_AUTH_ENABLED=false <image>`, then polls
     `/health` from inside the container with `docker exec … python -c` (urllib) for up to 60 s;
   - R3: compares `/health`'s `version` with `pyproject.toml`;
   - on any failure prints `docker logs`, removes the container and exits non-zero.
4. On non-PR events only: `docker push` each tag from step 2, so the pushed image is the tested one.
   `.github/scripts/select_push_tags.py` picks the tags: when `main` or `latest` is among them, it
   compares `github.sha` with `git ls-remote --exit-code <repo URL> refs/heads/main` and drops
   those two if they differ; an unreadable tip fails the step (R7, D7). `tests/test_docker_publish.py`
   tests the selection and checks the workflow's step order and the compose files (R5, R6).

Actions keep their existing tag pins in this workflow (non-goal).
