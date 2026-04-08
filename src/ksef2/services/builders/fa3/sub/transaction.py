from datetime import date, datetime
from decimal import Decimal
from collections.abc import Sequence
from typing import Callable, Self, TypedDict

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


class TransactionState(TypedDict):
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
        self._state = adapter.validate_python(transaction.model_dump())
        return self

    def delivery_terms(self, value: str | None) -> Self:
        self._state["delivery_terms"] = value
        return self

    def contract_exchange(
        self, *, rate: Decimal | None = None, currency: str | None = None
    ) -> Self:
        self._state["contract_exchange_rate"] = rate
        self._state["contract_currency"] = currency
        return self

    def intermediary_entity(self, enabled: bool = True) -> Self:
        self._state["intermediary_entity"] = enabled
        return self

    def add_contract(
        self, *, contract_date: date | None = None, contract_number: str | None = None
    ) -> Self:
        self._state["contracts"].append(
            TransactionContract(
                contract_date=contract_date,
                contract_number=contract_number,
            )
        )
        return self

    def add_contract_model(self, contract: TransactionContract) -> Self:
        self._state["contracts"].append(contract)
        return self

    def clear_contracts(self) -> Self:
        self._state["contracts"].clear()
        return self

    def add_order(
        self, *, order_date: date | None = None, order_number: str | None = None
    ) -> Self:
        self._state["orders"].append(
            TransactionOrder(
                order_date=order_date,
                order_number=order_number,
            )
        )
        return self

    def add_order_model(self, order: TransactionOrder) -> Self:
        self._state["orders"].append(order)
        return self

    def clear_orders(self) -> Self:
        self._state["orders"].clear()
        return self

    def add_lot_number(self, value: str) -> Self:
        self._state["lot_numbers"].append(value)
        return self

    def clear_lot_numbers(self) -> Self:
        self._state["lot_numbers"].clear()
        return self

    def add_transport(
        self,
        *,
        transport_type: TransportType | None = None,
        other_transport: bool = False,
        other_transport_description: str | None = None,
        carrier_identity: TransactionIdentity | None = None,
        carrier_address: TransactionAddress | None = None,
        transport_order_number: str | None = None,
        cargo_type: CargoType | None = None,
        other_cargo: bool = False,
        other_cargo_description: str | None = None,
        packaging_unit: str | None = None,
        transport_start: datetime | None = None,
        transport_end: datetime | None = None,
        shipping_from: TransactionAddress | None = None,
        shipping_via: Sequence[TransactionAddress] | None = None,
        shipping_to: TransactionAddress | None = None,
    ) -> Self:
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
        self._state["transports"].append(transport)
        return self

    def clear_transports(self) -> Self:
        self._state["transports"].clear()
        return self

    def build(self) -> TransactionConditions:
        return TransactionConditions(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Transaction details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class TransactionBuilderMixin:
    _transaction_conditions: TransactionConditions | None = None

    def transaction(self) -> TransactionBuilder[Self]:
        return TransactionBuilder(
            self, self._set_transaction, self._transaction_conditions
        )

    def _set_transaction(self, value: TransactionConditions) -> None:
        self._transaction_conditions = value
