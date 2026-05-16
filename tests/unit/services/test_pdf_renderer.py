import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

from ksef2.services.renderers import InvoicePDFExporter, InvoiceXSLTRenderer


def test_renderers_package_imports_without_loading_weasyprint() -> None:
    import ksef2.services.renderers as renderers

    assert renderers.InvoiceXSLTRenderer is InvoiceXSLTRenderer
    assert renderers.InvoicePDFExporter is InvoicePDFExporter


def test_pdf_exporter_reports_missing_optional_dependency() -> None:
    missing_weasyprint = ModuleNotFoundError(
        "No module named 'weasyprint'", name="weasyprint"
    )

    with patch(
        "ksef2.services.renderers.pdf.import_module",
        side_effect=missing_weasyprint,
    ):
        with pytest.raises(ImportError, match=r"ksef2\[pdf\]"):
            _ = InvoicePDFExporter()


def test_weasyprint_is_declared_as_pdf_extra() -> None:
    pyproject_path = Path(__file__).parents[3] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    assert "weasyprint>=63.0" not in pyproject["project"]["dependencies"]
    assert pyproject["project"]["optional-dependencies"]["pdf"] == ["weasyprint>=63.0"]
