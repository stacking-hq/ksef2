from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import field_validator

from ksef2.domain.models.base import KSeFBaseModel
from ksef2.domain.models.session import FormSchema
from ksef2.domain.types import CurrencyCodes, KsefInvoiceTypes


type SortOrder = Literal["asc", "desc"]
type BuyerIdentifierType = Literal["nip", "vat_ue", "other", "none"]
type InvoiceType = KsefInvoiceTypes
type InvoicingMode = Literal["online", "offline"]
type ThirdSubjectIdentifierType = Literal[
    "nip", "internal_id", "vat_ue", "other", "none"
]

type SortOrderSpecValue = Literal["Asc", "Desc"]
type InvoicingModeSpecValue = Literal["Online", "Offline"]


class SortOrderEnum(StrEnum):
    ASC = "Asc"
    DESC = "Desc"


class BuyerIdentifierTypeEnum(StrEnum):
    NIP = "Nip"
    VAT_UE = "VatUe"
    OTHER = "Other"
    NONE = "None"


class InvoiceTypeEnum(StrEnum):
    VAT = "Vat"
    ZAL = "Zal"
    KOR = "Kor"
    ROZ = "Roz"
    UPR = "Upr"
    KOR_ZAL = "KorZal"
    KOR_ROZ = "KorRoz"
    VAT_PEF = "VatPef"
    VAT_PEF_SP = "VatPefSp"
    KOR_PEF = "KorPef"
    VAT_RR = "VatRr"
    KOR_VAT_RR = "KorVatRr"


class InvoicingModeEnum(StrEnum):
    ONLINE = "Online"
    OFFLINE = "Offline"


class ThirdSubjectIdentifierTypeEnum(StrEnum):
    NIP = "Nip"
    INTERNAL_ID = "InternalId"
    VAT_UE = "VatUe"
    OTHER = "Other"
    NONE = "None"


_SORT_ORDER_TO_SPEC: dict[SortOrder, SortOrderSpecValue] = {
    "asc": "Asc",
    "desc": "Desc",
}
_SORT_ORDER_FROM_SPEC: dict[SortOrderSpecValue, SortOrder] = {
    value: key for key, value in _SORT_ORDER_TO_SPEC.items()
}
_INVOICING_MODE_TO_SPEC: dict[InvoicingMode, InvoicingModeSpecValue] = {
    "online": "Online",
    "offline": "Offline",
}
_INVOICING_MODE_FROM_SPEC: dict[InvoicingModeSpecValue, InvoicingMode] = {
    value: key for key, value in _INVOICING_MODE_TO_SPEC.items()
}


def normalize_sort_order(value: SortOrder | SortOrderEnum | str) -> SortOrder:
    if isinstance(value, SortOrderEnum):
        return _SORT_ORDER_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _SORT_ORDER_TO_SPEC:
        return lowered_value  # pyright: ignore[reportReturnType]

    if value in _SORT_ORDER_FROM_SPEC:
        return _SORT_ORDER_FROM_SPEC[value]

    raise ValueError(
        f"Invalid sort order: {value}. Valid sort orders are: "
        f"{', '.join(_SORT_ORDER_TO_SPEC)}"
    )


def sort_order_to_spec(value: SortOrder | SortOrderEnum | str) -> SortOrderSpecValue:
    return _SORT_ORDER_TO_SPEC[normalize_sort_order(value)]


def normalize_invoicing_mode(
    value: InvoicingMode | InvoicingModeEnum | str,
) -> InvoicingMode:
    if isinstance(value, InvoicingModeEnum):
        return _INVOICING_MODE_FROM_SPEC[value.value]

    lowered_value = value.strip().lower()
    if lowered_value in _INVOICING_MODE_TO_SPEC:
        return lowered_value  # pyright: ignore[reportReturnType]

    if value in _INVOICING_MODE_FROM_SPEC:
        return _INVOICING_MODE_FROM_SPEC[value]

    raise ValueError(
        f"Invalid invoicing mode: {value}. Valid invoicing modes are: "
        f"{', '.join(_INVOICING_MODE_TO_SPEC)}"
    )


def invoicing_mode_to_spec(
    value: InvoicingMode | InvoicingModeEnum | str,
) -> InvoicingModeSpecValue:
    return _INVOICING_MODE_TO_SPEC[normalize_invoicing_mode(value)]


# ---------------------------------------------------------------------------
# Existing response request
# ---------------------------------------------------------------------------


class SendInvoiceResponse(KSeFBaseModel):
    """Response from ``POST /sessions/online/{ref}/invoices``."""

    reference_number: str


class InvoicesMetadataFilter(KSeFBaseModel):
    role: Literal["seller", "buyer", "third_subject", "authorized_subject"]
    date_from: datetime | str
    date_to: datetime | str
    invoice_number: str | None = None
    ksef_number: str | None = None
    amount_min: float | None = None
    amount_max: float | None = None


class Identity(KSeFBaseModel):
    type: Literal["nip"]
    value: str


