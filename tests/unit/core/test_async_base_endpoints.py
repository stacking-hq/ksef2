"""Tests for AsyncBaseEndpoints.

Covers validation contract assertion:
- VAL-CORE-010: AsyncBaseEndpoints awaits transport and parses correctly
"""

import pytest
from pydantic import BaseModel

from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.core.exceptions import KSeFValidationError
from tests.unit.fakes.transport import AsyncFakeTransport


class _SampleModel(BaseModel):
    name: str
    value: int


class _ConcreteEndpoints(AsyncBaseEndpoints):
    """Minimal concrete subclass for testing."""

    async def fetch_one(self, path: str) -> _SampleModel:
        response = await self._transport.get(path)
        return self._parse(response, _SampleModel)

    async def fetch_list(self, path: str) -> list[_SampleModel]:
        response = await self._transport.get(path)
        return self._parse_list(response, _SampleModel)

    async def create(self, path: str, data: dict[str, object]) -> _SampleModel:
        response = await self._transport.post(path, json=data)
        return self._parse(response, _SampleModel)


class TestAsyncBaseEndpointsParse:
    """VAL-CORE-010: AsyncBaseEndpoints _parse works with awaited responses."""

    async def test_parse_returns_model(self) -> None:
        """_parse correctly parses a JSON response into a Pydantic model."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"name": "test", "value": 42})

        endpoints = _ConcreteEndpoints(fake)
        result = await endpoints.fetch_one("/test")

        assert isinstance(result, _SampleModel)
        assert result.name == "test"
        assert result.value == 42

    async def test_parse_list_returns_models(self) -> None:
        """_parse_list correctly parses a JSON array into a list of models."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            json_body=[
                {"name": "first", "value": 1},
                {"name": "second", "value": 2},
            ]
        )

        endpoints = _ConcreteEndpoints(fake)
        results = await endpoints.fetch_list("/test")

        assert len(results) == 2
        assert all(isinstance(r, _SampleModel) for r in results)
        assert results[0].name == "first"
        assert results[1].name == "second"

    async def test_parse_raises_validation_error_on_malformed_json(self) -> None:
        """_parse raises KSeFValidationError on malformed response body."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            content=b'{"name": 123, "value": "not-an-int"}',
            status_code=200,
            headers={"content-type": "application/json"},
        )

        endpoints = _ConcreteEndpoints(fake)
        with pytest.raises(KSeFValidationError, match="Invalid response payload"):
            await endpoints.fetch_one("/test")

    async def test_parse_list_raises_validation_error_on_malformed_json(self) -> None:
        """_parse_list raises KSeFValidationError on malformed response body."""
        fake = AsyncFakeTransport()
        fake.enqueue(
            content=b'[{"name": 123, "value": "not-an-int"}]',
            status_code=200,
            headers={"content-type": "application/json"},
        )

        endpoints = _ConcreteEndpoints(fake)
        with pytest.raises(KSeFValidationError, match="Invalid response payload"):
            await endpoints.fetch_list("/test")

    async def test_transport_is_awaited(self) -> None:
        """Endpoint methods await the transport correctly."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"name": "test", "value": 1})

        endpoints = _ConcreteEndpoints(fake)
        await endpoints.fetch_one("/test")

        assert len(fake.calls) == 1
        assert fake.calls[0].method == "GET"
        assert fake.calls[0].path == "/test"

    async def test_post_transport_is_awaited(self) -> None:
        """POST requests are awaited correctly."""
        fake = AsyncFakeTransport()
        fake.enqueue(json_body={"name": "created", "value": 99})

        endpoints = _ConcreteEndpoints(fake)
        result = await endpoints.create("/test", {"name": "created", "value": 99})

        assert len(fake.calls) == 1
        assert fake.calls[0].method == "POST"
        assert fake.calls[0].json == {"name": "created", "value": 99}
        assert result.name == "created"
        assert result.value == 99


class TestAsyncBaseEndpointsBuildParams:
    """Tests for build_params method on AsyncBaseEndpoints."""

    def test_build_params_drops_none_values(self) -> None:
        """build_params drops None values from the parameter dict."""
        fake = AsyncFakeTransport()
        endpoints = _ConcreteEndpoints(fake)

        result = endpoints.build_params(
            {"pageOffset": 1, "pageSize": None},
        )

        assert "pageOffset" in str(result)
        assert "pageSize" not in str(result)

    def test_build_params_empty_dict(self) -> None:
        """build_params handles empty dict."""
        fake = AsyncFakeTransport()
        endpoints = _ConcreteEndpoints(fake)

        result = endpoints.build_params({})
        assert str(result) == ""
