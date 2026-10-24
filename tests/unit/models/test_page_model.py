"""The public ``Page`` model: nested types survive JSON, and the schema stays usable."""

from ksef2._infra.mappers.invoices import from_spec as invoices_from_spec
from ksef2.models import InvoiceMetadata, Page, TokenInfo
from tests.unit.factories.tokens import DomainTokenInfoFactory
from tests.unit.support.payloads import InvoiceMetadataFactory


def _metadata() -> InvoiceMetadata:
    """One metadata row built the way the SDK builds it from a KSeF response."""
    return invoices_from_spec(InvoiceMetadataFactory.build())


def test_page_of_tokens_round_trips_through_json() -> None:
    page = Page[TokenInfo](
        items=[DomainTokenInfoFactory.build(), DomainTokenInfoFactory.build()],
        next_cursor="cursor-1",
    )

    restored = Page[TokenInfo].model_validate_json(page.model_dump_json())

    assert restored == page
    assert [type(item) for item in restored.items] == [TokenInfo, TokenInfo]


def test_page_of_invoice_metadata_round_trips_through_json() -> None:
    page = Page[InvoiceMetadata](items=[_metadata()], next_cursor=None)

    restored = Page[InvoiceMetadata].model_validate_json(page.model_dump_json())

    assert restored == page
    assert type(restored.items[0]) is InvoiceMetadata


def test_page_json_schema_describes_items_and_cursor() -> None:
    schema = Page[InvoiceMetadata].model_json_schema()

    properties = schema["properties"]
    assert properties["items"]["items"]["$ref"].endswith("InvoiceMetadata")
    assert (
        schema["$defs"]["InvoiceMetadata"]["properties"]["ksef_number"]["type"]
        == "string"
    )
    assert properties["next_cursor"]["anyOf"] == [{"type": "string"}, {"type": "null"}]
    assert schema["required"] == ["items"]
