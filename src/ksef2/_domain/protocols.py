import abc
from typing import Self

from ksef2._domain.models.fa3 import (
    InvoiceHeader,
    InvoiceEntity,
    InvoiceThirdParty,
    InvoiceFooter,
    Attachment,
)


class BaseBuilderProtocol(abc.ABC):
    """Common contract of invoice builders that accept whole sub-models."""

    _header: InvoiceHeader | None
    _seller: InvoiceEntity | None
    _buyer: InvoiceEntity | None
    _third_parties: list[InvoiceThirdParty] | None
    _footer: InvoiceFooter | None
    _attachment: Attachment | None

    @abc.abstractmethod
    def header_model(self, header: InvoiceHeader) -> Self:
        """Set the invoice header from a model.

        Args:
            header: Header to use.

        Returns:
            The builder, for chaining.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def seller_model(self, seller: InvoiceEntity) -> Self:
        """Set the seller from a model.

        Args:
            seller: Seller to use.

        Returns:
            The builder, for chaining.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def buyer_model(self, buyer: InvoiceEntity) -> Self:
        """Set the buyer from a model.

        Args:
            buyer: Buyer to use.

        Returns:
            The builder, for chaining.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def footer_model(self, footer: InvoiceFooter) -> Self:
        """Set the footer from a model.

        Args:
            footer: Footer to use.

        Returns:
            The builder, for chaining.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def attachment_model(self, attachment: Attachment) -> Self:
        """Set the attachment from a model.

        Args:
            attachment: Attachment to use.

        Returns:
            The builder, for chaining.
        """
        raise NotImplementedError
