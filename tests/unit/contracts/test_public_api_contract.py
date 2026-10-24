import inspect
from functools import cached_property
from importlib.util import find_spec
import os
from pathlib import Path
import subprocess
import sys
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

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PUBLIC_RUNTIME_ENUM_AND_HELPER_NAMES = (
    "AuthContextIdentifierTypeEnum",
    "AuthorizationPermissionTypeEnum",
    "AuthorizationSubjectIdentifierTypeEnum",
    "CertificateStatusEnum",
    "CertificateTypeEnum",
    "ContextIdentifierTypeEnum",
    "CurrencyCodes",
    "EntityPermissionTypeEnum",
    "EuEntityAdminContextIdentifierTypeEnum",
    "EuEntityPermissionTypeEnum",
    "IdentifierTypeEnum",
    "IndirectPermissionTypeEnum",
    "IndirectTargetIdentifierTypeEnum",
    "PermissionTypeEnum",
    "RevocationReasonEnum",
    "SubjectTypeEnum",
    "SubunitIdentifierTypeEnum",
    "TokenAuthorIdentifierTypeEnum",
    "TokenPermissionEnum",
    "TokenStatusEnum",
    "validate_certificate_serial_number",
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


def _pydantic_generic_origin(annotation: object) -> type[object] | None:
    """Return the model behind a parametrized pydantic generic such as ``Page[_T]``."""
    if not inspect.isclass(annotation):
        return None
    metadata = getattr(annotation, "__pydantic_generic_metadata__", None)
    if not isinstance(metadata, dict):
        return None
    origin = metadata.get("origin")
    return origin if isinstance(origin, type) else None


def _annotation_types(annotation: object) -> set[type[object]]:
    types: set[type[object]] = set()
    pending: list[object] = [annotation]

    while pending:
        current = pending.pop()
        pending.extend(get_args(current))
        origin = _pydantic_generic_origin(current)
        if origin is not None:
            # A parametrized generic is published under its own name, and its item
            # types still have to resolve through the same facade.
            types.add(origin)
            metadata = getattr(current, "__pydantic_generic_metadata__", {})
            pending.extend(metadata.get("args") or ())
        elif inspect.isclass(current):
            types.add(current)

    return types


def _annotated_types(cls: type[object]) -> set[type[object]]:
    types: set[type[object]] = set()
    for function in _public_functions(cls):
        hints = get_type_hints(function, include_extras=True)
        for annotation in hints.values():
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


@pytest.mark.parametrize("name", PUBLIC_RUNTIME_ENUM_AND_HELPER_NAMES)
def test_public_model_facade_exports_runtime_enums_and_helpers(name: str) -> None:
    assert name in public_models.__all__
    assert hasattr(public_models, name)


def test_public_model_facade_does_not_export_nip_weights() -> None:
    assert "NIP_WEIGHTS" not in public_models.__all__


def test_xades_facade_reexports_the_credential_holder_of_the_models_facade() -> None:
    """``ksef2.xades`` is where XAdES callers look, so it must hand out one class."""
    import ksef2.xades as public_xades

    assert "XAdESCredentials" in public_xades.__all__
    assert public_xades.XAdESCredentials is public_models.XAdESCredentials


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
            if module_name.startswith(("ksef2.clients.", "ksef2._services.")):
                exported = getattr(public_clients, annotation_type.__name__, None)
                if not _matches_facade_export(exported, annotation_type):
                    missing_clients.add(annotation_type.__name__)
                else:
                    pending_clients.add(annotation_type)
            elif module_name.startswith("ksef2._domain.models"):
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
                if annotation_type.__module__.startswith("ksef2._domain.models"):
                    pending_models.add(annotation_type)

        for annotation_type in _annotated_types(model_type):
            if annotation_type.__module__.startswith("ksef2._domain.models"):
                pending_models.add(annotation_type)

    assert not missing_clients, (
        "Public client/service annotation types missing from ksef2.clients: "
        f"{', '.join(sorted(missing_clients))}"
    )
    assert not missing_models, (
        "Public domain annotation types missing from ksef2.models: "
        f"{', '.join(sorted(missing_models))}"
    )


def _class_type_parameters(cls: type[object]) -> tuple[object, ...]:
    """Return the type variables a generic class declares, as the runtime sees them."""
    return tuple(getattr(cls, "__parameters__", ()))


def test_pager_page_type_hints_remain_public() -> None:
    """``page()`` names its cursor and its generic ``Page`` return for introspection.

    The runtime check on this return is narrower than the annotation, so a passing
    collection must not be taken as evidence that the annotation is still readable. Read
    it here, and pin that the page is parameterized by the pager's own type variable.
    """
    for pager_class in (public_clients.Pager, public_clients.AsyncPager):
        hints = get_type_hints(pager_class.page, include_extras=True)

        assert hints["cursor"] == str | None
        returned = hints["return"]
        assert _pydantic_generic_origin(returned) is public_models.Page
        metadata = getattr(returned, "__pydantic_generic_metadata__", None)
        assert isinstance(metadata, dict)
        assert tuple(metadata["args"]) == _class_type_parameters(pager_class)

        signature = inspect.signature(pager_class.page)
        assert list(signature.parameters) == ["self", "cursor"]
        assert signature.parameters["cursor"].default is None


# The runtime-check switch is read while ksef2 is imported, so a process cannot turn it
# on halfway through. This child re-reads the same contract in a fresh interpreter and
# then pages a real client, which is the return value beartype used to reject.
_PAGE_HINTS_CHILD = """
import inspect
import sys
from typing import get_type_hints

from ksef2.clients import AsyncPager, Pager
from ksef2.models import Page
from tests.unit.clients.test_paging import COLLECTIONS, _client, _page
from tests.unit.support.flavors import Flavor

runtime_checks = sys.argv[1] == "1"

for pager_class in (Pager, AsyncPager):
    hints = get_type_hints(pager_class.page)
    assert hints["cursor"] == str | None, hints
    returned = hints["return"]
    metadata = getattr(returned, "__pydantic_generic_metadata__", None)
    assert isinstance(metadata, dict), returned
    assert metadata["origin"] is Page, returned
    assert tuple(metadata["args"]) == pager_class.__parameters__, returned
    assert list(inspect.signature(pager_class.page).parameters) == ["self", "cursor"]

for flavor in (Flavor("sync"), Flavor("async")):
    collection = next(item for item in COLLECTIONS if item.id == "certificates.list")
    flavor.transport.enqueue(_page(collection, more=True))
    pager = getattr(_client(collection, flavor), collection.method)()
    page = flavor.run(pager.page(None))
    assert isinstance(page, Page), page
    assert page.items, page
    assert page.next_cursor, page

# Prove this interpreter really is in the mode the test asked for, so the checks-on case
# cannot quietly degrade into the checks-off one.
flavor.transport.clear()
flavor.transport.enqueue(_page(collection, more=True))
probe = getattr(_client(collection, flavor), collection.method)()
try:
    flavor.run(probe.page(123))
except Exception as exc:
    checked = type(exc).__name__ == "BeartypeCallHintParamViolation"
    assert checked == runtime_checks, exc
else:
    assert not runtime_checks, "page() did not enforce its own annotation"
print("page hints ok")
"""


@pytest.mark.parametrize(
    "runtime_checks", ["0", "1"], ids=["runtime-checks-off", "runtime-checks-on"]
)
def test_pager_page_annotations_survive_runtime_checks(
    runtime_checks: str,
) -> None:
    """The public ``page()`` signature and a real paged request both hold either way."""
    if runtime_checks == "1" and find_spec("beartype") is None:
        pytest.skip("ksef2[runtime-checks] is not installed")

    environment = os.environ.copy()
    environment["KSEF2_RUNTIME_CHECKS"] = runtime_checks

    completed = subprocess.run(
        [sys.executable, "-c", _PAGE_HINTS_CHILD, runtime_checks],
        capture_output=True,
        text=True,
        check=True,
        cwd=PROJECT_ROOT,
        env=environment,
    )

    assert completed.stdout.strip() == "page hints ok"


def test_testdata_facade_exports_identifier_generators() -> None:
    assert public_testdata.__all__ == ["generate_nip", "generate_pesel"]
    assert len(public_testdata.generate_nip()) == 10
    assert len(public_testdata.generate_pesel()) == 11
