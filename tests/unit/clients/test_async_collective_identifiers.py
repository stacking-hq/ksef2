import asyncio
from datetime import datetime, timezone

import pytest
from polyfactory.factories import BaseFactory
from pydantic import ValidationError

from ksef2._clients.async_collective_identifiers import AsyncCollectiveIdentifiersClient
from ksef2._core.routes import CollectiveIdentifierRoutes
from ksef2._domain.models.collective_identifiers import (
    CollectiveIdentifierInvoice,
    CollectiveIdentifiersQuery,
)
from ksef2._infra.schema.api import spec
from tests.unit.factories.collective_identifiers import (
    CollectiveIdentifierInvoicesResponseFactory,
    CollectiveIdentifiersQueryResponseFactory,
)
from tests.unit.fakes.transport import AsyncFakeTransport

_KSEF_NUMBER = "1234567890-20250625-ABC123-DEF456-07"
_SECOND_KSEF_NUMBER = "1234567890-20250625-ABC123-DEF457-08"
_COLLECTIVE_IDENTIFIER_NUMBER = "1111111111-IZ202607-65ED02180000-E7"
_DATE_CREATED = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)


async def _collect(iterable):  # pyright: ignore[reportMissingParameterType,reportUnknownParameterType]
    return [item async for item in iterable]  # pyright: ignore[reportUnknownVariableType]


class TestAsyncCollectiveIdentifiersClient:
    def test_generate_maps_domain_invoice(
        self,
        async_fake_transport: AsyncFakeTransport,
        collective_generate_resp: BaseFactory[
            spec.GenerateCollectiveIdentifierResponse
        ],
    ) -> None:
        expected = collective_generate_resp.build()
        async_fake_transport.enqueue(expected.model_dump(mode="json"))

        result = asyncio.run(
            AsyncCollectiveIdentifiersClient(async_fake_transport).generate(
                invoices=[
                    CollectiveIdentifierInvoice(ksef_number=_KSEF_NUMBER),
                    CollectiveIdentifierInvoice(ksef_number=_SECOND_KSEF_NUMBER),
                ]
            )
        )

        assert (
            result.collective_identifier_number == expected.collectiveIdentifierNumber
        )
        assert async_fake_transport.calls[0].json == {
            "invoices": [
                {
                    "ksefNumber": _KSEF_NUMBER,
                    "payment": None,
                    "description": None,
                },
                {
                    "ksefNumber": _SECOND_KSEF_NUMBER,
                    "payment": None,
                    "description": None,
                },
            ]
        }

    def test_query_all_follows_continuation_token(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        first = CollectiveIdentifiersQueryResponseFactory.build(
            continuationToken="next-page"
        )
        second = CollectiveIdentifiersQueryResponseFactory.build(continuationToken=None)
        async_fake_transport.enqueue(first.model_dump(mode="json"))
        async_fake_transport.enqueue(second.model_dump(mode="json"))

        pages = asyncio.run(
            _collect(
                AsyncCollectiveIdentifiersClient(async_fake_transport).query_all(
                    filters=CollectiveIdentifiersQuery(
                        date_created_from=_DATE_CREATED,
                        date_created_to=_DATE_CREATED,
                    )
                )
            )
        )

        assert len(pages) == 2
        assert pages[0].continuation_token == "next-page"
        assert async_fake_transport.calls[1].headers == {
            "x-continuation-token": "next-page"
        }

    def test_query_by_ksef_and_list_invoices_map_responses(
        self,
        async_fake_transport: AsyncFakeTransport,
        collective_by_ksef_resp: BaseFactory[
            spec.CollectiveIdentifiersByKsefNumberQueryResponse
        ],
        collective_invoices_resp: BaseFactory[
            spec.CollectiveIdentifierInvoicesQueryResponse
        ],
    ) -> None:
        async_fake_transport.enqueue(
            collective_by_ksef_resp.build().model_dump(mode="json")
        )
        async_fake_transport.enqueue(
            collective_invoices_resp.build().model_dump(mode="json")
        )
        client = AsyncCollectiveIdentifiersClient(async_fake_transport)

        identifiers = asyncio.run(client.query_by_ksef_number(ksef_number=_KSEF_NUMBER))
        invoices = asyncio.run(
            client.list_invoices(
                collective_identifier_numbers=[_COLLECTIVE_IDENTIFIER_NUMBER]
            )
        )

        assert (
            identifiers.collective_identifiers[0].collective_identifier_number
            == _COLLECTIVE_IDENTIFIER_NUMBER
        )
        assert invoices.invoices[0].ksef_number == _KSEF_NUMBER
        assert [(call.method, call.path) for call in async_fake_transport.calls] == [
            (
                "GET",
                CollectiveIdentifierRoutes.QUERY_BY_KSEF_NUMBER.format(
                    ksefNumber=_KSEF_NUMBER
                ),
            ),
            ("POST", CollectiveIdentifierRoutes.LIST_INVOICES),
        ]
        assert async_fake_transport.calls[1].json == {
            "collectiveIdentifierNumbers": [_COLLECTIVE_IDENTIFIER_NUMBER]
        }

    def test_list_all_invoices_follows_continuation_token(
        self,
        async_fake_transport: AsyncFakeTransport,
    ) -> None:
        first = CollectiveIdentifierInvoicesResponseFactory.build(
            continuationToken="next-page"
        )
        second = CollectiveIdentifierInvoicesResponseFactory.build(
            continuationToken=None
        )
        async_fake_transport.enqueue(first.model_dump(mode="json"))
        async_fake_transport.enqueue(second.model_dump(mode="json"))

        pages = asyncio.run(
            _collect(
                AsyncCollectiveIdentifiersClient(
                    async_fake_transport
                ).list_all_invoices(
                    collective_identifier_numbers=[_COLLECTIVE_IDENTIFIER_NUMBER]
                )
            )
        )

        assert len(pages) == 2
        assert pages[0].continuation_token == "next-page"
        assert async_fake_transport.calls[1].headers == {
            "x-continuation-token": "next-page"
        }
        assert async_fake_transport.calls[1].json == {
            "collectiveIdentifierNumbers": [_COLLECTIVE_IDENTIFIER_NUMBER]
        }

    @pytest.mark.parametrize(
        "collective_identifier_numbers",
        ([], [_COLLECTIVE_IDENTIFIER_NUMBER] * 11),
        ids=["empty", "more-than-ten"],
    )
    def test_list_invoices_rejects_identifier_count_outside_spec_range(
        self,
        async_fake_transport: AsyncFakeTransport,
        collective_identifier_numbers: list[str],
    ) -> None:
        # A queued response keeps an unvalidated request from raising inside the
        # transport, so a missing limit surfaces as DID NOT RAISE.
        async_fake_transport.enqueue(
            CollectiveIdentifierInvoicesResponseFactory.build().model_dump(mode="json")
        )
        client = AsyncCollectiveIdentifiersClient(async_fake_transport)

        with pytest.raises(ValidationError, match="collective_identifier_numbers"):
            _ = asyncio.run(
                client.list_invoices(
                    collective_identifier_numbers=collective_identifier_numbers
                )
            )

        assert async_fake_transport.calls == []
