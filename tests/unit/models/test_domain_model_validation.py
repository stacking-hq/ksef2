from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from ksef2._domain.models.batch import BatchFileInfo, BatchFilePart
from ksef2._domain.models.invoices import InvoicesFilter


def _batch_part(
    *,
    ordinal_number: int = 1,
    file_size: int = 1,
) -> BatchFilePart:
    return BatchFilePart(
        ordinal_number=ordinal_number,
        file_size=file_size,
        file_hash="hash",
    )


def _invoice_filter(**overrides: object) -> InvoicesFilter:
    data: dict[str, object] = {
        "role": "seller",
        "date_type": "issue_date",
        "date_from": "2026-01-01T00:00:00",
        "date_to": "2026-01-02T00:00:00",
    }
    data.update(overrides)
    return InvoicesFilter.model_validate(data)


def test_batch_file_info_rejects_file_larger_than_5gb() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 5000000000"):
        BatchFileInfo(
            file_size=5_000_000_001,
            file_hash="hash",
            parts=[_batch_part()],
        )


def test_batch_file_info_rejects_more_than_50_parts() -> None:
    parts = [
        _batch_part(ordinal_number=ordinal_number) for ordinal_number in range(1, 52)
    ]

    with pytest.raises(ValidationError, match="at most 50"):
        BatchFileInfo(file_size=1, file_hash="hash", parts=parts)


def test_batch_file_part_rejects_negative_size() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        _batch_part(file_size=-1)


def test_batch_file_part_rejects_encrypted_size_above_represented_limit() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 100000016"):
        _batch_part(file_size=100_000_017)


def test_batch_file_part_rejects_zero_ordinal_number() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        _batch_part(ordinal_number=0)


def test_invoices_filter_rejects_amount_min_greater_than_amount_max() -> None:
    with pytest.raises(
        ValidationError,
        match="amount_min must be less than or equal to amount_max",
    ):
        _invoice_filter(amount_type="brutto", amount_min=100.0, amount_max=10.0)


def test_invoices_filter_allows_missing_amount_type_without_amount_range() -> None:
    filters = _invoice_filter()

    assert filters.amount_type is None


def test_invoices_filter_requires_amount_type_with_amount_range() -> None:
    with pytest.raises(
        ValidationError,
        match="amount_type must be specified when amount_min or amount_max is used",
    ):
        _invoice_filter(amount_min=10.0)


def test_invoices_filter_rejects_multiple_buyer_identifiers() -> None:
    with pytest.raises(
        ValidationError,
        match="Only one buyer identifier can be specified: buyer_nip, buyer_vat_ue",
    ):
        _invoice_filter(buyer_nip="1234567890", buyer_vat_ue="PL1234567890")


def test_invoices_filter_buyer_constructor_sets_role_and_identifier() -> None:
    filters = InvoicesFilter.for_buyer(
        date_from="2026-01-01T00:00:00",
        date_to="2026-01-02T00:00:00",
        buyer_nip="1234567890",
        invoice_types=["vat"],
    )

    assert filters.role == "buyer"
    assert filters.date_type == "issue_date"
    assert filters.buyer_nip == "1234567890"
    assert filters.invoice_types == ["vat"]


def test_invoices_filter_seller_constructor_sets_role_and_counterparty() -> None:
    filters = InvoicesFilter.for_seller(
        date_from="2026-01-01T00:00:00",
        date_to="2026-01-02T00:00:00",
        seller_nip="1234567890",
        buyer_other_id="client-1",
    )

    assert filters.role == "seller"
    assert filters.seller_nip == "1234567890"
    assert filters.buyer_other_id == "client-1"


def test_invoices_filter_rejects_reversed_parseable_date_strings() -> None:
    with pytest.raises(
        ValidationError,
        match="date_from must be less than or equal to date_to",
    ):
        _invoice_filter(
            date_from="2026-02-01T00:00:00",
            date_to="2026-01-01T00:00:00",
        )


def test_invoices_filter_rejects_reversed_datetime_values() -> None:
    with pytest.raises(
        ValidationError,
        match="date_from must be less than or equal to date_to",
    ):
        _invoice_filter(
            date_from=datetime(2026, 2, 1),
            date_to=datetime(2026, 1, 1),
        )


def test_invoices_filter_normalizes_naive_warsaw_dates_to_utc() -> None:
    filters = _invoice_filter(
        date_from="2026-01-01T00:00:00",
        date_to="2026-01-02T00:00:00",
    )

    assert filters.date_from == datetime(2025, 12, 31, 23, tzinfo=timezone.utc)
    assert filters.date_to == datetime(2026, 1, 1, 23, tzinfo=timezone.utc)


def test_invoices_filter_normalizes_explicit_offsets_to_utc() -> None:
    filters = _invoice_filter(
        date_from="2026-01-01T01:00:00+01:00",
        date_to="2026-01-01T03:00:00+02:00",
    )

    assert filters.date_from == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert filters.date_to == datetime(2026, 1, 1, 1, tzinfo=timezone.utc)


def test_invoices_filter_accepts_equal_instants_with_different_offsets() -> None:
    filters = _invoice_filter(
        date_from="2026-01-01T00:00:00+00:00",
        date_to="2026-01-01T01:00:00+01:00",
    )

    assert filters.date_from == filters.date_to


def test_invoices_filter_rejects_reversed_mixed_timezone_range() -> None:
    with pytest.raises(
        ValidationError,
        match="date_from must be less than or equal to date_to",
    ):
        _invoice_filter(
            date_from="2026-01-02T00:00:00+00:00",
            date_to="2026-01-01T00:00:00",
        )


def test_invoices_filter_rejects_invalid_datetime_string() -> None:
    with pytest.raises(ValidationError, match="Input should be a valid datetime"):
        _invoice_filter(date_from="not-a-datetime")


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("2026-03-29T02:30:00", "does not exist in Europe/Warsaw"),
        ("2026-10-25T02:30:00", "is ambiguous in Europe/Warsaw"),
    ],
)
def test_invoices_filter_requires_offset_for_dst_transition_times(
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        _invoice_filter(date_from=value)


def test_invoices_filter_accepts_explicit_offset_during_dst_overlap() -> None:
    filters = _invoice_filter(
        date_from="2026-10-25T02:30:00+02:00",
        date_to="2026-10-25T02:30:00+01:00",
    )

    assert filters.date_from == datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)
    assert filters.date_to == datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc)
