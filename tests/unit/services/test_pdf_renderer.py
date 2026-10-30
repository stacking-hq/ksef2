import os
import importlib.util
import subprocess
import sys
import tomllib
from base64 import b64decode, urlsafe_b64encode
from hashlib import sha256
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import cast

import pytest
from lxml import etree

from ksef2 import Environment, KSeFArgumentError, KSeFValidationError

from ksef2.renderers import InvoicePDFExporter, InvoiceXSLTRenderer, PDFPageSize


def test_renderers_package_imports_without_loading_weasyprint() -> None:
    import ksef2.renderers as renderers

    assert renderers.InvoiceXSLTRenderer is InvoiceXSLTRenderer
    assert renderers.InvoicePDFExporter is InvoicePDFExporter


def test_pdf_exporter_reports_missing_optional_dependency() -> None:
    missing_weasyprint = ModuleNotFoundError(
        "No module named 'weasyprint'", name="weasyprint"
    )

    with patch(
        "ksef2._services.renderers.pdf.import_module",
        side_effect=missing_weasyprint,
    ):
        with pytest.raises(ImportError, match=r"ksef2\[pdf\]"):
            _ = InvoicePDFExporter(verification_environment=Environment.TEST)


def test_pdf_exporter_requires_verification_environment() -> None:
    with pytest.raises(TypeError):
        InvoicePDFExporter()  # pyright: ignore[reportCallIssue]


def test_pdf_exporter_accepts_case_insensitive_environment_name() -> None:
    with patch("ksef2._services.renderers.pdf._load_weasyprint"):
        exporter = InvoicePDFExporter(verification_environment="tEsT")

    assert exporter._verification_environment is Environment.TEST


def test_weasyprint_is_declared_as_pdf_extra() -> None:
    pyproject_path = Path(__file__).parents[3] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    assert "weasyprint>=63.0" not in pyproject["project"]["dependencies"]
    assert pyproject["project"]["optional-dependencies"]["pdf"] == [
        "weasyprint>=63.0",
        "segno>=1.6.6",
    ]


