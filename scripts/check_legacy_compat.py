"""Gate the public surface of published ksef2 releases against a built wheel.

Run ``python scripts/check_legacy_compat.py run`` (the default) from the
repository. The driver builds nothing itself: it takes a wheel, creates
throwaway environments with ``uv``, and runs each check in one of them with
``python -I`` from a working directory outside the repository, so neither the
source tree nor the project virtualenv can shadow the distribution under test.

Modes:
    run       create one environment per baseline release plus one for the
              candidate wheel, then run snapshot, verify, the consumer gate
              and the wheel-based typecheck.
    snapshot  run inside an environment holding only ``ksef2==<baseline>`` and
              record the public surface that later releases must preserve.
    verify    run inside an environment holding only the candidate wheel and
              report every recorded surface item that disappeared.
"""

import argparse
from collections.abc import Callable
import importlib
import importlib.metadata
import importlib.resources
import importlib.util
import json
import os
import pkgutil
import shutil
import site
import subprocess
import sys
import sysconfig
import tempfile
import tomllib
import types
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parent.parent
COMPAT_DIR = ROOT / "tests" / "compat"
PACKAGE_NAME = "ksef2"

# Published releases whose public surface must keep working in every later 1.x
# release. Append each 1.x version (e.g. "1.0.0") here once it is published on
# PyPI. Entries are never dropped while 1.x is supported: each one is the
# evidence that applications written against that release still import what
# they used to import and still call what they used to call.
BASELINE_VERSIONS: tuple[str, ...] = ("0.22.2", "1.0.0", "1.1.0", "1.2.0")

# Present since the #184 rename, including published 1.x releases. Pre-1.0
# baselines must lack it; both 1.x baselines and the candidate must expose it.
CANDIDATE_MARKER = "ksef2._core"
LEGACY_FAMILIES = ("core", "domain", "infra", "services")
ALLOWED_ENTRY_KINDS = frozenset({"tree", "exact", "submodules"})
DEFAULT_ALLOWLIST = COMPAT_DIR / "legacy_compat_allowlist.toml"
DEFAULT_CONSUMER_RUNNER = COMPAT_DIR / "run_legacy_consumer.py"


class GateError(RuntimeError):
    """Raised when the gate cannot run, as opposed to a compatibility miss."""


@dataclass(frozen=True)
class _Surface:
    """The public surface of one published baseline release."""

    baseline: str
    python: str
    modules: dict[str, list[str]]
    broken_modules: dict[str, str]
    classes: dict[str, str]
    class_attributes: dict[str, list[str]]
    data_files: dict[str, list[str]]

    def to_json(self) -> str:
        return json.dumps(
            {
                "baseline": self.baseline,
                "python": self.python,
                "modules": self.modules,
                "broken_modules": self.broken_modules,
                "classes": self.classes,
                "class_attributes": self.class_attributes,
                "data_files": self.data_files,
            },
            separators=(",", ":"),
            sort_keys=True,
        )


def _is_private_part(part: str) -> bool:
    return part.startswith("_") and not (part.startswith("__") and part.endswith("__"))


def _is_private_module(module: str) -> bool:
    return any(_is_private_part(part) for part in module.split("."))


def _is_ksef2_origin(value: object) -> bool:
    origin = getattr(value, "__module__", None)
    return isinstance(origin, str) and (
        origin == PACKAGE_NAME or origin.startswith(f"{PACKAGE_NAME}.")
    )


def _discover_modules(package: types.ModuleType) -> tuple[list[str], dict[str, str]]:
    """Return every public-path module name plus the packages that failed to import."""
    names = [package.__name__]
    broken: dict[str, str] = {}
    pending = [package]
    while pending:
        parent = pending.pop()
        raw_path = getattr(parent, "__path__", None)
        if raw_path is None:
            continue
        paths = cast("list[str]", raw_path)
        for info in pkgutil.iter_modules(paths, f"{parent.__name__}."):
            if _is_private_module(info.name):
                continue
            names.append(info.name)
            if not info.ispkg:
                continue
            try:
                pending.append(importlib.import_module(info.name))
            except BaseException as exc:  # noqa: BLE001 - recorded, then excluded
                broken[info.name] = f"{type(exc).__name__}: {exc}"
    return sorted(names), broken


