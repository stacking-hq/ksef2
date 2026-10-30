"""Shared validation for FA(3) domain models built by the public builder."""

import re
from typing import Any, cast

from pydantic import field_validator

from ksef2._core.exceptions import KSeFValidationError
from ksef2._domain.models.base import KSeFBaseModel


_INVALID_XML_CHARACTER = re.compile(
    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)


class Fa3Model(KSeFBaseModel):
    """Opt FA(3) inputs into SDK errors and reject characters XML cannot encode."""

    wrap_validation_errors = True

    def __init__(self, **data: Any) -> None:  # pyright: ignore[reportAny, reportExplicitAny]
        try:
            super().__init__(**data)
        except KSeFValidationError as exc:
            # Keep the shared wrapper, its structured errors and original cause.
            details = exc.errors()
            if not details:
                raise
            detail = details[0]
            location = detail["loc"]
            field = (
                ".".join(str(part) for part in cast(tuple[object, ...], location))
                if isinstance(location, tuple)
                else ""
            )
            exc.field_path = field or type(self).__name__
            exc.detected_schema = "FA(3)"
            exc.local_rule = True
            exc.hint = (
                f"Check {exc.field_path} in the draft. This is a local SDK rule; "
                "for XML already accepted by KSeF, use parse_invoice_xml or render "
                "the original XML instead of rebuilding a draft."
            )
            exc.context.update(
                field_path=exc.field_path,
                detected_schema=exc.detected_schema,
                detected_namespace=None,
                local_rule=True,
                accepted_by_ksef=None,
                hint=exc.hint,
            )
            exc.args = (f"Invalid FA(3) builder {field or 'fields'}: {detail['msg']}",)
            raise

    @field_validator("*")
    @classmethod
    def _validate_xml_text(cls, value: object) -> object:
        values = (
            cast(list[object] | tuple[object, ...], value)
            if isinstance(value, (list, tuple))
            else (value,)
        )
        for item in values:
            if isinstance(item, str) and _INVALID_XML_CHARACTER.search(item):
                raise ValueError("contains a character XML 1.0 cannot encode")
        return cast(object, value)
