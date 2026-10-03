"""Public FA(3) invoice domain models."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ksef2._domain.models.base import KSeFBaseModel, KSeFPersistedModel
from ksef2._domain.models.fa3.attachment import Attachment
from ksef2._domain.models.fa3.body import KsefInvoiceBody
from ksef2._domain.models.fa3.footer import InvoiceFooter
from ksef2._domain.models.fa3.header import InvoiceHeader
from ksef2._domain.models.fa3.party import InvoiceEntity
from ksef2._domain.models.fa3.third_party import InvoiceThirdParty


class KsefInvoiceDraft(KSeFPersistedModel):
    """Serializable editable snapshot of FA(3) builder state."""

    format_version: Literal[1] = 1

    header: Annotated[
        InvoiceHeader | None, Field(description="Draft header state.")
    ] = None
    seller: Annotated[
        InvoiceEntity | None, Field(description="Draft seller state.")
    ] = None
    buyer: Annotated[InvoiceEntity | None, Field(description="Draft buyer state.")] = (
        None
    )
    third_parties: Annotated[
        list[InvoiceThirdParty], Field(description="Draft third-party state.")
    ] = Field(default_factory=list)
    body: Annotated[
        KsefInvoiceBody | None, Field(description="Draft invoice body state.")
    ] = None
    footer: Annotated[
        InvoiceFooter | None, Field(description="Draft footer state.")
    ] = None
    attachment: Annotated[
        Attachment | None, Field(description="Draft attachment state.")
    ] = None

    @classmethod
    def from_invoice(cls, invoice: "KsefInvoice") -> "KsefInvoiceDraft":
        """Create an editable draft snapshot from a complete invoice."""
        return cls(
            header=invoice.header.model_copy(deep=True),
            seller=invoice.seller.model_copy(deep=True),
            buyer=invoice.buyer.model_copy(deep=True),
            third_parties=[
                third_party.model_copy(deep=True)
                for third_party in invoice.third_parties
            ],
            body=invoice.body.model_copy(deep=True),
            footer=invoice.footer.model_copy(deep=True) if invoice.footer else None,
            attachment=(
                invoice.attachment.model_copy(deep=True) if invoice.attachment else None
            ),
        )


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
