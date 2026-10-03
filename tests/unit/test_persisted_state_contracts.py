import json
from datetime import UTC, datetime

import pytest
from pydantic import SecretStr, ValidationError

from ksef2._domain.models.auth import (
    AuthenticationResumeState,
    AuthTokens,
    TokenCredentials,
)
from ksef2._domain.models.fa3.invoice import KsefInvoiceDraft
from ksef2._domain.models.session import FormSchema, OnlineSessionResumeState


AES_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
IV = "MDEyMzQ1Njc4OWFiY2RlZg=="


def test_token_credentials_omit_bearer_from_default_output() -> None:
    credentials = TokenCredentials(
        token="secret-access-token",
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
    )
    tokens = AuthTokens(access_token=credentials, refresh_token=credentials)

    assert "token" not in credentials.model_dump()
    assert "secret-access-token" not in credentials.model_dump_json()
    assert "secret-access-token" not in repr(credentials)
    assert "secret-access-token" not in tokens.model_dump_json()
    assert credentials.token == "secret-access-token"


def test_authentication_state_is_versioned_and_accepts_legacy_version_one() -> None:
    state = AuthenticationResumeState(
        access_token=SecretStr("secret-access-token"),
        access_token_valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        refresh_token=SecretStr("secret-refresh-token"),
        refresh_token_valid_until=datetime(2026, 1, 2, tzinfo=UTC),
    )
    exported = state.to_dict()

    assert exported["format_version"] == 1

    legacy_export = dict(exported)
    _ = legacy_export.pop("format_version")
    assert AuthenticationResumeState.from_dict(legacy_export).format_version == 1


def test_authentication_state_rejects_redacted_future_and_extra_state() -> None:
    state = AuthenticationResumeState(
        access_token=SecretStr("secret-access-token"),
        access_token_valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        refresh_token=SecretStr("secret-refresh-token"),
        refresh_token_valid_until=datetime(2026, 1, 2, tzinfo=UTC),
    )

    with pytest.raises(ValidationError, match="original bearer token"):
        AuthenticationResumeState.from_json(state.model_dump_json())

    future_state = state.to_dict()
    future_state["format_version"] = 2
    with pytest.raises(ValidationError, match="Input should be 1"):
        AuthenticationResumeState.from_dict(future_state)

    state_with_extra = state.to_dict()
    state_with_extra["future_capability"] = "must-not-be-ignored"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AuthenticationResumeState.from_dict(state_with_extra)


def test_session_state_is_versioned_and_rejects_redacted_or_invalid_keys() -> None:
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )
    exported = state.to_dict()

    assert exported["format_version"] == 1
    legacy_export = dict(exported)
    _ = legacy_export.pop("format_version")
    assert OnlineSessionResumeState.from_dict(legacy_export).format_version == 1

    with pytest.raises(ValidationError, match="redacted encryption material"):
        OnlineSessionResumeState.from_json(state.model_dump_json())

    invalid_key_state = dict(exported)
    invalid_key_state["aes_key"] = "not-base64"
    with pytest.raises(ValidationError, match="aes_key must be valid Base64"):
        OnlineSessionResumeState.from_dict(invalid_key_state)

    short_key_state = dict(exported)
    short_key_state["aes_key"] = "eA=="
    with pytest.raises(ValidationError, match="aes_key must decode to 32 bytes"):
        OnlineSessionResumeState.from_dict(short_key_state)


def test_invoice_draft_state_is_versioned_and_fails_on_unknown_shape() -> None:
    draft = KsefInvoiceDraft()
    serialized = json.loads(draft.model_dump_json())

    assert serialized["format_version"] == 1

    _ = serialized.pop("format_version")
    assert KsefInvoiceDraft.model_validate(serialized).format_version == 1

    serialized["format_version"] = 2
    with pytest.raises(ValidationError, match="Input should be 1"):
        KsefInvoiceDraft.model_validate(serialized)

    serialized["format_version"] = 1
    serialized["future_section"] = {}
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        KsefInvoiceDraft.model_validate(serialized)
