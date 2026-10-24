"""Public batch recovery contracts with local HTTP and synthetic invoices."""

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from ksef2 import AsyncClient, Client, Environment
from ksef2 import KSeFBatchUploadError, KSeFValidationError
from ksef2.models import (
    AuthenticationResumeState,
    AuthTokens,
    PreparedBatch,
    TokenCredentials,
)
from tests.unit.support.flavors import Flavor


@pytest.mark.parametrize("retain_prepared", [True, False])
@pytest.mark.parametrize("serialized_state", [True, False])
@pytest.mark.parametrize(
    "mismatch",
    [
        None,
        "content",
        "key",
        "iv",
        "encrypted_key",
        "metadata",
        "form",
        "ordinal",
        "state_key",
        "legacy_state",
    ],
)
def test_public_batch_recovery(
    flavor: Flavor,
    retain_prepared: bool,
    serialized_state: bool,
    mismatch: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "local fixture")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    calls: list[httpx.Request] = []
    uploaded: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/security/public-key-certificates"):
            return httpx.Response(
                200,
                json=[
                    {
                        "certificate": base64.b64encode(
                            certificate.public_bytes(serialization.Encoding.DER)
                        ).decode(),
                        "validFrom": (now - timedelta(days=1)).isoformat(),
                        "validTo": (now + timedelta(days=1)).isoformat(),
                        "usage": ["SymmetricKeyEncryption"],
                    }
                ],
            )
        if request.url.path.endswith("/sessions/batch"):
            return httpx.Response(
                201,
                json={
                    "referenceNumber": "B" * 36,
                    "partUploadRequests": [
                        {
                            "ordinalNumber": 1,
                            "method": "PUT",
                            "url": "https://storage.example/upload?sig=secret",
                            "headers": {},
                        }
                    ],
                },
            )
        if request.url.host == "storage.example":
            uploaded.append(request.content)
            if len(uploaded) == 1:
                raise httpx.ConnectTimeout("local storage timeout", request=request)
            return httpx.Response(201)
        if request.url.path.endswith("/close"):
            return httpx.Response(204)
        if request.url.path.endswith("B" * 36):
            return httpx.Response(
                200,
                json={
                    "status": {"code": 100, "description": "open"},
                    "dateCreated": now.isoformat(),
                    "dateUpdated": now.isoformat(),
                },
            )
        raise AssertionError(
            f"Unexpected local request: {request.method} {request.url.path}"
        )

    http: httpx.AsyncClient | httpx.Client
    client: AsyncClient | Client
    if flavor.is_async:
        http = httpx.AsyncClient(
            base_url=Environment.TEST.base_url, transport=httpx.MockTransport(handler)
        )
        client = AsyncClient(Environment.TEST, http_client=http)
    else:
        http = httpx.Client(
            base_url=Environment.TEST.base_url, transport=httpx.MockTransport(handler)
        )
        client = Client(Environment.TEST, http_client=http)
    try:
        auth = client.authentication.resume(
            AuthenticationResumeState.from_tokens(
                AuthTokens(
                    access_token=TokenCredentials(
                        token="local-access", valid_until=now + timedelta(hours=1)
                    ),
                    refresh_token=TokenCredentials(
                        token="local-refresh", valid_until=now + timedelta(days=1)
                    ),
                )
            )
        )
        prepared = (
            flavor.run(auth.batch.prepare([b"<Invoice/>"])) if retain_prepared else None
        )
        with pytest.raises(KSeFBatchUploadError) as caught:
            _ = flavor.run(
                auth.batch.submit(prepared if prepared is not None else [b"<Invoice/>"])
            )
        error = caught.value
        assert error.__cause__ is not None
        assert isinstance(error.__cause__.__cause__, httpx.ConnectTimeout)
        state = error.recovery_state()
        recovered = error.recovery_prepared_batch()
        if prepared is not None:
            assert recovered is prepared
        assert "sig=secret" not in str(error)
        assert "sig=secret" not in repr(state)
        assert "parts" not in recovered.model_dump()
        assert "encryption" not in recovered.model_dump()
        assert "content=" not in repr(recovered)
        assert "content" not in recovered.parts[0].model_dump()
        if mismatch == "iv":
            recovered = recovered.model_copy(deep=True)
            recovered.encryption.iv = base64.b64encode(b"x" * 16).decode()
        elif mismatch == "encrypted_key":
            recovered = recovered.model_copy(deep=True)
            recovered.encryption.encrypted_key = base64.b64encode(
                b"other wrapped key"
            ).decode()
        elif mismatch == "state_key":
            state = state.model_copy(
                update={"aes_key": SecretStr(base64.b64encode(b"x" * 32).decode())}
            )
        elif mismatch == "legacy_state":
            state = state.model_copy(update={"prepared_batch_digest": None})
            handle = flavor.run(auth.batch_session(state=state))
            assert handle.reference_number == state.reference_number
        elif mismatch == "content":
            recovered = recovered.model_copy(deep=True)
            recovered.parts[0].content = b"different ciphertext"
        elif mismatch == "key":
            recovered = recovered.model_copy(deep=True)
            recovered.encryption.aes_key = base64.b64encode(b"x" * 32).decode()
        elif mismatch == "metadata":
            recovered = recovered.model_copy(deep=True)
            recovered.batch_file.file_hash = "different"
        elif mismatch == "form":
            recovered = recovered.model_copy(deep=True)
            recovered.offline_mode = not recovered.offline_mode
        elif mismatch == "ordinal":
            recovered = recovered.model_copy(deep=True)
            recovered.parts[0].ordinal_number = 2
        saved = state.to_json() if serialized_state else state
        if serialized_state:
            # A failed caller-side save must leave the exact recovery objects usable.
            with monkeypatch.context() as patch:

                def fail_save(*args: object, **kwargs: object) -> int:
                    raise OSError("protected store unavailable")

                patch.setattr(Path, "write_text", fail_save)
                with pytest.raises(OSError, match="protected store unavailable"):
                    (tmp_path / "prepared.json").write_text(
                        recovered.to_sensitive_json()
                    )
            (tmp_path / "prepared.json").write_text(recovered.to_sensitive_json())
            (tmp_path / "session.json").write_text(state.to_json())
            recovered = PreparedBatch.from_sensitive_json(
                (tmp_path / "prepared.json").read_text()
            )
            saved = (tmp_path / "session.json").read_text()
            # Rebuild the SDK client as after a restart, without preparing again.
            auth_state = auth.resume_state()
            flavor.run(
                client.aclose() if isinstance(client, AsyncClient) else client.close()
            )
            client = (
                AsyncClient(Environment.TEST, http_client=http)
                if isinstance(http, httpx.AsyncClient)
                else Client(Environment.TEST, http_client=http)
            )
            auth = client.authentication.resume(auth_state)
        if mismatch is not None:
            with pytest.raises(KSeFValidationError, match="original prepared batch"):
                _ = flavor.run(
                    auth.batch_session(state=saved, prepared_batch=recovered)
                )
            assert len(uploaded) == 1
        else:
            session = flavor.run(
                auth.batch_session(state=saved, prepared_batch=recovered)
            )
            flavor.run(session.upload_parts())
            flavor.run(session.aclose() if flavor.is_async else session.close())
            assert session.reference_number == state.reference_number
            assert uploaded == [recovered.parts[0].content, recovered.parts[0].content]
        assert (
            sum(
                request.method == "POST"
                and request.url.path.endswith("/sessions/batch")
                for request in calls
            )
            == 1
        )
    finally:
        flavor.run(
            client.aclose() if isinstance(client, AsyncClient) else client.close()
        )
        flavor.run(
            http.aclose() if isinstance(http, httpx.AsyncClient) else http.close()
        )
