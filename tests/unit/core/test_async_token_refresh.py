"""Automatic access-token refresh: proactive, reactive, single-flight, failure, opt-out."""

import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from ksef2 import AsyncClient, Environment, TransportConfig
from ksef2._core.async_protocols import AsyncMiddleware
from ksef2._core.middlewares.async_base import AsyncBaseMiddleware
from ksef2._core.async_token_manager import (
    ACCESS_TOKEN_REFRESH_MARGIN,
    AsyncTokenManager,
)
from ksef2._core.exceptions import (
    KSeFAuthenticationExpiredError,
    KSeFAuthError,
)
from ksef2._core.middlewares.async_auth import AsyncBearerTokenMiddleware
from ksef2._core.middlewares.async_exceptions import AsyncKSeFExceptionMiddleware
from ksef2._domain.models.auth import (
    AuthenticationResumeState,
    AuthTokens,
    RefreshedToken,
    TokenCredentials,
)

T0 = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


def _tokens(
    *,
    access_in: timedelta = timedelta(minutes=15),
    refresh_in: timedelta = timedelta(days=7),
    access: str = "access-1",
    now: datetime = T0,
) -> AuthTokens:
    return AuthTokens(
        access_token=TokenCredentials(token=access, valid_until=now + access_in),
        refresh_token=TokenCredentials(token="refresh-1", valid_until=now + refresh_in),
    )


class Refresher:
    """Counts refresh calls and hands out ``access-2``, ``access-3``, ..."""

    def __init__(self, clock: FakeClock, *, fail_with: Exception | None = None) -> None:
        self.clock = clock
        self.fail_with = fail_with
        self.calls: list[str] = []

    async def __call__(self, refresh_token: str) -> RefreshedToken:
        self.calls.append(refresh_token)
        await asyncio.sleep(0)  # let concurrent requests pile up on the lock
        if self.fail_with is not None:
            raise self.fail_with
        return RefreshedToken(
            access_token=TokenCredentials(
                token=f"access-{len(self.calls) + 1}",
                valid_until=self.clock.now + timedelta(minutes=15),
            )
        )


class Server(AsyncBaseMiddleware):
    """Accepts only ``valid`` bearer tokens; everything else is a 401."""

    def __init__(self, valid: set[str], *, rejection: int = 401) -> None:
        self.valid = valid
        self.rejection = rejection
        self.seen: list[str] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: object = None,
        json: object = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        auth = (headers or {})["Authorization"].removeprefix("Bearer ")
        self.seen.append(auth)
        if auth in self.valid:
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(self.rejection, json={})


def _chain(
    server: AsyncMiddleware, manager: AsyncTokenManager
) -> AsyncBearerTokenMiddleware:
    return AsyncBearerTokenMiddleware(AsyncKSeFExceptionMiddleware(server), manager)


class TestProactiveRefresh:
    async def test_refreshes_inside_the_margin_before_sending(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(access_in=ACCESS_TOKEN_REFRESH_MARGIN - timedelta(seconds=1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-2"})

        response = await _chain(server, manager).get("/limits")

        assert response.status_code == 200
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-2"]

    async def test_waits_for_the_margin_to_start(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(minutes=5)), refresher, clock=clock
        )
        server = Server({"access-1", "access-2"})
        chain = _chain(server, manager)

        _ = await chain.get("/limits")
        assert refresher.calls == []

        clock.advance(timedelta(minutes=5) - ACCESS_TOKEN_REFRESH_MARGIN)
        _ = await chain.get("/limits")
        _ = await chain.get("/limits")

        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2", "access-2"]

    async def test_expired_refresh_token_does_not_block_a_still_valid_access_token(
        self,
    ) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(seconds=30), refresh_in=timedelta(seconds=-1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-1"})

        response = await _chain(server, manager).get("/limits")

        assert response.status_code == 200
        assert refresher.calls == []

    async def test_current_tokens_reflect_the_refresh(self) -> None:
        clock = FakeClock()
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(seconds=5)), Refresher(clock), clock=clock
        )

        _ = await manager.get_access_token()

        assert manager.tokens.access_token.token == "access-2"
        assert manager.tokens.refresh_token.token == "refresh-1"


class TestReactiveRefresh:
    async def test_401_triggers_one_refresh_and_one_retry(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)
        server = Server({"access-2"})

        response = await _chain(server, manager).post("/sessions/online")

        assert response.status_code == 200
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2"]

    async def test_a_second_401_is_raised_without_another_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)
        server = Server(set())

        with pytest.raises(KSeFAuthError) as excinfo:
            _ = await _chain(server, manager).get("/limits")

        assert not isinstance(excinfo.value, KSeFAuthenticationExpiredError)
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2"]

    async def test_403_is_not_refreshed(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(KSeFAuthError):
            _ = await _chain(Server(set(), rejection=403), manager).get("/limits")

        assert refresher.calls == []


class TestSingleFlight:
    async def test_concurrent_stale_requests_share_one_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(seconds=5)), refresher, clock=clock
        )
        server = Server({"access-2"})
        chain = _chain(server, manager)

        responses = await asyncio.gather(*(chain.get("/limits") for _ in range(10)))

        assert [r.status_code for r in responses] == [200] * 10
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-2"] * 10

    async def test_concurrent_401s_share_one_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)
        server = Server({"access-2"})
        chain = _chain(server, manager)

        responses = await asyncio.gather(*(chain.get("/limits") for _ in range(10)))

        assert [r.status_code for r in responses] == [200] * 10
        assert refresher.calls == ["refresh-1"]


