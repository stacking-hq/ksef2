"""Mappings from generated invoice schema models to domain models."""

from functools import singledispatch
from typing import assert_never, overload

from pydantic import BaseModel

from ksef2._domain.models import invoices
from ksef2._infra.schema.api import spec


def _map_buyer_identifier_type(
    response: spec.BuyerIdentifierType,
) -> invoices.BuyerIdentifierType:
    match response:
        case spec.BuyerIdentifierType.Nip:
            return "nip"
        case spec.BuyerIdentifierType.VatUe:
            return "vat_ue"
        case spec.BuyerIdentifierType.Other:
            return "other"
        case spec.BuyerIdentifierType.None_:
            return "none"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_third_subject_identifier_type(
    response: spec.ThirdSubjectIdentifierType,
) -> invoices.ThirdSubjectIdentifierType:
    match response:
        case spec.ThirdSubjectIdentifierType.Nip:
            return "nip"
        case spec.ThirdSubjectIdentifierType.InternalId:
            return "internal_id"
        case spec.ThirdSubjectIdentifierType.VatUe:
            return "vat_ue"
        case spec.ThirdSubjectIdentifierType.Other:
            return "other"
        case spec.ThirdSubjectIdentifierType.None_:
            return "none"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_invoicing_mode(response: spec.InvoicingMode) -> invoices.InvoicingMode:
    match response:
        case spec.InvoicingMode.Online:
            return "online"
        case spec.InvoicingMode.Offline:
            return "offline"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


def _map_invoice_type(response: spec.InvoiceType) -> invoices.InvoiceType:
    match response:
        case spec.InvoiceType.Vat:
            return "vat"
        case spec.InvoiceType.Zal:
            return "zal"
        case spec.InvoiceType.Kor:
            return "kor"
        case spec.InvoiceType.Roz:
            return "roz"
        case spec.InvoiceType.Upr:
            return "upr"
        case spec.InvoiceType.KorZal:
            return "kor_zal"
        case spec.InvoiceType.KorRoz:
            return "kor_roz"
        case spec.InvoiceType.VatPef:
            return "vat_pef"
        case spec.InvoiceType.VatPefSp:
            return "vat_pef_sp"
        case spec.InvoiceType.KorPef:
            return "kor_pef"
        case spec.InvoiceType.VatRr:
            return "vat_rr"
        case spec.InvoiceType.KorVatRr:
            return "kor_vat_rr"
        case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(unreachable)


@overload
def from_spec(response: spec.SendInvoiceResponse) -> invoices.SendInvoiceResponse: ...


@overload
def from_spec(
    response: spec.QueryInvoicesMetadataResponse,
) -> invoices.QueryInvoicesMetadataResponse: ...


@overload
def from_spec(
    response: spec.ExportInvoicesResponse,
) -> invoices.ExportInvoicesResponse: ...


@overload
def from_spec(
    response: spec.InvoiceExportStatusResponse,
) -> invoices.InvoiceExportStatusResponse: ...


@overload
def from_spec(response: spec.InvoiceMetadata) -> invoices.InvoiceMetadata: ...


@overload
def from_spec(
    response: spec.InvoiceMetadataSeller,
) -> invoices.InvoiceMetadataSeller: ...


@overload
def from_spec(
    response: spec.InvoiceMetadataBuyerIdentifier,
) -> invoices.InvoiceMetadataBuyerIdentifier: ...


@overload
def from_spec(
    response: spec.InvoiceMetadataBuyer,
) -> invoices.InvoiceMetadataBuyer: ...


@overload
def from_spec(
    response: spec.InvoiceMetadataThirdSubject,
) -> invoices.InvoiceMetadataThirdSubject: ...


@overload
def from_spec(
    response: spec.InvoiceMetadataAuthorizedSubject,
) -> invoices.InvoiceMetadataAuthorizedSubject: ...


@overload
def from_spec(response: spec.InvoicePackagePart) -> invoices.PackagePart: ...


@overload
def from_spec(response: spec.InvoicePackage) -> invoices.InvoicePackage: ...


def from_spec(response: BaseModel) -> object:
    """Convert a generated invoice schema model into its domain counterpart."""
    return _from_spec(response)


@singledispatch
def _from_spec(response: BaseModel) -> object:
    raise NotImplementedError(
        f"No mapper registered for {type(response).__name__}. "
        f"Register one with @_from_spec.register"
    )


@_from_spec.register
def _(response: spec.SendInvoiceResponse) -> invoices.SendInvoiceResponse:
    return invoices.SendInvoiceResponse(reference_number=response.referenceNumber)


@_from_spec.register
def _(
    response: spec.QueryInvoicesMetadataResponse,
) -> invoices.QueryInvoicesMetadataResponse:
    return invoices.QueryInvoicesMetadataResponse(
        has_more=response.hasMore,
        is_truncated=response.isTruncated,
        permanent_storage_hwm_date=response.permanentStorageHwmDate,
        invoices=[from_spec(inv) for inv in response.invoices],
    )


