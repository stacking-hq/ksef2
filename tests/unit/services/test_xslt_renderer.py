from pathlib import Path

import pytest

from ksef2.core.exceptions import KSeFInvoiceRenderingError
from ksef2.renderers import InvoiceXSLTRenderer


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


@pytest.mark.parametrize("schema_source", ["file", "network"])
def test_default_xslt_access_control_denies_document_reads(
    tmp_path: Path,
    schema_source: str,
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
    renderer = InvoiceXSLTRenderer(stylesheet_path=stylesheet_path)

    with pytest.raises(
        KSeFInvoiceRenderingError,
        match="XSLT transformation failed while rendering invoice.",
    ) as exc_info:
        _ = renderer.render_from_string("<invoice/>")

    assert exc_info.value.__cause__ is not None


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
