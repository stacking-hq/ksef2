"""Fluent builder for FA(3) transaction condition blocks."""

from datetime import date, datetime
from decimal import Decimal
from collections.abc import Sequence
from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import TransactionConditions
from ksef2.domain.models.fa3.body import (
    CargoType,
    TransactionAddress,
    TransactionContract,
    TransactionIdentity,
    TransactionOrder,
    TransactionTransport,
    TransportType,
)
from ksef2.services.builders.fa3.metadata import builder_param


class TransactionState(TypedDict):
    """Typed state for Transaction fields."""

    contracts: list[TransactionContract]
    orders: list[TransactionOrder]
    lot_numbers: list[str]
    delivery_terms: str | None
    contract_exchange_rate: Decimal | None
    contract_currency: str | None
    transports: list[TransactionTransport]
    intermediary_entity: bool


adapter = TypeAdapter(TransactionState)


def _default_state() -> TransactionState:
    return {
        "contracts": [],
        "orders": [],
        "lot_numbers": [],
        "delivery_terms": None,
        "contract_exchange_rate": None,
        "contract_currency": None,
        "transports": [],
        "intermediary_entity": False,
    }


class TransactionBuilder[TParent]:
    """Fluent builder for FA(3) transaction conditions."""

    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[TransactionConditions], None],
        existing_state: TransactionConditions | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: TransactionState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, transaction: TransactionConditions) -> Self:
        """Replace the builder state from an existing domain model."""
        self._state = adapter.validate_python(transaction.model_dump())
        return self

    def delivery_terms(
        self,
        value: Annotated[
            str | None,
            builder_param(
                "Delivery terms agreed for the transaction.",
                examples=["DAP Berlin", "EXW warehouse"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        """Set the delivery terms value."""
        self._state["delivery_terms"] = value
        return self

    def contract_exchange(
        self,
        *,
        rate: Annotated[
            Decimal | None,
            builder_param(
                "Contract exchange rate used in the transaction section.",
                examples=["4.2512"],
                format="decimal-string",
                priority="advanced",
            ),
        ] = None,
        currency: Annotated[
            str | None,
            builder_param(
                "Contract currency used in the transaction section.",
                examples=["EUR", "USD"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Set the contract exchange value."""
        self._state["contract_exchange_rate"] = rate
        self._state["contract_currency"] = currency
        return self

    def intermediary_entity(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the transaction as involving an intermediary entity.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        """Set the intermediary entity value."""
        self._state["intermediary_entity"] = enabled
        return self

    def add_contract(
        self,
        *,
        contract_date: Annotated[
            date | None,
            builder_param(
                "Date of the related contract.",
                examples=["2026-04-01"],
                format="date",
                priority="advanced",
            ),
        ] = None,
        contract_number: Annotated[
            str | None,
            builder_param(
                "Number of the related contract.",
                examples=["CTR/2026/04/01"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Add a contract entry."""
        self._state["contracts"].append(
            TransactionContract(
                contract_date=contract_date,
                contract_number=contract_number,
            )
        )
        return self

    def add_contract_model(self, contract: TransactionContract) -> Self:
        """Add an existing transaction contract model."""
        self._state["contracts"].append(contract)
        return self

    def clear_contracts(self) -> Self:
        """Remove all transaction contracts."""
        self._state["contracts"].clear()
        return self

    def add_order(
        self,
        *,
        order_date: Annotated[
            date | None,
            builder_param(
                "Date of the related order.",
                examples=["2026-04-02"],
                format="date",
                priority="advanced",
            ),
        ] = None,
        order_number: Annotated[
            str | None,
            builder_param(
                "Number of the related order.",
                examples=["ORD/2026/04/15"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Add an order reference entry."""
        self._state["orders"].append(
            TransactionOrder(
                order_date=order_date,
                order_number=order_number,
            )
        )
        return self

    def add_order_model(self, order: TransactionOrder) -> Self:
        """Add an existing transaction order model."""
        self._state["orders"].append(order)
        return self

    def clear_orders(self) -> Self:
        """Remove all transaction orders."""
        self._state["orders"].clear()
        return self

    def add_lot_number(
        self,
        value: Annotated[
            str,
            builder_param(
                "Lot or batch number linked to the transaction.",
                examples=["LOT-2026-04-01"],
                priority="advanced",
            ),
        ],
    ) -> Self:
        """Add a lot number entry."""
        self._state["lot_numbers"].append(value)
        return self

    def clear_lot_numbers(self) -> Self:
        """Remove all lot numbers."""
        self._state["lot_numbers"].clear()
        return self

    def add_transport(
        self,
        *,
        transport_type: Annotated[
            TransportType | None,
            builder_param(
                "Transport type used for the shipment.",
                examples=["road", "sea"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
        other_transport: Annotated[
            bool,
            builder_param(
                "Set to true when the shipment uses a transport type outside the predefined enum.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        other_transport_description: Annotated[
            str | None,
            builder_param(
                "Free-text description of the transport type when other_transport is enabled.",
                examples=["Courier locker delivery"],
                priority="advanced",
            ),
        ] = None,
        carrier_identity: Annotated[
            TransactionIdentity | None,
            builder_param(
                "Carrier identity information stored in the transaction section.",
                examples=[],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.TransactionIdentity",
            ),
        ] = None,
        carrier_address: Annotated[
            TransactionAddress | None,
            builder_param(
                "Carrier address stored in the transaction section.",
                examples=[],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.TransactionAddress",
            ),
        ] = None,
        transport_order_number: Annotated[
            str | None,
            builder_param(
                "Transport order number linked to the shipment.",
                examples=["TRN/2026/04/22"],
                priority="advanced",
            ),
        ] = None,
        cargo_type: Annotated[
            CargoType | None,
            builder_param(
                "Cargo type used for the shipment.",
                examples=["parcel", "bulk"],
                format="enum-string",
                priority="advanced",
            ),
        ] = None,
        other_cargo: Annotated[
            bool,
            builder_param(
                "Set to true when the cargo type is described manually instead of using the predefined enum.",
                examples=[False],
                priority="advanced",
            ),
        ] = False,
        other_cargo_description: Annotated[
            str | None,
            builder_param(
                "Free-text description of the cargo type when other_cargo is enabled.",
                examples=["Mixed electronics"],
                priority="advanced",
            ),
        ] = None,
        packaging_unit: Annotated[
            str | None,
            builder_param(
                "Packaging unit used for the shipment.",
                examples=["pallet", "box"],
                priority="advanced",
            ),
        ] = None,
        transport_start: Annotated[
            datetime | None,
            builder_param(
                "Start timestamp of the transport.",
                examples=["2026-04-08T08:00:00+02:00"],
                format="date-time",
                priority="advanced",
            ),
        ] = None,
        transport_end: Annotated[
            datetime | None,
            builder_param(
                "End timestamp of the transport.",
                examples=["2026-04-09T14:30:00+02:00"],
                format="date-time",
                priority="advanced",
            ),
        ] = None,
        shipping_from: Annotated[
            TransactionAddress | None,
            builder_param(
                "Shipping origin address.",
                examples=[],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.TransactionAddress",
            ),
        ] = None,
        shipping_via: Annotated[
            Sequence[TransactionAddress] | None,
            builder_param(
                "Intermediate shipping locations.",
                examples=[],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.TransactionAddress",
            ),
        ] = None,
        shipping_to: Annotated[
            TransactionAddress | None,
            builder_param(
                "Final shipping destination address.",
                examples=[],
                format="object",
                priority="advanced",
                schema_ref="ksef2.domain.models.fa3.body.TransactionAddress",
            ),
        ] = None,
    ) -> Self:
        """Add a transport entry."""
        self._state["transports"].append(
            TransactionTransport(
                transport_type=transport_type,
                other_transport=other_transport,
                other_transport_description=other_transport_description,
                carrier_identity=carrier_identity,
                carrier_address=carrier_address,
                transport_order_number=transport_order_number,
                cargo_type=cargo_type,
                other_cargo=other_cargo,
                other_cargo_description=other_cargo_description,
                packaging_unit=packaging_unit,
                transport_start=transport_start,
                transport_end=transport_end,
                shipping_from=shipping_from,
                shipping_via=list(shipping_via or []),
                shipping_to=shipping_to,
            )
        )
        return self

    def add_transport_model(self, transport: TransactionTransport) -> Self:
        """Add an existing transport detail model."""
        self._state["transports"].append(transport)
        return self

    def clear_transports(self) -> Self:
        """Remove all transport details."""
        self._state["transports"].clear()
        return self

    def build(self) -> TransactionConditions:
        """Build the corresponding FA(3) domain model."""
        return TransactionConditions(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        """Attach the built transaction details to the parent builder and return it.

        Raises:
            ValueError: If transaction details are empty.
        """
        if self._is_empty():
            raise ValueError(
                "Transaction details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class TransactionBuilderMixin:
    """Mixin exposing the Transaction sub-builder."""

    _transaction_conditions: TransactionConditions | None = None

    def transaction(self) -> TransactionBuilder[Self]:
        """Start a transaction-conditions sub-builder."""
        return TransactionBuilder(
            self, self._set_transaction, self._transaction_conditions
        )

    def _set_transaction(self, value: TransactionConditions) -> None:
        self._transaction_conditions = value
