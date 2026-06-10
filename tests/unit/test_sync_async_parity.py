import importlib
import inspect
import pkgutil
import re
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Any

import pytest

PACKAGES = ("ksef2.clients", "ksef2.endpoints", "ksef2.services")

SKIPPED_MODULES = {
    "ksef2.clients._metadata_pagination": "shared pagination helpers, not a public sync facade",
    "ksef2.endpoints.shared": "shared endpoint helper protocols, not a public sync facade",
    "ksef2.services.auth": "sync-only authentication helper module with no async facade class",
    "ksef2.services.batch_preparation": "shared batch preparation helpers, not a public sync facade",
}

SKIPPED_CLASSES = {
    "ksef2.endpoints.auth.AuthSessionsQueryParams": "shared request parameter model",
    "ksef2.endpoints.auth.XadesAuthParams": "shared request parameter model",
    "ksef2.endpoints.async_auth.AuthSessionsQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_auth.XadesAuthParams": "shared request parameter model",
    "ksef2.endpoints.base.OffsetPaginationQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_base.OffsetPaginationQueryParams": "shared request parameter model",
    "ksef2.endpoints.invoices.InvoiceMetadataQueryParams": "shared request parameter model",
    "ksef2.endpoints.invoices.SessionInvoiceListQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_invoices.InvoiceMetadataQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_invoices.SessionInvoiceListQueryParams": "shared request parameter model",
    "ksef2.endpoints.session.ListSessionsQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_session.ListSessionsQueryParams": "shared request parameter model",
    "ksef2.endpoints.tokens.ListTokensQueryParams": "shared request parameter model",
    "ksef2.endpoints.async_tokens.ListTokensQueryParams": "shared request parameter model",
}

KNOWN_DIVERGENCES = {
    "BaseEndpoints.build_params": (
        "TODO: sync still accepts a generic TypeAdapter while async already accepts "
        "the shared QueryParamsAdapter protocol."
    ),
}

ASYNC_METHOD_ALIASES = {
    "aclose": "close",
}

ANNOTATION_REPLACEMENTS = (
    ("AsyncIterator", "Iterator"),
    ("AsyncIterable", "Iterable"),
    ("AsyncGenerator", "Generator"),
    ("httpx.AsyncClient", "httpx.Client"),
    ("AsyncMiddleware", "Middleware"),
)


@dataclass(frozen=True)
class ApiClassPair:
    sync_class: type[Any]
    async_class: type[Any]


@dataclass(frozen=True)
class ApiMember:
    name: str
    value: Any

    @property
    def callable(self) -> Callable[..., Any]:
        if isinstance(self.value, property):
            if self.value.fget is None:
                msg = f"Property {self.name} has no getter"
                raise AssertionError(msg)
            return self.value.fget
        return self.value

    @property
    def has_docstring(self) -> bool:
        return inspect.getdoc(self.callable) is not None


@dataclass(frozen=True)
class NormalizedParameter:
    name: str
    kind: inspect._ParameterKind
    default: str
    annotation: str


