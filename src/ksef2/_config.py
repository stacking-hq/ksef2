"""Transport and environment configuration for KSeF clients."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class Environment(Enum):
    """Supported KSeF API environments.

    Attributes:
        PRODUCTION: The production KSeF API.
        TEST: The TEST environment, for development and testing.
        DEMO: The DEMO (pre-production) environment.
    """

    PRODUCTION = "https://api.ksef.mf.gov.pl/v2"
    TEST = "https://api-test.ksef.mf.gov.pl/v2"
    DEMO = "https://api-demo.ksef.mf.gov.pl/v2"

    @property
    def base_url(self) -> str:
        """Return the base API URL for this environment.

        Returns:
            The base API URL for this environment.
        """
        return self.value


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """HTTP timeout settings passed to ``httpx``."""

    connect: float = 5.0
    """Seconds to wait for a connection to be established."""
    read: float = 30.0
    """Seconds to wait for a chunk of the response."""
    write: float = 30.0
    """Seconds to wait while sending the request."""
    pool: float = 5.0
    """Seconds to wait for a free connection from the pool."""


@dataclass(frozen=True, slots=True)
class ConnectionPoolConfig:
    """HTTP connection pool limits passed to ``httpx``."""

    max_connections: int = 100
    """Maximum number of concurrent connections."""
    max_keepalive_connections: int = 20
    """Maximum number of idle connections kept open for reuse."""
    keepalive_expiry: float = 30.0
    """Seconds an idle connection stays open before it is closed."""


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Retry behavior for retryable KSeF responses and transient failures."""

    max_attempts: int = 3
    """Total number of attempts per request, including the first."""
    initial_delay: float = 0.5
    """Seconds to wait before the first retry."""
    max_delay: float = 4.0
    """Upper bound in seconds for the exponential backoff delay between retries."""
    max_retry_after: float = 120.0
    """Upper bound in seconds for a ``Retry-After`` value the SDK is willing to sleep.

    When a retryable response carries ``Retry-After`` at or below this ceiling, the
    SDK sleeps that exact value (not ``max_delay``) and retries. When it exceeds the
    ceiling, the SDK does not sleep or retry: the request fails immediately with
    ``KSeFRateLimitError`` carrying the true header value so callers can reschedule.
    """
    backoff_multiplier: float = 2.0
    """Factor by which the delay grows after each retry."""
    retryable_status_codes: tuple[int, ...] = (429, 502, 503, 504)
    """HTTP status codes that trigger a retry."""


@dataclass(frozen=True, slots=True)
class TlsConfig:
    """TLS verification settings for SDK-managed HTTP clients."""

    verify: bool = True
    """Whether to verify the server's TLS certificate."""
    ca_bundle_path: str | None = None
    """Path to a custom CA bundle used for verification; ``None`` for the default trust store."""


@dataclass(frozen=True, slots=True)
class TransportConfig:
    """Complete transport configuration for SDK-managed HTTP clients."""

    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    """HTTP timeout settings."""
    pool: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    """HTTP connection pool limits."""
    retry: RetryConfig = field(default_factory=RetryConfig)
    """Retry behavior for retryable responses and transient failures."""
    tls: TlsConfig = field(default_factory=TlsConfig)
    """TLS verification settings."""
    proxy_url: str | None = None
    """URL of a proxy to route requests through; ``None`` for no explicit proxy."""
    trust_env: bool = True
    """Whether ``httpx`` honors proxy and certificate environment variables."""
    http2: bool = True
    """Whether to use HTTP/2 when the server supports it."""
    auto_refresh_tokens: bool = True
    """Whether authenticated clients refresh their access token automatically, shortly before it expires and once after a 401 response. Set to ``False`` to manage refreshing yourself."""
    error_format: Literal["problem-details", "legacy"] = "problem-details"
    """Error format requested from KSeF. ``"problem-details"`` sends ``X-Error-Format: problem-details``, so 400 and 429 errors carry ``trace_id`` and ``exc.response`` is a Problem Details model. ``"legacy"`` sends no header, so those errors come in the older format, without ``trace_id``. 401, 403 and 410 are always Problem Details."""
