from pathlib import Path

import pytest

from scripts import test_coverage_badge as badge_script

from scripts.test_coverage_badge import build_badge, check_badge, render_badge


def write_coverage_xml(path: Path, line_rate: str) -> None:
    _ = path.write_text(f'<coverage line-rate="{line_rate}" />\n')


def test_build_badge_uses_half_up_percentage_rounding(tmp_path: Path) -> None:
    coverage_xml_path = tmp_path / "coverage.xml"
    write_coverage_xml(coverage_xml_path, "0.795")

    badge = build_badge(coverage_xml_path)

    assert badge["message"] == "80%"
    assert badge["color"] == "44cc11"


def test_check_badge_accepts_exact_generated_badge(tmp_path: Path) -> None:
    coverage_xml_path = tmp_path / "coverage.xml"
    badge_path = tmp_path / "test-coverage.json"
    write_coverage_xml(coverage_xml_path, "0.7992")
    badge = build_badge(coverage_xml_path)
    _ = badge_path.write_text(render_badge(badge))

    assert check_badge(coverage_xml_path, badge_path)


def test_check_badge_rejects_stale_badge(tmp_path: Path) -> None:
    coverage_xml_path = tmp_path / "coverage.xml"
    badge_path = tmp_path / "test-coverage.json"
    write_coverage_xml(coverage_xml_path, "0.7992")
    _ = badge_path.write_text('{"message": "82%"}\n')

    assert not check_badge(coverage_xml_path, badge_path)


@pytest.mark.parametrize(
    ("line_rate", "stored_percent", "expected_exit"),
    [
        ("0.9349", 94, 0),  # Linux container, Python 3.12.12
        ("0.9351", 93, 0),  # GitHub runner, Python 3.12.16
        ("0.9349", 93, 0),
        ("0.9351", 94, 0),
        ("0.9344", 94, 1),
        ("0.9356", 93, 1),
        ("0.9249", 94, 1),
        ("0.9451", 93, 1),
    ],
)
def test_cli_badge_check_allows_only_small_rounding_boundary_variation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    line_rate: str,
    stored_percent: int,
    expected_exit: int,
) -> None:
    coverage_path = tmp_path / "coverage.xml"
    badge_path = tmp_path / "test-coverage.json"
    write_coverage_xml(coverage_path, line_rate)
    badge_path.write_text(
        '{\n  "schemaVersion": 1,\n  "label": "Unit test coverage",\n'
        f'  "message": "{stored_percent}%",\n'
        '  "color": "44cc11"\n}\n'
    )
    monkeypatch.setattr(badge_script, "COVERAGE_XML_PATH", coverage_path)
    monkeypatch.setattr(badge_script, "BADGE_PATH", badge_path)
    monkeypatch.setattr("sys.argv", ["test_coverage_badge.py"])

    assert badge_script.main() == expected_exit
