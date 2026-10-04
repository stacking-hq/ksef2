"""Domain models for invoice metadata, sending, downloading, and export."""

import base64
import json
from collections.abc import Mapping
from dataclasses import field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import ConfigDict, Field as PydanticField, SecretStr
from pydantic import field_validator, model_validator

from ksef2._domain.models.base import KSeFBaseModel, KSeFPersistedModel
from ksef2._domain.models.compression import (
    CompressionType,
    normalize_compression_type,
)
from ksef2._domain.models.session import (
    FormSchema,
    _validate_encoded_session_secret,  # pyright: ignore[reportPrivateUsage]
)
from ksef2._domain.types import CurrencyCodes, KsefInvoiceTypes


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
    """Runtime enum for invoice metadata sort order values."""

    ASC = "Asc"
    DESC = "Desc"


class BuyerIdentifierTypeEnum(StrEnum):
    """Runtime enum for buyer identifier types in invoice metadata."""

    NIP = "Nip"
    VAT_UE = "VatUe"
    OTHER = "Other"
    NONE = "None"


class InvoiceTypeEnum(StrEnum):
    """Runtime enum for KSeF invoice type values."""

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
    """Runtime enum for invoice submission modes."""

    ONLINE = "Online"
    OFFLINE = "Offline"


class ThirdSubjectIdentifierTypeEnum(StrEnum):
    """Runtime enum for third-subject identifier types."""

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
_WARSAW_TIMEZONE = ZoneInfo("Europe/Warsaw")


def normalize_sort_order(value: SortOrder | SortOrderEnum | str) -> SortOrder:
    """Normalize SDK or OpenAPI sort order values to SDK literals.

    Raises:
        ValueError: If ``value`` is not a supported sort order.
    """
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
    """Convert a sort order value to the OpenAPI representation."""
    return _SORT_ORDER_TO_SPEC[normalize_sort_order(value)]


def normalize_invoicing_mode(
    value: InvoicingMode | InvoicingModeEnum | str,
) -> InvoicingMode:
    """Normalize SDK or OpenAPI invoicing mode values to SDK literals.

    Raises:
        ValueError: If ``value`` is not a supported invoicing mode.
    """
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
    """Convert an invoicing mode value to the OpenAPI representation."""
    return _INVOICING_MODE_TO_SPEC[normalize_invoicing_mode(value)]


# ---------------------------------------------------------------------------
# Existing response request
# ---------------------------------------------------------------------------


class SendInvoiceResponse(KSeFBaseModel):
    """Response from ``POST /sessions/online/{ref}/invoices``."""

    reference_number: str
    """KSeF reference number of the submitted invoice within the session."""


class InvoicesMetadataFilter(KSeFBaseModel):
    """Legacy invoice metadata filter model retained for compatibility."""

    role: Literal["seller", "buyer", "third_subject", "authorized_subject"]
    """Role of the authenticated subject on the invoices to list."""
    date_from: datetime | str
    """Start of the date range (inclusive), as a datetime or ISO 8601 string."""
    date_to: datetime | str
    """End of the date range, as a datetime or ISO 8601 string."""
    invoice_number: str | None = None
    """Seller's invoice number to match exactly."""
    ksef_number: str | None = None
    """KSeF number of the invoice to match exactly."""
    amount_min: float | None = None
    """Minimum amount to match."""
    amount_max: float | None = None
    """Maximum amount to match."""


class Identity(KSeFBaseModel):
    """NIP identity used by invoice metadata filters."""

    type: Literal["nip"]
    """Identifier kind; always ``nip``."""
    value: str
    """NIP value."""


# ---------------------------------------------------------------------------
# Response models — Invoice Metadata
# ---------------------------------------------------------------------------


class InvoiceMetadataSeller(KSeFBaseModel):
    """Seller data returned with invoice metadata."""

    nip: str
    """NIP of the seller."""
    name: str | None = None
    """Name of the seller, if present on the invoice."""


