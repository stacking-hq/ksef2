"""Modern imports must stay silent and must not activate compatibility aliases."""

import importlib
import sys
import warnings

MODERN_MODULES = (
    "ksef2",
    "ksef2.clients",
    "ksef2.models",
    "ksef2.fa3",
    "ksef2.raw",
    "ksef2.renderers",
    "ksef2.xades",
    "ksef2.profiles",
    "ksef2.testdata",
)
LEGACY_FAMILIES = ("core", "domain", "infra", "services")


def main() -> int:
    """Import the public modern surface and report everything it dragged along."""
    problems: list[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for name in MODERN_MODULES:
            importlib.import_module(name)
        for warning in caught:
            if not issubclass(
                warning.category, (DeprecationWarning, PendingDeprecationWarning)
            ):
                continue
            # WarningMessage records where the warning points, not who raised it;
            # the SDK's deprecations always name ksef2 in their text.
            if "ksef2" not in str(warning.message):
                continue
            problems.append(
                f"{warning.filename}:{warning.lineno} warned at import time: "
                f"{warning.message}"
            )

    for family in LEGACY_FAMILIES:
        module = f"ksef2.{family}"
        if module in sys.modules:
            problems.append(f"{module} was activated by a modern import")
    if any(name.startswith("ksef2.clients.") for name in sys.modules):
        problems.append("a deprecated ksef2.clients submodule was activated")
    if "ksef2._legacy_imports" in sys.modules:
        problems.append("ksef2._legacy_imports was activated by a modern import")
    if "weasyprint" in sys.modules:
        problems.append(
            "weasyprint was imported; the optional PDF extra must stay lazy"
        )

    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    print(
        f"modern imports are silent: {len(MODERN_MODULES)} modules, no compat aliases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
