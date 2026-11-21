"""Tests for the Docker publish workflow: which tags are pushed (R7) and when (R6)."""

from __future__ import annotations

from pathlib import Path

import pytest
import select_push_tags
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "docker-publish.yml"
IMAGE = "ghcr.io/geosp/mcp-mixsearch"
MAIN_TAGS = [f"{IMAGE}:main", f"{IMAGE}:sha-aaaaaaa", f"{IMAGE}:latest"]
VERSION_TAGS = [f"{IMAGE}:v1.2.0", f"{IMAGE}:1.2.0", f"{IMAGE}:1.2", f"{IMAGE}:1", f"{IMAGE}:sha-a"]


def test_tip_run_pushes_every_tag():
    assert select_push_tags.select(MAIN_TAGS, "A", lambda: "A") == MAIN_TAGS


def test_old_run_pushes_only_its_sha_tag():
    assert select_push_tags.select(MAIN_TAGS, "A", lambda: "B") == [f"{IMAGE}:sha-aaaaaaa"]


def test_version_run_needs_no_tip_and_pushes_every_tag():
    def no_tip() -> str:
        raise AssertionError("the tip must not be read when no moving tag is present")

    assert select_push_tags.select(VERSION_TAGS, "A", no_tip) == VERSION_TAGS


def test_unreadable_tip_fails_instead_of_skipping():
    with pytest.raises(select_push_tags.TipError):
        select_push_tags.select(MAIN_TAGS, "A", lambda: "")


def test_blank_lines_are_ignored():
    assert select_push_tags.parse_tags(f"\n{IMAGE}:main\n\n{IMAGE}:sha-a\n") == [
        f"{IMAGE}:main",
        f"{IMAGE}:sha-a",
    ]


def steps() -> list[dict]:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    return workflow["jobs"]["build-and-push"]["steps"]


def step(name: str) -> tuple[int, dict]:
    for index, s in enumerate(steps()):
        if s.get("name") == name:
            return index, s
    raise AssertionError(f"no step named {name!r}")


def test_image_is_built_once_and_not_pushed_by_the_build():
    _, build = step("Build Docker image")
    assert build["with"]["load"] is True
    assert build["with"]["push"] is False
    pushing = [s for s in steps() if s.get("with", {}).get("push") not in (None, False)]
    assert pushing == []


def test_push_runs_only_after_a_passing_smoke_test_and_never_on_prs():
    smoke_index, smoke = step("Smoke test")
    login_index, login = step("Log in to GitHub Container Registry")
    push_index, push = step("Push the tested image")
    build_index, _ = step("Build Docker image")
    assert build_index < smoke_index < login_index < push_index
    for s in (smoke, login, push):
        assert "continue-on-error" not in s
        assert "always()" not in str(s.get("if", ""))
    assert "if" not in smoke
    assert login["if"] == push["if"] == "github.event_name != 'pull_request'"
    assert "select_push_tags.py" in push["run"]
    assert "docker_smoke.sh" in smoke["run"]


def test_latest_follows_the_default_branch_only():
    _, meta = step("Extract metadata (tags, labels)")
    assert meta["with"]["flavor"].strip() == "latest=false"
    tag_lines = [line.strip() for line in meta["with"]["tags"].splitlines()]
    assert "type=raw,value=latest,enable={{is_default_branch}}" in tag_lines
    assert "latest" not in tag_lines


@pytest.mark.parametrize(
    "path", ["docker/prod/docker-compose.yml", "docker/mcp/docker-compose.yml"]
)
def test_compose_files_run_the_image_as_built(path):
    service = yaml.safe_load((ROOT / path).read_text())["services"]["mcp-mixsearch"]
    assert "command" not in service
    assert "volumes" not in service
    assert "working_dir" not in service
