"""Sync twin of test_token_refresh: automatic access-token refresh: proactive, reactive, single-flight, failure, opt-out."""

import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from ksef2 import Client, Environment, TransportConfig
from ksef2._core.protocols import Middleware
from ksef2._core.middlewares.base import BaseMiddleware
from ksef2._core.token_manager import (
    ACCESS_TOKEN_REFRESH_MARGIN,
    TokenManager,
)
from ksef2._core.exceptions import (
    KSeFAuthenticationExpiredError,
    KSeFAuthError,
)
from ksef2._core.middlewares.auth import BearerTokenMiddleware
from ksef2._core.middlewares.exceptions import KSeFExceptionMiddleware
from ksef2._domain.models.auth import (
    AuthenticationResumeState,
    AuthTokens,
    RefreshedToken,
    TokenCredentials,
)

T0 = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


def _concurrently(fn: Callable[[], httpx.Response], count: int) -> list[httpx.Response]:
    results: list[httpx.Response] = []
    barrier = threading.Barrier(count)

    def run() -> None:
        _ = barrier.wait()
        results.append(fn())

    threads = [threading.Thread(target=run) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


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

    def __call__(self, refresh_token: str) -> RefreshedToken:
        self.calls.append(refresh_token)
        time.sleep(0.01)  # let concurrent requests pile up on the lock
        if self.fail_with is not None:
            raise self.fail_with
        return RefreshedToken(
            access_token=TokenCredentials(
                token=f"access-{len(self.calls) + 1}",
                valid_until=self.clock.now + timedelta(minutes=15),
            )
        )


class Server(BaseMiddleware):
    """Accepts only ``valid`` bearer tokens; everything else is a 401."""

    def __init__(self, valid: set[str], *, rejection: int = 401) -> None:
        self.valid = valid
        self.rejection = rejection
        self.seen: list[str] = []

    def request(
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


def _chain(server: Middleware, manager: TokenManager) -> BearerTokenMiddleware:
    return BearerTokenMiddleware(KSeFExceptionMiddleware(server), manager)


class TestProactiveRefresh:
    def test_refreshes_inside_the_margin_before_sending(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(access_in=ACCESS_TOKEN_REFRESH_MARGIN - timedelta(seconds=1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-2"})

        response = _chain(server, manager).get("/limits")

        assert response.status_code == 200
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-2"]

    def test_waits_for_the_margin_to_start(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(access_in=timedelta(minutes=5)), refresher, clock=clock
        )
        server = Server({"access-1", "access-2"})
        chain = _chain(server, manager)

        _ = chain.get("/limits")
        assert refresher.calls == []

        clock.advance(timedelta(minutes=5) - ACCESS_TOKEN_REFRESH_MARGIN)
        _ = chain.get("/limits")
        _ = chain.get("/limits")

        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2", "access-2"]

    def test_expired_refresh_token_does_not_block_a_still_valid_access_token(
        self,
    ) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(access_in=timedelta(seconds=30), refresh_in=timedelta(seconds=-1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-1"})

        response = _chain(server, manager).get("/limits")

        assert response.status_code == 200
        assert refresher.calls == []

    def test_current_tokens_reflect_the_refresh(self) -> None:
        clock = FakeClock()
        manager = TokenManager(
            _tokens(access_in=timedelta(seconds=5)), Refresher(clock), clock=clock
        )

        _ = manager.get_access_token()

        assert manager.tokens.access_token.token == "access-2"
        assert manager.tokens.refresh_token.token == "refresh-1"


class TestReactiveRefresh:
    def test_401_triggers_one_refresh_and_one_retry(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(_tokens(), refresher, clock=clock)
        server = Server({"access-2"})

        response = _chain(server, manager).post("/sessions/online")

        assert response.status_code == 200
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2"]

    def test_a_second_401_is_raised_without_another_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(_tokens(), refresher, clock=clock)
        server = Server(set())

        with pytest.raises(KSeFAuthError) as excinfo:
            _ = _chain(server, manager).get("/limits")

        assert not isinstance(excinfo.value, KSeFAuthenticationExpiredError)
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-1", "access-2"]

    def test_403_is_not_refreshed(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(KSeFAuthError):
            _ = _chain(Server(set(), rejection=403), manager).get("/limits")

        assert refresher.calls == []


class TestSingleFlight:
    def test_concurrent_stale_requests_share_one_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(access_in=timedelta(seconds=5)), refresher, clock=clock
        )
        server = Server({"access-2"})
        chain = _chain(server, manager)

        responses = _concurrently(lambda: chain.get("/limits"), 10)

        assert [r.status_code for r in responses] == [200] * 10
        assert refresher.calls == ["refresh-1"]
        assert server.seen == ["access-2"] * 10

    def test_concurrent_401s_share_one_refresh(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(_tokens(), refresher, clock=clock)
        server = Server({"access-2"})
        chain = _chain(server, manager)

        responses = _concurrently(lambda: chain.get("/limits"), 10)

        assert [r.status_code for r in responses] == [200] * 10
        assert refresher.calls == ["refresh-1"]


class TestRefreshFailure:
    def test_expired_refresh_token_with_expired_access_token_raises(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(access_in=timedelta(seconds=-1), refresh_in=timedelta(seconds=-1)),
            refresher,
            clock=clock,
        )
        server = Server({"access-1"})

        with pytest.raises(KSeFAuthenticationExpiredError, match="Authenticate again"):
            _ = _chain(server, manager).get("/limits")

        assert refresher.calls == []
        assert server.seen == []

    def test_expired_refresh_token_after_a_401_raises(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock)
        manager = TokenManager(
            _tokens(refresh_in=timedelta(seconds=-1)), refresher, clock=clock
        )

        with pytest.raises(KSeFAuthenticationExpiredError):
            _ = _chain(Server(set()), manager).get("/limits")

        assert refresher.calls == []

    def test_rejected_refresh_token_raises_the_dedicated_error(self) -> None:
        clock = FakeClock()
        refresher = Refresher(
            clock, fail_with=KSeFAuthError(status_code=401, message="refresh rejected")
        )
        manager = TokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(KSeFAuthenticationExpiredError) as excinfo:
            _ = _chain(Server(set()), manager).get("/limits")

        assert isinstance(excinfo.value, KSeFAuthError)
        assert "Authenticate again" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, KSeFAuthError)

    def test_other_refresh_failures_are_not_reported_as_expiry(self) -> None:
        clock = FakeClock()
        refresher = Refresher(clock, fail_with=httpx.ConnectError("down"))
        manager = TokenManager(_tokens(), refresher, clock=clock)

        with pytest.raises(httpx.ConnectError):
            _ = _chain(Server(set()), manager).get("/limits")


class TestOptOut:
    def test_disabled_manager_never_refreshes(self) -> None:
        clock = FakeClock()
        manager = TokenManager(
            _tokens(access_in=timedelta(seconds=-1)), None, clock=clock
        )
        server = Server(set())

        with pytest.raises(KSeFAuthError) as excinfo:
            _ = _chain(server, manager).get("/limits")

        assert not isinstance(excinfo.value, KSeFAuthenticationExpiredError)
        assert server.seen == ["access-1"]


def _mock_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    config: TransportConfig | None = None,
) -> Client:
    return Client(
        Environment.TEST,
        transport_config=config,
        http_client=httpx.Client(
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
    def test_expired_state_refreshes_and_exposes_current_tokens(self) -> None:
        requests: list[httpx.Request] = []
        client = _mock_client(_refresh_aware_handler(requests))
        auth = client.authentication.resume(
            _resume_state(access_in=timedelta(minutes=-5))
        )

        auth.sessions.terminate_current()

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

    def test_opting_out_through_transport_config(self) -> None:
        requests: list[httpx.Request] = []
        client = _mock_client(
            _refresh_aware_handler(requests),
            config=TransportConfig(auto_refresh_tokens=False),
        )
        auth = client.authentication.resume(
            _resume_state(access_in=timedelta(minutes=-5))
        )

        with pytest.raises(KSeFAuthError):
            auth.sessions.terminate_current()

        assert all("/auth/token/refresh" not in r.url.path for r in requests)
        assert auth.access_token == "access-1"
