"""Keep renamed package trees importable throughout 1.x."""

import sys
import warnings
from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType


_warned_clients = False


def _bind_module_aliases(
    legacy: str, canonical: str, modules: list[ModuleType]
) -> None:
    """Register module aliases and bind children on their legacy parents."""
    for module in modules:
        module_name = module.__name__
        legacy_name = legacy + module_name[len(canonical) :]
        sys.modules[legacy_name] = module
        parent_name, _, child_name = legacy_name.rpartition(".")
        parent = sys.modules.get(parent_name)
        if parent is not None:
            setattr(parent, child_name, module)


def alias_package(legacy: str, canonical: str, replacement: str) -> None:
    """Load a canonical tree once, then reuse its modules under the old names."""
    warnings.warn(
        f"`{legacy}` and its submodules are deprecated; use {replacement} instead. "
        "Removal may happen no earlier than ksef2 2.0.0.",
        DeprecationWarning,
        stacklevel=3,
    )
    package = import_module(canonical)
    modules = [package]
    for entry in walk_packages(package.__path__, canonical + "."):
        modules.append(import_module(entry.name))
    _bind_module_aliases(legacy, canonical, modules)


def alias_client_modules() -> None:
    """Alias the old client submodules to the canonical implementations once."""
    global _warned_clients
    canonical = "ksef2._clients"
    legacy = "ksef2.clients"
    package = import_module(canonical)
    modules = [package]
    for entry in walk_packages(package.__path__, canonical + "."):
        modules.append(import_module(entry.name))
    _bind_module_aliases(legacy, canonical, modules[1:])
    if not _warned_clients:
        warnings.warn(
            "`ksef2.clients` submodules are deprecated; use the public "
            "`ksef2.clients` facade instead. Removal may happen no earlier "
            "than ksef2 2.0.0.",
            DeprecationWarning,
            stacklevel=3,
        )
        _warned_clients = True
