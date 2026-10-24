"""Saving and resuming every handle KSeF finishes asynchronously.

Each round trip goes through ``resume_state().to_json()``, crosses to a new
client over the same fake transport, and polls from the saved reference number.
The sync classes are generated from the async ones, so every case runs in both
flavours. No test here reaches KSeF.
"""

import inspect
import json
from typing import Any

import pytest
from polyfactory import BaseFactory
from pydantic import ValidationError

from ksef2._clients.async_certificates import AsyncCertificateEnrollment
from ksef2._clients.async_certificates import AsyncCertificatesClient
from ksef2._clients.async_online import AsyncInvoiceSubmission
from ksef2._clients.async_online import AsyncOnlineSessionClient
from ksef2._clients.async_permissions import AsyncPermissionOperation
from ksef2._clients.async_permissions import AsyncPermissionsClient
from ksef2._clients.async_tokens import AsyncGeneratedToken
from ksef2._clients.async_tokens import AsyncTokensClient
from ksef2._clients.certificates import CertificateEnrollment
from ksef2._clients.certificates import CertificatesClient
from ksef2._clients.online import InvoiceSubmission
from ksef2._clients.online import OnlineSessionClient
from ksef2._clients.permissions import PermissionOperation
from ksef2._clients.permissions import PermissionsClient
from ksef2._clients.tokens import GeneratedToken
from ksef2._clients.tokens import TokensClient
from ksef2._core import exceptions
from ksef2._core.routes import (
    CertificateRoutes,
    InvoiceRoutes,
    RevokePermissionsRoutes,
    TokenRoutes,
)
from ksef2._domain.models.session import OnlineSessionResumeState
from ksef2._infra.schema.api import spec
from ksef2.models import (
    CertificateEnrollmentResumeState,
    GeneratedTokenResumeState,
    InvoiceSubmissionResumeState,
    PermissionOperationResumeState,
)
from tests.unit.support.flavors import Flavor
from tests.unit.support.payloads import INVOICE_REF, KSEF_NUMBER, invoice_status

SECRET_TOKEN = "SECRET-TOKEN-VALUE"
TOKEN_REF = "20250625-TK-2F14610000-3AC9C8E13B-AB"
ENROLLMENT_REF = "20250625-EH-2F14610000-3AC9C8E13B-AB"
OPERATION_REF = "20250625-EU-2F14610000-3AC9C8E13B-AB"
PERMISSION_ID = "123e4567-e89b-12d3-a456-426614174000"
OTHER_SESSION_REF = "20250625-SO-0000000000-0000000000-00"

_HANDLE_PAIRS: tuple[tuple[type[Any], type[Any], type[Any]], ...] = (
    (GeneratedToken, AsyncGeneratedToken, GeneratedTokenResumeState),
    (
        CertificateEnrollment,
        AsyncCertificateEnrollment,
        CertificateEnrollmentResumeState,
    ),
    (
        PermissionOperation,
        AsyncPermissionOperation,
        PermissionOperationResumeState,
    ),
    (InvoiceSubmission, AsyncInvoiceSubmission, InvoiceSubmissionResumeState),
)

_RESUMERS: tuple[tuple[type[Any], type[Any], str, type[Any]], ...] = (
    (TokensClient, AsyncTokensClient, "generation", GeneratedTokenResumeState),
    (
        CertificatesClient,
        AsyncCertificatesClient,
        "enrollment",
        CertificateEnrollmentResumeState,
    ),
    (
        PermissionsClient,
        AsyncPermissionsClient,
        "operation",
        PermissionOperationResumeState,
    ),
    (
        OnlineSessionClient,
        AsyncOnlineSessionClient,
        "submission",
        InvoiceSubmissionResumeState,
    ),
)


def _enrollment_status(code: int) -> dict[str, Any]:
    return {
        "requestDate": "2026-01-01T10:00:00+00:00",
        "status": {
            "code": code,
            "description": "issued" if code == 200 else f"status {code}",
        },
        **({"certificateSerialNumber": "0123456789ABCDEF"} if code == 200 else {}),
    }


def _operation_status(code: int) -> dict[str, Any]:
    return {"status": {"code": code, "description": f"status {code}"}}


