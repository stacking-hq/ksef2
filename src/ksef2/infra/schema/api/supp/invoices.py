from datetime import date
from typing import Annotated

from pydantic import AnyUrl, AwareDatetime, Field

from ksef2.infra.schema.api.spec.models import (
    CompressionType,
    FormCode,
    InvoiceMetadataAuthorizedSubject,
    InvoiceMetadataBuyerIdentifier,
    InvoiceMetadataSeller,
    InvoiceMetadataThirdSubjectIdentifier,
    InvoiceQueryFilters,
    InvoiceStatusInfo,
    InvoiceType,
    InvoicingMode,
    StatusInfo,
)
from ksef2.infra.schema.api.supp.base import BaseSupp
from ksef2.infra.schema.api.supp.session import EncryptionInfo


class SendInvoiceRequest(BaseSupp):
    invoiceHash: Annotated[str, Field(max_length=44, min_length=44)]
    invoiceSize: Annotated[int, Field(ge=1)]
    encryptedInvoiceHash: Annotated[str, Field(max_length=44, min_length=44)]
    encryptedInvoiceSize: Annotated[int, Field(ge=1)]
    encryptedInvoiceContent: str
    offlineMode: bool = False


class SessionInvoiceStatusResponse(BaseSupp):
    ordinalNumber: Annotated[int, Field(ge=1)]
    invoiceNumber: Annotated[str | None, Field(max_length=256)] = None
    ksefNumber: Annotated[
        str | None,
        Field(
            max_length=36,
            min_length=35,
            pattern="^([1-9](\\d[1-9]|[1-9]\\d)\\d{7})-(20[2-9][0-9]|2[1-9]\\d{2}|[3-9]\\d{3})(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])-([0-9A-F]{6})-?([0-9A-F]{6})-([0-9A-F]{2})$",
        ),
    ] = None
    referenceNumber: Annotated[str, Field(max_length=36, min_length=36)]
    invoiceHash: Annotated[str, Field(max_length=44, min_length=44)]
    invoiceFileName: Annotated[str | None, Field(max_length=128)] = None
    acquisitionDate: AwareDatetime | None = None
    invoicingDate: AwareDatetime
    permanentStorageDate: AwareDatetime | None = None
    upoDownloadUrl: AnyUrl | None = None
    upoDownloadUrlExpirationDate: AwareDatetime | None = None
    invoicingMode: InvoicingMode | None = None
    status: InvoiceStatusInfo


class SessionInvoicesResponse(BaseSupp):
    continuationToken: str | None = None
    invoices: list[SessionInvoiceStatusResponse] = []


# ---------------------------------------------------------------------------
# Invoice query / export supplementary models
# ---------------------------------------------------------------------------


class InvoiceExportRequest(BaseSupp):
    encryption: EncryptionInfo
    onlyMetadata: bool = False
    filters: InvoiceQueryFilters
    compressionType: CompressionType | None = None


class InvoiceMetadataBuyer(BaseSupp):
    identifier: InvoiceMetadataBuyerIdentifier
    name: Annotated[str | None, Field(max_length=512)] = None


class InvoiceMetadataThirdSubject(BaseSupp):
    identifier: InvoiceMetadataThirdSubjectIdentifier
    name: Annotated[str | None, Field(max_length=512)] = None
    role: int


class InvoiceMetadata(BaseSupp):
    ksefNumber: Annotated[
        str,
        Field(
            max_length=36,
            min_length=35,
            pattern="^([1-9](\\d[1-9]|[1-9]\\d)\\d{7})-(20[2-9][0-9]|2[1-9]\\d{2}|[3-9]\\d{3})(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])-([0-9A-F]{6})-?([0-9A-F]{6})-([0-9A-F]{2})$",
        ),
    ]
    invoiceNumber: Annotated[str, Field(max_length=256)]
    issueDate: date
    invoicingDate: AwareDatetime
    acquisitionDate: AwareDatetime
    permanentStorageDate: AwareDatetime
    seller: InvoiceMetadataSeller
    buyer: InvoiceMetadataBuyer
    netAmount: float
    grossAmount: float
    vatAmount: float
    currency: Annotated[str, Field(max_length=3, min_length=3)]
    invoicingMode: InvoicingMode
    invoiceType: InvoiceType
    formCode: FormCode
    isSelfInvoicing: bool
    hasAttachment: bool
    invoiceHash: Annotated[str, Field(max_length=44, min_length=44)]
    hashOfCorrectedInvoice: Annotated[
        str | None, Field(max_length=44, min_length=44)
    ] = None
    thirdSubjects: list[InvoiceMetadataThirdSubject] | None = None
    authorizedSubject: InvoiceMetadataAuthorizedSubject | None = None


class QueryInvoicesMetadataResponse(BaseSupp):
    hasMore: bool
    isTruncated: bool
    permanentStorageHwmDate: AwareDatetime | None = None
    invoices: list[InvoiceMetadata]


class InvoicePackagePart(BaseSupp):
    ordinalNumber: Annotated[int, Field(ge=1)]
    partName: Annotated[str, Field(max_length=100)]
    method: str
    url: AnyUrl
    partSize: Annotated[int, Field(ge=1)]
    partHash: Annotated[str, Field(max_length=44, min_length=44)]
    encryptedPartSize: Annotated[int, Field(ge=1)]
    encryptedPartHash: Annotated[str, Field(max_length=44, min_length=44)]
    expirationDate: AwareDatetime


class InvoicePackage(BaseSupp):
    invoiceCount: Annotated[int, Field(ge=0, le=10000)]
    size: Annotated[int, Field(ge=0)]
    parts: list[InvoicePackagePart]
    isTruncated: bool
    lastIssueDate: date | None = None
    lastInvoicingDate: AwareDatetime | None = None
    lastPermanentStorageDate: AwareDatetime | None = None
    permanentStorageHwmDate: AwareDatetime | None = None


class InvoiceExportStatusResponse(BaseSupp):
    status: StatusInfo
    completedDate: AwareDatetime | None = None
    packageExpirationDate: AwareDatetime | None = None
    package: InvoicePackage | None = None


# ---------------------------------------------------------------------------
# Query params models
# ---------------------------------------------------------------------------


class QueryInvoicesMetadataParams(BaseSupp):
    sortOrder: str | None = None
    pageOffset: int | None = None
    pageSize: int | None = None


class ListSessionInvoicesParams(BaseSupp):
    pageSize: int | None = None


class QueryInvoicesMetadataRequest(BaseSupp):
    filters: InvoiceQueryFilters


# ---------------------------------------------------------------------------
# Certificate request models
# ---------------------------------------------------------------------------


class EnrollCertificateRequest(BaseSupp):
    csr: str


class RetrieveCertificatesRequest(BaseSupp):
    certificateSerialNumbers: list[str]


class RevokeCertificateRequest(BaseSupp):
    reasonCode: int | None = None


class QueryCertificatesRequest(BaseSupp):
    filters: "InvoiceQueryFilters"
