from typing import cast

import pytest

from polyfactory.factories import BaseFactory
from pydantic import BaseModel

from ksef2.core import exceptions
from ksef2.core.routes import InvoiceRoutes
from ksef2.endpoints.invoices import InvoicesEndpoints
from tests.unit.fakes import transport
from tests.unit.factories.invoices import (
    QueryInvoicesMetadataRequestFactory,
    QueryInvoicesMetadataResponseFactory,
    SessionInvoicesResponseFactory,
)

from ksef2.core.middlewares.exceptions import KSeFExceptionMiddleware

_REF = "20250625-SO-2C3E6C8000-B675CF5D68-07"
_INV_REF = "20250625-EE-319D7EE000-B67F415CDC-2C"
_KSEF = "1234567890-20250625-ABC123-DEF456-07"
_EXPORT_REF = "20250625-EX-2C3E6C8000-B675CF5D68-07"

_TRANSPORT_ERRORS = [
    (exceptions.KSeFApiError, 500),
    (exceptions.KSeFRateLimitError, 429),
    (exceptions.KSeFAuthError, 403),
    (exceptions.KSeFAuthError, 401),
    (exceptions.KSeFApiError, 400),
]


class InvalidContent(BaseModel):
    invalid_field: str


def _build_request(req_factory: object) -> BaseModel:
    if hasattr(req_factory, "build"):
        return cast(BaseFactory[BaseModel], req_factory).build()
    return cast(BaseModel, req_factory)


@pytest.fixture
def req_factory(request: pytest.FixtureRequest) -> object:
    return request.getfixturevalue(request.param)


@pytest.fixture
def resp_factory(request: pytest.FixtureRequest) -> BaseFactory[BaseModel]:
    return cast(BaseFactory[BaseModel], request.getfixturevalue(request.param))


@pytest.fixture
def inv_query_metadata_body(
    inv_query_metadata_req: QueryInvoicesMetadataRequestFactory,
):
    return inv_query_metadata_req.build().filters


