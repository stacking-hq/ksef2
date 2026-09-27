import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from ksef2.domain.models import BatchInvoice
from ksef2.fa3 import FA3InvoiceBuilder, VatRate

_MARKER = "pyproject.toml"
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


def example_seller_nip() -> str:
    return required_env(EXAMPLE_SELLER_NIP_ENV)


def example_invoice_number() -> str:
    """Return a fresh FA(3) ``<P_2>`` number that KSeF has not seen from this seller."""
    return f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-{uuid4().hex}"


def example_invoice_xml(*, seller_nip: str, invoice_number: str | None = None) -> bytes:
    """Return one XSD-valid FA(3) invoice issued by ``seller_nip``.

    The number defaults to a fresh :func:`example_invoice_number`, because KSeF
    identifies an invoice by seller plus ``<P_2>`` and rejects a repeat with
    ``440 Duplikat faktury``.

    This is the only FA(3) generator in the repository: the examples and the
    integration tests both build their invoices here.
    """
    number = example_invoice_number() if invoice_number is None else invoice_number
    builder = (
        FA3InvoiceBuilder()
        .header(system_info="ksef2 examples")
        .seller(
            name="KSeF2 example seller",
            tax_id=seller_nip,
            country_code="PL",
            address_line_1="Przykładowa 1",
        )
        .buyer(
            name="KSeF2 example buyer",
            country_code="PL",
            address_line_1="Przykładowa 2",
        )
        .standard()
        .issue_date(date.today())
        .invoice_number(number)
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


def example_batch_invoices(
    *,
    seller_nip: str,
    count: int,
) -> list[BatchInvoice]:
    """Build ``count`` FA(3) invoices for one batch, each with its own number.

    KSeF identifies an invoice by seller plus its ``<P_2>`` number and rejects a
    repeat with ``440 Duplikat faktury``. Submitting one document twice therefore
    loses every invoice after the first while the session itself still reports
    success, so each invoice is given a unique number such as
    ``KSEF2-EXAMPLE-1f4c9a…-01`` and each run of the example is reproducible.
    """
    batch_tag = f"{EXAMPLE_INVOICE_NUMBER_PREFIX}-{uuid4().hex}"
    return [
        BatchInvoice(
            file_name=f"invoice-{ordinal:02d}.xml",
            content=example_invoice_xml(
                seller_nip=seller_nip,
                invoice_number=f"{batch_tag}-{ordinal:02d}",
            ),
        )
        for ordinal in range(1, count + 1)
    ]
