---
status: accepted
date: 2026-11-21
supersedes: null
plan: docs/plans/2026-11-17-docker-image-pins-code
---

# ADR-0002: The Docker image holds the app, and a tag pins its code

## Context

Up to v1.1.0 the published image held only Python, uv and Firefox. Its entrypoint was `uvx`, and
the compose file downloaded the app from the repository's default branch every time a container
started. No image tag said what code ran, a restart could quietly run newer code, and startup
needed GitHub. The Dockerfile also pinned Playwright separately from `uv.lock`, so a dependency
bump could leave Firefox out of step with the Playwright package.

We considered pinning the git ref in the compose command instead. It was a smaller change, but
startup would still download code, and the image and code pins could drift apart.

## Decision

The image is built with the app and its dependencies installed from `uv.lock`, and Firefox is
installed by the locked Playwright. Its entrypoint is `mcp-mixsearch` in HTTP mode
(`MCP_TRANSPORT=http`), and a container command holds only server options. The publish workflow
pushes only an image that passed its smoke test, and it moves `main` and `latest` only from the
tip of `main`.

## Consequences

- An image tag names the code it runs, and the image's revision label names the commit. Starting a
  container needs no network.
- `uv.lock` is the only source of the Python dependency and Playwright versions. A Dependabot bump
  changes the image the next time it is built, and the smoke test checks Firefox against it.
- The image is larger (about 2.8 GB), and any code change needs a new image, including in the dev
  compose. Live editing happens on the host with `uv run`.
- The entrypoint and `MCP_TRANSPORT=http` are part of the deployment contract. Changing them breaks
  compose files and needs a changelog migration note.
- `.github/scripts/docker_smoke.sh` must keep passing for every image. A new runtime need, such as
  another browser, is added to the image and to the smoke test together.
- Images up to v1.1.0 still work the old way. `docker/README.md` keeps the recipe for running
  them.
