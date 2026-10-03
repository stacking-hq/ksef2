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
    """Version of the serialized draft format; currently always ``1``."""

    header: Annotated[
        InvoiceHeader | None, Field(description="Draft header state.")
    ] = None
    """Draft header state."""
    seller: Annotated[
        InvoiceEntity | None, Field(description="Draft seller state.")
    ] = None
    """Draft seller state."""
    buyer: Annotated[InvoiceEntity | None, Field(description="Draft buyer state.")] = (
        None
    )
    """Draft buyer state."""
    third_parties: Annotated[
        list[InvoiceThirdParty], Field(description="Draft third-party state.")
    ] = Field(default_factory=list)
    """Draft third-party state."""
    body: Annotated[
        KsefInvoiceBody | None, Field(description="Draft invoice body state.")
    ] = None
    """Draft invoice body state."""
    footer: Annotated[
        InvoiceFooter | None, Field(description="Draft footer state.")
    ] = None
    """Draft footer state."""
    attachment: Annotated[
        Attachment | None, Field(description="Draft attachment state.")
    ] = None
    """Draft attachment state."""

    @classmethod
    def from_invoice(cls, invoice: "KsefInvoice") -> "KsefInvoiceDraft":
        """Create an editable draft from a finished invoice.

        Args:
            invoice: Invoice to snapshot.

        Returns:
            A draft holding the invoice's state.
        """
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
    """Invoice header (``Faktura/Naglowek``)."""

    seller: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot1")]
    """Seller (``Faktura/Podmiot1``)."""
    buyer: Annotated[InvoiceEntity, Field(description="Maps to Faktura.Podmiot2")]
    """Buyer (``Faktura/Podmiot2``)."""
    third_parties: Annotated[
        Sequence[InvoiceThirdParty], Field(description="Maps to Faktura.Podmiot3")
    ] = Field(default_factory=tuple)
    """Additional subjects (``Faktura/Podmiot3``)."""

    body: Annotated[KsefInvoiceBody, Field(description="Maps to Faktura.Fa")]
    """Invoice body (``Faktura/Fa``)."""
    footer: Annotated[
        InvoiceFooter | None, Field(description="Maps to Faktura.Stopka")
    ] = None
    """Footer (``Faktura/Stopka``), if any."""

    attachment: Annotated[
        Attachment | None, Field(description="Maps to Faktura.FakturaZalacznik")
    ] = None
    """Attachment (``Faktura/Zalacznik``), if any."""

    @property
    def total_gross(self) -> Decimal:
        """Return the gross total computed by the invoice body.

        Returns:
            The gross total computed by the invoice body.
        """
        return self.body.total_gross

    @property
    def total_net(self) -> Decimal:
        """Return the net total computed by the invoice body.

        Returns:
            The net total computed by the invoice body.
        """
        return self.body.total_net

    @property
    def total_vat(self) -> Decimal:
        """Return the VAT total computed by the invoice body.

        Returns:
            The VAT total computed by the invoice body.
        """
        return self.body.total_vat

    @model_validator(mode="after")
    def _validate_seller_tax_id(self) -> "KsefInvoice":
        if not self.seller.tax_id:
            raise ValueError("seller tax_id is required")
        return self
