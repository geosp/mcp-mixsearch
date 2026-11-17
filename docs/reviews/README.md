# Reviews

Plans in [docs/plans/](../plans/README.md) are reviewed with Skill Central's `design-review` skill before implementation and `impl-review` after each phase. Both skills log each round in the plan's `reviews.md`. This file adds the project rules: what makes a review count as a gate, how many reviewers to run, where the raw reports go, and how to keep reviews within a usage budget.

- **Informal review:** a stress-test at any time. Findings go to chat and the plan's `reviews.md`; it is not gate evidence.
- **Gate review:** approves a plan or phase for implementation (design review), or closes a phase (implementation review). Gate reviews follow every rule below.

## Review profile: `small`

The review skills don't read this section themselves. Whoever coordinates a review applies it when choosing which reviewers to run and when to stop.

For a project with one maintainer, the default:

- **Design review, round 1:** all three lenses (fresh reader, codebase fit, zoom out), one at a time.
- **Later design rounds:** only when a Blocker or Major is still open, and only with the lens that raised it. Nits never trigger a round.
- **Implementation review:** the contract lens only.
- **More lenses:** only when the owner asks for them for a given round, recorded in the plan's `reviews.md`.
- **A requirement changed during implementation:** add a line to the plan's decision log and re-check that requirement with one lens. It does not reopen a full design round.

## Gate rules

1. **Fresh reviewers.** Reviewers are subagents that start with a fresh context. Any session may coordinate them, including the one that wrote the work. The coordinator passes only the rule 3 inputs, saves every report verbatim and never edits a verdict or finding.
2. **Pinned revision.** Review a committed revision only.
   - Record `git rev-parse HEAD` in the round's entry in the plan's `reviews.md`.
   - The reviewed paths have no uncommitted changes: `git status --porcelain -- <paths>` is empty.
   - Implementation review diffs `<base>..<commit>`, not the working tree.
3. **Inputs only.** Reviewers receive the plan, the relevant phase file, the ADRs in force and the pinned revision. They never receive the author's reasoning, the session transcript, or another reviewer's verdict.
4. **Saved reports, one record.** Each reviewer's report is copied by tool, never re-typed: on Claude Code with `plan-tool.py save-report` (see the `design-review` skill), otherwise with `cp` from the file the reviewer wrote. Raw reports go to `docs/reviews/<plan-folder>/raw/<review>-<round>-<lens>.md`, for example `raw/design-review-01-fresh-reader.md`. The plan's `reviews.md` is the only round summary: its entry names the commit, the reviewers and the findings.
5. **Verdict.**
   - **FAIL** if any Blocker is open or any reviewer did not complete.
   - Every Major is fixed or contested with evidence before a PASS.
   - Nits do not block.
6. **No fixing by reviewers.** Reviewers never change the work. The coordinator applies fixes, then starts fresh reviewers for the re-check the profile calls for.
7. **One subagent at a time.** See the token budget below.
8. **No private data.** Reviewers, reports and PR descriptions never quote secrets or data the project keeps out of Git. Describe inputs instead.

A review verdict never authorizes a merge. The required `ci-ok` check on the latest head still applies, and only the owner merges.

## Closing a phase

There is no verifier agent. A phase closes with its implementation review, plus a **manual check** when its behavior needs real input to judge. The manual check is recorded in `docs/demos/<YYYY-MM-DD>-<slug>/README.md` ([format](../demos/README.md)): the machine, the versions, who ran it, the commands, and what was observed. The owner may delegate the run to an agent; the record says so. The PR that closes the phase links the record.

## Token budget

| Rule | Why |
| --- | --- |
| Run reviewers one at a time; save and commit each report before starting the next | A usage limit costs only the reviewer in flight, and work resumes from the last commit |
| A follow-up round runs only the lenses the profile names | Follow-up rounds were most of the review cost in earlier projects |
| One line per Nit: location, what, why | Most findings are Nits; long ones inflate every report |
| Save reports by tool (`save-report` or `cp`), never re-type them | A re-typed report costs its length in output and stays in context for every later turn |
| Run the checks once from a clean checkout, with only the documented setup, before the first review round | Catches failures that only your own environment hides |
| Start each phase in a fresh session | The plan files hold all state; a long session's history is paid for on every turn |
| Keep `AGENTS.md` short and load phase files on demand | Always-loaded text is paid for on every turn of every session |

## Session roles and permissions

Separation between roles comes from sessions and subagents, not credentials: every session uses the owner's GitHub login.

| Role | Runs | May | May not |
| --- | --- | --- | --- |
| Implementer | A normal session; `impl-plan apply` | Edit files, run tests, commit, push a feature branch, open and update its PR | Push to `main`, merge, change repository settings, protection or secrets |
| Reviewer | `design-review` / `impl-review`; agents `design-reader`, `design-reviewer`, `impl-reviewer` | Read the inputs and code; run read-only commands; write its own report to the scratch path it is given | Edit repository files, commit, push, write to GitHub, fix what it finds |
| Coordinator | The session that runs a review skill | Choose inputs and reviewers per the profile, save reports, apply fixes between rounds | Edit a reviewer's report or verdict, merge, change protection |
| Owner (a human) | - | Merge PRs, change repository settings, rulesets, secrets and security features; run or delegate the manual check | - |

**What enforces it:**

- **Claude Code sessions and their subagents:** `.claude/settings.json` denies pushes to `main`, force pushes, `gh repo edit/delete/rename/archive`, `gh api` writes, `gh secret`/`gh variable` changes, `gh workflow disable` and `gh auth token`, and asks before `gh pr merge`. Deny rules match the command as written, so they are a guardrail, not a wall.
- **Reviewer agents:** the Skill Central reviewer definitions give them no Edit or Write tools.
- **GitHub:** the owner's ruleset on `main` requires a pull request and a passing `ci-ok`, whatever the session.

When a repository setting needs changing, an agent gives the owner the exact command to run.
