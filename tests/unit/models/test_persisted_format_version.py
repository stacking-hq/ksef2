import json

import pytest
from pydantic import SecretStr

from ksef2 import KSeFValidationError
from ksef2._domain.models.base import CURRENT_FORMAT_VERSION, parse_format_version
from ksef2._domain.models.fa3.invoice import KsefInvoiceDraft
from ksef2._domain.models.invoices import ExportResumeState
from ksef2._domain.models.tokens import GeneratedTokenResumeState

KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
IV = "MDEyMzQ1Njc4OWFiY2RlZg=="


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (1, "1"),
        ("1", "1"),
        ("1.0", "1.0"),
        ("1.2", "1.2"),
        ("1.0.1", "1.0.1"),
        ("1.10.20", "1.10.20"),
    ],
)
def test_accepts_dotted_versions_with_supported_major(
    stored: object, expected: str
) -> None:
    assert parse_format_version(stored) == expected


@pytest.mark.parametrize(
    "stored",
    [
        0,
        2,
        -1,
        True,
        False,
        1.0,
        1.2,
        None,
        [1],
        "",
        " 1",
        "1 ",
        "0",
        "2",
        "2.0",
        "0.9",
        "1.",
        ".1",
        "1..2",
        "1.2.3.4",
        "01",
        "1.02",
        "v1",
        "1e0",
        "+1",
        "-1",
        "١",
        "1" * 5000,
    ],
)
def test_rejects_other_versions(stored: object) -> None:
    with pytest.raises(ValueError):
        _ = parse_format_version(stored)


def test_rejection_does_not_echo_the_stored_value() -> None:
    with pytest.raises(ValueError) as caught:
        _ = parse_format_version("secret-version")
    assert "secret-version" not in str(caught.value)


def test_state_writes_the_current_version_as_a_string() -> None:
    state = ExportResumeState(
        reference_number="ref", aes_key=SecretStr(KEY), iv=SecretStr(IV)
    )

    assert state.format_version == CURRENT_FORMAT_VERSION == "1"
    assert state.to_dict()["format_version"] == "1"
    assert json.loads(state.to_json())["format_version"] == "1"


def test_state_reads_the_integer_written_by_earlier_releases() -> None:
    released = {"format_version": 1, "reference_number": "ref"}
    from_dict = GeneratedTokenResumeState.from_dict(released)
    from_json = GeneratedTokenResumeState.from_json(json.dumps(released))

    assert from_dict == from_json
    assert from_dict.format_version == "1"
    assert from_dict.to_dict()["format_version"] == "1"


def test_state_keeps_a_later_minor_version_it_can_read() -> None:
    state = GeneratedTokenResumeState.from_dict(
        {"format_version": "1.2", "reference_number": "ref"}
    )

    assert state.format_version == "1.2"
    assert GeneratedTokenResumeState.from_json(state.to_json()) == state


@pytest.mark.parametrize("stored", [True, 1.0, "2", "1.", "v1", 2])
def test_state_rejects_unreadable_versions(stored: object) -> None:
    with pytest.raises(KSeFValidationError, match="format version"):
        _ = GeneratedTokenResumeState.from_dict(
            {"format_version": stored, "reference_number": "ref"}
        )


def test_invoice_draft_reads_integer_and_dotted_versions() -> None:
    assert KsefInvoiceDraft.model_validate({"format_version": 1}).format_version == "1"
    assert (
        KsefInvoiceDraft.model_validate({"format_version": "1.1"}).format_version
        == "1.1"
    )
    with pytest.raises(KSeFValidationError, match="format version"):
        _ = KsefInvoiceDraft.model_validate({"format_version": True})
