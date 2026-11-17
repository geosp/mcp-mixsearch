"""Tests for `.github/scripts/ci_gate.py`, the logic behind the required `ci-ok` check."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import ci_gate
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".github" / "scripts" / "ci_gate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "ci-gate.yml"
MAIN = ci_gate.MAIN_REF
BRANCH = "refs/heads/feat/1-x"
PR_REF = "refs/pull/1/merge"
PR_ONLY = sorted(ci_gate.PR_ONLY_JOBS)
EVERY_RUN = [job for job in ci_gate.REQUIRED_JOBS if job not in ci_gate.PR_ONLY_JOBS]
FIRST_JOB = ci_gate.REQUIRED_JOBS[0]
LAST_JOB = ci_gate.REQUIRED_JOBS[-1]


def needs(**overrides: str) -> dict[str, dict[str, str]]:
    results = {job: "success" for job in ci_gate.REQUIRED_JOBS}
    results.update(overrides)
    return {job: {"result": r} for job, r in results.items()}


def test_all_success_passes() -> None:
    assert ci_gate.problems(needs(), "pull_request", PR_REF) == []


@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped"])
@pytest.mark.parametrize("job", ci_gate.REQUIRED_JOBS)
def test_any_non_success_fails_a_pull_request(job: str, result: str) -> None:
    assert ci_gate.problems(needs(**{job: result}), "pull_request", PR_REF) == [f"{job}: {result}"]


@pytest.mark.parametrize("job", EVERY_RUN)
def test_skipped_job_fails_on_main_too(job: str) -> None:
    assert ci_gate.problems(needs(**{job: "skipped"}), "push", MAIN) == [f"{job}: skipped"]


@pytest.mark.parametrize("event", ["push", "workflow_dispatch"])
@pytest.mark.parametrize("job", PR_ONLY)
def test_pr_only_job_may_be_skipped_on_main(job: str, event: str) -> None:
    assert ci_gate.problems(needs(**{job: "skipped"}), event, MAIN) == []


@pytest.mark.parametrize(
    ("event", "ref"),
    [("workflow_dispatch", BRANCH), ("push", BRANCH), ("pull_request", MAIN)],
)
@pytest.mark.parametrize("job", PR_ONLY)
def test_pr_only_job_skipped_elsewhere_fails(job: str, event: str, ref: str) -> None:
    # A manual run on a pull request's branch must not give its head a green ci-ok
    # without the pull-request-only checks.
    assert ci_gate.problems(needs(**{job: "skipped"}), event, ref) == [f"{job}: skipped"]


def test_missing_and_unknown_jobs_fail() -> None:
    n = needs()
    del n[LAST_JOB]
    n["extra"] = {"result": "success"}
    assert ci_gate.problems(n, "pull_request", PR_REF) == [
        f"{LAST_JOB}: missing",
        "extra: not in REQUIRED_JOBS",
    ]


def test_required_jobs_match_the_workflow() -> None:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    gate = jobs["ci-ok"]
    assert gate["if"] == "always()"
    assert tuple(gate["needs"]) == ci_gate.REQUIRED_JOBS
    assert set(jobs) - {"ci-ok"} == set(ci_gate.REQUIRED_JOBS)
    assert any(".github/scripts/ci_gate.py" in step.get("run", "") for step in gate["steps"])


@pytest.mark.parametrize(
    ("result", "code"),
    [("success", 0), ("skipped", 1)],
)
def test_script_exit_code(result: str, code: int) -> None:
    env = {
        **os.environ,
        "NEEDS": json.dumps(needs(**{FIRST_JOB: result})),
        "EVENT": "pull_request",
        "REF": PR_REF,
    }
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, check=False
    )
    assert proc.returncode == code, proc.stderr
