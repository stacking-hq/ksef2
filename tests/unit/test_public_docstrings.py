"""Docstring gate for the public API.

Every name in the public ``__all__`` lists, plus the classes reachable through
their public method and property signatures, must carry Google-style
docstrings. The API reference is generated from these docstrings, so a missing
one is a hole in the reference.

Run ``python tests/unit/test_public_docstrings.py`` for a coverage report.
"""

import ast
import dataclasses
import importlib
import inspect
import re
import sys
import textwrap
import types
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

import pytest
from pydantic import BaseModel

PUBLIC_MODULES = (
    "ksef2",
    "ksef2.clients",
    "ksef2.models",
    "ksef2.fa3",
    "ksef2.xades",
    "ksef2.profiles",
    "ksef2.renderers",
    "ksef2.raw",
    "ksef2.raw.mappers",
    "ksef2.raw.mappers.auth",
    "ksef2.testdata",
)

# Generated code is documented by its generator, not by hand.
GENERATED_MODULE_PREFIXES = ("ksef2._infra.schema",)

# Public names that may lack a docstring, each with the reason. Empty by default:
# an entry here needs a real exception, not a backlog item.
ALLOWLIST: dict[str, str] = {}

_SECTION_RE = re.compile(
    r"^(\s*)(Args|Returns|Yields|Raises|Example|Examples|Note):\s*$"
)
_ARG_RE = re.compile(r"^\s+\*{0,2}(\w+)(?:\s*\(.*?\))?\s*:")


@dataclass(frozen=True)
class Issue:
    unit: str
    problem: str


@dataclass
class Report:
    units: set[str]
    issues: list[Issue]
    fields: int
    undocumented_fields: int


def _is_generated(module: str) -> bool:
    return module.startswith(GENERATED_MODULE_PREFIXES)


def _is_ours(obj: object) -> bool:
    module = getattr(obj, "__module__", "") or ""
    name = getattr(obj, "__name__", "")
    # Private names and parametrized generics (``Base[Param]``) are not documented API.
    if name.startswith("_") or "[" in name:
        return False
    return module.startswith("ksef2") and not _is_generated(module)


def _own_doc(obj: object) -> str:
    if inspect.isclass(obj):
        doc = obj.__dict__.get("__doc__")
    else:
        doc = getattr(obj, "__doc__", None)
    return inspect.cleandoc(doc) if isinstance(doc, str) else ""


