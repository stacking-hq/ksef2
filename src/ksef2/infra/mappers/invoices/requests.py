"""Mappings from invoice domain models to generated API schema models."""

import base64
from functools import singledispatch
from typing import overload

from pydantic import BaseModel

from ksef2.core.crypto import sha256_b64
from ksef2.domain.models import invoices
from ksef2.infra.mappers.helpers import to_aware_datetime
from ksef2.infra.schema.api import spec


def _map_subject_type(value: str) -> spec.InvoiceQuerySubjectType:
    match value:
        case "seller":
            return spec.InvoiceQuerySubjectType.Subject1
        case "buyer":
            return spec.InvoiceQuerySubjectType.Subject2
        case "third_subject":
            return spec.InvoiceQuerySubjectType.Subject3
        case "authorized_subject":
            return spec.InvoiceQuerySubjectType.SubjectAuthorized
        case _:
            raise ValueError(f"Unknown invoice subject type: {value!r}")


def _map_buyer_identifier_type(
    field_name: str,
) -> spec.BuyerIdentifierType:
    match field_name:
        case "buyer_nip":
            return spec.BuyerIdentifierType.Nip
        case "buyer_vat_ue":
            return spec.BuyerIdentifierType.VatUe
        case "buyer_other_id":
            return spec.BuyerIdentifierType.Other
        case _:
            raise ValueError(f"Unknown buyer identifier field: {field_name!r}")


def _map_date_type(value: str) -> spec.InvoiceQueryDateType:
    match value:
        case "issue_date":
            return spec.InvoiceQueryDateType.Issue
        case "invoicing_date":
            return spec.InvoiceQueryDateType.Invoicing
        case "permanent_storage":
            return spec.InvoiceQueryDateType.PermanentStorage
        case _:
            raise ValueError(f"Unknown invoice date type: {value!r}")


def _map_amount_type(value: str) -> spec.AmountType:
    match value:
        case "brutto":
            return spec.AmountType.Brutto
        case "netto":
            return spec.AmountType.Netto
        case "vat":
            return spec.AmountType.Vat
        case _:
            raise ValueError(f"Unknown invoice amount type: {value!r}")


def _map_invoicing_mode(
    value: invoices.InvoicingMode | None,
) -> spec.InvoicingMode | None:
    match value:
        case "online":
            return spec.InvoicingMode.Online
        case "offline":
            return spec.InvoicingMode.Offline
        case None:
            return None
        case _:
            raise ValueError(f"Unknown invoicing mode: {value!r}")


def _map_form_type(
    value: invoices.FormSchema | None,
) -> spec.InvoiceQueryFormType | None:
    match value:
        case invoices.FormSchema.FA2 | invoices.FormSchema.FA3:
            return spec.InvoiceQueryFormType.FA
        case invoices.FormSchema.FA_RR1:
            return spec.InvoiceQueryFormType.FA_RR
        case invoices.FormSchema.PEF3 | invoices.FormSchema.PEF_KOR3:
            return spec.InvoiceQueryFormType.PEF
        case None:
            return None
        case _:
            raise ValueError(f"Unknown invoice schema: {value!r}")


def _map_buyer_identifier(
    request: invoices.InvoicesFilter,
) -> spec.InvoiceQueryBuyerIdentifier | None:
    for attr_name in ("buyer_nip", "buyer_vat_ue", "buyer_other_id"):
        identifier_value: str | None = getattr(request, attr_name, None)
        if identifier_value:
            return spec.InvoiceQueryBuyerIdentifier(
                type=_map_buyer_identifier_type(attr_name),
                value=identifier_value,
            )
    return None


def _map_date_range(
    request: invoices.InvoicesFilter,
) -> spec.InvoiceQueryDateRange:
    if not (request.date_from and request.date_to and request.date_type):
        raise ValueError("Date range must be specified")

    return spec.InvoiceQueryDateRange(
        dateType=_map_date_type(request.date_type),
        **{"from": to_aware_datetime(request.date_from)},
        to=to_aware_datetime(request.date_to),
        restrictToPermanentStorageHwmDate=(
            request.restrict_to_permanent_storage_hwm_date
            if request.date_type == "permanent_storage"
            else None
        ),
    )


def _map_amount(
    request: invoices.InvoicesFilter,
) -> spec.InvoiceQueryAmount | None:
    if request.amount_min is None and request.amount_max is None:
        return None

    return spec.InvoiceQueryAmount(
        type=_map_amount_type(request.amount_type),
        **{"from": request.amount_min},
        to=request.amount_max,
    )


