import zipfile
from pathlib import Path

from scripts.verify_release import verify_release


def write_release_fixture(root: Path, *, version: str, wheel_version: str) -> Path:
    (root / "src/ksef2").mkdir(parents=True)
    (root / "dist").mkdir()
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "ksef2"\nversion = "{version}"\n'
    )
    (root / "src/ksef2/__version__.py").write_text(f'version = "{version}"\n')
    (root / "CHANGELOG.md").write_text(f"## v{version} (2026-07-10)\n")
    (root / f"dist/ksef2-{version}.tar.gz").write_bytes(b"source distribution")

    wheel = root / f"dist/ksef2-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"ksef2-{wheel_version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: ksef2\nVersion: {wheel_version}\n",
        )
    return root / "dist"


def test_verify_release_accepts_matching_tag_source_and_artifacts(
    tmp_path: Path,
) -> None:
    dist_directory = write_release_fixture(
        tmp_path, version="1.0.0", wheel_version="1.0.0"
    )

    assert (
        verify_release(tag="v1.0.0", root=tmp_path, dist_directory=dist_directory) == []
    )


def test_verify_release_reports_tag_and_wheel_mismatches(tmp_path: Path) -> None:
    dist_directory = write_release_fixture(
        tmp_path, version="1.0.0", wheel_version="0.19.0"
    )

    errors = verify_release(tag="v0.19.0", root=tmp_path, dist_directory=dist_directory)

    assert "tag 'v0.19.0' does not match project version 'v1.0.0'" in errors
    assert "wheel metadata declares '0.19.0', expected '1.0.0'" in errors


def test_verify_release_rejects_unreleased_heading_and_source_mismatch(
    tmp_path: Path,
) -> None:
    dist_directory = write_release_fixture(
        tmp_path, version="1.0.0", wheel_version="1.0.0"
    )
    (tmp_path / "src/ksef2/__version__.py").write_text('version = "0.19.0"\n')
    (tmp_path / "CHANGELOG.md").write_text("## v1.0.0 (unreleased)\n")

    errors = verify_release(tag="v1.0.0", root=tmp_path, dist_directory=dist_directory)

    assert "src/ksef2/__version__.py declares '0.19.0', expected '1.0.0'" in errors
    assert any("using the actual release date" in error for error in errors)


def test_verify_release_requires_exactly_one_wheel_and_source_distribution(
    tmp_path: Path,
) -> None:
    dist_directory = write_release_fixture(
        tmp_path, version="1.0.0", wheel_version="1.0.0"
    )
    (dist_directory / "ksef2-1.0.0.tar.gz").unlink()
    (dist_directory / "ksef2-1.0.0-extra.whl").write_bytes(b"extra wheel")

    errors = verify_release(tag="v1.0.0", root=tmp_path, dist_directory=dist_directory)

    assert "expected exactly one ksef2 1.0.0 wheel, found 2" in errors
    assert "expected exactly one ksef2 1.0.0 source distribution, found 0" in errors
