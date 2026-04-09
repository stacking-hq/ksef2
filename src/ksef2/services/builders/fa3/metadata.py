from collections.abc import Sequence
from typing import Literal, cast

from pydantic import Field
from pydantic.config import JsonDict
from pydantic.fields import FieldInfo

BuilderPriority = Literal["common", "advanced", "override"]
BuilderFormat = Literal[
    "date",
    "date-time",
    "decimal-string",
    "enum-string",
    "object",
    "country-code",
]


def builder_param(
    description: str,
    *,
    examples: Sequence[object] | None = None,
    format: BuilderFormat | None = None,
    priority: BuilderPriority | None = None,
    schema_ref: str | None = None,
    prefer_omit_when_null: bool = True,
) -> FieldInfo:
    json_schema_extra: JsonDict = {
        "x-builder-prefer-omit-when-null": prefer_omit_when_null,
    }
    if format is not None:
        json_schema_extra["x-builder-format"] = format
    if priority is not None:
        json_schema_extra["x-builder-priority"] = priority
    if schema_ref is not None:
        json_schema_extra["x-builder-schema-ref"] = schema_ref

    return cast(
        FieldInfo,
        Field(
            description=description,
            examples=list(examples) if examples is not None else None,
            json_schema_extra=json_schema_extra,
        ),
    )
