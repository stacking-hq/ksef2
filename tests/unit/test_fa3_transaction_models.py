from decimal import Decimal

import pytest
from pydantic import ValidationError

from ksef2.domain.models.fa3.body.transaction import (
    TransactionAddress,
    TransactionConditions,
    TransactionContract,
    TransactionIdentity,
    TransactionTransport,
)


def test_transaction_contract_requires_date_or_number() -> None:
    with pytest.raises(
        ValidationError,
        match="At least one of contract_date or contract_number must be provided",
    ):
        TransactionContract()


def test_transaction_conditions_require_currency_and_exchange_rate_together() -> None:
    with pytest.raises(
        ValidationError,
        match="contract_exchange_rate and contract_currency must be provided together",
    ):
        TransactionConditions(contract_exchange_rate=Decimal("4.500000"))


def test_transaction_conditions_reject_pln_contract_currency() -> None:
    with pytest.raises(
        ValidationError,
        match="contract_currency cannot be PLN",
    ):
        TransactionConditions(
            contract_exchange_rate=Decimal("4.500000"),
            contract_currency="PLN",
        )


def test_transaction_transport_requires_other_transport_description() -> None:
    with pytest.raises(
        ValidationError,
        match="other_transport_description is required when other_transport is true",
    ):
        TransactionTransport(other_transport=True)


def test_transaction_transport_requires_flattened_carrier_fields_together() -> None:
    with pytest.raises(
        ValidationError,
        match="carrier_identity and carrier_address must be provided together",
    ):
        TransactionTransport(
            carrier_identity=TransactionIdentity(name="Jan Nowak"),
        )

    with pytest.raises(
        ValidationError,
        match="carrier_identity and carrier_address must be provided together",
    ):
        TransactionTransport(
            carrier_address=TransactionAddress(
                country_code="PL",
                address_line_1="ul. Pomaranczowa 12",
            ),
        )
