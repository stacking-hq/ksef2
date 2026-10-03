"""Every deprecated API warns exactly once with the 2.0 message and still works."""

import asyncio
import os
import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from polyfactory import BaseFactory
from pydantic import SecretStr

from ksef2 import AsyncClient, Client, Environment
from ksef2.clients.async_authenticated import AsyncAuthenticatedClient
from ksef2.clients.async_batch import AsyncBatchSessionClient
from ksef2.clients.async_online import AsyncOnlineSessionClient
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.clients.batch import BatchSessionClient
from ksef2.clients.online import OnlineSessionClient
from ksef2.domain.models.auth import AuthTokens
from ksef2.domain.models.batch import BatchSessionResumeState
from ksef2.domain.models.session import FormSchema, OnlineSessionResumeState
from tests.unit.fakes.transport import AsyncFakeTransport, FakeTransport

AES_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
IV = "MDEyMzQ1Njc4OWFiY2RlZg=="
SUFFIX = "will be removed in ksef2 2.0; use `{new}` instead."


def _call_once[T](call: Callable[[], T], old: str, new: str) -> T:
    """Run ``call``, assert exactly one DeprecationWarning with the 2.0 message."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = call()
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 1, [str(w.message) for w in deprecations]
    message = str(deprecations[0].message)
    assert message.startswith(f"`{old}` is deprecated and ")
    assert message.endswith(SUFFIX.format(new=new))
    if not os.environ.get("KSEF2_RUNTIME_CHECKS"):
        # beartype's wrapper frame sits between the SDK and the caller.
        assert deprecations[0].filename == __file__
    return result


def _online_state() -> OnlineSessionResumeState:
    return OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr(AES_KEY),
        iv=SecretStr(IV),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )


class TestRootClients:
    def test_client_authenticated(
        self, domain_auth_tokens: BaseFactory[AuthTokens]
    ) -> None:
        tokens = domain_auth_tokens.build()
        client = Client(
            environment=Environment.TEST, http_client=MagicMock(spec=httpx.Client)
        )
        authenticated = _call_once(
            lambda: client.authenticated(tokens),
            "Client.authenticated()",
            "Client.authentication.resume()` with "
            "`AuthenticationResumeState.from_tokens()",
        )
        assert isinstance(authenticated, AuthenticatedClient)
        assert authenticated.resume_state().to_tokens() == tokens

    def test_async_client_authenticated(
        self, domain_auth_tokens: BaseFactory[AuthTokens]
    ) -> None:
        tokens = domain_auth_tokens.build()
        client = AsyncClient(
            environment=Environment.TEST,
            http_client=AsyncMock(spec=httpx.AsyncClient),
        )
        try:
            authenticated = _call_once(
                lambda: client.authenticated(tokens),
                "AsyncClient.authenticated()",
                "AsyncClient.authentication.resume()` with "
                "`AuthenticationResumeState.from_tokens()",
            )
        finally:
            asyncio.run(client.aclose())
        assert isinstance(authenticated, AsyncAuthenticatedClient)
        assert authenticated.resume_state().to_tokens() == tokens


class TestSessionClients:
    def test_online_get_state(
        self,
        fake_transport: FakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        state = domain_online_session_state.build()
        client = OnlineSessionClient(fake_transport, state)
        assert _call_once(client.get_state, "get_state()", "resume_state()") == state

    def test_async_online_get_state(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    ) -> None:
        state = domain_online_session_state.build()
        client = AsyncOnlineSessionClient(async_fake_transport, state)
        assert _call_once(client.get_state, "get_state()", "resume_state()") == state

    def test_batch_get_state_and_access_token(
        self,
        fake_transport: FakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = BatchSessionClient(fake_transport, state, access_token="token")
        assert _call_once(client.get_state, "get_state()", "resume_state()") == state
        assert (
            _call_once(
                lambda: client.access_token,
                "BatchSessionClient.access_token",
                "AuthenticatedClient.access_token",
            )
            == "token"
        )

    def test_async_batch_get_state_and_access_token(
        self,
        async_fake_transport: AsyncFakeTransport,
        domain_batch_session_state: BaseFactory[BatchSessionResumeState],
    ) -> None:
        state = domain_batch_session_state.build()
        client = AsyncBatchSessionClient(
            async_fake_transport, state, access_token="token"
        )
        assert _call_once(client.get_state, "get_state()", "resume_state()") == state
        assert (
            _call_once(
                lambda: client.access_token,
                "BatchSessionClient.access_token",
                "AuthenticatedClient.access_token",
            )
            == "token"
        )


class TestResumeStateMethods:
    def test_dump_state(self) -> None:
        state = _online_state()
        dumped = _call_once(state.dump_state, "dump_state()", "to_dict()")
        assert dumped == state.to_dict(mode="python")

    def test_model_dump_sensitive(self) -> None:
        state = _online_state()
        dumped = _call_once(
            state.model_dump_sensitive, "model_dump_sensitive()", "to_dict()"
        )
        assert dumped == state.to_dict(mode="python")

    def test_model_dump_sensitive_json(self) -> None:
        state = _online_state()
        dumped = _call_once(
            state.model_dump_sensitive_json, "model_dump_sensitive_json()", "to_json()"
        )
        assert dumped == state.to_json()

    def test_from_state(self) -> None:
        state = _online_state()
        restored = _call_once(
            lambda: OnlineSessionResumeState.from_state(state.to_dict()),
            "from_state()",
            "from_dict()",
        )
        assert restored == state


class TestModuleAliases:
    @pytest.mark.parametrize(
        ("module", "name", "target"),
        [
            ("ksef2.models", "BaseSessionState", "BaseSessionResumeState"),
            ("ksef2.models", "OnlineSessionState", "OnlineSessionResumeState"),
            ("ksef2.models", "BatchSessionState", "BatchSessionResumeState"),
            ("ksef2.domain.models", "BaseSessionState", "BaseSessionResumeState"),
            ("ksef2.domain.models", "OnlineSessionState", "OnlineSessionResumeState"),
            ("ksef2.domain.models", "BatchSessionState", "BatchSessionResumeState"),
            (
                "ksef2.domain.models.session",
                "OnlineSessionState",
                "OnlineSessionResumeState",
            ),
            (
                "ksef2.domain.models.batch",
                "BatchSessionState",
                "BatchSessionResumeState",
            ),
        ],
    )
    def test_alias_warns_once(self, module: str, name: str, target: str) -> None:
        import importlib

        mod = importlib.import_module(module)
        value = _call_once(lambda: getattr(mod, name), f"{module}.{name}", target)
        assert value.__name__ == target


class TestIgnoredLegacyInputs:
    def test_stored_access_token_key_still_loads_and_warns_once(self) -> None:
        state = _online_state()
        legacy = state.to_dict()
        legacy["access_token"] = "secret"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            restored = OnlineSessionResumeState.from_dict(legacy)
        assert len(caught) == 1
        assert "will be removed in ksef2 2.0" in str(caught[0].message)
        assert restored == state

    def test_from_encoded_access_token_argument_warns_once(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            state = OnlineSessionResumeState.from_encoded(
                "ref",
                b"0123456789abcdef0123456789abcdef",
                b"0123456789abcdef",
                datetime(2026, 1, 1, tzinfo=UTC),
                FormSchema.FA3,
                access_token="secret",
            )
        assert len(caught) == 1
        assert "will be removed in ksef2 2.0" in str(caught[0].message)
        assert state.reference_number == "ref"
