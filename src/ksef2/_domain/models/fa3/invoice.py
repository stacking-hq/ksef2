"""Public FA(3) invoice domain models."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, override

from pydantic import Field, GetJsonSchemaHandler, model_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from ksef2._domain.models.base import (
    CURRENT_FORMAT_VERSION,
    KSeFPersistedModel,
    PersistedFormatVersion,
)
from ksef2._domain.models.base import KSeFBaseModel as KSeFBaseModel
from ksef2._domain.models.fa3.base import Fa3Model
from ksef2._domain.models.fa3.draft_input import check_draft_fields, forbid_model_extras
from ksef2._domain.models.fa3.attachment import Attachment
from ksef2._domain.models.fa3.body import KsefInvoiceBody
from ksef2._domain.models.fa3.footer import InvoiceFooter
from ksef2._domain.models.fa3.header import InvoiceHeader
from ksef2._domain.models.fa3.party import InvoiceEntity
from ksef2._domain.models.fa3.third_party import InvoiceThirdParty


class KsefInvoiceDraft(KSeFPersistedModel):
    """Serializable editable snapshot of FA(3) builder state.

    Raw draft input rejects unknown fields in every nested model before normalizing
    invoice data. Validation errors include the full input path. Partial rows and
    free-form attachment metadata remain supported.
    """

    wrap_validation_errors = True

    @model_validator(mode="before")
    @classmethod
    def _check_input_fields(cls, data: object) -> object:
        return check_draft_fields(cls, data)

    @classmethod
    @override
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema)
        forbid_model_extras(schema, handler)
        return schema

    wrap_validation_errors = True

    format_version: PersistedFormatVersion = CURRENT_FORMAT_VERSION
    """Version of the serialized draft format, a dotted number; currently ``"1"``."""

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


class KsefInvoice(Fa3Model):
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
