"""Fail unless the required KSeF integration workflows actually ran and passed.

The release command in ``.github/workflows/publish.yml`` runs
``pytest tests/integration/ -m integration``, and a skipped test is green there.
Every workflow listed in ``REQUIRED_WORKFLOWS`` submits an invoice to the real KSeF
TEST environment, so one that never ran proves nothing about the release it gates.
This script reads the JUnit XML that ``just release-integration`` writes and treats
a required workflow as a failure unless it genuinely passed.

Usage:
    uv run python scripts/verify_integration_results.py output/release-integration.xml
"""

import argparse
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parent.parent

# Workflows that must reach KSeF TEST and come back passing on every release.
REQUIRED_WORKFLOWS: tuple[str, ...] = (
    "test_open_batch_session",
    "test_get_session_upo_by_reference",
    "test_example_quickstart",
    "test_example_send_invoice",
    "test_example_send_query_export_download",
    "test_example_send_batch",
    "test_example_submit_batch",
)

# KSeF TEST builds export packages on its own schedule, so
# test_example_send_query_export_download may legitimately skip when a scheduled
# export never becomes ready. That one skip is tolerated, and it is tolerated by
# marker rather than by test name: the reason has to carry this text, so an
# unrelated skip in the same test -- missing credentials, a bad fixture -- still
# fails the gate instead of hiding behind the exemption.
EXPORT_TIMEOUT_SKIP_MARKER = "KSEF2_EXPORT_TIMEOUT"
MARKER_TOLERATED_SKIPS: dict[str, str] = {
    "test_example_send_query_export_download": EXPORT_TIMEOUT_SKIP_MARKER,
}

_PASSED = "passed"
_SKIPPED = "skipped"
_FAILED = "failed"
_ERRORED = "errored"


def _test_outcomes(report: ElementTree.Element) -> dict[str, list[str]]:
    """Map each test name in the report to the outcome each entry reported.

    A name can appear more than once, from a rerun or from parametrization, so
    every outcome is kept and the worst one decides.
    """
    outcomes: dict[str, list[str]] = {}

    for case in report.iter("testcase"):
        raw_name = case.get("name")
        if not raw_name:
            continue
        # Strip a parametrization suffix so test_x[case] still matches test_x.
        name = raw_name.split("[", 1)[0]

        if case.find("error") is not None:
            outcome = _ERRORED
        elif case.find("failure") is not None:
            outcome = _FAILED
        elif case.find("skipped") is not None:
            outcome = _SKIPPED
        else:
            outcome = _PASSED

        outcomes.setdefault(name, []).append(outcome)

    return outcomes


def _describe_skip(case_name: str, report: ElementTree.Element) -> str:
    for case in report.iter("testcase"):
        if (case.get("name") or "").split("[", 1)[0] != case_name:
            continue
        skipped = case.find("skipped")
        if skipped is None:
            continue
        reason = skipped.get("message") or (skipped.text or "").strip()
        if reason:
            return reason if len(reason) <= 200 else f"{reason[:200]}..."
    return "no skip reason recorded"


def _skip_is_tolerated(name: str, report: ElementTree.Element) -> bool:
    """Return whether a skip of ``name`` is the one documented exemption.

    The exemption needs both the right test and the marker in the reason, so the
    reason is read from the report rather than assumed.
    """
    marker = MARKER_TOLERATED_SKIPS.get(name)
    if marker is None:
        return False

    for case in report.iter("testcase"):
        if (case.get("name") or "").split("[", 1)[0] != name:
            continue
        skipped = case.find("skipped")
        if skipped is None:
            continue
        reason = f"{skipped.get('message') or ''} {skipped.text or ''}"
        if marker in reason:
            return True

    return False


def verify_integration_results(report_path: Path) -> list[str]:
    """Return the reasons this integration report must not gate a release."""
    if not report_path.is_file():
        return [f"JUnit report {report_path} does not exist; run the integration suite"]

    try:
        report = ElementTree.parse(str(report_path)).getroot()
    except ElementTree.ParseError as exc:
        return [f"JUnit report {report_path} is not well-formed XML: {exc}"]

    outcomes = _test_outcomes(report)
    if not outcomes:
        return [
            f"JUnit report {report_path} contains no test cases. An empty report "
            "means the integration suite never ran; a gate that validated zero "
            "workflows is worse than no gate at all."
        ]

    errors: list[str] = []
    for name in REQUIRED_WORKFLOWS:
        reported = outcomes.get(name)
        if reported is None:
            errors.append(
                f"required workflow {name} is missing from the report; it was "
                "never collected or never selected by -m integration"
            )
            continue

        for outcome in sorted(set(reported)):
            if outcome == _PASSED:
                continue
            if outcome == _SKIPPED and _skip_is_tolerated(name, report):
                print(
                    f"tolerating documented export-timeout skip in {name}: "
                    f"{_describe_skip(name, report)}"
                )
                continue
            if outcome == _SKIPPED:
                errors.append(
                    f"required workflow {name} was SKIPPED, so it never reached "
                    f"KSeF TEST. Reason: {_describe_skip(name, report)}"
                )
            else:
                errors.append(f"required workflow {name} {outcome}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require the release-blocking KSeF integration workflows to have passed",
    )
    _ = parser.add_argument(
        "report",
        type=Path,
        nargs="?",
        default=ROOT / "output" / "release-integration.xml",
        help="JUnit XML written by pytest --junitxml",
    )
    args = parser.parse_args()
    report_path = cast(Path, args.report)

    errors = verify_integration_results(report_path)
    if errors:
        for error in errors:
            print(f"integration results rejected: {error}", file=sys.stderr)
        return 1

    print(
        f"integration results verified: all {len(REQUIRED_WORKFLOWS)} "
        "required workflows reached KSeF TEST and passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