def _token_status(
    token_status_resp: BaseFactory[spec.TokenStatusResponse], *, active: bool
) -> dict[str, Any]:
    status = (
        spec.AuthenticationTokenStatus.Active
        if active
        else spec.AuthenticationTokenStatus.Pending
    )
    return token_status_resp.build(referenceNumber=TOKEN_REF, status=status).model_dump(
        mode="json"
    )


def _generate(
    flavor: Flavor, token_generate_resp: BaseFactory[spec.GenerateTokenResponse]
) -> Any:
    """Start a token generation whose one-time secret is ``SECRET_TOKEN``."""
    client = flavor.client(TokensClient, AsyncTokensClient)
    response = token_generate_resp.build(referenceNumber=TOKEN_REF, token=SECRET_TOKEN)
    flavor.transport.enqueue(response.model_dump(mode="json"))
    return flavor.run(
        client.generate(permissions=["invoice_read"], description="test token")
    )


def _enroll(
    flavor: Flavor, cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse]
) -> Any:
    client = flavor.client(CertificatesClient, AsyncCertificatesClient)
    response = cert_enroll_resp.build(referenceNumber=ENROLLMENT_REF)
    flavor.transport.enqueue(response.model_dump(mode="json"))
    return flavor.run(
        client.enroll(
            certificate_name="signing",
            certificate_type="offline",
            csr="MIIBMAKe",
        )
    )


def _revoke(
    flavor: Flavor, perm_op_resp: BaseFactory[spec.PermissionsOperationResponse]
) -> Any:
    client = flavor.client(PermissionsClient, AsyncPermissionsClient)
    response = perm_op_resp.build(referenceNumber=OPERATION_REF)
    flavor.transport.enqueue(response.model_dump(mode="json"))
    return flavor.run(client.revoke(permission_id=PERMISSION_ID))


def _paths(flavor: Flavor) -> list[str]:
    return [call.path for call in flavor.transport.calls]


def test_generated_token_resume_state_omits_the_one_time_token(
    flavor: Flavor, token_generate_resp: BaseFactory[spec.GenerateTokenResponse]
) -> None:
    generated = _generate(flavor, token_generate_resp)

    assert generated.token == SECRET_TOKEN
    state = generated.resume_state()

    assert isinstance(state, GeneratedTokenResumeState)
    assert state.reference_number == TOKEN_REF
    assert "token" not in GeneratedTokenResumeState.model_fields
    assert state.to_dict() == {"format_version": "1", "reference_number": TOKEN_REF}
    for text in (
        state.to_json(),
        json.dumps(state.to_dict()),
        state.model_dump_json(),
        str(state.model_dump()),
        repr(state),
    ):
        assert SECRET_TOKEN not in text


def test_generated_token_resume_round_trip_polls_the_same_reference(
    flavor: Flavor,
    token_generate_resp: BaseFactory[spec.GenerateTokenResponse],
    token_status_resp: BaseFactory[spec.TokenStatusResponse],
) -> None:
    generated = _generate(flavor, token_generate_resp)

    saved = generated.resume_state().to_json()
    resumed = flavor.client(TokensClient, AsyncTokensClient).generation(saved)

    assert resumed.reference_number == TOKEN_REF
    assert _paths(flavor) == [TokenRoutes.GENERATE_TOKEN]

    flavor.transport.enqueue(_token_status(token_status_resp, active=True))
    status = flavor.run(resumed.get_status())
    flavor.transport.enqueue(_token_status(token_status_resp, active=True))
    from_the_original_handle = flavor.run(generated.get_status())

    assert status.status == "active"
    assert status == from_the_original_handle
    assert _paths(flavor)[-1] == TokenRoutes.TOKEN_STATUS.format(
        referenceNumber=TOKEN_REF
    )

    flavor.transport.clear()
    flavor.transport.enqueue(_token_status(token_status_resp, active=True))
    waited = flavor.run(resumed.wait(timeout=1.0, poll_interval=0.0))

    assert waited == status
    assert len(flavor.transport.calls) == 1


