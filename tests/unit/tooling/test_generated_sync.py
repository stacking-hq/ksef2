from pathlib import Path

import pytest

from scripts import gen_sync
from scripts.gen_sync import (
    GENERATED_PAIRS,
    REPO_ROOT,
    GeneratedPair,
    generate_formatted_source,
    generate_source,
)


def test_generated_sync_files_match_async_sources() -> None:
    stale_files: list[str] = []

    for pair in GENERATED_PAIRS:
        expected = generate_formatted_source(pair)
        actual = (REPO_ROOT / pair.target).read_text()
        if actual != expected:
            stale_files.append(pair.target.as_posix())

    assert not stale_files, "Generated sync files are stale: " + ", ".join(stale_files)


def test_unsupported_asyncio_references_fail_generation(tmp_path: Path) -> None:
    source_path = tmp_path / "async_example.py"
    source_path.write_text(
        "import asyncio\n\n"
        "async def run_all() -> object:\n"
        "    return await asyncio.gather()\n"
    )

    pair = GeneratedPair(Path("async_example.py"), Path("example.py"))

    with pytest.raises(ValueError, match=r"asyncio\.gather"):
        _ = generate_source(pair, repo_root=tmp_path)


def test_ruff_uses_repo_config_for_generated_formatting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[list[str]] = []

    def capture_run(command: list[str], cwd: Path) -> None:
        commands.append(command)

    monkeypatch.setattr(gen_sync, "_run", capture_run)

    gen_sync._run_ruff_fix([tmp_path / "example.py"], cwd=tmp_path)

    config = str(tmp_path / "pyproject.toml")
    assert len(commands) == 2
    assert all("--config" in command for command in commands)
    assert all(config in command for command in commands)
