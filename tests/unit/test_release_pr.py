import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.release_pr import (
    MergeEvent,
    Release,
    git,
    publish_release,
    validate_release,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def release_repo(tmp_path: Path) -> tuple[Path, MergeEvent]:
    remote = tmp_path / "origin.git"
    _ = git(tmp_path, "init", "--bare", str(remote))
    root = tmp_path / "checkout"
    _ = git(tmp_path, "clone", str(remote), str(root))
    _ = git(root, "config", "user.email", "test@example.invalid")
    _ = git(root, "config", "user.name", "Release test")
    _ = git(root, "checkout", "-b", "main")
    for version in ("0.20.0", "0.21.0"):
        _ = (root / "pyproject.toml").write_text(
            f'[project]\nversion = "{version}"\n'
            f'[tool.commitizen]\nversion = "{version}"\n'
        )
        _ = (root / "CHANGELOG.md").write_text(
            f"## v{version} (2026-09-24)\n\n- Release changes\n"
        )
        _ = git(root, "add", ".")
        _ = git(root, "commit", "-m", version)
    sha = git(root, "rev-parse", "HEAD")
    base = git(root, "rev-parse", "HEAD^")
    _ = git(root, "push", "origin", "main")
    event: MergeEvent = {
        "action": "closed",
        "repository": {"full_name": "stacking-hq/ksef2"},
        "pull_request": {
            "merged": True,
            "base": {
                "ref": "main",
                "sha": base,
                "repo": {"full_name": "stacking-hq/ksef2"},
            },
            "head": {
                "ref": "release/0.21.0",
                "sha": sha,
                "repo": {"full_name": "stacking-hq/ksef2"},
            },
            "merge_commit_sha": sha,
        },
    }
    return root, event


@pytest.mark.parametrize("reason", ["ordinary", "unmerged", "other-base", "opened"])
def test_non_release_events_do_nothing(
    release_repo: tuple[Path, MergeEvent], reason: str
) -> None:
    root, event = release_repo
    if reason == "ordinary":
        event["pull_request"]["head"]["ref"] = "feat/new-version"
    elif reason == "unmerged":
        event["pull_request"]["merged"] = False
    elif reason == "other-base":
        event["pull_request"]["base"]["ref"] = "develop"
    else:
        event["action"] = "opened"
    assert validate_release(event, root) is None
    assert git(root, "ls-remote", "--tags", "origin") == ""


@pytest.mark.parametrize(
    "branch", ["release/next", "release/v0.21.0", "release/01.0.0", "release/0.21.0rc1"]
)
def test_invalid_release_branch_fails(
    release_repo: tuple[Path, MergeEvent], branch: str
) -> None:
    root, event = release_repo
    event["pull_request"]["head"]["ref"] = branch
    with pytest.raises(ValueError, match="Release branch must be"):
        _ = validate_release(event, root)


def test_fork_cannot_release(release_repo: tuple[Path, MergeEvent]) -> None:
    root, event = release_repo
    event["pull_request"]["head"]["repo"]["full_name"] = "someone/ksef2"
    with pytest.raises(ValueError, match="same repository"):
        _ = validate_release(event, root)


@pytest.mark.parametrize(
    ("filename", "old", "new", "error"),
    [
        (
            "pyproject.toml",
            '[project]\nversion = "0.21.0"',
            '[project]\nversion = "0.22.0"',
            "branch and project",
        ),
        (
            "pyproject.toml",
            '[tool.commitizen]\nversion = "0.21.0"',
            '[tool.commitizen]\nversion = "0.20.0"',
            "Commitizen",
        ),
        ("CHANGELOG.md", "## v0.21.0", "## v0.20.0", "CHANGELOG"),
    ],
)
def test_inconsistent_release_fails(
    release_repo: tuple[Path, MergeEvent], filename: str, old: str, new: str, error: str
) -> None:
    root, event = release_repo
    path = root / filename
    _ = path.write_text(path.read_text().replace(old, new))
    _ = git(root, "commit", "-am", "Invalid release")
    _ = git(root, "push", "origin", "main")
    event["pull_request"]["merge_commit_sha"] = git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match=error):
        _ = validate_release(event, root)


