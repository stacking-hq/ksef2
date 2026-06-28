from datetime import UTC, datetime
from typing import cast

import pytest
from pydantic import SecretStr

from ksef2.domain.models.auth import (
    AuthenticationResumeState,
    AuthTokens,
    TokenCredentials,
)
from ksef2.domain.models.batch import (
    BatchSessionResumeState,
    PartUploadRequest,
)
from ksef2.domain.models.session import (
    BaseSessionResumeState,
    FormSchema,
    OnlineSessionResumeState,
)

AES_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
IV = "MDEyMzQ1Njc4OWFiY2RlZg=="
ACCESS_TOKEN = "secret-access-token"
UPLOAD_URL = "https://example.com/upload/part-1?sig=secret-upload-url"


def test_online_session_state_redacts_sensitive_fields_in_default_dump_and_repr() -> (
    None
):
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )

    dumped = state.model_dump()
    json_dump = state.model_dump_json()
    representation = repr(state)

    assert dumped["reference_number"] == state.reference_number
    assert str(cast(object, dumped["aes_key"])) == "**********"
    assert str(cast(object, dumped["iv"])) == "**********"
    assert "access_token" not in dumped
    for secret in [AES_KEY, IV, ACCESS_TOKEN]:
        assert secret not in json_dump
        assert secret not in representation


def test_online_session_state_sensitive_export_round_trips_for_resume() -> None:
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )

    sensitive_dump = state.to_dict()
    sensitive_json = state.to_json()

    assert sensitive_dump["aes_key"] == AES_KEY
    assert sensitive_dump["iv"] == IV
    assert "access_token" not in sensitive_dump
    assert sensitive_dump["form_code"] == "FA3"
    for secret in [AES_KEY, IV]:
        assert secret in sensitive_json
    assert ACCESS_TOKEN not in sensitive_json
    assert '"form_code":"FA3"' in sensitive_json

    restored = OnlineSessionResumeState.from_json(sensitive_json)

    assert restored.reference_number == state.reference_number
    assert restored.form_code == FormSchema.FA3
    assert restored.get_aes_key_bytes() == b"0123456789abcdef0123456789abcdef"
    assert restored.get_iv_bytes() == b"0123456789abcdef"


def test_batch_session_state_redacts_credentials_and_omits_upload_urls_by_default() -> (
    None
):
    state = BatchSessionResumeState(
        reference_number="20250625-BS-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        form_code=FormSchema.FA3,
        part_upload_requests=[
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url=UPLOAD_URL,
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ],
    )

    dumped = state.model_dump()
    json_dump = state.model_dump_json()
    representation = repr(state)

    assert str(cast(object, dumped["aes_key"])) == "**********"
    assert str(cast(object, dumped["iv"])) == "**********"
    assert "access_token" not in dumped
    assert "part_upload_requests" not in dumped
    for secret in [AES_KEY, IV, ACCESS_TOKEN, UPLOAD_URL]:
        assert secret not in json_dump
        assert secret not in representation


def test_batch_session_state_sensitive_export_round_trips_for_resume() -> None:
    state = BatchSessionResumeState(
        reference_number="20250625-BS-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        form_code=FormSchema.FA3,
        part_upload_requests=[
            PartUploadRequest(
                ordinal_number=1,
                method="PUT",
                url=UPLOAD_URL,
                headers={"x-ms-blob-type": "BlockBlob"},
            )
        ],
    )

    sensitive_dump = state.to_dict()
    sensitive_json = state.to_json()

    assert sensitive_dump["aes_key"] == AES_KEY
    assert sensitive_dump["iv"] == IV
    assert "access_token" not in sensitive_dump
    assert sensitive_dump["form_code"] == "FA3"
    for secret in [AES_KEY, IV, UPLOAD_URL]:
        assert secret in sensitive_json
    assert ACCESS_TOKEN not in sensitive_json
    assert '"form_code":"FA3"' in sensitive_json

    restored = BatchSessionResumeState.from_json(sensitive_json)

    assert restored.reference_number == state.reference_number
    assert restored.form_code == FormSchema.FA3
    assert restored.part_upload_requests[0].url == UPLOAD_URL
    assert restored.get_aes_key_bytes() == b"0123456789abcdef0123456789abcdef"
    assert restored.get_iv_bytes() == b"0123456789abcdef"