class InvoiceMetadataBuyerIdentifier(KSeFBaseModel):
    """Buyer identifier returned with invoice metadata."""

    type: BuyerIdentifierType
    """Kind of buyer identifier, such as ``nip``, ``vat_ue``, ``other`` or ``none``."""
    value: str | None = None
    """Buyer identifier value; ``None`` when the buyer has no identifier."""


class InvoiceMetadataBuyer(KSeFBaseModel):
    """Buyer data returned with invoice metadata."""

    identifier: InvoiceMetadataBuyerIdentifier
    """Identifier of the buyer."""
    name: str | None = None
    """Name of the buyer, if present on the invoice."""


class InvoiceMetadataThirdSubjectIdentifier(KSeFBaseModel):
    """Third-subject identifier returned with invoice metadata."""

    type: ThirdSubjectIdentifierType
    """Kind of third-subject identifier."""
    value: str | None = None
    """Third-subject identifier value; ``None`` when absent."""


class InvoiceMetadataThirdSubject(KSeFBaseModel):
    """Third subject data returned with invoice metadata."""

    identifier: InvoiceMetadataThirdSubjectIdentifier
    """Identifier of the third subject."""
    name: str | None = None
    """Name of the third subject, if present on the invoice."""
    role: int
    """Numeric role code of the third subject on the invoice."""


class InvoiceMetadataAuthorizedSubject(KSeFBaseModel):
    """Authorized subject data returned with invoice metadata."""

    nip: str
    """NIP of the authorized subject."""
    name: str | None = None
    """Name of the authorized subject, if present on the invoice."""
    role: int
    """Numeric role code of the authorized subject on the invoice."""


class InvoiceMetadata(KSeFBaseModel):
    """Metadata describing an invoice visible to the authenticated subject."""

    ksef_number: str
    """KSeF number assigned to the invoice."""
    invoice_number: str
    """Seller's invoice number."""
    issue_date: date
    """Issue date stated on the invoice."""
    invoicing_date: datetime
    """When the invoice was submitted to KSeF."""
    acquisition_date: datetime
    """When KSeF accepted the invoice and assigned its KSeF number."""
    permanent_storage_date: datetime
    """When the invoice was moved to permanent storage."""
    seller: InvoiceMetadataSeller
    """Seller of the invoice."""
    buyer: InvoiceMetadataBuyer
    """Buyer of the invoice."""
    net_amount: float
    """Total net amount."""
    gross_amount: float
    """Total gross amount."""
    vat_amount: float
    """Total VAT amount."""
    currency: str
    """ISO 4217 currency code of the invoice."""
    invoicing_mode: InvoicingMode
    """Whether the invoice was issued online or offline."""
    invoice_type: InvoiceType
    """KSeF invoice type, such as a standard invoice or a correction."""
    form_code_system: str
    """System code of the invoice schema, for example ``FA (3)``."""
    form_code_version: str
    """Schema version of the invoice, for example ``1-0E``."""
    form_code_value: str
    """Form value of the invoice schema, for example ``FA``."""
    is_self_invoicing: bool
    """Whether the invoice was issued by the buyer on the seller's behalf (self-invoicing)."""
    has_attachment: bool
    """Whether the invoice carries an attachment."""
    invoice_hash: str
    """SHA-256 hash of the invoice XML, Base64-encoded."""
    hash_of_corrected_invoice: str | None = None
    """Hash of the invoice corrected by this one; ``None`` for non-corrections."""
    third_subjects: list[InvoiceMetadataThirdSubject] | None = None
    """Third subjects named on the invoice, if any."""
    authorized_subject: InvoiceMetadataAuthorizedSubject | None = None
    """Authorized subject named on the invoice, if any."""


class QueryInvoicesMetadataResponse(KSeFBaseModel):
    """One page of invoice metadata query results."""

    has_more: bool
    """Whether more results are available after this page."""
    is_truncated: bool
    """Whether the result set was cut at the server-side limit; narrow the filter or continue from the last dates."""
    permanent_storage_hwm_date: datetime | None = None
    """High-water mark of permanent storage up to which results are complete; ``None`` if not reported."""
    invoices: list[InvoiceMetadata]
    """Invoice metadata records on this page."""


