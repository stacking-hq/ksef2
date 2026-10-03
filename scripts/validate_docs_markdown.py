#!/usr/bin/env python3
"""Fail when product docs contain MDX instead of plain Markdown.

Product docs are plain Markdown; Starlight components live only in ksef2-docs.
This gate rejects ``.mdx`` files, ``import``/``export`` lines and JSX component
tags outside code fences and inline code.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import cast

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
ESM_RE = re.compile(r"^(import|export)\b")
COMPONENT_TAG_RE = re.compile(r"</?[A-Z][A-Za-z0-9_.]*(?=[\s/>])")
JSX_ATTRIBUTE_RE = re.compile(r"<[A-Za-z][^<>]*\sclassName=")
INLINE_CODE_RE = re.compile(r"(`+).+?\1")


def markdown_lines_outside_code(text: str) -> list[tuple[int, str]]:
    """Return ``(line number, line)`` pairs that are not inside a code fence."""
    lines: list[tuple[int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                continue
            lines.append((number, line))
        elif (
            match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
            and line.strip() == match.group(1)
        ):
            fence = None
    return lines


def validate_page(text: str) -> list[str]:
    """Return MDX-only constructs found in one Markdown page."""
    errors: list[str] = []
    for number, line in markdown_lines_outside_code(text):
        if esm := ESM_RE.match(line):
            errors.append(f"line {number}: MDX {esm.group(1)} statement")
            continue
        prose = INLINE_CODE_RE.sub("", line)
        tag = COMPONENT_TAG_RE.search(prose)
        if tag:
            errors.append(f"line {number}: JSX component tag {tag.group(0)}>")
        elif JSX_ATTRIBUTE_RE.search(prose):
            errors.append(f"line {number}: JSX attribute className")
    return errors


def validate_docs_markdown(docs_dir: Path) -> list[str]:
    """Return plain-Markdown violations for every file under ``docs_dir``."""
    errors = [
        f"{path.relative_to(docs_dir)}: .mdx pages are not allowed; use plain .md"
        for path in sorted(docs_dir.rglob("*.mdx"))
    ]
    pages = sorted(docs_dir.rglob("*.md"))
    if not pages:
        errors.append(f"{docs_dir}: no Markdown pages found to validate")
    for page in pages:
        relative = page.relative_to(docs_dir)
        errors.extend(
            f"{relative}: {error}"
            for error in validate_page(page.read_text(encoding="utf-8"))
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("docs_dir", nargs="?", default="docs")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    docs_dir = Path(cast(str, args.docs_dir))

    errors = validate_docs_markdown(docs_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Validated plain Markdown in {len(list(docs_dir.rglob('*.md')))} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
