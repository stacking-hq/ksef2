"""Extract the API version from openapi.json and sync documented version text."""

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict, cast

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "openapi.json"
OUTPUT_PATH = ROOT / "src" / "ksef2" / "__openapi_version__.py"

MARKER = "**Wersja API:** "

README_LINES: dict[Path, tuple[str, str]] = {
    ROOT / "README.md": (
        "The SDK currently targets KSeF OpenAPI version ",
        "The SDK currently targets KSeF OpenAPI version `{version}`.",
    ),
    ROOT / "README.pl.md": (
        "SDK obecnie celuje w wersję OpenAPI KSeF ",
        "SDK obecnie celuje w wersję OpenAPI KSeF `{version}`.",
    ),
}


class OpenApiInfo(TypedDict):
    description: str


class OpenApiSpec(TypedDict):
    info: OpenApiInfo


def load_openapi_spec() -> OpenApiSpec:
    data = cast(object, json.loads(OPENAPI_PATH.read_text()))
    if not isinstance(data, Mapping):
        raise ValueError(f"{OPENAPI_PATH.relative_to(ROOT)} must contain a JSON object")

    spec_data = cast(Mapping[str, object], data)
    info = spec_data.get("info")
    if not isinstance(info, Mapping):
        raise ValueError(f"{OPENAPI_PATH.relative_to(ROOT)} is missing info object")

    info_data = cast(Mapping[str, object], info)
    description = info_data.get("description")
    if not isinstance(description, str):
        raise ValueError(
            f"{OPENAPI_PATH.relative_to(ROOT)} is missing info.description"
        )

    return {"info": {"description": description}}


def extract_ksef_api_version(spec: OpenApiSpec) -> str:
    description = spec["info"]["description"]
    start = description.index(MARKER) + len(MARKER)
    end = description.index(" ", start)
    return description[start:end]


def replace_readme_line(path: Path, prefix: str, replacement: str) -> None:
    lines = path.read_text().splitlines()

    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            _ = path.write_text("\n".join(lines) + "\n")
            return

    raise ValueError(f"{path.relative_to(ROOT)} is missing OpenAPI version line")


def read_synced_version() -> str:
    namespace: dict[str, str] = {}
    exec(OUTPUT_PATH.read_text(), namespace)
    return namespace["version"]


def read_readme_version_line(path: Path, prefix: str) -> str:
    for line in path.read_text().splitlines():
        if line.startswith(prefix):
            return line
    raise ValueError(f"{path.relative_to(ROOT)} is missing OpenAPI version line")


def check_synced(version: str) -> list[str]:
    errors: list[str] = []

    actual_module_version = read_synced_version()
    if actual_module_version != version:
        errors.append(
            f"{OUTPUT_PATH.relative_to(ROOT)} has {actual_module_version!r}, "
            f"expected {version!r}"
        )

    for path, (prefix, template) in README_LINES.items():
        expected_line = template.format(version=version)
        actual_line = read_readme_version_line(path, prefix)
        if actual_line != expected_line:
            errors.append(
                f"{path.relative_to(ROOT)} has {actual_line!r}, "
                f"expected {expected_line!r}"
            )

    return errors


def parse_check_flag(argv: Sequence[str]) -> bool:
    usage = "usage: sync_ksef_api_version.py [--check]"
    match list(argv):
        case []:
            return False
        case ["--check"]:
            return True
        case ["-h"] | ["--help"]:
            print(usage)
            print(
                "  --check  fail if documented KSeF OpenAPI version differs from openapi.json"
            )
            raise SystemExit(0)
        case _:
            print(usage, file=sys.stderr)
            raise SystemExit(2)


def main(argv: Sequence[str] | None = None) -> int:
    check = parse_check_flag(sys.argv[1:] if argv is None else argv)

    spec = load_openapi_spec()
    version = extract_ksef_api_version(spec)

    if check:
        errors = check_synced(version)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        return 0

    _ = OUTPUT_PATH.write_text(f'version = "{version}"\n')

    for path, (prefix, template) in README_LINES.items():
        replace_readme_line(path, prefix, template.format(version=version))

    print(f'Set KSeF API version = "{version}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