def _public_names(module: types.ModuleType) -> list[str]:
    declared = getattr(module, "__all__", None)
    if declared is not None:
        return sorted({str(name) for name in cast("list[object]", declared)})
    names: list[str] = []
    namespace = cast("dict[str, object]", vars(module))
    for key, value in namespace.items():
        if key.startswith("_"):
            continue
        if isinstance(value, types.ModuleType):
            # A re-exported submodule is surface only when it belongs to ksef2.
            if (value.__name__ or "").startswith(f"{PACKAGE_NAME}."):
                names.append(key)
            continue
        # Anything defined outside ksef2 is an incidental import, not surface.
        if _is_ksef2_origin(value):
            names.append(key)
    return sorted(names)


def _attributes_of(kind: type[object]) -> list[str]:
    attributes = {name for name in dir(kind) if not name.startswith("_")}
    fields = getattr(kind, "model_fields", None)
    if isinstance(fields, dict):
        attributes |= {str(name) for name in cast("dict[str, object]", fields)}
    return sorted(attributes)


def _data_files(module: types.ModuleType) -> list[str]:
    """List the packaged data a package owns directly, which a wheel can drop.

    Files inside a nested package belong to that package's own listing, so each
    data file is recorded once, under the resource path an application would
    use: ``importlib.resources.files(<package>).joinpath(<relative path>)``.
    """
    raw_paths = getattr(module, "__path__", None)
    if raw_paths is None:
        return []
    found: set[str] = set()
    for entry in cast("list[str]", raw_paths):
        root = Path(entry)
        if not root.is_dir():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file() or candidate.suffix in {".py", ".pyc"}:
                continue
            if "__pycache__" in candidate.parts:
                continue
            relative = candidate.relative_to(root)
            nested = (
                (root / parent / "__init__.py").is_file()
                for parent in relative.parents
                if parent != Path(".")
            )
            if any(nested):
                continue
            found.add(relative.as_posix())
    return sorted(found)


def _site_dirs() -> list[Path]:
    dirs = [Path(sysconfig.get_paths()["purelib"])]
    dirs.extend(Path(entry) for entry in site.getsitepackages())
    dirs.append(Path(site.getusersitepackages()))
    return [directory.resolve() for directory in dirs]


def _assert_environment(
    *, candidate: bool, label: str, version: str | None = None
) -> Path:
    """Prove the interpreter loaded an installed distribution, not this checkout."""
    module = importlib.import_module(PACKAGE_NAME)
    location = getattr(module, "__file__", None)
    if not isinstance(location, str):
        raise GateError(f"{label}: {PACKAGE_NAME} has no __file__ to identify it")
    module_file = Path(location).resolve()

    src_root = (ROOT / "src").resolve()
    if src_root in module_file.parents:
        raise GateError(
            f"{label}: {PACKAGE_NAME} loaded from the source tree at {module_file}; "
            "run the gate against an installed distribution"
        )
    if not any(directory in module_file.parents for directory in _site_dirs()):
        raise GateError(
            f"{label}: {PACKAGE_NAME} loaded outside site-packages at {module_file}"
        )

    cwd = Path.cwd().resolve()
    if cwd == ROOT or ROOT in cwd.parents:
        raise GateError(f"{label}: working directory {cwd} is inside the repository")

    if version is not None:
        installed_version = importlib.metadata.version(PACKAGE_NAME)
        if installed_version != version:
            raise GateError(
                f"{label}: installed version {installed_version!r} does not match "
                f"published baseline {version!r}"
            )

    marker_present = importlib.util.find_spec(CANDIDATE_MARKER) is not None
    modern_package = candidate or (version is not None and not version.startswith("0."))
    if modern_package and not marker_present:
        raise GateError(
            f"{label}: {CANDIDATE_MARKER} is not importable, so {module_file} is not "
            "the expected modern distribution"
        )
    if not modern_package and marker_present:
        raise GateError(
            f"{label}: {CANDIDATE_MARKER} is importable, so {module_file} is not the "
            "published baseline distribution"
        )
    return module_file


