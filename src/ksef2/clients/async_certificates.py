from collections.abc import AsyncIterator
from datetime import datetime
from typing import final

from ksef2.core.async_protocols import AsyncMiddleware
from ksef2.domain.models.certificates import (
    CertificateEnrollmentData,
    CertificateEnrollmentResponse,
    CertificateEnrollmentStatusResponse,
    CertificateInfo,
    CertificateLimitsResponse,
    CertificatesInfoList,
    CertificateStatusValue,
    CertificateTypeValue,
    EnrollCertificateRequest,
    QueryCertificatesRequest,
    RetrieveCertificatesRequest,
    RetrievedCertificatesList,
    RevocationReason,
    RevokeCertificateRequest,
)
from ksef2.domain.models.pagination import OffsetPaginationParams
from ksef2.endpoints.async_certificates import AsyncCertificatesEndpoints
from ksef2.infra.mappers.certificates import from_spec, to_spec


@final
class AsyncCertificatesClient:
    """Async high-level API for certificate enrollment, retrieval, and search."""

    def __init__(self, transport: AsyncMiddleware) -> None:
        self._endpoints = AsyncCertificatesEndpoints(transport)

    async def get_limits(self) -> CertificateLimitsResponse:
        return from_spec(await self._endpoints.get_limits())

    async def get_enrollment_data(self) -> CertificateEnrollmentData:
        return from_spec(await self._endpoints.get_enrollment_data())

    async def enroll(
        self,
        *,
        certificate_name: str,
        certificate_type: CertificateTypeValue,
        csr: str,
        valid_from: datetime | str | None = None,
    ) -> CertificateEnrollmentResponse:
        request = EnrollCertificateRequest(
            certificate_name=certificate_name,
            certificate_type=certificate_type,
            csr=csr,
            valid_from=valid_from,
        )
        body = to_spec(request)
        return from_spec(await self._endpoints.enroll(body=body))

    async def get_enrollment_status(
        self,
        *,
        reference_number: str,
    ) -> CertificateEnrollmentStatusResponse:
        return from_spec(
            await self._endpoints.get_enrollment_status(
                reference_number=reference_number,
            )
        )

    async def retrieve(
        self,
        *,
        certificate_serial_numbers: list[str],
    ) -> RetrievedCertificatesList:
        request = RetrieveCertificatesRequest(
            certificate_serial_numbers=certificate_serial_numbers,
        )
        body = to_spec(request)
        return from_spec(await self._endpoints.retrieve(body=body))

    async def revoke(
        self,
        *,
        certificate_serial_number: str,
        reason: RevocationReason | None = None,
    ) -> None:
        request = RevokeCertificateRequest(revocation_reason=reason)
        body = to_spec(request)
        await self._endpoints.revoke(
            certificate_serial_number=certificate_serial_number,
            body=body,
        )

    async def query(
        self,
        *,
        name: str | None = None,
        certificate_serial_number: str | None = None,
        certificate_type: CertificateTypeValue | None = None,
        status: CertificateStatusValue | None = None,
        expires_after: datetime | str | None = None,
        params: OffsetPaginationParams | None = None,
    ) -> CertificatesInfoList:
        parameters = params or OffsetPaginationParams()
        request = QueryCertificatesRequest(
            certificate_serial_number=certificate_serial_number,
            name=name,
            certificate_type=certificate_type,
            status=status,
            expires_after=expires_after,
        )
        body = to_spec(request)
        spec_resp = await self._endpoints.query(
            body=body, **parameters.to_query_params()
        )
        return from_spec(spec_resp)

    async def all(
        self,
        *,
        certificate_serial_number: str | None = None,
        name: str | None = None,
        certificate_type: CertificateTypeValue | None = None,
        status: CertificateStatusValue | None = None,
        expires_after: datetime | str | None = None,
        params: OffsetPaginationParams | None = None,
    ) -> AsyncIterator[CertificateInfo]:
        current_params = params or OffsetPaginationParams()

        while True:
            response = await self.query(
                name=name,
                certificate_serial_number=certificate_serial_number,
                certificate_type=certificate_type,
                status=status,
                expires_after=expires_after,
                params=current_params,
            )
            for certificate in response.certificates:
                yield certificate

            if not response.has_more:
                break

            current_params = current_params.next_page()
