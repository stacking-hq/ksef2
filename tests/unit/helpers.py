import pytest
from base64 import b64encode

VALID_BASE64 = b64encode(b"polyfactory-test-certificate-data").decode()
VALID_CERTIFICATE_ID = b64encode(b"certificate-id-32-byte-value-000").decode()
VALID_PUBLIC_KEY_ID = b64encode(b"public-key-id-32-byte-value-000").decode()

# Marks tests that keep covering the behaviour of a deprecated alias. The warning
# itself is asserted in tests/unit/test_deprecated_apis.py.
legacy_api = pytest.mark.filterwarnings(
    "ignore:.*is deprecated and will be removed in ksef2 1.10.0:DeprecationWarning"
)
