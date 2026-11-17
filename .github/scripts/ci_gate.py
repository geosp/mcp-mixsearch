"""Decide the result of the required `ci-ok` check from the `needs` context.

Run by the `ci-ok` job in .github/workflows/ci-gate.yml with NEEDS (the JSON of the
`needs` context), EVENT (`github.event_name`) and REF (`github.ref`).

Every job in REQUIRED_JOBS must have succeeded. A skipped job is a failure, with
one exception: a job in PR_ONLY_JOBS (such as `licenses`, dependency review) runs
only on pull requests, so it may be skipped for runs on the default branch itself,
whose commits all arrived through a pull request that already ran it.

tests/test_ci_gate.py checks that REQUIRED_JOBS matches the `needs` list of
`ci-ok`, so removing a job from the gate takes an edit here as well.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

REQUIRED_JOBS = (
    "lint",
    "types",
    "tests",
    "agents-sync",
    "workflows",
    "secrets",
    "links",
    "licenses",
)
PR_ONLY_JOBS: frozenset[str] = frozenset({"licenses"})
MAIN_REF = "refs/heads/main"


def result_of(needs: dict[str, Any], job: str) -> str:
    entry = needs.get(job)
    if isinstance(entry, dict) and isinstance(entry.get("result"), str):
        return str(entry["result"])
    return "missing"


def may_skip(job: str, event: str, ref: str) -> bool:
    return job in PR_ONLY_JOBS and ref == MAIN_REF and event in ("push", "workflow_dispatch")


def problems(needs: dict[str, Any], event: str, ref: str) -> list[str]:
    found = []
    for job in REQUIRED_JOBS:
        result = result_of(needs, job)
        if result == "success" or (result == "skipped" and may_skip(job, event, ref)):
            continue
        found.append(f"{job}: {result}")
    found += [f"{job}: not in REQUIRED_JOBS" for job in sorted(set(needs) - set(REQUIRED_JOBS))]
    return found


def main() -> int:
    needs = json.loads(os.environ["NEEDS"])
    event = os.environ.get("EVENT", "")
    ref = os.environ.get("REF", "")
    for job in REQUIRED_JOBS:
        print(f"{job}: {result_of(needs, job)}")
    bad = problems(needs, event, ref)
    if bad:
        print(f"ci-ok fails ({event} on {ref}):", *bad, sep="\n  ", file=sys.stderr)
        return 1
    print("ci-ok: all required jobs passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
