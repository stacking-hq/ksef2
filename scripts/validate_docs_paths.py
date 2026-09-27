#!/usr/bin/env python3
"""Fail when documentation points at a retired KSeF profile config path."""

import argparse
import sys
from pathlib import Path
from typing import cast

OBSOLETE_PROFILE_PATH = "~/.config/ksef/config.toml"
CANONICAL_PROFILE_PATH = "~/.config/ksef2/config.toml"
LEGACY_FALLBACK_PROFILE_PATH = "~/.config/ksef2-cli/config.toml"

DOC_SUFFIXES = {".md", ".mdx"}


def documented_pages(docs_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in docs_dir.rglob("*")
        if path.is_file()
        and path.suffix in DOC_SUFFIXES
        and "assets" not in path.relative_to(docs_dir).parts
    )


def validate_docs_paths(docs_dir: Path) -> list[str]:
    """Return documentation mistakes for the profile config paths."""
    pages = documented_pages(docs_dir)
    if not pages:
        return [f"{docs_dir}: no documentation files found to validate"]

    errors: list[str] = []
    canonical_pages = 0

    for page in pages:
        text = page.read_text(encoding="utf-8")
        relative = page.relative_to(docs_dir)
        if OBSOLETE_PROFILE_PATH in text:
            errors.append(f"{relative}: uses retired {OBSOLETE_PROFILE_PATH}")
        if LEGACY_FALLBACK_PROFILE_PATH in text and CANONICAL_PROFILE_PATH not in text:
            errors.append(
                f"{relative}: documents {LEGACY_FALLBACK_PROFILE_PATH} without "
                f"{CANONICAL_PROFILE_PATH}"
            )
        if CANONICAL_PROFILE_PATH in text:
            canonical_pages += 1

    if canonical_pages == 0:
        errors.append(f"{docs_dir}: no page documents {CANONICAL_PROFILE_PATH}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("docs_dir", nargs="?", default="docs")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    docs_dir = Path(cast(str, args.docs_dir))

    errors = validate_docs_paths(docs_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Validated profile paths in {len(documented_pages(docs_dir))} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