def _snapshot(version: str) -> _Surface:
    """Record the public surface of the installed baseline distribution."""
    _ = _assert_environment(
        candidate=False, label=f"baseline {PACKAGE_NAME}=={version}", version=version
    )
    package = importlib.import_module(PACKAGE_NAME)
    module_names, broken_modules = _discover_modules(package)

    modules: dict[str, list[str]] = {}
    broken: dict[str, str] = dict(broken_modules)
    classes: dict[str, str] = {}
    class_attributes: dict[str, list[str]] = {}
    data_files: dict[str, list[str]] = {}

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except BaseException as exc:  # noqa: BLE001 - recorded, then excluded
            broken[module_name] = f"{type(exc).__name__}: {exc}"
            continue
        names = _public_names(module)
        modules[module_name] = names
        packaged = _data_files(module)
        if packaged:
            data_files[module_name] = packaged
        for name in names:
            value = getattr(module, name, None)
            if not isinstance(value, type) or not _is_ksef2_origin(value):
                continue
            # One class can be re-exported everywhere; record its attributes once.
            definition = f"{value.__module__}.{value.__qualname__}"
            classes[f"{module_name}.{name}"] = definition
            _ = class_attributes.setdefault(definition, _attributes_of(value))

    return _Surface(
        baseline=version,
        python=".".join(str(part) for part in sys.version_info[:3]),
        modules=modules,
        broken_modules=dict(sorted(broken.items())),
        classes=dict(sorted(classes.items())),
        class_attributes=dict(sorted(class_attributes.items())),
        data_files=dict(sorted(data_files.items())),
    )


def _string_list_map(value: object, label: str) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise GateError(f"snapshot field {label} must be a JSON object")
    mapping = cast("dict[str, object]", value)
    result: dict[str, list[str]] = {}
    for key, item in mapping.items():
        if not isinstance(item, list):
            raise GateError(f"snapshot field {label}.{key} must be a list of strings")
        names: list[str] = []
        for entry in cast("list[object]", item):
            if not isinstance(entry, str):
                raise GateError(
                    f"snapshot field {label}.{key} must be a list of strings"
                )
            names.append(entry)
        result[key] = names
    return result


def _string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise GateError(f"snapshot field {label} must be a JSON object")
    mapping = cast("dict[str, object]", value)
    for key, item in mapping.items():
        if not isinstance(item, str):
            raise GateError(f"snapshot field {label}.{key} must be a string")
    return cast("dict[str, str]", mapping)


def _load_snapshot(path: Path) -> _Surface:
    if not path.is_file():
        raise GateError(f"snapshot {path} does not exist")
    raw = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict):
        raise GateError(f"snapshot {path} must contain a JSON object")
    data = cast("dict[str, object]", raw)
    baseline = data.get("baseline")
    python = data.get("python")
    if not isinstance(baseline, str) or not baseline:
        raise GateError(f"snapshot {path} has no baseline version")
    for field in ("modules", "classes", "class_attributes"):
        if field not in data:
            raise GateError(f"snapshot {path} has no {field!r} field")
    return _Surface(
        baseline=baseline,
        python=python if isinstance(python, str) else "unknown",
        modules=_string_list_map(data["modules"], "modules"),
        broken_modules=_string_map(data.get("broken_modules", {}), "broken_modules"),
        classes=_string_map(data["classes"], "classes"),
        class_attributes=_string_list_map(data["class_attributes"], "class_attributes"),
        data_files=_string_list_map(data.get("data_files", {}), "data_files"),
    )


def _verify(surface: _Surface) -> list[str]:
    """Return raw compatibility misses for the installed candidate distribution."""
    _ = _assert_environment(candidate=True, label="candidate")
    with warnings.catch_warnings(record=True) as caught:
        # Deprecated names must keep resolving and resolving them warns; the
        # consumer gate is what checks the wording of those warnings.
        warnings.simplefilter("always", DeprecationWarning)
        misses = _collect_misses(surface)
    warned = {
        str(warning.message)
        for warning in caught
        if warning.category is DeprecationWarning
    }
    print(
        f"resolved the recorded surface with {len(warned)} distinct deprecation "
        "warnings, which the gate allows"
    )
    return misses


