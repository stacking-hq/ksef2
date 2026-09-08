#!/usr/bin/env python3
"""Validate the public example scripts against the supported SDK surface."""

import ast
import re
import sys
from pathlib import Path
from typing import override

PUBLIC_EXAMPLES_ROOT = Path(__file__).resolve().parent / "examples"
INTERNAL_MODULE_PREFIXES = (
    "ksef2.core",
    "ksef2.domain",
    "ksef2.endpoints",
    "ksef2.infra",
    "ksef2.services",
)
SENSITIVE_OUTPUT_RE = re.compile(r"(?:access_token|refresh_token|\.token)\b")


class ExampleVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.errors: list[str] = []
        self.client_context_depth = 0

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(alias.name, node.lineno)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._check_import(node.module, node.lineno)
        self.generic_visit(node)

    @override
    def visit_With(self, node: ast.With) -> None:
        has_client_context = any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id in {"Client", "AsyncClient"}
            for item in node.items
        )
        if has_client_context:
            self.client_context_depth += 1
        self.generic_visit(node)
        if has_client_context:
            self.client_context_depth -= 1

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {
            "Client",
            "AsyncClient",
        }:
            if self.client_context_depth == 0:
                self.errors.append(
                    f"line {node.lineno}: {node.func.id} must be used as a context manager"
                )

        if isinstance(node.func, ast.Name) and node.func.id == "print":
            for argument in node.args:
                rendered = ast.unparse(argument)
                if (
                    SENSITIVE_OUTPUT_RE.search(rendered)
                    and "valid_until" not in rendered
                ):
                    self.errors.append(
                        f"line {node.lineno}: print() exposes token material"
                    )
        self.generic_visit(node)

    def _check_import(self, module: str, line: int) -> None:
        if module.startswith(INTERNAL_MODULE_PREFIXES):
            self.errors.append(
                f"line {line}: internal import {module!r}; use the public facade"
            )


def main() -> int:
    failures: list[str] = []
    for path in sorted(PUBLIC_EXAMPLES_ROOT.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path}: syntax error: {exc}")
            continue
        visitor = ExampleVisitor(path)
        visitor.visit(tree)
        failures.extend(f"{path}: {error}" for error in visitor.errors)

    if failures:
        print("Example validation failed:", file=sys.stderr)
        print("\n".join(f"- {failure}" for failure in failures), file=sys.stderr)
        return 1

    print(
        f"Validated {len(list(PUBLIC_EXAMPLES_ROOT.rglob('*.py')))} public example files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
