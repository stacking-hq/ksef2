"""Unit tests for the FA(3) transaction sub-builder reached from the public builder."""

from datetime import UTC, datetime, date
from decimal import Decimal
from typing import Any

import pytest

from ksef2.fa3 import FA3InvoiceBuilder, VatRate
from ksef2._domain.models.fa3.body import (
    TransactionAddress,
    TransactionConditions,
    TransactionContract,
    TransactionIdentity,
    TransactionOrder,
    TransactionTransport,
)
from ksef2._services.builders.fa3.sub.transaction import TransactionBuilder


def started_standard_body() -> Any:
    """Open a standard body on an invoice whose header, seller and buyer are set."""
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
    return builder.standard()


def address(line: str) -> TransactionAddress:
    return TransactionAddress(country_code="pl", address_line_1=line)


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


def test_transaction_starts_empty() -> None:
    transaction = started_standard_body().transaction().build()

    assert transaction.contracts == []
    assert transaction.orders == []
    assert transaction.lot_numbers == []
    assert transaction.delivery_terms is None
    assert transaction.contract_exchange_rate is None
    assert transaction.contract_currency is None
    assert transaction.transports == []
    assert transaction.intermediary_entity is False


def test_delivery_terms_can_be_set_and_overwritten() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .delivery_terms("DAP Berlin")
        .delivery_terms("EXW warehouse")
        .build()
    )

    assert transaction.delivery_terms == "EXW warehouse"


def test_contract_exchange_normalizes_the_currency() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .contract_exchange(rate=Decimal("4.2512"), currency="eur")
        .build()
    )

    assert transaction.contract_exchange_rate == Decimal("4.2512")
    assert transaction.contract_currency == "EUR"


def test_contract_exchange_accepts_no_arguments() -> None:
    transaction = started_standard_body().transaction().contract_exchange().build()

    assert transaction.contract_exchange_rate is None
    assert transaction.contract_currency is None


def test_contract_exchange_without_currency_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="must be provided together"):
        _ = (
            started_standard_body()
            .transaction()
            .contract_exchange(rate=Decimal("4.2512"))
            .build()
        )


def test_contract_currency_cannot_be_pln() -> None:
    with pytest.raises(ValueError, match="cannot be PLN"):
        _ = (
            started_standard_body()
            .transaction()
            .contract_exchange(rate=Decimal("1"), currency="PLN")
            .build()
        )


def test_intermediary_entity_defaults_to_enabled_and_can_be_disabled() -> None:
    transaction = started_standard_body().transaction().intermediary_entity().build()
    disabled = started_standard_body().transaction().intermediary_entity(False).build()

    assert transaction.intermediary_entity is True
    assert disabled.intermediary_entity is False


def test_add_contract_accepts_date_and_number() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .add_contract(contract_date=date(2026, 4, 1), contract_number="CTR/2026/04")
        .build()
    )

    assert transaction.contracts == [
        TransactionContract(
            contract_date=date(2026, 4, 1), contract_number="CTR/2026/04"
        )
    ]


def test_add_contract_with_nothing_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="contract_date or contract_number"):
        _ = started_standard_body().transaction().add_contract().build()


def test_add_order_accepts_date_and_number() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .add_order(order_date=date(2026, 4, 2), order_number="ORD/2026/04/15")
        .build()
    )

    assert transaction.orders == [
        TransactionOrder(order_date=date(2026, 4, 2), order_number="ORD/2026/04/15")
    ]


def test_add_order_with_nothing_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="order_date or order_number"):
        _ = started_standard_body().transaction().add_order().build()


def test_add_contract_model_and_add_order_model_take_existing_models() -> None:
    contract = TransactionContract(contract_number="CTR/1")
    order = TransactionOrder(order_number="ORD/1")

    transaction = (
        started_standard_body()
        .transaction()
        .add_contract_model(contract)
        .add_order_model(order)
        .build()
    )

    assert transaction.contracts == [contract]
    assert transaction.orders == [order]


