"""Mappings from collective identifier domain models to API schema models."""

from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2._domain.models.collective_identifiers import (
    CollectiveIdentifierInvoice,
    CollectiveIdentifierInvoicePayment,
    CollectiveIdentifierInvoicesQuery,
    CollectiveIdentifiersQuery,
)
from ksef2._infra.schema.api import spec


@overload
def to_spec(
    request: CollectiveIdentifierInvoicePayment,
) -> spec.CollectiveIdentifierInvoicePayment: ...


@overload
def to_spec(
    request: CollectiveIdentifierInvoice,
) -> spec.CollectiveIdentifierInvoice: ...


@overload
def to_spec(
    request: list[CollectiveIdentifierInvoice],
) -> spec.GenerateCollectiveIdentifierRequest: ...


@overload
def to_spec(
    request: CollectiveIdentifiersQuery,
) -> spec.CollectiveIdentifiersQueryRequest: ...


@overload
def to_spec(
    request: CollectiveIdentifierInvoicesQuery,
) -> spec.CollectiveIdentifierInvoicesQueryRequest: ...


def to_spec(
    request: BaseModel | list[CollectiveIdentifierInvoice],
) -> BaseModel:
    """Convert a collective identifier domain object into an API payload."""
    if isinstance(request, list):
        return spec.GenerateCollectiveIdentifierRequest(
            invoices=[to_spec(invoice) for invoice in request]
        )
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> BaseModel:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(
    request: CollectiveIdentifierInvoicePayment,
) -> spec.CollectiveIdentifierInvoicePayment:
    return spec.CollectiveIdentifierInvoicePayment(
        amount=request.amount,
        currency=spec.CurrencyCode(request.currency),
    )


@_to_spec.register
def _(
    request: CollectiveIdentifierInvoice,
) -> spec.CollectiveIdentifierInvoice:
    return spec.CollectiveIdentifierInvoice(
        ksefNumber=request.ksef_number,
        payment=to_spec(request.payment) if request.payment is not None else None,
        description=request.description,
    )


@_to_spec.register
def _(
    request: CollectiveIdentifiersQuery,
) -> spec.CollectiveIdentifiersQueryRequest:
    return spec.CollectiveIdentifiersQueryRequest(
        collectiveIdentifierNumber=request.collective_identifier_number,
        dateCreatedFrom=request.date_created_from,
        dateCreatedTo=request.date_created_to,
        invoiceCountFrom=request.invoice_count_from,
        invoiceCountTo=request.invoice_count_to,
        createdInCurrentContext=request.created_in_current_context,
    )


@_to_spec.register
def _(
    request: CollectiveIdentifierInvoicesQuery,
) -> spec.CollectiveIdentifierInvoicesQueryRequest:
    return spec.CollectiveIdentifierInvoicesQueryRequest(
        collectiveIdentifierNumbers=list(request.collective_identifier_numbers)
    )