def test_resumed_generated_token_has_no_token_attribute(
    flavor: Flavor, token_generate_resp: BaseFactory[spec.GenerateTokenResponse]
) -> None:
    generated = _generate(flavor, token_generate_resp)
    state = generated.resume_state()

    resumed = flavor.client(TokensClient, AsyncTokensClient).generation(state)

    assert resumed.reference_number == TOKEN_REF
    with pytest.raises(AttributeError):
        _ = resumed.token
    with pytest.raises(AttributeError, match="resume state only knows"):
        _ = resumed.response
    with pytest.raises(AttributeError):
        _ = resumed.to_sensitive_dict()
    assert not hasattr(resumed, "token")
    assert resumed.resume_state() == state


def test_certificate_enrollment_resume_round_trip_polls_the_same_reference(
    flavor: Flavor, cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse]
) -> None:
    enrollment = _enroll(flavor, cert_enroll_resp)

    saved = enrollment.resume_state().to_json()
    resumed = flavor.client(CertificatesClient, AsyncCertificatesClient).enrollment(
        saved
    )

    assert resumed.reference_number == ENROLLMENT_REF
    assert _paths(flavor) == [CertificateRoutes.ENROLLMENT]

    flavor.transport.enqueue(_enrollment_status(200))
    status = flavor.run(resumed.get_status())
    flavor.transport.enqueue(_enrollment_status(200))
    from_the_original_handle = flavor.run(enrollment.get_status())

    assert status.status_code == 200
    assert status == from_the_original_handle
    assert _paths(flavor)[-1] == CertificateRoutes.ENROLLMENT_STATUS.format(
        referenceNumber=ENROLLMENT_REF
    )

    flavor.transport.clear()
    flavor.transport.enqueue(_enrollment_status(200))
    waited = flavor.run(resumed.wait(timeout=1.0, poll_interval=0.0))

    assert waited == status
    assert len(flavor.transport.calls) == 1


def test_resumed_certificate_enrollment_has_no_timestamp(
    flavor: Flavor, cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse]
) -> None:
    enrollment = _enroll(flavor, cert_enroll_resp)
    state = enrollment.resume_state()

    resumed = flavor.client(CertificatesClient, AsyncCertificatesClient).enrollment(
        state
    )

    assert isinstance(state, CertificateEnrollmentResumeState)
    assert state.to_dict() == {
        "format_version": "1",
        "reference_number": ENROLLMENT_REF,
    }
    with pytest.raises(AttributeError):
        _ = resumed.timestamp
    with pytest.raises(AttributeError, match="resume state only knows"):
        _ = resumed.response
    assert resumed.resume_state() == state


def test_permission_operation_resume_round_trip_polls_the_same_reference(
    flavor: Flavor, perm_op_resp: BaseFactory[spec.PermissionsOperationResponse]
) -> None:
    operation = _revoke(flavor, perm_op_resp)
    revoke_path = _paths(flavor)[-1]

    saved = operation.resume_state().to_json()
    resumed = flavor.client(PermissionsClient, AsyncPermissionsClient).operation(saved)

    assert resumed.reference_number == OPERATION_REF
    assert resumed.response.reference_number == OPERATION_REF
    assert revoke_path == RevokePermissionsRoutes.REVOKE_PERMISSION.format(
        permissionId=PERMISSION_ID
    )

    flavor.transport.enqueue(_operation_status(200))
    status = flavor.run(resumed.get_status())
    flavor.transport.enqueue(_operation_status(200))
    from_the_original_handle = flavor.run(operation.get_status())

    assert status.status.code == 200
    assert status == from_the_original_handle
    assert OPERATION_REF in _paths(flavor)[-1]

    flavor.transport.clear()
    flavor.transport.enqueue(_operation_status(200))
    waited = flavor.run(resumed.wait(timeout=1.0, poll_interval=0.0))

    assert waited == status
    assert len(flavor.transport.calls) == 1


