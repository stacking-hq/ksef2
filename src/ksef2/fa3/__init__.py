"""Public FA(3) API facade."""

from typing import TYPE_CHECKING

from ksef2._domain.models.fa3 import (
    ContactInfo,
    InvoiceAddress,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceThirdParty,
    KsefInvoice,
    KsefInvoiceDraft,
)
from ksef2._domain.models.fa3.body import (
    InvoiceOrderLine,
    InvoiceRow,
    InvoiceSummaryOverrides,
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
    VatTreatment,
)
from ksef2._services.builders.fa3.root import StandardInvoiceBuilder
from ksef2._services.fa3 import parse_invoice_xml


class InvoiceBuilder(StandardInvoiceBuilder):
    """Canonical public FA(3) invoice builder.

    Example:
        ```python
        from datetime import date
        from decimal import Decimal

        from ksef2.fa3 import InvoiceBuilder, VatRate

        builder = (
            InvoiceBuilder()
            .header(system_info="billing-service")
            .seller(
                name="ACME S.A.",
                tax_id="1234567890",
                country_code="PL",
                address_line_1="ul. Przykladowa 123",
            )
            .buyer(
                name="XYZ GmbH",
                country_code="DE",
                address_line_1="Unter den Linden 1",
            )
            .standard()
                .issue_place("Warszawa")
                .issue_date(date(2026, 3, 29))
                .invoice_number("FV/2026/03/0001")
                .rows()
                    .add_line(
                        name="Consulting service",
                        unit_of_measure="h",
                        quantity=Decimal("10"),
                        unit_price_net=Decimal("100.00"),
                        vat_rate=VatRate.VAT_23,
                    )
                .done()
            .done()
        )

        xml_bytes = builder.to_xml().encode("utf-8")
        ```
    """


if TYPE_CHECKING:
    FA3InvoiceBuilder = InvoiceBuilder


def __getattr__(name: str):
    if name == "FA3InvoiceBuilder":
        import warnings

        warnings.warn(
            "FA3InvoiceBuilder is deprecated; use InvoiceBuilder instead. "
            "It may be removed no earlier than ksef2 2.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        globals()[name] = InvoiceBuilder
        return InvoiceBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ContactInfo",
    "InvoiceBuilder",
    "FA3InvoiceBuilder",
    "InvoiceAddress",
    "InvoiceEntity",
    "InvoiceHeader",
    "InvoiceOrderLine",
    "InvoiceRow",
    "InvoiceSummaryOverrides",
    "InvoiceThirdParty",
    "KsefInvoice",
    "KsefInvoiceDraft",
    "SaleCategory",
    "TaxRegime",
    "VatClassification",
    "VatRate",
    "VatTreatment",
    "parse_invoice_xml",
]
