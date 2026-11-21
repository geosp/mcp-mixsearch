# Reviews · Build the app into the Docker image

## 2026-11-17 · design-review · plan · round 1 · changes-requested
Commit: 76a0581acef2ee60e748aab1058a8a3ca99a7848
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅
Raw reports: docs/reviews/2026-11-17-docker-image-pins-code/raw/design-review-01-*.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | codebase fit, zoom out, fresh reader | Rollback: v1.1.0 compose has no `@ref` (downloads new main) and uses `:main`; a revert leaves deployments on the command-less compose with a `uvx` entrypoint | fixed: Rollout & rollback (v1.1.0 snippet with image and `@v1.1.0`; revert restores `command`) |
| F2 | Major | fresh reader | Summary omits the dev compose change (R5, D4) and that `MCP_AUTH_ENABLED=false` is required | fixed: Summary |
| F3 | Major | fresh reader | `ci-ok`, the ruleset and `ci-gate` are used but never defined | fixed: Terms (`ci-ok`, Ruleset) |
| F4 | Major | fresh reader, zoom out | R1 scenario omits `MCP_AUTH_ENABLED=false`, and "that commit's package version" can't tell commits apart | fixed: R1 (auth env; revision label scenario) |
| F5 | Major | fresh reader | The plan never says what the smoke test checks; R2's Firefox scenario has no named place to run | fixed: Terms › Smoke test; notes.md#d5 |
| F6 | Major | fresh reader | Unclear whether prod compose running with auth disabled is intended | contested: prod already runs with auth off, the server has no auth provider and docker/README says to front it with a gateway; stated in Assumptions |
| F7 | Major | fresh reader | Deployments on `:latest`/`:main` break at their next pull before Rollout step 2; source of the new compose not stated | fixed: Risks (auto-pull) and Rollout steps 1, 3 |
| F8 | Major | fresh reader, zoom out | Rollout step 4 relies on the owner checking PR #9's smoke test; nothing enforces it | fixed: D5 and Rollout step 5 say the owner checks it |
| F9 | Major | fresh reader, codebase fit | R3 covers the MCP server info, but no scenario or test checks it | fixed: R3 second scenario; task 1.1 |
| F10 | Nit | codebase fit, zoom out | Task 4.2 runs "its script" but no script file is named or listed in Impact | fixed: Terms, Impact, tasks 4.1-4.2 (`.github/scripts/docker_smoke.sh`) |
| F11 | Nit | codebase fit, zoom out | The pushed image comes from a second build, not the smoke-tested one | fixed: notes.md#d5 step 4; task 4.3 |
| F12 | Nit | codebase fit, zoom out | Copying README/LICENSE before the deps-only sync invalidates the deps and Firefox layers | fixed: notes.md#d1 steps 3, 6 |
| F13 | Nit | codebase fit, zoom out | `uv==0.13.5` is a second hand-bumped uv pin with no sync note | fixed: Assumptions; notes.md#d1 step 2; task 2.2 |
| F14 | Nit | codebase fit | `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS` is dropped without saying so | fixed: notes.md#d1 step 2 |
| F15 | Nit | codebase fit | Task 5.1 misses stale `docker/README.md` text (UV_CACHE_DIR, git prerequisite, LXC versioned mode, …) | fixed: task 5.1 |
| F16 | Nit | codebase fit | Decision-log task covers D1 only; D3 changes a public interface | fixed: task 5.3 |
| F17 | Nit | zoom out | `docker-publish.yml` has no concurrency group; overlapping main pushes can leave `:main` on an older commit | fixed: What changes; notes.md#d5 step 1; task 4.3 |
| F18 | Nit | fresh reader | R1, R2, R3, R5, R6 each hold two rules | accepted: each pair is one testable property; splitting adds IDs without clarity |
| F19 | Nit | fresh reader | Small gaps: D3 migration line not given, "manual check" and `mcp-service-kit` not introduced, Impact lists README/tests that What changes doesn't, breaking change stated 4 times | fixed: D3 migration line, Terms (manual check, mcp-service-kit), What changes matches Impact, breaking change marked once in D3 |

