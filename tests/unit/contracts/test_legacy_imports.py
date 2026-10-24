"""Existing application imports work with canonical modules and one warning."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("canonical_first", [False, True])
@pytest.mark.parametrize(
    ("family", "paths", "replacements"),
    [
        (
            "core",
            ["exceptions", "xades", "middlewares.retry"],
            ["ksef2", "ksef2.xades"],
        ),
        (
            "domain",
            [
                "models.invoices",
                "models.pagination",
                "models.session",
                "models.fa3.body.row",
            ],
            ["ksef2.models", "ksef2.fa3"],
        ),
        (
            "infra",
            [
                "schema.fa3.models.schemat",
                "mappers",
                "schema",
                "schema.api.spec.models",
            ],
            ["ksef2.raw", "ksef2.fa3"],
        ),
        (
            "services",
            ["invoices", "async_invoices", "builders.fa3.root", "renderers.xslt"],
            ["ksef2.clients", "ksef2.fa3", "ksef2.renderers"],
        ),
    ],
)
def test_legacy_imports_preserve_identity_and_warn_once(
    family: str, paths: list[str], replacements: list[str], canonical_first: bool
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import importlib
import sys
import warnings
import ksef2

hooks = tuple(sys.meta_path)
if {canonical_first!r}:
    for path in {paths!r}:
        importlib.import_module('ksef2._{family}.' + path)

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always', DeprecationWarning)
    from ksef2.{family}.{paths[0]} import __name__ as module_name
    for path in {paths!r}:
        old = importlib.import_module('ksef2.{family}.' + path)
        new = importlib.import_module('ksef2._{family}.' + path)
        assert old is new, path
    assert importlib.import_module('ksef2.{family}') is importlib.import_module('ksef2._{family}')

messages = [str(w.message) for w in caught if w.category is DeprecationWarning]
assert len(messages) == 1, messages
assert messages[0].startswith('`ksef2.{family}` and its submodules are deprecated'), messages
assert 'no earlier than ksef2 2.0.0' in messages[0], messages
for replacement in {replacements!r}:
    assert replacement in messages[0], messages
assert tuple(sys.meta_path) == hooks
assert 'weasyprint' not in sys.modules

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always', DeprecationWarning)
    for path in {paths!r}:
        importlib.import_module('ksef2.{family}.' + path)
assert not caught
""",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_real_application_imports_and_resources() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "ignore::DeprecationWarning",
            "-c",
            """
import sys
from importlib.resources import files
import ksef2
from ksef2.domain.models.invoices import InvoicesFilter
from ksef2.domain.models.pagination import InvoiceMetadataParams
from ksef2.domain.models.session import FormSchema
from ksef2.services.invoices import InvoicesFilter as ServiceFilter
from ksef2.core.exceptions import KSeFApiError
from ksef2.core.xades import load_certificate_from_pem
from ksef2.services.builders import FA3InvoiceBuilder
from ksef2.services.renderers.xslt import InvoiceXSLTRenderer
import ksef2.infra.schema.fa3.models.schemat
from ksef2.infra.schema.fa3 import STYLESHEET_PATH
from ksef2 import models, fa3, xades, renderers

assert InvoicesFilter is ServiceFilter is models.InvoicesFilter
assert InvoiceMetadataParams is models.InvoiceMetadataParams
assert FormSchema is ksef2.FormSchema
assert KSeFApiError is ksef2.KSeFApiError
assert load_certificate_from_pem is xades.load_certificate_from_pem
assert FA3InvoiceBuilder is fa3.FA3InvoiceBuilder
assert InvoiceXSLTRenderer is renderers.InvoiceXSLTRenderer
assert STYLESHEET_PATH.is_file()
assert files('ksef2.infra.schema.fa3').joinpath('definitions/schemat.xsd').is_file()
assert ksef2.infra.schema.fa3.models.schemat is sys.modules['ksef2._infra.schema.fa3.models.schemat']
assert 'weasyprint' not in sys.modules
""",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_modern_imports_do_not_activate_legacy_packages() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
import warnings
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always', DeprecationWarning)
    import ksef2
    from ksef2 import clients, models, fa3, xades, raw

assert not [w for w in caught if w.category is DeprecationWarning], caught
for family in ('core', 'domain', 'infra', 'services'):
    assert 'ksef2.' + family not in sys.modules, family
assert 'ksef2._legacy_imports' not in sys.modules
assert 'ksef2._services.renderers.pdf' not in sys.modules
assert 'weasyprint' not in sys.modules
""",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
