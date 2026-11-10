"""Dependency-free SDK input errors shared by domain models and core services."""

from typing import Any, Callable, cast, override


class KSeFException(Exception):
    """Base exception for all KSeF SDK errors.

    Branch on the exception class, or on ``ksef_code`` for API errors, and never
    on the message text: messages are meant for people and can change.

    Args:
        message: Human-readable error message.
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.

    Attributes:
        code: Stable machine-readable error code of the exception class.
        hint: What to do next, or ``None`` when the SDK does not know the cause. Shown as a ``Hint:`` line in ``str(exc)``.
        context: Structured details about the failure; always contains ``code``, and ``hint`` when there is one.
    """

    code: str = "SDK_ERROR"
    hint: str | None = None

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        **context: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ):
        super().__init__(message)
        if hint is not None:
            self.hint = hint
        self.context: dict[str, Any] = context  # pyright: ignore[reportExplicitAny]
        self.context["code"] = self.code
        if self.hint is not None:
            self.context["hint"] = self.hint

    @override
    def __str__(self) -> str:
        message = super().__str__()
        if self.hint is None:
            return message
        return f"{message}\nHint: {self.hint}"


class KSeFValidationError(KSeFException, ValueError):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Raised when validation fails.

    Args:
        message: Human-readable error message.
        validation_error: Original Pydantic validation error, if one was wrapped.
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.

    Attributes:
        field_path: XML XPath or draft field path, or None when unknown.
        detected_schema: Detected schema name, or None when unknown.
        detected_namespace: Detected root namespace, or None when unknown.
        local_rule: Whether the error comes from a local draft rule.
        accepted_by_ksef: Independently established acceptance, or None when unknown.
    """

    code: str = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        validation_error: object | None = None,
        **context: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        self.field_path: str | None = context.get("field_path")
        self.detected_schema: str | None = context.get("detected_schema")
        self.detected_namespace: str | None = context.get("detected_namespace")
        self.local_rule: bool = context.get("local_rule", False)
        self.accepted_by_ksef: bool | None = context.get("accepted_by_ksef")
        self.validation_error = validation_error
        super().__init__(message, **context)  # pyright: ignore[reportAny]

    def errors(self) -> list[dict[str, object]]:
        """Return Pydantic's structured validation errors when available.

        Returns:
            Structured validation errors, or an empty list when no Pydantic error was wrapped.
        """
        if self.validation_error is None:
            return []
        errors_method = getattr(self.validation_error, "errors", None)
        if errors_method is None:
            return []
        errors = cast(Callable[[], object], errors_method)
        return cast(list[dict[str, object]], errors())


class KSeFArgumentError(KSeFValidationError, TypeError):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Raised when a call combines arguments the SDK does not allow.

    It is raised for "exactly one of" violations, such as passing both or neither
    of ``form_code`` and ``state`` to ``online_session()``. It subclasses
    ``KSeFValidationError`` so existing handlers keep catching it, and
    ``TypeError`` because the call itself is wrong. Through
    ``KSeFValidationError``, it also remains a ``ValueError``.

    Args:
        message: Human-readable error message.
        hint: Next step for this occurrence; overrides the class default.
        **context: Additional structured details, stored in ``context``.
    """

    code: str = "ARGUMENT_ERROR"
    hint: str | None = (
        "Pass exactly one of the mutually exclusive arguments named in the message."
    )


# Preserve the established public identity and pickle path throughout 1.x.
KSeFException.__module__ = "ksef2._core.exceptions"
KSeFValidationError.__module__ = "ksef2._core.exceptions"
KSeFArgumentError.__module__ = "ksef2._core.exceptions"
