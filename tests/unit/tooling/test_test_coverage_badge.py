from pathlib import Path

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

    assert check_badge(badge, badge_path)


def test_check_badge_rejects_stale_badge(tmp_path: Path) -> None:
    coverage_xml_path = tmp_path / "coverage.xml"
    badge_path = tmp_path / "test-coverage.json"
    write_coverage_xml(coverage_xml_path, "0.7992")
    _ = badge_path.write_text('{"message": "82%"}\n')

    assert not check_badge(build_badge(coverage_xml_path), badge_path)
