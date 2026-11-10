"""Keep input validation independent of implementation services."""

import ast
import importlib
from pathlib import Path

import pytest

from ksef2 import KSeFArgumentError, KSeFException, KSeFValidationError
from ksef2 import _errors
from ksef2._core import exceptions


def test_domain_has_no_core_dependency() -> None:
    root = Path(__file__).resolve().parents[3] / "src" / "ksef2" / "_domain"
    violations: list[str] = []
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                if (node.module or "").startswith("ksef2._core"):
                    violations.append(f"{path.name}:{node.lineno}")
            elif isinstance(node, ast.Import):
                if any(alias.name.startswith("ksef2._core") for alias in node.names):
                    violations.append(f"{path.name}:{node.lineno}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"import_module", "__import__"}:
                    violations.append(f"{path.name}:{node.lineno}: dynamic import")
    assert not violations, violations


@pytest.mark.parametrize(
    "name", ["KSeFException", "KSeFValidationError", "KSeFArgumentError"]
)
def test_shared_errors_preserve_identity_and_module(name: str) -> None:
    cls = getattr(_errors, name)
    assert cls is getattr(exceptions, name)
    assert (
        cls
        is {
            "KSeFException": KSeFException,
            "KSeFValidationError": KSeFValidationError,
            "KSeFArgumentError": KSeFArgumentError,
        }[name]
    )
    assert getattr(importlib.import_module(cls.__module__), cls.__name__) is cls
    assert cls.__module__ == "ksef2._core.exceptions"
