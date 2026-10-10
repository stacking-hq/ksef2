"""Unit tests for the invoice request mapper's enum and validation branches."""

from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import BaseModel

from ksef2._domain.models import invoices as domain_invoices
from ksef2._domain.models.session import FormSchema
from ksef2._infra.mappers.invoices import requests as requests_mapper
from ksef2._infra.mappers.invoices.requests import to_spec
from ksef2._infra.schema.api import spec


def filter_for(role: str, **overrides: Any) -> domain_invoices.InvoicesFilter:
    """Build a seller-role filter, bypassing validation so odd values can be probed.

    ``InvoicesFilter`` declares every enum as a ``Literal``, so the mapper's
    unknown-value branches are only reachable with an unchecked instance.
    """
    values: dict[str, Any] = {
        "role": role,
        "date_type": "issue_date",
        "date_from": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "date_to": datetime(2026, 1, 31, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return domain_invoices.InvoicesFilter.model_construct(**values)


def seller_filter(**overrides: Any) -> domain_invoices.InvoicesFilter:
    values: dict[str, Any] = {
        "date_from": "2026-01-01T00:00:00",
        "date_to": "2026-01-31T00:00:00",
    }
    values.update(overrides)
    return domain_invoices.InvoicesFilter.for_seller(**values)


def mapped_filter(request: domain_invoices.InvoicesFilter) -> spec.InvoiceQueryFilters:
    output = to_spec(request)
    assert isinstance(output, spec.InvoiceQueryFilters)
    return output


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("seller", spec.InvoiceQuerySubjectType.Subject1),
        ("buyer", spec.InvoiceQuerySubjectType.Subject2),
        ("third_subject", spec.InvoiceQuerySubjectType.Subject3),
        ("authorized_subject", spec.InvoiceQuerySubjectType.SubjectAuthorized),
    ],
)
def test_subject_type_covers_every_role(role: str, expected: object) -> None:
    assert mapped_filter(filter_for(role)).subjectType == expected


def test_unknown_subject_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown invoice subject type: 'auditor'"):
        _ = mapped_filter(filter_for("auditor"))


def test_date_type_covers_every_variant() -> None:
    mapped = {
        date_type: mapped_filter(filter_for("seller", date_type=date_type)).dateRange
        for date_type in ("issue_date", "invoicing_date", "permanent_storage")
    }

    assert mapped["issue_date"].dateType == spec.InvoiceQueryDateType.Issue
    assert mapped["invoicing_date"].dateType == spec.InvoiceQueryDateType.Invoicing
    assert (
        mapped["permanent_storage"].dateType
        == spec.InvoiceQueryDateType.PermanentStorage
    )


def test_unknown_date_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown invoice date type: 'received_date'"):
        _ = mapped_filter(filter_for("seller", date_type="received_date"))


def test_permanent_storage_flag_only_maps_for_that_date_type() -> None:
    storage = mapped_filter(
        filter_for(
            "seller",
            date_type="permanent_storage",
            restrict_to_permanent_storage_hwm_date=True,
        )
    )
    issue = mapped_filter(
        filter_for(
            "seller",
            date_type="issue_date",
            restrict_to_permanent_storage_hwm_date=True,
        )
    )

    assert storage.dateRange.restrictToPermanentStorageHwmDate is True
    assert issue.dateRange.restrictToPermanentStorageHwmDate is None


def test_date_range_is_required() -> None:
    with pytest.raises(ValueError, match="Date range must be specified"):
        _ = mapped_filter(filter_for("seller", date_to=None))


@pytest.mark.parametrize(
    ("field", "expected_type"),
    [
        ("buyer_nip", spec.BuyerIdentifierType.Nip),
        ("buyer_vat_ue", spec.BuyerIdentifierType.VatUe),
        ("buyer_other_id", spec.BuyerIdentifierType.Other),
    ],
)
def test_buyer_identifier_uses_the_first_populated_field(
    field: str, expected_type: object
) -> None:
    output = mapped_filter(
        filter_for("seller", **{field: "PL1234567890"})
    ).buyerIdentifier

    assert output is not None
    assert output.type == expected_type
    assert output.value == "PL1234567890"


