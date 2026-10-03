"""Public package facade for the KSeF 2 SDK."""

import os
from importlib.metadata import version


_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


def _enable_runtime_checks() -> None:
    try:
        from warnings import filterwarnings

        from beartype import BeartypeConf
        from beartype.claw import beartype_this_package
        from beartype.roar import BeartypeClawDecorWarning
    except ImportError as exc:
        raise RuntimeError(
            "KSEF2_RUNTIME_CHECKS is enabled, but beartype is not installed. "
            'Install the "ksef2[runtime-checks]" extra to enable runtime '
            "type checks."
        ) from exc

    # Silences beartype warning caused by endpoint TypeAdapter annotations.
    filterwarnings(
        "ignore",
        category=BeartypeClawDecorWarning,
        module=r"ksef2\._endpoints\.(base|async_base|shared)",
    )

    beartype_this_package(
        conf=BeartypeConf(
            claw_skip_package_names=("ksef2._infra.schema.fa3",),
        ),
    )


if os.environ.get("KSEF2_RUNTIME_CHECKS", "").lower() in _TRUE_ENV_VALUES:
    _enable_runtime_checks()

from ksef2._clients.async_base import AsyncClient
from ksef2._clients.base import Client
from ksef2._domain.models import FormSchema

__version__ = version("ksef2")
from ksef2._config import (
    ConnectionPoolConfig,
    Environment,
    RetryConfig,
    TimeoutConfig,
    TlsConfig,
    TransportConfig,
)
from ksef2._core.exceptions import (
    ExceptionCode,
    KSeFApiError,
    KSeFAuthError,
    KSeFAuthPollingTimeoutError,
    KSeFAuthTokenRedemptionError,
    KSeFBatchUploadError,
    KSeFBatchSessionTimeoutError,
    KSeFClientClosedError,
    KSeFEncryptionError,
    KSeFException,
    KSeFExternalTransferError,
    KSeFExportFailedError,
    KSeFExportTimeoutError,
    KSeFInvoiceDownloadTimeoutError,
    KSeFInvoiceProcessingTimeoutError,
    KSeFInvoiceQueryTimeoutError,
    KSeFInvoiceRejectedError,
    KSeFOnlineSessionTimeoutError,
    KSeFInvoiceRenderingError,
    KSeFMetadataPaginationError,
    KSeFRateLimitError,
    KSeFSessionError,
    KSeFTokenStatusTimeoutError,
    KSeFUnsupportedEnvironmentError,
    KSeFValidationError,
    NoCertificateAvailableError,
)
from ksef2._core.stores import CertificateStore, CertificateStoreProtocol

__all__ = [
    "AsyncClient",
    "CertificateStore",
    "CertificateStoreProtocol",
    "Client",
    "ConnectionPoolConfig",
    "Environment",
    "ExceptionCode",
    "FormSchema",
    "KSeFApiError",
    "KSeFAuthError",
    "KSeFAuthPollingTimeoutError",
    "KSeFAuthTokenRedemptionError",
    "KSeFBatchUploadError",
    "KSeFBatchSessionTimeoutError",
    "KSeFClientClosedError",
    "KSeFEncryptionError",
    "KSeFException",
    "KSeFExternalTransferError",
    "KSeFExportFailedError",
    "KSeFExportTimeoutError",
    "KSeFInvoiceDownloadTimeoutError",
    "KSeFInvoiceProcessingTimeoutError",
    "KSeFInvoiceQueryTimeoutError",
    "KSeFInvoiceRejectedError",
    "KSeFOnlineSessionTimeoutError",
    "KSeFInvoiceRenderingError",
    "KSeFMetadataPaginationError",
    "KSeFRateLimitError",
    "KSeFSessionError",
    "KSeFTokenStatusTimeoutError",
    "KSeFUnsupportedEnvironmentError",
    "KSeFValidationError",
    "NoCertificateAvailableError",
    "RetryConfig",
    "TimeoutConfig",
    "TlsConfig",
    "TransportConfig",
    "__version__",
]