class TestInvoiceEndpoints:
    @pytest.fixture
    def invoice_eps(self, fake_transport: transport.FakeTransport) -> InvoicesEndpoints:
        return InvoicesEndpoints(fake_transport)

    @pytest.fixture
    def handled_invoice_eps(
        self, fake_transport: transport.FakeTransport
    ) -> InvoicesEndpoints:
        return InvoicesEndpoints(KSeFExceptionMiddleware(fake_transport))

    # ===== POST body -> response =====

    @pytest.mark.parametrize(
        ["method_name", "route", "req_factory", "resp_factory", "prefix_args"],
        [
            (
                "query_metadata",
                InvoiceRoutes.QUERY_METADATA,
                "inv_query_metadata_body",
                "inv_query_metadata_resp",
                [],
            ),
            (
                "export",
                InvoiceRoutes.EXPORT,
                "inv_export_req",
                "inv_export_resp",
                [],
            ),
            (
                "send",
                InvoiceRoutes.SEND.format(referenceNumber=_REF),
                "inv_send_req",
                "inv_send_resp",
                [_REF],
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_post(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        route: str,
        req_factory: object,
        resp_factory: BaseFactory[BaseModel],
        prefix_args: list[str],
    ):
        request = _build_request(req_factory)
        request_dump = request.model_dump(mode="json", by_alias=True)
        expected = resp_factory.build()

        fake_transport.enqueue(expected.model_dump(mode="json"))
        response = getattr(invoice_eps, method_name)(*prefix_args, request)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "POST"
        assert str(call.path) == route
        assert call.json is not None
        assert call.json == request_dump
        assert call.content is None
        assert call.headers is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "req_factory", "prefix_args"],
        [
            ("query_metadata", "inv_query_metadata_body", []),
            ("export", "inv_export_req", []),
            ("send", "inv_send_req", [_REF]),
        ],
        indirect=["req_factory"],
    )
    def test_post_response_validation(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        req_factory: object,
        prefix_args: list[str],
    ):
        request = _build_request(req_factory)
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = getattr(invoice_eps, method_name)(*prefix_args, request)

        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "route", "req_factory", "resp_factory", "prefix_args"],
        [
            (
                "query_metadata",
                InvoiceRoutes.QUERY_METADATA,
                "inv_query_metadata_body",
                "inv_query_metadata_resp",
                [],
            ),
            (
                "export",
                InvoiceRoutes.EXPORT,
                "inv_export_req",
                "inv_export_resp",
                [],
            ),
            (
                "send",
                InvoiceRoutes.SEND.format(referenceNumber=_REF),
                "inv_send_req",
                "inv_send_resp",
                [_REF],
            ),
        ],
        indirect=["req_factory", "resp_factory"],
    )
    def test_post_transport_error(
        self,
        handled_invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        route: str,
        req_factory: object,
        resp_factory: BaseFactory[BaseModel],
        prefix_args: list[str],
    ):
        request = _build_request(req_factory)
        response = resp_factory.build()

        for exc, code in _TRANSPORT_ERRORS:
            fake_transport.enqueue(
                status_code=code,
                json_body=response.model_dump(mode="json"),
            )

            with pytest.raises(exc):
                _ = getattr(handled_invoice_eps, method_name)(*prefix_args, request)

            call = fake_transport.calls[0]
            assert call.method == "POST"
            assert str(call.path) == route
            assert call.json is not None
            assert call.content is None
            assert call.headers is None

            assert fake_transport.responses == []

    # ===== query_metadata params (unique behavior) =====

    def test_query_metadata_with_params(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        inv_query_metadata_body,
        inv_query_metadata_resp: QueryInvoicesMetadataResponseFactory,
    ):
        request = inv_query_metadata_body
        expected = inv_query_metadata_resp.build()

        fake_transport.enqueue(expected.model_dump(mode="json"))
        response = invoice_eps.query_metadata(
            request, pageSize=20, pageOffset=0, sortOrder="ASC"
        )

        assert response == expected
        call = fake_transport.calls[0]
        assert call.params is not None
        assert call.params.get("pageSize") == "20"
        assert call.params.get("pageOffset") == "0"
        assert call.params.get("sortOrder") == "ASC"
        assert fake_transport.responses == []

    # ===== GET -> request =====

    @pytest.mark.parametrize(
        ["method_name", "call_args", "expected_path", "resp_factory"],
        [
            (
                "get_export_status",
                [_EXPORT_REF],
                InvoiceRoutes.EXPORT_STATUS.format(referenceNumber=_EXPORT_REF),
                "inv_export_status_resp",
            ),
            (
                "get_session_status",
                [_REF],
                InvoiceRoutes.SESSION_STATUS.format(referenceNumber=_REF),
                "inv_session_status_resp",
            ),
            (
                "get_session_invoice_status",
                [_REF, _INV_REF],
                InvoiceRoutes.SESSION_INVOICE_STATUS.format(
                    referenceNumber=_REF,
                    invoiceReferenceNumber=_INV_REF,
                ),
                "inv_session_invoice_status_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_get_model(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        call_args: list[str],
        expected_path: str,
        resp_factory: BaseFactory[BaseModel],
    ):
        expected = resp_factory.build()

        fake_transport.enqueue(expected.model_dump(mode="json"))
        response = getattr(invoice_eps, method_name)(*call_args)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == expected_path
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "call_args"],
        [
            ("get_export_status", [_EXPORT_REF]),
            ("get_session_status", [_REF]),
            ("get_session_invoice_status", [_REF, _INV_REF]),
        ],
    )
    def test_get_model_response_validation(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        call_args: list[str],
    ):
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = getattr(invoice_eps, method_name)(*call_args)

        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "call_args", "expected_path", "resp_factory"],
        [
            (
                "get_export_status",
                [_EXPORT_REF],
                InvoiceRoutes.EXPORT_STATUS.format(referenceNumber=_EXPORT_REF),
                "inv_export_status_resp",
            ),
            (
                "get_session_status",
                [_REF],
                InvoiceRoutes.SESSION_STATUS.format(referenceNumber=_REF),
                "inv_session_status_resp",
            ),
            (
                "get_session_invoice_status",
                [_REF, _INV_REF],
                InvoiceRoutes.SESSION_INVOICE_STATUS.format(
                    referenceNumber=_REF,
                    invoiceReferenceNumber=_INV_REF,
                ),
                "inv_session_invoice_status_resp",
            ),
        ],
        indirect=["resp_factory"],
    )
    def test_get_model_transport_error(
        self,
        handled_invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        call_args: list[str],
        expected_path: str,
        resp_factory: BaseFactory[BaseModel],
    ):
        response = resp_factory.build()

        for exc, code in _TRANSPORT_ERRORS:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = getattr(handled_invoice_eps, method_name)(*call_args)

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == expected_path
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    # ===== GET -> bytes =====

    @pytest.mark.parametrize(
        ["method_name", "call_args", "expected_path"],
        [
            (
                "download",
                [_KSEF],
                InvoiceRoutes.DOWNLOAD.format(ksefNumber=_KSEF),
            ),
            (
                "get_invoice_upo_by_ksef",
                [_REF, _KSEF],
                InvoiceRoutes.INVOICE_UPO_BY_KSEF.format(
                    referenceNumber=_REF, ksefNumber=_KSEF
                ),
            ),
            (
                "get_invoice_upo_by_reference",
                [_REF, _INV_REF],
                InvoiceRoutes.INVOICE_UPO_BY_REFERENCE.format(
                    referenceNumber=_REF, invoiceReferenceNumber=_INV_REF
                ),
            ),
        ],
    )
    def test_get_bytes(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        call_args: list[str],
        expected_path: str,
    ):
        content = b"<content>...</content>"

        fake_transport.enqueue(content=content)
        result = getattr(invoice_eps, method_name)(*call_args)

        assert result == content
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == expected_path
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "call_args", "expected_path"],
        [
            (
                "download",
                [_KSEF],
                InvoiceRoutes.DOWNLOAD.format(ksefNumber=_KSEF),
            ),
            (
                "get_invoice_upo_by_ksef",
                [_REF, _KSEF],
                InvoiceRoutes.INVOICE_UPO_BY_KSEF.format(
                    referenceNumber=_REF, ksefNumber=_KSEF
                ),
            ),
            (
                "get_invoice_upo_by_reference",
                [_REF, _INV_REF],
                InvoiceRoutes.INVOICE_UPO_BY_REFERENCE.format(
                    referenceNumber=_REF, invoiceReferenceNumber=_INV_REF
                ),
            ),
        ],
    )
    def test_get_bytes_transport_error(
        self,
        handled_invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
        call_args: list[str],
        expected_path: str,
    ):
        for exc, code in _TRANSPORT_ERRORS:
            fake_transport.enqueue(status_code=code, content=b"")

            with pytest.raises(exc):
                getattr(handled_invoice_eps, method_name)(*call_args)

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == expected_path
            assert call.headers is None
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []

    # ===== List with pagination =====

    @pytest.mark.parametrize(
        ["method_name", "route"],
        [
            ("list_session_invoices", InvoiceRoutes.LIST_SESSION_INVOICES),
            (
                "list_failed_session_invoices",
                InvoiceRoutes.LIST_FAILED_SESSION_INVOICES,
            ),
        ],
    )
    def test_list_invoices(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        inv_session_invoices_resp: SessionInvoicesResponseFactory,
        method_name: str,
        route: str,
    ):
        expected = inv_session_invoices_resp.build()

        fake_transport.enqueue(expected.model_dump(mode="json"))
        response = getattr(invoice_eps, method_name)(_REF, pageSize=10)

        assert response == expected
        assert len(fake_transport.calls) == 1
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == route.format(referenceNumber=_REF)
        assert call.params is not None
        assert call.params.get("pageSize") == "10"
        assert call.headers is None
        assert call.json is None
        assert call.content is None
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "route"],
        [
            ("list_session_invoices", InvoiceRoutes.LIST_SESSION_INVOICES),
            (
                "list_failed_session_invoices",
                InvoiceRoutes.LIST_FAILED_SESSION_INVOICES,
            ),
        ],
    )
    def test_list_invoices_continuation_token(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        inv_session_invoices_resp: SessionInvoicesResponseFactory,
        method_name: str,
        route: str,
    ):
        expected = inv_session_invoices_resp.build()
        continuation_token = "test-continuation-token"

        fake_transport.enqueue(expected.model_dump(mode="json"))
        response = getattr(invoice_eps, method_name)(
            _REF, continuation_token=continuation_token, pageSize=10
        )

        assert response == expected
        call = fake_transport.calls[0]
        assert call.method == "GET"
        assert str(call.path) == route.format(referenceNumber=_REF)
        assert call.headers is not None
        assert call.headers.get("x-continuation-token") == continuation_token
        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        "method_name",
        ["list_session_invoices", "list_failed_session_invoices"],
    )
    def test_list_invoices_response_validation(
        self,
        invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        method_name: str,
    ):
        invalid_response = InvalidContent(invalid_field="invalid")

        with pytest.raises(exceptions.KSeFValidationError):
            fake_transport.enqueue(invalid_response.model_dump(mode="json"))
            _ = getattr(invoice_eps, method_name)(_REF, pageSize=10)

        assert fake_transport.responses == []

    @pytest.mark.parametrize(
        ["method_name", "route"],
        [
            ("list_session_invoices", InvoiceRoutes.LIST_SESSION_INVOICES),
            (
                "list_failed_session_invoices",
                InvoiceRoutes.LIST_FAILED_SESSION_INVOICES,
            ),
        ],
    )
    def test_list_invoices_transport_error(
        self,
        handled_invoice_eps: InvoicesEndpoints,
        fake_transport: transport.FakeTransport,
        inv_session_invoices_resp: SessionInvoicesResponseFactory,
        method_name: str,
        route: str,
    ):
        response = inv_session_invoices_resp.build()

        for exc, code in _TRANSPORT_ERRORS:
            fake_transport.enqueue(
                json_body=response.model_dump(mode="json"),
                status_code=code,
            )

            with pytest.raises(exc):
                _ = getattr(handled_invoice_eps, method_name)(_REF, pageSize=10)

            call = fake_transport.calls[0]
            assert call.method == "GET"
            assert str(call.path) == route.format(referenceNumber=_REF)
            assert call.json is None
            assert call.content is None

            assert fake_transport.responses == []
