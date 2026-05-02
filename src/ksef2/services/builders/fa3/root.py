from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self, override

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
from ksef2.services.builders.fa3.metadata import builder_param


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
        self,
        *,
        generation_timestamp: Annotated[
            datetime | str | None,
            builder_param(
                "Invoice generation timestamp written to the FA(3) header. Leave it empty to use the current time.",
                examples=["2026-04-09T10:15:00+02:00"],
                format="date-time",
                priority="advanced",
            ),
        ] = None,
        system_info: Annotated[
            str | None,
            builder_param(
                "Name of the application or service that generated the invoice. Leave empty to omit from the header.",
                examples=["my-erp", "billing-service"],
            ),
        ] = None,
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
        name: Annotated[
            str,
            builder_param(
                "Seller name shown on the invoice.",
                examples=["ACME sp. z o.o."],
            ),
        ],
        country_code: Annotated[
            str,
            builder_param(
                "Two-letter country code for the seller address.",
                examples=["PL", "DE"],
                format="country-code",
            ),
        ],
        address_line_1: Annotated[
            str,
            builder_param(
                "First seller address line, typically street and building number.",
                examples=["ul. Przykladowa 10"],
            ),
        ],
        tax_id: Annotated[
            str | None,
            builder_param(
                "Seller tax identifier, usually the NIP for Polish entities.",
                examples=["1234567890"],
            ),
        ] = None,
        address_line_2: Annotated[
            str | None,
            builder_param(
                "Second seller address line, typically postal code and city.",
                examples=["00-001 Warszawa"],
            ),
        ] = None,
        gln: Annotated[
            str | None,
            builder_param(
                "Seller GLN identifier when the seller is identified in logistics systems.",
                examples=["5901234123457"],
                priority="advanced",
            ),
        ] = None,
        vat_prefix: Annotated[
            str | None,
            builder_param(
                "Seller VAT prefix used together with domestic tax identifiers.",
                examples=["PL"],
                priority="advanced",
            ),
        ] = None,
        eu_vat_id: Annotated[
            str | None,
            builder_param(
                "Seller EU VAT identifier used for intra-EU transactions.",
                examples=["PL1234567890"],
                priority="advanced",
            ),
        ] = None,
        other_id: Annotated[
            str | None,
            builder_param(
                "Alternative seller identifier when tax_id or eu_vat_id is not used.",
                examples=["REG-445566"],
                priority="advanced",
            ),
        ] = None,
        eori_number: Annotated[
            str | None,
            builder_param(
                "Seller EORI number for customs-related invoice scenarios.",
                examples=["PL123456789000000"],
                priority="advanced",
            ),
        ] = None,
        customer_number: Annotated[
            str | None,
            builder_param(
                "Seller customer number used by the trading parties.",
                examples=["CUS-0001"],
                priority="advanced",
            ),
        ] = None,
        email: Annotated[
            str | None,
            builder_param(
                "Seller contact email included in invoice party details.",
                examples=["billing@example.com"],
                priority="advanced",
            ),
        ] = None,
        phone: Annotated[
            str | None,
            builder_param(
                "Seller contact phone number included in invoice party details.",
                examples=["+48 123 456 789"],
                priority="advanced",
            ),
        ] = None,
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
        name: Annotated[
            str | None,
            builder_param(
                "Buyer name shown on the invoice. Leave empty only when the invoice scenario allows it.",
                examples=["XYZ GmbH"],
            ),
        ],
        country_code: Annotated[
            str | None,
            builder_param(
                "Two-letter country code for the buyer address.",
                examples=["PL", "DE"],
                format="country-code",
            ),
        ],
        address_line_1: Annotated[
            str | None,
            builder_param(
                "First buyer address line, typically street and building number.",
                examples=["ul. Odbiorcza 20"],
            ),
        ],
        tax_id: Annotated[
            str | None,
            builder_param(
                "Buyer tax identifier, usually the NIP for domestic invoices.",
                examples=["9876543210"],
            ),
        ] = None,
        address_line_2: Annotated[
            str | None,
            builder_param(
                "Second buyer address line, typically postal code and city.",
                examples=["00-950 Warszawa"],
            ),
        ] = None,
        gln: Annotated[
            str | None,
            builder_param(
                "Buyer GLN identifier used in logistics or EDI processes.",
                examples=["5901234123457"],
                priority="advanced",
            ),
        ] = None,
        vat_prefix: Annotated[
            str | None,
            builder_param(
                "Buyer VAT prefix used together with domestic identifiers.",
                examples=["PL"],
                priority="advanced",
            ),
        ] = None,
        eu_vat_id: Annotated[
            str | None,
            builder_param(
                "Buyer EU VAT identifier for intra-EU transactions.",
                examples=["DE123456789"],
                priority="advanced",
            ),
        ] = None,
        other_id: Annotated[
            str | None,
            builder_param(
                "Alternative buyer identifier used when tax_id or eu_vat_id is not available.",
                examples=["CUST-7788"],
                priority="advanced",
            ),
        ] = None,
        eori_number: Annotated[
            str | None,
            builder_param(
                "Buyer EORI number for customs-related invoice scenarios.",
                examples=["DE123456789000000"],
                priority="advanced",
            ),
        ] = None,
        customer_number: Annotated[
            str | None,
            builder_param(
                "Buyer customer number used by the trading parties.",
                examples=["BUY-0004"],
                priority="advanced",
            ),
        ] = None,
        buyer_id: Annotated[
            str | None,
            builder_param(
                "Internal buyer identifier used in some FA(3) scenarios.",
                examples=["buyer-42"],
                priority="advanced",
            ),
        ] = None,
        jst_subordinate_unit: Annotated[
            bool,
            builder_param(
                "Set to true when the buyer is a subordinate unit of a Polish local government entity.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        vat_group_member: Annotated[
            bool,
            builder_param(
                "Set to true when the buyer belongs to a VAT group.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        email: Annotated[
            str | None,
            builder_param(
                "Buyer contact email included in invoice party details.",
                examples=["ap@example.com"],
                priority="advanced",
            ),
        ] = None,
        phone: Annotated[
            str | None,
            builder_param(
                "Buyer contact phone number included in invoice party details.",
                examples=["+49 30 123456"],
                priority="advanced",
            ),
        ] = None,
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
        name: Annotated[
            str,
            builder_param(
                "Third-party name shown in the FA(3) party section.",
                examples=["Logistics Partner sp. z o.o."],
            ),
        ],
        tax_id: Annotated[
            str | None,
            builder_param(
                "Third-party tax identifier.",
                examples=["1234567890"],
            ),
        ] = None,
        internal_id: Annotated[
            str | None,
            builder_param(
                "Internal identifier assigned to the third party.",
                examples=["TP-001"],
                priority="advanced",
            ),
        ] = None,
        eu_vat_id: Annotated[
            str | None,
            builder_param(
                "EU VAT identifier for the third party.",
                examples=["PL1234567890"],
                priority="advanced",
            ),
        ] = None,
        identity_country_code: Annotated[
            str | None,
            builder_param(
                "Country code attached to the third-party identity data.",
                examples=["PL", "DE"],
                format="country-code",
                priority="advanced",
            ),
        ] = None,
        other_id: Annotated[
            str | None,
            builder_param(
                "Alternative third-party identifier.",
                examples=["ALT-7788"],
                priority="advanced",
            ),
        ] = None,
        no_id: Annotated[
            bool,
            builder_param(
                "Set to true when the third party is intentionally recorded without an identifier.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        address_country_code: Annotated[
            str | None,
            builder_param(
                "Country code for the third-party address.",
                examples=["PL"],
                format="country-code",
                priority="advanced",
            ),
        ] = None,
        address_line_1: Annotated[
            str | None,
            builder_param(
                "First line of the third-party address.",
                examples=["ul. Partnera 1"],
                priority="advanced",
            ),
        ] = None,
        address_line_2: Annotated[
            str | None,
            builder_param(
                "Second line of the third-party address.",
                examples=["00-100 Warszawa"],
                priority="advanced",
            ),
        ] = None,
        gln: Annotated[
            str | None,
            builder_param(
                "GLN assigned to the third-party address.",
                examples=["5901234123457"],
                priority="advanced",
            ),
        ] = None,
        correspondence_country_code: Annotated[
            str | None,
            builder_param(
                "Country code for the correspondence address.",
                examples=["PL"],
                format="country-code",
                priority="advanced",
            ),
        ] = None,
        correspondence_address_line_1: Annotated[
            str | None,
            builder_param(
                "First line of the third-party correspondence address.",
                examples=["ul. Korespondencyjna 7"],
                priority="advanced",
            ),
        ] = None,
        correspondence_address_line_2: Annotated[
            str | None,
            builder_param(
                "Second line of the third-party correspondence address.",
                examples=["00-120 Warszawa"],
                priority="advanced",
            ),
        ] = None,
        correspondence_gln: Annotated[
            str | None,
            builder_param(
                "GLN assigned to the correspondence address.",
                examples=["5901234123457"],
                priority="advanced",
            ),
        ] = None,
        contacts: Annotated[
            Sequence[ContactInfoTuple] | None,
            builder_param(
                "Contact entries for the third party, such as email and phone.",
                examples=[],
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.party.ContactInfoTuple",
            ),
        ] = None,
        role: Annotated[
            ThirdPartyRole | None,
            builder_param(
                "Role of the third party in the invoice context.",
                examples=["factor"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
        other_role: Annotated[
            bool,
            builder_param(
                "Set to true when the role is described manually instead of using the predefined role enum.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        role_description: Annotated[
            str | None,
            builder_param(
                "Free-text description of the third-party role.",
                examples=["Customs representative"],
                priority="advanced",
            ),
        ] = None,
        share_percentage: Annotated[
            Decimal | None,
            builder_param(
                "Share percentage assigned to the third party when the invoice scenario requires it.",
                examples=["50.00"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
        customer_number: Annotated[
            str | None,
            builder_param(
                "Customer number assigned to the third party.",
                examples=["TP-CUST-1"],
                priority="advanced",
            ),
        ] = None,
        eori_number: Annotated[
            str | None,
            builder_param(
                "Third-party EORI number.",
                examples=["PL123456789000000"],
                priority="advanced",
            ),
        ] = None,
        buyer_id: Annotated[
            str | None,
            builder_param(
                "Buyer identifier linked to the third party when required.",
                examples=["buyer-42"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        address = None
        if address_line_1 is not None:
            # Allow building address with just address_line_1 and optionally address_line_2
            # country_code and gln are not required
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
            if correspondence_address_line_1 is None:
                raise ValueError(
                    "correspondence_address_line_1 is required when providing a correspondence address."
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
        if address_line_1:
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
        country_code: str | None,
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
