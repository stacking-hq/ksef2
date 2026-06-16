"""FA(3) new means of transport annotation models."""

from datetime import date

from pydantic import Field

from ksef2.domain.models import KSeFBaseModel


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
    row_number: int = Field(
        gt=0,
        description="p_nr_wiersza_nst: Invoice row number covering the supply.",
    )
    brand: str | None = Field(default=None, min_length=1, max_length=256)
    model: str | None = Field(default=None, min_length=1, max_length=256)
    color: str | None = Field(default=None, min_length=1, max_length=256)
    registration_number: str | None = Field(default=None, min_length=1, max_length=256)
    production_year: str | None = Field(default=None, min_length=1, max_length=256)
    land_vehicle_mileage: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_b: Mileage for land vehicles.",
    )
    vin: str | None = Field(default=None, min_length=1, max_length=256)
    body_number: str | None = Field(default=None, min_length=1, max_length=256)
    chassis_number: str | None = Field(default=None, min_length=1, max_length=256)
    frame_number: str | None = Field(default=None, min_length=1, max_length=256)
    land_vehicle_type: str | None = Field(default=None, min_length=1, max_length=256)
    vessel_working_hours: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_c: Working hours for vessels.",
    )
    hull_number: str | None = Field(default=None, min_length=1, max_length=256)
    aircraft_working_hours: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="p_22_d: Working hours for aircraft.",
    )
    aircraft_serial_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
    )


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
    items: list[NewTransportMeansItem] = Field(
        min_length=1,
        max_length=10000,
        description="nowy_srodek_transportu: Detailed supplied new means of transport.",
    )