def _dotted(module: str, relative: str) -> str:
    return f"{module}.{relative.replace('/', '.')}"


def _collect_misses(surface: _Surface) -> list[str]:
    """Check every recorded module, name and class attribute against this build."""
    floor = f"(baseline {PACKAGE_NAME}=={surface.baseline})"
    misses: list[str] = []
    loaded: dict[str, types.ModuleType | None] = {}

    for module_name in sorted(surface.modules):
        try:
            imported = importlib.import_module(module_name)
        except BaseException:  # noqa: BLE001 - reported as a missing module
            loaded[module_name] = None
            misses.append(f"module {module_name} {floor}")
            continue
        loaded[module_name] = imported
        for name in surface.modules[module_name]:
            if not hasattr(imported, name):
                misses.append(f"name {module_name}.{name} {floor}")

    for module_name in sorted(surface.data_files):
        module = loaded.get(module_name)
        if module is None:
            continue  # the module miss is reported above
        anchor = importlib.resources.files(module)
        for relative in surface.data_files[module_name]:
            if not anchor.joinpath(*relative.split("/")).is_file():
                misses.append(f"data {_dotted(module_name, relative)} {floor}")

    for access_path in sorted(surface.classes):
        module_name, _, name = access_path.rpartition(".")
        module = loaded.get(module_name)
        if module is None and module_name not in loaded:
            # The module was not part of the recorded module surface itself.
            try:
                module = importlib.import_module(module_name)
            except BaseException:  # noqa: BLE001 - the module miss is reported above
                module = None
        if module is None:
            continue
        kind = getattr(module, name, None)
        if kind is None:
            continue  # already reported as a missing name
        if not isinstance(kind, type):
            misses.append(f"name {access_path} {floor} is no longer a class")
            continue
        present = set(_attributes_of(kind))
        for attribute in surface.class_attributes.get(surface.classes[access_path], []):
            if attribute not in present:
                misses.append(f"attribute {access_path}.{attribute} {floor}")
    return misses


def _check_legacy_families() -> list[str]:
    """Return the legacy families this build cannot import."""
    misses: list[str] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        for family in LEGACY_FAMILIES:
            module_name = f"{PACKAGE_NAME}.{family}"
            try:
                _ = importlib.import_module(module_name)
            except BaseException as exc:  # noqa: BLE001 - reported as a missing module
                misses.append(f"{module_name} ({type(exc).__name__}: {exc})")
    return [f"module {entry} (deprecated compatibility family)" for entry in misses]


class Allowlist:
    """Approved removals, each with the reason that justifies its absence."""

    def __init__(self, entries: list[tuple[str, str, str]]) -> None:
        self._entries = entries
        self._matched = [False] * len(entries)

    def covers(self, miss: str) -> bool:
        kind, _, rest = miss.partition(" ")
        path = rest.split(" (")[0]
        for index, (entry_kind, entry_path, _) in enumerate(self._entries):
            if entry_kind == "exact":
                match = path == entry_path
            elif entry_kind == "tree":
                match = path == entry_path or path.startswith(f"{entry_path}.")
            else:  # submodules: children only, so the parent stays protected
                match = kind == "module" and path.startswith(f"{entry_path}.")
            if match:
                self._matched[index] = True
                return True
        return False

    def stale(self) -> list[str]:
        return [
            f"{kind} {path}: {reason}"
            for index, (kind, path, reason) in enumerate(self._entries)
            if not self._matched[index]
        ]


