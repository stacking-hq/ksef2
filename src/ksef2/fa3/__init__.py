"""Public FA(3) API facade."""

from ksef2.domain.models.fa3 import (
    ContactInfo,
    InvoiceAddress,
    InvoiceEntity,
    InvoiceHeader,
    InvoiceThirdParty,
    KsefInvoice,
    KsefInvoiceDraft,
)
from ksef2.domain.models.fa3.body import (
    InvoiceSummaryOverrides,
    SaleCategory,
    TaxRegime,
    VatClassification,
    VatRate,
    VatTreatment,
)
from ksef2.services.builders.fa3.root import StandardInvoiceBuilder


class FA3InvoiceBuilder(StandardInvoiceBuilder):
    """Canonical public FA(3) invoice builder."""


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