# ---------------------------------------------------------------------------
# Response models — Export
# ---------------------------------------------------------------------------


class ExportInvoicesResponse(KSeFBaseModel):
    """Reference returned after scheduling an invoice export."""

    reference_number: str
    """KSeF reference number of the scheduled export operation."""


class ExportStatusInfo(KSeFBaseModel):
    """Status code and description for an invoice export operation."""

    code: int
    """Numeric status code of the export operation."""
    description: str
    """Human-readable description of the status."""
    details: list[str] | None = None
    """Additional status details, if any."""


class PackagePart(KSeFBaseModel):
    """Download metadata for one encrypted package part."""

    ordinal_number: int
    """One-based position of this part in the package."""
    part_name: str
    """File name of the part."""
    method: str
    """HTTP method to use when downloading the part."""
    url: str = PydanticField(exclude=True, repr=False)
    """Pre-signed download URL of the part. Excluded from serialization and ``repr``."""
    part_size: int
    """Size of the part in bytes before encryption."""
    part_hash: str
    """SHA-256 hash of the part before encryption, Base64-encoded."""
    encrypted_part_size: int
    """Size of the encrypted part in bytes."""
    encrypted_part_hash: str
    """SHA-256 hash of the encrypted part, Base64-encoded."""
    expiration_date: datetime
    """When the download URL expires."""

    def to_sensitive_dict(
        self, *, mode: Literal["json", "python"] | str = "json"
    ) -> dict[str, object]:
        """Export package metadata with its presigned capability URL.

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary including the plain download URL.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        data["url"] = self.url
        return data


class InvoicePackage(KSeFBaseModel):
    """Package metadata returned when an invoice export is ready."""

    invoice_count: int
    """Number of invoices in the package."""
    size: int
    """Total size of the package in bytes."""
    parts: list[PackagePart]
    """Package parts to download and concatenate."""
    is_truncated: bool
    """Whether the export hit the server-side limit and more invoices match the filter."""
    last_issue_date: date | None = None
    """Issue date of the last invoice in the package, for continuing a truncated export."""
    last_invoicing_date: datetime | None = None
    """Invoicing date of the last invoice in the package, for continuing a truncated export."""
    last_permanent_storage_date: datetime | None = None
    """Permanent-storage date of the last invoice in the package, for continuing a truncated export."""
    permanent_storage_hwm_date: datetime | None = None
    """High-water mark of permanent storage covered by the package."""


class InvoiceExportStatusResponse(KSeFBaseModel):
    """Status response for a scheduled invoice export."""

    status: ExportStatusInfo
    """Status of the export operation."""
    completed_date: datetime | None = None
    """When the export finished; ``None`` while it is running."""
    package_expiration_date: datetime | None = None
    """When the package stops being downloadable; ``None`` until the export is ready."""
    package: InvoicePackage | None = None
    """Package metadata once the export is ready; ``None`` before that."""


class ExportHandle(KSeFBaseModel):
    """Holds export reference + crypto keys needed to later fetch/decrypt the package."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    reference_number: str
    """KSeF reference number of the export operation."""
    aes_key: bytes = PydanticField(exclude=True, repr=False)
    """AES-256 key used to decrypt the exported package. Excluded from serialization and ``repr``."""
    iv: bytes = PydanticField(exclude=True, repr=False)
    """Initialization vector used to decrypt the exported package. Excluded from serialization and ``repr``."""

    def to_sensitive_dict(self) -> dict[str, str | bytes]:
        """Export the key material only for deliberate protected handling.

        Returns:
            A dictionary with the reference number, AES key and initialization vector.
        """
        return {
            "reference_number": self.reference_number,
            "aes_key": self.aes_key,
            "iv": self.iv,
        }