def _load_allowlist(path: Path) -> Allowlist:
    if not path.is_file():
        return Allowlist([])
    document = cast(
        "dict[str, object]", tomllib.loads(path.read_text(encoding="utf-8"))
    )
    raw_entries = document.get("entry", [])
    if not isinstance(raw_entries, list):
        raise GateError(f"{path}: [[entry]] must be a list of tables")
    entries: list[tuple[str, str, str]] = []
    for position, raw in enumerate(cast("list[object]", raw_entries), start=1):
        if not isinstance(raw, dict):
            raise GateError(f"{path}: entry {position} must be a table")
        table = cast("dict[str, object]", raw)
        entry_path = table.get("path")
        reason = table.get("reason")
        kind = table.get("kind", "tree")
        if not isinstance(entry_path, str) or not entry_path.strip():
            raise GateError(f"{path}: entry {position} needs a non-empty path")
        if not isinstance(reason, str) or not reason.strip():
            raise GateError(
                f"{path}: entry {entry_path} needs a non-empty reason for its removal"
            )
        if kind not in ALLOWED_ENTRY_KINDS:
            raise GateError(
                f"{path}: entry {entry_path} kind must be one of "
                f"{', '.join(sorted(ALLOWED_ENTRY_KINDS))}"
            )
        entries.append((cast("str", kind), entry_path.strip(), reason.strip()))
    return Allowlist(entries)


def _print_misses(misses: list[str], allowlist: Allowlist, label: str) -> int:
    allowed = [miss for miss in misses if allowlist.covers(miss)]
    failures = [miss for miss in misses if miss not in allowed]
    for miss in failures:
        print(f"MISSING {miss}")
    stale = allowlist.stale()
    for entry in stale:
        print(f"STALE allowlist entry {entry}")
    print(
        f"{label}: {len(failures)} missing, {len(allowed)} allowlisted, "
        f"{len(stale)} stale"
    )
    return 1 if failures or stale else 0


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = cast("dict[str, object]", tomllib.load(handle))["project"]
    version = cast("dict[str, object]", project)["version"]
    if not isinstance(version, str):
        raise GateError("pyproject.toml has no string project.version")
    return version


def _resolve_wheel(explicit: str | None) -> Path:
    if explicit is not None:
        wheel = Path(explicit).resolve()
        if not wheel.is_file():
            raise GateError(f"wheel {wheel} does not exist")
        return wheel
    version = _project_version()
    wheels = sorted((ROOT / "dist").glob(f"{PACKAGE_NAME}-{version}-*.whl"))
    if not wheels:
        raise GateError(
            f"no dist/{PACKAGE_NAME}-{version}-*.whl found; run `uv build --wheel` first"
        )
    if len(wheels) > 1:
        found = ", ".join(wheel.name for wheel in wheels)
        raise GateError(f"several candidate wheels found ({found}); pass --wheel")
    return wheels[0]


