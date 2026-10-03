"""Public FA(3) API facade."""

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
    InvoiceSummaryOverrides,
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
    VatTreatment,
)
from ksef2._services.builders.fa3.root import StandardInvoiceBuilder


class FA3InvoiceBuilder(StandardInvoiceBuilder):
    """Canonical public FA(3) invoice builder.

    Example:
        ```python
        from datetime import date
        from decimal import Decimal

        from ksef2.fa3 import FA3InvoiceBuilder, VatRate

        builder = (
            FA3InvoiceBuilder()
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


__all__ = [
    "ContactInfo",
    "FA3InvoiceBuilder",
    "InvoiceAddress",
    "InvoiceEntity",
    "InvoiceHeader",
    "InvoiceSummaryOverrides",
    "InvoiceThirdParty",
    "KsefInvoice",
    "KsefInvoiceDraft",
    "SaleCategory",
    "TaxRegime",
    "VatClassification",
    "VatRate",
    "VatTreatment",
]
