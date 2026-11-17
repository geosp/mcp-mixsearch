## Summary

> [!TIP]
> 2-5 sentences: what changed and why. Write for a reviewer who has not seen the work.

## Issue

> [!TIP]
> `Closes #N` only if this PR fully resolves the issue; otherwise `Part of #N`. Never use closing keywords (closes/fixes/resolves) for any other issue.

Closes #

## Plan trace

- **Implementation plan and phase:** <!-- docs/plans/<plan>/ and phase NN, or n/a -->
- **ADR:** <!-- docs/adrs/..., or n/a -->

## Changes

-

## Testing

> [!TIP]
> List only the checks actually run (the commands in AGENTS.md, Checks), with their result.

| Check | Command | Result |
| --- | --- | --- |
| | | |

## Manual check

> [!TIP]
> Required when this PR closes a phase that needs a manual check: link its record in `docs/demos/`. Delete this section otherwise.

## Notes for reviewers

> [!TIP]
> New dependencies or lockfile changes, interface or output changes others rely on, known limitations. Delete if none.

## Checklist

- [ ] No secrets, credentials or session transcripts committed
- [ ] No data this project keeps out of Git in the diff, fixtures or this description
- [ ] Decision log or plan updated if constraints or interfaces changed
- [ ] Plan task boxes checked only for work whose tests pass
- [ ] Generated agent files in sync (`uv run .agents/sync_agents.py --check`)