@pytest.mark.parametrize(
    "environment, host",
    [
        ("PRODUCTION", "qr.ksef.mf.gov.pl"),
        ("TEST", "qr-test.ksef.mf.gov.pl"),
        ("DEMO", "qr-demo.ksef.mf.gov.pl"),
    ],
)
def test_pdf_verification_qr_uses_original_bytes(environment: str, host: str) -> None:
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    xml += b"\n  "
    number = "5261040828-20260201-ABCDEF123456-AB"
    with patch("ksef2._services.renderers.pdf._load_weasyprint") as load:
        weasyprint = load.return_value
        weasyprint.HTML.return_value.write_pdf.return_value = b"%PDF-test"
        exporter = InvoicePDFExporter(
            page_size=PDFPageSize.A4,
            verification_environment=Environment[environment],
            html_overrides="@page { size: A3 landscape; }",
        )
        with patch("ksef2._services.renderers.pdf.import_module") as import_module:
            qr = MagicMock()
            import_module.return_value = qr
            # The dependency writes a real SVG-shaped payload into the output stream.
            qr.make_qr.return_value.save.side_effect = lambda stream, **kwargs: (
                stream.write(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
            )
            assert exporter.export_from_string(xml, ksef_number=number) == b"%PDF-test"
            expected = (
                f"https://{host}/invoice/9999999999/15-02-2026/"
                + urlsafe_b64encode(sha256(xml).digest()).decode().rstrip("=")
            )
            qr.make_qr.assert_called_once_with(expected, error="m")
        content = weasyprint.HTML.call_args.kwargs["string"]
        document = etree.HTML(content)
        assert document is not None
        assert expected in [link.get("href") for link in document.findall(".//a")]
        assert number in content
        element = document.find(".//img[@alt='KSeF QR']")
        assert element is not None
        image = element.attrib["src"]
        assert isinstance(image, str)
        assert b64decode(image.split(",", 1)[1]).startswith(b"<svg")
        assert weasyprint.CSS.call_args.kwargs["string"].endswith(
            "@page { size: A4 portrait; }"
        )


def test_pdf_default_has_no_qr_and_rejects_empty_number() -> None:
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    with patch("ksef2._services.renderers.pdf._load_weasyprint") as load:
        load.return_value.HTML.return_value.write_pdf.return_value = b"%PDF-test"
        exporter = InvoicePDFExporter(verification_environment=Environment.TEST)
        assert exporter.export_from_string(xml) == b"%PDF-test"
        assert "KSeF QR" not in load.return_value.HTML.call_args.kwargs["string"]
        with pytest.raises(KSeFArgumentError, match="must not be empty"):
            _ = exporter.export_from_string(xml, ksef_number=" ")
        with pytest.raises(KSeFArgumentError, match="KSeF number format"):
            _ = exporter.export_from_string(xml, ksef_number="bogus")
        with pytest.raises(KSeFValidationError, match="Faktura root"):
            _ = exporter.export_from_string(b"<a/>")


def test_pdf_file_exports_include_real_svg_qr(tmp_path: Path) -> None:
    _ = pytest.importorskip("segno")
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    source = tmp_path / "invoice.xml"
    _ = source.write_bytes(xml)
    target = tmp_path / "nested/invoice.pdf"
    with patch("ksef2._services.renderers.pdf._load_weasyprint") as load:
        load.return_value.HTML.return_value.write_pdf.return_value = b"%PDF-test"
        exporter = InvoicePDFExporter(verification_environment=Environment.TEST)
        assert (
            exporter.export_to_file(
                source, target, ksef_number="5261040828-20260201-ABCDEF123456-AB"
            )
            == target
        )
        assert target.read_bytes() == b"%PDF-test"
        document = etree.HTML(load.return_value.HTML.call_args.kwargs["string"])
        assert document is not None
        element = document.find(".//img[@alt='KSeF QR']")
        assert element is not None
        image = element.attrib["src"]
        assert isinstance(image, str)
        svg = etree.fromstring(b64decode(image.split(",", 1)[1]))
        assert svg.tag == "{http://www.w3.org/2000/svg}svg"
        assert svg.xpath("//*[local-name()='path']")


@pytest.mark.parametrize(
    "size, css_size",
    [
        (PDFPageSize.A4, "A4 portrait"),
        (PDFPageSize.A4_LANDSCAPE, "A4 landscape"),
        (PDFPageSize.A3, "A3 portrait"),
        (PDFPageSize.A3_LANDSCAPE, "A3 landscape"),
        (PDFPageSize.LETTER, "letter portrait"),
        (PDFPageSize.LETTER_LANDSCAPE, "letter landscape"),
    ],
)
def test_pdf_page_size_overrides_css(size: PDFPageSize, css_size: str) -> None:
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    with patch("ksef2._services.renderers.pdf._load_weasyprint") as load:
        load.return_value.HTML.return_value.write_pdf.return_value = b"%PDF-test"
        exporter = InvoicePDFExporter(
            verification_environment=Environment.TEST,
            page_size=size,
            html_overrides="@page { size: A5; }",
        )
        assert exporter.export_from_string(xml) == b"%PDF-test"
        assert (
            load.return_value.CSS.call_args.kwargs["string"]
            == "@page { size: A5; }\n@page { size: " + css_size + "; }"
        )


@pytest.mark.skipif(
    os.getenv("KSEF2_RUNTIME_CHECKS") == "1",
    reason="Runtime type checks reject strings before the enum value boundary runs.",
)
def test_invalid_pdf_page_size_raises_sdk_argument_error() -> None:
    with pytest.raises(KSeFArgumentError, match="Invalid PDFPageSize value"):
        InvoicePDFExporter(
            verification_environment=Environment.TEST,
            page_size=cast(PDFPageSize, cast(object, "A7")),
        )


def test_pdf_notices_follow_qr_and_escape_text() -> None:
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    with (
        patch("ksef2._services.renderers.pdf._load_weasyprint") as load,
        patch("ksef2._services.renderers.pdf.import_module") as import_module,
    ):
        import_module.return_value.make_qr.return_value.save.side_effect = (
            lambda stream, **kwargs: stream.write(
                b'<svg xmlns="http://www.w3.org/2000/svg"/>'
            )
        )
        load.return_value.HTML.return_value.write_pdf.return_value = b"%PDF-test"
        exporter = InvoicePDFExporter(
            verification_environment="TEST",
            footer_text="TEST <script>alert(1)</script>",
            watermark_text="DEMO & TEST",
        )
        exporter.export_from_string(
            xml, ksef_number="5261040828-20260201-ABCDEF123456-AB"
        )
        document = etree.HTML(load.return_value.HTML.call_args.kwargs["string"])
        assert document is not None
        assert document.find(".//script") is None
        footer = document.find(".//div[@class='ksef2-footer']")
        assert footer is not None
        assert footer.text == "TEST <script>alert(1)</script>"
        qr_block = footer.getprevious()
        assert qr_block is not None
        assert qr_block.find(".//img[@alt='KSeF QR']") is not None
        watermark = document.find(".//div[@class='ksef2-watermark']")
        assert watermark is not None
        assert watermark.text == "DEMO & TEST"


@pytest.mark.parametrize("content_height, expected_pages", [(165, 1), (180, 2)])
@pytest.mark.parametrize("watermark_text", [None, "TEST visualization"])
def test_pdf_qr_fits_after_one_line_invoice(
    tmp_path: Path, content_height: int, expected_pages: int, watermark_text: str | None
) -> None:
    # The one-line invoice leaves room for a 35mm QR and its number, but not
    # the former 8mm margins on both sides of the QR block.
    if (
        importlib.util.find_spec("weasyprint") is None
        or importlib.util.find_spec("segno") is None
    ):
        pytest.skip("Requires ksef2[pdf] and WeasyPrint system libraries")
    stylesheet = tmp_path / "invoice.xsl"
    stylesheet.write_text(f"""<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/"><html><body style="margin:0">
<div style="height:{content_height}mm">One invoice line</div>
</body></html></xsl:template></xsl:stylesheet>""")
    sample = Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    # Keep the optional backend out of this process so lazy-import contract
    # tests can still detect accidental eager imports elsewhere in the SDK.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from unittest.mock import patch
from ksef2.renderers import InvoicePDFExporter
import weasyprint

def page_text(box):
    return getattr(box, "text", "") + " ".join(
        page_text(child) for child in getattr(box, "children", [])
    )

def capture_pages(html, **kwargs):
    document = html.render(**kwargs)
    print(len(document.pages))
    if sys.argv[3]:
        for page in document.pages:
            assert sys.argv[3] in page_text(page._page_box)
    return document.write_pdf()

exporter = InvoicePDFExporter(
    stylesheet_path=sys.argv[1], verification_environment="TEST",
    watermark_text=sys.argv[3] or None,
)
with patch.object(weasyprint.HTML, "write_pdf", capture_pages):
    pdf = exporter.export_from_path(sys.argv[2], ksef_number="5261040828-20260201-ABCDEF123456-AB")
assert pdf.startswith(b"%PDF-")
""",
            str(stylesheet),
            str(sample),
            watermark_text or "",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(expected_pages)