def _sections(doc: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in doc.splitlines():
        match = _SECTION_RE.match(line)
        if match and not line.startswith(" "):
            current = str(match.group(2))
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def _documented_args(doc: str) -> set[str]:
    names: set[str] = set()
    for line in _sections(doc).get("Args", []):
        match = _ARG_RE.match(line)
        if match:
            names.add(match.group(1))
    return names


def _check_callable(
    unit: str,
    func: typing.Any,
    doc: str,
    *,
    drop_first: bool,
    check_returns: bool = True,
    extra_arg_docs: str = "",
) -> list[Issue]:
    issues: list[Issue] = []
    summary = next((line.strip() for line in doc.splitlines() if line.strip()), "")
    if not summary:
        return [Issue(unit, "missing docstring summary")]
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return issues
    params = list(signature.parameters.values())
    if drop_first and params:
        params = params[1:]
    documented = _documented_args(doc) | _documented_args(extra_arg_docs)
    missing = [p.name for p in params if p.name not in documented]
    if missing:
        issues.append(
            Issue(unit, f"parameters missing from Args: {', '.join(missing)}")
        )
    if check_returns:
        returns = signature.return_annotation
        is_none = returns is None or returns is type(None) or returns == "None"
        no_return = returns is typing.NoReturn or returns is typing.Never
        if (
            returns is not inspect.Signature.empty
            and not is_none
            and not no_return
            and "Returns" not in _sections(doc)
            and "Yields" not in _sections(doc)
        ):
            issues.append(Issue(unit, "missing Returns:"))
    return issues


def _field_nodes(cls: type) -> list[tuple[str, bool]] | None:
    """Return ``(field name, has attribute docstring)`` for fields in the class body."""
    try:
        source = textwrap.dedent(inspect.getsource(cls))
    except (OSError, TypeError):
        return None
    tree = ast.parse(source)
    class_def = tree.body[0]
    if not isinstance(class_def, ast.ClassDef):
        return None
    fields: list[tuple[str, bool]] = []
    body = class_def.body
    for index, node in enumerate(body):
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        name = node.target.id
        if name.startswith("_") or "ClassVar" in ast.unparse(node.annotation):
            continue
        following = body[index + 1] if index + 1 < len(body) else None
        documented = (
            isinstance(following, ast.Expr)
            and isinstance(following.value, ast.Constant)
            and isinstance(following.value.value, str)
        )
        fields.append((name, documented))
    return fields


def _annotation_classes(annotation: object) -> Iterator[type]:
    if isinstance(annotation, str):
        return
    if inspect.isclass(annotation):
        yield annotation
    origin = typing.get_origin(annotation)
    if inspect.isclass(origin):
        yield origin
    for arg in typing.get_args(annotation):
        yield from _annotation_classes(arg)
    value = getattr(annotation, "__value__", None)  # PEP 695 aliases
    if value is not None and not inspect.isclass(annotation):
        yield from _annotation_classes(value)


def _hints(func: Callable[..., object], owner: type | None) -> dict[str, object]:
    localns = dict(vars(owner)) if owner is not None else None
    try:
        return typing.get_type_hints(func, localns=localns)
    except Exception:
        pass
    # Fall back to resolving annotations one by one, skipping unresolvable ones.
    resolved: dict[str, object] = {}
    namespace = getattr(inspect.unwrap(func), "__globals__", {})
    for name, annotation in getattr(func, "__annotations__", {}).items():
        if isinstance(annotation, str):
            try:
                annotation = eval(annotation, namespace, localns)  # noqa: S307
            except Exception:
                continue
        resolved[name] = annotation
    return resolved


def audit() -> Report:
    units: set[str] = set()
    issues: list[Issue] = []
    seen_classes: set[type] = set()
    fields = 0
    undocumented_fields = 0
    queue: list[type] = []

    def record(unit: str, found: list[Issue]) -> None:
        units.add(unit)
        issues.extend(found)

    def enqueue_from(func: Callable[..., object], owner: type | None) -> None:
        hints = _hints(func, owner)
        for annotation in hints.values():
            for cls in _annotation_classes(annotation):
                if _is_ours(cls) and cls not in seen_classes:
                    queue.append(cls)

    def visit_function(
        unit: str, func: Callable[..., object], owner: type | None, drop_first: bool
    ) -> None:
        record(
            unit,
            _check_callable(unit, func, _own_doc(func), drop_first=drop_first),
        )
        enqueue_from(func, owner)

    def visit_class(cls: type) -> None:
        nonlocal fields, undocumented_fields
        if cls in seen_classes:
            return
        seen_classes.add(cls)
        qual = f"{cls.__module__}.{cls.__qualname__}"
        class_doc = _own_doc(cls)
        if not class_doc:
            record(qual, [Issue(qual, "missing class docstring")])
        else:
            units.add(qual)
        is_model = issubclass(cls, BaseModel) or dataclasses.is_dataclass(cls)
        init = cls.__dict__.get("__init__")
        if (
            inspect.isfunction(init)
            and init.__module__.startswith("ksef2")
            and not issubclass(cls, (BaseModel, Enum))
            and not dataclasses.is_dataclass(cls)
        ):
            init_unit = f"{qual}.__init__"
            init_issues = _check_callable(
                init_unit,
                init,
                _own_doc(init) or class_doc,
                drop_first=True,
                check_returns=False,
                extra_arg_docs=class_doc,
            )
            record(init_unit, init_issues)
        field_info = _field_nodes(cls) if is_model else None
        if field_info:
            for name, documented in field_info:
                fields += 1
                if not documented:
                    undocumented_fields += 1
                    issues.append(Issue(f"{qual}.{name}", "undocumented model field"))
        for name, member in list(vars(cls).items()):
            if name.startswith("_"):
                continue
            unit = f"{qual}.{name}"
            raw = member
            if isinstance(raw, (staticmethod, classmethod)):
                drop = isinstance(raw, classmethod)
                func = raw.__func__
                visit_function(unit, func, cls, drop_first=drop)
            elif isinstance(raw, property):
                if raw.fget is None:
                    continue
                prop_issues = _check_callable(
                    unit,
                    raw.fget,
                    inspect.cleandoc(raw.__doc__ or ""),
                    drop_first=True,
                )
                record(unit, prop_issues)
                enqueue_from(raw.fget, cls)
            elif isinstance(raw, cached_property):
                func = raw.func
                record(
                    unit,
                    _check_callable(
                        unit,
                        func,
                        inspect.cleandoc(func.__doc__ or ""),
                        drop_first=True,
                    ),
                )
                enqueue_from(func, cls)
            elif inspect.isfunction(raw):
                visit_function(unit, raw, cls, drop_first=True)
        # Inherited public members are documented where their base defines them.
        for base in cls.__mro__[1:]:
            if _is_ours(base) and base not in seen_classes:
                queue.append(base)
        # Fields' own annotations can also point at further public classes.
        try:
            hints = typing.get_type_hints(cls)
        except Exception:
            hints = {}
        for annotation in hints.values():
            for sub in _annotation_classes(annotation):
                if _is_ours(sub) and sub not in seen_classes:
                    queue.append(sub)

    for module_name in PUBLIC_MODULES:
        module = importlib.import_module(module_name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name)
            if isinstance(obj, types.ModuleType):
                continue
            if inspect.isclass(obj):
                if _is_ours(obj):
                    queue.append(obj)
            elif inspect.isfunction(obj) and _is_ours(obj):
                unit = f"{obj.__module__}.{obj.__qualname__}"
                if unit not in units:
                    visit_function(unit, obj, None, drop_first=False)

    while queue:
        visit_class(queue.pop())

    return Report(units, issues, fields, undocumented_fields)


def _allowed(issue: Issue) -> bool:
    return issue.unit in ALLOWLIST


def test_allowlist_entries_have_reasons() -> None:
    for unit, reason in ALLOWLIST.items():
        assert reason.strip(), f"allowlist entry {unit} needs a reason"


def test_public_api_is_fully_documented() -> None:
    report = audit()
    problems = sorted(
        f"{issue.unit}: {issue.problem}"
        for issue in report.issues
        if not _allowed(issue)
    )
    assert not problems, f"{len(problems)} public docstring problem(s):\n" + "\n".join(
        problems
    )


def test_audit_reaches_the_documented_surface() -> None:
    units = audit().units
    expected = (
        "ksef2._clients.base.Client",
        "ksef2._clients.async_base.AsyncClient.authentication",
        "ksef2._clients.authenticated.AuthenticatedClient.online_session",
        "ksef2._services.invoices.InvoicesService.export_and_download",
        "ksef2._services.builders.fa3.root.StandardInvoiceBuilder.build",
        "ksef2._services.builders.fa3.sub.rows.RowsBuilder.add_line",
        "ksef2._domain.models.invoices.InvoicesFilter.for_seller",
        "ksef2._core.exceptions.KSeFApiError",
        "ksef2.fa3.FA3InvoiceBuilder",
    )
    missing = [name for name in expected if name not in units]
    assert not missing, f"audit no longer reaches: {missing}"
    assert len(units) > 1000


def test_allowlist_has_no_stale_entries() -> None:
    report = audit()
    flagged = {issue.unit for issue in report.issues}
    stale = sorted(unit for unit in ALLOWLIST if unit not in flagged)
    assert not stale, f"allowlist entries no longer needed: {stale}"


@pytest.mark.parametrize("unit", sorted(ALLOWLIST))
def test_allowlist_unit_is_public(unit: str) -> None:
    assert not any(part.startswith("_") for part in unit.split(".")[2:])


if __name__ == "__main__":
    result = audit()
    flagged = {issue.unit for issue in result.issues}
    full = len(result.units - flagged)
    print(
        f"public units fully documented: {full}/{len(result.units)}; "
        f"model fields documented: {result.fields - result.undocumented_fields}/{result.fields}"
    )
    if "--list" in sys.argv:
        for issue in sorted(result.issues, key=lambda i: (i.unit, i.problem)):
            print(f"{issue.unit}: {issue.problem}")
