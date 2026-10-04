import pytest
from base64 import b64encode
from datetime import UTC, datetime, timedelta

from ksef2._core.async_token_manager import AsyncTokenManager
from ksef2._domain.models.auth import AuthTokens, TokenCredentials

VALID_BASE64 = b64encode(b"polyfactory-test-certificate-data").decode()
VALID_CERTIFICATE_ID = b64encode(b"certificate-id-32-byte-value-000").decode()
VALID_PUBLIC_KEY_ID = b64encode(b"public-key-id-32-byte-value-000").decode()

# Marks tests that keep covering the behaviour of a deprecated alias. The warning
# itself is asserted in tests/unit/test_deprecated_apis.py.
legacy_api = pytest.mark.filterwarnings(
    "ignore:.*is deprecated and will be removed in ksef2 1.10.0:DeprecationWarning"
)


def static_token_manager(token: str) -> AsyncTokenManager:
    """Return a token manager holding ``token`` with automatic refresh disabled."""
    valid_until = datetime.now(UTC) + timedelta(days=1)
    return AsyncTokenManager(
        AuthTokens(
            access_token=TokenCredentials(token=token, valid_until=valid_until),
            refresh_token=TokenCredentials(token="refresh", valid_until=valid_until),
        )
    )
