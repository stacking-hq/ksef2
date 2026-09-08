"""Require successful invoice workflow tests before signing off a release."""

import argparse
from pathlib import Path
from typing import cast
from xml.etree import ElementTree


REQUIRED_TESTS = (
    "test_open_batch_session",
    "test_get_session_upo_by_reference",
    "test_example_quickstart",
    "test_example_send_invoice",
    "test_example_send_query_export_download",
    "test_example_send_batch",
    "test_example_submit_batch",
)


def verify_integration_results(report: Path) -> list[str]:
    """Reject absent, skipped, or failing release-critical invoice tests."""
    root = ElementTree.parse(report).getroot()
    cases = list(root.iter("testcase"))
    errors: list[str] = []
    for name in REQUIRED_TESTS:
        matches = [case for case in cases if case.get("name") == name]
        if not matches:
            errors.append(f"Required integration test was not run: {name}")
        for case in matches:
            if any(
                case.find(outcome) is not None
                for outcome in ("skipped", "failure", "error")
            ):
                errors.append(f"Required integration test did not pass: {name}")
    if not cases:
        errors.append("Integration report contains no tests")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("report", type=Path)
    args = parser.parse_args()
    errors = verify_integration_results(cast(Path, args.report))
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"All {len(REQUIRED_TESTS)} required invoice integration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
