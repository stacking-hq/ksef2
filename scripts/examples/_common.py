import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from lxml import etree

from ksef2.domain.models import BatchInvoice
from ksef2.fa3 import FA3InvoiceBuilder, VatRate

_MARKER = "pyproject.toml"
EXAMPLE_INVOICE_XML_ENV = "KSEF2_EXAMPLE_INVOICE_XML"
EXAMPLE_SELLER_NIP_ENV = "KSEF2_EXAMPLE_SELLER_NIP"
EXAMPLE_INVOICE_NUMBER_PREFIX = "KSEF2-EXAMPLE"


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


def example_batch_invoices(
    *,
    seller_nip: str,
    count: int,
    invoice_path: Path | None = None,
) -> list[BatchInvoice]:
    """Build ``count`` FA(3) invoices for one batch, each with its own number.

    KSeF identifies an invoice by seller plus its ``<P_2>`` number and rejects a
    repeat with ``440 Duplikat faktury``. Submitting one document twice therefore
    loses every invoice after the first while the session itself still reports
    success, so each invoice is given a unique number such as
    ``KSEF2-EXAMPLE-1f4c9a…-01`` and each run of the example is reproducible.

    Invoices are generated FA(3) documents unless ``invoice_path`` is given or
    ``KSEF2_EXAMPLE_INVOICE_XML`` points at a file; then that document is reused
    with only its invoice number rewritten per invoice.
    """
    configured_path = os.environ.get(EXAMPLE_INVOICE_XML_ENV)
    source_path = invoice_path
    if source_path is None and configured_path:
        source_path = Path(configured_path).expanduser()

    batch_tag = f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-{uuid4().hex}"
    invoices: list[BatchInvoice] = []

    for ordinal in range(1, count + 1):
        invoice_number = f"{batch_tag}-{ordinal:02d}"
        if source_path is None:
            content = _generated_invoice_xml(
                seller_nip=seller_nip,
                invoice_number=invoice_number,
            )
        else:
            content = _invoice_xml_with_number(source_path, invoice_number)
        invoices.append(
            BatchInvoice(
                file_name=f"invoice-{ordinal:02d}.xml",
                content=content,
            )
        )

    return invoices


def _generated_invoice_xml(*, seller_nip: str, invoice_number: str) -> bytes:
    """Build a minimal FA(3) standard invoice issued by ``seller_nip``."""
    builder = (
        FA3InvoiceBuilder()
        .header(system_info="ksef2 examples")
        .seller(
            name="KSeF2 example seller",
            tax_id=seller_nip,
            country_code="PL",
            address_line_1="Przykładowa 1",
            address_line_2="Warszawa",
        )
        .buyer(
            name="KSeF2 example buyer",
            country_code="PL",
            address_line_1="Przykładowa 2",
        )
        .standard()
        .issue_place("Warszawa")
        .issue_date(date.today())
        .invoice_number(invoice_number)
        .rows()
        .add_line(
            name="Example service",
            quantity=Decimal("1"),
            unit_of_measure="szt.",
            unit_price_net=Decimal("10.00"),
            vat_rate=VatRate.VAT_23,
        )
        .done()
        .done()
    )
    return builder.to_xml().encode("utf-8")


def _invoice_xml_with_number(source_path: Path, invoice_number: str) -> bytes:
    """Return the invoice at ``source_path`` with only its FA(3) `<P_2>` replaced.

    Everything else the caller supplied — seller, buyer, lines, dates — is kept,
    so this stays a way to demo the batch API with a real invoice.
    """
    if not source_path.is_file():
        raise FileNotFoundError(f"Example invoice XML not found: {source_path}")

    try:
        document = etree.parse(str(source_path))
    except etree.XMLSyntaxError as exc:
        raise ValueError(
            f"Example invoice XML is not well-formed XML: {source_path}"
        ) from exc

    fa_body = document.find("{*}Fa")
    if fa_body is None:
        raise ValueError(
            f"{source_path} is not an FA invoice document: it has no <Fa> element."
        )

    number_element = fa_body.find("{*}P_2")
    if number_element is None:
        raise ValueError(
            f"{source_path} has no <P_2> invoice number inside <Fa>, so the example "
            "cannot give each invoice in the batch its own number."
        )

    number_element.text = invoice_number
    return etree.tostring(document, xml_declaration=True, encoding="UTF-8")
