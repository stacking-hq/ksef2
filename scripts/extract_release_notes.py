"""Extract one version section from CHANGELOG.md for a GitHub Release."""

import argparse
from pathlib import Path
from typing import cast


ROOT = Path(__file__).resolve().parent.parent


def extract_release_notes(changelog: str, *, tag: str) -> str:
    """Return the complete changelog section for ``tag``."""
    heading_prefix = f"## {tag} "
    lines = changelog.splitlines()

    start = next(
        (index for index, line in enumerate(lines) if line.startswith(heading_prefix)),
        None,
    )
    if start is None:
        raise ValueError(f"CHANGELOG.md has no section for {tag}")

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end]).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--tag", required=True, help="Release tag, for example v1.0.0"
    )
    _ = parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    tag = cast(str, args.tag)
    output = cast(Path, args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    _ = output.write_text(
        extract_release_notes((ROOT / "CHANGELOG.md").read_text(), tag=tag)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
