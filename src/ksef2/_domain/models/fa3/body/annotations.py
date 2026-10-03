"""FA(3) invoice annotation domain models."""

from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

from ksef2._domain.models import KSeFBaseModel


class MarginProcedure(StrEnum):
    """Margin procedure variants supported by FA(3) annotations."""

    TRAVEL_AGENCY = "travel_agency"
    USED_GOODS = "used_goods"
    ARTWORKS = "artworks"
    COLLECTIBLES_AND_ANTIQUES = "collectibles_and_antiques"


class InvoiceTaxExemption(KSeFBaseModel):
    """FA(3) invoice tax-exemption annotation.

    References:
        schemat.FakturaFaAdnotacjeZwolnienie

    Maps:
        legal_basis_act - p_19_a (str)
        legal_basis_eu_directive - p_19_b (str)
        legal_basis_other - p_19_c (str)
    """

    legal_basis_act: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_19_a: Legal basis from the VAT act or an act issued under it.",
    )
    """Legal basis in national law for the exemption (``P_19A``, 1–256 characters)."""
    legal_basis_eu_directive: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_19_b: Legal basis from Directive 2006/112/WE.",
    )
    """Legal basis in the EU VAT Directive for the exemption (``P_19B``, 1–256 characters)."""
    legal_basis_other: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_19_c: Other legal basis for the exemption.",
    )
    """Other legal basis for the exemption (``P_19C``, 1–256 characters)."""

    @model_validator(mode="after")
    def validate_single_basis(self) -> "InvoiceTaxExemption":
        """Require exactly one exemption legal basis.

        Returns:
            The validated exemption.

        Raises:
            ValueError: If none or more than one legal basis is set.
        """
        provided_bases = [
            self.legal_basis_act,
            self.legal_basis_eu_directive,
            self.legal_basis_other,
        ]
        if sum(value is not None for value in provided_bases) != 1:
            raise ValueError("Exactly one exemption legal basis must be provided")
        return self


class NewTransportMeansItem(KSeFBaseModel):
    """FA(3) new means of transport annotation line.

    References:
        schemat.FakturaFaAdnotacjeNoweSrodkiTransportuNowySrodekTransportu

    Maps:
        available_from - p_22_a (date)
        row_number - p_nr_wiersza_nst (int)
        brand - p_22_bmk (str)
        model - p_22_bmd (str)
        color - p_22_bk (str)
        registration_number - p_22_bnr (str)
        production_year - p_22_brp (str)
        land_vehicle_mileage - p_22_b (str)
        vin - p_22_b1 (str)
        body_number - p_22_b2 (str)
        chassis_number - p_22_b3 (str)
        frame_number - p_22_b4 (str)
        land_vehicle_type - p_22_bt (str)
        vessel_working_hours - p_22_c (str)
        hull_number - p_22_c1 (str)
        aircraft_working_hours - p_22_d (str)
        aircraft_serial_number - p_22_d1 (str)
    """

    available_from: date = Field(
        description="p_22_a: Date when the new means of transport was put into use."
    )
    """Date the new means of transport was put into service (``P_22A``)."""
    row_number: int = Field(
        gt=0,
        description="p_nr_wiersza_nst: Invoice row number covering the supply.",
    )
    """Number of the invoice row this item refers to (``P_NrWierszaNST``); greater than zero."""
    brand: str | None = Field(default=None, min_length=1, max_length=256)
    """Brand of the new means of transport (``P_22BMK``)."""
    model: str | None = Field(default=None, min_length=1, max_length=256)
    """Model of the new means of transport (``P_22BMD``)."""
    color: str | None = Field(default=None, min_length=1, max_length=256)
    """Color of the new means of transport (``P_22BK``)."""
    registration_number: str | None = Field(default=None, min_length=1, max_length=256)
    """Registration number of the new means of transport (``P_22BNR``)."""
    production_year: str | None = Field(default=None, min_length=1, max_length=256)
    """Year of production of the new means of transport (``P_22BRP``)."""
    land_vehicle_mileage: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_b: Mileage for land vehicles.",
    )
    """Mileage of a land vehicle (``P_22B``); required for land vehicles."""
    vin: str | None = Field(default=None, min_length=1, max_length=256)
    """VIN of a land vehicle (``P_22B1``)."""
    body_number: str | None = Field(default=None, min_length=1, max_length=256)
    """Body number of a land vehicle (``P_22B2``)."""
    chassis_number: str | None = Field(default=None, min_length=1, max_length=256)
    """Chassis number of a land vehicle (``P_22B3``)."""
    frame_number: str | None = Field(default=None, min_length=1, max_length=256)
    """Frame number of a land vehicle (``P_22B4``)."""
    land_vehicle_type: str | None = Field(default=None, min_length=1, max_length=256)
    """Type of a land vehicle (``P_22BT``)."""
    vessel_working_hours: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_c: Working hours for vessels.",
    )
    """Working hours of a vessel (``P_22C``); required for vessels."""
    hull_number: str | None = Field(default=None, min_length=1, max_length=256)
    """Hull number of a vessel (``P_22C1``)."""
    aircraft_working_hours: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_d: Working hours for aircraft.",
    )
    """Working hours of an aircraft (``P_22D``); required for aircraft."""
    aircraft_serial_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
    )
    """Serial number of an aircraft (``P_22D1``)."""


