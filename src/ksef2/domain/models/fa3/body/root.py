"""Root FA(3) invoice body aggregate and computed summary totals."""

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from ksef2.domain.models import KSeFBaseModel
from ksef2.domain.models.fa3.body.description import AdditionalDescriptionEntry
from ksef2.domain.models.fa3.body.advance_payment import (
    AdvancePaymentInvoiceContext,
)
from ksef2.domain.models.fa3.body.annotations import InvoiceAnnotationsContext
from ksef2.domain.models.fa3.body.correction import (
    CorrectionInvoiceContext,
)
from ksef2.domain.models.fa3.body.order import InvoiceOrder, InvoiceOrderLine
from ksef2.domain.models.fa3.body.payment import InvoicePayment
from ksef2.domain.models.fa3.body.row import InvoiceRow
from ksef2.domain.models.fa3.body.settlement import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)
from ksef2.domain.models.fa3.body.tax import SaleCategory, TaxRegime
from ksef2.domain.models.fa3.body.transaction import TransactionConditions


# Helper to round to 2 decimal places (standard Polish accounting rounding)
def round_pln(value: Decimal) -> Decimal:
    """Round a monetary amount using standard PLN precision."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class InvoiceType(StrEnum):
    """Human-readable FA(3) invoice type labels."""

    VAT = "Faktura podstawowa"
    CORRECTING = "Faktura korygująca"
    ZAL = "Faktura dokumentująca otrzymanie zapłaty lub jej części przed dokonaniem czynności oraz faktura wystawiona w związku z art. 106f ust. 4 ustawy (faktura zaliczkowa)"
    ROZ = "Faktura wystawiona w związku z art. 106f ust. 3 ustawy"
    UPR = "Faktura, o której mowa w art. 106e ust. 5 pkt 3 ustawy"
    CORRECTING_ZAL = "Faktura korygująca fakturę dokumentującą otrzymanie zapłaty lub jej części przed dokonaniem czynności oraz fakturę wystawioną w związku z art. 106f ust. 4 ustawy (faktura korygująca fakturę zaliczkową)"
    CORRECTING_ROZ = (
        "Faktura korygująca fakturę wystawioną w związku z art. 106f ust. 3 ustawy"
    )


class InvoiceSummaryOverrides(KSeFBaseModel):
    """Imported FA(3) summary totals preserved when line-level data is incomplete."""

    base_rate_net_total: Decimal | None = None
    base_rate_vat_total: Decimal | None = None
    base_rate_vat_total_pln: Decimal | None = None
    first_reduced_rate_net_total: Decimal | None = None
    first_reduced_rate_vat_total: Decimal | None = None
    first_reduced_rate_vat_total_pln: Decimal | None = None
    second_reduced_rate_net_total: Decimal | None = None
    second_reduced_rate_vat_total: Decimal | None = None
    second_reduced_rate_vat_total_pln: Decimal | None = None
    taxi_flat_rate_net_total: Decimal | None = None
    taxi_flat_rate_vat_total: Decimal | None = None
    taxi_flat_rate_vat_total_pln: Decimal | None = None
    special_procedure_xii_net_total: Decimal | None = None
    special_procedure_xii_vat_total: Decimal | None = None
    zero_rate_domestic_total: Decimal | None = None
    zero_rate_wdt_total: Decimal | None = None
    zero_rate_export_total: Decimal | None = None
    exempt_total: Decimal | None = None
    out_of_territory_total: Decimal | None = None
    article_100_services_total: Decimal | None = None
    reverse_charge_total: Decimal | None = None
    margin_total: Decimal | None = None
    total_gross: Decimal | None = None

    @field_validator("*")
    @classmethod
    def round_optional_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return round_pln(value)


def get_placeholder_invoice_number() -> str:
    """Return a timestamped placeholder invoice number for draft invoices."""
    return f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"


class KsefInvoiceBody(KSeFBaseModel):
    """Main ``Fa`` body aggregate for an FA(3) invoice."""

    currency: str = Field(
        default="PLN",
        description="kod_waluty: Invoice currency code in ISO 4217 format.",
    )
    issue_date: date = Field(description="p_1: Invoice issue date.")
    issue_place: str | None = Field(
        None, description="p_1_m: Place where the invoice was issued."
    )
    invoice_number: str = Field(
        description="p_2: Sequential invoice number identifying the invoice.",
        default_factory=get_placeholder_invoice_number,
    )

    warehouse_documents: list[str] = Field(
        default_factory=list,
        description="wz: Warehouse issue document numbers linked to the invoice.",
    )

    date_of_supply: date | None = Field(
        default=None,
        description="p_6: Shared delivery/service completion date when it differs from issue date.",
    )
    period_start: date | None = Field(
        default=None,
        description="okres_fa_a: Start date of the accounting/service period.",
    )
    period_end: date | None = Field(
        default=None,
        description="okres_fa_b: End date of the accounting/service period.",
    )

    # Computed summary properties below map to P_13_1..P_13_11, P_14_1..P_14_5, and P_15.
    vat_currency_exchange_rate: Decimal | None = Field(
        default=None,
        gt=0,
        description="kurs_waluty_z: Exchange rate used to convert VAT amounts to PLN on foreign-currency invoices.",
    )
    annotations: InvoiceAnnotationsContext | None = Field(
        default=None,
        description="Annotation-specific data grouped from Fa/Adnotacje.",
    )
    invoice_type: InvoiceType = Field(
        default=InvoiceType.VAT, description="rodzaj_faktury: Type of invoice."
    )
    correction: CorrectionInvoiceContext | None = Field(
        default=None,
        description="Correction-specific data grouped from Fa correction fields.",
    )
    advance: AdvancePaymentInvoiceContext | None = Field(
        default=None,
        description="Advance-invoice-specific data grouped from Fa advance fields.",
    )
    fp_invoice: bool = Field(
        default=False,
        description="fp: Marks the invoice as the document referred to in art. 109 ust. 3d ustawy.",
    )
    related_party_transaction: bool = Field(
        default=False,
        description="tp: Marks related-party links between buyer and seller/service provider.",
    )
    additional_description: list[AdditionalDescriptionEntry] = Field(
        default_factory=list,
        description="dodatkowy_opis: Additional key/value invoice metadata entries.",
    )
    return_of_excise: bool | None = Field(
        default=None,
        description="zwrot_akcyzy: Flag indicating return of excise duty.",
    )
    rows: list[InvoiceRow] = Field(
        default_factory=list,
        description="fa_wiersz: Detailed invoice line items.",
    )
    settlement: InvoiceSettlement | None = Field(
        default=None,
        description="rozliczenie: Additional settlement data for the invoice.",
    )
    payment: InvoicePayment | None = Field(
        default=None,
        description="platnosc: Payment details for the invoice.",
    )
    transaction_conditions: TransactionConditions | None = Field(
        default=None,
        description="warunki_transakcji: Transaction conditions for the invoice.",
    )
    order: InvoiceOrder | None = Field(
        default=None,
        description="zamowienie: Order block used on advance invoices.",
    )
    summary_overrides: InvoiceSummaryOverrides | None = Field(
        default=None,
        description=(
            "Optional imported FA(3) summary totals used when the source schema does "
            "not provide enough line-level detail to recompute P_13/P_14/P_15 exactly."
        ),
    )

    # --- validation ---

    @model_validator(mode="after")
    def validate_dates(self) -> "KsefInvoiceBody":
        has_period_start = self.period_start is not None
        has_period_end = self.period_end is not None

        if has_period_start != has_period_end:
            raise ValueError("period_start and period_end must be provided together")

        if self.date_of_supply is not None and has_period_start:
            raise ValueError(
                "date_of_supply cannot be combined with period_start/period_end"
            )

        if (
            self.period_start
            and self.period_end
            and self.period_start > self.period_end
        ):
            raise ValueError("period_start cannot be later than period_end")
        self._validate_vat_currency_exchange_rate()
        self._validate_row_presence()
        self._validate_intent_specific_data()
        return self

    def _validate_vat_currency_exchange_rate(self) -> None:
        if self.vat_currency_exchange_rate is None:
            return

        if self.currency.upper() == "PLN":
            raise ValueError(
                "vat_currency_exchange_rate is only valid for non-PLN invoices"
            )

    def _validate_row_presence(self) -> None:
        if (
            self.invoice_type == InvoiceType.CORRECTING
            and not self.rows
            and self.order is None
        ):
            return
        if not self.rows and self.order is None:
            raise ValueError("At least one invoice line or order is required")

        if self.invoice_type == InvoiceType.ZAL:
            if self.rows:
                raise ValueError("Advance invoices use order instead of lines")
            if self.order is None:
                raise ValueError("Advance invoices require order data")
        elif self.invoice_type == InvoiceType.CORRECTING_ZAL:
            if self.order is None and not self.rows:
                raise ValueError("Advance invoices require order data or lines")
            if self.order is not None and self.rows:
                raise ValueError("Advance invoices cannot combine order and lines")
        elif self.order is not None:
            raise ValueError("order is only valid for advance invoices")
        elif not self.rows:
            raise ValueError("At least one invoice line is required")

    def _validate_intent_specific_data(self) -> None:
        correction = self.correction
        advance = self.advance

        corrected_invoices = correction.corrected_invoices if correction else []
        corrected_seller = correction.corrected_seller if correction else None
        corrected_buyers = correction.corrected_buyers if correction else []
        advance_invoice_references = (
            advance.advance_invoice_references if advance else []
        )
        has_correction_data = correction is not None and any(
            [
                correction.correction_reason is not None,
                correction.correction_effect_type is not None,
                bool(corrected_invoices),
                correction.corrected_invoice_period is not None,
                correction.corrected_invoice_number_override is not None,
                corrected_seller is not None,
                bool(corrected_buyers),
            ]
        )
        has_advance_data = advance is not None and any(
            [
                advance.amount_before_correction is not None,
                advance.currency_exchange_rate_before_correction is not None,
                bool(advance.advance_partial_payments),
                bool(advance_invoice_references),
            ]
        )

        if has_correction_data and self.invoice_type not in {
            InvoiceType.CORRECTING,
            InvoiceType.CORRECTING_ZAL,
            InvoiceType.CORRECTING_ROZ,
        }:
            raise ValueError("correction is only valid for correcting invoices")
        if has_advance_data and self.invoice_type not in {
            InvoiceType.ZAL,
            InvoiceType.ROZ,
            InvoiceType.CORRECTING_ZAL,
            InvoiceType.CORRECTING_ROZ,
        }:
            raise ValueError(
                "advance is only valid for advance and settlement invoices"
            )

        if self.invoice_type == InvoiceType.CORRECTING and not corrected_invoices:
            raise ValueError("Correcting invoices require corrected_invoices data")
        if self.invoice_type == InvoiceType.ROZ and not advance_invoice_references:
            raise ValueError(
                "Settlement invoices require at least one advance invoice reference"
            )
        if corrected_seller is not None or corrected_buyers:
            if self.invoice_type not in {
                InvoiceType.CORRECTING,
                InvoiceType.CORRECTING_ZAL,
                InvoiceType.CORRECTING_ROZ,
            }:
                raise ValueError(
                    "corrected_seller and corrected_buyers are only valid for correcting invoices"
                )
        margin_procedure = (
            self.annotations.margin_procedure if self.annotations else None
        )
        if margin_procedure is not None:
            if not self.rows:
                raise ValueError("Margin procedure requires invoice lines")

    @property
    def order_lines(self) -> list[InvoiceOrderLine]:
        """Return order lines or an empty list when no order block exists."""
        if self.order is None:
            return []
        return list(self.order.order_lines)

    def _financial_rows(self):
        if self.invoice_type == InvoiceType.ZAL:
            return self.order_lines
        if self.invoice_type == InvoiceType.CORRECTING_ZAL:
            return self.order_lines if self.order is not None else list(self.rows)
        return list(self.rows)

    def _summary_override(self, field_name: str) -> Decimal | None:
        if self.summary_overrides is None:
            return None
        return getattr(self.summary_overrides, field_name)

    def _summary_value(self, field_name: str, computed: Decimal) -> Decimal:
        if self.summary_overrides is not None:
            override = self._summary_override(field_name)
            if override is not None:
                return override
            return Decimal("0.00")
        return computed

    def _summary_optional_value(
        self, field_name: str, computed: Decimal | None
    ) -> Decimal | None:
        override = self._summary_override(field_name)
        if override is not None:
            return override
        return computed

    def _correction_multiplier(self, line: InvoiceRow | InvoiceOrderLine) -> Decimal:
        if self.invoice_type not in {
            InvoiceType.CORRECTING,
            InvoiceType.CORRECTING_ZAL,
            InvoiceType.CORRECTING_ROZ,
        }:
            return Decimal("1")
        if getattr(line, "before_correction", False):
            return Decimal("-1")
        return Decimal("1")

    def _sum_net(
        self, predicate: Callable[[InvoiceRow | InvoiceOrderLine], bool]
    ) -> Decimal:
        sum_net = Decimal("0.00")
        for line in self._financial_rows():
            if predicate(line) and line.net_amount is not None:
                sum_net += line.net_amount * self._correction_multiplier(line)

        return sum_net

    def _sum_vat(
        self, predicate: Callable[[InvoiceRow | InvoiceOrderLine], bool]
    ) -> Decimal:
        sum_vat = Decimal("0.00")
        for line in self._financial_rows():
            if predicate(line) and line.vat_amount is not None:
                sum_vat += line.vat_amount * self._correction_multiplier(line)
        return sum_vat

    @property
    def total_net(
        self,
    ) -> Annotated[Decimal, "Helper: total net value across all invoice lines"]:
        """Return the signed net total across financial invoice rows."""
        sum_net = Decimal("0.00")
        for line in self._financial_rows():
            if line.net_amount is None:
                continue
            sum_net += line.net_amount * self._correction_multiplier(line)
        return sum_net

    @property
    def total_vat(
        self,
    ) -> Annotated[Decimal, "Helper: total VAT amount across all invoice lines"]:
        """Return the signed VAT total across financial invoice rows."""
        sum_vat = Decimal("0.00")
        for line in self._financial_rows():
            if line.vat_amount is None:
                continue
            sum_vat += line.vat_amount * self._correction_multiplier(line)
        return sum_vat

    @property
    def total_gross(
        self,
    ) -> Annotated[
        Decimal, "p_15: Kwota należności ogółem / gross amount of the invoice"
    ]:
        """Return the gross invoice total mapped to ``P_15``."""
        return self._summary_value("total_gross", self.total_net + self.total_vat)

    @property
    def base_rate_net_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_1: Net total for the basic VAT rate bucket (23%/22%)"
    ]:
        """Return the net total for the basic VAT-rate bucket."""
        return self._summary_value(
            "base_rate_net_total",
            self._sum_net(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category
                    in {SaleCategory.RATE_23, SaleCategory.RATE_22}
                )
            ),
        )

    @property
    def base_rate_vat_total(
        self,
    ) -> Annotated[
        Decimal, "p_14_1: VAT total for the basic VAT rate bucket (23%/22%)"
    ]:
        """Return the VAT total for the basic VAT-rate bucket."""
        return self._summary_value(
            "base_rate_vat_total",
            self._sum_vat(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category
                    in {SaleCategory.RATE_23, SaleCategory.RATE_22}
                )
            ),
        )

    @property
    def first_reduced_rate_net_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_2: Net total for the first reduced VAT rate bucket (8%/7%)"
    ]:
        """Return the net total for the first reduced VAT-rate bucket."""
        return self._summary_value(
            "first_reduced_rate_net_total",
            self._sum_net(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category in {SaleCategory.RATE_8, SaleCategory.RATE_7}
                )
            ),
        )

    @property
    def first_reduced_rate_vat_total(
        self,
    ) -> Annotated[
        Decimal, "p_14_2: VAT total for the first reduced VAT rate bucket (8%/7%)"
    ]:
        """Return the VAT total for the first reduced VAT-rate bucket."""
        return self._summary_value(
            "first_reduced_rate_vat_total",
            self._sum_vat(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category in {SaleCategory.RATE_8, SaleCategory.RATE_7}
                )
            ),
        )

    @property
    def second_reduced_rate_net_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_3: Net total for the second reduced VAT rate bucket (5%)"
    ]:
        """Return the net total for the second reduced VAT-rate bucket."""
        return self._summary_value(
            "second_reduced_rate_net_total",
            self._sum_net(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category == SaleCategory.RATE_5
                )
            ),
        )

    @property
    def second_reduced_rate_vat_total(
        self,
    ) -> Annotated[
        Decimal, "p_14_3: VAT total for the second reduced VAT rate bucket (5%)"
    ]:
        """Return the VAT total for the second reduced VAT-rate bucket."""
        return self._summary_value(
            "second_reduced_rate_vat_total",
            self._sum_vat(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category == SaleCategory.RATE_5
                )
            ),
        )

    @property
    def taxi_flat_rate_net_total(
        self,
    ) -> Annotated[Decimal, "p_13_4: Net total for the taxi flat-rate bucket"]:
        """Return the net total for taxi flat-rate lines."""
        return self._summary_value(
            "taxi_flat_rate_net_total",
            self._sum_net(lambda line: line.tax_regime == TaxRegime.TAXI_FLAT_RATE),
        )

    @property
    def taxi_flat_rate_vat_total(
        self,
    ) -> Annotated[Decimal, "p_14_4: VAT total for the taxi flat-rate bucket"]:
        """Return the VAT total for taxi flat-rate lines."""
        return self._summary_value(
            "taxi_flat_rate_vat_total",
            self._sum_vat(lambda line: line.tax_regime == TaxRegime.TAXI_FLAT_RATE),
        )

    def _vat_total_in_pln_for(
        self, predicate: Callable[[InvoiceRow | InvoiceOrderLine], bool], value: Decimal
    ) -> Decimal | None:
        if self.currency.upper() == "PLN":
            return None
        if self.vat_currency_exchange_rate is not None:
            return round_pln(value * self.vat_currency_exchange_rate)
        total = Decimal("0.00")
        for line in self._financial_rows():
            if (
                predicate(line)
                and line.vat_amount is not None
                and line.currency_exchange_rate is not None
            ):
                total += line.vat_amount * line.currency_exchange_rate
        if total == Decimal("0.00"):
            return None
        return round_pln(total)

    @property
    def base_rate_vat_total_pln(
        self,
    ) -> Annotated[
        Decimal | None,
        "p_14_1_w: VAT total for the basic rate bucket converted to PLN.",
    ]:
        """Return basic-rate VAT converted to PLN when required."""
        return self._summary_optional_value(
            "base_rate_vat_total_pln",
            self._vat_total_in_pln_for(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category
                    in {SaleCategory.RATE_23, SaleCategory.RATE_22}
                ),
                self.base_rate_vat_total,
            ),
        )

    @property
    def first_reduced_rate_vat_total_pln(
        self,
    ) -> Annotated[
        Decimal | None,
        "p_14_2_w: VAT total for the first reduced rate bucket converted to PLN.",
    ]:
        """Return first-reduced-rate VAT converted to PLN when required."""
        return self._summary_optional_value(
            "first_reduced_rate_vat_total_pln",
            self._vat_total_in_pln_for(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category in {SaleCategory.RATE_8, SaleCategory.RATE_7}
                ),
                self.first_reduced_rate_vat_total,
            ),
        )

    @property
    def second_reduced_rate_vat_total_pln(
        self,
    ) -> Annotated[
        Decimal | None,
        "p_14_3_w: VAT total for the second reduced rate bucket converted to PLN.",
    ]:
        """Return second-reduced-rate VAT converted to PLN when required."""
        return self._summary_optional_value(
            "second_reduced_rate_vat_total_pln",
            self._vat_total_in_pln_for(
                lambda line: (
                    line.tax_regime == TaxRegime.STANDARD
                    and line.sale_category == SaleCategory.RATE_5
                ),
                self.second_reduced_rate_vat_total,
            ),
        )

    @property
    def taxi_flat_rate_vat_total_pln(
        self,
    ) -> Annotated[
        Decimal | None,
        "p_14_4_w: VAT total for the taxi flat-rate bucket converted to PLN.",
    ]:
        """Return taxi flat-rate VAT converted to PLN when required."""
        return self._summary_optional_value(
            "taxi_flat_rate_vat_total_pln",
            self._vat_total_in_pln_for(
                lambda line: line.tax_regime == TaxRegime.TAXI_FLAT_RATE,
                self.taxi_flat_rate_vat_total,
            ),
        )

    @property
    def special_procedure_xii_net_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_5: Net total for the Title XII special procedure bucket"
    ]:
        """Return the net total for Title XII special-procedure lines."""
        return self._summary_value(
            "special_procedure_xii_net_total",
            self._sum_net(lambda line: line.tax_regime == TaxRegime.SPECIAL_XII),
        )

    @property
    def special_procedure_xii_vat_total(
        self,
    ) -> Annotated[
        Decimal, "p_14_5: VAT total for the Title XII special procedure bucket"
    ]:
        """Return the VAT total for Title XII special-procedure lines."""
        return self._summary_value(
            "special_procedure_xii_vat_total",
            self._sum_vat(lambda line: line.tax_regime == TaxRegime.SPECIAL_XII),
        )

    @property
    def zero_rate_domestic_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_6_1: Net total for domestic 0% sales excluding WDT/export"
    ]:
        """Return the net total for domestic zero-rate sales."""
        return self._summary_value(
            "zero_rate_domestic_total",
            self._sum_net(
                lambda line: line.sale_category == SaleCategory.ZERO_DOMESTIC
            ),
        )

    @property
    def zero_rate_wdt_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_6_2: Net total for intra-EU supply of goods (WDT) at 0%"
    ]:
        """Return the net total for zero-rate intra-EU supply of goods."""
        return self._summary_value(
            "zero_rate_wdt_total",
            self._sum_net(lambda line: line.sale_category == SaleCategory.ZERO_WDT),
        )

    @property
    def zero_rate_export_total(
        self,
    ) -> Annotated[Decimal, "p_13_6_3: Net total for export sales at 0%"]:
        """Return the net total for zero-rate export sales."""
        return self._summary_value(
            "zero_rate_export_total",
            self._sum_net(lambda line: line.sale_category == SaleCategory.ZERO_EXPORT),
        )

    @property
    def exempt_total(
        self,
    ) -> Annotated[Decimal, "p_13_7: Net total for VAT-exempt sales"]:
        """Return the net total for VAT-exempt sales."""
        return self._summary_value(
            "exempt_total",
            self._sum_net(lambda line: line.sale_category == SaleCategory.EXEMPT),
        )

    @property
    def out_of_territory_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_8: Net total for out-of-scope foreign sales outside Poland"
    ]:
        """Return the net total for sales outside Polish VAT territory."""
        return self._summary_value(
            "out_of_territory_total",
            self._sum_net(
                lambda line: (
                    line.sale_category == SaleCategory.OUT_OF_SCOPE_OUTSIDE_TERRITORY
                )
            ),
        )

    @property
    def article_100_services_total(
        self,
    ) -> Annotated[
        Decimal, "p_13_9: Net total for services reported under Article 100(1)(4)"
    ]:
        """Return the net total for Article 100 service sales."""
        return self._summary_value(
            "article_100_services_total",
            self._sum_net(
                lambda line: line.sale_category == SaleCategory.OUT_OF_SCOPE_ARTICLE_100
            ),
        )

    @property
    def reverse_charge_total(
        self,
    ) -> Annotated[Decimal, "p_13_10: Net total for reverse-charge sales"]:
        """Return the net total for reverse-charge sales."""
        return self._summary_value(
            "reverse_charge_total",
            self._sum_net(
                lambda line: line.sale_category == SaleCategory.REVERSE_CHARGE
            ),
        )

    @property
    def margin_total(
        self,
    ) -> Annotated[
        Decimal,
        "p_13_11: Total value of sales in the margin scheme under art. 119 and 120",
    ]:
        """Return the total for margin-scheme sales."""
        return self._summary_value(
            "margin_total",
            self._sum_net(lambda line: line.tax_regime == TaxRegime.MARGIN),
        )

    @property
    def settlement_charges_total(self) -> Decimal:
        """Return the total settlement charges applied to the invoice."""
        if self.settlement is None:
            return Decimal("0.00")

        if self.settlement.charges_total is not None:
            return self.settlement.charges_total

        return sum(
            (charge.amount for charge in self.settlement_charges),
            start=Decimal("0.00"),
        )

    @property
    def settlement_deductions_total(self) -> Decimal:
        """Return the total settlement deductions applied to the invoice."""
        explicit_deductions_total = Decimal("0.00")
        if self.settlement is not None:
            if self.settlement.deductions_total is not None:
                explicit_deductions_total = self.settlement.deductions_total
            else:
                explicit_deductions_total = sum(
                    (deduction.amount for deduction in self.settlement_deductions),
                    start=Decimal("0.00"),
                )

        referenced_deductions = [
            reference.deduction_amount
            for reference in (
                self.advance.advance_invoice_references if self.advance else []
            )
            if reference.deduction_amount is not None
        ]
        return sum(
            [explicit_deductions_total] + referenced_deductions,
            start=Decimal("0.00"),
        )

    @property
    def settlement_charges(self) -> list[SettlementCharge]:
        """Return settlement charges or an empty list when absent."""
        if self.settlement is None:
            return []
        return list(self.settlement.charges)

    @property
    def settlement_deductions(self) -> list[SettlementDeduction]:
        """Return settlement deductions or an empty list when absent."""
        if self.settlement is None:
            return []
        return list(self.settlement.deductions)

    @property
    def settlement_balance(self) -> Decimal:
        """Return the final amount due after settlement charges and deductions."""
        if self.settlement is not None:
            if self.settlement.amount_due is not None:
                return self.settlement.amount_due
            if self.settlement.amount_to_settle is not None:
                return -self.settlement.amount_to_settle

        return (
            self.total_gross
            + self.settlement_charges_total
            - self.settlement_deductions_total
        )
