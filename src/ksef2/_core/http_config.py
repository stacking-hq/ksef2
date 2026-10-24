from typing import TypedDict

import httpx

from ksef2._config import (
    ConnectionPoolConfig,
    Environment,
    TimeoutConfig,
    TlsConfig,
    TransportConfig,
)
from ksef2._core.exceptions import KSeFArgumentError


class HttpClientKwargs(TypedDict):
    base_url: str
    timeout: httpx.Timeout
    limits: httpx.Limits
    verify: bool | str
    proxy: str | None
    trust_env: bool
    http2: bool


def build_http_client_kwargs(
    *,
    environment: Environment,
    config: TransportConfig,
) -> HttpClientKwargs:
    timeout_cfg: TimeoutConfig = config.timeouts
    pool_cfg: ConnectionPoolConfig = config.pool
    tls_cfg: TlsConfig = config.tls

    verify: bool | str = (
        tls_cfg.ca_bundle_path if tls_cfg.ca_bundle_path is not None else tls_cfg.verify
    )

    return {
        "base_url": environment.base_url,
        "timeout": httpx.Timeout(
            connect=timeout_cfg.connect,
            read=timeout_cfg.read,
            write=timeout_cfg.write,
            pool=timeout_cfg.pool,
        ),
        "limits": httpx.Limits(
            max_connections=pool_cfg.max_connections,
            max_keepalive_connections=pool_cfg.max_keepalive_connections,
            keepalive_expiry=pool_cfg.keepalive_expiry,
        ),
        "verify": verify,
        "proxy": config.proxy_url,
        "trust_env": config.trust_env,
        "http2": config.http2,
    }


def apply_environment_base_url(
    *,
    http_client: object,
    environment: Environment,
) -> None:
    """Bind a supplied HTTP client to the selected KSeF environment."""
    base_url = getattr(http_client, "base_url", None)
    if not isinstance(base_url, httpx.URL):
        return
    if not str(base_url):
        setattr(http_client, "base_url", httpx.URL(environment.base_url))
        return
    expected = httpx.URL(f"{environment.base_url.rstrip('/')}/")
    if base_url != expected:
        raise KSeFArgumentError(
            "http_client.base_url must match the selected environment.",
            hint="Set http_client.base_url to the selected environment URL or leave it empty.",
            environment=environment.name,
            expected_base_url=str(expected),
            actual_base_url=str(base_url),
        )
    setattr(http_client, "base_url", expected)
