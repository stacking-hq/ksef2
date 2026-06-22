"""Raw endpoint interface for advanced KSeF integrations."""

from ksef2.core.crypto import (
    encrypt_invoice,
    encrypt_symmetric_key,
    encrypt_token,
    generate_session_key,
    sha256_b64,
)
from ksef2.infra.schema.api import spec as spec
from ksef2.infra.schema.api import supp as supp
from ksef2.infra.schema.api.supp import (
    auth as auth,
    batch as batch,
    certificates as certificates,
    encryption as encryption,
    invoices as invoices,
    peppol as peppol,
    permissions as permissions,
    session as session,
    testdata as testdata,
)
from ksef2.raw.async_facade import (
    AsyncRawAuthenticatedClient,
    AsyncRawClient,
    AsyncRawPermissionsEndpoints,
)
from ksef2.raw.facade import (
    RawAuthenticatedClient,
    RawClient,
    RawPermissionsEndpoints,
)
from ksef2.services.batch_preparation import prepare_batch_package

__all__ = [
    "AsyncRawAuthenticatedClient",
    "AsyncRawClient",
    "AsyncRawPermissionsEndpoints",
    "RawAuthenticatedClient",
    "RawClient",
    "RawPermissionsEndpoints",
    "auth",
    "batch",
    "certificates",
    "encrypt_invoice",
    "encrypt_symmetric_key",
    "encrypt_token",
    "encryption",
    "generate_session_key",
    "invoices",
    "peppol",
    "permissions",
    "prepare_batch_package",
    "session",
    "sha256_b64",
    "spec",
    "supp",
    "testdata",
]
