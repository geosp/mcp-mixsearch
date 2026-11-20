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
| G1 | Major | fresh reader | Summary's "serves only with `MCP_AUTH_ENABLED=false`" reads like auth is being turned off | open |
| G2 | Major | fresh reader | Summary says PR #9 is unblocked and only tested images are pushed, but omits that the smoke test is not a required check | open |
| G3 | Major | fresh reader | `MCP_AUTH_ENABLED` is never defined (what it controls, what refusing looks like) | open |
| G4 | Major | fresh reader | R1's revision-label scenario: nothing says who checks it or whether metadata-action already sets the label | open |
| G5 | Major | fresh reader | "pushes that same image" has no mechanism in plan.md (only in notes) | open |
| G6 | Major | fresh reader | Rollout step 3 assumes deployments run from a git checkout | open |
| G7 | Major | zoom out | Re-running an old publish run (or a `v*` tag on an older commit) moves `:main`/`:latest` back to older code | open |
| G8 | Nit | zoom out | notes D5: `python -c` in the image needs `--entrypoint python` | open |
| G9 | Nit | zoom out | D3: any custom `command` replaces `CMD --mode http` and falls back to stdio; `ENV MCP_TRANSPORT=http` is simpler | open |
| G10 | Nit | zoom out | Rollout step 1 edits the tracked compose file, so step 3's `git pull` conflicts | open |
| G11 | Nit | zoom out | Task 5.1 Verify grep passes vacuously | open |
| G12 | Nit | zoom out | PR runs should cancel in progress, as ci-gate does | open |
| G13 | Nit | zoom out | `playwright install --with-deps` leaves apt lists in its layer | open |
| G14 | Nit | zoom out | D6: `PackageNotFoundError` when run from source without install | open |
| G15 | Nit | fresh reader | Wording: two Summary sentences, Risks bullet 2 length, D3 stray space, build needs GitHub, manual-check timing, revert's "same command", uv pin file names, base image is current, minor vs major | open |
