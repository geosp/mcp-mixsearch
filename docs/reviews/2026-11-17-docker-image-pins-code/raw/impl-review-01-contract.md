Review of phase 01 (R1–R7, D1–D7) on diff 3057bac..9ec30e5, repository /home/geo/develop/mcp-mixsearch.

The diff keeps most of the contract. I found one real problem (R7's "always pushed"). The rest are gaps in what the automated tests can observe, plus a few small doc mismatches.

## Major

**M1 · R7 ("Commit and version tags are always pushed"), D5 · `/home/geo/develop/mcp-mixsearch/.github/workflows/docker-publish.yml:10-13`**
- **Failure scenario:** commits A, B and C are merged to `main` one after another while A's run is still in progress (a Firefox build takes about 3–5 minutes).
  1. B's run joins the `docker-publish-refs/heads/main` group and waits as pending.
  2. When C's run arrives, GitHub cancels the pending B run. A concurrency group keeps at most one pending run, even with `cancel-in-progress: false`.
  3. `sha-B` is never built or pushed.
- **Wrong outcome:** R7 promises "Commit and version tags are always pushed", and the comment on line 10 says "Pushes to main queue in order", which they don't. The moving tags still end up correct, because C pushes `main`. What is lost is the per-commit tag that the docs offer for pinning and auditing.
- **Evidence:** the `concurrency:` block at lines 11-13, and the R7 text quoted above. This follows notes.md#d5 step 1 exactly, so it is a gap in the contract as much as in the code. The engineer should either relax R7's wording or accept the gap and fix the comment.
- **Test that would expose it:** push three commits to `main` within a minute of each other, then list the GHCR tags. `sha-<B>` is missing and B's run shows "Canceled".

## Nits
- **R4, `--help` scenario:** the smoke script and tests never run `docker run <image> --help` or check for exit 0. Argparse makes this very likely to work, but no test would fail if it broke. Add `docker run --rm "$image" --help >/dev/null` to `/home/geo/develop/mcp-mixsearch/.github/scripts/docker_smoke.sh`.
- **R4, host-port scenarios, `/home/geo/develop/mcp-mixsearch/.github/scripts/docker_smoke.sh:61-80`:** the script fetches `/health` only from inside the container, with `--network none`. It cannot see a bind to 127.0.0.1 or a broken `-p` mapping, and R4's scenarios publish a port and fetch through it. The bind address defaults to `0.0.0.0` in `mcp_service_kit/config.py:96-98`. Only the unticked manual check 6.2 would observe this. A `-p` run curled from the runner would.
- **R1, revision-label scenario:** no automated check. A smoke step could compare `docker inspect … org.opencontainers.image.revision` with `github.sha` before pushing; for now only the post-merge manual check (6.2, unticked) covers it.
- **R3, server info, `/home/geo/develop/mcp-mixsearch/tests/test_server.py:19-21`:** the test checks the `service_version` property, not the `serverInfo.version` an MCP client sees. The installed kit passes it through (`mcp_service_kit/server.py:203`, `FastMCP(version=self.service_version)`), so the risk is low. A test that builds the FastMCP app through `BaseMCPServer` and reads its version would observe the promise directly.
- **R5:** no automated test renders either compose file with `docker compose config`. Both files are correct by inspection (`/home/geo/develop/mcp-mixsearch/docker/prod/docker-compose.yml`, `/home/geo/develop/mcp-mixsearch/docker/mcp/docker-compose.yml`), and only the manual verification steps cover them.
- **R6:** the "fails before the push step" and "PR pushes nothing" scenarios depend only on step order and the `if:` conditions at `docker-publish.yml:76,84`. Both look correct. Task 4.3 is still unticked and has no recorded actionlint or PR run, so the workflow behavior is not yet observed.
- **D7, `docker-publish.yml:91`:** if `git ls-remote` fails, `tip` is empty: the pipe returns `cut`'s exit status 0, so `-e` doesn't stop the step. `main` and `latest` are then skipped while the job stays green, so a transient failure silently leaves `:main` on old code. Use `set -o pipefail` and fail when `tip` is empty.
- **D7:** the code uses `git ls-remote "$REPO_URL"`, not `origin` as D7 says. The behavior is the same for a public repository. Wording only.
- **R7:** the semver tags `1` and `1.2` (`docker-publish.yml:50-51`) also move. Re-running an old `v1.1.x` run moves `1.1` back. This is allowed by "version tags are always pushed", but the Terms section doesn't list them as moving tags.
- **R6/task 4.2, `docker_smoke.sh:82`:** if `/health` returns something that isn't JSON or has no `version`, the `python3` parse exits non-zero under `set -e` and bypasses `fail`, so no container logs are printed.
- **Docs, `/home/geo/develop/mcp-mixsearch/docker/README.md:96,240`:** these lines use `:v1.1.0` as the example of a pinned tag. With the new compose file (no `command`), a `:v1.1.0` image doesn't start, because its entrypoint is `uvx`. Use `v1.2.0` or point to the rollback snippet.
- **D3, `/home/geo/develop/mcp-mixsearch/CHANGELOG.md:15-16`:** the migration line says `command: ["--port", "3001"]` where D3 says "for example `--port 3001`". The meaning is the same.
- **Plan bookkeeping, `/home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/plan.md:252`:** the phase table still shows `0/14` tasks, but 12 are ticked.
- **Phase completeness:** tasks 4.3 (the workflow rework, which is implemented) and 6.2 (the manual check) are unticked. So R6 and R7 have no recorded verification, and neither do the R1 label scenario or the R4 search check.

## Promises with enforcing code and tests
- **R1 (start with no network, /health 200):** enforced by `Dockerfile:50-52` and the entrypoint. Checked by `docker_smoke.sh:61-90` (`--network none`, fetch from inside the container).
- **R2 (playwright version, Firefox launch):** enforced by `Dockerfile:50-55` (`--locked`, the venv's `playwright install --with-deps`). Checked by `docker_smoke.sh:42-56`.
- **R3 (/health version):** enforced by `server.py:26` and the `/health` handler. Checked by `tests/test_server.py:10-16` (fails against the old `1.0.0`) and `docker_smoke.sh:82-84`.
- **R4 `--port 3001`:** checked by `docker_smoke.sh:89`.
- **D3:** `ENV MCP_TRANSPORT=http`, no `CMD` and `ENTRYPOINT ["mcp-mixsearch"]` (`Dockerfile:60-69`). The `--mode` default comes from the environment (`mcp_service_kit/server.py:372-378, 421`).
- **D1:** dependency-only sync followed by the app sync.
- **D2:** no separate pin left in the `Dockerfile`.
- **D6:** `importlib.metadata`.
- **R7 for `latest`:** `flavor: latest=false` plus `enable={{is_default_branch}}`, and the push loop skips `*:main|*:latest` unless the commit is the tip.
- **Uv pin:** the Assumptions' cross-references between the `Dockerfile` and `ci-gate.yml` are present, and `UV_VERSION` is 0.13.5.
- **Other places that publish images:** I searched every workflow. Only `docker-publish.yml` pushes images, and no other compose files exist.