# ---------------------------------------------------------------------------
# Response models — Invoice Metadata
# ---------------------------------------------------------------------------


class InvoiceMetadataSeller(KSeFBaseModel):
    nip: str
    name: str | None = None


class InvoiceMetadataBuyerIdentifier(KSeFBaseModel):
    type: BuyerIdentifierType
    value: str | None = None


class InvoiceMetadataBuyer(KSeFBaseModel):
    identifier: InvoiceMetadataBuyerIdentifier
    name: str | None = None


class InvoiceMetadataThirdSubjectIdentifier(KSeFBaseModel):
    type: ThirdSubjectIdentifierType
    value: str | None = None


class InvoiceMetadataThirdSubject(KSeFBaseModel):
    identifier: InvoiceMetadataThirdSubjectIdentifier
    name: str | None = None
    role: int


class InvoiceMetadataAuthorizedSubject(KSeFBaseModel):
    nip: str
    name: str | None = None
    role: int


class InvoiceMetadata(KSeFBaseModel):
    ksef_number: str
    invoice_number: str
    issue_date: date
    invoicing_date: datetime
    acquisition_date: datetime
    permanent_storage_date: datetime
    seller: InvoiceMetadataSeller
    buyer: InvoiceMetadataBuyer
    net_amount: float
    gross_amount: float
    vat_amount: float
    currency: str
    invoicing_mode: InvoicingMode
    invoice_type: InvoiceType
    form_code_system: str
    form_code_version: str
    form_code_value: str
    is_self_invoicing: bool
    has_attachment: bool
    invoice_hash: str
    hash_of_corrected_invoice: str | None = None
    third_subjects: list[InvoiceMetadataThirdSubject] | None = None
    authorized_subject: InvoiceMetadataAuthorizedSubject | None = None


class QueryInvoicesMetadataResponse(KSeFBaseModel):
    has_more: bool
    is_truncated: bool
    permanent_storage_hwm_date: datetime | None = None
    invoices: list[InvoiceMetadata]


# ---------------------------------------------------------------------------
# Response models — Export
# ---------------------------------------------------------------------------


class ExportInvoicesResponse(KSeFBaseModel):
    reference_number: str


class ExportStatusInfo(KSeFBaseModel):
    code: int
    description: str
    details: list[str] | None = None


class PackagePart(KSeFBaseModel):
    ordinal_number: int
    part_name: str
    method: str
    url: str
    part_size: int
    part_hash: str
    encrypted_part_size: int
    encrypted_part_hash: str
    expiration_date: datetime


class InvoicePackage(KSeFBaseModel):
    invoice_count: int
    size: int
    parts: list[PackagePart]
    is_truncated: bool
    last_issue_date: date | None = None
    last_invoicing_date: datetime | None = None
    last_permanent_storage_date: datetime | None = None
    permanent_storage_hwm_date: datetime | None = None


class InvoiceExportStatusResponse(KSeFBaseModel):
    status: ExportStatusInfo
    completed_date: datetime | None = None
    package_expiration_date: datetime | None = None
    package: InvoicePackage | None = None


@dataclass(frozen=True)
class ExportHandle:
    """Holds export reference + crypto keys needed to later fetch/decrypt the package."""

    reference_number: str
    aes_key: bytes
    iv: bytes


### Public API ###


class AmountMixin(KSeFBaseModel):
    amount_type: Literal["brutto", "netto", "vat"]
    amount_min: float | None = None
    amount_max: float | None = None


class InvoicesFilter(KSeFBaseModel):
    # role
    role: Literal["buyer", "seller", "third_subject", "authorized_subject"]

    # dates
    date_type: Literal["issue_date", "invoicing_date", "permanent_storage"]
    date_from: datetime | str
    date_to: datetime | str = field(default_factory=datetime.now)
    restrict_to_permanent_storage_hwm_date: bool | None = None

    # currency and amounts
    currency_codes: list[CurrencyCodes] | None = None
    amount_type: Literal["brutto", "netto", "vat"]
    amount_min: float | None = None
    amount_max: float | None = None

    # identification
    seller_nip: str | None = None
    buyer_nip: str | None = None
    buyer_vat_ue: str | None = None
    buyer_other_id: str | None = None
    invoice_number: str | None = None
    ksef_number: str | None = None

    # data
    invoice_schema: FormSchema | None = None
    invoice_types: list[KsefInvoiceTypes] | None = None
    has_attachment: bool | None = None

    # others
    invoicing_mode: InvoicingMode | None = None
    is_self_invoicing: bool | None = None

    @field_validator("invoicing_mode", mode="before")
    @classmethod
    def _normalize_invoicing_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_invoicing_mode(value)
        return value


class ExportInvoicesPayload(KSeFBaseModel):
    filter: InvoicesFilter
    encrypted_symmetric_key: str
    initialization_vector: str
    public_key_id: str | None = None
    only_metadata: bool = False


class SendInvoicePayload(KSeFBaseModel):
    xml_bytes: bytes
    encrypted_bytes: bytes
