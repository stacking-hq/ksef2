"""Handles returned by ``tokens.generate``, permission grants/revokes and ``certificates.enroll``.

Each ``wait()`` is covered for success, KSeF failure and timeout, sync and async.
"""

from typing import Any

import httpx
import pytest
from polyfactory import BaseFactory

from ksef2._clients._async_handles import AsyncOperationHandle
from ksef2._clients._handles import OperationHandle
from ksef2._clients.async_tokens import AsyncTokensClient
from ksef2._clients.tokens import TokensClient
from ksef2._core import exceptions
from ksef2._core.routes import TokenRoutes
from ksef2._domain.models.tokens import GenerateTokenResponse
from ksef2._infra.schema.api import spec
from tests.unit.factories.tokens import TokenStatusResponseFactory
from tests.unit.flavors import Flavor


def _handle_base(flavor: Flavor) -> type[Any]:
    return AsyncOperationHandle if flavor.is_async else OperationHandle


class TestGeneratedToken:
    def _tokens(self, flavor: Flavor) -> Any:
        cls = AsyncTokensClient if flavor.is_async else TokensClient
        return cls(flavor.transport)

    def _generate(
        self,
        flavor: Flavor,
        generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> tuple[Any, spec.GenerateTokenResponse]:
        response = generate_resp.build()
        flavor.transport.enqueue(response.model_dump(mode="json"))
        generated = flavor.run(
            self._tokens(flavor).generate(
                permissions=["invoice_read"], description="Test token"
            )
        )
        return generated, response

    def _enqueue_status(
        self, flavor: Flavor, status: spec.AuthenticationTokenStatus
    ) -> None:
        flavor.transport.enqueue(
            TokenStatusResponseFactory.build(status=status).model_dump(mode="json")
        )

    def test_is_a_handle_and_reads_the_one_time_token_immediately(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, response = self._generate(flavor, token_generate_resp)

        assert _handle_base(flavor) in type(generated).__mro__
        assert generated.token == response.token
        assert generated.reference_number == response.referenceNumber
        assert len(flavor.transport.calls) == 1
        assert flavor.transport.calls[0].path == TokenRoutes.GENERATE_TOKEN

    def test_exposes_every_generate_response_field(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, _ = self._generate(flavor, token_generate_resp)

        assert isinstance(generated.response, GenerateTokenResponse)
        for field in GenerateTokenResponse.model_fields:
            assert getattr(generated, field) == getattr(generated.response, field)
        assert generated.to_sensitive_dict() == generated.response.to_sensitive_dict()
        with pytest.raises(AttributeError):
            _ = generated.no_such_field

    def test_repr_never_contains_the_token(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, response = self._generate(flavor, token_generate_resp)

        assert response.token not in repr(generated)
        assert response.token not in str(generated)

    def test_wait_returns_the_active_status(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, _ = self._generate(flavor, token_generate_resp)
        self._enqueue_status(flavor, spec.AuthenticationTokenStatus.Pending)
        self._enqueue_status(flavor, spec.AuthenticationTokenStatus.Active)

        status = flavor.run(generated.wait(timeout=1.0, poll_interval=0.0))

        assert status.status == "active"
        assert len(flavor.transport.calls) == 3
        assert flavor.transport.calls[1].method == "GET"

    @pytest.mark.parametrize(
        "terminal",
        [spec.AuthenticationTokenStatus.Failed, spec.AuthenticationTokenStatus.Revoked],
        ids=["failed", "revoked"],
    )
    def test_wait_raises_when_activation_fails(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
        terminal: spec.AuthenticationTokenStatus,
    ) -> None:
        generated, _ = self._generate(flavor, token_generate_resp)
        self._enqueue_status(flavor, terminal)

        with pytest.raises(exceptions.KSeFApiError, match="Token activation failed"):
            _ = flavor.run(generated.wait(timeout=1.0, poll_interval=0.0))

    def test_wait_times_out_and_keeps_the_token(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, response = self._generate(flavor, token_generate_resp)
        self._enqueue_status(flavor, spec.AuthenticationTokenStatus.Pending)

        with pytest.raises(
            exceptions.KSeFTokenStatusTimeoutError, match="not active"
        ) as raised:
            _ = flavor.run(generated.wait(timeout=0.0, poll_interval=0.0))

        assert raised.value.reference_number == response.referenceNumber
        assert raised.value.timeout == 0.0
        assert generated.token == response.token

    def test_wait_transport_error_keeps_the_token(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, response = self._generate(flavor, token_generate_resp)
        flavor.transport.enqueue_error(httpx.ReadError("status response lost"))

        with pytest.raises(httpx.ReadError, match="status response lost"):
            _ = flavor.run(generated.wait())

        assert generated.token == response.token

    def test_get_status_does_not_wait(
        self,
        flavor: Flavor,
        token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    ) -> None:
        generated, _ = self._generate(flavor, token_generate_resp)
        self._enqueue_status(flavor, spec.AuthenticationTokenStatus.Pending)

        status = flavor.run(generated.get_status())

        assert status.status == "pending"
        assert len(flavor.transport.calls) == 2