def _map_currency_codes(
    request: invoices.InvoicesFilter,
) -> list[spec.CurrencyCode] | None:
    if not request.currency_codes:
        return None
    currency_codes: list[spec.CurrencyCode] = []
    for currency_code in request.currency_codes:
        try:
            currency_codes.append(spec.CurrencyCode(currency_code))
        except ValueError as exc:
            raise ValueError(f"Invalid currency code: {currency_code!r}") from exc

    return currency_codes


def _map_invoice_types(
    request: invoices.InvoicesFilter,
) -> list[spec.InvoiceType] | None:
    if not request.invoice_types:
        return None

    spec_codes: list[spec.InvoiceType] = []
    for invoice_type in request.invoice_types:
        match invoice_type:
            case "vat":
                spec_codes.append(spec.InvoiceType.Vat)
            case "zal":
                spec_codes.append(spec.InvoiceType.Zal)
            case "kor":
                spec_codes.append(spec.InvoiceType.Kor)
            case "roz":
                spec_codes.append(spec.InvoiceType.Roz)
            case "upr":
                spec_codes.append(spec.InvoiceType.Upr)
            case "kor_zal":
                spec_codes.append(spec.InvoiceType.KorZal)
            case "kor_roz":
                spec_codes.append(spec.InvoiceType.KorRoz)
            case "vat_pef":
                spec_codes.append(spec.InvoiceType.VatPef)
            case "vat_pef_sp":
                spec_codes.append(spec.InvoiceType.VatPefSp)
            case "kor_pef":
                spec_codes.append(spec.InvoiceType.KorPef)
            case "vat_rr":
                spec_codes.append(spec.InvoiceType.VatRr)
            case "kor_vat_rr":
                spec_codes.append(spec.InvoiceType.KorVatRr)
            case _:
                raise ValueError(f"Invalid invoice type: {invoice_type!r}")

    return spec_codes


@overload
def to_spec(request: invoices.InvoicesFilter) -> spec.InvoiceQueryFilters: ...


@overload
def to_spec(request: invoices.ExportInvoicesPayload) -> spec.InvoiceExportRequest: ...


@overload
def to_spec(request: invoices.SendInvoicePayload) -> spec.SendInvoiceRequest: ...


def to_spec(
    request: BaseModel,
) -> object:
    """Convert an invoice domain model into the schema payload expected by KSeF."""
    return _to_spec(request)


@singledispatch
def _to_spec(request: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(request).__name__}. "
        f"Register one with @_to_spec.register"
    )


@_to_spec.register
def _(request: invoices.InvoicesFilter) -> spec.InvoiceQueryFilters:
    return spec.InvoiceQueryFilters(
        subjectType=_map_subject_type(request.role),
        dateRange=_map_date_range(request),
        ksefNumber=request.ksef_number,
        invoiceNumber=request.invoice_number,
        amount=_map_amount(request),
        sellerNip=request.seller_nip,
        buyerIdentifier=_map_buyer_identifier(request),
        currencyCodes=_map_currency_codes(request),
        invoicingMode=_map_invoicing_mode(request.invoicing_mode),
        isSelfInvoicing=request.is_self_invoicing,
        formType=_map_form_type(request.invoice_schema),
        invoiceTypes=_map_invoice_types(request),
        hasAttachment=request.has_attachment,
    )


@_to_spec.register
def _(request: invoices.ExportInvoicesPayload) -> spec.InvoiceExportRequest:
    return spec.InvoiceExportRequest(
        encryption=spec.EncryptionInfo(
            encryptedSymmetricKey=request.encrypted_symmetric_key,
            initializationVector=request.initialization_vector,
            publicKeyId=request.public_key_id,
        ),
        onlyMetadata=request.only_metadata,
        filters=to_spec(request.filter),
    )


@_to_spec.register
def _(request: invoices.SendInvoicePayload) -> spec.SendInvoiceRequest:
    return spec.SendInvoiceRequest(
        invoiceHash=sha256_b64(request.xml_bytes),
        invoiceSize=len(request.xml_bytes),
        encryptedInvoiceHash=sha256_b64(request.encrypted_bytes),
        encryptedInvoiceSize=len(request.encrypted_bytes),
        encryptedInvoiceContent=base64.b64encode(request.encrypted_bytes).decode(),
    )
