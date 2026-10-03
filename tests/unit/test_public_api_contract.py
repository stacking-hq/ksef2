import inspect
from functools import cached_property
from typing import get_args, get_type_hints

import pytest

import ksef2.clients as public_clients
import ksef2.models as public_models
import ksef2.testdata as public_testdata


PUBLIC_DOMAIN_ALIAS_NAMES = (
    "CertificateSerialNumber",
    "CertificateStatusValue",
    "CertificateTypeValue",
    "CertUsage",
    "CertUsageEnum",
    "RevocationReason",
    "SessionStatus",
    "TokenPermission",
    "TokenStatus",
)


def _public_functions(cls: type[object]) -> list[object]:
    functions: list[object] = []

    for name, value in vars(cls).items():
        if name.startswith("_"):
            continue

        function: object | None = None
        if isinstance(value, cached_property):
            function = value.func
        elif isinstance(value, property):
            function = value.fget
        elif isinstance(value, staticmethod | classmethod):
            function = value.__func__
        elif inspect.isfunction(value):
            function = value

        if function is not None:
            functions.append(function)

    return functions


def _annotation_types(annotation: object) -> set[type[object]]:
    types: set[type[object]] = set()
    pending = [annotation]

    while pending:
        current = pending.pop()
        pending.extend(get_args(current))
        if inspect.isclass(current):
            types.add(current)

    return types


def _annotated_types(cls: type[object]) -> set[type[object]]:
    types: set[type[object]] = set()
    for function in _public_functions(cls):
        for annotation in get_type_hints(function, include_extras=True).values():
            types.update(_annotation_types(annotation))
    return types


def _matches_facade_export(exported: object, annotation_type: type[object]) -> bool:
    if exported is annotation_type:
        return True

    # Runtime instrumentation represents quoted annotations as Beartype proxy
    # classes. Keep the normal identity contract and narrowly recognize that
    # framework proxy by its original module and qualified name.
    return (
        inspect.isclass(exported)
        and type(annotation_type).__module__.startswith("beartype.")
        and exported.__module__ == annotation_type.__module__
        and exported.__qualname__ == annotation_type.__qualname__
    )


def test_public_facades_have_unique_resolvable_exports() -> None:
    for facade in (public_clients, public_models):
        assert len(facade.__all__) == len(set(facade.__all__))
        assert all(hasattr(facade, name) for name in facade.__all__)


@pytest.mark.parametrize("name", PUBLIC_DOMAIN_ALIAS_NAMES)
def test_public_model_facade_exports_domain_aliases_used_by_clients(name: str) -> None:
    assert name in public_models.__all__
    assert hasattr(public_models, name)


def test_public_client_annotations_resolve_through_stable_facades() -> None:
    pending_clients = {
        value
        for name in public_clients.__all__
        if inspect.isclass(value := getattr(public_clients, name))
    }
    checked_clients: set[type[object]] = set()
    reachable_models: set[type[object]] = set()
    missing_clients: set[str] = set()

    while pending_clients:
        client_type = pending_clients.pop()
        if client_type in checked_clients:
            continue
        checked_clients.add(client_type)

        for annotation_type in _annotated_types(client_type):
            module_name = annotation_type.__module__
            if module_name.startswith(("ksef2.clients.", "ksef2.services.")):
                exported = getattr(public_clients, annotation_type.__name__, None)
                if not _matches_facade_export(exported, annotation_type):
                    missing_clients.add(annotation_type.__name__)
                else:
                    pending_clients.add(annotation_type)
            elif module_name.startswith("ksef2.domain.models"):
                reachable_models.add(annotation_type)

    checked_models: set[type[object]] = set()
    pending_models = set(reachable_models)
    missing_models: set[str] = set()

    while pending_models:
        model_type = pending_models.pop()
        if model_type in checked_models:
            continue
        checked_models.add(model_type)

        exported = getattr(public_models, model_type.__name__, None)
        if not _matches_facade_export(exported, model_type):
            missing_models.add(model_type.__name__)

        for field in getattr(model_type, "model_fields", {}).values():
            for annotation_type in _annotation_types(field.annotation):
                if annotation_type.__module__.startswith("ksef2.domain.models"):
                    pending_models.add(annotation_type)

        for annotation_type in _annotated_types(model_type):
            if annotation_type.__module__.startswith("ksef2.domain.models"):
                pending_models.add(annotation_type)

    assert not missing_clients, (
        "Public client/service annotation types missing from ksef2.clients: "
        f"{', '.join(sorted(missing_clients))}"
    )
    assert not missing_models, (
        "Public domain annotation types missing from ksef2.models: "
        f"{', '.join(sorted(missing_models))}"
    )


def test_testdata_facade_exports_identifier_generators() -> None:
    assert public_testdata.__all__ == ["generate_nip", "generate_pesel"]
    assert len(public_testdata.generate_nip()) == 10
    assert len(public_testdata.generate_pesel()) == 11
