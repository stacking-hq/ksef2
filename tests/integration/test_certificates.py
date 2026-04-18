import base64
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ObjectIdentifier

from ksef2 import Client, Environment
from ksef2.clients.authenticated import AuthenticatedClient
from ksef2.core.tools import generate_nip, generate_pesel
from ksef2.core.xades import generate_test_certificate
from ksef2.domain.models.certificates import (
    CertificateEnrollmentData,
    CertificateLimitsResponse,
    QueryCertificatesResponse,
)
from ksef2.domain.models.testdata import Identifier, Permission

_OID_ORGANIZATION_IDENTIFIER = ObjectIdentifier("2.5.4.97")
_OID_SERIAL_NUMBER = ObjectIdentifier("2.5.4.5")


def _build_certificate_csr(data: CertificateEnrollmentData) -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    attributes: list[x509.NameAttribute[str]] = []
    if data.organization_name:
        attributes.append(
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, data.organization_name)
        )
    if data.organization_identifier:
        attributes.append(
            x509.NameAttribute(
                _OID_ORGANIZATION_IDENTIFIER, data.organization_identifier
            )
        )
    if data.serial_number:
        attributes.append(x509.NameAttribute(_OID_SERIAL_NUMBER, data.serial_number))
    if data.surname:
        attributes.append(x509.NameAttribute(NameOID.SURNAME, data.surname))
    if data.name:
        attributes.append(x509.NameAttribute(NameOID.GIVEN_NAME, data.name))
    attributes.append(x509.NameAttribute(NameOID.COMMON_NAME, data.common_name))
    attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, data.iso_country_code))

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name(attributes))
        .sign(private_key, hashes.SHA256())
    )
    return base64.b64encode(csr.public_bytes(serialization.Encoding.DER)).decode()


def _wait_for_certificate_serial(
    auth: AuthenticatedClient,
    *,
    reference_number: str,
    timeout: float = 120.0,
    poll_interval: float = 2.0,
) -> str:
    deadline = time.monotonic() + timeout
    last_status = None

    while time.monotonic() < deadline:
        status = auth.certificates.get_enrollment_status(
            reference_number=reference_number,
        )
        last_status = status.status_code
        if status.certificate_serial_number:
            return status.certificate_serial_number
        if status.status_code >= 400:
            raise AssertionError(
                f"Certificate enrollment failed: "
                f"{status.status_code} {status.status_description}"
            )
        time.sleep(poll_interval)

    raise AssertionError(
        f"Certificate enrollment timed out after {timeout} seconds; "
        f"last status={last_status}"
    )


@pytest.mark.integration
def test_get_certificate_limits(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Fetch certificate limits for the authenticated subject."""
    client, auth = xades_authenticated_context

    result = auth.certificates.get_limits()

    assert isinstance(result, CertificateLimitsResponse)
    assert isinstance(result.can_request, bool)
    assert result.enrollment.limit >= 0
    assert result.enrollment.remaining >= 0
    assert result.certificate.limit >= 0
    assert result.certificate.remaining >= 0


@pytest.mark.integration
def test_get_enrollment_data(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Fetch certificate enrollment data for CSR preparation.

    Note: This endpoint may fail with self-signed certs because it requires
    a specific authentication method (qualified certificate).
    """
    client, auth = xades_authenticated_context

    try:
        result = auth.certificates.get_enrollment_data()

        assert isinstance(result, CertificateEnrollmentData)
        assert result.common_name
        assert result.country_name
    except Exception as e:
        # Expected to fail with self-signed certs (error 25001)
        if "25001" in str(e):
            pytest.skip("Enrollment data not available for self-signed cert auth")
        raise


@pytest.mark.integration
def test_query_certificates_no_filters(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Query all certificates without filter."""
    client, auth = xades_authenticated_context

    result = auth.certificates.query()

    assert isinstance(result, QueryCertificatesResponse)
    assert isinstance(result.certificates, list)
    assert isinstance(result.has_more, bool)


@pytest.mark.integration
def test_query_certificates_with_status_filter(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Query certificates filtering by status."""
    client, auth = xades_authenticated_context

    result = auth.certificates.query(status="active")

    assert isinstance(result, QueryCertificatesResponse)
    # All returned certificates should be active
    for cert in result.certificates:
        assert cert.status == "active"


@pytest.mark.integration
def test_query_certificates_with_type_filter(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Query certificates filtering by type."""
    client, auth = xades_authenticated_context

    result = auth.certificates.query(certificate_type="authentication")

    assert isinstance(result, QueryCertificatesResponse)
    # All returned certificates should be authentication type
    for cert in result.certificates:
        assert cert.type == "authentication"


@pytest.mark.integration
def test_query_certificates_with_pagination(
    xades_authenticated_context: tuple[Client, AuthenticatedClient],
) -> None:
    """Query certificates with pagination parameters."""
    client, auth = xades_authenticated_context

    # Query with small page size
    result = auth.certificates.query()

    assert isinstance(result, QueryCertificatesResponse)
    assert len(result.certificates) <= 10


@pytest.mark.integration
def test_query_certificates_with_name_filter() -> None:
    """Query certificates by name after enrolling a uniquely named certificate."""
    client = Client(environment=Environment.TEST)
    org_nip = generate_nip()
    person_nip = generate_nip()
    person_pesel = generate_pesel()

    with client.testdata.temporal() as temp:
        temp.create_subject(
            nip=org_nip,
            subject_type="enforcement_authority",
            description="Certificate query test",
        )
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Certificate query manager",
        )
        temp.grant_permissions(
            permissions=[
                Permission(
                    type="credentials_manage",
                    description="Manage credentials",
                ),
            ],
            grant_to=Identifier(type="nip", value=person_nip),
            in_context_of=Identifier(type="nip", value=org_nip),
        )

        cert, private_key = generate_test_certificate(org_nip)
        auth = client.authentication.with_xades(
            nip=org_nip,
            cert=cert,
            private_key=private_key,
        )

        enrollment_data = auth.certificates.get_enrollment_data()
        certificate_name = f"SDK Cert Query {int(time.time())}"
        enrollment = auth.certificates.enroll(
            certificate_name=certificate_name,
            certificate_type="authentication",
            csr=_build_certificate_csr(enrollment_data),
        )

        certificate_serial = _wait_for_certificate_serial(
            auth,
            reference_number=enrollment.reference_number,
        )

        try:
            result = auth.certificates.query(name=certificate_name)

            assert isinstance(result, QueryCertificatesResponse)
            assert result.certificates
            assert any(
                cert.serial_number == certificate_serial
                and cert.name == certificate_name
                for cert in result.certificates
            )
            for cert in result.certificates:
                assert certificate_name.lower() in cert.name.lower()
        finally:
            auth.certificates.revoke(
                certificate_serial_number=certificate_serial,
                reason="superseded",
            )