def test_sync_async_class_pairs_are_discovered_by_convention() -> None:
    failures: list[str] = []

    for package_name in PACKAGES:
        package = importlib.import_module(package_name)
        module_names = _module_names(package)

        for module_name in sorted(module_names):
            if module_name.startswith("async_") or module_name == "__init__":
                continue

            sync_module_name = f"{package_name}.{module_name}"
            if sync_module_name in SKIPPED_MODULES:
                continue

            sync_module = importlib.import_module(sync_module_name)
            sync_classes = _public_classes(sync_module)
            async_module_short_name = f"async_{module_name}"
            async_module_name = f"{package_name}.{async_module_short_name}"

            if async_module_short_name not in module_names:
                if sync_classes:
                    failures.append(
                        f"{sync_module_name} has public sync classes without "
                        f"{async_module_name}: {', '.join(sorted(sync_classes))}"
                    )
                continue

            async_module = importlib.import_module(async_module_name)
            async_classes = _public_classes(async_module)
            expected_async_names = {f"Async{name}" for name in sync_classes}
            expected_sync_names = {
                name.removeprefix("Async")
                for name in async_classes
                if name.startswith("Async")
            }

            for missing in sorted(expected_async_names - set(async_classes)):
                sync_name = missing.removeprefix("Async")
                failures.append(
                    f"{sync_module_name}.{sync_name} is missing async twin {missing}"
                )

            for missing in sorted(set(sync_classes) - expected_sync_names):
                failures.append(
                    f"{async_module_name}.Async{missing} is missing sync twin {missing}"
                )

            unexpected_async = sorted(
                name for name in async_classes if not name.startswith("Async")
            )
            for name in unexpected_async:
                failures.append(
                    f"{async_module_name}.{name} is public but does not follow AsyncX naming"
                )

        for module_name in sorted(
            name for name in module_names if name.startswith("async_")
        ):
            sync_module_short_name = module_name.removeprefix("async_")
            sync_module_name = f"{package_name}.{sync_module_short_name}"
            async_module_name = f"{package_name}.{module_name}"
            if (
                sync_module_short_name not in module_names
                and async_module_name not in SKIPPED_MODULES
            ):
                failures.append(
                    f"{async_module_name} has no sync sibling {sync_module_name}"
                )

    assert not failures, "Sync/async class discovery mismatches:\n" + "\n".join(
        failures
    )


def test_public_method_surface_matches_between_sync_and_async_classes() -> None:
    failures: list[str] = []

    for pair in _api_class_pairs():
        sync_members = _public_members(pair.sync_class)
        async_members = _public_members(pair.async_class)
        sync_by_name = {_normalized_member_name(name): name for name in sync_members}
        async_by_name = {_normalized_member_name(name): name for name in async_members}

        for name in sorted(set(sync_by_name) - set(async_by_name)):
            failures.append(
                f"{pair.sync_class.__name__}.{sync_by_name[name]} is missing from "
                f"{pair.async_class.__name__}"
            )

        for name in sorted(set(async_by_name) - set(sync_by_name)):
            failures.append(
                f"{pair.async_class.__name__}.{async_by_name[name]} is missing from "
                f"{pair.sync_class.__name__}"
            )

    assert not failures, "Sync/async public method surface mismatches:\n" + "\n".join(
        failures
    )


def test_public_method_signatures_match_between_sync_and_async_classes() -> None:
    failures: list[str] = []
    seen_divergences: set[str] = set()

    for pair in _api_class_pairs():
        sync_members = _public_members(pair.sync_class)
        async_members = _public_members(pair.async_class)
        sync_by_name = {
            _normalized_member_name(name): member
            for name, member in sync_members.items()
        }
        async_by_name = {
            _normalized_member_name(name): member
            for name, member in async_members.items()
        }

        for name in sorted(set(sync_by_name) & set(async_by_name)):
            sync_member = sync_by_name[name]
            async_member = async_by_name[name]
            divergence_key = f"{pair.sync_class.__name__}.{sync_member.name}"

            if _normalized_signature(sync_member) == _normalized_signature(
                async_member
            ):
                continue

            if divergence_key in KNOWN_DIVERGENCES:
                seen_divergences.add(divergence_key)
                continue

            failures.append(
                f"{pair.sync_class.__name__}.{sync_member.name} signature does not match "
                f"{pair.async_class.__name__}.{async_member.name}\n"
                f"  sync:  {_signature(sync_member)}\n"
                f"  async: {_signature(async_member)}"
            )

    stale_divergences = sorted(set(KNOWN_DIVERGENCES) - seen_divergences)
    for key in stale_divergences:
        failures.append(f"{key} is listed in KNOWN_DIVERGENCES but now matches")

    assert not failures, "Sync/async signature mismatches:\n" + "\n".join(failures)


