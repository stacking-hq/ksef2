"""Public export result contracts over local HTTP mocks."""

import base64
import io
import json
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.x509.oid import NameOID

from ksef2 import AsyncClient, Client, Environment
from ksef2.models import AuthenticationResumeState, ExportResumeState, InvoicesFilter
from ksef2._core.crypto import encrypt_invoice


@pytest.mark.parametrize("compression", ["Zip", "TarGz"])
@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("resumed", [False, True], ids=["scheduled", "resumed"])
async def test_export_reads_and_saves_response_format(
    compression: str, is_async: bool, resumed: bool, tmp_path: Path
) -> None:
    entries = {
        "nested/invoice.xml": b"<invoice />",
        "_metadata.json": b'{"invoices": []}',
    }
    buffer = io.BytesIO()
    if compression == "Zip":
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
    else:
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name, content in entries.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
    payload = buffer.getvalue()
    key, iv = b"k" * 32, b"v" * 16
    parts = [payload[: len(payload) // 2], payload[len(payload) // 2 :]]
    encrypted = [encrypt_invoice(part, key=key, iv=iv) for part in parts]

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "local-export-test")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(1)
        .not_valid_before(datetime(2020, 1, 1, tzinfo=UTC))
        .not_valid_after(datetime(2030, 1, 1, tzinfo=UTC))
        .sign(private_key, hashes.SHA256())
    )
    cert_b64 = base64.b64encode(
        certificate.public_bytes(serialization.Encoding.DER)
    ).decode()

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal encrypted
        if request.url.path.endswith("/security/public-key-certificates"):
            return httpx.Response(
                200,
                json=[
                    {
                        "certificate": cert_b64,
                        "validFrom": "2020-01-01T00:00:00Z",
                        "validTo": "2030-01-01T00:00:00Z",
                        "usage": ["SymmetricKeyEncryption"],
                    }
                ],
            )
        if request.url.path.endswith("/invoices/exports") and request.method == "POST":
            body = json.loads(request.content)
            assert body["compressionType"] == compression
            export_key = private_key.decrypt(
                base64.b64decode(body["encryption"]["encryptedSymmetricKey"]),
                OAEP(mgf=MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
            )
            export_iv = base64.b64decode(body["encryption"]["initializationVector"])
            encrypted = [
                encrypt_invoice(part, key=export_key, iv=export_iv) for part in parts
            ]
            return httpx.Response(201, json={"referenceNumber": "E" * 36})
        if request.url.path.endswith("/invoices/exports/" + "E" * 36):
            return httpx.Response(
                200,
                json={
                    "status": {"code": 200, "description": "Ready"},
                    "package": {
                        "invoiceCount": 1,
                        "size": len(payload),
                        "isTruncated": False,
                        "compressionType": compression,
                        "parts": [
                            {
                                "ordinalNumber": i + 1,
                                "partName": f"part-{i}.aes",
                                "method": "GET",
                                "url": f"https://storage.mock/parts/{i}",
                                "partSize": len(parts[i]),
                                "partHash": "A" * 43 + "=",
                                "encryptedPartSize": len(content),
                                "encryptedPartHash": "A" * 43 + "=",
                                "expirationDate": "2030-01-01T00:00:00Z",
                            }
                            for i, content in enumerate(encrypted)
                        ],
                    },
                },
            )
        if request.url.host == "storage.mock":
            assert "authorization" not in request.headers
            return httpx.Response(
                200, content=encrypted[int(request.url.path.rsplit("/", 1)[-1])]
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    auth_state = AuthenticationResumeState(
        access_token=SecretStr("synthetic-access"),
        access_token_valid_until=datetime(2030, 1, 1, tzinfo=UTC),
        refresh_token=SecretStr("synthetic-refresh"),
        refresh_token_valid_until=datetime(2030, 1, 1, tzinfo=UTC),
    )
    state = ExportResumeState(
        reference_number="E" * 36,
        aes_key=SecretStr(base64.b64encode(key).decode()),
        iv=SecretStr(base64.b64encode(iv).decode()),
    )
    filters = InvoicesFilter.for_seller(date_from="2026-01-01T00:00:00Z")
    sdk_compression = "zip" if compression == "Zip" else "tar_gz"
    transport = httpx.MockTransport(handle)
    if is_async:
        async with AsyncClient(
            Environment.TEST,
            http_client=httpx.AsyncClient(
                base_url=Environment.TEST.base_url, transport=transport
            ),
        ) as client:
            auth = client.authentication.resume(auth_state)
            if resumed:
                job = await auth.invoices.export(state=state)
            else:
                job = await auth.invoices.export(
                    filters, compression_type=sdk_compression
                )
            exported = await job.wait(poll_interval=0.0)
    else:
        with Client(
            Environment.TEST,
            http_client=httpx.Client(
                base_url=Environment.TEST.base_url, transport=transport
            ),
        ) as client:
            auth = client.authentication.resume(auth_state)
            if resumed:
                job = auth.invoices.export(state=state)
            else:
                job = auth.invoices.export(filters, compression_type=sdk_compression)
            exported = job.wait(poll_interval=0.0)
    assert exported.archive == payload
    assert list(exported.invoices()) == [("invoice", b"<invoice />")]
    assert exported.metadata == []
    assert exported.package is not None
    assert exported.package.compression_type == (
        "zip" if compression == "Zip" else "tar_gz"
    )
    output = tmp_path / "out"
    assert {p.relative_to(output).as_posix() for p in exported.save(output)} == set(
        entries
    )
    for name, content in entries.items():
        assert (output / name).read_bytes() == content
