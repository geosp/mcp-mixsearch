I found no Blockers. The image, compose files, version change and docs keep R1–R5 and D1–D6 as written. The real gap is the publish workflow (R6, R7, D7): its push logic only runs on a real push, so nothing in the diff checks it.

Range reviewed: 3057bac..a3214a7. I read the code statically and ran nothing.

## Promise map (what enforces each promise, and what would catch a regression)

- **R1 S1** (`--network none`, `/health` is 200): `Dockerfile:50-60` installs the deps and the app at build time; `ENTRYPOINT` is at `Dockerfile:69`. Tested by `.github/scripts/docker_smoke.sh:130-131` (inside the container, `--network none`).
- **R1 S2** (revision label is C): `docker-publish.yml`, where the metadata labels are passed to the build. The smoke script checks the label when `EXPECTED_REVISION` is set (`docker_smoke.sh:46-51`), and the workflow sets it to `github.sha`. Task 6.2 (the manual read after merge) is still open.
- **R2 S1** (playwright reports V): `Dockerfile:51` (`--locked`). Tested by `docker_smoke.sh:35-39, 54-59`.
- **R2 S2** (Firefox launches): `Dockerfile:54`. Tested by `docker_smoke.sh:61-69`. A browser build that doesn't match Playwright would fail the launch, so the test can see it.
- **R3 S1/S2** (version is X): `server.py:26, 54, 76`. Tested by `tests/test_server.py:10-24`. These tests would fail without the change, because the old constant `1.0.0` differs from the `pyproject.toml` version `1.1.0`. In the image, `docker_smoke.sh:121-125` also compares against `pyproject.toml`.
- **R4 S1/S2/S3** (port 3000, `--port 3001`, `--help`): `Dockerfile:62-69` sets `MCP_TRANSPORT=http` and has no `CMD`. I checked `mcp_service_kit/server.py`: `--mode` defaults to None, so the environment value applies. Tested by `docker_smoke.sh:130-132` and `:72-74`.
- **R5**: `docker/prod/docker-compose.yml` and `docker/mcp/docker-compose.yml` have no `command` and no volumes. No test checks this; see the Nits.
- **R6 S1** (smoke failure stops the push): the smoke step runs before the login and push steps, which run only on success by default. The only check is manual task 4.2.
- **R6 S2** (a PR runs the smoke test and pushes nothing): `if: github.event_name != 'pull_request'` on the login and push steps. Task 4.3 (a PR run) is still unticked.
- **R7 S1/S2** and **D7**: the "Push the tested image" step in `docker-publish.yml`, plus `flavor: latest=false` and `type=raw,value=latest,enable={{is_default_branch}}`. No test covers this.
- **D1–D6**: the Dockerfile layer order matches notes.md#d1. The changelog migration line matches the D3 wording. The decision-log has the D1, D3 and D7 lines. `ci-gate.yml` names the Dockerfile in its header comment.

## Findings

