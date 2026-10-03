"""Regenerate or verify schema-derived source and packaged definition files.

``schemas/FA3`` owns the shared XSD and XML definitions. The packaged XSL files
are runtime-only assets and are intentionally left untouched.
"""

import argparse
import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, cast


ROOT = Path(__file__).resolve().parent.parent

OPENAPI_SOURCE = ROOT / "openapi.json"
OPENAPI_TARGET = (
    ROOT / "src" / "ksef2" / "_infra" / "schema" / "api" / "spec" / "models.py"
)

FA3_SOURCE = ROOT / "schemas" / "FA3"
FA3_MODELS_TARGET = ROOT / "src" / "ksef2" / "_infra" / "schema" / "fa3" / "models"
FA3_DEFINITIONS_TARGET = (
    ROOT / "src" / "ksef2" / "_infra" / "schema" / "fa3" / "definitions"
)

# xsdata snake-cases every package segment and drops the leading underscore of
# ``_infra``. The generated modules use relative imports and carry no package
# name, so they are generated under this neutral package and copied into
# ``FA3_MODELS_TARGET``.
FA3_GENERATION_PACKAGE = "ksef2.infra.schema.fa3.models"

PYRIGHT_META_IGNORE = "  # pyright: ignore[reportIncompatibleVariableOverride]"


def run(command: list[str], *, cwd: Path | None = None) -> None:
    _ = subprocess.run(command, cwd=cwd, check=True)


def format_python(path: Path) -> None:
    ruff = Path(sys.executable).with_name("ruff")
    if not ruff.is_file():
        ruff_from_path = shutil.which("ruff")
        if ruff_from_path is not None:
            ruff = Path(ruff_from_path)
    if not ruff.is_file():
        raise RuntimeError("ruff is required to format generated models")
    run([str(ruff), "format", str(path)])


def generate_openapi_models(output: Path) -> None:
    run(
        [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(OPENAPI_SOURCE),
            "--input-file-type",
            "openapi",
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--use-annotated",
            "--field-constraints",
            "--use-standard-collections",
            "--use-union-operator",
            "--strict-nullable",
            "--collapse-root-models",
            "--use-schema-description",
            "--use-field-description",
            "--disable-timestamp",
            "--target-python-version",
            "3.12",
            "--formatters",
            "black",
            "isort",
            "--output",
            str(output),
        ]
    )
    format_python(output)


def add_generated_pyright_ignores(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()

    meta_line_numbers: list[int] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or not node.bases:
            continue
        for child in node.body:
            if isinstance(child, ast.ClassDef) and child.name == "Meta":
                meta_line_numbers.append(child.lineno)

    for line_number in meta_line_numbers:
        line_index = line_number - 1
        if not lines[line_index].endswith("class Meta:"):
            raise RuntimeError(
                f"Unexpected generated Meta declaration at {path}:{line_number}"
            )
        lines[line_index] += PYRIGHT_META_IGNORE

    _ = path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def generate_fa3_models(output_root: Path) -> Path:
    output_root.mkdir(parents=True)
    run(
        [
            sys.executable,
            "-m",
            "xsdata",
            "generate",
            str(FA3_SOURCE / "schemat.xsd"),
            "--output",
            "dataclasses",
            "--unnest-classes",
            "--relative-imports",
            "--package",
            FA3_GENERATION_PACKAGE,
            "--structure-style",
            "filenames",
            "--docstring-style",
            "Google",
        ],
        cwd=output_root,
    )
    generated_models = output_root.joinpath(*FA3_GENERATION_PACKAGE.split("."))
    _ = (generated_models / "__init__.py").write_text(
        '"""Generated FA(3) schema models package."""\n',
        encoding="utf-8",
        newline="\n",
    )
    for path in generated_models.glob("*.py"):
        if path.name == "__init__.py":
            continue
        add_generated_pyright_ignores(path)
        format_python(path)
    return generated_models


def files_match(expected: Path, actual: Path) -> bool:
    return actual.is_file() and expected.read_bytes() == actual.read_bytes()


def sync_file(expected: Path, actual: Path, *, check: bool) -> bool:
    if files_match(expected, actual):
        return True
    if check:
        print(f"stale generated artifact: {actual.relative_to(ROOT)}")
        return False
    actual.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copyfile(expected, actual)
    print(f"updated generated artifact: {actual.relative_to(ROOT)}")
    return True


def sync_openapi(*, check: bool, temporary_root: Path) -> bool:
    generated = temporary_root / "openapi_models.py"
    generate_openapi_models(generated)
    return sync_file(generated, OPENAPI_TARGET, check=check)


def sync_fa3(*, check: bool, temporary_root: Path) -> bool:
    generated_models = generate_fa3_models(temporary_root / "fa3")
    expected_model_names = {path.name for path in generated_models.glob("*.py")}
    actual_model_names = {path.name for path in FA3_MODELS_TARGET.glob("*.py")}

    matches = True
    for name in sorted(expected_model_names):
        if not sync_file(
            generated_models / name, FA3_MODELS_TARGET / name, check=check
        ):
            matches = False

    for name in sorted(actual_model_names - expected_model_names):
        path = FA3_MODELS_TARGET / name
        if check:
            print(f"unexpected generated artifact: {path.relative_to(ROOT)}")
            matches = False
        else:
            path.unlink()
            print(f"removed generated artifact: {path.relative_to(ROOT)}")

    expected_definition_names = {
        path.name
        for path in FA3_SOURCE.iterdir()
        if path.is_file() and path.suffix in {".xml", ".xsd"}
    }
    actual_definition_names = {
        path.name
        for path in FA3_DEFINITIONS_TARGET.glob("*")
        if path.is_file() and path.suffix in {".xml", ".xsd"}
    }

    for name in sorted(expected_definition_names):
        if not sync_file(FA3_SOURCE / name, FA3_DEFINITIONS_TARGET / name, check=check):
            matches = False

    for name in sorted(actual_definition_names - expected_definition_names):
        path = FA3_DEFINITIONS_TARGET / name
        if check:
            print(f"unexpected generated artifact: {path.relative_to(ROOT)}")
            matches = False
        else:
            path.unlink()
            print(f"removed generated artifact: {path.relative_to(ROOT)}")

    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate or verify OpenAPI and FA(3) schema artifacts."
    )
    _ = parser.add_argument(
        "--check",
        action="store_true",
        help="fail if checked-in artifacts differ without modifying the repository",
    )
    _ = parser.add_argument(
        "--only",
        choices=("openapi", "fa3"),
        help="limit generation to one schema family",
    )
    args = parser.parse_args()
    check = cast(bool, args.check)
    only = cast(Literal["openapi", "fa3"] | None, args.only)

    with tempfile.TemporaryDirectory(prefix="ksef2-generated-artifacts-") as temp_dir:
        temporary_root = Path(temp_dir)
        matches = True
        if only in {None, "openapi"}:
            matches = (
                sync_openapi(check=check, temporary_root=temporary_root) and matches
            )
        if only in {None, "fa3"}:
            matches = sync_fa3(check=check, temporary_root=temporary_root) and matches

    if check and not matches:
        print("Run `just regenerate-artifacts` and commit the resulting changes.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
