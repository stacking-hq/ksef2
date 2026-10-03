import pytest

from ksef2._clients.auth import AuthClient
from ksef2._clients.certificates import CertificatesClient
from ksef2._clients.invoice_sessions import InvoiceSessionsClient
from ksef2._clients.invoices import InvoicesClient
from ksef2._clients.limits import LimitsClient
from ksef2._clients.peppol import PeppolClient
from ksef2._clients.permissions import PermissionsClient
from ksef2._clients.session_management import SessionManagementClient
from ksef2._clients.testdata import TestDataClient
from ksef2._clients.tokens import TokensClient
from ksef2._core.stores import CertificateStore
from tests.unit.fakes.transport import FakeTransport


@pytest.fixture
def auth_client(fake_transport: FakeTransport) -> AuthClient:
    return AuthClient(fake_transport, CertificateStore())


@pytest.fixture
def permissions_client(fake_transport: FakeTransport) -> PermissionsClient:
    return PermissionsClient(fake_transport)


@pytest.fixture
def certificates_client(fake_transport: FakeTransport) -> CertificatesClient:
    return CertificatesClient(fake_transport)


@pytest.fixture
def peppol_client(fake_transport: FakeTransport) -> PeppolClient:
    return PeppolClient(fake_transport)


@pytest.fixture
def tokens_client(fake_transport: FakeTransport) -> TokensClient:
    return TokensClient(fake_transport)


@pytest.fixture
def invoices_client(fake_transport: FakeTransport) -> InvoicesClient:
    return InvoicesClient(fake_transport)


@pytest.fixture
def limits_client(fake_transport: FakeTransport) -> LimitsClient:
    return LimitsClient(fake_transport)


@pytest.fixture
def session_management_client(fake_transport: FakeTransport) -> SessionManagementClient:
    return SessionManagementClient(fake_transport)


@pytest.fixture
def invoice_sessions_client(fake_transport: FakeTransport) -> InvoiceSessionsClient:
    return InvoiceSessionsClient(fake_transport)


@pytest.fixture
def testdata_client(fake_transport: FakeTransport) -> TestDataClient:
    return TestDataClient(fake_transport)
