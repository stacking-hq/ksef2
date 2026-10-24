"""Shared invoice filter for workflow tests."""

from datetime import UTC, datetime

from ksef2._domain.models.invoices import InvoicesFilter


def filters() -> InvoicesFilter:
    return InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime(2026, 1, 1, tzinfo=UTC),
        date_to=datetime(2026, 2, 1, tzinfo=UTC),
    )