def test_public_method_docstring_presence_matches() -> None:
    gaps: list[str] = []

    for pair in _api_class_pairs():
        sync_members = _public_members(pair.sync_class)
        async_members = _public_members(pair.async_class)
        sync_by_name = {
            _normalized_member_name(name): member
            for name, member in sync_members.items()
        }
        async_by_name = {
            _normalized_member_name(name): member
            for name, member in async_members.items()
        }

        for name in sorted(set(sync_by_name) & set(async_by_name)):
            sync_member = sync_by_name[name]
            async_member = async_by_name[name]
            if sync_member.has_docstring == async_member.has_docstring:
                continue

            missing_side = "async" if sync_member.has_docstring else "sync"
            gaps.append(
                f"{pair.sync_class.__name__}.{sync_member.name} / "
                f"{pair.async_class.__name__}.{async_member.name}: missing {missing_side} docstring"
            )

    if not gaps:
        return

    message = (
        f"Docstring parity is not yet enforced because there are {len(gaps)} gaps.\n"
        + "\n".join(gaps)
    )
    warnings.warn(message, stacklevel=1)
    pytest.xfail(message)


def _module_names(package: ModuleType) -> set[str]:
    return {
        module.name
        for module in pkgutil.iter_modules(package.__path__)
        if not module.ispkg
    }


def _public_classes(module: ModuleType) -> dict[str, type[Any]]:
    classes: dict[str, type[Any]] = {}
    for name, value in vars(module).items():
        full_name = f"{module.__name__}.{name}"
        if (
            inspect.isclass(value)
            and value.__module__ == module.__name__
            and not name.startswith("_")
            and full_name not in SKIPPED_CLASSES
        ):
            classes[name] = value
    return classes


def _api_class_pairs() -> list[ApiClassPair]:
    pairs: list[ApiClassPair] = []

    for package_name in PACKAGES:
        package = importlib.import_module(package_name)
        module_names = _module_names(package)

        for module_name in sorted(module_names):
            if module_name.startswith("async_") or module_name == "__init__":
                continue

            sync_module_name = f"{package_name}.{module_name}"
            if sync_module_name in SKIPPED_MODULES:
                continue

            async_module_short_name = f"async_{module_name}"
            if async_module_short_name not in module_names:
                continue

            sync_module = importlib.import_module(sync_module_name)
            async_module = importlib.import_module(
                f"{package_name}.{async_module_short_name}"
            )
            sync_classes = _public_classes(sync_module)
            async_classes = _public_classes(async_module)

            for sync_name, sync_class in sorted(sync_classes.items()):
                async_class = async_classes.get(f"Async{sync_name}")
                if async_class is not None:
                    pairs.append(
                        ApiClassPair(sync_class=sync_class, async_class=async_class)
                    )

    return pairs


def _public_members(cls: type[Any]) -> dict[str, ApiMember]:
    members: dict[str, ApiMember] = {}

    for name, value in vars(cls).items():
        if name.startswith("_"):
            continue

        if isinstance(value, property):
            members[name] = ApiMember(name=name, value=value)
        elif isinstance(value, staticmethod | classmethod):
            members[name] = ApiMember(name=name, value=value.__func__)
        elif inspect.isfunction(value):
            members[name] = ApiMember(name=name, value=value)

    return members


def _normalized_member_name(name: str) -> str:
    return ASYNC_METHOD_ALIASES.get(name, name)


def _signature(member: ApiMember) -> inspect.Signature:
    return inspect.signature(inspect.unwrap(member.callable))


def _normalized_signature(member: ApiMember) -> tuple[NormalizedParameter, ...]:
    return tuple(
        _normalized_parameter(parameter)
        for parameter in _signature(member).parameters.values()
        if parameter.name != "self"
    )


def _normalized_parameter(parameter: inspect.Parameter) -> NormalizedParameter:
    return NormalizedParameter(
        name=parameter.name,
        kind=parameter.kind,
        default=_normalized_default(parameter.default),
        annotation=_normalized_annotation(parameter.annotation),
    )


def _normalized_default(default: Any) -> str:
    if default is inspect.Signature.empty:
        return "<empty>"
    return repr(default)


def _normalized_annotation(annotation: Any) -> str:
    if annotation is inspect.Signature.empty:
        return "<empty>"

    text = str(annotation).replace("typing.", "")
    text = re.sub(r"<class '([^']+)'>", r"\1", text)
    text = re.sub(r"\.async_([a-z_]+)\.", r".\1.", text)

    for async_type, sync_type in ANNOTATION_REPLACEMENTS:
        text = text.replace(async_type, sync_type)

    return re.sub(r"\bAsync([A-Z][A-Za-z0-9_]*)", r"\1", text)
