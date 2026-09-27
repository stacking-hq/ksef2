from datetime import datetime, timezone

from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

_KSEF_NUMBER = "1234567890-20250625-ABC123-DEF456-07"
_SECOND_KSEF_NUMBER = "1234567890-20250625-ABC123-DEF457-08"
_COLLECTIVE_IDENTIFIER_NUMBER = "1111111111-IZ202607-65ED02180000-E7"
_DATE_CREATED = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)


@register_fixture(name="collective_generate_req")
class GenerateCollectiveIdentifierRequestFactory(
    ModelFactory[spec.GenerateCollectiveIdentifierRequest]
):
    invoices = [
        spec.CollectiveIdentifierInvoice(ksefNumber=_KSEF_NUMBER),
        spec.CollectiveIdentifierInvoice(ksefNumber=_SECOND_KSEF_NUMBER),
    ]


@register_fixture(name="collective_generate_resp")
class GenerateCollectiveIdentifierResponseFactory(
    ModelFactory[spec.GenerateCollectiveIdentifierResponse]
):
    collectiveIdentifierNumber = _COLLECTIVE_IDENTIFIER_NUMBER


@register_fixture(name="collective_query_req")
class CollectiveIdentifiersQueryRequestFactory(
    ModelFactory[spec.CollectiveIdentifiersQueryRequest]
):
    dateCreatedFrom = _DATE_CREATED
    dateCreatedTo = _DATE_CREATED


@register_fixture(name="collective_query_resp")
class CollectiveIdentifiersQueryResponseFactory(
    ModelFactory[spec.CollectiveIdentifiersQueryResponse]
):
    continuationToken: str | None = None
    collectiveIdentifiers = [
        spec.CollectiveIdentifiersQueryResponseItem(
            collectiveIdentifierNumber=_COLLECTIVE_IDENTIFIER_NUMBER,
            dateCreated=_DATE_CREATED,
            invoiceCount=1,
            createdInCurrentContext=True,
        )
    ]


@register_fixture(name="collective_by_ksef_resp")
class CollectiveIdentifiersByKsefNumberResponseFactory(
    ModelFactory[spec.CollectiveIdentifiersByKsefNumberQueryResponse]
):
    continuationToken: str | None = None
    collectiveIdentifiers = [
        spec.CollectiveIdentifiersByKsefNumberQueryResponseItem(
            collectiveIdentifierNumber=_COLLECTIVE_IDENTIFIER_NUMBER,
            dateCreated=_DATE_CREATED,
            createdInCurrentContext=True,
        )
    ]


@register_fixture(name="collective_invoices_req")
class CollectiveIdentifierInvoicesRequestFactory(
    ModelFactory[spec.CollectiveIdentifierInvoicesQueryRequest]
):
    collectiveIdentifierNumbers = [_COLLECTIVE_IDENTIFIER_NUMBER]


@register_fixture(name="collective_invoices_resp")
class CollectiveIdentifierInvoicesResponseFactory(
    ModelFactory[spec.CollectiveIdentifierInvoicesQueryResponse]
):
    continuationToken: str | None = None
    invoices = [
        spec.CollectiveIdentifierInvoicesQueryResponseItem(
            ksefNumber=_KSEF_NUMBER,
            collectiveIdentifierNumber=_COLLECTIVE_IDENTIFIER_NUMBER,
            description="Settlement",
            detailsHidden=False,
        )
    ]
