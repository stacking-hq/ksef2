#!/usr/bin/env python3
"""Validate product-owned documentation before site assembly."""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docs_dir", nargs="?", default="docs")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    manifest_path = docs_dir / "docs.manifest.json"
    if not manifest_path.is_file():
        print(f"missing manifest: {manifest_path}", file=sys.stderr)
        return 1

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not manifest.get("product"):
        print("manifest must include product", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in sorted(docs_dir.rglob("*")):
        if path.is_dir() or path.name.startswith("."):
            continue
        relative = path.relative_to(docs_dir)
        if relative.parts and relative.parts[0] == "assets":
            continue
        if path.suffix == ".mdx":
            errors.append(f"{relative}: product docs must be Markdown, not MDX")
            continue
        if path.suffix != ".md":
            continue
        if relative.name == "README.md" and len(relative.parts) == 1:
            continue
        if not has_frontmatter(path):
            errors.append(f"{relative}: missing YAML frontmatter")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def has_frontmatter(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return False
    return any(line.strip() == "---" for line in lines[1:])


if __name__ == "__main__":
    sys.exit(main())