def test_buyer_identifier_precedence_and_absence() -> None:
    both = mapped_filter(
        filter_for("seller", buyer_nip="5252525252", buyer_vat_ue="DE811937334")
    )
    assert both.buyerIdentifier is not None
    assert both.buyerIdentifier.type == spec.BuyerIdentifierType.Nip

    assert mapped_filter(filter_for("seller", buyer_nip="")).buyerIdentifier is None
    assert mapped_filter(filter_for("seller")).buyerIdentifier is None


def test_unknown_buyer_identifier_field_is_rejected() -> None:
    with pytest.raises(
        ValueError, match="Unknown buyer identifier field: 'buyer_peppol_id'"
    ):
        _ = requests_mapper._map_buyer_identifier_type("buyer_peppol_id")


@pytest.mark.parametrize(
    ("amount_type", "expected"),
    [
        ("brutto", spec.AmountType.Brutto),
        ("netto", spec.AmountType.Netto),
        ("vat", spec.AmountType.Vat),
    ],
)
def test_amount_type_covers_every_variant(amount_type: str, expected: object) -> None:
    amount = mapped_filter(
        filter_for("seller", amount_type=amount_type, amount_min=10.0, amount_max=200.0)
    ).amount

    assert amount is not None
    assert amount.type == expected
    assert amount.from_ == 10.0
    assert amount.to == 200.0


def test_amount_bounds_without_a_type_are_rejected() -> None:
    # ``InvoicesFilter`` rejects this combination itself, so the mapper's own guard
    # is only reachable with an instance that skipped validation.
    with pytest.raises(
        ValueError, match="amount_type must be specified when amount range is used"
    ):
        _ = mapped_filter(filter_for("seller", amount_min=10.0))


def test_amount_type_without_bounds_is_ignored() -> None:
    assert mapped_filter(filter_for("seller", amount_type="netto")).amount is None


def test_unknown_amount_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown invoice amount type: 'marza'"):
        _ = mapped_filter(filter_for("seller", amount_type="marza", amount_min=10.0))


def test_currency_codes_are_mapped_to_spec_members() -> None:
    output = mapped_filter(filter_for("seller", currency_codes=["EUR", "USD"]))

    assert output.currencyCodes == [spec.CurrencyCode.EUR, spec.CurrencyCode.USD]


def test_empty_currency_code_list_is_dropped() -> None:
    assert mapped_filter(filter_for("seller", currency_codes=[])).currencyCodes is None


def test_invalid_currency_code_is_rejected_with_the_offending_value() -> None:
    with pytest.raises(ValueError, match="Invalid currency code: 'ZZZ'") as exc_info:
        _ = mapped_filter(filter_for("seller", currency_codes=["EUR", "ZZZ"]))

    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("invoice_type", "expected"),
    [
        ("vat", spec.InvoiceType.Vat),
        ("zal", spec.InvoiceType.Zal),
        ("kor", spec.InvoiceType.Kor),
        ("roz", spec.InvoiceType.Roz),
        ("upr", spec.InvoiceType.Upr),
        ("kor_zal", spec.InvoiceType.KorZal),
        ("kor_roz", spec.InvoiceType.KorRoz),
        ("vat_pef", spec.InvoiceType.VatPef),
        ("vat_pef_sp", spec.InvoiceType.VatPefSp),
        ("kor_pef", spec.InvoiceType.KorPef),
        ("vat_rr", spec.InvoiceType.VatRr),
        ("kor_vat_rr", spec.InvoiceType.KorVatRr),
    ],
)
def test_every_invoice_type_has_a_spec_counterpart(
    invoice_type: str, expected: object
) -> None:
    output = mapped_filter(filter_for("seller", invoice_types=[invoice_type]))

    assert output.invoiceTypes == [expected]


def test_invoice_type_list_keeps_its_order() -> None:
    output = mapped_filter(filter_for("seller", invoice_types=["kor", "vat"]))

    assert output.invoiceTypes == [spec.InvoiceType.Kor, spec.InvoiceType.Vat]


def test_empty_invoice_type_list_is_dropped() -> None:
    assert mapped_filter(filter_for("seller", invoice_types=[])).invoiceTypes is None


def test_unknown_invoice_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid invoice type: 'proforma'"):
        _ = mapped_filter(filter_for("seller", invoice_types=["proforma"]))


