from typing import TypedDict

import httpx

from ksef2.config import (
    ConnectionPoolConfig,
    Environment,
    TimeoutConfig,
    TlsConfig,
    TransportConfig,
)


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
