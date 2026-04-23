from ksef2.domain.models import CertificateLimitsResponse
from ksef2.domain.models import certificates
from ksef2.infra.schema.api import spec
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from tests.unit.helpers import VALID_BASE64

VALID_CERTIFICATE_SERIAL_NUMBER = "0123456789ABCDEF"
VALID_CERTIFICATE_SERIAL_NUMBER_2 = "FEDCBA9876543210"
VALID_CERTIFICATE_SERIAL_NUMBER_3 = "ABCDEF1234567890"

# --- factories for spec models ---


@register_fixture(name="cert_limits_resp")
class CertificateLimitsResponseFactory(
    ModelFactory[spec.CertificateLimitsResponse]
): ...


@register_fixture(name="cert_enrollment_data_resp")
class CertificateEnrollmentDataResponseFactory(
    ModelFactory[spec.CertificateEnrollmentDataResponse]
): ...


@register_fixture(name="cert_enroll_req")
class EnrollCertificateRequestFactory(ModelFactory[spec.EnrollCertificateRequest]):
    csr: str = VALID_BASE64
    validFrom = None


@register_fixture(name="cert_enroll_resp")
class EnrollCertificateResponseFactory(
    ModelFactory[spec.EnrollCertificateResponse]
): ...


@register_fixture(name="cert_enrollment_status_resp")
class CertificateEnrollmentStatusResponseFactory(
    ModelFactory[spec.CertificateEnrollmentStatusResponse]
):
    certificateSerialNumber: str = VALID_CERTIFICATE_SERIAL_NUMBER


@register_fixture(name="cert_retrieve_req")
class RetrieveCertificatesRequestFactory(
    ModelFactory[spec.RetrieveCertificatesRequest]
):
    certificateSerialNumbers: list[str] = [VALID_CERTIFICATE_SERIAL_NUMBER]


class RetrieveCertificatesListItemFactory(
    ModelFactory[spec.RetrieveCertificatesListItem]
):
    certificate: str = VALID_BASE64
    certificateName: str = "Test Cert"
    certificateSerialNumber: str = VALID_CERTIFICATE_SERIAL_NUMBER
    certificateType: spec.KsefCertificateType = spec.KsefCertificateType.Authentication


@register_fixture(name="cert_retrieve_resp")
class RetrieveCertificatesResponseFactory(
    ModelFactory[spec.RetrieveCertificatesResponse]
):
    @classmethod
    def certificates(cls) -> list[spec.RetrieveCertificatesListItem]:
        return [RetrieveCertificatesListItemFactory.build()]


@register_fixture(name="cert_revoke_req")
class RevokeCertificateRequestFactory(ModelFactory[spec.RevokeCertificateRequest]): ...


@register_fixture(name="cert_query_req")
class QueryCertificatesRequestFactory(ModelFactory[spec.QueryCertificatesRequest]):
    certificateSerialNumber: str | None = VALID_CERTIFICATE_SERIAL_NUMBER


@register_fixture(name="cert_query_resp")
class QueryCertificatesResponseFactory(
    ModelFactory[spec.QueryCertificatesResponse]
): ...


class CertificateListItemFactory(ModelFactory[spec.CertificateListItem]):
    certificateSerialNumber: str = VALID_CERTIFICATE_SERIAL_NUMBER
    name: str = "Test Cert"
    commonName: str = "CN=Test"
    type: spec.KsefCertificateType = spec.KsefCertificateType.Authentication
    status: spec.CertificateListItemStatus = spec.CertificateListItemStatus.Active


class CertificateSubjectIdentifierFactory(
    ModelFactory[spec.CertificateSubjectIdentifier]
):
    type: spec.CertificateSubjectIdentifierType = (
        spec.CertificateSubjectIdentifierType.Pesel
    )
    value: str = "1234567890"


# --- factories for domain models ---


@register_fixture(name="domain_cert_limits_resp")
class DomainCertificateLimitsResponseFactory(
    ModelFactory[CertificateLimitsResponse]
): ...


@register_fixture(name="domain_enroll_cert_req")
class DomainEnrollCertificateRequestFactory(
    ModelFactory[certificates.EnrollCertificateRequest]
):
    certificate_type: str = "authentication"
    csr: str = VALID_BASE64


@register_fixture(name="domain_revoke_cert_req")
class DomainRevokeCertificateRequestFactory(
    ModelFactory[certificates.RevokeCertificateRequest]
):
    revocation_reason: str = "unspecified"


@register_fixture(name="domain_retrieve_certs_req")
class DomainRetrieveCertificatesRequestFactory(
    ModelFactory[certificates.RetrieveCertificatesRequest]
):
    certificate_serial_numbers: list[str] = [VALID_CERTIFICATE_SERIAL_NUMBER]


@register_fixture(name="domain_query_certs_req")
class DomainQueryCertificatesRequestFactory(
    ModelFactory[certificates.QueryCertificatesRequest]
):
    certificate_serial_number: str | None = VALID_CERTIFICATE_SERIAL_NUMBER
    certificate_type: str = "authentication"
    status: str = "active"
    expires_after: str = "2025-12-31T23:59:59+00:00"
