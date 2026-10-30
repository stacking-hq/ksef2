from pathlib import Path

import pytest
from lxml import etree

from ksef2._core.exceptions import KSeFInvoiceRenderingError
from ksef2.renderers import InvoiceXSLTRenderer


@pytest.mark.parametrize("source", ["path", "bytes"])
def test_bundled_code_lookups_render_valid_fa3_invoice_offline(source: str) -> None:
    root = Path(__file__).parents[3]
    invoice_path = root / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    # Both validation and the renderer use parsers that forbid network access.
    parser = etree.XMLParser(no_network=True)
    schema = etree.XMLSchema(etree.parse(str(root / "schemas/FA3/schemat.xsd"), parser))
    schema.assertValid(etree.parse(str(invoice_path), parser))
    renderer = InvoiceXSLTRenderer(enable_code_lookups=True)

    if source == "path":
        html = renderer.render_from_path(invoice_path)
    else:
        html = renderer.render_from_string(invoice_path.read_bytes())

    assert "POLSKA" in html
    assert "FV2026/02/150" in html


@pytest.mark.parametrize(
    ("parameter", "type_name", "code", "description"),
    [
        ("schema-krajow", "TKodKraju", "PL", "POLSKA"),
        ("schema-urzedow", "TKodUS", "0202", "URZĄD SKARBOWY W BOLESŁAWCU"),
        ("schema-urzedowexwus", "TKodUS1", "0202", "URZĄD SKARBOWY W BOLESŁAWCU"),
        (
            "schema-naczelnikow-urzedow",
            "TKodNaczUS",
            "0202",
            "NACZELNIK URZĘDU SKARBOWEGO W BOLESŁAWCU",
        ),
        ("schema-walut", "TKodWaluty", "PLN", "ZŁOTY"),
    ],
)
def test_custom_stylesheet_resolves_each_bundled_code_list_offline(
    tmp_path: Path, parameter: str, type_name: str, code: str, description: str
) -> None:
    common_stylesheet = (
        InvoiceXSLTRenderer().stylesheet_path.parent
        / "WspolneSzablonyWizualizacji_v12-0E.xsl"
    )
    stylesheet = tmp_path / "lookups.xsl"
    _ = stylesheet.write_text(
        f"""<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:import href="{common_stylesheet.as_uri()}"/>
  <xsl:template match="/">
    <html><body><xsl:call-template name="ZnajdzWEnumeracji">
      <xsl:with-param name="schema" select="${parameter}"/>
      <xsl:with-param name="typ" select="'{type_name}'"/>
      <xsl:with-param name="kod" select="'{code}'"/>
    </xsl:call-template></body></html>
  </xsl:template>
</xsl:stylesheet>""",
        encoding="utf-8",
    )
    renderer = InvoiceXSLTRenderer(stylesheet_path=stylesheet, enable_code_lookups=True)

    assert description in renderer.render_from_string("<invoice/>")


def write_document_lookup_stylesheet(tmp_path: Path, schema_uri: str) -> Path:
    stylesheet_path = tmp_path / "lookup.xsl"
    _ = stylesheet_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="html"/>
  <xsl:param name="schema" select="'{schema_uri}'"/>
  <xsl:template match="/">
    <html>
      <body>
        <xsl:value-of select="document($schema)/codes/value"/>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
""",
        encoding="utf-8",
    )
    return stylesheet_path


@pytest.mark.parametrize(
    ("schema_source", "enable_code_lookups"),
    [("file", False), ("network", False), ("network", True)],
)
def test_default_xslt_access_control_denies_document_reads(
    tmp_path: Path,
    schema_source: str,
    enable_code_lookups: bool,
) -> None:
    codes_path = tmp_path / "codes.xml"
    _ = codes_path.write_text(
        "<codes><value>lookup ok</value></codes>",
        encoding="utf-8",
    )
    if schema_source == "file":
        schema_uri = codes_path.as_uri()
    else:
        schema_uri = "http://127.0.0.1:9/codes.xml"

    stylesheet_path = write_document_lookup_stylesheet(tmp_path, schema_uri)
    renderer = InvoiceXSLTRenderer(
        stylesheet_path=stylesheet_path, enable_code_lookups=enable_code_lookups
    )

    with pytest.raises(
        KSeFInvoiceRenderingError,
        match="XSLT transformation failed while rendering invoice",
    ) as exc_info:
        _ = renderer.render_from_string("<invoice/>")

    assert exc_info.value.__cause__ is not None
    assert schema_uri in str(exc_info.value)


def test_unresolved_document_uri_is_in_rendering_error(tmp_path: Path) -> None:
    schema_uri = (tmp_path / "missing codes.xml").as_uri()
    stylesheet = write_document_lookup_stylesheet(tmp_path, schema_uri)
    renderer = InvoiceXSLTRenderer(stylesheet_path=stylesheet, enable_code_lookups=True)

    with pytest.raises(KSeFInvoiceRenderingError) as exc_info:
        _ = renderer.render_from_string("<invoice/>")

    assert schema_uri in str(exc_info.value)
    assert schema_uri in exc_info.value.context["details"]
    assert isinstance(exc_info.value.__cause__, etree.XSLTApplyError)


def test_enabled_code_lookups_allow_read_only_document_file_reads(
    tmp_path: Path,
) -> None:
    codes_path = tmp_path / "codes.xml"
    _ = codes_path.write_text(
        "<codes><value>lookup ok</value></codes>",
        encoding="utf-8",
    )
    stylesheet_path = write_document_lookup_stylesheet(tmp_path, codes_path.as_uri())
    renderer = InvoiceXSLTRenderer(
        stylesheet_path=stylesheet_path,
        enable_code_lookups=True,
    )

    html = renderer.render_from_string("<invoice/>")

    assert "lookup ok" in html


def test_html_optional_notices_are_plain_text(tmp_path: Path) -> None:
    from lxml import etree

    xml_path = Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    renderer = InvoiceXSLTRenderer(
        footer_text="TEST <b>notice</b>", watermark_text="DEMO"
    )
    target = renderer.render_to_file(xml_path, tmp_path / "invoice.html")
    html = target.read_text()
    assert html == renderer.render_from_path(xml_path)
    assert html == renderer.render_from_string(xml_path.read_bytes())
    document = etree.HTML(html)
    assert document is not None
    footer = document.find(".//div[@class='ksef2-footer']")
    assert footer is not None
    assert footer.text == "TEST <b>notice</b>"
    assert len(footer) == 0
    watermark = document.find(".//div[@class='ksef2-watermark']")
    assert watermark is not None
    assert watermark.text == "DEMO"


def test_html_default_notices_leave_output_unchanged() -> None:
    xml = (
        Path(__file__).parents[3] / "schemas/FA3/samples/FA_3_Przykład_1.xml"
    ).read_bytes()
    assert InvoiceXSLTRenderer().render_from_string(xml) == InvoiceXSLTRenderer(
        footer_text=None, watermark_text=None
    ).render_from_string(xml)
