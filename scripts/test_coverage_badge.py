import argparse
import difflib
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TypedDict
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
COVERAGE_XML_PATH = ROOT / "coverage.xml"
BADGE_PATH = ROOT / "test-coverage.json"


class CoverageBadge(TypedDict):
    schemaVersion: int
    label: str
    message: str
    color: str


class Arguments(argparse.Namespace):
    write: bool = False
    reference_python: str = ""


def badge_color(pct: int) -> str:
    if pct >= 80:
        return "44cc11"
    if pct >= 60:
        return "dfb317"
    if pct >= 40:
        return "fe7d37"
    return "e05d44"


def build_badge(coverage_xml_path: Path) -> CoverageBadge:
    root = ElementTree.parse(coverage_xml_path).getroot()
    line_rate = Decimal(root.attrib["line-rate"])
    pct = int((line_rate * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return {
        "schemaVersion": 1,
        "label": "Unit test coverage",
        "message": f"{pct}%",
        "color": badge_color(pct),
    }


def render_badge(badge: CoverageBadge) -> str:
    return json.dumps(badge, indent=2) + "\n"


def check_badge(badge: CoverageBadge, badge_path: Path) -> bool:
    expected = render_badge(badge)
    actual = badge_path.read_text() if badge_path.exists() else ""
    if actual == expected:
        print(f"{badge_path.name} matches coverage.xml ({badge['message']}).")
        return True

    print(
        f"{badge_path.name} is stale. Run "
        "`uv run python scripts/test_coverage_badge.py --write` after "
        "reviewing the coverage result."
    )
    print(
        "".join(
            difflib.unified_diff(
                actual.splitlines(keepends=True),
                expected.splitlines(keepends=True),
                fromfile=str(badge_path),
                tofile="expected from coverage.xml",
            )
        ),
        end="",
    )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or deliberately update the unit-test coverage badge."
    )
    _ = parser.add_argument(
        "--write",
        action="store_true",
        help="write test-coverage.json instead of checking it",
    )
    _ = parser.add_argument(
        "--reference-python",
        default="",
        metavar="X.Y",
        help=(
            "only check the badge on this Python minor version; coverage differs "
            "slightly between interpreters, so one version owns the badge"
        ),
    )
    args = Arguments()
    _ = parser.parse_args(namespace=args)
    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if args.reference_python and not args.write and running != args.reference_python:
        print(
            f"Skipping badge check on Python {running}; "
            f"the badge is owned by Python {args.reference_python}."
        )
        return 0
    badge = build_badge(COVERAGE_XML_PATH)

    if args.write:
        _ = BADGE_PATH.write_text(render_badge(badge))
        print(f"Updated {BADGE_PATH.name} to {badge['message']}.")
        return 0

    return 0 if check_badge(badge, BADGE_PATH) else 1


if __name__ == "__main__":
    raise SystemExit(main())
