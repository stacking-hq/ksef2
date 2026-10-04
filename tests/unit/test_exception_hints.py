"""Hints on SDK exceptions, and backward compatibility of the exception hierarchy."""

import inspect
import pickle
import re
from types import SimpleNamespace
from typing import Any

import pytest

import ksef2
import ksef2.clients as public_clients
from ksef2._core import exceptions, response_errors
from ksef2._core.exceptions import ExceptionCode
from ksef2._domain.models.session import SessionInvoiceStatusResponse


def _all_exception_classes() -> list[type[exceptions.KSeFException]]:
    return [
        cls
        for _, cls in inspect.getmembers(exceptions, inspect.isclass)
        if issubclass(cls, exceptions.KSeFException)
        and cls.__module__ == exceptions.__name__
    ]


_DUMMY_ARGUMENTS: dict[str, Any] = {
    "reference_number": "ref-1",
    "invoice_reference_number": "inv-ref-1",
    "ksef_number": "1234567890-20260101-ABCDEF-123456-7A",
    "timeout": 3.0,
    "status_code": 400,
    "description": "something",
    "retry_after": 7,
    "message": "boom",
    "exception_code": ExceptionCode.UNKNOWN_ERROR,
    "operation": "upload",
    "host": "storage.example",
    "part_ordinal": 1,
}


def _build(cls: type[exceptions.KSeFException]) -> exceptions.KSeFException | None:
    """Instantiate an exception class from the dummy values its parameters ask for.

    Returns ``None`` for classes that need a model or another exception to build.
    """
    parameters = inspect.signature(cls).parameters
    kwargs: dict[str, Any] = {}
    for name, parameter in parameters.items():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.kind not in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            continue
        if name not in _DUMMY_ARGUMENTS:
            return None
        kwargs[name] = _DUMMY_ARGUMENTS[name]
    return cls(**kwargs)


# --- public methods named in hints -----------------------------------------


def _public_methods() -> set[str]:
    """Names of current, non-deprecated public methods on the public client classes."""
    names: set[str] = set()
    classes = [getattr(public_clients, name) for name in public_clients.__all__]
    classes += [ksef2.Client, ksef2.AsyncClient]
    for cls in classes:
        if not inspect.isclass(cls):
            continue
        for name, member in inspect.getmembers(cls):
            if name.startswith("_"):
                continue
            target = member.fget if isinstance(member, property) else member
            if not callable(target) or getattr(target, "__deprecated__", None):
                continue
            names.add(name)
    return names


def _method_names_in(hint: str) -> set[str]:
    return set(re.findall(r"([A-Za-z_]\w*)\(", hint))


def _all_hints() -> list[tuple[str, str]]:
    hints: list[tuple[str, str]] = []
    for cls in _all_exception_classes():
        if cls.hint:
            hints.append((cls.__name__, cls.hint))
        built = _build(cls)
        instance_hint = built.hint if built else None
        if instance_hint and instance_hint != cls.hint:
            hints.append((f"{cls.__name__} (instance)", instance_hint))
    for (status, code), rule in response_errors._RULES.items():  # pyright: ignore[reportPrivateUsage]
        if rule.hint:
            hints.append((f"rule ({status}, {code})", rule.hint))
    return hints


class TestHintsNameRealMethods:
    def test_the_public_api_helper_sees_the_methods_hints_rely_on(self) -> None:
        methods = _public_methods()

        assert {"wait", "download_upo", "resume_state", "submission"} <= methods
        assert "get_state" not in methods  # deprecated alias of resume_state()

    @pytest.mark.parametrize(("owner", "hint"), _all_hints(), ids=lambda v: str(v)[:60])
    def test_every_method_named_in_a_hint_exists_and_is_not_deprecated(
        self, owner: str, hint: str
    ) -> None:
        methods = _public_methods()

        unknown = _method_names_in(hint) - methods
        assert not unknown, f"{owner} hint names unknown or deprecated: {unknown}"

    def test_a_hint_naming_a_deprecated_method_would_be_caught(self) -> None:
        assert "get_state" not in _public_methods()
        assert _method_names_in("Call `get_state()` first.") == {"get_state"}


