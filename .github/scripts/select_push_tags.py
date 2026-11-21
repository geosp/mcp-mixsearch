"""Choose which image tags the Docker publish workflow pushes.

Run by the "Push the tested image" step of .github/workflows/docker-publish.yml with TAGS (the
metadata-action tags, one per line), SHA (`github.sha`) and REPO_URL. Prints the tags to push,
one per line.

`main` and `latest` are moving tags: they are pushed only when SHA is still the tip of `main`, so
re-running an old run can't move them back to older code. Every other tag (`sha-…`, version tags)
is always pushed. The tip is read only when a moving tag is present, and a tip that can't be read
fails the step instead of quietly skipping the moving tags.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable

MOVING_TAGS = ("main", "latest")


class TipError(RuntimeError):
    """The tip of main could not be read."""


def parse_tags(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def is_moving(tag: str) -> bool:
    return tag.rsplit(":", 1)[-1] in MOVING_TAGS


def select(tags: list[str], sha: str, read_tip: Callable[[], str]) -> list[str]:
    if not any(is_moving(tag) for tag in tags):
        return tags
    tip = read_tip()
    if not tip:
        raise TipError("could not read the tip of main")
    if tip == sha:
        return tags
    for tag in tags:
        if is_moving(tag):
            print(f"skip {tag}: {sha} is no longer the tip of main ({tip})", file=sys.stderr)
    return [tag for tag in tags if not is_moving(tag)]


def read_tip(repo_url: str) -> str:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", repo_url, "refs/heads/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise TipError(f"git ls-remote failed: {result.stderr.strip()}")
    return result.stdout.split("\t", 1)[0].strip()


def main() -> int:
    tags = parse_tags(os.environ["TAGS"])
    try:
        selected = select(tags, os.environ["SHA"], lambda: read_tip(os.environ["REPO_URL"]))
    except TipError as error:
        print(error, file=sys.stderr)
        return 1
    print("\n".join(selected))
    return 0


if __name__ == "__main__":
    sys.exit(main())
