"""Public FA(3) invoice domain models."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.fa3.body import KsefInvoiceBody
from ksef2.domain.models.fa3.header import InvoiceHeader
from ksef2.domain.models.fa3.party import InvoiceEntity


class InvoiceDetails(KSeFBaseModel):
    """Minimal invoice details needed by the public FA(3) layer."""

    invoice_number: str
    issue_date: date
    currency: str = "PLN"


class KsefInvoice(KSeFBaseModel):
    """Root public aggregate for a minimal FA(3) invoice draft."""

    invoice_header: Annotated[
        InvoiceHeader, Field(description="Maps to Faktura.Naglowek")
    ]

    seller: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot1")]
    buyer: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot2")]

    body: Annotated[KsefInvoiceBody, Field(description="Maps to Faktura.Fa")]

    @property
    def total_gross(self) -> Decimal:
        return self.body.total_gross

    @property
    def total_net(self) -> Decimal:
        return self.body.total_net

    @property
    def total_vat(self) -> Decimal:
        return self.body.total_vat

    @model_validator(mode="after")
    def _validate_seller_tax_id(self) -> "KsefInvoice":
        if not self.seller.tax_id:
            raise ValueError("seller tax_id is required")
        return self
