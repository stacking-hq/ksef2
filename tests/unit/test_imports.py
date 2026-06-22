import asyncio
import os
from pathlib import Path
import subprocess
import sys
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

HTTPX_CLIENT_CLASS = httpx.Client
HTTPX_ASYNC_CLIENT_CLASS = httpx.AsyncClient
PROJECT_ROOT = Path(__file__).parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
BEARTYPE_BLOCKED_IMPORT = """
import builtins

original_import = builtins.__import__


def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "beartype" or name.startswith("beartype."):
        raise ModuleNotFoundError("No module named 'beartype'")
    return original_import(name, globals, locals, fromlist, level)


builtins.__import__ = blocked_import
import ksef2
print(ksef2.__version__)
"""


def test_public_clients_import() -> None:
    from ksef2 import AsyncClient, Client

    assert Client.__name__ == "Client"
    assert AsyncClient.__name__ == "AsyncClient"


def test_root_error_surface_import() -> None:
    import ksef2

    assert ksef2.__version__
    assert ksef2.KSeFException.__name__ == "KSeFException"
    assert ksef2.KSeFApiError.__name__ == "KSeFApiError"
    assert ksef2.KSeFAuthError.__name__ == "KSeFAuthError"
    assert ksef2.KSeFValidationError.__name__ == "KSeFValidationError"
    assert ksef2.KSeFRateLimitError.__name__ == "KSeFRateLimitError"
    assert ksef2.KSeFAuthPollingTimeoutError.__name__ == "KSeFAuthPollingTimeoutError"
    assert ksef2.KSeFTokenStatusTimeoutError.__name__ == "KSeFTokenStatusTimeoutError"
    assert ksef2.ExceptionCode.UNKNOWN_ERROR == 10000
    assert "KSeFApiError" in ksef2.__all__
    assert "__version__" in ksef2.__all__


def test_root_import_does_not_require_beartype_by_default() -> None:
    env = os.environ.copy()
    _ = env.pop("KSEF2_RUNTIME_CHECKS", None)
    env["PYTHONPATH"] = str(SRC_ROOT)

    result = subprocess.run(
        [sys.executable, "-c", BEARTYPE_BLOCKED_IMPORT],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.stdout.strip()


def test_runtime_checks_extra_is_required_when_enabled_without_beartype() -> None:
    env = os.environ.copy()
    env["KSEF2_RUNTIME_CHECKS"] = "1"
    env["PYTHONPATH"] = str(SRC_ROOT)

    result = subprocess.run(
        [sys.executable, "-c", BEARTYPE_BLOCKED_IMPORT],
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0
    assert "ksef2[runtime-checks]" in result.stderr


def test_common_domain_models_import() -> None:
    from ksef2.domain.models import InvoiceMetadataParams, InvoicesFilter

    assert InvoicesFilter.__name__ == "InvoicesFilter"
    assert InvoiceMetadataParams.__name__ == "InvoiceMetadataParams"


def test_public_profiles_import() -> None:
    from ksef2.profiles import Profile, ProfileStore, TokenProfileAuth

    assert Profile.__name__ == "ProfileConfig"
    assert ProfileStore.__name__ == "ProfileStore"
    assert TokenProfileAuth.__name__ == "TokenProfileAuth"


def test_public_xades_import() -> None:
    from ksef2.xades import LocalSigner, generate_test_certificate, sign_xades

    assert LocalSigner.__name__ == "LocalSigner"
    assert generate_test_certificate.__name__ == "generate_test_certificate"
    assert sign_xades.__name__ == "sign_xades"


def test_middlewares_import() -> None:
    from ksef2.core import middlewares

    assert middlewares.KSeFExceptionMiddleware.__name__ == "KSeFExceptionMiddleware"
    assert (
        middlewares.AsyncKSeFExceptionMiddleware.__name__
        == "AsyncKSeFExceptionMiddleware"
    )


def test_root_clients_construct_and_close_with_mocked_http_clients() -> None:
    from ksef2 import AsyncClient, Client
    from ksef2.config import Environment

    with (
        patch("ksef2.clients.base.httpx.Client") as sync_client_cls,
        patch("ksef2.clients.async_base.httpx.AsyncClient") as async_client_cls,
    ):
        sync_http_client = MagicMock(spec=HTTPX_CLIENT_CLASS)
        async_http_client = AsyncMock(spec=HTTPX_ASYNC_CLIENT_CLASS)
        sync_client_cls.return_value = sync_http_client
        async_client_cls.return_value = async_http_client

        client = Client(environment=Environment.TEST)
        async_client = AsyncClient(environment=Environment.TEST)

        client.close()
        asyncio.run(async_client.aclose())

    sync_close = cast(MagicMock, sync_http_client.close)
    async_aclose = cast(AsyncMock, async_http_client.aclose)
    sync_close.assert_called_once()
    async_aclose.assert_awaited_once()