def test_add_lot_number_accumulates() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .add_lot_number("LOT-2026-04-01")
        .add_lot_number("LOT-2026-04-02")
        .build()
    )

    assert transaction.lot_numbers == ["LOT-2026-04-01", "LOT-2026-04-02"]


def test_clear_methods_remove_only_their_own_collection() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .add_contract(contract_number="CTR/1")
        .clear_contracts()
        .add_order(order_number="ORD/1")
        .clear_orders()
        .add_lot_number("LOT-1")
        .clear_lot_numbers()
        .add_transport(transport_type="road")
        .clear_transports()
        .delivery_terms("EXW")
        .build()
    )

    assert transaction.contracts == []
    assert transaction.orders == []
    assert transaction.lot_numbers == []
    assert transaction.transports == []
    assert transaction.delivery_terms == "EXW"


def test_add_transport_maps_every_shipment_field() -> None:
    carrier_identity = TransactionIdentity(
        name="SPEDITOR Sp. z o.o.", tax_id="1234567890"
    )
    carrier_address = address("ul. Transportowa 4")

    transport = (
        started_standard_body()
        .transaction()
        .add_transport(
            transport_type="road",
            carrier_identity=carrier_identity,
            carrier_address=carrier_address,
            transport_order_number="TRN/2026-04-22",
            cargo_type="parcel",
            packaging_unit="pallet",
            transport_start=datetime(2026, 4, 8, 8, tzinfo=UTC),
            transport_end=datetime(2026, 4, 9, 14, 30, tzinfo=UTC),
            shipping_from=address("ul. Nadawcy 1"),
            shipping_via=[address("ul. Przesiadki 2")],
            shipping_to=address("Unter den Linden 1"),
        )
        .build()
        .transports[0]
    )

    assert transport.transport_type == "road"
    assert transport.other_transport is False
    assert transport.carrier_identity == carrier_identity
    assert transport.carrier_address == carrier_address
    assert transport.transport_order_number == "TRN/2026-04-22"
    assert transport.cargo_type == "parcel"
    assert transport.other_cargo is False
    assert transport.packaging_unit == "pallet"
    assert transport.transport_start == datetime(2026, 4, 8, 8, tzinfo=UTC)
    assert transport.transport_end == datetime(2026, 4, 9, 14, 30, tzinfo=UTC)
    assert transport.shipping_from == address("ul. Nadawcy 1")
    assert transport.shipping_via == [address("ul. Przesiadki 2")]
    assert transport.shipping_to == address("Unter den Linden 1")


def test_add_transport_without_a_type_uses_other_transport_description() -> None:
    transport = (
        started_standard_body()
        .transaction()
        .add_transport(
            other_transport=True,
            other_transport_description="Courier locker delivery",
            other_cargo=True,
            other_cargo_description="Mixed electronics",
        )
        .build()
        .transports[0]
    )

    assert transport.transport_type is None
    assert transport.other_transport is True
    assert transport.other_transport_description == "Courier locker delivery"
    assert transport.cargo_type is None
    assert transport.other_cargo is True
    assert transport.other_cargo_description == "Mixed electronics"


def test_add_transport_with_an_unknown_type_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="transport_type"):
        _ = (
            started_standard_body()
            .transaction()
            .add_transport(
                transport_type="hovercraft"  # type: ignore[arg-type]
            )
            .build()
        )


def test_add_transport_with_an_inverted_period_is_rejected_on_build() -> None:
    with pytest.raises(ValueError, match="cannot be later than transport_end"):
        _ = (
            started_standard_body()
            .transaction()
            .add_transport(
                transport_start=datetime(2026, 4, 9, 8, tzinfo=UTC),
                transport_end=datetime(2026, 4, 8, 8, tzinfo=UTC),
            )
            .build()
        )