class NewTransportSupply(KSeFBaseModel):
    """FA(3) annotation for intra-Community supply of new means of transport.

    References:
        schemat.FakturaFaAdnotacjeNoweSrodkiTransportu

    Maps:
        article_42_5_required - p_42_5 (bool)
        items - nowy_srodek_transportu (list[NewTransportMeansItem])
    """

    article_42_5_required: bool | None = Field(
        default=None,
        description="p_42_5: Indicates whether the reporting obligation from art. 42 ust. 5 applies.",
    )
    """Whether the supplier is required to fulfil the obligations of article 42(5) of the VAT Act (``P_42_5``)."""
    items: list[NewTransportMeansItem] = Field(
        min_length=1,
        max_length=10000,
        description="nowy_srodek_transportu: Detailed supplied new means of transport.",
    )
    """New means of transport supplied (1–10000)."""


class InvoiceAnnotationsContext(KSeFBaseModel):
    """FA(3) invoice annotations stored in ``Fa/Adnotacje``.

    References:
        schemat.FakturaFaAdnotacje

    Maps:
        cash_accounting - p_16 (bool)
        self_billing - p_17 (bool)
        reverse_charge_annotation - p_18 (bool)
        split_payment - p_18_a (bool)
        tax_exemption - zwolnienie (InvoiceTaxExemption)
        new_transport_supply - nowe_srodki_transportu (NewTransportSupply)
        simplified_procedure - p_23 (bool)
        margin_procedure - pmarzy (MarginProcedure)
    """

    cash_accounting: bool = Field(
        default=False,
        description='p_16: Marks the invoice with the "metoda kasowa" annotation.',
    )
    """Marks the cash accounting method (``P_16``)."""
    self_billing: bool = Field(
        default=False,
        description='p_17: Marks the invoice with the "samofakturowanie" annotation.',
    )
    """Marks self-billing, where the buyer issues the invoice (``P_17``)."""
    reverse_charge_annotation: bool = Field(
        default=False,
        description='p_18: Marks the invoice with the "odwrotne obciążenie" annotation.',
    )
    """Marks the reverse charge mechanism (``P_18``)."""
    split_payment: bool = Field(
        default=False,
        description='p_18_a: Marks the invoice with the "mechanizm podzielonej płatności" annotation.',
    )
    """Marks the split payment mechanism (``P_18A``)."""
    tax_exemption: InvoiceTaxExemption | None = Field(
        default=None,
        description="zwolnienie: VAT-exemption legal basis annotation.",
    )
    """VAT exemption legal bases (``Zwolnienie``)."""
    new_transport_supply: NewTransportSupply | None = Field(
        default=None,
        description="nowe_srodki_transportu: Intra-Community supply of new means of transport.",
    )
    """Intra-Community supply of new means of transport (``NoweSrodkiTransportu``)."""
    simplified_procedure: bool = Field(
        default=False,
        description="p_23: Marks the simplified-procedure annotation.",
    )
    """Marks the simplified procedure for triangular transactions (``P_23``)."""
    margin_procedure: MarginProcedure | None = Field(
        default=None,
        description="pmarzy: Margin procedure flag.",
    )
    """Margin procedure variant (``PMarzy``)."""
