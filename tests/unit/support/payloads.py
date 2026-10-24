"""Canned KSeF response payloads shared by the workflow tests."""

import io
import json
import zipfile
from datetime import UTC, datetime
from typing import Any

from polyfactory import BaseFactory
from polyfactory.factories.pydantic_factory import ModelFactory

from ksef2._infra.schema.api import spec

INVOICE_REF = "20250625-EE-319D7EE000-B67F415CDC-2C"
KSEF_NUMBER = "1234567890-20260306-ABCDEF-123456-7A"
KSEF_1 = "5265877635-20260101-0100100AB5B5-4B"
KSEF_2 = "5265877635-20260102-0100100AB5B5-5C"
UPO_REFS = ("a" * 36, "b" * 36)


class InvoiceMetadataFactory(ModelFactory[spec.InvoiceMetadata]): ...


def upo(*refs: str) -> spec.UpoResponse:
    return spec.UpoResponse(
        pages=[
            spec.UpoPageResponse(
                referenceNumber=ref,
                downloadUrl=f"https://example.com/upo/{ref}",  # pyright: ignore[reportArgumentType]
                downloadUrlExpirationDate=datetime(2030, 1, 1, tzinfo=UTC),
            )
            for ref in refs
        ]
    )


def session_status(
    factory: BaseFactory[spec.SessionStatusResponse],
    code: int,
    upo_pages: spec.UpoResponse | None = None,
) -> dict[str, Any]:
    return factory.build(
        status=spec.StatusInfo(code=code, description=f"status {code}"),
        upo=upo_pages,
    ).model_dump(mode="json")


def invoice_status(
    factory: BaseFactory[spec.SessionInvoiceStatusResponse],
    code: int,
    ksef_number: str | None,
) -> dict[str, Any]:
    return factory.build(
        referenceNumber=INVOICE_REF,
        ksefNumber=ksef_number,
        status=spec.InvoiceStatusInfo(code=code, description=f"status {code}"),
    ).model_dump(mode="json")


def metadata_page(
    factory: BaseFactory[spec.QueryInvoicesMetadataResponse],
    *,
    count: int,
    has_more: bool,
) -> dict[str, Any]:
    return factory.build(
        hasMore=has_more,
        isTruncated=False,
        permanentStorageHwmDate=None,
        invoices=[InvoiceMetadataFactory.build() for _ in range(count)],
    ).model_dump(mode="json")


def package_status(
    factory: BaseFactory[spec.InvoiceExportStatusResponse],
    code: int,
    part_count: int = 0,
) -> dict[str, Any]:
    package = None
    if part_count:
        package = spec.InvoicePackage.model_validate(
            {
                "invoiceCount": 2,
                "size": 128,
                "parts": [
                    {
                        "ordinalNumber": ordinal,
                        "partName": f"part-{ordinal}.zip.aes",
                        "method": "GET",
                        "url": f"https://example.com/export/part-{ordinal}?sig=secret",
                        "partSize": 64,
                        "partHash": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "encryptedPartSize": 128,
                        "encryptedPartHash": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",
                        "expirationDate": datetime(2030, 1, 1, tzinfo=UTC),
                    }
                    for ordinal in range(1, part_count + 1)
                ],
                "isTruncated": False,
            }
        )
    return factory.build(
        status=spec.StatusInfo(code=code, description=f"status {code}"),
        package=package,
    ).model_dump(mode="json")


def archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(f"{KSEF_1}.xml", b"<one />")
        zf.writestr(f"{KSEF_2}.xml", b"<two />")
        zf.writestr("_metadata.json", json.dumps({"invoices": []}))
    return buffer.getvalue()
