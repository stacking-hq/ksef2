import abc
from typing import Self

from ksef2.domain.models.fa3 import (
    InvoiceHeader,
    InvoiceEntity,
    InvoiceThirdParty,
    InvoiceFooter,
    Attachment,
)


class BaseBuilderProtocol(abc.ABC):
    _header: InvoiceHeader | None
    _seller: InvoiceEntity | None
    _buyer: InvoiceEntity | None
    _third_parties: list[InvoiceThirdParty] | None
    _footer: InvoiceFooter | None
    _attachment: Attachment | None

    @abc.abstractmethod
    def header_model(self, header: InvoiceHeader) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    def seller_model(self, seller: InvoiceEntity) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    def buyer_model(self, buyer: InvoiceEntity) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    def footer_model(self, footer: InvoiceFooter) -> Self:
        raise NotImplementedError

    @abc.abstractmethod
    def attachment_model(self, attachment: Attachment) -> Self:
        raise NotImplementedError
