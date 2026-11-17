# Decision log

Decisions about constraints, interfaces, tooling and process that are not recorded in an ADR. Newest first. Plans keep their own decision logs; add a line here only when a decision applies to the project as a whole.

| Date | Decision | Reason |
| --- | --- | --- |
| 2026-11-17 | Reviews follow the `small` profile in `docs/reviews/README.md` | Sized to the project; change it here and in that file if the project grows |
| 2026-11-17 | The project is licensed MIT | Owner's choice at setup. Revisit before inviting contributions or publishing a package. |
| 2026-11-17 | Setup commits use the repository's existing Git configuration | Adoption doesn't change who commits or how |
| 2026-11-17 | Agent harnesses: Claude Code (`ENABLED_HARNESSES` in `.agents/sync_agents.py`) | Owner's choice. Adding a harness is a one-line change plus the tooling table in `AGENTS.md`. |
| 2026-11-17 | The Claude Code deny list (`.claude/settings.json`) arrived in the first pull request of the adoption, before any other agent tooling | Guardrails exist before any agent works in the repository |
