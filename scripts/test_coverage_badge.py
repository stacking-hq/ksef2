import json
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
COVERAGE_XML_PATH = ROOT / "coverage.xml"
BADGE_PATH = ROOT / "test-coverage.json"


def badge_color(pct: int) -> str:
    if pct >= 80:
        return "44cc11"
    if pct >= 60:
        return "dfb317"
    if pct >= 40:
        return "fe7d37"
    return "e05d44"


def main() -> None:
    root = ElementTree.parse(COVERAGE_XML_PATH).getroot()
    line_rate = float(root.attrib["line-rate"])
    pct = round(line_rate * 100)

    badge = {
        "schemaVersion": 1,
        "label": "Unit test coverage",
        "message": f"{pct}%",
        "color": badge_color(pct),
    }

    with open(BADGE_PATH, "w") as f:
        json.dump(badge, f, indent=2)
        f.write("\n")

    print(json.dumps(badge, indent=2))


if __name__ == "__main__":
    main()
