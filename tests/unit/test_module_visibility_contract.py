"""Enforce the namespace rule: no underscore means public, underscore means private."""

from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
PACKAGE_ROOT = SRC_ROOT / "ksef2"

# Every importable module whose path has no underscore-prefixed component.
# Adding a name here is a public API decision; see docs/en/reference/public-api.md.
PUBLIC_MODULES = frozenset(
    {
        "ksef2",
        "ksef2.clients",
        "ksef2.fa3",
        "ksef2.models",
        "ksef2.profiles",
        "ksef2.raw",
        "ksef2.raw.mappers",
        "ksef2.raw.mappers.auth",
        "ksef2.renderers",
        "ksef2.testdata",
        "ksef2.xades",
    }
)


def _is_dunder(part: str) -> bool:
    return part.startswith("__") and part.endswith("__")


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(SRC_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _all_modules() -> set[str]:
    return {_module_name(path) for path in PACKAGE_ROOT.rglob("*.py")}


def _is_private(module: str) -> bool:
    return any(
        part.startswith("_") and not _is_dunder(part) for part in module.split(".")
    )


def _is_dunder_module(module: str) -> bool:
    return _is_dunder(module.rsplit(".", 1)[-1]) and module != "ksef2"


def test_every_module_without_an_underscore_component_is_listed_as_public() -> None:
    unlisted = sorted(
        module
        for module in _all_modules()
        if not _is_private(module)
        and not _is_dunder_module(module)
        and module not in PUBLIC_MODULES
    )

    assert not unlisted, (
        "Modules without an underscore-prefixed component are public. Rename "
        "them with a leading underscore or add them to PUBLIC_MODULES: "
        f"{', '.join(unlisted)}"
    )


def test_every_listed_public_module_exists() -> None:
    missing = sorted(PUBLIC_MODULES - _all_modules())

    assert not missing, f"PUBLIC_MODULES lists modules that do not exist: {missing}"


def test_no_internal_package_is_importable_without_an_underscore() -> None:
    old_internal = {
        "ksef2.core",
        "ksef2.domain",
        "ksef2.infra",
        "ksef2.endpoints",
        "ksef2.services",
        "ksef2.config",
        "ksef2.logging",
        "ksef2.clients.base",
        "ksef2.raw.facade",
    }

    assert not old_internal & _all_modules()
