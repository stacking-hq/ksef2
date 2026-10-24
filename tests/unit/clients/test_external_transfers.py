import asyncio
import json
from datetime import datetime, timezone

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients.async_base import AsyncClient
from ksef2._clients.base import Client
from ksef2._config import Environment
from ksef2._core.crypto import sha256_b64
from ksef2._core.exceptions import (
    KSeFAuthError,
    KSeFBatchUploadError,
    KSeFExternalTransferError,
)
from ksef2._domain.models.auth import AuthenticationResumeState, AuthTokens
from ksef2._domain.models.batch import (
    BatchEncryptionData,
    BatchFileInfo,
    BatchFilePart,
    BatchPreparedPart,
    BatchSessionResumeState,
    PartUploadRequest,
    PreparedBatch,
)
from ksef2._domain.models.invoices import ExportHandle, InvoicePackage, PackagePart
from ksef2._core.exceptions import KSeFTransportError
from tests.unit.support.flavors import Flavor
from tests.unit.support.helpers import legacy_api


_SIGNED_DOWNLOAD_URL = "https://storage.example/export/part-1?sig=secret"
_SIGNED_UPLOAD_URL = "https://storage.example/upload/part-1?sig=secret"


def _export_package() -> InvoicePackage:
    return InvoicePackage(
        invoice_count=1,
        size=128,
        parts=[
            PackagePart(
                ordinal_number=1,
                part_name="part-1.zip.aes",
                method="GET",
                url=_SIGNED_DOWNLOAD_URL,
                part_size=64,
                part_hash="A" * 44,
                encrypted_part_size=128,
                encrypted_part_hash="B" * 44,
                expiration_date=datetime.now(timezone.utc),
            )
        ],
        is_truncated=False,
    )


def _export_handle() -> ExportHandle:
    return ExportHandle(
        reference_number="export-ref",
        aes_key=b"k" * 32,
        iv=b"v" * 16,
    )


def _prepared_batch() -> PreparedBatch:
    return PreparedBatch(
        batch_file=BatchFileInfo(
            file_size=10,
            file_hash=sha256_b64(b"plaintext"),
            parts=[
                BatchFilePart(
                    ordinal_number=1,
                    file_size=12,
                    file_hash=sha256_b64(b"encrypted"),
                )
            ],
        ),
        parts=[
            BatchPreparedPart(
                ordinal_number=1,
                content=b"encrypted",
                file_size=len(b"encrypted"),
                file_hash=sha256_b64(b"encrypted"),
            )
        ],
        encryption=BatchEncryptionData.from_bytes(
            aes_key=b"k" * 32,
            iv=b"v" * 16,
            encrypted_key=b"encrypted-key",
        ),
        invoices=[],
    )


