"""Every KSeF error code documented in ``openapi.json`` is mapped, with hints where known."""

import json
import re
from pathlib import Path
from typing import Any

import httpx
import pytest

from ksef2._core import exceptions, response_errors
from ksef2._core.exceptions import ExceptionCode

SPEC_PATH = Path(__file__).parents[3] / "openapi.json"

# Codes the spec documents that ``ExceptionCode`` deliberately does not list.
# Add a code here only with a comment saying why it is left out.
NOT_MAPPED: set[int] = set()

# First column of the ``| ExceptionCode | ExceptionDescription | Details |``
# markdown tables. The spec has no machine-readable code list, only these tables.
_TABLE_ROW = re.compile(r"^\|\s*(\d{4,5})\s*\|", re.MULTILINE)


def _documented_codes() -> dict[int, set[str]]:
    """Map each documented code to the HTTP statuses whose descriptions list it."""
    spec: dict[str, Any] = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    codes: dict[int, set[str]] = {}
    for operations in spec["paths"].values():
        for operation in operations.values():
            if not isinstance(operation, dict):
                continue
            responses: dict[str, Any] = operation.get("responses", {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            for status, response in responses.items():
                description: str = response.get("description", "")
                if "ExceptionCode" not in description:
                    continue
                for code in _TABLE_ROW.findall(description):
                    codes.setdefault(int(code), set()).add(status)
    return codes


class TestSpecCodes:
    def test_the_spec_scan_finds_the_code_tables(self) -> None:
        codes = _documented_codes()

        assert len(codes) >= 54
        assert {21165, 21178, 21405, 9101, 25001, 26001, 71001} <= codes.keys()

    def test_every_documented_code_is_in_exception_code(self) -> None:
        missing = sorted(
            code
            for code in _documented_codes()
            if code not in NOT_MAPPED and ExceptionCode.from_code(code).value != code
        )

        assert not missing, (
            f"openapi.json documents KSeF codes that ExceptionCode does not list: "
            f"{missing}. Add them to ExceptionCode (with a hint in "
            f"response_errors._CODE_HINTS where the next step is known) and to "
            f"docs/en|pl/reference/errors.md, or to NOT_MAPPED with a reason."
        )

    def test_not_mapped_lists_only_documented_codes(self) -> None:
        assert NOT_MAPPED <= _documented_codes().keys()

    def test_hints_exist_only_for_listed_codes(self) -> None:
        hinted = set(response_errors._CODE_HINTS)  # pyright: ignore[reportPrivateUsage]

        assert all(ExceptionCode.from_code(code).value == code for code in hinted)


def _raise(status: int, code: int) -> exceptions.KSeFApiError:
    response = httpx.Response(
        status,
        json={
            "title": "Bad Request",
            "status": status,
            "instance": "https://ksef.example/errors/1",
            "detail": "general problem",
            "errors": [{"code": code, "description": "Something."}],
            "timestamp": "2026-04-16T12:00:00Z",
            "traceId": "trace-1",
        },
        headers={"content-type": "application/problem+json"},
    )
    with pytest.raises(exceptions.KSeFApiError) as exc_info:
        response_errors.raise_for_ksef_status(response, method="GET", path="/x")
    return exc_info.value


class TestCodeHints:
    @pytest.mark.parametrize(
        "code",
        sorted(response_errors._CODE_HINTS),  # pyright: ignore[reportPrivateUsage]
    )
    def test_a_known_code_carries_its_hint(self, code: int) -> None:
        error = _raise(400, code)

        assert error.hint == response_errors._CODE_HINTS[code]  # pyright: ignore[reportPrivateUsage]
        assert error.exception_code.value == code
        assert f"\nHint: {error.hint}" in str(error)

    def test_a_code_without_a_hint_has_none(self) -> None:
        error = _raise(400, 21164)

        assert type(error) is exceptions.KSeFApiError
        assert error.exception_code is ExceptionCode.INVOICE_NOT_FOUND
        assert error.hint is None

    def test_the_upo_hint_says_a_rejected_invoice_never_gets_one(self) -> None:
        hint = _raise(400, 21178).hint

        assert hint is not None
        assert "wait()" in hint and "KSeFInvoiceRejectedError" in hint

    def test_a_code_hint_wins_over_the_status_hint(self) -> None:
        raised = _raise_legacy(403, 26001)

        assert type(raised) is exceptions.KSeFAuthError
        assert raised.hint == response_errors._CODE_HINTS[26001]  # pyright: ignore[reportPrivateUsage]

    def test_the_status_hint_applies_without_a_code_hint(self) -> None:
        raised = _raise_legacy(401, 21301)

        assert type(raised) is exceptions.KSeFAuthError
        assert raised.hint == response_errors._UNAUTHORIZED_HINT  # pyright: ignore[reportPrivateUsage]


def _raise_legacy(status: int, code: int) -> exceptions.KSeFApiError:
    response = httpx.Response(
        status,
        json={
            "exception": {
                "exceptionDetailList": [
                    {"exceptionCode": code, "exceptionDescription": "Something."}
                ]
            }
        },
    )
    with pytest.raises(exceptions.KSeFApiError) as exc_info:
        response_errors.raise_for_ksef_status(response, method="GET", path="/x")
    return exc_info.value


class TestDocsInSync:
    DOCS = [
        Path(__file__).parents[3] / "docs" / lang / "reference" / "errors.md"
        for lang in ("en", "pl")
    ]

    @pytest.mark.parametrize("path", DOCS, ids=lambda p: p.parts[-3])
    def test_every_code_hint_is_documented(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")

        missing = [
            code
            for code, hint in response_errors._CODE_HINTS.items()  # pyright: ignore[reportPrivateUsage]
            if f"| {code} |" not in text or hint not in text
        ]
        assert not missing, f"{path.name} lacks the hints of codes {missing}"

    @pytest.mark.parametrize("path", DOCS, ids=lambda p: p.parts[-3])
    def test_every_exception_code_is_documented(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")

        missing = [
            member.name
            for member in ExceptionCode
            if member is not ExceptionCode.UNKNOWN_ERROR
            and f"| `{member.value}` | `{member.name}` |" not in text
        ]
        assert not missing, f"{path.name} lacks the ExceptionCode rows {missing}"