@pytest.mark.parametrize(
    ("invoicing_mode", "expected"),
    [
        ("online", spec.InvoicingMode.Online),
        ("offline", spec.InvoicingMode.Offline),
        (None, None),
    ],
)
def test_invoicing_mode_covers_every_variant(
    invoicing_mode: str | None, expected: object
) -> None:
    output = mapped_filter(filter_for("seller", invoicing_mode=invoicing_mode))

    assert output.invoicingMode == expected


def test_unknown_invoicing_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown invoicing mode: 'semi_online'"):
        _ = mapped_filter(filter_for("seller", invoicing_mode="semi_online"))


@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        (FormSchema.FA2, spec.InvoiceQueryFormType.FA),
        (FormSchema.FA3, spec.InvoiceQueryFormType.FA),
        (FormSchema.FA_RR1, spec.InvoiceQueryFormType.FA_RR),
        (FormSchema.PEF3, spec.InvoiceQueryFormType.PEF),
        (FormSchema.PEF_KOR3, spec.InvoiceQueryFormType.PEF),
        (None, None),
    ],
)
def test_form_schema_covers_every_variant(schema: Any, expected: Any) -> None:
    output = mapped_filter(filter_for("seller", invoice_schema=schema))

    assert output.formType == expected


def test_unknown_form_schema_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown invoice schema:"):
        _ = mapped_filter(filter_for("seller", invoice_schema="FA (4)"))


def test_pass_through_filter_fields() -> None:
    output = mapped_filter(
        filter_for(
            "seller",
            ksef_number="5252525252-20260115-ABCDEF-ABCDEF-9A",
            invoice_number="FV/2026/01/0015",
            seller_nip="5252525252",
            has_attachment=True,
            is_self_invoicing=False,
        )
    )

    assert output.ksefNumber == "5252525252-20260115-ABCDEF-ABCDEF-9A"
    assert output.invoiceNumber == "FV/2026/01/0015"
    assert output.sellerNip == "5252525252"
    assert output.hasAttachment is True
    assert output.isSelfInvoicing is False


def test_export_payload_maps_encryption_filter_and_compression() -> None:
    payload = domain_invoices.ExportInvoicesPayload(
        filter=seller_filter(),
        encrypted_symmetric_key="Q0lwaGVyVGV4dEtleQ==",
        initialization_vector="aXZWYWx1ZTEyMzQ=",
        public_key_id="key-1",
        only_metadata=True,
        compression_type="zip",
    )

    output = to_spec(payload)

    assert isinstance(output, spec.InvoiceExportRequest)
    assert output.encryption == spec.EncryptionInfo(
        encryptedSymmetricKey="Q0lwaGVyVGV4dEtleQ==",
        initializationVector="aXZWYWx1ZTEyMzQ=",
        publicKeyId="key-1",
    )
    assert output.onlyMetadata is True
    assert isinstance(output.filters, spec.InvoiceQueryFilters)
    assert output.compressionType == spec.CompressionType.Zip


def test_export_payload_without_compression_or_public_key() -> None:
    payload = domain_invoices.ExportInvoicesPayload(
        filter=seller_filter(),
        encrypted_symmetric_key="a2V5",
        initialization_vector="aXY",
    )

    output = to_spec(payload)

    assert isinstance(output, spec.InvoiceExportRequest)
    assert output.compressionType is None
    assert output.onlyMetadata is False
    assert output.encryption.publicKeyId is None


def test_send_payload_hashes_and_encodes_both_bodies() -> None:
    import base64
    import hashlib

    xml = b"<Faktura/>"
    encrypted = b"\x00\x01\x02enc"

    output = to_spec(
        domain_invoices.SendInvoicePayload(xml_bytes=xml, encrypted_bytes=encrypted)
    )

    assert isinstance(output, spec.SendInvoiceRequest)
    assert output.invoiceHash == base64.b64encode(hashlib.sha256(xml).digest()).decode()
    assert output.invoiceSize == len(xml)
    assert (
        output.encryptedInvoiceHash
        == base64.b64encode(hashlib.sha256(encrypted).digest()).decode()
    )
    assert output.encryptedInvoiceSize == len(encrypted)
    assert output.encryptedInvoiceContent == base64.b64encode(encrypted).decode()


def test_payloads_reach_the_mapper_through_the_package_export() -> None:
    class UnmappedPayload(BaseModel):
        kind: str = "unknown"

    with pytest.raises(NotImplementedError, match="UnmappedPayload"):
        _ = requests_mapper._to_spec(UnmappedPayload())
