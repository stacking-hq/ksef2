import os
from pathlib import Path

_MARKER = "pyproject.toml"
EXAMPLE_INVOICE_XML_ENV = "KSEF2_EXAMPLE_INVOICE_XML"
EXAMPLE_SELLER_NIP_ENV = "KSEF2_EXAMPLE_SELLER_NIP"


def repo_root() -> Path:
    """Find the repository root by walking up from this file looking for pyproject.toml."""
    for parent in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        if (parent / _MARKER).exists():
            return parent
    raise FileNotFoundError("Could not find repo root")


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    raise RuntimeError(f"Set {name} before running this example.")


def example_invoice_xml_path() -> Path:
    return Path(required_env(EXAMPLE_INVOICE_XML_ENV)).expanduser()


def example_seller_nip() -> str:
    return required_env(EXAMPLE_SELLER_NIP_ENV)
