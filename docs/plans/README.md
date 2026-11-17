# Implementation plans

Plans are created and driven by Skill Central's `impl-plan` skill, and reviewed with `design-review` before implementation and `impl-review` after each phase.

```text
docs/plans/YYYY-MM-DD-<slug>/
  plan.md               Summary, requirements, decisions, phases, decision log
  notes.md              optional evidence that plan.md links to
  phases/NN-<slug>.md   one per phase: goal and tasks
  reviews.md            append-only log of review rounds, approvals and waivers
```

Read a plan's `plan.md`, then only the current phase file. Raw reviewer reports are saved under [../reviews/](../reviews/README.md); the plan's `reviews.md` is the only round summary.
