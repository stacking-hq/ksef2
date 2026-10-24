"""Shared Pydantic base classes for SDK models and query parameter models."""

import json
import re
from importlib import import_module
from collections.abc import Mapping
from typing import Annotated, Any, Callable, ClassVar, Literal, Self, cast, override

from pydantic import (
    AliasChoices,
    AliasGenerator,
    AliasPath,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    model_validator,
    ValidationError,
)
from pydantic.alias_generators import to_camel

from ksef2._logging import get_logger

logger = get_logger(__name__)


def _validation_exception(error: ValidationError, model_name: str) -> Exception:
    exception_module = import_module("ksef2._core.exceptions")
    error_type = cast(
        Callable[..., Exception], getattr(exception_module, "KSeFValidationError")
    )
    reason = error.errors()[0]["msg"]
    return error_type(f"Invalid {model_name} input: {reason}", validation_error=error)


_AliasSpec = str | AliasPath | AliasChoices | None


def _resolve_aliases(alias: _AliasSpec) -> set[str]:
    """Return all string alternatives from a single alias specification."""
    if alias is None:
        return set()
    if isinstance(alias, str):
        return {alias}
    if isinstance(alias, AliasChoices):
        return {c for c in alias.choices if isinstance(c, str)}
    return set()  # AliasPath — nested path, not a flat key


def _build_known_keys(cls: type[BaseModel]) -> set[str]:
    """Collect every key that Pydantic will accept as input for *cls*.

    Covers field names, explicit ``validation_alias`` / ``alias``, and
    ``AliasGenerator``-produced aliases (e.g. camelCase on ``KSeFBaseParams``).
    """
    known: set[str] = set()
    alias_gen = cls.model_config.get("alias_generator")

    for name, field in cls.model_fields.items():
        known.add(name)

        # Explicit validation_alias takes precedence over alias_generator
        if field.validation_alias is not None:
            known |= _resolve_aliases(field.validation_alias)
        elif (
            isinstance(alias_gen, AliasGenerator)
            and alias_gen.validation_alias is not None
        ):
            va = alias_gen.validation_alias(name)
            if isinstance(va, str):
                known.add(va)

        # alias is used as a fallback when validation_alias is not set
        if field.alias is not None:
            known |= _resolve_aliases(field.alias)
        elif (
            field.validation_alias is None
            and isinstance(alias_gen, AliasGenerator)
            and alias_gen.alias is not None
        ):
            known.add(alias_gen.alias(name))

    return known


class KSeFBaseModel(BaseModel):
    """Base model that ignores undeclared fields and logs warnings about them."""

    model_config = ConfigDict(extra="ignore")
    wrap_validation_errors: ClassVar[bool] = False

    def __init__(self, **data: Any) -> None:  # pyright: ignore[reportAny, reportExplicitAny]
        try:
            super().__init__(**data)
        except ValidationError as exc:
            if self.wrap_validation_errors:
                raise _validation_exception(exc, type(self).__name__) from exc
            raise

    @classmethod
    @override
    def model_validate(cls, obj: Any, **kwargs: Any) -> Self:  # pyright: ignore[reportAny, reportExplicitAny]
        """Validate an object, optionally wrapping input errors for SDK-facing models.

        Args:
            obj: Object to validate.
            **kwargs: Pydantic validation options.

        Returns:
            The validated model.
        """
        try:
            return super().model_validate(obj, **kwargs)  # pyright: ignore[reportAny]
        except ValidationError as exc:
            if cls.wrap_validation_errors:
                raise _validation_exception(exc, cls.__name__) from exc
            raise

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        known = _build_known_keys(cls)
        extra = [k for k in data if k not in known]
        if extra:
            logger.warning(
                "ignoring undeclared fields", model=cls.__name__, fields=extra
            )
        return data


SUPPORTED_FORMAT_MAJOR = 1
"""Major version of the persisted-state format this SDK reads."""

CURRENT_FORMAT_VERSION = "1"
"""Persisted-state format version this SDK writes."""

_FORMAT_VERSION = re.compile(r"(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){0,2}")


def parse_format_version(value: object) -> str:
    """Read a persisted format version and accept the supported major version.

    Versions are dotted numbers such as ``"1"``, ``"1.2"`` or ``"1.0.1"``. The
    integer ``1`` that earlier releases wrote is read as ``"1"``. Any version with
    major ``1`` is accepted; a higher major, a malformed string, a boolean or a
    float is rejected.

    Args:
        value: Stored version, a string or the integer written by earlier releases.

    Returns:
        The version as a string.

    Raises:
        ValueError: If the version is malformed or its major is unsupported.
    """
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("format version must be a dotted number string such as '1'")
    text = str(value)
    if _FORMAT_VERSION.fullmatch(text) is None:
        raise ValueError("format version must be a dotted number string such as '1'")
    if int(text.split(".", 1)[0]) != SUPPORTED_FORMAT_MAJOR:
        raise ValueError(
            f"unsupported format version; this SDK reads major version "
            f"{SUPPORTED_FORMAT_MAJOR}"
        )
    return text


type PersistedFormatVersion = Annotated[str, BeforeValidator(parse_format_version)]
"""Persisted-state version field: a dotted number string with a supported major."""


class KSeFPersistedModel(KSeFBaseModel):
    """Base for versioned state whose stored shape must fail closed."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        """Let Pydantic reject unknown persisted fields without ignore warnings."""
        return data


class KSeFResumeState(KSeFPersistedModel):
    """Base for the saveable state of an operation KSeF finishes asynchronously.

    A subclass names the operation and adds whatever else the resume call needs
    to rebuild its handle. Stored state fails closed: any ``format_version``
    whose major is not ``1`` is rejected, and so is a field this SDK does not know.
    These states hold no secrets, so ``to_dict()`` and ``to_json()`` are the
    persistence format and show the same fields as ``model_dump()``.
    """

    format_version: PersistedFormatVersion = CURRENT_FORMAT_VERSION
    """Version of the serialized state format, a dotted number; currently ``"1"``."""
    reference_number: str
    """KSeF reference number of the operation."""

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] | str = "json",
    ) -> dict[str, object]:
        """Export the state as a dictionary.

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary with every field of the state.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Export the state as JSON.

        Args:
            indent: Number of spaces to indent nested values; ``None`` for compact output.

        Returns:
            JSON text with every field of the state.
        """
        data = self.to_dict(mode="json")
        if indent is None:
            return json.dumps(data, separators=(",", ":"))
        return json.dumps(data, indent=indent)

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Restore the state from a dictionary exported by ``to_dict()``.

        Args:
            state: Mapping produced by ``to_dict()``.

        Returns:
            The restored state.
        """
        return cls.model_validate(state)

    @classmethod
    def from_json(cls, state: str | bytes | bytearray) -> Self:
        """Restore the state from JSON exported by ``to_json()``.

        Args:
            state: JSON text produced by ``to_json()``.

        Returns:
            The restored state.
        """
        return cls.model_validate_json(state)


class KSeFBaseParams[ParamsT](KSeFBaseModel):
    """Base model for query-parameter objects serialized with camelCase aliases."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        use_enum_values=True,
        serialize_by_alias=True,
    )

    def to_query_params(self) -> ParamsT:
        """Serialize the model into a JSON-safe query-parameter mapping.

        Returns:
            Query parameters keyed by their API names, with unset values omitted.
        """
        return cast(
            ParamsT, self.model_dump(by_alias=True, exclude_none=True, mode="json")
        )
