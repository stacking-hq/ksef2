#!/usr/bin/env python3
"""Validate that examples and documentation only import the public SDK surface.

Checks ``import`` lines in the example scripts, in fenced Python blocks of the
documentation pages and in the READMEs against the rule in
``docs/en/reference/public-api.md``: a module path with an underscore-prefixed
component is private and must not appear in examples or documentation.
"""

import argparse
import ast
import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast, override

REPO_ROOT = Path(__file__).resolve().parent.parent

DOC_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(ksef2[\w.]*)\s+import\b|import\s+(ksef2[\w.]*))"
)
FENCE_OPEN_RE = re.compile(r"^\s*```\s*(?:python|py)\b")
FENCE_CLOSE_RE = re.compile(r"^\s*```\s*$")
DOC_SUFFIXES = {".md"}


def is_public_module(module: str) -> bool:
    """Return whether ``module`` is a public import path.

    The contract is: a module path with no underscore-prefixed component is
    public; anything with one is private.
    """
    parts = module.split(".")
    if parts[0] != "ksef2":
        return True
    return not any(part.startswith("_") for part in parts[1:])


def _import_error(module: str, line: int) -> str | None:
    if is_public_module(module):
        return None
    return f"line {line}: private import {module!r}; use the public facade"


class ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[str] = []

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(alias.name, node.lineno)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0 and node.module:
            self._check_import(node.module, node.lineno)

    def _check_import(self, module: str, line: int) -> None:
        error = _import_error(module, line)
        if error:
            self.errors.append(error)


def check_python_source(source: str) -> list[str]:
    """Return non-public imports found in one example script."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"syntax error: {exc}"]
    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.errors


def check_markdown_source(text: str) -> list[str]:
    """Return non-public imports found in fenced Python blocks of one page.

    Documentation snippets are often partial, so import lines are matched per
    line instead of parsing each block.
    """
    errors: list[str] = []
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        if not in_block:
            in_block = bool(FENCE_OPEN_RE.match(line))
            continue
        if FENCE_CLOSE_RE.match(line):
            in_block = False
            continue
        match = DOC_IMPORT_RE.match(line)
        if match:
            error = _import_error(match.group(1) or match.group(2), number)
            if error:
                errors.append(error)
    return errors


def example_files(root: Path) -> list[Path]:
    return sorted((root / "scripts" / "examples").rglob("*.py"))


def markdown_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for locale in ("en", "pl"):
        docs_dir = root / "docs" / locale
        if docs_dir.is_dir():
            paths.extend(
                p
                for p in docs_dir.rglob("*")
                if p.is_file() and p.suffix in DOC_SUFFIXES
            )
    paths.extend(
        p
        for p in (
            root / "README.md",
            root / "README.pl.md",
            root / "scripts" / "examples" / "README.md",
        )
        if p.is_file()
    )
    return sorted(paths)


def _scan(
    paths: Iterable[Path], root: Path, checker: Callable[[str], list[str]]
) -> list[str]:
    failures: list[str] = []
    for path in paths:
        errors = checker(path.read_text(encoding="utf-8"))
        failures.extend(f"{path.relative_to(root)}: {error}" for error in errors)
    return failures


def validate(root: Path) -> tuple[list[str], int, int]:
    """Return ``(failures, example_count, markdown_count)`` for ``root``."""
    examples = example_files(root)
    quickstart = root / "scripts" / "quickstart.py"
    if quickstart.is_file():
        examples.append(quickstart)
    pages = markdown_files(root)

    failures: list[str] = []
    if not examples:
        failures.append("no example scripts found under scripts/examples")
    if not any(p.suffix in DOC_SUFFIXES and "docs" in p.parts for p in pages):
        failures.append("no documentation pages found under docs/en or docs/pl")
    failures.extend(_scan(examples, root, check_python_source))
    failures.extend(_scan(pages, root, check_markdown_source))
    return failures, len(examples), len(pages)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("root", nargs="?", default=str(REPO_ROOT))
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(cast(str, args.root))

    failures, example_count, page_count = validate(root)
    if failures:
        print("Example validation failed:", file=sys.stderr)
        print("\n".join(f"- {failure}" for failure in failures), file=sys.stderr)
        return 1

    print(
        f"Validated {example_count} example files and {page_count} documentation files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
