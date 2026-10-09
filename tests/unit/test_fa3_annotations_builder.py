"""Unit tests for the fluent FA(3) annotations builder reached from the public builder."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from ksef2.fa3 import FA3InvoiceBuilder, VatRate
from ksef2._domain.models.fa3.body import (
    InvoiceAnnotationsContext,
    MarginProcedure,
    NewTransportMeansItem,
    NewTransportSupply,
)
from ksef2._services.builders.fa3.sub.annotations import AnnotationsBuilder


def started_standard_body() -> tuple[FA3InvoiceBuilder, Any]:
    builder = FA3InvoiceBuilder()
    _ = builder.header(system_info="billing-service")
    _ = builder.seller(
        name="ACME S.A.",
        tax_id="1234567890",
        country_code="PL",
        address_line_1="ul. Przykladowa 123",
    )
    _ = builder.buyer(
        name="XYZ GmbH",
        country_code="PL",
        address_line_1="Unter den Linden 1",
    )
    return builder, builder.standard()


def with_one_line(body: Any) -> None:
    """Close the rows and body sub-builders so the draft holds a complete body."""
    rows = body.rows().add_line(
        name="Consulting service",
        unit_of_measure="h",
        quantity=Decimal("1"),
        unit_price_net=Decimal("100.00"),
        vat_rate=VatRate.VAT_23,
    )
    rows.done().done()


def test_annotations_start_empty() -> None:
    _, body = started_standard_body()

    annotations = body.annotations().build()

    assert annotations.cash_accounting is False
    assert annotations.self_billing is False
    assert annotations.reverse_charge_annotation is False
    assert annotations.split_payment is False
    assert annotations.simplified_procedure is False
    assert annotations.margin_procedure is None
    assert annotations.tax_exemption is None
    assert annotations.new_transport_supply is None


def test_annotation_flags_can_be_set_and_cleared() -> None:
    _, body = started_standard_body()

    annotations = (
        body.annotations()
        .cash_accounting()
        .self_billing(True)
        .reverse_charge_annotation()
        .split_payment()
        .simplified_procedure()
        .split_payment(False)
        .build()
    )

    assert annotations.cash_accounting is True
    assert annotations.self_billing is True
    assert annotations.reverse_charge_annotation is True
    assert annotations.split_payment is False
    assert annotations.simplified_procedure is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("travel_agency", MarginProcedure.TRAVEL_AGENCY),
        ("used_goods", MarginProcedure.USED_GOODS),
        (MarginProcedure.ARTWORKS, MarginProcedure.ARTWORKS),
        (None, None),
    ],
)
def test_margin_procedure_accepts_text_and_enum(
    value: MarginProcedure | str | None,
    expected: MarginProcedure | None,
) -> None:
    _, body = started_standard_body()

    annotations = body.annotations().margin_procedure(value).build()

    assert annotations.margin_procedure is expected


def test_tax_exemption_can_be_replaced_and_cleared() -> None:
    _, body = started_standard_body()

    annotations = (
        body.annotations()
        .tax_exemption(legal_basis_act="art. 43 ust. 1 pkt 10 ustawy")
        .tax_exemption(
            legal_basis_eu_directive="art. 132 Dyrektywy 2006/112/WE",
        )
        .build()
    )

    assert annotations.tax_exemption is not None
    assert annotations.tax_exemption.legal_basis_act is None
    assert annotations.tax_exemption.legal_basis_eu_directive == (
        "art. 132 Dyrektywy 2006/112/WE"
    )

    cleared = (
        body.annotations()
        .tax_exemption(legal_basis_other="umowa")
        .tax_exemption()
        .build()
    )

    assert cleared.tax_exemption is None
    assert (
        body.annotations()
        .tax_exemption(legal_basis_act="art. 43")
        .clear_tax_exemption()
        .build()
        .tax_exemption
        is None
    )


def test_tax_exemption_requires_exactly_one_legal_basis() -> None:
    _, body = started_standard_body()

    with pytest.raises(ValueError, match="Exactly one exemption legal basis"):
        body.annotations().tax_exemption(
            legal_basis_act="art. 43 ust. 1 pkt 10 ustawy",
            legal_basis_other="umowa miedzynarodowa",
        )


def test_new_transport_items_keep_every_field() -> None:
    _, body = started_standard_body()

    annotations = (
        body.annotations()
        .cash_accounting()
        .new_transport_supply(article_42_5_required=True)
        .add_new_transport_item(
            available_from=date(2026, 4, 1),
            row_number=1,
            brand="Tesla",
            model="Model Y",
            color="black",
            registration_number="WX12345",
            production_year="2026",
            land_vehicle_mileage="1200",
            vin="5YJYGDEE0MF123456",
            body_number="BODY-123",
            chassis_number="CHASSIS-123",
            frame_number="FRAME-123",
            land_vehicle_type="passenger car",
        )
        .add_new_transport_item(
            available_from=date(2026, 4, 2),
            row_number=2,
            vessel_working_hours="25",
            hull_number="HULL-123",
        )
        .add_new_transport_item(
            available_from=date(2026, 4, 3),
            row_number=3,
            aircraft_working_hours="40",
            aircraft_serial_number="AIR-123",
        )
        .build()
    )

    supply = annotations.new_transport_supply
    assert supply is not None
    assert supply.article_42_5_required is True
    assert len(supply.items) == 3
    first = supply.items[0]
    assert first.available_from == date(2026, 4, 1)
    assert first.row_number == 1
    assert first.brand == "Tesla"
    assert first.model == "Model Y"
    assert first.color == "black"
    assert first.registration_number == "WX12345"
    assert first.production_year == "2026"
    assert first.land_vehicle_mileage == "1200"
    assert first.vin == "5YJYGDEE0MF123456"
    assert first.body_number == "BODY-123"
    assert first.chassis_number == "CHASSIS-123"
    assert first.frame_number == "FRAME-123"
    assert first.land_vehicle_type == "passenger car"
    assert first.vessel_working_hours is None
    assert supply.items[1].hull_number == "HULL-123"
    assert supply.items[1].vessel_working_hours == "25"
    assert supply.items[2].aircraft_serial_number == "AIR-123"
    assert supply.items[2].aircraft_working_hours == "40"


def test_new_transport_items_can_be_added_from_models_and_cleared() -> None:
    _, body = started_standard_body()
    item = NewTransportMeansItem(available_from=date(2026, 4, 1), row_number=7)

    annotations = (
        body.annotations()
        .add_new_transport_item(available_from=date(2026, 4, 1), row_number=1)
        .clear_new_transport_items()
        .add_new_transport_item_model(item)
        .build()
    )

    assert annotations.new_transport_supply is not None
    assert annotations.new_transport_supply.items == [item]


def test_the_article_42_5_marker_without_items_is_rejected() -> None:
    """A supply needs at least one item, so the marker alone cannot be built."""
    _, body = started_standard_body()

    with pytest.raises(ValidationError, match="at least 1 item"):
        body.annotations().new_transport_supply(article_42_5_required=False).build()


def test_annotations_builder_from_model_replaces_the_state() -> None:
    existing = InvoiceAnnotationsContext(
        cash_accounting=True,
        margin_procedure=MarginProcedure.COLLECTIBLES_AND_ANTIQUES,
        new_transport_supply=NewTransportSupply(
            article_42_5_required=True,
            items=[
                NewTransportMeansItem(available_from=date(2026, 4, 1), row_number=1)
            ],
        ),
    )

    annotations = (
        AnnotationsBuilder(None, lambda value: None)
        .split_payment()
        .from_model(existing)
        .add_new_transport_item(available_from=date(2026, 4, 2), row_number=2)
        .build()
    )

    assert annotations.cash_accounting is True
    assert annotations.split_payment is False
    assert annotations.margin_procedure is MarginProcedure.COLLECTIBLES_AND_ANTIQUES
    assert annotations.new_transport_supply is not None
    assert [item.row_number for item in annotations.new_transport_supply.items] == [
        1,
        2,
    ]


def test_empty_annotations_cannot_be_attached() -> None:
    _, body = started_standard_body()

    with pytest.raises(ValueError, match="Annotation details are empty"):
        body.annotations().done()


def test_annotations_done_returns_the_parent_builder() -> None:
    builder, body = started_standard_body()

    parent = body.annotations().split_payment().cash_accounting().done()

    assert parent is body
    with_one_line(body)
    draft = builder.dump_state()
    assert draft.body is not None
    assert draft.body.annotations is not None
    assert draft.body.annotations.split_payment is True
    assert draft.body.annotations.cash_accounting is True


def test_reopening_the_annotations_builder_keeps_the_previous_state() -> None:
    builder, body = started_standard_body()
    _ = body.annotations().split_payment().done()

    annotations = body.annotations().cash_accounting().build()

    assert annotations.split_payment is True
    assert annotations.cash_accounting is True

    with_one_line(body)
    draft = builder.dump_state()
    assert draft.body is not None
    assert draft.body.annotations is not None
    assert draft.body.annotations.split_payment is True


def test_transport_only_annotations_can_be_attached() -> None:
    builder, body = started_standard_body()

    _ = (
        body.annotations()
        .add_new_transport_item(available_from=date(2026, 4, 1), row_number=1)
        .done()
    )

    with_one_line(body)
    draft = builder.dump_state()
    assert draft.body is not None
    assert draft.body.annotations is not None
    supply = draft.body.annotations.new_transport_supply
    assert supply is not None
    assert [item.row_number for item in supply.items] == [1]


def test_the_article_42_5_marker_alone_counts_as_annotation_details() -> None:
    """The marker is state, so ``done()`` proceeds and the missing items surface."""
    _, body = started_standard_body()
    annotations = body.annotations().new_transport_supply(article_42_5_required=True)

    with pytest.raises(ValidationError, match="at least 1 item"):
        annotations.done()


def test_cleared_transport_items_leave_the_annotations_empty() -> None:
    _, body = started_standard_body()
    annotations = (
        body.annotations()
        .add_new_transport_item(available_from=date(2026, 4, 1), row_number=1)
        .clear_new_transport_items()
    )

    with pytest.raises(ValueError, match="Annotation details are empty"):
        annotations.done()