## 2026-11-19 · design-review · plan · round 2 · changes-requested
Commit: 9bfd2c9eb45987e39039aca07db1a4f9d0cbd5ce
Reviewers: fresh reader ✅ · zoom out ✅ (lenses that raised round 1 Majors, per the `small` profile)
Raw reports: docs/reviews/2026-11-17-docker-image-pins-code/raw/design-review-02-*.md
Round 1 fixes: none came back. The two-rules Nits on R1, R5, R6 stay closed (F18 accepted).

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| G1 | Major | fresh reader | Summary's "serves only with `MCP_AUTH_ENABLED=false`" reads like auth is being turned off | fixed: Summary (no auth provider, gateway) |
| G2 | Major | fresh reader | Summary says PR #9 is unblocked and only tested images are pushed, but omits that the smoke test is not a required check | fixed: Summary last sentence |
| G3 | Major | fresh reader | `MCP_AUTH_ENABLED` is never defined (what it controls, what refusing looks like) | fixed: Terms › `MCP_AUTH_ENABLED` |
| G4 | Major | fresh reader | R1's revision-label scenario: nothing says who checks it or whether metadata-action already sets the label | fixed: Terms › Revision label, Manual check; R1 scenario; task 6.2 |
| G5 | Major | fresh reader | "pushes that same image" has no mechanism in plan.md (only in notes) | fixed: D5 |
| G6 | Major | fresh reader | Rollout step 3 assumes deployments run from a git checkout | fixed: Rollout step 3 |
| G7 | Major | zoom out | Re-running an old publish run (or a `v*` tag on an older commit) moves `:main`/`:latest` back to older code | fixed: new R7 and D7; notes.md#d5 steps 2, 4; tasks 4.3, 5.1, 5.3 |
| G8 | Nit | zoom out | notes D5: `python -c` in the image needs `--entrypoint python` | fixed: notes.md#d5 step 3 |
| G9 | Nit | zoom out | D3: any custom `command` replaces `CMD --mode http` and falls back to stdio; `ENV MCP_TRANSPORT=http` is simpler | fixed: D3 (`ENV MCP_TRANSPORT=http`, no `CMD`); R4 second scenario; notes.md#d1 step 7; tasks 2.2, 4.1 |
| G10 | Nit | zoom out | Rollout step 1 edits the tracked compose file, so step 3's `git pull` conflicts | fixed: Rollout step 3 |
| G11 | Nit | zoom out | Task 5.1 Verify grep passes vacuously | fixed: task 5.1 |
| G12 | Nit | zoom out | PR runs should cancel in progress, as ci-gate does | fixed: notes.md#d5 step 1 |
| G13 | Nit | zoom out | `playwright install --with-deps` leaves apt lists in its layer | fixed: notes.md#d1 step 5 |
| G14 | Nit | zoom out | D6: `PackageNotFoundError` when run from source without install | accepted: running without the package installed is unsupported; stated in D6 |
| G15 | Nit | fresh reader | Wording: two Summary sentences, Risks bullet 2 length, D3 stray space, build needs GitHub, manual-check timing, revert's "same command", uv pin file names, base image is current, minor vs major | fixed: Summary, Risks, D3, Terms, Assumptions, Rollout steps 3-4 and revert paragraph |

## 2026-11-21 · approved · plan (and phase 01)

