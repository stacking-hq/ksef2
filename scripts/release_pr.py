"""Validate a merged release PR; opt in to tag creation and publish dispatch."""

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from scripts.verify_release import read_source_version


class Repository(TypedDict):
    full_name: str


class Branch(TypedDict):
    ref: str
    sha: str
    repo: Repository


class PullRequest(TypedDict):
    merged: bool
    base: Branch
    head: Branch
    merge_commit_sha: str


class MergeEvent(TypedDict):
    action: str
    repository: Repository
    pull_request: PullRequest


@dataclass(frozen=True)
class Release:
    repository: str
    tag: str
    sha: str


VERSION_PATTERN = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def validate_release(event: MergeEvent, root: Path) -> Release | None:
    """Inspect the event and Git history without creating tags or dispatching CI."""
    pr = event["pull_request"]
    if (
        event["action"] != "closed"
        or not pr["merged"]
        or pr["base"]["ref"] != "main"
        or not pr["head"]["ref"].startswith("release/")
    ):
        return None

    repository = event["repository"]["full_name"]
    if (
        pr["base"]["repo"]["full_name"] != repository
        or pr["head"]["repo"]["full_name"] != repository
    ):
        raise ValueError("Release PR must come from the same repository")

    version = pr["head"]["ref"].removeprefix("release/")
    if re.fullmatch(VERSION_PATTERN, version) is None:
        raise ValueError("Release branch must be release/X.Y.Z with a stable version")
    sha = pr["merge_commit_sha"]
    base_sha = pr["base"]["sha"]
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (sha, base_sha)):
        raise ValueError("Merge and base commits must be full Git SHAs")
    if git(root, "rev-parse", "HEAD") != sha:
        raise ValueError("Checkout must be the exact merged PR commit")
    _ = git(root, "merge-base", "--is-ancestor", sha, "refs/remotes/origin/main")
    _ = git(root, "merge-base", "--is-ancestor", base_sha, sha)

    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    if pyproject["project"]["version"] != version:
        raise ValueError("Release branch and project version disagree")
    if pyproject["tool"]["commitizen"]["version"] != version:
        raise ValueError("Commitizen and project versions disagree")
    if read_source_version(root / "src/ksef2/__version__.py") != version:
        raise ValueError("Source and project versions disagree")

    previous = tomllib.loads(git(root, "show", f"{base_sha}:pyproject.toml"))
    previous_version = cast(str, previous["project"]["version"])
    if re.fullmatch(VERSION_PATTERN, previous_version) is None:
        raise ValueError("Previous project version must be a stable X.Y.Z version")
    if tuple(map(int, version.split("."))) <= tuple(
        map(int, previous_version.split("."))
    ):
        raise ValueError("Release version must increase from the PR base version")

    changelog = (root / "CHANGELOG.md").read_text()
    if not changelog.startswith(f"## v{version} "):
        raise ValueError("CHANGELOG.md must start with the release version heading")
    tag = f"v{version}"
    if git(root, "ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        raise ValueError(
            f"Tag {tag} already exists; never move or recreate release tags"
        )
    return Release(repository=repository, tag=tag, sha=sha)


def publish_release(release: Release, root: Path) -> None:
    """Create the ref atomically, then dispatch the existing publish workflow."""
    # The create-ref API rejects existing refs, even if they target the same SHA.
    _ = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{release.repository}/git/refs",
            "--input",
            "-",
        ],
        input=json.dumps({"ref": f"refs/tags/{release.tag}", "sha": release.sha}),
        cwd=root,
        text=True,
        check=True,
    )
    # workflow_dispatch is exempt from GITHUB_TOKEN event suppression.
    _ = subprocess.run(
        [
            "gh",
            "workflow",
            "run",
            "publish.yml",
            "--repo",
            release.repository,
            "--ref",
            release.tag,
            "--field",
            f"release_sha={release.sha}",
        ],
        cwd=root,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--event", type=Path, required=True)
    _ = parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    event_path = cast(Path, args.event)
    root = Path.cwd()
    try:
        event = cast(MergeEvent, json.loads(event_path.read_text()))
        release = validate_release(event, root)
        if release is None:
            print("Not a merged release PR to main; nothing to publish")
            return 0
        print(f"Validated {release.tag} at merged commit {release.sha}", flush=True)
        if cast(bool, args.execute):
            publish_release(release, root)
        else:
            print("Dry run: no tag created and no publish workflow dispatched")
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"Release PR failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            stderr = cast(str | None, error.stderr)
            if stderr:
                print(stderr, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