def test_invoice_submission_resume_state_keeps_session_and_invoice_references(
    flavor: Flavor,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
    inv_session_invoice_status_resp: BaseFactory[spec.SessionInvoiceStatusResponse],
) -> None:
    session = flavor.online_session(domain_online_session_state.build())
    submission = session.submission(INVOICE_REF)

    state = submission.resume_state()

    assert isinstance(state, InvoiceSubmissionResumeState)
    assert state.reference_number == INVOICE_REF
    assert state.session_reference_number == session.reference_number

    resumed = session.submission(state=state.to_json())

    assert resumed.reference_number == INVOICE_REF
    assert resumed.resume_state() == state

    status_payload = invoice_status(inv_session_invoice_status_resp, 200, KSEF_NUMBER)
    flavor.transport.enqueue(status_payload)
    status = flavor.run(resumed.get_status())

    assert status.ksef_number == KSEF_NUMBER
    assert _paths(flavor)[-1] == InvoiceRoutes.SESSION_INVOICE_STATUS.format(
        referenceNumber=session.reference_number,
        invoiceReferenceNumber=INVOICE_REF,
    )

    flavor.transport.clear()
    flavor.transport.enqueue(status_payload)
    waited = flavor.run(resumed.wait(timeout=1.0, poll_interval=0.0))

    assert waited == status
    assert len(flavor.transport.calls) == 1


def test_submission_state_rejects_a_different_session(
    flavor: Flavor,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> None:
    session = flavor.online_session(domain_online_session_state.build())
    state = InvoiceSubmissionResumeState(
        reference_number=INVOICE_REF,
        session_reference_number=OTHER_SESSION_REF,
    )

    with pytest.raises(exceptions.KSeFArgumentError, match=OTHER_SESSION_REF):
        _ = session.submission(state=state)

    assert _paths(flavor) == []


def test_submission_rejects_both_reference_and_state(
    flavor: Flavor,
    domain_online_session_state: BaseFactory[OnlineSessionResumeState],
) -> None:
    session = flavor.online_session(domain_online_session_state.build())
    state = InvoiceSubmissionResumeState(
        reference_number=INVOICE_REF,
        session_reference_number=session.reference_number,
    )

    with pytest.raises(exceptions.KSeFArgumentError, match="exactly one"):
        _ = session.submission(INVOICE_REF, state=state)
    with pytest.raises(exceptions.KSeFArgumentError, match="exactly one"):
        _ = session.submission()

    assert session.submission(INVOICE_REF).reference_number == INVOICE_REF
    assert session.submission(state=state).reference_number == INVOICE_REF
    assert _paths(flavor) == []


@pytest.mark.parametrize(
    ("state_cls", "fields"),
    [
        (GeneratedTokenResumeState, {"reference_number": TOKEN_REF}),
        (CertificateEnrollmentResumeState, {"reference_number": ENROLLMENT_REF}),
        (PermissionOperationResumeState, {"reference_number": OPERATION_REF}),
        (
            InvoiceSubmissionResumeState,
            {
                "reference_number": INVOICE_REF,
                "session_reference_number": "20250625-SO-2C3E6C8000-B675CF5D68-07",
            },
        ),
    ],
    ids=["token", "enrollment", "permission", "submission"],
)
def test_resume_state_rejects_version_2_and_unknown_fields(
    state_cls: type[Any], fields: dict[str, str]
) -> None:
    state = state_cls(**fields)

    assert state.format_version == "1"
    assert state.to_json(indent=2) == json.dumps(state.to_dict(), indent=2)

    future_version = state.to_dict()
    future_version["format_version"] = 2
    with pytest.raises(ValidationError, match="unsupported format version"):
        state_cls.from_dict(future_version)
    with pytest.raises(ValidationError, match="unsupported format version"):
        state_cls.from_json(json.dumps(future_version))

    with_unknown_field = state.to_dict()
    with_unknown_field["future_capability"] = "must-not-be-ignored"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        state_cls.from_dict(with_unknown_field)

    assert state_cls.from_json(state.to_json()) == state
    assert state_cls.from_dict(state.to_dict()) == state


def test_async_handles_match_sync_resume_api() -> None:
    for sync_cls, async_cls, state_cls in _HANDLE_PAIRS:
        for cls in (sync_cls, async_cls):
            signature = inspect.signature(cls.resume_state)

            assert list(signature.parameters) == ["self"]
            assert state_cls.__name__ in str(signature.return_annotation)

    for sync_cls, async_cls, method_name, state_cls in _RESUMERS:
        for cls in (sync_cls, async_cls):
            state_parameter = inspect.signature(getattr(cls, method_name)).parameters[
                "state"
            ]

            assert state_cls.__name__ in str(state_parameter.annotation)
            assert "str" in str(state_parameter.annotation)
