"""Extract the API version from openapi.json and sync documented version text."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "openapi.json"
OUTPUT_PATH = ROOT / "src" / "ksef2" / "__openapi_version__.py"

MARKER = "**Wersja API:** "

README_LINES = {
    ROOT / "README.md": (
        "The SDK currently targets KSeF OpenAPI version ",
        "The SDK currently targets KSeF OpenAPI version `{version}`.",
    ),
    ROOT / "README.pl.md": (
        "SDK obecnie celuje w wersję OpenAPI KSeF ",
        "SDK obecnie celuje w wersję OpenAPI KSeF `{version}`.",
    ),
}


def extract_ksef_api_version(spec: dict[str, Any]) -> str:
    description: str = spec["info"]["description"]
    start = description.index(MARKER) + len(MARKER)
    end = description.index(" ", start)
    return description[start:end]


def replace_readme_line(path: Path, prefix: str, replacement: str) -> None:
    lines = path.read_text().splitlines()

    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            path.write_text("\n".join(lines) + "\n")
            return

    raise ValueError(f"{path.relative_to(ROOT)} is missing OpenAPI version line")


def main() -> None:
    spec = json.loads(OPENAPI_PATH.read_text())
    version = extract_ksef_api_version(spec)
    _ = OUTPUT_PATH.write_text(f'version = "{version}"\n')

    for path, (prefix, template) in README_LINES.items():
        replace_readme_line(path, prefix, template.format(version=version))

    print(f'Set KSeF API version = "{version}"')


if __name__ == "__main__":
    main()
