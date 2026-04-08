from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Self, override

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ksef2.domain.models.fa3 import Attachment, InvoiceFooter, KsefInvoiceDraft
from ksef2.domain.models.fa3.body.root import KsefInvoiceBody
from ksef2.domain.protocols import BaseBuilderProtocol
from ksef2.domain.models.fa3.header import InvoiceHeader
from ksef2.domain.models.fa3.invoice import KsefInvoice
from ksef2.domain.models.fa3.party import (
    ContactInfo,
    ContactInfoTuple,
    InvoiceAddress,
    InvoiceEntity,
)
from ksef2.domain.models.fa3.third_party import InvoiceThirdParty, ThirdPartyRole
from ksef2.infra.mappers.helpers import to_aware_datetime
from ksef2.infra.mappers.invoices.fa3.domain.invoice import to_spec as invoice_to_spec
from ksef2.infra.schema.fa3.models.schemat import Faktura, __NAMESPACE__
from ksef2.services.builders.fa3.attachment import AttachmentBuilderMixin
from ksef2.services.builders.fa3.footer import FooterBuilderMixin
from ksef2.services.builders.fa3.body.advance import AdvanceBodyBuilder
from ksef2.services.builders.fa3.body.correction import CorrectionBodyBuilder
from ksef2.services.builders.fa3.body.correction_advance import (
    CorrectionAdvanceBodyBuilder,
)
from ksef2.services.builders.fa3.body.correction_settlement import (
    CorrectionSettlementBodyBuilder,
)
from ksef2.services.builders.fa3.body.settlement import SettlementBodyBuilder
from ksef2.services.builders.fa3.body.simplified import SimplifiedBodyBuilder
from ksef2.services.builders.fa3.body.standard import StandardBodyBuilder