def _execute(
    command: list[str], cwd: Path, label: str
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        raise GateError(f"{label} failed with exit {result.returncode}:\n{output}")
    return result


def _create_env(name: str, work: Path, requirements: list[str], python: str) -> Path:
    """Create a throwaway interpreter holding exactly the given requirements."""
    directory = work / name
    interpreter = directory / "bin" / "python"
    print(f":: env {name}: {' '.join(requirements)}", flush=True)
    _ = _execute(
        ["uv", "venv", os.fspath(directory), "--python", python], work, f"create {name}"
    )
    _ = _execute(
        [
            "uv",
            "pip",
            "install",
            "--refresh-package",
            PACKAGE_NAME,
            "--python",
            os.fspath(interpreter),
            *requirements,
        ],
        work,
        f"install into {name}",
    )
    return interpreter


def _run_gate(interpreter: Path, arguments: list[str], work: Path, label: str) -> None:
    """Re-enter this script inside an isolated interpreter, outside the checkout."""
    command = [
        os.fspath(interpreter),
        "-I",
        os.fspath(Path(__file__).resolve()),
        *arguments,
    ]
    _ = sys.stdout.flush()
    result = subprocess.run(
        command, cwd=work, capture_output=True, text=True, check=False
    )
    _ = sys.stdout.write(result.stdout)
    _ = sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise GateError(f"{label} failed with exit {result.returncode}")


def _basedpyright_command(explicit: str | None) -> list[str]:
    if explicit is not None:
        return [explicit]
    executable = shutil.which("basedpyright") or shutil.which("pyright")
    if executable is None:
        local = ROOT / ".venv" / "bin" / "basedpyright"
        if not local.is_file():
            raise GateError(
                "basedpyright is not on PATH; run `just sync` or pass --basedpyright"
            )
        executable = os.fspath(local)
    return [executable]


@dataclass(frozen=True)
class _RunOptions:
    """Where the driver takes its wheel, its interpreter and its environments."""

    wheel: str | None
    python: str | None
    allowlist: str
    consumer_runner: str
    basedpyright: str | None
    work_dir: str | None
    keep_work_dir: bool


def _run_stage(failures: list[str], label: str, action: Callable[[], object]) -> bool:
    """Run one gate stage, recording its label when it fails."""
    try:
        _ = action()
    except GateError as error:
        print(f"ERROR {error}", file=sys.stderr)
        failures.append(label)
        return False
    return True


def _typecheck_wheel(candidate: Path, executable: str | None) -> None:
    """Typecheck the consumer application against the installed wheel, not src/."""
    command = [
        *_basedpyright_command(executable),
        "--project",
        os.fspath(COMPAT_DIR),
        "--pythonpath",
        os.fspath(candidate),
        "--level",
        "error",
    ]
    _ = sys.stdout.flush()
    # Under GitHub Actions basedpyright fails on warnings too; `just typecheck`
    # clears the variable for the same reason. Runtime-only legacy aliases have
    # unknown static types, so only errors count here.
    environment = {**os.environ, "GITHUB_ACTIONS": ""}
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    _ = sys.stdout.write(result.stdout)
    _ = sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise GateError(
            f"basedpyright against the installed wheel failed with exit {result.returncode}"
        )


def _check_baseline(
    failures: list[str],
    work: Path,
    version: str,
    options: _RunOptions,
) -> Path | None:
    """Snapshot one published baseline for the combined compatibility check."""
    label = f"{PACKAGE_NAME}=={version}"
    snapshot_path = work / f"snapshot-{version}.json"

    def snapshot() -> None:
        baseline = _create_env(
            f"baseline-{version}", work, [label], options.python or sys.executable
        )
        _run_gate(
            baseline,
            ["snapshot", "--version", version, "--output", os.fspath(snapshot_path)],
            work,
            f"snapshot {label}",
        )

    if _run_stage(failures, f"snapshot {label}", snapshot):
        return snapshot_path
    return None


def _run_driver(options: _RunOptions) -> int:
    """Snapshot every baseline and check the candidate wheel against each."""
    try:
        wheel = _resolve_wheel(options.wheel)
        python = options.python or sys.executable
        keeper: tempfile.TemporaryDirectory[str] | None = None
        if options.work_dir is None:
            keeper = tempfile.TemporaryDirectory(prefix="ksef2-legacy-compat-")
            work = Path(keeper.name)
        else:
            work = Path(options.work_dir)
            work.mkdir(parents=True, exist_ok=True)
    except GateError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1

    failures: list[str] = []
    try:
        candidate = _create_env("candidate", work, [os.fspath(wheel)], python)
        snapshot_paths: list[str] = []
        for version in BASELINE_VERSIONS:
            snapshot_path = _check_baseline(failures, work, version, options)
            if snapshot_path is not None:
                snapshot_paths.append(os.fspath(snapshot_path))
        if snapshot_paths:
            # Allowlist entries must justify a miss in at least one baseline.
            # Checking them separately falsely marks pre-1.0 removals as stale
            # against 1.x, where those paths were never published.
            _ = _run_stage(
                failures,
                "verify baselines",
                lambda: _run_gate(
                    candidate,
                    [
                        "verify",
                        "--snapshot",
                        *snapshot_paths,
                        "--allowlist",
                        options.allowlist,
                    ],
                    work,
                    "verify baselines",
                ),
            )
        _ = _run_stage(
            failures,
            "consumer smoke test",
            lambda: print(
                _execute(
                    [os.fspath(candidate), "-I", options.consumer_runner],
                    work,
                    "consumer smoke test",
                ).stdout.strip()
            ),
        )
        _ = _run_stage(
            failures,
            "wheel typecheck",
            lambda: _typecheck_wheel(candidate, options.basedpyright),
        )
    except GateError as error:
        failures.append(f"environment setup: {error}")

    finally:
        if keeper is not None and not options.keep_work_dir:
            shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(
            f"legacy compatibility gate failed: {', '.join(failures)}", file=sys.stderr
        )
        return 1
    print(f"legacy compatibility gate passed for {wheel.name}")
    print(f"baselines checked: {', '.join(BASELINE_VERSIONS)}")
    print(f"work directory: {work}")
    return 0


def _text(args: argparse.Namespace, name: str) -> str:
    value = cast("object", getattr(args, name))
    return value if isinstance(value, str) else ""


def _optional_text(args: argparse.Namespace, name: str) -> str | None:
    value = cast("object", getattr(args, name))
    return value if isinstance(value, str) and value else None


def _flag(args: argparse.Namespace, name: str) -> bool:
    return cast("object", getattr(args, name)) is True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode")

    run = modes.add_parser("run", help="snapshot every baseline and verify the wheel")
    _ = run.add_argument(
        "--wheel", help="candidate wheel; defaults to the project wheel in dist/"
    )
    _ = run.add_argument(
        "--python", help="interpreter used as the base of the throwaway environments"
    )
    _ = run.add_argument("--allowlist", default=os.fspath(DEFAULT_ALLOWLIST))
    _ = run.add_argument(
        "--consumer-runner", default=os.fspath(DEFAULT_CONSUMER_RUNNER)
    )
    _ = run.add_argument(
        "--basedpyright", help="basedpyright executable used for the wheel typecheck"
    )
    _ = run.add_argument("--work-dir", help="create throwaway environments here")
    _ = run.add_argument(
        "--keep-work-dir", action="store_true", help="do not delete the work directory"
    )

    snapshot = modes.add_parser(
        "snapshot", help="record the installed baseline distribution"
    )
    _ = snapshot.add_argument(
        "--version", required=True, help="baseline version being recorded"
    )
    _ = snapshot.add_argument("--output", required=True, help="JSON file to write")

    verify = modes.add_parser(
        "verify", help="check the installed candidate against a snapshot"
    )
    _ = verify.add_argument(
        "--snapshot", required=True, nargs="+", help="JSON snapshots to check together"
    )
    _ = verify.add_argument("--allowlist", default=os.fspath(DEFAULT_ALLOWLIST))
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one gate mode and return the process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in ("snapshot", "verify"):
        arguments.insert(0, "run")
    args = _parser().parse_args(arguments)
    mode = _text(args, "mode")

    try:
        if mode == "snapshot":
            version = _text(args, "version")
            surface = _snapshot(version)
            output = Path(_text(args, "output"))
            output.parent.mkdir(parents=True, exist_ok=True)
            _ = output.write_text(surface.to_json(), encoding="utf-8")
            print(
                f"snapshot {PACKAGE_NAME}=={version} on python {surface.python}: "
                f"{len(surface.modules)} modules, {len(surface.classes)} class paths, "
                f"{len(surface.broken_modules)} unimportable"
            )
            return 0

        if mode == "verify":
            allowlist_path = Path(_text(args, "allowlist"))
            misses: list[str] = []
            stable_misses: list[str] = []
            for snapshot_path in cast(list[str], args.snapshot):
                surface = _load_snapshot(Path(snapshot_path))
                if surface.baseline.startswith("0."):
                    misses.extend(_verify(surface))
                else:
                    # Pre-1.0 removal approvals cannot waive the 1.x contract.
                    stable_misses.extend(_verify(surface))
            if "weasyprint" in sys.modules:
                misses.append(
                    "module weasyprint.eager_import (optional dependency must stay lazy)"
                )
            misses.extend(_check_legacy_families())
            legacy_result = _print_misses(
                misses, _load_allowlist(allowlist_path), "verify legacy"
            )
            stable_result = _print_misses(stable_misses, Allowlist([]), "verify 1.x")
            return max(legacy_result, stable_result)

        return _run_driver(
            _RunOptions(
                wheel=_optional_text(args, "wheel"),
                python=_optional_text(args, "python"),
                allowlist=_text(args, "allowlist"),
                consumer_runner=_text(args, "consumer_runner"),
                basedpyright=_optional_text(args, "basedpyright"),
                work_dir=_optional_text(args, "work_dir"),
                keep_work_dir=_flag(args, "keep_work_dir"),
            )
        )
    except GateError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
