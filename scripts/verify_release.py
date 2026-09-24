"""Verify that a release tag and built distributions describe one SDK version."""

import argparse
import sys
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import cast


ROOT = Path(__file__).resolve().parent.parent


def verify_release(*, tag: str, root: Path, dist_directory: Path) -> list[str]:
    """Return release metadata mismatches without publishing any artifact."""
    errors: list[str] = []

    with (root / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = cast(dict[str, object], tomllib.load(pyproject_file))
    project = cast(dict[str, object], pyproject["project"])
    project_version = cast(str, project["version"])

    expected_tag = f"v{project_version}"

    if tag != expected_tag:
        errors.append(f"tag {tag!r} does not match project version {expected_tag!r}")
    changelog_heading = f"## v{project_version} "
    changelog = (root / "CHANGELOG.md").read_text()
    if not changelog.startswith(changelog_heading):
        errors.append(
            f"CHANGELOG.md must start with a {changelog_heading.strip()!r} heading"
        )

    wheels = sorted(dist_directory.glob(f"ksef2-{project_version}-*.whl"))
    if len(wheels) != 1:
        errors.append(
            f"expected exactly one ksef2 {project_version} wheel, found {len(wheels)}"
        )
    else:
        with zipfile.ZipFile(wheels[0]) as wheel:
            metadata_files = [
                name
                for name in wheel.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_files) != 1:
                errors.append(
                    f"expected one METADATA file in {wheels[0].name}, "
                    f"found {len(metadata_files)}"
                )
            else:
                metadata = Parser().parsestr(
                    wheel.read(metadata_files[0]).decode("utf-8")
                )
                wheel_version = metadata.get("Version")
                if wheel_version != project_version:
                    errors.append(
                        f"wheel metadata declares {wheel_version!r}, "
                        f"expected {project_version!r}"
                    )

    source_distributions = sorted(
        dist_directory.glob(f"ksef2-{project_version}.tar.gz")
    )
    if len(source_distributions) != 1:
        errors.append(
            f"expected exactly one ksef2 {project_version} source distribution, "
            f"found {len(source_distributions)}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--tag", required=True, help="Git tag, for example v1.0.0")
    _ = parser.add_argument(
        "--dist-directory",
        type=Path,
        default=ROOT / "dist",
        help="Directory containing the wheel and source distribution",
    )
    args = parser.parse_args()
    tag = cast(str, args.tag)
    dist_directory = cast(Path, args.dist_directory)

    errors = verify_release(
        tag=tag,
        root=ROOT,
        dist_directory=dist_directory,
    )
    if errors:
        for error in errors:
            print(f"release verification failed: {error}", file=sys.stderr)
        return 1

    print(f"release artifact verified for {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