class TestHintCoverage:
    TIMEOUTS = [
        c for c in _all_exception_classes() if c.__name__.endswith("TimeoutError")
    ]

    def test_there_are_timeout_classes_to_check(self) -> None:
        assert len(self.TIMEOUTS) >= 10

    @pytest.mark.parametrize("cls", TIMEOUTS, ids=lambda c: c.__name__)
    def test_every_timeout_error_says_how_to_keep_waiting(
        self, cls: type[exceptions.KSeFException]
    ) -> None:
        error = _build(cls)

        assert error is not None and error.hint
        assert "timeout" in error.hint
        assert f"\nHint: {error.hint}" in str(error)

    @pytest.mark.parametrize(
        "cls",
        [
            exceptions.KSeFNotReadyError,
            exceptions.KSeFAuthenticationExpiredError,
            exceptions.KSeFRateLimitError,
            exceptions.KSeFExportFailedError,
            exceptions.KSeFPermissionOperationFailedError,
            exceptions.KSeFCertificateEnrollmentFailedError,
            exceptions.KSeFArgumentError,
        ],
        ids=lambda c: c.__name__,
    )
    def test_named_error_classes_have_a_hint(
        self, cls: type[exceptions.KSeFException]
    ) -> None:
        error = _build(cls)

        assert error is not None and error.hint
        assert error.context["hint"] == error.hint

    def test_timeout_hint_for_processing_names_the_resume_path(self) -> None:
        hint = exceptions.KSeFInvoiceProcessingTimeoutError.hint

        assert hint is not None
        assert "submission(" in hint and "wait()" in hint and "resume_state()" in hint

    def test_hints_are_only_set_when_the_cause_is_known(self) -> None:
        for cls in (
            exceptions.KSeFException,
            exceptions.KSeFApiError,
            exceptions.KSeFSessionError,
            exceptions.KSeFValidationError,
            exceptions.KSeFEncryptionError,
            exceptions.KSeFClientClosedError,
            exceptions.KSeFMetadataPaginationError,
            exceptions.NoCertificateAvailableError,
        ):
            assert cls.hint is None, cls.__name__


class TestHintRendering:
    def test_instance_override_wins_over_the_class_default(self) -> None:
        error = exceptions.KSeFArgumentError("bad", hint="Do this instead.")

        assert error.hint == "Do this instead."
        assert exceptions.KSeFArgumentError.hint != "Do this instead."
        assert error.context["hint"] == "Do this instead."

    def test_str_puts_the_hint_on_its_own_last_line(self) -> None:
        error = exceptions.KSeFApiError(
            400,
            ExceptionCode.UNKNOWN_ERROR,
            "KSeF rejected GET /x (HTTP 400): nope\nTrace ID: t",
            hint="Try again.",
        )

        assert str(error).splitlines() == [
            "KSeF rejected GET /x (HTTP 400): nope",
            "Trace ID: t",
            "Hint: Try again.",
        ]
        assert error.args == ("KSeF rejected GET /x (HTTP 400): nope\nTrace ID: t",)

    def test_no_hint_means_no_hint_line_and_no_context_key(self) -> None:
        error = exceptions.KSeFException("plain", extra=1)

        assert str(error) == "plain"
        assert error.hint is None
        assert error.context == {"extra": 1, "code": "SDK_ERROR"}

    def test_rate_limit_hint_carries_the_wait(self) -> None:
        assert (
            exceptions.KSeFRateLimitError(12, "slow").hint
            == "Wait 12 seconds before retrying."
        )
        assert exceptions.KSeFRateLimitError(None, "slow").hint

    def test_invoice_rejected_hint_and_duplicate_override(self) -> None:
        def rejected_with(code: int) -> exceptions.KSeFInvoiceRejectedError:
            status = SessionInvoiceStatusResponse.model_construct(
                status=SimpleNamespace(
                    code=code, description="d", details=["x"], extensions=None
                )
            )
            return exceptions.KSeFInvoiceRejectedError("r", status)

        rejected = rejected_with(450)
        duplicate = rejected_with(440)

        assert rejected.hint and "send_invoice()" in rejected.hint
        assert duplicate.hint and "originalKsefNumber" in duplicate.hint
        assert exceptions.KSeFInvoiceRejectedError.hint == rejected.hint


