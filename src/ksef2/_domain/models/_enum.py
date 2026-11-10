"""Shared coercion for public enum inputs."""

from enum import Enum
from typing import TypeVar, cast

from ksef2._errors import KSeFArgumentError

EnumT = TypeVar("EnumT", bound=Enum)


def _valid_value(member: Enum) -> str:
    value = cast(object, member.value)
    if not isinstance(value, str) or value == member.name:
        return member.name
    return f"{member.name} ({value})"


def coerce_enum(
    enum_type: type[EnumT],
    value: object,
    *,
    snake_case_only: bool = False,
    parameter: str | None = None,
) -> EnumT:
    """Match an enum member, name, or string value without regard to case."""
    if isinstance(value, enum_type):
        return value

    if isinstance(value, str):
        normalized = value.strip().casefold()
        for member in enum_type:
            if (not snake_case_only or value == str(cast(object, member.value))) and (
                member.name.casefold() == normalized
                or str(cast(object, member.value)).casefold() == normalized
            ):
                return member

    suggestion = ""
    if isinstance(value, str):
        for member in enum_type:
            candidate = str(cast(object, member.value))
            if value.casefold() == candidate.replace("_", "").casefold():
                suggestion = f' did you mean "{candidate}"?'
                break
    valid_values = ", ".join(
        str(cast(object, member.value)) if snake_case_only else _valid_value(member)
        for member in enum_type
    )
    raise KSeFArgumentError(
        f"Invalid {parameter or enum_type.__name__} value {value!r}.{suggestion} Valid values are: {valid_values}.",
        hint="Pass a snake_case permission value or its enum member."
        if snake_case_only
        else "Pass one of the listed enum names or values.",
    )
