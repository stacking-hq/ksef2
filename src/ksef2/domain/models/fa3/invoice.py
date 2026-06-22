"""Public FA(3) invoice domain models."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.fa3.attachment import Attachment
from ksef2.domain.models.fa3.body import KsefInvoiceBody
from ksef2.domain.models.fa3.footer import InvoiceFooter
from ksef2.domain.models.fa3.header import InvoiceHeader
from ksef2.domain.models.fa3.party import InvoiceEntity
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty


class KsefInvoice(KSeFBaseModel):
    """Root public aggregate for a FA(3) invoice."""

    header: Annotated[InvoiceHeader, Field(description="Maps to Faktura.Naglowek")]

    seller: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot1")]
    buyer: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot2")]
    third_parties: Annotated[
        Sequence[InvoiceThirdParty], Field(description="Maps to Faktura.Podmiot3")
    ] = Field(default_factory=tuple)

    body: Annotated[KsefInvoiceBody, Field(description="Maps to Faktura.Fa")]
    footer: Annotated[
        InvoiceFooter | None, Field(description="Maps to Faktura.Stopka")
    ] = None

    attachment: Annotated[
        Attachment | None, Field(description="Maps to Faktura.FakturaZalacznik")
    ] = None

    @property
    def total_gross(self) -> Decimal:
        """Return the gross total computed by the invoice body."""
        return self.body.total_gross

    @property
    def total_net(self) -> Decimal:
        """Return the net total computed by the invoice body."""
        return self.body.total_net

    @property
    def total_vat(self) -> Decimal:
        """Return the VAT total computed by the invoice body."""
        return self.body.total_vat

    @model_validator(mode="after")
    def _validate_seller_tax_id(self) -> "KsefInvoice":
        if not self.seller.tax_id:
            raise ValueError("seller tax_id is required")
        return self
