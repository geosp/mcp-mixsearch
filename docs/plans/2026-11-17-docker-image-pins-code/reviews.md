# Reviews · Build the app into the Docker image

## 2026-11-17 · design-review · plan · round 1 · changes-requested
Commit: 76a0581acef2ee60e748aab1058a8a3ca99a7848
Reviewers: fresh reader ✅ · codebase fit ✅ · zoom out ✅
Raw reports: docs/reviews/2026-11-17-docker-image-pins-code/raw/design-review-01-*.md

| ID | Sev | Lens | Finding | Resolution |
| --- | --- | --- | --- | --- |
| F1 | Major | codebase fit, zoom out, fresh reader | Rollback: v1.1.0 compose has no `@ref` (downloads new main) and uses `:main`; a revert leaves deployments on the command-less compose with a `uvx` entrypoint | open |
| F2 | Major | fresh reader | Summary omits the dev compose change (R5, D4) and that `MCP_AUTH_ENABLED=false` is required | open |
| F3 | Major | fresh reader | `ci-ok`, the ruleset and `ci-gate` are used but never defined | open |
| F4 | Major | fresh reader, zoom out | R1 scenario omits `MCP_AUTH_ENABLED=false`, and "that commit's package version" can't tell commits apart | open |
| F5 | Major | fresh reader | The plan never says what the smoke test checks; R2's Firefox scenario has no named place to run | open |
| F6 | Major | fresh reader | Unclear whether prod compose running with auth disabled is intended | open |
| F7 | Major | fresh reader | Deployments on `:latest`/`:main` break at their next pull before Rollout step 2; source of the new compose not stated | open |
| F8 | Major | fresh reader, zoom out | Rollout step 4 relies on the owner checking PR #9's smoke test; nothing enforces it | open |
| F9 | Major | fresh reader, codebase fit | R3 covers the MCP server info, but no scenario or test checks it | open |
| F10 | Nit | codebase fit, zoom out | Task 4.2 runs "its script" but no script file is named or listed in Impact | open |
| F11 | Nit | codebase fit, zoom out | The pushed image comes from a second build, not the smoke-tested one | open |
| F12 | Nit | codebase fit, zoom out | Copying README/LICENSE before the deps-only sync invalidates the deps and Firefox layers | open |
| F13 | Nit | codebase fit, zoom out | `uv==0.13.5` is a second hand-bumped uv pin with no sync note | open |
| F14 | Nit | codebase fit | `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS` is dropped without saying so | open |
| F15 | Nit | codebase fit | Task 5.1 misses stale `docker/README.md` text (UV_CACHE_DIR, git prerequisite, LXC versioned mode, …) | open |
| F16 | Nit | codebase fit | Decision-log task covers D1 only; D3 changes a public interface | open |
| F17 | Nit | zoom out | `docker-publish.yml` has no concurrency group; overlapping main pushes can leave `:main` on an older commit | open |
| F18 | Nit | fresh reader | R1, R2, R3, R5, R6 each hold two rules | open |
| F19 | Nit | fresh reader | Small gaps: D3 migration line not given, "manual check" and `mcp-service-kit` not introduced, Impact lists README/tests that What changes doesn't, breaking change stated 4 times | open |