## 2026-11-21 · impl-review · phase 01 · round 1 · changes-requested
Diff: 3057bac1dabfe64b7511a7cd52bc6bb5eb45a51b..9ec30e586a347924edd18863e2d8e256a782aec0
Reviewers: contract ✅ (the `small` profile's only impl lens)
Raw report: docs/reviews/2026-11-17-docker-image-pins-code/raw/impl-review-01-contract.md

| ID | Sev | Lens | Req | Finding | Resolution |
| --- | --- | --- | --- | --- | --- |
| I1 | Major | contract | R7, D5 | A concurrency group keeps one pending run, so a third push to `main` cancels the second and its `sha-…` tag is never pushed | fixed: per-commit concurrency group in docker-publish.yml (notes.md#d5 step 1, Decision log); observed by the PR and main runs |
| I2 | Nit | contract | R4 | Nothing runs `--help` and checks exit 0 | fixed: `--help` check in docker_smoke.sh |
| I3 | Nit | contract | R4 | The smoke test never fetches `/health` through a published port | fixed: published-port check in docker_smoke.sh; fails on an image bound to 127.0.0.1 |
| I4 | Nit | contract | R1 | No automated check of the revision label | fixed: EXPECTED_REVISION check in docker_smoke.sh, set to github.sha by the workflow; fails on a wrong SHA |
| I5 | Nit | contract | R3 | Test reads `service_version`, not the version the FastMCP app reports | fixed: tests/test_server.py reads serverInfo through an MCP client; fails with the hard-coded version |
| I6 | Nit | contract | R5 | No automated `docker compose config` check | accepted: compose files have no build logic; rendered by `docker compose config` in tasks 3.1-3.2 |
| I7 | Nit | contract | R6 | Workflow behaviour not yet observed (task 4.3 open) | open: observed when the PR's docker-publish run passes (task 4.3) |
| I8 | Nit | contract | D7 | A failing `git ls-remote` leaves `tip` empty and silently skips `main`/`latest` | fixed: pipefail, `--exit-code` and an empty-tip failure in the push step |
| I9 | Nit | contract | D7 | Code uses the repo URL, D7 says `origin` | accepted: the repository URL and `origin` name the same public repository |
| I10 | Nit | contract | R7 | Semver `1`, `1.2` tags also move on re-runs | accepted: version tags are pushed on every run by design (R7); only `main` and `latest` are moving tags |
| I11 | Nit | contract | R6 | A non-JSON `/health` body exits through `set -e`, bypassing `fail` and its logs | fixed: version parse routes through `fail` in docker_smoke.sh |
| I12 | Nit | contract | docs | `docker/README.md` uses `:v1.1.0` as a pinned example, which won't start with the new compose | fixed: docker/README.md examples use `:v1.2.0` |
| I13 | Nit | contract | D3 | CHANGELOG migration example differs in form from D3 | accepted: same meaning; the compose form is clearer in a changelog |
| I14 | Nit | contract | plan | Phases table shows 0/14 | fixed: Phases table |
| I15 | Nit | contract | phase | Tasks 4.3 and 6.2 unticked | open: task 4.3 waits for the PR run, task 6.2 for the manual check |

## 2026-11-21 · impl-review · phase 01 · round 2 · changes-requested
Diff: 3057bac1dabfe64b7511a7cd52bc6bb5eb45a51b..a3214a7294d607adf5c62e73ae32f9739d1fc078
Reviewers: contract ✅
Raw report: docs/reviews/2026-11-17-docker-image-pins-code/raw/impl-review-02-contract.md
Round 1 fixes: none came back. Closed round 1 findings (I6, I9, I10, I13) stay closed.

| ID | Sev | Lens | Req | Finding | Resolution |
| --- | --- | --- | --- | --- | --- |
| J1 | Major | contract | R7, D7 | The moving-tag logic is inline in the workflow and runs only on real pushes; no test can observe it | fixed: `.github/scripts/select_push_tags.py`, tests in tests/test_docker_publish.py; they fail when the tip check is removed |
| J2 | Major | contract | R6, D5 | No automated check that the push follows a passing smoke test and is skipped on PRs | fixed: tests/test_docker_publish.py checks build `push: false`, step order, no `continue-on-error`/`always()`, PR `if:`; they fail with `push: true` |
| J3 | Nit | contract | R7 | A failing `ls-remote` blocks version and sha tags even when no moving tag is pushed | fixed: the tip is read only when a moving tag is present (test_version_run_needs_no_tip_and_pushes_every_tag) |
| J4 | Nit | contract | D7 | Unauthenticated `ls-remote` works only while the repo is public | accepted: the repository is public; if it goes private the step fails loudly, not silently |
| J5 | Nit | contract | R7 | Main can move between the tip read and `docker push :main` | accepted: the window is the seconds between the tip read and the push, while a newer run needs a ~4 min build first |
| J6 | Nit | contract | R7 | A `master` push would push `:master` without the tip check | fixed: `master` triggers removed from docker-publish.yml |
| J7 | Nit | contract | R4 | `--help \| grep -q` can SIGPIPE under pipefail | fixed: `grep >/dev/null` instead of `grep -q` in docker_smoke.sh |
| J8 | Nit | contract | R4 | `--port 3001` checked inside the container, not through `-p` | accepted: port 3000 is checked through a published port, and `--port 3001` binds the same way; the published path is what `-p` adds |
| J9 | Nit | contract | R3 | Smoke compares with pyproject.toml, not installed metadata | accepted: equal in a locked build; tests/test_server.py checks against installed metadata |
| J10 | Nit | contract | R1 | PR `github.sha` vs metadata-action's revision not yet observed | open: observed by the PR's docker-publish run (task 4.3) |
| J11 | Nit | contract | R5 | No automated compose check (as I6) | fixed: test_compose_files_run_the_image_as_built |
| J12 | Nit | contract | R1 | Lazy downloads on the search path aren't run offline | accepted: searching needs the network by design; R1 is about code, which startup alone loads |
| J13 | Nit | contract | phase | Tasks 4.3 and 6.2 open (as I15) | open: task 4.3 waits for the PR run, task 6.2 for the manual check |
