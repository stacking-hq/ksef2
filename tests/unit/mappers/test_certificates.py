from polyfactory import BaseFactory

from ksef2.domain.models import certificates
from ksef2.infra.mappers.certificates.requests import to_spec
from ksef2.infra.mappers.certificates.responses import from_spec
from ksef2.infra.schema.api import spec
from tests.unit.factories.certificates import (
    CertificateListItemFactory,
    CertificateSubjectIdentifierFactory,
    DomainEnrollCertificateRequestFactory,
    DomainQueryCertificatesRequestFactory,
    DomainRetrieveCertificatesRequestFactory,
    DomainRevokeCertificateRequestFactory,
    RetrieveCertificatesListItemFactory,
)


class TestCertificatesMapper:
    def test_map_limits_response(
        self, cert_limits_resp: BaseFactory[spec.CertificateLimitsResponse]
    ):
        mapped_input = cert_limits_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificateLimitsResponse)
        assert output.can_request == mapped_input.canRequest
        assert output.enrollment_limit == mapped_input.enrollment.limit
        assert output.enrollment_remaining == mapped_input.enrollment.remaining
        assert output.certificate_limit == mapped_input.certificate.limit
        assert output.certificate_remaining == mapped_input.certificate.remaining

    def test_map_enrollment_data_response(
        self,
        cert_enrollment_data_resp: BaseFactory[spec.CertificateEnrollmentDataResponse],
    ):
        mapped_input = cert_enrollment_data_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificateEnrollmentData)
        assert output.common_name == mapped_input.commonName
        assert output.name == mapped_input.givenName
        assert output.surname == mapped_input.surname
        assert output.iso_country_code == mapped_input.countryName
        assert output.serial_number == mapped_input.serialNumber
        assert output.unique_identifier == mapped_input.uniqueIdentifier
        assert output.organization_name == mapped_input.organizationName
        assert output.organization_identifier == mapped_input.organizationIdentifier

    def test_map_enroll_certificate_response(
        self, cert_enroll_resp: BaseFactory[spec.EnrollCertificateResponse]
    ):
        mapped_input = cert_enroll_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificateEnrollmentResponse)
        assert output.reference_number == mapped_input.referenceNumber
        assert output.timestamp == mapped_input.timestamp

    def test_map_enrollment_status_response(
        self,
        cert_enrollment_status_resp: BaseFactory[
            spec.CertificateEnrollmentStatusResponse
        ],
    ):
        mapped_input = cert_enrollment_status_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificateEnrollmentStatusResponse)
        assert output.request_date == mapped_input.requestDate
        assert output.status_code == mapped_input.status.code
        assert output.status_description == mapped_input.status.description
        assert output.status_details == mapped_input.status.details
        assert output.certificate_serial_number == mapped_input.certificateSerialNumber

    def test_map_certificate_list_item(self):
        mapped_input = CertificateListItemFactory.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificateInfo)
        assert output.serial_number == mapped_input.certificateSerialNumber
        assert output.name == mapped_input.name
        assert output.common_name == mapped_input.commonName
        assert output.type == from_spec(mapped_input.type)
        assert output.status == from_spec(mapped_input.status)
        assert output.subject_identifier.type == from_spec(
            mapped_input.subjectIdentifier.type
        )
        assert output.subject_identifier.value == mapped_input.subjectIdentifier.value

    def test_map_subject_identifier_nip(self):
        mapped_input = CertificateSubjectIdentifierFactory.build(
            type=spec.CertificateSubjectIdentifierType.Nip
        )
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.SubjectIdentifier)
        assert output.type == "nip"
        assert output.value == mapped_input.value

    def test_map_subject_identifier_pesel(self):
        mapped_input = CertificateSubjectIdentifierFactory.build(
            type=spec.CertificateSubjectIdentifierType.Pesel
        )
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.SubjectIdentifier)
        assert output.type == "pesel"
        assert output.value == mapped_input.value

    def test_map_subject_identifier_fingerprint(self):
        mapped_input = CertificateSubjectIdentifierFactory.build(
            type=spec.CertificateSubjectIdentifierType.Fingerprint
        )
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.SubjectIdentifier)
        assert output.type == "fingerprint"
        assert output.value == mapped_input.value

    def test_map_certificate_status_active(self):
        output = from_spec(spec.CertificateListItemStatus.Active)
        assert output == "active"

    def test_map_certificate_status_revoked(self):
        output = from_spec(spec.CertificateListItemStatus.Revoked)
        assert output == "revoked"

    def test_map_certificate_status_expired(self):
        output = from_spec(spec.CertificateListItemStatus.Expired)
        assert output == "expired"

    def test_map_certificate_status_blocked(self):
        output = from_spec(spec.CertificateListItemStatus.Blocked)
        assert output == "blocked"

    def test_map_certificate_type_authentication(self):
        output = from_spec(spec.KsefCertificateType.Authentication)
        assert output == "authentication"

    def test_map_certificate_type_offline(self):
        output = from_spec(spec.KsefCertificateType.Offline)
        assert output == "offline"

    def test_map_query_certificates_response(
        self, cert_query_resp: BaseFactory[spec.QueryCertificatesResponse]
    ):
        mapped_input = cert_query_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.CertificatesInfoList)
        assert len(output.certificates) == len(mapped_input.certificates)
        assert output.has_more == mapped_input.hasMore

    def test_map_retrieve_certificates_list_item(self):
        mapped_input = RetrieveCertificatesListItemFactory.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.Certificate)
        assert output.name == mapped_input.certificateName
        assert output.certificate_type == from_spec(mapped_input.certificateType)
        assert output.base64_encoded_certificate == mapped_input.certificate
        assert output.serial_number == mapped_input.certificateSerialNumber

    def test_map_retrieve_certificates_response(
        self,
        cert_retrieve_resp: BaseFactory[spec.RetrieveCertificatesResponse],
    ):
        mapped_input = cert_retrieve_resp.build()
        output = from_spec(mapped_input)

        assert output is not None
        assert isinstance(output, certificates.RetrievedCertificatesList)
        assert len(output.certificates) == len(mapped_input.certificates)


