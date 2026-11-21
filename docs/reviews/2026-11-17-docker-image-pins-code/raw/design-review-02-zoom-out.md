Review of /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code at commit 9bfd2c9. I read plan.md, phases/01-image-with-app.md, notes.md, ADR-0001, and the code at that commit: Dockerfile, both compose files, docker-publish.yml, ci-gate.yml, server.py, pyproject.toml, .python-version, docker/README.md, and the installed mcp_service_kit config.py and server.py.

**Root cause:** The plan fixes the cause, not a symptom. It stops the download at startup (current `ENTRYPOINT ["uvx"]` plus the compose `command: ["mcp-mixsearch@git+…"]`) and removes the second Playwright pin (`pip install playwright==1.64.1` in the Dockerfile). The rejected option of pinning the git ref in the compose file is rightly rejected.

**Simplicity and placement:** No over-building. The version test lives in `tests/` and the smoke script sits next to `.github/scripts/ci_gate.py`. D1 to D6 are the smallest changes that deliver R1 to R6.

## Findings

### Major 1: re-running an old publish run puts older code on `:main`/`:latest`
- **Where:** plan.md, What changes ("a `concurrency` group keeps two pushes to `main` from publishing out of order") and notes.md › D5 step 1. Affects R6 and D5.
- **Problem:** `concurrency: { group: docker-publish-${{ github.ref }}, cancel-in-progress: false }` only orders runs that are queued at the same time. Suppose the smoke test fails on commit A, a later commit B publishes, and the owner then clicks "Re-run jobs" on A's run. The Firefox launch and the 60 s `/health` poll make flaky failures, and so re-runs, likely. A then runs alone, passes, and pushes `main`, `latest` and `sha-A`. `:main` now quietly holds older code, which is the inverse of the problem under Why ("a restart can quietly run newer code").
- **Related:** `latest` is also pushed by `v*` tag runs, which use a different `github.ref` and so a different concurrency group. A tag on an older commit therefore moves `latest` backwards. docker/README.md's tag table lists `latest` for both main pushes and version tags, yet the same file says "`latest` follows `main`". This part already exists today.
- **Fix:**
  - Before pushing the moving tags (`main`, `latest`), check that `github.sha` is still the tip of the ref, for example `git ls-remote origin refs/heads/main`. Push `sha-…` regardless.
  - Or, at minimum, add the re-run hazard to Risks with that mitigation.
  - Also consider limiting `latest` to one event.

### Nit
- **notes.md › D5 step 3 (R2 bullet), "runs `python -c` in the image":** with `ENTRYPOINT ["mcp-mixsearch"]`, `docker run <img> python -c …` passes `python -c` to the server's argparse and fails. The script needs `--entrypoint python`. Say so, or task 4.1 will hit it first.
- **Decisions › D3 (`CMD ["--mode", "http"]`):** any user-supplied command replaces CMD. A compose file with only `command: ["--port", "3001"]` or `["--no-auth"]` therefore falls back to stdio, because `--mode` defaults to `MCP_TRANSPORT`, else stdio (`mcp_service_kit/server.py`, `--mode` `default=None`). The container then exits and `restart: unless-stopped` keeps restarting it. Adding `ENV MCP_TRANSPORT=http` to the image makes HTTP the default whatever arguments are passed, and is simpler for the migration line.
- **Rollout & rollback, step 1 then step 3:** step 1 edits the tracked `docker/prod/docker-compose.yml` in place, so the plain `git pull` in step 3 fails with "local changes would be overwritten". Step 3 needs `git checkout -- docker/prod/docker-compose.yml` (or `git stash`) first.
- **Phase 01 › 5.1 Verify:** this expects `grep -n -i 'uvx\|UV_CACHE_DIR'` to find "only the rollback snippet", but the snippet in Rollout & rollback contains no "uvx" text. The check passes vacuously or needs rewording.
- **notes.md › D5 step 1 on PRs:** the group key for PRs is `refs/pull/N/merge` with `cancel-in-progress: false`, so a new push to a PR waits behind a stale 3 to 5 minute Firefox build instead of cancelling it. ci-gate.yml cancels on PRs, and the same pattern would fit here.
- **notes.md › D1 steps 4–5:** any `uv.lock` change reruns `playwright install --with-deps firefox`, which runs `apt-get update` again. That step also leaves apt lists in the layer because its `rm -rf /var/lib/apt/lists/*` is in step 1. Worth an `rm` in the same RUN.
- **Decisions › D6:** `importlib.metadata.version("mcp-mixsearch")` raises `PackageNotFoundError` if `server.py` is run from source without the package installed. That is unlikely with uv, but a fallback, or one line saying it is not supported, removes the doubt.

## Failure modes and rollout (no further findings)
- **Docker build:**
  - The step 3 copy omits `.python-version` (3.13) and sets `UV_PYTHON_DOWNLOADS=never`, so uv uses the image's 3.14 as intended.
  - Copying only the two files for the `--no-install-project` sync is the documented uv pattern.
  - The server binds `0.0.0.0:3000` by default (`mcp_service_kit/config.py` `BaseServerConfig`), so `--network none` plus `docker exec` works.
  - Auth refusing to start without `MCP_AUTH_ENABLED=false` matches `server.py` lines 183–190 of the kit.
- **Pushing:** `docker push` after `load: true` keeps the revision label, because labels live in the image config.
- **Rollback:** The rollback snippet and the revert note are correct. There is no data migration or backfill.
