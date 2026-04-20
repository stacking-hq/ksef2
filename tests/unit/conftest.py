import pytest
from tests.unit.fakes import transport

from tests.unit.factories.certificates import *  # noqa
from tests.unit.factories.encryption import *  # noqa
from tests.unit.factories.invoices import *  # noqa
from tests.unit.factories.auth import *  # noqa
from tests.unit.factories.limits import *  # noqa
from tests.unit.factories.peppol import *  # noqa
from tests.unit.factories.testdata import *  # noqa
from tests.unit.factories.session import *  # noqa
from tests.unit.factories.tokens import *  # noqa
from tests.unit.factories.permissions import *  # noqa


_REF = "20250625-SO-2C3E6C8000-B675CF5D68-07"
_TOKEN = "fake-access-token"
_INVOICE_REF = "20250625-EE-319D7EE000-B67F415CDC-2C"


@pytest.fixture
def fake_token_bearer() -> str:
    return _TOKEN


@pytest.fixture
def fake_transport() -> transport.FakeTransport:
    return transport.FakeTransport()


@pytest.fixture
def async_fake_transport() -> transport.AsyncFakeTransport:
    return transport.AsyncFakeTransport()