def test_add_transport_model_adds_an_existing_model() -> None:
    transport = TransactionTransport(transport_type="sea")

    built = started_standard_body().transaction().add_transport_model(transport).build()

    assert built.transports == [transport]


def test_shipping_via_defaults_to_an_empty_list_per_transport() -> None:
    transaction = (
        started_standard_body()
        .transaction()
        .add_transport(transport_type="road")
        .add_transport(transport_type="air")
        .build()
    )

    assert [list(t.shipping_via) for t in transaction.transports] == [[], []]


def test_from_model_replaces_the_whole_state() -> None:
    existing = TransactionConditions(
        contracts=[TransactionContract(contract_number="CTR/OLD")],
        lot_numbers=["LOT-OLD"],
        delivery_terms="DAP Warsaw",
    )

    transaction = (
        started_standard_body()
        .transaction()
        .add_contract(contract_number="CTR/NEW")
        .from_model(existing)
        .build()
    )

    assert transaction == existing


def test_builder_does_not_mutate_the_model_it_was_seeded_from() -> None:
    existing = TransactionConditions(lot_numbers=["LOT-OLD"])

    _ = (
        started_standard_body()
        .transaction()
        .from_model(existing)
        .add_lot_number("LOT-NEW")
        .build()
    )

    assert existing.lot_numbers == ["LOT-OLD"]


def test_done_attaches_the_transaction_to_the_body() -> None:
    body = started_standard_body()
    with_one_line(body)

    returned = body.transaction().add_lot_number("LOT-1").done()

    assert returned is body
    built = body.build()
    assert built.transaction_conditions is not None
    assert built.transaction_conditions.lot_numbers == ["LOT-1"]


def test_done_on_an_empty_transaction_is_rejected() -> None:
    with pytest.raises(ValueError, match="Transaction details are empty"):
        _ = started_standard_body().transaction().done()


def test_done_is_rejected_when_clearing_empties_the_transaction() -> None:
    with pytest.raises(ValueError, match="Transaction details are empty"):
        _ = (
            started_standard_body()
            .transaction()
            .add_lot_number("LOT-1")
            .clear_lot_numbers()
            .done()
        )


def test_intermediary_entity_alone_is_enough_for_done() -> None:
    body = started_standard_body()
    with_one_line(body)

    _ = body.transaction().intermediary_entity().done()

    assert body.build().transaction_conditions.intermediary_entity is True


def test_reopening_the_sub_builder_keeps_the_attached_transaction() -> None:
    body = started_standard_body()
    with_one_line(body)
    _ = body.transaction().add_lot_number("LOT-1").done()

    transaction = body.transaction().add_contract(contract_number="CTR/1").build()

    assert transaction.lot_numbers == ["LOT-1"]
    assert [contract.contract_number for contract in transaction.contracts] == ["CTR/1"]


def test_settlement_and_transaction_blocks_are_independent() -> None:
    body = started_standard_body()
    with_one_line(body)
    _ = body.transaction().add_lot_number("LOT-1").done()
    _ = body.settlement().add_charge(amount=Decimal("10.00"), reason="Freight").done()

    built = body.build()

    assert built.transaction_conditions is not None
    assert built.transaction_conditions.lot_numbers == ["LOT-1"]
    assert built.settlement is not None
    assert built.settlement.charges_total == Decimal("10.00")


def test_standalone_builder_can_be_used_without_a_parent() -> None:
    built: list[TransactionConditions] = []
    builder: TransactionBuilder[None] = TransactionBuilder(None, built.append)

    returned = builder.delivery_terms("EXW").done()

    assert returned is None
    assert [t.delivery_terms for t in built] == ["EXW"]


def test_existing_state_seeds_the_constructor_directly() -> None:
    existing = TransactionConditions(
        contracts=[TransactionContract(contract_number="C")]
    )

    builder: TransactionBuilder[None] = TransactionBuilder(
        None, lambda _value: None, existing
    )

    assert builder.build() == existing
