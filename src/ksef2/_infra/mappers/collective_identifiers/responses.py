"""Mappings from collective identifier API models to domain models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2._domain.models.collective_identifiers import (
    CollectiveIdentifierInvoiceDetails,
    CollectiveIdentifierInvoicePayment,
    CollectiveIdentifierInvoicesPage,
    CollectiveIdentifierReference,
    CollectiveIdentifierReferencesPage,
    CollectiveIdentifierSummary,
    CollectiveIdentifiersPage,
    GenerateCollectiveIdentifierResponse,
)
from ksef2._domain.types import CurrencyCodes
from ksef2._infra.schema.api import spec
from typing import cast


@overload
def from_spec(
    response: spec.GenerateCollectiveIdentifierResponse,
) -> GenerateCollectiveIdentifierResponse: ...


@overload
def from_spec(
    response: spec.CollectiveIdentifiersQueryResponse,
) -> CollectiveIdentifiersPage: ...


@overload
def from_spec(
    response: spec.CollectiveIdentifiersByKsefNumberQueryResponse,
) -> CollectiveIdentifierReferencesPage: ...


@overload
def from_spec(
    response: spec.CollectiveIdentifierInvoicesQueryResponse,
) -> CollectiveIdentifierInvoicesPage: ...


def from_spec(response: BaseModel) -> BaseModel:
    """Convert a collective identifier API response into a domain model."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel) -> BaseModel:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(
    response: spec.GenerateCollectiveIdentifierResponse,
) -> GenerateCollectiveIdentifierResponse:
    return GenerateCollectiveIdentifierResponse(
        collective_identifier_number=response.collectiveIdentifierNumber
    )


@_from_spec.register
def _(
    response: spec.CollectiveIdentifiersQueryResponse,
) -> CollectiveIdentifiersPage:
    return CollectiveIdentifiersPage(
        continuation_token=response.continuationToken,
        collective_identifiers=[
            CollectiveIdentifierSummary(
                collective_identifier_number=item.collectiveIdentifierNumber,
                date_created=item.dateCreated,
                invoice_count=item.invoiceCount,
                created_in_current_context=item.createdInCurrentContext,
            )
            for item in response.collectiveIdentifiers
        ],
    )


@_from_spec.register
def _(
    response: spec.CollectiveIdentifiersByKsefNumberQueryResponse,
) -> CollectiveIdentifierReferencesPage:
    return CollectiveIdentifierReferencesPage(
        continuation_token=response.continuationToken,
        collective_identifiers=[
            CollectiveIdentifierReference(
                collective_identifier_number=item.collectiveIdentifierNumber,
                date_created=item.dateCreated,
                created_in_current_context=item.createdInCurrentContext,
            )
            for item in response.collectiveIdentifiers
        ],
    )


@_from_spec.register
def _(
    response: spec.CollectiveIdentifierInvoicesQueryResponse,
) -> CollectiveIdentifierInvoicesPage:
    return CollectiveIdentifierInvoicesPage(
        continuation_token=response.continuationToken,
        invoices=[
            CollectiveIdentifierInvoiceDetails(
                ksef_number=item.ksefNumber,
                payment=(
                    CollectiveIdentifierInvoicePayment(
                        amount=item.payment.amount,
                        currency=cast(CurrencyCodes, item.payment.currency),
                    )
                    if item.payment is not None
                    else None
                ),
                description=item.description,
                details_hidden=item.detailsHidden,
            )
            for item in response.invoices
        ],
    )