@pytest.mark.parametrize("version", ["0.20.0", "0.19.0"])
def test_release_must_increase_version(
    release_repo: tuple[Path, MergeEvent], version: str
) -> None:
    root, event = release_repo
    for filename in ("pyproject.toml", "CHANGELOG.md"):
        path = root / filename
        _ = path.write_text(path.read_text().replace("0.21.0", version))
    _ = git(root, "commit", "-am", "No version increase")
    _ = git(root, "push", "origin", "main")
    event["pull_request"]["head"]["ref"] = f"release/{version}"
    event["pull_request"]["merge_commit_sha"] = git(root, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="must increase"):
        _ = validate_release(event, root)


def test_wrong_checkout_fails(release_repo: tuple[Path, MergeEvent]) -> None:
    root, event = release_repo
    _ = git(root, "commit", "--allow-empty", "-m", "Later main change")
    _ = git(root, "push", "origin", "main")
    with pytest.raises(ValueError, match="exact merged PR commit"):
        _ = validate_release(event, root)


def test_commit_outside_main_fails(release_repo: tuple[Path, MergeEvent]) -> None:
    root, event = release_repo
    _ = git(
        root,
        "update-ref",
        "refs/remotes/origin/main",
        event["pull_request"]["base"]["sha"],
    )
    with pytest.raises(subprocess.CalledProcessError, match="merge-base"):
        _ = validate_release(event, root)


@pytest.mark.parametrize("target", ["HEAD", "HEAD^"])
def test_existing_tag_fails_even_at_same_commit(
    release_repo: tuple[Path, MergeEvent], target: str
) -> None:
    root, event = release_repo
    _ = git(root, "push", "origin", f"{target}:refs/tags/v0.21.0")
    with pytest.raises(ValueError, match="already exists"):
        _ = validate_release(event, root)


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    executable = tmp_path / "bin/gh"
    executable.parent.mkdir()
    _ = executable.write_text(
        f"#!{sys.executable}\n"
        + """
import json
import os
from pathlib import Path
import subprocess
import sys

with Path(os.environ["GH_CALLS"]).open("a") as log:
    _ = log.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1] == "api":
    data = json.load(sys.stdin)
    if os.environ.get("FAIL_CREATE"):
        raise SystemExit(1)
    # A local bare remote stands in for GitHub's atomic create-ref endpoint.
    _ = subprocess.run([
        "git", "--git-dir", "../origin.git", "update-ref",
        data["ref"], data["sha"], "0" * 40,
    ], check=True)
elif os.environ.get("FAIL_DISPATCH"):
    raise SystemExit(1)
"""
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{executable.parent}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    calls = tmp_path / "gh-calls.jsonl"
    monkeypatch.setenv("GH_CALLS", str(calls))
    return calls


def test_cli_tags_exact_merge_after_main_advances_and_dispatches(
    release_repo: tuple[Path, MergeEvent], fake_gh: Path
) -> None:
    root, event = release_repo
    sha = event["pull_request"]["merge_commit_sha"]
    _ = git(root, "commit", "--allow-empty", "-m", "Later main change")
    _ = git(root, "push", "origin", "main")
    _ = git(root, "checkout", "--detach", sha)
    assert validate_release(event, root) == Release("stacking-hq/ksef2", "v0.21.0", sha)
    event_path = root.parent / "event.json"
    _ = event_path.write_text(json.dumps(event))
    _ = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.release_pr",
            "--event",
            str(event_path),
            "--execute",
        ],
        cwd=root,
        check=True,
    )
    assert git(root, "ls-remote", "--tags", "origin") == f"{sha}\trefs/tags/v0.21.0"
    calls = [json.loads(line) for line in fake_gh.read_text().splitlines()]
    assert calls[0][:5] == [
        "api",
        "--method",
        "POST",
        "repos/stacking-hq/ksef2/git/refs",
        "--input",
    ]
    assert calls[1] == [
        "workflow",
        "run",
        "publish.yml",
        "--repo",
        "stacking-hq/ksef2",
        "--ref",
        "v0.21.0",
        "--field",
        f"release_sha={sha}",
    ]
    retry = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.release_pr",
            "--event",
            str(event_path),
            "--execute",
        ],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert retry.returncode == 1
    assert "already exists" in retry.stderr
    assert len(fake_gh.read_text().splitlines()) == 2


