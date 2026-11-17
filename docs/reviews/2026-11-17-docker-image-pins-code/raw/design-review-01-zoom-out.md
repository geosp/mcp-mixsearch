Review of /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code at commit 76a0581 (plan.md, phases/01-image-with-app.md, notes.md; ADR-0001 is unaffected, as the plan says).

**Summary.** The plan fixes the root cause. The image will hold the app, installed from `uv.lock`, and Firefox will come from the venv's own Playwright. That removes both the code download at startup and the duplicate Playwright pin. The scope is small, and it's in the right places: the version lookup goes in `server.py` and the smoke test gates the existing publish job. There is one Major finding, about rollback. The rest are Nits.

## Major

**M1 · plan.md › Rollout & rollback (Rollback paragraph). Neither rollback path gives back the old code.**
- The plan says: "Rollback: run `ghcr.io/geosp/mcp-mixsearch:v1.1.0` with the v1.1.0 compose file (it still has the `uvx` command), or revert the merge commit."
- **Path 1 (v1.1.0 image and compose).** The compose file at tag v1.1.0 has `command: ["mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git", "--mode", "http"]` (`git show v1.1.0:docker/prod/docker-compose.yml`, line 13). That URL has no `@ref`, so `uvx` installs the default branch at startup. After the merge, that is the new code being rolled back from. This is the same bug the plan describes under Why. The repo has no `prod/docker-compose.v1.1.0.yml`; only the `sed` recipe in `docker/README.md` would add `@v1.1.0`.
  - Fix: tell the rollback to set the command to `...mcp-mixsearch.git@v1.1.0`.
- **Path 2 (revert the merge commit).** A revert republishes `:main` with `ENTRYPOINT ["uvx"]`. Deployments already moved to the new compose file (no `command`, Rollout step 2) would then run bare `uvx` and crash-loop under `restart: unless-stopped`.
  - Fix: say that a revert also needs the old compose `command` restored, in the same order as the forward rollout.

## Nits

- **N1 · phases/01 › 4.2 and notes.md › D5:** Task 4.2 says to "run its script locally", but D5 describes inline workflow steps and no task says where a script lives. The repo already keeps CI scripts in `.github/scripts/` (`ci_gate.py`, tested by `tests/test_ci_gate.py`); name the file so 4.2 can be done as written.
- **N2 · notes.md › D5 last paragraph:** "the BuildKit cache from step 1 makes it a re-tag, not a rebuild" is not guaranteed; any cache miss pushes a rebuilt image that was never smoke-tested. Simpler and exact: build once with `load: true` and the meta tags, then `docker push` those tags on non-PR events.
- **N3 · notes.md › D1 step 3:** copying `README.md` and `LICENSE` before the dependencies-only `uv sync --no-install-project` means a README edit rebuilds the dependency and Firefox layers. Only `pyproject.toml` and `uv.lock` are needed for that step; copy README and LICENSE in step 6.
- **N4 · plan.md › Assumptions (uv==0.13.5):** this adds a second hand-bumped uv pin. The `ci-gate.yml` header (lines 4-7) says uv is bumped by hand through `UV_VERSION`; that comment should also name the `Dockerfile`, or it will drift the way D2 warns about for Playwright.
- **N5 · plan.md › R1:** "answers 200 with that commit's package version": the version is static (`pyproject.toml:3` is `1.1.0`), so it is the same for every commit. The check proves the image runs offline, not which commit's code is inside. That is fine, but the wording promises more than it checks.
- **N6 · plan.md › Rollout step 4:** "its smoke test must pass before the owner merges it" depends on discipline, because `docker-publish.yml` is deliberately not part of `ci-ok` (D5). Say so explicitly.
- **N7 · plan.md › Risks (overlapping runs):** `docker-publish.yml` has no `concurrency` group. With the longer smoke-tested job, two quick pushes to `main` can finish out of order and leave `:main`/`:latest` on the older commit. This existed before, but the job is now longer; one line in the workflow would fix it.

## By question

1. **Root cause:** fixed, not a symptom.
2. **Simplicity:** nothing is built for a future need. N2 and N3 are small simplifications.
3. **Placement:** fine. N1 is the only gap.
4. **Failure modes:**
   - The build and its steps can safely run twice.
   - Two runs overlapping is N7.
   - A broken image is gated before the push on `main`.
   - Each listed risk has a mitigation that works.
5. **Rollout:** the deploy order is stated and there is no data migration or backfill. Rollback is wrong (M1).

Relevant files:
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/plan.md
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/notes.md
- /home/geo/develop/mcp-mixsearch/docs/plans/2026-11-17-docker-image-pins-code/phases/01-image-with-app.md
- /home/geo/develop/mcp-mixsearch/docker/prod/docker-compose.yml
- /home/geo/develop/mcp-mixsearch/.github/workflows/docker-publish.yml
- /home/geo/develop/mcp-mixsearch/.github/workflows/ci-gate.yml
- /home/geo/develop/mcp-mixsearch/docker/README.md
