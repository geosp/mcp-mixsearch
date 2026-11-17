# Notes · Build the app into the Docker image

## D1 · Build layout

Current `Dockerfile` (on `main` at plan time): `python:3.14-slim`, an apt list with Playwright's
system libraries and fonts, `pip install uv`, `pip install playwright==1.64.1`,
`playwright install firefox` and `install-deps firefox`, `ENTRYPOINT ["uvx"]`.

Planned order, so a code-only change rebuilds only the last layers:

1. Base image and the existing apt list (unchanged).
2. `pip install --no-cache-dir uv==0.13.5`; `ENV UV_PYTHON_DOWNLOADS=never UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`.
3. `WORKDIR /app`; copy `pyproject.toml`, `uv.lock`, `README.md`, `LICENSE` (hatchling reads the last two).
4. `uv sync --locked --no-dev --no-install-project` (dependencies only).
5. `/app/.venv/bin/playwright install --with-deps firefox` (D2).
6. Copy `server.py`, `config.py`, `features/`; `uv sync --locked --no-dev --no-editable`.
7. `ENV PATH=/app/.venv/bin:$PATH`; `EXPOSE 3000`; `ENTRYPOINT ["mcp-mixsearch"]`; `CMD ["--mode", "http"]`.

The server binds `0.0.0.0:3000` by default (`mcp_service_kit.config.BaseServerConfig`: `host`
default `"0.0.0.0"`, `port` default `3000`), so no host flag is needed. With auth enabled (the
default) and no auth provider, the server refuses to start; that is why `MCP_AUTH_ENABLED=false`
is set by the compose files and the smoke test, not by the image.

The wheel ships only `server.py`, `config.py` and `features/` (`[tool.hatch.build.targets.wheel]`),
which includes the tool instruction `.md` files under `features/web_search/`.

## D5 · Smoke test mechanics

In `docker-publish.yml`, before the existing push step:

1. Build with `docker/build-push-action` and `load: true`, tagged `mcp-mixsearch:smoke`.
2. R2: `docker run --rm --entrypoint python mcp-mixsearch:smoke -c '<print playwright version>'`,
   compared with the version read from `uv.lock` on the runner; then a script that launches
   headless Firefox, opens `about:blank` and exits.
3. R1/R4: `docker run -d --network none -e MCP_AUTH_ENABLED=false mcp-mixsearch:smoke`, then poll
   `/health` from inside the container with `docker exec … python -c` (urllib) for up to 60 s,
   and compare its `version` with `pyproject.toml`.
4. On failure, print `docker logs` and fail the job.

The push step then builds again with `push: true` for non-PR events; the BuildKit cache from step 1
makes it a re-tag, not a rebuild. Actions keep their existing tag pins in this workflow (non-goal).