@pytest.mark.parametrize(
    "mode", ["dry-run", "create-failure", "dispatch-failure", "invalid"]
)
def test_cli_failure_boundaries(
    release_repo: tuple[Path, MergeEvent],
    fake_gh: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    root, event = release_repo
    if mode == "create-failure":
        monkeypatch.setenv("FAIL_CREATE", "1")
    if mode == "dispatch-failure":
        monkeypatch.setenv("FAIL_DISPATCH", "1")
    if mode == "invalid":
        event["pull_request"]["head"]["ref"] = "release/0.22.0"
    event_path = root.parent / "event.json"
    _ = event_path.write_text(json.dumps(event))
    command = [sys.executable, "-m", "scripts.release_pr", "--event", str(event_path)]
    if mode != "dry-run":
        command.append("--execute")
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    assert result.returncode == (0 if mode == "dry-run" else 1)
    if mode in ("dry-run", "invalid"):
        assert not fake_gh.exists()
    else:
        assert len(fake_gh.read_text().splitlines()) == (
            1 if mode == "create-failure" else 2
        )
    tags = git(root, "ls-remote", "--tags", "origin")
    if mode == "dispatch-failure":
        assert tags == f"{event['pull_request']['merge_commit_sha']}\trefs/tags/v0.21.0"
    else:
        assert tags == ""


@pytest.mark.parametrize(
    "case", ["valid", "push", "branch", "wrong-sha", "moved-tag", "outside-main"]
)
def test_publish_ref_guard_executes_before_integration(
    release_repo: tuple[Path, MergeEvent], case: str
) -> None:
    root, event = release_repo
    sha = event["pull_request"]["merge_commit_sha"]
    _ = git(root, "tag", "v0.21.0")
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())
    guard = workflow["jobs"]["release-ref"]["steps"][-1]["run"]
    env = dict(
        os.environ,
        GITHUB_REF_TYPE="tag",
        GITHUB_REF_NAME="v0.21.0",
        GITHUB_REF="refs/tags/v0.21.0",
        GITHUB_SHA=sha,
        GITHUB_EVENT_NAME="workflow_dispatch",
        EXPECTED_SHA=sha,
    )
    if case == "push":
        env["GITHUB_EVENT_NAME"] = "push"
        env["EXPECTED_SHA"] = ""
    elif case == "branch":
        env["GITHUB_REF_TYPE"] = "branch"
    elif case == "wrong-sha":
        env["EXPECTED_SHA"] = "0" * 40
    elif case == "moved-tag":
        _ = git(root, "tag", "-f", "v0.21.0", "HEAD^")
    elif case == "outside-main":
        _ = git(root, "update-ref", "refs/remotes/origin/main", "HEAD^")
    result = subprocess.run(
        ["bash", "-c", guard], cwd=root, env=env, capture_output=True
    )
    assert (result.returncode == 0) == (case in ("valid", "push"))