class ExportResumeState(KSeFPersistedModel):
    """Serializable state needed to resume an invoice export after a restart.

    ``ExportJob.resume_state()`` returns it and ``auth.invoices.export(state=...)``
    turns it back into an ``ExportJob``. It holds the AES key and IV that decrypt
    the package, so treat ``to_json()`` and ``to_dict()`` output as credential
    material. ``model_dump()`` and ``repr()`` redact the secrets and are not a
    persistence format.
    """

    format_version: Literal[1] = 1
    """Version of the serialized state format; currently always ``1``."""
    reference_number: str
    """KSeF reference number of the export operation."""
    aes_key: SecretStr
    """AES-256 key that decrypts the package, Base64 encoded."""
    iv: SecretStr
    """Initialization vector that decrypts the package, Base64 encoded."""

    @field_validator("aes_key", mode="before")
    @classmethod
    def _validate_encoded_aes_key(cls, value: object) -> object:
        return _validate_encoded_session_secret(
            value, field_name="aes_key", expected_length=32
        )

    @field_validator("iv", mode="before")
    @classmethod
    def _validate_encoded_iv(cls, value: object) -> object:
        return _validate_encoded_session_secret(
            value, field_name="iv", expected_length=16
        )

    @classmethod
    def from_handle(cls, handle: ExportHandle) -> Self:
        """Create state from an export handle.

        Args:
            handle: Handle returned when the export was scheduled.

        Returns:
            State holding the reference number and the Base64-encoded key material.
        """
        return cls(
            reference_number=handle.reference_number,
            aes_key=SecretStr(base64.b64encode(handle.aes_key).decode()),
            iv=SecretStr(base64.b64encode(handle.iv).decode()),
        )

    def to_handle(self) -> ExportHandle:
        """Rebuild the export handle with raw key material.

        Returns:
            A handle with the reference number and the decoded AES key and IV.
        """
        return ExportHandle(
            reference_number=self.reference_number,
            aes_key=base64.b64decode(self.aes_key.get_secret_value(), validate=True),
            iv=base64.b64decode(self.iv.get_secret_value(), validate=True),
        )

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] | str = "json",
    ) -> dict[str, object]:
        """Export the state with the secrets included.

        Args:
            mode: Pydantic dump mode, ``"json"`` for JSON-safe values or ``"python"`` for native types.

        Returns:
            A dictionary with the full state, including the AES key and IV.
        """
        data: dict[str, object] = self.model_dump(mode=mode)
        data["aes_key"] = self.aes_key.get_secret_value()
        data["iv"] = self.iv.get_secret_value()
        return data

    def to_json(self, *, indent: int | None = None) -> str:
        """Export the state as JSON with the secrets included.

        Args:
            indent: Number of spaces to indent nested values; ``None`` for compact output.

        Returns:
            JSON text with the full state, including the AES key and IV.
        """
        data = self.to_dict(mode="json")
        if indent is None:
            return json.dumps(data, separators=(",", ":"))
        return json.dumps(data, indent=indent)

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Restore the state from a dictionary exported by ``to_dict()``.

        Args:
            state: Mapping produced by ``to_dict()``.

        Returns:
            The restored state.
        """
        return cls.model_validate(state)

    @classmethod
    def from_json(cls, state: str | bytes | bytearray) -> Self:
        """Restore the state from JSON exported by ``to_json()``.

        Args:
            state: JSON text produced by ``to_json()``.

        Returns:
            The restored state.
        """
        return cls.model_validate_json(state)


### Public API ###


class InvoicesFilter(KSeFBaseModel):
    """Filters accepted by invoice metadata query and export operations.

    Datetimes are stored as UTC-aware values. Inputs with an explicit offset keep
    their instant. Naive inputs are interpreted as Europe/Warsaw local time;
    ambiguous or nonexistent daylight-saving times require an explicit offset.
    """

    # role
    role: Literal["buyer", "seller", "third_subject", "authorized_subject"]
    """Role of the authenticated subject on the invoices to match."""

    # dates
    date_type: Literal["issue_date", "invoicing_date", "permanent_storage"]
    """Which date ``date_from`` and ``date_to`` apply to: issue date, invoicing date or permanent-storage date."""
    date_from: datetime
    """Start of the date range (inclusive). Naive values are read as Europe/Warsaw local time."""
    date_to: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """End of the date range. Defaults to the current UTC time."""
    restrict_to_permanent_storage_hwm_date: bool | None = None
    """Limit results to the permanent-storage high-water mark so repeated queries stay consistent."""

    # currency and amounts
    currency_codes: list[CurrencyCodes] | None = None
    """Match invoices in any of these currencies."""
    amount_type: Literal["brutto", "netto", "vat"] | None = None
    """Which amount ``amount_min`` and ``amount_max`` apply to: gross (``brutto``), net (``netto``) or ``vat``."""
    amount_min: float | None = None
    """Minimum amount, in the currency of the invoice."""
    amount_max: float | None = None
    """Maximum amount, in the currency of the invoice."""

    # identification
    seller_nip: str | None = None
    """Match invoices from this seller NIP."""
    buyer_nip: str | None = None
    """Match invoices to this buyer NIP."""
    buyer_vat_ue: str | None = None
    """Match invoices to this buyer EU VAT identifier."""
    buyer_other_id: str | None = None
    """Match invoices to this buyer identifier of another kind."""
    invoice_number: str | None = None
    """Match this seller invoice number."""
    ksef_number: str | None = None
    """Match this KSeF number."""

    # data
    invoice_schema: FormSchema | None = None
    """Match invoices issued in this schema."""
    invoice_types: list[KsefInvoiceTypes] | None = None
    """Match any of these invoice types."""
    has_attachment: bool | None = None
    """Match only invoices with (``True``) or without (``False``) an attachment."""

    # others
    invoicing_mode: InvoicingMode | None = None
    """Match only online or offline invoices."""
    is_self_invoicing: bool | None = None
    """Match only self-invoiced invoices (``True``) or exclude them (``False``)."""

    @field_validator("invoicing_mode", mode="before")
    @classmethod
    def _normalize_invoicing_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_invoicing_mode(value)
        return value

    @field_validator("date_from", "date_to", mode="after")
    @classmethod
    def _normalize_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is not None and value.utcoffset() is not None:
            return value.astimezone(timezone.utc)

        normalized_candidates: list[datetime] = []
        for fold in (0, 1):
            local_candidate = value.replace(tzinfo=_WARSAW_TIMEZONE, fold=fold)
            normalized = local_candidate.astimezone(timezone.utc)
            round_trip = normalized.astimezone(_WARSAW_TIMEZONE).replace(tzinfo=None)
            if round_trip == value and normalized not in normalized_candidates:
                normalized_candidates.append(normalized)

        if not normalized_candidates:
            raise ValueError(
                f"{value.isoformat()} does not exist in Europe/Warsaw local time; "
                "provide an explicit UTC offset."
            )
        if len(normalized_candidates) > 1:
            raise ValueError(
                f"{value.isoformat()} is ambiguous in Europe/Warsaw local time; "
                "provide an explicit UTC offset."
            )
        return normalized_candidates[0]

    @classmethod
    def for_buyer(
        cls,
        *,
        date_from: datetime | str,
        date_to: datetime | str | None = None,
        date_type: Literal[
            "issue_date", "invoicing_date", "permanent_storage"
        ] = "issue_date",
        restrict_to_permanent_storage_hwm_date: bool | None = None,
        currency_codes: list[CurrencyCodes] | None = None,
        amount_type: Literal["brutto", "netto", "vat"] | None = None,
        amount_min: float | None = None,
        amount_max: float | None = None,
        seller_nip: str | None = None,
        buyer_nip: str | None = None,
        buyer_vat_ue: str | None = None,
        buyer_other_id: str | None = None,
        invoice_number: str | None = None,
        ksef_number: str | None = None,
        invoice_schema: FormSchema | None = None,
        invoice_types: list[KsefInvoiceTypes] | None = None,
        has_attachment: bool | None = None,
        invoicing_mode: InvoicingMode | None = None,
        is_self_invoicing: bool | None = None,
    ) -> Self:
        """Build a filter for invoices where the authenticated subject is the buyer.

        Args:
            date_from: Start of the date range. Naive values are read as Europe/Warsaw local time.
            date_to: End of the date range; defaults to the current UTC time.
            date_type: Which date the range applies to: issue date, invoicing date or permanent-storage date.
            restrict_to_permanent_storage_hwm_date: Limit results to the permanent-storage high-water mark so repeated queries stay consistent.
            currency_codes: Match invoices in any of these currencies.
            amount_type: Which amount ``amount_min`` and ``amount_max`` apply to: gross (``brutto``), net (``netto``) or ``vat``.
            amount_min: Minimum amount.
            amount_max: Maximum amount.
            seller_nip: Match invoices from this seller NIP.
            buyer_nip: Match invoices to this buyer NIP.
            buyer_vat_ue: Match invoices to this buyer EU VAT identifier.
            buyer_other_id: Match invoices to this buyer identifier of another kind.
            invoice_number: Match this seller invoice number.
            ksef_number: Match this KSeF number.
            invoice_schema: Match invoices issued in this schema.
            invoice_types: Match any of these invoice types.
            has_attachment: Match only invoices with or without an attachment.
            invoicing_mode: Match only online or offline invoices.
            is_self_invoicing: Match only self-invoiced invoices, or exclude them.

        Returns:
            A filter with ``role="buyer"``.

        Example:
            ```python
            from ksef2.models import InvoicesFilter

            filters = InvoicesFilter.for_buyer(date_from="2026-01-01T00:00:00+01:00")
            ```
        """
        effective_date_to = (
            date_to if date_to is not None else datetime.now(timezone.utc)
        )
        return cls.model_validate(
            {
                "role": "buyer",
                "date_type": date_type,
                "date_from": date_from,
                "date_to": effective_date_to,
                "restrict_to_permanent_storage_hwm_date": (
                    restrict_to_permanent_storage_hwm_date
                ),
                "currency_codes": currency_codes,
                "amount_type": amount_type,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "seller_nip": seller_nip,
                "buyer_nip": buyer_nip,
                "buyer_vat_ue": buyer_vat_ue,
                "buyer_other_id": buyer_other_id,
                "invoice_number": invoice_number,
                "ksef_number": ksef_number,
                "invoice_schema": invoice_schema,
                "invoice_types": invoice_types,
                "has_attachment": has_attachment,
                "invoicing_mode": invoicing_mode,
                "is_self_invoicing": is_self_invoicing,
            }
        )

    @classmethod
    def for_seller(
        cls,
        *,
        date_from: datetime | str,
        date_to: datetime | str | None = None,
        date_type: Literal[
            "issue_date", "invoicing_date", "permanent_storage"
        ] = "issue_date",
        restrict_to_permanent_storage_hwm_date: bool | None = None,
        currency_codes: list[CurrencyCodes] | None = None,
        amount_type: Literal["brutto", "netto", "vat"] | None = None,
        amount_min: float | None = None,
        amount_max: float | None = None,
        seller_nip: str | None = None,
        buyer_nip: str | None = None,
        buyer_vat_ue: str | None = None,
        buyer_other_id: str | None = None,
        invoice_number: str | None = None,
        ksef_number: str | None = None,
        invoice_schema: FormSchema | None = None,
        invoice_types: list[KsefInvoiceTypes] | None = None,
        has_attachment: bool | None = None,
        invoicing_mode: InvoicingMode | None = None,
        is_self_invoicing: bool | None = None,
    ) -> Self:
        """Build a filter for invoices where the authenticated subject is the seller.

        Args:
            date_from: Start of the date range. Naive values are read as Europe/Warsaw local time.
            date_to: End of the date range; defaults to the current UTC time.
            date_type: Which date the range applies to: issue date, invoicing date or permanent-storage date.
            restrict_to_permanent_storage_hwm_date: Limit results to the permanent-storage high-water mark so repeated queries stay consistent.
            currency_codes: Match invoices in any of these currencies.
            amount_type: Which amount ``amount_min`` and ``amount_max`` apply to: gross (``brutto``), net (``netto``) or ``vat``.
            amount_min: Minimum amount.
            amount_max: Maximum amount.
            seller_nip: Match invoices from this seller NIP.
            buyer_nip: Match invoices to this buyer NIP.
            buyer_vat_ue: Match invoices to this buyer EU VAT identifier.
            buyer_other_id: Match invoices to this buyer identifier of another kind.
            invoice_number: Match this seller invoice number.
            ksef_number: Match this KSeF number.
            invoice_schema: Match invoices issued in this schema.
            invoice_types: Match any of these invoice types.
            has_attachment: Match only invoices with or without an attachment.
            invoicing_mode: Match only online or offline invoices.
            is_self_invoicing: Match only self-invoiced invoices, or exclude them.

        Returns:
            A filter with ``role="seller"``.

        Example:
            ```python
            from ksef2.models import InvoicesFilter

            filters = InvoicesFilter.for_seller(date_from="2026-01-01T00:00:00+01:00")
            ```
        """
        effective_date_to = (
            date_to if date_to is not None else datetime.now(timezone.utc)
        )
        return cls.model_validate(
            {
                "role": "seller",
                "date_type": date_type,
                "date_from": date_from,
                "date_to": effective_date_to,
                "restrict_to_permanent_storage_hwm_date": (
                    restrict_to_permanent_storage_hwm_date
                ),
                "currency_codes": currency_codes,
                "amount_type": amount_type,
                "amount_min": amount_min,
                "amount_max": amount_max,
                "seller_nip": seller_nip,
                "buyer_nip": buyer_nip,
                "buyer_vat_ue": buyer_vat_ue,
                "buyer_other_id": buyer_other_id,
                "invoice_number": invoice_number,
                "ksef_number": ksef_number,
                "invoice_schema": invoice_schema,
                "invoice_types": invoice_types,
                "has_attachment": has_attachment,
                "invoicing_mode": invoicing_mode,
                "is_self_invoicing": is_self_invoicing,
            }
        )

    @model_validator(mode="after")
    def _validate_filter_shape(self) -> Self:
        if (
            self.amount_min is not None or self.amount_max is not None
        ) and self.amount_type is None:
            raise ValueError(
                "amount_type must be specified when amount_min or amount_max is used."
            )

        if (
            self.amount_min is not None
            and self.amount_max is not None
            and self.amount_min > self.amount_max
        ):
            raise ValueError("amount_min must be less than or equal to amount_max.")

        buyer_identifiers = [
            field_name
            for field_name in ("buyer_nip", "buyer_vat_ue", "buyer_other_id")
            if getattr(self, field_name)
        ]
        if len(buyer_identifiers) > 1:
            joined = ", ".join(buyer_identifiers)
            raise ValueError(f"Only one buyer identifier can be specified: {joined}.")

        if self.date_from > self.date_to:
            raise ValueError("date_from must be less than or equal to date_to.")

        return self


class ExportInvoicesPayload(KSeFBaseModel):
    """Payload used to schedule an encrypted invoice export."""

    filter: InvoicesFilter
    """Filter selecting the invoices to export."""
    encrypted_symmetric_key: str
    """AES key encrypted with the KSeF public key, Base64-encoded."""
    initialization_vector: str
    """AES initialization vector, Base64-encoded."""
    public_key_id: str | None = None
    """Identifier of the KSeF public key used for encryption; ``None`` to use the default."""
    only_metadata: bool = False
    """Export only invoice metadata instead of full invoice XML."""
    compression_type: CompressionType | None = None
    """Compression applied to the package; ``None`` for the server default."""

    @field_validator("compression_type", mode="before")
    @classmethod
    def _normalize_compression_type(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return normalize_compression_type(value)
        return value


class SendInvoicePayload(KSeFBaseModel):
    """Plain and encrypted bytes for one invoice submitted to an online session."""

    xml_bytes: bytes
    """Plain invoice XML bytes."""
    encrypted_bytes: bytes
    """Invoice XML encrypted with the session key."""