def test_deprecated_state_model_imports_warn() -> None:
    with pytest.deprecated_call(match="BaseSessionState"):
        from ksef2.domain.models.session import BaseSessionState as LegacyBaseState

    with pytest.deprecated_call(match="OnlineSessionState"):
        from ksef2.domain.models.session import OnlineSessionState as LegacyOnlineState

    with pytest.deprecated_call(match="BatchSessionState"):
        from ksef2.domain.models.batch import BatchSessionState as LegacyBatchState

    base_state = LegacyBaseState
    online_state = LegacyOnlineState
    batch_state = LegacyBatchState

    assert base_state is BaseSessionResumeState
    assert online_state is OnlineSessionResumeState
    assert batch_state is BatchSessionResumeState


def test_deprecated_state_facade_imports_warn() -> None:
    import ksef2.domain.models as domain_models
    import ksef2.models as facade_models

    assert "OnlineSessionState" not in domain_models.__all__
    assert "BatchSessionState" not in domain_models.__all__
    assert "OnlineSessionState" not in facade_models.__all__
    assert "BatchSessionState" not in facade_models.__all__

    with pytest.deprecated_call(match="ksef2.domain.models.OnlineSessionState"):
        from ksef2.domain.models import OnlineSessionState as DomainOnlineState

    with pytest.deprecated_call(match="ksef2.models.BatchSessionState"):
        from ksef2.models import BatchSessionState as FacadeBatchState

    domain_online_state = DomainOnlineState
    facade_batch_state = FacadeBatchState

    assert domain_online_state is OnlineSessionResumeState
    assert facade_batch_state is BatchSessionResumeState


def test_deprecated_state_export_methods_delegate_to_resume_api() -> None:
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )

    with pytest.deprecated_call(match="dump_state"):
        sensitive_dump = state.dump_state()
    with pytest.deprecated_call(match="model_dump_sensitive_json"):
        sensitive_json = state.model_dump_sensitive_json()
    with pytest.deprecated_call(match="from_state"):
        restored = OnlineSessionResumeState.from_state(sensitive_dump)

    assert sensitive_dump == state.to_dict(mode="python")
    assert sensitive_json == state.to_json()
    assert restored == state


def test_legacy_session_state_access_token_is_ignored_with_warning() -> None:
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )
    legacy_state = state.to_dict()
    legacy_state["access_token"] = ACCESS_TOKEN

    with pytest.deprecated_call(match="access_token"):
        restored = OnlineSessionResumeState.from_dict(legacy_state)

    assert restored == state
    assert "access_token" not in restored.to_dict()


def test_authentication_resume_state_round_trips_with_explicit_sensitive_export() -> (
    None
):
    auth_tokens = AuthTokens(
        access_token=TokenCredentials(
            token=ACCESS_TOKEN,
            valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        refresh_token=TokenCredentials(
            token="secret-refresh-token",
            valid_until=datetime(2026, 1, 2, tzinfo=UTC),
        ),
    )

    state = AuthenticationResumeState.from_tokens(auth_tokens)
    dumped = state.model_dump()
    json_dump = state.model_dump_json()
    sensitive_json = state.to_json()

    assert str(cast(object, dumped["access_token"])) == "**********"
    assert str(cast(object, dumped["refresh_token"])) == "**********"
    assert ACCESS_TOKEN not in json_dump
    assert "secret-refresh-token" not in json_dump
    assert ACCESS_TOKEN in sensitive_json
    assert "secret-refresh-token" in sensitive_json
    assert (
        AuthenticationResumeState.from_json(sensitive_json).to_tokens() == auth_tokens
    )