class TestRefreshFailure:
    async def test_expired_refresh_token_with_expired_access_token_raises(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(seconds=-1), refresh_in=timedelta(seconds=-1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-1"})

        with pytest.raises(KSeFAuthenticationExpiredError, match="Authenticate again"):
            _ = await _chain(server, manager).get("/limits")

        assert refresher.calls == []
        assert server.seen == []

    async def test_expired_refresh_token_after_a_401_raises(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = AsyncTokenManager(
            _tokens(refresh_in=timedelta(seconds=-1)), refresher, clock=clock
        )

        with pytest.raises(KSeFAuthenticationExpiredError):
            _ = await _chain(Server(set()), manager).get("/limits")

        assert refresher.calls == []

    async def test_rejected_refresh_token_raises_the_dedicated_error(self) -> None:
        clock = FakeClock()
        refresher = Refresher(
            clock, fail_with=KSeFAuthError(status_code=401, message="refresh rejected")
        )
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(KSeFAuthenticationExpiredError) as excinfo:
            _ = await _chain(Server(set()), manager).get("/limits")

        assert isinstance(excinfo.value, KSeFAuthError)
        assert "Authenticate again" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, KSeFAuthError)

    async def test_other_refresh_failures_are_not_reported_as_expiry(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock, fail_with=httpx.ConnectError("down"))
        manager = AsyncTokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(httpx.ConnectError):
            _ = await _chain(Server(set()), manager).get("/limits")


class TestOptOut:
    async def test_disabled_manager_never_refreshes(self) -> None:
        clock = FakeClock()
        manager = AsyncTokenManager(
            _tokens(access_in=timedelta(seconds=-1)), None, clock=clock
        )
        server = Server(set())

        with pytest.raises(KSeFAuthError) as excinfo:
            _ = await _chain(server, manager).get("/limits")

        assert not isinstance(excinfo.value, KSeFAuthenticationExpiredError)
        assert server.seen == ["access-1"]


def _mock_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    config: TransportConfig | None = None,
) -> AsyncClient:
    return AsyncClient(
        Environment.TEST,
        transport_config=config,
        http_client=httpx.AsyncClient(
            base_url=Environment.TEST.base_url,
            transport=httpx.MockTransport(handler),
        ),
    )


def _resume_state(*, access_in: timedelta) -> AuthenticationResumeState:
    return AuthenticationResumeState.from_tokens(
        _tokens(access_in=access_in, now=datetime.now(UTC))
    )


def _refresh_aware_handler(
    requests: list[httpx.Request],
) -> Callable[[httpx.Request], httpx.Response]:
    valid_until = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        bearer = request.headers["Authorization"]
        if request.url.path.endswith("/auth/token/refresh"):
            assert bearer == "Bearer refresh-1"
            return httpx.Response(
                200,
                json={
                    "accessToken": {"token": "access-new", "validUntil": valid_until}
                },
            )
        if bearer == "Bearer access-new":
            return httpx.Response(204)
        return httpx.Response(401, json={})

    return handler


class TestResumedClient:
    async def test_expired_state_refreshes_and_exposes_current_tokens(self) -> None:
        requests: list[httpx.Request] = []
        client = _mock_client(_refresh_aware_handler(requests))
        auth = client.authentication.resume(
            _resume_state(access_in=timedelta(minutes=-5))
        )

        await auth.sessions.terminate_current()

        assert [r.url.path.rsplit("/v2", 1)[-1] for r in requests] == [
            "/auth/token/refresh",
            "/auth/sessions/current",
        ]
        assert auth.auth_tokens.access_token.token == "access-new"
        assert auth.access_token == "access-new"
        assert auth.refresh_token == "refresh-1"
        state = json.loads(auth.resume_state().to_json())
        assert state["access_token"] == "access-new"
        assert state["refresh_token"] == "refresh-1"

    async def test_opting_out_through_transport_config(self) -> None:
        requests: list[httpx.Request] = []
        client = _mock_client(
            _refresh_aware_handler(requests),
            config=TransportConfig(auto_refresh_tokens=False),
        )
        auth = client.authentication.resume(
            _resume_state(access_in=timedelta(minutes=-5))
        )

        with pytest.raises(KSeFAuthError):
            await auth.sessions.terminate_current()

        assert all("/auth/token/refresh" not in r.url.path for r in requests)
        assert auth.access_token == "access-1"