def test_workflows_keep_publication_gated() -> None:
    publish = yaml.safe_load((ROOT / ".github/workflows/publish.yml").read_text())
    release = yaml.safe_load((ROOT / ".github/workflows/release-pr.yml").read_text())
    # PyYAML's YAML 1.1 parser reads the Actions key `on` as True.
    assert publish[True]["workflow_dispatch"]["inputs"]["release_sha"]["required"]
    assert publish[True]["push"]["tags"] == ["v*"]
    assert release[True]["pull_request"] == {"types": ["closed"], "branches": ["main"]}
    release_job = release["jobs"]["release"]
    assert "head.repo.full_name == github.repository" in release_job["if"]
    assert (
        "startsWith(github.event.pull_request.head.ref, 'release/')"
        in release_job["if"]
    )
    assert release_job["permissions"] == {"contents": "write", "actions": "write"}
    assert (
        release_job["steps"][0]["with"]["ref"]
        == "${{ github.event.pull_request.merge_commit_sha }}"
    )
    assert '--event "$GITHUB_EVENT_PATH" --execute' in release_job["steps"][-1]["run"]
    jobs = publish["jobs"]
    assert jobs["integration"]["needs"] == "release-ref"
    assert jobs["publish"]["needs"] == "integration"
    assert jobs["publish"]["environment"] == "pypi"
    assert jobs["publish"]["permissions"]["id-token"] == "write"
    assert jobs["notify-docs"]["needs"] == "publish"
    assert not publish["concurrency"]["cancel-in-progress"]
    for job in ("integration", "publish"):
        assert jobs[job]["steps"][0]["with"]["ref"] == "${{ github.sha }}"
    integration_commands = [
        step.get("run", "") for step in jobs["integration"]["steps"]
    ]
    assert "uv run pytest tests/integration/ -v -m integration" in integration_commands
    publish_commands = [step.get("run", "") for step in jobs["publish"]["steps"]]
    assert "just release-check" in publish_commands
    assert (
        'uv run python scripts/verify_release.py --tag "$GITHUB_REF_NAME"'
        in publish_commands
    )
    assert any(".release-venv/bin/python" in command for command in publish_commands)
    assert (
        jobs["publish"]["steps"][-1]["uses"] == "pypa/gh-action-pypi-publish@release/v1"
    )


@pytest.mark.parametrize("merge_style", ["merge", "squash", "rebase"])
def test_release_targets_github_merge_sha_for_each_merge_style(
    release_repo: tuple[Path, MergeEvent], merge_style: str
) -> None:
    root, event = release_repo
    pr = event["pull_request"]
    base = pr["base"]["sha"]
    # Keep the original PR head distinct from the resulting main commit.
    _ = git(root, "branch", "release/0.21.0")
    _ = git(root, "reset", "--hard", base)
    _ = git(root, "commit", "--allow-empty", "-m", "Concurrent main change")
    pr["base"]["sha"] = git(root, "rev-parse", "HEAD")
    if merge_style == "merge":
        _ = git(root, "merge", "--no-ff", "release/0.21.0", "-m", "Merge release PR")
    elif merge_style == "squash":
        _ = git(root, "merge", "--squash", "release/0.21.0")
        _ = git(root, "commit", "-m", "Squash release PR")
    else:
        _ = git(root, "cherry-pick", pr["head"]["sha"])
        _ = git(root, "commit", "--allow-empty", "-m", "Final rebased PR commit")
    pr["merge_commit_sha"] = git(root, "rev-parse", "HEAD")
    _ = git(root, "push", "--force", "origin", "main")
    release = validate_release(event, root)
    assert release is not None
    assert release.sha == pr["merge_commit_sha"]
    assert release.sha != pr["head"]["sha"]


def test_tag_creation_race_never_dispatches(
    release_repo: tuple[Path, MergeEvent], fake_gh: Path
) -> None:
    root, event = release_repo
    release = validate_release(event, root)
    assert release is not None
    _ = git(root, "push", "origin", "HEAD:refs/tags/v0.21.0")
    with pytest.raises(subprocess.CalledProcessError):
        publish_release(release, root)
    assert len(fake_gh.read_text().splitlines()) == 1
    assert (
        git(root, "ls-remote", "--tags", "origin")
        == f"{release.sha}\trefs/tags/v0.21.0"
    )