@legacy_api
def test_sync_download_uses_unauthed_non_ksef_transfer_transport(
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    requests: list[httpx.Request] = []

    def _reject(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status_code=403, request=request)

    with httpx.Client(transport=httpx.MockTransport(_reject)) as http_client:
        client = Client(http_client=http_client)
        authenticated = client.authentication.resume(
            AuthenticationResumeState.from_tokens(domain_auth_tokens.build())
        )
        try:
            with pytest.raises(KSeFExternalTransferError) as exc_info:
                authenticated.invoices.fetch_package_bytes(
                    package=_export_package(),
                    export=_export_handle(),
                )
        finally:
            client.close()

    error = exc_info.value
    assert not isinstance(error, KSeFAuthError)
    assert error.status_code == 403
    assert error.outcome_ambiguous is False
    assert error.host == "storage.example"
    assert isinstance(error.__cause__, httpx.HTTPStatusError)
    assert "sig=secret" not in str(error)
    assert "sig=secret" not in repr(error.context)
    assert len(requests) == 1
    assert "Authorization" not in requests[0].headers


def test_sync_upload_marks_lost_response_ambiguous_and_exposes_recovery(
    domain_auth_tokens: BaseFactory[AuthTokens],
    domain_batch_session_state: BaseFactory[BatchSessionResumeState],
) -> None:
    requests: list[httpx.Request] = []

    def _lose_response(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.ReadTimeout("response lost", request=request)

    state = domain_batch_session_state.build(
        reference_number="batch-ref",
        part_upload_requests=[
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url=_SIGNED_UPLOAD_URL,
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ],
    )
    with httpx.Client(transport=httpx.MockTransport(_lose_response)) as http_client:
        client = Client(http_client=http_client)
        authenticated = client.authentication.resume(
            AuthenticationResumeState.from_tokens(domain_auth_tokens.build())
        )
        session = authenticated.batch_session(state=state)
        try:
            with pytest.raises(KSeFBatchUploadError) as exc_info:
                authenticated.batch.upload_parts(
                    session=session,
                    prepared_batch=_prepared_batch(),
                )
        finally:
            client.close()

    error = exc_info.value
    assert error.outcome_ambiguous is True
    assert error.recovery_state() is state
    assert isinstance(error.__cause__, KSeFExternalTransferError)
    assert isinstance(error.__cause__.__cause__, httpx.ReadTimeout)
    assert len(requests) == 1
    assert "Authorization" not in requests[0].headers


@legacy_api
def test_async_download_uses_unauthed_non_ksef_transfer_transport(
    domain_auth_tokens: BaseFactory[AuthTokens],
) -> None:
    requests: list[httpx.Request] = []

    def _reject(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status_code=403, request=request)

    async def _run() -> KSeFExternalTransferError:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(_reject)
        ) as http_client:
            client = AsyncClient(http_client=http_client)
            authenticated = client.authentication.resume(
                AuthenticationResumeState.from_tokens(domain_auth_tokens.build())
            )
            try:
                with pytest.raises(KSeFExternalTransferError) as exc_info:
                    await authenticated.invoices.fetch_package_bytes(
                        package=_export_package(),
                        export=_export_handle(),
                    )
            finally:
                await client.aclose()
        return exc_info.value

    error = asyncio.run(_run())

    assert not isinstance(error, KSeFAuthError)
    assert error.status_code == 403
    assert error.outcome_ambiguous is False
    assert error.host == "storage.example"
    assert isinstance(error.__cause__, httpx.HTTPStatusError)
    assert "sig=secret" not in str(error)
    assert "sig=secret" not in repr(error.context)
    assert len(requests) == 1
    assert "Authorization" not in requests[0].headers


def test_async_upload_marks_lost_response_ambiguous_and_exposes_recovery(
    domain_auth_tokens: BaseFactory[AuthTokens],
    domain_batch_session_state: BaseFactory[BatchSessionResumeState],
) -> None:
    requests: list[httpx.Request] = []

    def _lose_response(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.ReadTimeout("response lost", request=request)

    state = domain_batch_session_state.build(
        reference_number="batch-ref",
        part_upload_requests=[
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url=_SIGNED_UPLOAD_URL,
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ],
    )

    async def _run() -> KSeFBatchUploadError[BatchSessionResumeState]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(_lose_response)
        ) as http_client:
            client = AsyncClient(http_client=http_client)
            authenticated = client.authentication.resume(
                AuthenticationResumeState.from_tokens(domain_auth_tokens.build())
            )
            session = await authenticated.batch_session(state=state)
            try:
                with pytest.raises(KSeFBatchUploadError) as exc_info:
                    await authenticated.batch.upload_parts(
                        session=session,
                        prepared_batch=_prepared_batch(),
                    )
            finally:
                await client.aclose()
        return exc_info.value

    error = asyncio.run(_run())

    assert error.outcome_ambiguous is True
    assert error.recovery_state() is state
    assert isinstance(error.__cause__, KSeFExternalTransferError)
    assert isinstance(error.__cause__.__cause__, httpx.ReadTimeout)
    assert len(requests) == 1
    assert "Authorization" not in requests[0].headers


@legacy_api
@pytest.mark.parametrize(
    ("failure", "expected_cause", "expected_requests"),
    [
        ("transport", httpx.ConnectError, 1),
        ("decoding", httpx.DecodingError, 1),
        ("redirect", httpx.TooManyRedirects, 2),
        ("status", httpx.HTTPStatusError, 1),
    ],
    ids=["transport", "decoding", "redirect", "status"],
)
@pytest.mark.parametrize("operation", ["download", "upload"])
def test_external_errors_are_transport_errors(
    flavor: Flavor,
    domain_auth_tokens: BaseFactory[AuthTokens],
    domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    operation: str,
    failure: str,
    expected_cause: type[httpx.RequestError],
    expected_requests: int,
) -> None:
    """Presigned-storage failures keep their own class and code under the transport base."""
    requests: list[httpx.Request] = []

    def _handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if failure == "transport":
            raise httpx.ConnectError("storage unreachable", request=request)
        if failure == "decoding":
            return httpx.Response(
                200,
                headers={"Content-Encoding": "gzip"},
                content=b"not-gzip",
                request=request,
            )
        if failure == "redirect":
            return httpx.Response(
                302,
                headers={"Location": request.url.path},
                request=request,
            )
        return httpx.Response(403, content=b"", request=request)

    state = domain_batch_session_state.build(
        reference_number="batch-ref",
        part_upload_requests=[
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url=_SIGNED_UPLOAD_URL,
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ],
    )
    http_client: httpx.Client | httpx.AsyncClient
    if flavor.is_async:
        http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(_handle),
            follow_redirects=failure == "redirect",
            max_redirects=1,
        )
    else:
        http_client = httpx.Client(
            transport=httpx.MockTransport(_handle),
            follow_redirects=failure == "redirect",
            max_redirects=1,
        )

    client = flavor.root_client(
        environment=Environment.PRODUCTION, http_client=http_client
    )
    try:
        authenticated = client.authentication.resume(
            AuthenticationResumeState.from_tokens(domain_auth_tokens.build())
        )
        if operation == "download":
            with pytest.raises(KSeFExternalTransferError) as exc_info:
                _ = flavor.run(
                    authenticated.invoices.fetch_package_bytes(
                        package=_export_package(),
                        export=_export_handle(),
                    )
                )
            error: KSeFExternalTransferError = exc_info.value
        else:
            session = flavor.run(authenticated.batch_session(state=state))
            with pytest.raises(KSeFBatchUploadError) as exc_info:
                _ = flavor.run(
                    authenticated.batch.upload_parts(
                        session=session,
                        prepared_batch=_prepared_batch(),
                    )
                )
            error = exc_info.value
    finally:
        flavor.close(client)
        if isinstance(http_client, httpx.AsyncClient):
            _ = asyncio.run(http_client.aclose())
        else:
            http_client.close()

    assert isinstance(error, KSeFTransportError)
    if operation == "upload":
        assert isinstance(error, KSeFBatchUploadError)
        assert error.code == "BATCH_UPLOAD_ERROR"
        assert error.recovery_state() is state
        transfer_error = error.__cause__
    else:
        assert type(error) is KSeFExternalTransferError
        assert error.code == "EXTERNAL_TRANSFER_ERROR"
        transfer_error = error

    assert isinstance(transfer_error, KSeFExternalTransferError)
    # Only a real storage answer carries a status; a lost or undecodable response
    # and an abandoned redirect chain leave the SDK without one.
    assert transfer_error.status_code == (403 if failure == "status" else None)
    assert transfer_error.outcome_ambiguous is (
        operation == "upload" and failure != "status"
    )
    assert isinstance(transfer_error.__cause__, expected_cause)
    assert not isinstance(error, KSeFAuthError)
    assert "sig=secret" not in str(error)
    assert "sig=secret" not in json.dumps(error.context, default=str)
    assert len(requests) == expected_requests
    assert "Authorization" not in requests[0].headers
