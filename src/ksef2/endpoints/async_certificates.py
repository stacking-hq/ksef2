from typing import Unpack, final

from ksef2.core import routes
from ksef2.domain.types import OffsetPaginationQueryParams
from ksef2.endpoints.async_base import AsyncBaseEndpoints
from ksef2.infra.schema.api import spec


@final
class AsyncCertificatesEndpoints(AsyncBaseEndpoints):
    """Raw certificate endpoints backed by generated schema models."""

    async def get_limits(self) -> spec.CertificateLimitsResponse:
        """Fetch effective certificate quotas."""
        return self._parse(
            await self._transport.get(
                path=routes.CertificateRoutes.LIMITS,
            ),
            spec.CertificateLimitsResponse,
        )

    async def get_enrollment_data(self) -> spec.CertificateEnrollmentDataResponse:
        """Fetch subject data needed to prepare a certificate request."""
        return self._parse(
            await self._transport.get(
                path=routes.CertificateRoutes.ENROLLMENT_DATA,
            ),
            spec.CertificateEnrollmentDataResponse,
        )

    async def enroll(
        self, body: spec.EnrollCertificateRequest
    ) -> spec.EnrollCertificateResponse:
        """Start certificate enrollment from a schema-native payload."""
        return self._parse(
            await self._transport.post(
                path=routes.CertificateRoutes.ENROLLMENT,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.EnrollCertificateResponse,
        )

    async def get_enrollment_status(
        self, reference_number: str
    ) -> spec.CertificateEnrollmentStatusResponse:
        """Fetch enrollment status by reference number."""
        return self._parse(
            await self._transport.get(
                path=routes.CertificateRoutes.ENROLLMENT_STATUS.format(
                    referenceNumber=reference_number
                ),
            ),
            spec.CertificateEnrollmentStatusResponse,
        )

    async def retrieve(
        self, body: spec.RetrieveCertificatesRequest
    ) -> spec.RetrieveCertificatesResponse:
        """Retrieve issued certificates from a schema-native request payload."""
        return self._parse(
            await self._transport.post(
                path=routes.CertificateRoutes.RETRIEVE,
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.RetrieveCertificatesResponse,
        )

    async def revoke(
        self,
        certificate_serial_number: str,
        body: spec.RevokeCertificateRequest | None = None,
    ) -> None:
        """Revoke a certificate, optionally sending a revocation reason."""
        _ = await self._transport.post(
            path=routes.CertificateRoutes.REVOKE.format(
                certificateSerialNumber=certificate_serial_number
            ),
            json=body.model_dump(mode="json", by_alias=True) if body else None,
        )

    async def query(
        self,
        body: spec.QueryCertificatesRequest,
        **params: Unpack[OffsetPaginationQueryParams],
    ) -> spec.QueryCertificatesResponse:
        """Fetch one page of certificate query results."""
        return self._parse(
            await self._transport.post(
                path=routes.CertificateRoutes.QUERY,
                params=self.build_params(params),
                json=body.model_dump(mode="json", by_alias=True),
            ),
            spec.QueryCertificatesResponse,
        )
