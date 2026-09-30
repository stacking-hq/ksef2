"""Offline tests for the release gate in scripts/verify_integration_results.py.

Every case here writes a synthetic JUnit report: the gate must be trustworthy
without reaching KSeF TEST, because its whole job is to notice when the real
suite did not run.
"""

from html import escape
from pathlib import Path
from typing import Sequence

import pytest

from scripts.verify_integration_results import (
    EXPORT_TIMEOUT_SKIP_MARKER,
    REQUIRED_WORKFLOWS,
    verify_integration_results,
)

_EMITTED_NAME = "test_example_send_batch"
_TOLERATED_NAME = "test_example_send_query_export_download"

_OUTCOME_ELEMENT = {"skipped": "skipped", "failed": "failure", "errored": "error"}


def _junit(cases: Sequence[tuple[str, str, str | None]]) -> str:
    """Build a JUnit XML report from (name, outcome, reason) triples."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<testsuites>",
        f'<testsuite name="pytest" tests="{len(cases)}">',
    ]
    for name, outcome, reason in cases:
        opening = f'  <testcase classname="tests.integration" name="{name}" time="1.0">'
        if outcome == "passed":
            lines.append(opening[:-1] + "/>")
            continue
        element = _OUTCOME_ELEMENT[outcome]
        lines.append(opening)
        lines.append(
            f'    <{element} message="{escape(reason or "", quote=True)}" '
            f'type="{element}"/>'
        )
        lines.append("  </testcase>")
    lines += ["</testsuite>", "</testsuites>"]
    return "\n".join(lines)


def _all_required_passed() -> list[tuple[str, str, str | None]]:
    return [(name, "passed", None) for name in REQUIRED_WORKFLOWS]


def _with_outcome(name: str, outcome: str, reason: str | None = None) -> str:
    """Return a report where one required workflow reports ``outcome``."""
    cases = [
        (n, outcome if n == name else "passed", reason if n == name else None)
        for n in REQUIRED_WORKFLOWS
    ]
    return _junit(cases)


def _write(tmp_path: Path, xml: str) -> Path:
    report = tmp_path / "release-integration.xml"
    report.write_text(xml, encoding="utf-8")
    return report


def test_all_required_workflows_passed_is_accepted(tmp_path: Path) -> None:
    errors = verify_integration_results(
        _write(tmp_path, _junit(_all_required_passed()))
    )

    assert errors == []


@pytest.mark.parametrize("outcome", ["failed", "errored"])
def test_failed_or_errored_workflow_is_rejected(tmp_path: Path, outcome: str) -> None:
    report = _write(tmp_path, _with_outcome(_EMITTED_NAME, outcome, "boom"))

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert _EMITTED_NAME in errors[0]
    assert outcome in errors[0]


def test_skipped_workflow_is_rejected_and_reports_the_reason(
    tmp_path: Path,
) -> None:
    report = _write(
        tmp_path,
        _with_outcome(_EMITTED_NAME, "skipped", "Set KSEF2_TEST_INVOICE_SELLER_NIP"),
    )

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "SKIPPED" in errors[0]
    assert "Set KSEF2_TEST_INVOICE_SELLER_NIP" in errors[0]


def test_missing_workflow_is_rejected(tmp_path: Path) -> None:
    cases = [(n, "passed", None) for n in REQUIRED_WORKFLOWS if n != _EMITTED_NAME]
    report = _write(tmp_path, _junit(cases))

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert _EMITTED_NAME in errors[0]
    assert "missing" in errors[0]


def test_empty_report_is_rejected(tmp_path: Path) -> None:
    report = _write(
        tmp_path,
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuites><testsuite name="pytest" tests="0"/></testsuites>',
    )

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "no test cases" in errors[0]


def test_missing_report_file_is_rejected(tmp_path: Path) -> None:
    errors = verify_integration_results(tmp_path / "absent.xml")

    assert len(errors) == 1
    assert "does not exist" in errors[0]


def test_malformed_report_is_rejected(tmp_path: Path) -> None:
    report = _write(tmp_path, "<testsuites><oops")

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "not well-formed" in errors[0]


def test_documented_export_timeout_skip_is_tolerated(tmp_path: Path) -> None:
    report = _write(
        tmp_path,
        _with_outcome(
            _TOLERATED_NAME,
            "skipped",
            f"{EXPORT_TIMEOUT_SKIP_MARKER} KSeF TEST export package REF-1 "
            "was not ready after 120.0s",
        ),
    )

    errors = verify_integration_results(report)

    assert errors == []


def test_export_timeout_test_skipped_for_any_other_reason_is_rejected(
    tmp_path: Path,
) -> None:
    """The exemption is earned by the marker, not by the test name."""
    report = _write(
        tmp_path,
        _with_outcome(_TOLERATED_NAME, "skipped", "Set KSEF2_EXAMPLE_SELLER_NIP"),
    )

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "SKIPPED" in errors[0]


def test_marker_in_a_different_workflow_is_not_tolerated(tmp_path: Path) -> None:
    report = _write(
        tmp_path,
        _with_outcome(_EMITTED_NAME, "skipped", EXPORT_TIMEOUT_SKIP_MARKER),
    )

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "SKIPPED" in errors[0]


def test_parametrized_workflow_matches_its_required_name(tmp_path: Path) -> None:
    cases = [(name, "passed", None) for name in REQUIRED_WORKFLOWS]
    cases[REQUIRED_WORKFLOWS.index(_EMITTED_NAME)] = (
        f"{_EMITTED_NAME}[case-1]",
        "passed",
        None,
    )
    report = _write(tmp_path, _junit(cases))

    assert verify_integration_results(report) == []


def test_a_failing_rerun_of_a_passing_workflow_is_rejected(tmp_path: Path) -> None:
    cases = _all_required_passed()
    cases.append((_EMITTED_NAME, "failed", "second attempt broke"))
    report = _write(tmp_path, _junit(cases))

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "failed" in errors[0]


def test_a_skipped_rerun_of_a_passing_workflow_is_rejected(tmp_path: Path) -> None:
    """One genuine pass plus a skip is not evidence the workflow ran as required."""
    cases = _all_required_passed()
    cases.append((_EMITTED_NAME, "skipped", "environment drifted between attempts"))
    report = _write(tmp_path, _junit(cases))

    errors = verify_integration_results(report)

    assert len(errors) == 1
    assert "SKIPPED" in errors[0]


def test_unrelated_failures_alongside_required_workflows_are_not_reported(
    tmp_path: Path,
) -> None:
    """The gate owns the required list, so one broken optional test stays silent."""
    cases = _all_required_passed() + [("test_example_limits_query", "failed", "boom")]
    report = _write(tmp_path, _junit(cases))

    assert verify_integration_results(report) == []
