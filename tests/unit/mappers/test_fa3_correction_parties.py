from ksef2.domain.models.fa3 import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
    InvoiceAddress,
)
from ksef2.infra.mappers.invoices.fa3.domain.correction_party import to_spec
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import Twybor1
from ksef2.infra.schema.fa3.models.schemat import (
    FakturaFaPodmiot1K,
    FakturaFaPodmiot2K,
    TkodyKrajowUe,
)


def make_polish_address() -> InvoiceAddress:
    return InvoiceAddress(
        country_code="PL",
        address_line_1="Marszalkowska 10/5",
        address_line_2="00-001 Warszawa",
    )


def test_corrected_seller_to_spec_maps_prefix_and_identity() -> None:
    output = to_spec(
        CorrectedSellerEntity(
            vat_prefix="DE",
            tax_id="1234567890",
            name="Old Seller Sp. z o.o.",
            address=make_polish_address(),
        )
    )

    assert isinstance(output, FakturaFaPodmiot1K)
    assert output.prefiks_podatnika == TkodyKrajowUe.DE
    assert output.dane_identyfikacyjne.nip == "1234567890"
    assert output.dane_identyfikacyjne.nazwa == "Old Seller Sp. z o.o."
    assert output.adres.adres_l1 == "Marszalkowska 10/5"


def test_corrected_buyer_to_spec_maps_optional_address_and_link_id() -> None:
    output = to_spec(
        CorrectedBuyerEntity(
            eu_vat_id="DE123456789",
            name="Old Buyer GmbH",
            buyer_id="BUYER-1",
            no_id=False,
        )
    )

    assert isinstance(output, FakturaFaPodmiot2K)
    assert output.dane_identyfikacyjne.kod_ue == TkodyKrajowUe.DE
    assert output.dane_identyfikacyjne.nr_vat_ue == "123456789"
    assert output.dane_identyfikacyjne.brak_id is None
    assert output.idnabywcy == "BUYER-1"
    assert output.adres is None


def test_corrected_buyer_to_spec_maps_no_id_flag() -> None:
    output = to_spec(
        CorrectedBuyerEntity(
            no_id=True,
            name="Anonymous Buyer",
        )
    )

    assert output.dane_identyfikacyjne.brak_id == Twybor1.VALUE_1
