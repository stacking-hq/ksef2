"""Mappings from FA(3) annotation schema models to domain objects."""

from datetime import date, datetime
from functools import singledispatch
from typing import overload

from ksef2.domain.models.fa3.body import (
    InvoiceAnnotationsContext,
    InvoiceTaxExemption,
    MarginProcedure,
    NewTransportMeansItem,
    NewTransportSupply,
)
from ksef2.infra.schema.fa3.models.elementarne_typy_danych_v10_0_e import (
    Twybor12,
)
from ksef2.infra.schema.fa3.models.schemat import FakturaFaAdnotacje


@overload
def from_spec(
    schema: FakturaFaAdnotacje | None,
) -> InvoiceAnnotationsContext | None: ...


@overload
def from_spec(schema: object) -> object: ...


def from_spec(schema: object) -> object:
    """Convert FA(3) annotation schema into the domain model."""
    return _from_spec(schema)


@singledispatch
def _from_spec(schema: object) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(schema).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(schema: FakturaFaAdnotacje) -> InvoiceAnnotationsContext | None:
    margin_procedure: MarginProcedure | None = None
    if schema.pmarzy is not None:
        if schema.pmarzy.p_pmarzy_2 is not None:
            margin_procedure = MarginProcedure.TRAVEL_AGENCY
        elif schema.pmarzy.p_pmarzy_3_1 is not None:
            margin_procedure = MarginProcedure.USED_GOODS
        elif schema.pmarzy.p_pmarzy_3_2 is not None:
            margin_procedure = MarginProcedure.ARTWORKS
        elif schema.pmarzy.p_pmarzy_3_3 is not None:
            margin_procedure = MarginProcedure.COLLECTIBLES_AND_ANTIQUES

    has_non_default = margin_procedure is not None or any(
        [
            schema.p_16 == Twybor12.VALUE_1,
            schema.p_17 == Twybor12.VALUE_1,
            schema.p_18 == Twybor12.VALUE_1,
            schema.p_18_a == Twybor12.VALUE_1,
            schema.p_23 == Twybor12.VALUE_1,
            schema.zwolnienie is not None and schema.zwolnienie.p_19 is not None,
            schema.nowe_srodki_transportu is not None
            and (
                schema.nowe_srodki_transportu.p_22 is not None
                or schema.nowe_srodki_transportu.nowy_srodek_transportu
            ),
        ]
    )
    if not has_non_default:
        return None

    tax_exemption = None
    if schema.zwolnienie is not None and schema.zwolnienie.p_19 is not None:
        tax_exemption = InvoiceTaxExemption(
            legal_basis_act=schema.zwolnienie.p_19_a,
            legal_basis_eu_directive=schema.zwolnienie.p_19_b,
            legal_basis_other=schema.zwolnienie.p_19_c,
        )

    new_transport_supply = None
    if schema.nowe_srodki_transportu is not None:
        transport = schema.nowe_srodki_transportu
        if transport.p_22 is not None or transport.nowy_srodek_transportu:
            items = []
            for item in transport.nowy_srodek_transportu:
                raw_date = item.p_22_a
                if isinstance(raw_date, datetime):
                    available_from = raw_date.date()
                elif isinstance(raw_date, date):
                    available_from = raw_date
                else:
                    raw_str = str(raw_date)
                    try:
                        available_from = date.fromisoformat(raw_str)
                    except ValueError:
                        available_from = datetime.fromisoformat(raw_str).date()
                items.append(
                    NewTransportMeansItem(
                        available_from=available_from,
                        row_number=item.p_nr_wiersza_nst,
                        brand=item.p_22_bmk,
                        model=item.p_22_bmd,
                        color=item.p_22_bk,
                        registration_number=item.p_22_bnr,
                        production_year=item.p_22_brp,
                        land_vehicle_mileage=item.p_22_b,
                        vin=item.p_22_b1,
                        body_number=item.p_22_b2,
                        chassis_number=item.p_22_b3,
                        frame_number=item.p_22_b4,
                        land_vehicle_type=item.p_22_bt,
                        vessel_working_hours=item.p_22_c,
                        hull_number=item.p_22_c1,
                        aircraft_working_hours=item.p_22_d,
                        aircraft_serial_number=item.p_22_d1,
                    )
                )
            new_transport_supply = NewTransportSupply(
                article_42_5_required=transport.p_42_5 == Twybor12.VALUE_1
                if transport.p_42_5 is not None
                else None,
                items=items,
            )

    return InvoiceAnnotationsContext(
        cash_accounting=schema.p_16 == Twybor12.VALUE_1,
        self_billing=schema.p_17 == Twybor12.VALUE_1,
        reverse_charge_annotation=schema.p_18 == Twybor12.VALUE_1,
        split_payment=schema.p_18_a == Twybor12.VALUE_1,
        simplified_procedure=schema.p_23 == Twybor12.VALUE_1,
        margin_procedure=margin_procedure,
        tax_exemption=tax_exemption,
        new_transport_supply=new_transport_supply,
    )


__all__ = ["from_spec"]
