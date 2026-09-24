import zipfile
from pathlib import Path

from scripts.verify_release import verify_release


def write_release_fixture(root: Path, *, version: str, wheel_version: str) -> Path:
    (root / "dist").mkdir()
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "ksef2"\nversion = "{version}"\n'
    )
    (root / "CHANGELOG.md").write_text(f"## v{version} (2026-07-10)\n")
    (root / f"dist/ksef2-{version}.tar.gz").write_bytes(b"source distribution")

    wheel = root / f"dist/ksef2-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"ksef2-{wheel_version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: ksef2\nVersion: {wheel_version}\n",
        )
    return root / "dist"


def test_verify_release_accepts_matching_tag_and_artifacts(
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