@_from_spec.register
def _(response: spec.ExportInvoicesResponse) -> invoices.ExportInvoicesResponse:
    return invoices.ExportInvoicesResponse(
        reference_number=response.referenceNumber,
    )


@_from_spec.register
def _(
    response: spec.InvoiceExportStatusResponse,
) -> invoices.InvoiceExportStatusResponse:
    return invoices.InvoiceExportStatusResponse(
        status=invoices.ExportStatusInfo(
            code=response.status.code,
            description=response.status.description,
            details=response.status.details,
        ),
        completed_date=response.completedDate,
        package_expiration_date=response.packageExpirationDate,
        package=from_spec(response.package) if response.package is not None else None,
    )


@_from_spec.register
def _(response: spec.InvoiceMetadataSeller) -> invoices.InvoiceMetadataSeller:
    return invoices.InvoiceMetadataSeller(
        nip=response.nip,
        name=response.name,
    )


@_from_spec.register
def _(
    response: spec.InvoiceMetadataBuyerIdentifier,
) -> invoices.InvoiceMetadataBuyerIdentifier:
    return invoices.InvoiceMetadataBuyerIdentifier(
        type=_map_buyer_identifier_type(response.type),
        value=response.value,
    )


@_from_spec.register
def _(response: spec.InvoiceMetadataBuyer) -> invoices.InvoiceMetadataBuyer:
    return invoices.InvoiceMetadataBuyer(
        identifier=from_spec(response.identifier),
        name=response.name,
    )


@_from_spec.register
def _(
    response: spec.InvoiceMetadataThirdSubject,
) -> invoices.InvoiceMetadataThirdSubject:
    return invoices.InvoiceMetadataThirdSubject(
        identifier=invoices.InvoiceMetadataThirdSubjectIdentifier(
            type=_map_third_subject_identifier_type(response.identifier.type),
            value=response.identifier.value,
        ),
        name=response.name,
        role=response.role,
    )


@_from_spec.register
def _(
    response: spec.InvoiceMetadataAuthorizedSubject,
) -> invoices.InvoiceMetadataAuthorizedSubject:
    return invoices.InvoiceMetadataAuthorizedSubject(
        nip=response.nip,
        name=response.name,
        role=response.role,
    )


@_from_spec.register
def _(response: spec.InvoiceMetadata) -> invoices.InvoiceMetadata:
    third_subjects = (
        [from_spec(subject) for subject in response.thirdSubjects]
        if response.thirdSubjects is not None
        else None
    )

    return invoices.InvoiceMetadata(
        ksef_number=response.ksefNumber,
        invoice_number=response.invoiceNumber,
        issue_date=response.issueDate,
        invoicing_date=response.invoicingDate,
        acquisition_date=response.acquisitionDate,
        permanent_storage_date=response.permanentStorageDate,
        seller=from_spec(response.seller),
        buyer=from_spec(response.buyer),
        net_amount=response.netAmount,
        gross_amount=response.grossAmount,
        vat_amount=response.vatAmount,
        currency=response.currency,
        invoicing_mode=_map_invoicing_mode(response.invoicingMode),
        invoice_type=_map_invoice_type(response.invoiceType),
        form_code_system=response.formCode.systemCode,
        form_code_version=response.formCode.schemaVersion,
        form_code_value=response.formCode.value,
        is_self_invoicing=response.isSelfInvoicing,
        has_attachment=response.hasAttachment,
        invoice_hash=response.invoiceHash,
        hash_of_corrected_invoice=response.hashOfCorrectedInvoice,
        third_subjects=third_subjects,
        authorized_subject=(
            from_spec(response.authorizedSubject)
            if response.authorizedSubject is not None
            else None
        ),
    )


@_from_spec.register
def _(response: spec.InvoicePackagePart) -> invoices.PackagePart:
    return invoices.PackagePart(
        ordinal_number=response.ordinalNumber,
        part_name=response.partName,
        method=response.method,
        url=str(response.url),
        part_size=response.partSize,
        part_hash=response.partHash,
        encrypted_part_size=response.encryptedPartSize,
        encrypted_part_hash=response.encryptedPartHash,
        expiration_date=response.expirationDate,
    )


@_from_spec.register
def _(response: spec.InvoicePackage) -> invoices.InvoicePackage:
    return invoices.InvoicePackage(
        invoice_count=response.invoiceCount,
        size=response.size,
        parts=[from_spec(part) for part in response.parts],
        is_truncated=response.isTruncated,
        last_issue_date=response.lastIssueDate,
        last_invoicing_date=response.lastInvoicingDate,
        last_permanent_storage_date=response.lastPermanentStorageDate,
        permanent_storage_hwm_date=response.permanentStorageHwmDate,
    )