class TestCertificatesRequestMapper:
    def test_to_spec_certificate_type_authentication(self):
        assert to_spec("authentication") == spec.KsefCertificateType.Authentication

    def test_to_spec_certificate_type_offline(self):
        assert to_spec("offline") == spec.KsefCertificateType.Offline

    def test_to_spec_certificate_status_active(self):
        assert to_spec("active") == spec.CertificateListItemStatus.Active

    def test_to_spec_certificate_status_blocked(self):
        assert to_spec("blocked") == spec.CertificateListItemStatus.Blocked

    def test_to_spec_certificate_status_revoked(self):
        assert to_spec("revoked") == spec.CertificateListItemStatus.Revoked

    def test_to_spec_certificate_status_expired(self):
        assert to_spec("expired") == spec.CertificateListItemStatus.Expired

    def test_to_spec_enroll_certificate_request(self):
        request = DomainEnrollCertificateRequestFactory.build(valid_from=None)
        output = to_spec(request)

        assert isinstance(output, spec.EnrollCertificateRequest)
        assert output.certificateName == request.certificate_name
        assert output.certificateType == to_spec(request.certificate_type)
        assert output.csr is not None
        assert output.validFrom is None

    def test_to_spec_enroll_certificate_request_with_valid_from(self):
        request = DomainEnrollCertificateRequestFactory.build(
            certificate_type="offline",
            valid_from="2025-06-01T12:00:00+00:00",
        )
        output = to_spec(request)

        assert isinstance(output, spec.EnrollCertificateRequest)
        assert output.certificateType == spec.KsefCertificateType.Offline
        assert output.validFrom is not None

    def test_to_spec_revoke_certificate_request_unspecified(self):
        request = DomainRevokeCertificateRequestFactory.build(
            revocation_reason="unspecified",
        )
        output = to_spec(request)

        assert isinstance(output, spec.RevokeCertificateRequest)
        assert output.revocationReason == spec.CertificateRevocationReason.Unspecified

    def test_to_spec_revoke_certificate_request_superseded(self):
        request = DomainRevokeCertificateRequestFactory.build(
            revocation_reason="superseded",
        )
        output = to_spec(request)

        assert isinstance(output, spec.RevokeCertificateRequest)
        assert output.revocationReason == spec.CertificateRevocationReason.Superseded

    def test_to_spec_revoke_certificate_request_key_compromise(self):
        request = DomainRevokeCertificateRequestFactory.build(
            revocation_reason="key_compromise",
        )
        output = to_spec(request)

        assert isinstance(output, spec.RevokeCertificateRequest)
        assert output.revocationReason == spec.CertificateRevocationReason.KeyCompromise

    def test_to_spec_revoke_certificate_request_none(self):
        request = DomainRevokeCertificateRequestFactory.build(
            revocation_reason=None,
        )
        output = to_spec(request)

        assert output is None

    def test_to_spec_retrieve_certificates_request(self):
        request = DomainRetrieveCertificatesRequestFactory.build()
        output = to_spec(request)

        assert isinstance(output, spec.RetrieveCertificatesRequest)
        assert output.model_dump(mode="json")["certificateSerialNumbers"] == (
            request.certificate_serial_numbers
        )

    def test_to_spec_query_certificates_request_minimal(self):
        request = DomainQueryCertificatesRequestFactory.build(
            certificate_serial_number=None,
            name=None,
            certificate_type=None,
            status=None,
            expires_after=None,
        )
        output = to_spec(request)

        assert isinstance(output, spec.QueryCertificatesRequest)
        assert output.certificateSerialNumber is None
        assert output.name is None
        assert output.type is None
        assert output.status is None
        assert output.expiresAfter is None

    def test_to_spec_query_certificates_request_full(self):
        request = DomainQueryCertificatesRequestFactory.build()
        output = to_spec(request)

        assert isinstance(output, spec.QueryCertificatesRequest)
        assert output.certificateSerialNumber == request.certificate_serial_number
        assert output.name == request.name
        assert request.certificate_type is not None
        assert request.status is not None
        assert output.type == to_spec(request.certificate_type)
        assert output.status == to_spec(request.status)
        assert output.expiresAfter is not None
