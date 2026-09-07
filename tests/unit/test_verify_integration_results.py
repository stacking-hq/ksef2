from pathlib import Path
from xml.etree import ElementTree

import pytest

from scripts.verify_integration_results import (
    REQUIRED_TESTS,
    verify_integration_results,
)


@pytest.mark.parametrize(
    "outcome", ["passed", "skipped", "failure", "error", "missing"]
)
def test_release_requires_every_invoice_workflow_to_pass(
    tmp_path: Path, outcome: str
) -> None:
    suite = ElementTree.Element("testsuite")
    for name in REQUIRED_TESTS:
        if name == REQUIRED_TESTS[0] and outcome == "missing":
            continue
        case = ElementTree.SubElement(suite, "testcase", name=name)
        if name == REQUIRED_TESTS[0] and outcome not in ("passed", "missing"):
            ElementTree.SubElement(case, outcome)
    report = tmp_path / "results.xml"
    ElementTree.ElementTree(suite).write(report)
    errors = verify_integration_results(report)
    if outcome == "passed":
        assert errors == []
    else:
        assert len(errors) == 1
        assert REQUIRED_TESTS[0] in errors[0]


def test_release_rejects_an_empty_integration_report(tmp_path: Path) -> None:
    report = tmp_path / "results.xml"
    report.write_text("<testsuites/>")
    assert "Integration report contains no tests" in verify_integration_results(report)