### Major 1: the moving-tag rule has no test that could observe it (R7, D7)
- **Where:** the `.github/workflows/docker-publish.yml` "Push the tested image" step (inline `run:` script).
- **Failure scenario:** a later edit breaks the moving-tag logic, for example a typo in the `*:main|*:latest` pattern or a wrong comparison against `$SHA`. Then commit B lands on `main`, someone re-runs the run for the older commit A, and it moves `:main` and `:latest` back to A. That is the exact case R7 S1 forbids, and nothing fails beforehand.
- **Why nothing catches it:** the step only runs on non-PR events, so the PR run (task 4.3's check) never executes it. `actionlint` checks syntax, not this logic. The other R7 scenario (a `v*` tag run pushes no `latest`) depends on metadata-action's flavor and `enable` handling, which also only shows on a real tag push.
- **Fix:** move the tag selection into a script, for example `.github/scripts/select_push_tags.sh` or a Python helper tested in `tests/` like `ci_gate.py`. It would take `TAGS`, `SHA` and `tip`, and print the tags to push. Unit tests would cover:
  - tip ≠ SHA: `sha-A` is pushed, `main` and `latest` are not;
  - tip = SHA: all tags are pushed;
  - the tag set for a `v*` run: no `latest`.
- **Alternative:** a `workflow_dispatch` dry run that prints the selected tags.

### Major 2: neither R6 scenario has an automated check (R6, D5)
- **Where:** the step order in `docker-publish.yml`; tasks 4.2 and 4.3.
- **Failure scenario:** someone later adds `if: always()` or `continue-on-error: true` to the smoke step, or moves the push into `build-push-action` with `push: true`. A broken image is then pushed.
- **Why nothing catches it:** the "fails before push" scenario was checked once, by hand (task 4.2, `CMD ["--no-such-flag"]`). Task 4.3's PR run is still unticked, so "PR runs smoke and pushes nothing" isn't recorded as observed either.
- **What would observe it:** at minimum, a recorded PR run log showing the smoke test ran and the login/push steps were skipped. For the failure path, a test that asserts the workflow's structure: parse the YAML, then check that the push step comes after the smoke step, that neither has `continue-on-error` or `always()`, and that the build step has `push: false`.

## Nits
- **`docker-publish.yml`, push step (R7, D7):** a `git ls-remote` failure exits 1 before anything is pushed, including `sha-…` and version tags on a `v*` run that has no moving tags. R7 says "Commit and version tags are always pushed". Failing safe is defensible, but the tip check could run only when a `:main` or `:latest` tag is present.
- **`docker-publish.yml`, push step (D7):** it calls `git ls-remote "$REPO_URL"` with no credentials, not `git ls-remote origin` as D7 says. This works only while the repo is public. If it goes private, every push run fails.
- **`docker-publish.yml`, push step (R7):** the tip is read once, before the pushes. If main moves during that short window (between the check and `docker push <...>:main`), the old run could still move `main` back. In practice this is unlikely, because the newer run must build Firefox first. I can't rule it out.
- **`docker-publish.yml` triggers (R7):** the workflow still runs on `master`. A `:master` branch tag would be pushed without the tip check. That's harmless while `main` is the only default branch.
- **`docker_smoke.sh:72`, `docker run ... --help | grep -q` (R4 S3):** under `pipefail`, if `grep -q` exits early and docker gets SIGPIPE, a good image could fail. The risk is low because the help text is small, and I haven't verified it can happen. `grep` without `-q`, piped to `/dev/null`, would avoid it.
- **`docker_smoke.sh:131` (R4 S2):** the `--port 3001` case is checked inside a `--network none` container, not through `-p 3001:3001` as the scenario says. Only port 3000 is checked through a published port (`:132`). It is close enough, but not literally the scenario.
- **`docker_smoke.sh:124` (R3):** it compares `/health` with the `pyproject.toml` version, not the installed package's metadata. The two are the same in a locked build, so the check is equivalent in practice.
- **`docker_smoke.sh:47` with the workflow's `EXPECTED_REVISION: github.sha` (R1 S2):** on `pull_request` events this is the merge commit. I believe metadata-action also uses it unless `DOCKER_METADATA_PR_HEAD_SHA` is set, but I haven't verified that. The PR run will show it.
- **Compose files (R5):** no automated `docker compose config` check exists; only the manual checks in tasks 3.1 and 3.2. A regression that adds `command:` or a volume back would go unnoticed until deploy.
- **R1 ("must never download code"):** only startup and `/health` are run under `--network none`. Lazy downloads on the first search path aren't covered. That's beyond the scenario's wording.
- **Phase file:** task 4.3's work is in the diff but still unticked, and task 6.2 (the manual demo with the revision label read after merge) is open. So the evidence for R1 S2 and R6 S2 is still to come.

## Relevant files
- /home/geo/develop/mcp-mixsearch/.github/workflows/docker-publish.yml
- /home/geo/develop/mcp-mixsearch/.github/scripts/docker_smoke.sh
- /home/geo/develop/mcp-mixsearch/Dockerfile
- /home/geo/develop/mcp-mixsearch/server.py
- /home/geo/develop/mcp-mixsearch/tests/test_server.py
- /home/geo/develop/mcp-mixsearch/docker/prod/docker-compose.yml
- /home/geo/develop/mcp-mixsearch/docker/mcp/docker-compose.yml