class TestBackwardCompatibility:
    def test_except_api_error_catches_not_ready_error(self) -> None:
        with pytest.raises(exceptions.KSeFApiError):
            raise exceptions.KSeFNotReadyError(
                400, ExceptionCode.NOT_PROCESSED_YET, "not yet", ksef_code=21165
            )

    def test_hierarchy_is_unchanged(self) -> None:
        assert issubclass(exceptions.KSeFApiError, exceptions.KSeFException)
        assert issubclass(exceptions.KSeFNotReadyError, exceptions.KSeFApiError)
        assert issubclass(exceptions.KSeFAuthError, exceptions.KSeFApiError)
        assert issubclass(
            exceptions.KSeFAuthenticationExpiredError, exceptions.KSeFAuthError
        )
        assert issubclass(exceptions.KSeFRateLimitError, exceptions.KSeFApiError)
        assert issubclass(
            exceptions.KSeFInvoiceRejectedError, exceptions.KSeFSessionError
        )
        assert issubclass(exceptions.KSeFArgumentError, exceptions.KSeFValidationError)
        assert issubclass(exceptions.KSeFArgumentError, TypeError)

    def test_not_ready_error_is_exported_from_the_package(self) -> None:
        assert ksef2.KSeFNotReadyError is exceptions.KSeFNotReadyError
        assert "KSeFNotReadyError" in ksef2.__all__

    def test_old_constructors_and_attributes_still_work(self) -> None:
        api = exceptions.KSeFApiError(404, ExceptionCode.UPO_NOT_FOUND, "gone", None)
        auth = exceptions.KSeFAuthError(401, "denied")
        limit = exceptions.KSeFRateLimitError(3, "slow")
        expired = exceptions.KSeFAuthenticationExpiredError()

        assert (api.status_code, api.exception_code, api.response) == (
            404,
            ExceptionCode.UPO_NOT_FOUND,
            None,
        )
        assert (api.ksef_code, api.trace_id, api.details) == (None, None, [])
        assert (auth.status_code, auth.exception_code) == (
            401,
            ExceptionCode.UNKNOWN_ERROR,
        )
        assert (limit.status_code, limit.retry_after) == (429, 3)
        assert (expired.status_code, expired.code) == (401, "AUTHENTICATION_EXPIRED")
        assert api.code == "API_ERROR" and api.context["code"] == "API_ERROR"
        assert str(api) == "gone"

    def test_exception_code_enum_keeps_its_members_and_unknown_fallback(self) -> None:
        assert ExceptionCode.NOT_PROCESSED_YET == 21165
        assert ExceptionCode.UPO_NOT_FOUND == 21178
        assert ExceptionCode.from_code(99999) is ExceptionCode.UNKNOWN_ERROR
        assert ExceptionCode.from_code(None) is ExceptionCode.UNKNOWN_ERROR

    def test_services_can_still_match_not_processed_yet(self) -> None:
        error = _raise_api(400, 21165)

        assert isinstance(error, exceptions.KSeFApiError)
        assert error.status_code == 400
        assert error.exception_code == ExceptionCode.NOT_PROCESSED_YET


def _raise_api(status: int, code: int) -> exceptions.KSeFApiError:
    import httpx

    response = httpx.Response(
        status,
        json={"exception": {"exceptionDetailList": [{"exceptionCode": code}]}},
    )
    with pytest.raises(exceptions.KSeFApiError) as exc_info:
        response_errors.raise_for_ksef_status(response, method="GET", path="/x")
    return exc_info.value


class TestPickling:
    """Classes whose constructor takes just a message pickled before; they still do."""

    @pytest.mark.parametrize(
        "error",
        [
            exceptions.KSeFException("plain", answer=42),
            exceptions.KSeFValidationError("invalid"),
            exceptions.KSeFArgumentError("bad arguments"),
            exceptions.KSeFArgumentError("bad arguments", hint="Do this."),
            exceptions.KSeFAuthenticationExpiredError(),
            exceptions.KSeFSessionError("closed"),
            exceptions.KSeFSessionError("closed", hint="Reopen it."),
            exceptions.KSeFEncryptionError("bad key"),
        ],
        ids=lambda e: f"{type(e).__name__}-{e.args[0][:12]}",
    )
    def test_round_trip_keeps_type_hint_and_context(
        self, error: exceptions.KSeFException
    ) -> None:
        restored = pickle.loads(pickle.dumps(error))

        assert type(restored) is type(error)
        assert restored.hint == error.hint
        assert restored.context.get("hint") == error.context.get("hint")
        assert ("Hint:" in str(restored)) is (error.hint is not None)
