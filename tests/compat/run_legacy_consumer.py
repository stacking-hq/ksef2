"""Run the legacy consumer application against the installed ksef2 distribution.

Invoke it with an interpreter that has only the candidate wheel installed, from
a working directory outside the repository, so the source tree cannot shadow
the distribution under test::

    python -I tests/compat/run_legacy_consumer.py
"""

import importlib
import importlib.util
import site
import subprocess
import sys
import sysconfig
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REMOVAL_FLOOR = "no earlier than ksef2 2.0.0"
LEGACY_APP = "legacy_app"

# Fragments an application written for ksef2 0.x sees in a DeprecationWarning.
# Every fragment has to fire, and every warning the SDK emits has to name a
# replacement and the removal floor.
EXPECTED_DEPRECATIONS: tuple[str, ...] = (
    "`ksef2.core` and its submodules are deprecated",
    "`ksef2.domain` and its submodules are deprecated",
    "`ksef2.infra` and its submodules are deprecated",
    "`ksef2.services` and its submodules are deprecated",
    "`ksef2.clients` submodules are deprecated",
    "`ksef2.models.OnlineSessionState` is deprecated",
    "`ksef2.models.BatchSessionState` is deprecated",
    "`ksef2.clients.InvoicesClient` is deprecated",
    "`dump_state()` is deprecated",
    "`model_dump_sensitive()` is deprecated",
    "`model_dump_sensitive_json()` is deprecated",
    "`from_state()` is deprecated",
    "`Client.authenticated()` is deprecated",
    "The `auth_timeout` profile key is deprecated",
)

sys.path.insert(0, str(HERE))


def _check_environment() -> None:
    """Prove this interpreter runs an installed distribution, not the checkout."""
    import ksef2

    location = getattr(ksef2, "__file__", None)
    if not isinstance(location, str):
        raise RuntimeError("ksef2 has no __file__ to identify it")
    module_file = Path(location).resolve()
    if (ROOT / "src").resolve() in module_file.parents:
        raise RuntimeError(f"ksef2 loaded from the source tree at {module_file}")
    search_dirs = [
        Path(sysconfig.get_paths()["purelib"]),
        *(Path(entry) for entry in site.getsitepackages()),
    ]
    if not any(directory.resolve() in module_file.parents for directory in search_dirs):
        raise RuntimeError(f"ksef2 loaded outside site-packages at {module_file}")
    if importlib.util.find_spec("ksef2._core") is None:
        raise RuntimeError(
            f"ksef2._core is not importable, so {module_file} is not the candidate build"
        )
    cwd = Path.cwd().resolve()
    if cwd == ROOT or ROOT in cwd.parents:
        raise RuntimeError(f"working directory {cwd} is inside the repository")


def _is_sdk_warning(warning: warnings.WarningMessage) -> bool:
    """Attribute a warning to the SDK even when its wording was tampered with."""
    module = getattr(warning, "module", None)
    if isinstance(module, str) and (module == "ksef2" or module.startswith("ksef2.")):
        return True
    message = str(warning.message)
    return "deprecated" in message.lower() and "ksef2" in message


def _sdk_deprecations(caught: list[warnings.WarningMessage]) -> list[str]:
    return [
        str(warning.message)
        for warning in caught
        if issubclass(warning.category, DeprecationWarning) and _is_sdk_warning(warning)
    ]


def _check_messages(messages: list[str]) -> list[str]:
    problems: list[str] = []
    if not messages:
        problems.append("the legacy application triggered no deprecation warning")
    for fragment in EXPECTED_DEPRECATIONS:
        if not any(fragment in message for message in messages):
            problems.append(f"expected deprecation never fired: {fragment}")
    for message in messages:
        if REMOVAL_FLOOR not in message:
            problems.append(
                f"warning does not permit removal {REMOVAL_FLOOR}: {message}"
            )
        lowered = message.lower()
        if "instead" not in lowered or "use" not in lowered:
            problems.append(f"warning does not name a replacement: {message}")
    return problems


def _check_modern_imports() -> list[str]:
    """Import the modern surface in a fresh interpreter with the same wheel."""
    result = subprocess.run(
        [sys.executable, "-I", str(HERE / "modern_imports_check.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return []
    output = (result.stdout + result.stderr).strip()
    return [f"modern import check failed:\n{output}"]


def main() -> int:
    """Run the legacy application and the modern import check."""
    try:
        _check_environment()
    except RuntimeError as error:
        print(f"FAIL {error}")
        return 1

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        application = importlib.import_module(LEGACY_APP)
        application.run()

    problems = _check_messages(_sdk_deprecations(list(caught)))
    if "weasyprint" in sys.modules:
        problems.append("the legacy application imported weasyprint")
    problems.extend(_check_modern_imports())

    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1

    messages = _sdk_deprecations(list(caught))
    print(
        f"legacy consumer gate passed: {len(EXPECTED_DEPRECATIONS)} expected deprecations "
        f"fired among {len(messages)} SDK deprecation warnings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