class StandardInvoiceBuilder(
    BaseBuilderProtocol,
    FooterBuilderMixin,
    AttachmentBuilderMixin,
):
    def __init__(self) -> None:
        self._header: InvoiceHeader | None = InvoiceHeader()
        self._seller: InvoiceEntity | None = None
        self._buyer: InvoiceEntity | None = None
        self._third_parties: list[InvoiceThirdParty] | None = None
        self._body: KsefInvoiceBody | None = None
        self._footer: InvoiceFooter | None = None
        self._attachment: Attachment | None = None

    def header(
        self, *, generation_timestamp: datetime | str | None = None, system_info: str
    ) -> Self:
        self._header = InvoiceHeader(
            generation_timestamp=to_aware_datetime(
                generation_timestamp or datetime.now()
            ),
            system_info=system_info,
        )
        return self

    @override
    def header_model(self, header: InvoiceHeader) -> Self:
        self._header = header
        return self

    def seller(
        self,
        *,
        name: str,
        country_code: str,
        address_line_1: str,
        tax_id: str | None = None,
        address_line_2: str | None = None,
        gln: str | None = None,
        vat_prefix: str | None = None,
        eu_vat_id: str | None = None,
        other_id: str | None = None,
        eori_number: str | None = None,
        customer_number: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Self:
        self._seller = self._build_entity(
            name=name,
            country_code=country_code,
            address_line_1=address_line_1,
            tax_id=tax_id,
            address_line_2=address_line_2,
            gln=gln,
            vat_prefix=vat_prefix,
            eu_vat_id=eu_vat_id,
            other_id=other_id,
            eori_number=eori_number,
            customer_number=customer_number,
            email=email,
            phone=phone,
        )
        return self

    @override
    def seller_model(self, seller: InvoiceEntity) -> Self:
        self._seller = seller
        return self

    def buyer(
        self,
        *,
        name: str | None,
        country_code: str | None,
        address_line_1: str | None,
        tax_id: str | None = None,
        address_line_2: str | None = None,
        gln: str | None = None,
        vat_prefix: str | None = None,
        eu_vat_id: str | None = None,
        other_id: str | None = None,
        eori_number: str | None = None,
        customer_number: str | None = None,
        buyer_id: str | None = None,
        jst_subordinate_unit: bool = False,
        vat_group_member: bool = False,
        email: str | None = None,
        phone: str | None = None,
    ) -> Self:
        self._buyer = self._build_entity(
            name=name,
            country_code=country_code,
            address_line_1=address_line_1,
            tax_id=tax_id,
            address_line_2=address_line_2,
            gln=gln,
            vat_prefix=vat_prefix,
            eu_vat_id=eu_vat_id,
            other_id=other_id,
            eori_number=eori_number,
            customer_number=customer_number,
            buyer_id=buyer_id,
            jst_subordinate_unit=jst_subordinate_unit,
            vat_group_member=vat_group_member,
            email=email,
            phone=phone,
        )
        return self

    @override
    def buyer_model(self, buyer: InvoiceEntity) -> Self:
        self._buyer = buyer
        return self

    def third_party(
        self,
        *,
        name: str,
        tax_id: str | None = None,
        internal_id: str | None = None,
        eu_vat_id: str | None = None,
        identity_country_code: str | None = None,
        other_id: str | None = None,
        no_id: bool = False,
        address_country_code: str | None = None,
        address_line_1: str | None = None,
        address_line_2: str | None = None,
        gln: str | None = None,
        correspondence_country_code: str | None = None,
        correspondence_address_line_1: str | None = None,
        correspondence_address_line_2: str | None = None,
        correspondence_gln: str | None = None,
        contacts: Sequence[ContactInfoTuple] | None = None,
        role: ThirdPartyRole | None = None,
        other_role: bool = False,
        role_description: str | None = None,
        share_percentage: Decimal | None = None,
        customer_number: str | None = None,
        eori_number: str | None = None,
        buyer_id: str | None = None,
    ) -> Self:
        address = None
        if (
            address_country_code is not None
            and address_line_1 is not None
            and address_line_2 is not None
            and gln is not None
        ):
            address = self._build_address(
                country_code=address_country_code,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                gln=gln,
            )

        correspondence_address = None
        if any(
            (
                correspondence_country_code,
                correspondence_address_line_1,
                correspondence_address_line_2,
                correspondence_gln,
            )
        ):
            if (
                correspondence_country_code is None
                or correspondence_address_line_1 is None
            ):
                raise ValueError(
                    "correspondence_country_code and correspondence_address_line_1 are required when providing a correspondence address."
                )
            correspondence_address = self._build_address(
                country_code=correspondence_country_code,
                address_line_1=correspondence_address_line_1,
                address_line_2=correspondence_address_line_2,
                gln=correspondence_gln,
            )

        built_contacts = None
        if contacts is not None:
            built_contacts = [
                ContactInfo(email=contact.email, phone=contact.phone)
                for contact in contacts
            ]

        third_party = InvoiceThirdParty(
            tax_id=tax_id,
            internal_id=internal_id,
            eu_vat_id=eu_vat_id,
            country_code=identity_country_code,
            other_id=other_id,
            no_id=no_id,
            name=name,
            address=address,
            correspondence_address=correspondence_address,
            contact=built_contacts,
            role=role,
            other_role=other_role,
            role_description=role_description,
            share_percentage=share_percentage,
            customer_number=customer_number,
            eori_number=eori_number,
            buyer_id=buyer_id,
        )
        return self.add_third_party_model(third_party)

    def add_third_party_model(self, third_party: InvoiceThirdParty) -> Self:
        if self._third_parties is None:
            self._third_parties = []
        self._third_parties.append(third_party)
        return self

    def replace_third_parties(self, third_parties: Sequence[InvoiceThirdParty]) -> Self:
        self._third_parties = list(third_parties)
        return self

    def clear_third_parties(self) -> Self:
        self._third_parties = []
        return self

    @override
    def footer_model(self, footer: InvoiceFooter) -> Self:
        self._footer = footer
        return self

    @override
    def attachment_model(self, attachment: Attachment) -> Self:
        self._attachment = attachment
        return self

    def standard(self) -> StandardBodyBuilder[Self]:
        return StandardBodyBuilder(self, self._set_body, self._body)

    def simplified(self) -> SimplifiedBodyBuilder[Self]:
        return SimplifiedBodyBuilder(self, self._set_body, self._body)

    def correction(self) -> CorrectionBodyBuilder[Self]:
        return CorrectionBodyBuilder(self, self._set_body, self._body)

    def advance(self) -> AdvanceBodyBuilder[Self]:
        return AdvanceBodyBuilder(self, self._set_body, self._body)

    def settlement(self) -> SettlementBodyBuilder[Self]:
        return SettlementBodyBuilder(self, self._set_body, self._body)

    def correction_advance(self) -> CorrectionAdvanceBodyBuilder[Self]:
        return CorrectionAdvanceBodyBuilder(self, self._set_body, self._body)

    def correction_settlement(self) -> CorrectionSettlementBodyBuilder[Self]:
        return CorrectionSettlementBodyBuilder(self, self._set_body, self._body)

    def _set_body(self, body: KsefInvoiceBody) -> None:
        self._body = body

    def dump_state(self) -> KsefInvoiceDraft:
        return KsefInvoiceDraft(
            header=self._header.model_copy(deep=True) if self._header else None,
            seller=self._seller.model_copy(deep=True) if self._seller else None,
            buyer=self._buyer.model_copy(deep=True) if self._buyer else None,
            third_parties=[
                third_party.model_copy(deep=True)
                for third_party in (self._third_parties or [])
            ],
            body=self._body.model_copy(deep=True) if self._body else None,
            footer=self._footer.model_copy(deep=True) if self._footer else None,
            attachment=(
                self._attachment.model_copy(deep=True) if self._attachment else None
            ),
        )

    def dump_state_json(self, *, indent: int | None = None) -> str:
        return self.dump_state().model_dump_json(indent=indent)

    def load_state(self, state: KsefInvoiceDraft) -> Self:
        self._header = state.header.model_copy(deep=True) if state.header else None
        self._seller = state.seller.model_copy(deep=True) if state.seller else None
        self._buyer = state.buyer.model_copy(deep=True) if state.buyer else None
        self._third_parties = [
            third_party.model_copy(deep=True) for third_party in state.third_parties
        ]
        self._body = state.body.model_copy(deep=True) if state.body else None
        self._footer = state.footer.model_copy(deep=True) if state.footer else None
        self._attachment = (
            state.attachment.model_copy(deep=True) if state.attachment else None
        )
        return self

    @classmethod
    def from_state(cls, state: KsefInvoiceDraft) -> Self:
        return cls().load_state(state)

    @classmethod
    def from_state_json(cls, data: str | bytes | bytearray) -> Self:
        return cls.from_state(KsefInvoiceDraft.model_validate_json(data))

    @classmethod
    def from_invoice(cls, invoice: KsefInvoice) -> Self:
        return cls.from_state(KsefInvoiceDraft.from_invoice(invoice))

    def build(self) -> KsefInvoice:
        if self._header is None:
            raise ValueError("Invoice header is required but not set.")
        if self._seller is None:
            raise ValueError("Invoice seller is required but not set.")
        if self._buyer is None:
            raise ValueError("Invoice buyer is required but not set.")
        if self._body is None:
            raise ValueError("Invoice body is required but not set.")

        if self._third_parties is None:
            self._third_parties = []

        return KsefInvoice(
            header=self._header,
            seller=self._seller,
            buyer=self._buyer,
            third_parties=self._third_parties,
            body=self._body,
            footer=self._footer,
            attachment=self._attachment,
        )

    def to_spec(self) -> Faktura:
        return invoice_to_spec(self.build())

    def to_xml(
        self,
        *,
        pretty_print: bool = True,
        xml_declaration: bool = True,
        encoding: str = "UTF-8",
    ) -> str:
        serializer = XmlSerializer(
            config=SerializerConfig(
                pretty_print=pretty_print,
                xml_declaration=xml_declaration,
                encoding=encoding,
            )
        )
        return serializer.render(  # pyright: ignore[reportUnknownMemberType]
            self.to_spec(), ns_map={None: __NAMESPACE__}
        )

    @staticmethod
    def _build_entity(
        *,
        name: str | None,
        country_code: str | None,
        address_line_1: str | None,
        tax_id: str | None,
        address_line_2: str | None,
        gln: str | None,
        vat_prefix: str | None,
        eu_vat_id: str | None,
        other_id: str | None = None,
        eori_number: str | None = None,
        customer_number: str | None = None,
        buyer_id: str | None = None,
        jst_subordinate_unit: bool = False,
        vat_group_member: bool = False,
        email: str | None = None,
        phone: str | None = None,
    ) -> InvoiceEntity:
        contact = ContactInfo(email=email, phone=phone) if email or phone else None
        address = None
        if country_code and address_line_1:
            address = StandardInvoiceBuilder._build_address(
                country_code=country_code,
                address_line_1=address_line_1,
                address_line_2=address_line_2,
                gln=gln,
            )
        return InvoiceEntity(
            tax_id=tax_id,
            eu_vat_id=eu_vat_id,
            other_id=other_id,
            eori_number=eori_number,
            customer_number=customer_number,
            buyer_id=buyer_id,
            jst_subordinate_unit=jst_subordinate_unit,
            vat_group_member=vat_group_member,
            vat_prefix=vat_prefix,
            name=name,
            address=address,
            contact=contact,
        )

    @staticmethod
    def _build_address(
        *,
        country_code: str,
        address_line_1: str,
        address_line_2: str | None = None,
        gln: str | None = None,
    ) -> InvoiceAddress:
        return InvoiceAddress(
            country_code=country_code,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            gln=gln,
        )
