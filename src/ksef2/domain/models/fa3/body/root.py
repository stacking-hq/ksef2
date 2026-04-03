from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Annotated

from pydantic import Field, model_validator

from ksef2.domain.models import KSeFBaseModel
from ksef2.domain.models.fa3.body.advance_payment import PartialAdvancePayment
from ksef2.domain.models.fa3.body.order import InvoiceOrder, InvoiceOrderLine
from ksef2.domain.models.fa3.body.payment import InvoicePayment
from ksef2.domain.models.fa3.body.row import Money, InvoiceRow, SaleCategory, VatRate
from ksef2.domain.models.fa3.body.settlement import (
    InvoiceSettlement,
    SettlementCharge,
    SettlementDeduction,
)
from ksef2.domain.models.fa3.body.transaction import TransactionConditions
from ksef2.domain.models.fa3.drafts import (
    AdvanceInvoiceReference,
    CorrectedInvoiceReference,
    MarginProcedure,
)
from ksef2.domain.models.fa3.party import (
    CorrectedBuyerEntity,
    CorrectedSellerEntity,
)


# Helper to round to 2 decimal places (standard Polish accounting rounding)
def round_pln(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class InvoiceType(StrEnum):
    VAT = "Faktura podstawowa"
    CORRECTING = "Faktura korygująca"
    ZAL = "Faktura dokumentująca otrzymanie zapłaty lub jej części przed dokonaniem czynności oraz faktura wystawiona w związku z art. 106f ust. 4 ustawy (faktura zaliczkowa)"
    ROZ = "Faktura wystawiona w związku z art. 106f ust. 3 ustawy"
    UPR = "Faktura, o której mowa w art. 106e ust. 5 pkt 3 ustawy"
    CORRECTING_ZAL = "Faktura korygująca fakturę dokumentującą otrzymanie zapłaty lub jej części przed dokonaniem czynności oraz fakturę wystawioną w związku z art. 106f ust. 4 ustawy (faktura korygująca fakturę zaliczkową)"
    CORRECTING_ROZ = (
        "Faktura korygująca fakturę wystawioną w związku z art. 106f ust. 3 ustawy"
    )


def get_placeholder_invoice_number() -> str:
    return f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"


class KsefInvoiceBody(KSeFBaseModel):
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
    invoice_type: InvoiceType = Field(
        default=InvoiceType.VAT, description="rodzaj_faktury: Type of invoice."
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

    return_of_excise: bool | None = Field(
        default=None,
        description="zwrot_akcyzy: Flag indicating return of excise duty.",
    )

    correction_reason: str | None = Field(
        default=None, description="przyczyna_korekty: Optional correction reason."
    )
    corrected_invoices: list[CorrectedInvoiceReference] = Field(
        default_factory=list,
        description="dane_fa_korygowanej: References to corrected invoices.",
    )
    corrected_seller: CorrectedSellerEntity | None = Field(
        default=None,
        description="podmiot1_k: Seller data from the corrected invoice.",
    )
    corrected_buyers: list[CorrectedBuyerEntity] = Field(
        default_factory=list,
        description="podmiot2_k: Buyer data from the corrected invoice.",
    )

    margin_procedure: MarginProcedure | None = Field(
        default=None,
        description="adnotacje/pmarzy: Margin procedure flag.",
    )
    advance_partial_payments: list[PartialAdvancePayment] = Field(
        default_factory=list,
        description="zaliczka_czesciowa: Partial advance payments.",
    )
    # --- aggregated fields ---
    advance_invoice_references: list[AdvanceInvoiceReference] = Field(
        default_factory=list,
        description="faktura_zaliczkowa: Referenced advance invoices on settlements.",
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
        self._validate_row_presence()
        self._validate_intent_specific_data()
        return self

    def _validate_row_presence(self) -> None:
        if not self.rows and self.order is None:
            raise ValueError("At least one invoice line or order is required")

        if self.invoice_type == InvoiceType.ZAL:
            if self.rows:
                raise ValueError("Advance invoices use order instead of lines")
            if self.order is None:
                raise ValueError("Advance invoices require order data")
        elif self.order is not None:
            raise ValueError("order is only valid for advance invoices")
        elif not self.rows:
            raise ValueError("At least one invoice line is required")

    def _validate_intent_specific_data(self) -> None:
        if self.invoice_type == InvoiceType.CORRECTING and not self.corrected_invoices:
            raise ValueError("Correcting invoices require corrected_invoices data")
        if self.invoice_type == InvoiceType.ROZ and not self.advance_invoice_references:
            raise ValueError(
                "Settlement invoices require at least one advance invoice reference"
            )
        if self.corrected_seller is not None or self.corrected_buyers:
            if self.invoice_type not in {
                InvoiceType.CORRECTING,
                InvoiceType.CORRECTING_ZAL,
                InvoiceType.CORRECTING_ROZ,
            }:
                raise ValueError(
                    "corrected_seller and corrected_buyers are only valid for correcting invoices"
                )
        if self.margin_procedure is not None:
            if not self.rows:
                raise ValueError("Margin procedure requires invoice lines")
            non_margin_lines = [
                line for line in self.rows if line.sale_category != SaleCategory.MARGIN
            ]
            if non_margin_lines:
                raise ValueError(
                    "Margin procedure can only be used with MARGIN sale_category lines"
                )

    @property
    def order_lines(self) -> list[InvoiceOrderLine]:
        if self.order is None:
            return []
        return list(self.order.order_lines)

    def _financial_rows(self) -> list[InvoiceRow | InvoiceOrderLine]:
        if self.invoice_type == InvoiceType.ZAL:
            return self.order_lines
        return list(self.rows)

    def _sum_net(
        self, predicate: Callable[[InvoiceRow | InvoiceOrderLine], bool]
    ) -> Money:
        sum_net = Decimal("0.00")
        for line in self._financial_rows():
            assert line.net_amount is not None, (
                "net_amount must be set for all invoice rows"
            )
            if predicate(line):
                sum_net += line.net_amount

        return sum_net

    def _sum_vat(
        self, predicate: Callable[[InvoiceRow | InvoiceOrderLine], bool]
    ) -> Money:
        sum_vat = Decimal("0.00")
        for line in self._financial_rows():
            assert line.vat_amount is not None, (
                "vat_amount must be set for all invoice rows"
            )
            if predicate(line):
                sum_vat += line.vat_amount
        return sum_vat

    @property
    def total_net(
        self,
    ) -> Annotated[Money, "Helper: total net value across all invoice lines"]:
        sum_net = Decimal("0.00")
        for line in self._financial_rows():
            assert line.net_amount is not None, (
                "net_amount must be set for all invoice rows"
            )
            sum_net += line.net_amount
        return sum_net

    @property
    def total_vat(
        self,
    ) -> Annotated[Money, "Helper: total VAT amount across all invoice lines"]:
        sum_vat = Decimal("0.00")
        for line in self._financial_rows():
            assert line.vat_amount is not None, (
                "vat_amount must be set for all invoice rows"
            )
            sum_vat += line.vat_amount
        return sum_vat

    @property
    def total_gross(
        self,
    ) -> Annotated[
        Money, "p_15: Kwota należności ogółem / gross amount of the invoice"
    ]:
        return self.total_net + self.total_vat

    @property
    def base_rate_net_total(
        self,
    ) -> Annotated[Money, "p_13_1: Net total for the basic VAT rate bucket (23%/22%)"]:
        return self._sum_net(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate in {VatRate.VAT_23, VatRate.VAT_22}
            )
        )

    @property
    def base_rate_vat_total(
        self,
    ) -> Annotated[Money, "p_14_1: VAT total for the basic VAT rate bucket (23%/22%)"]:
        return self._sum_vat(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate in {VatRate.VAT_23, VatRate.VAT_22}
            )
        )

    @property
    def first_reduced_rate_net_total(
        self,
    ) -> Annotated[
        Money, "p_13_2: Net total for the first reduced VAT rate bucket (8%/7%)"
    ]:
        return self._sum_net(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate in {VatRate.VAT_8, VatRate.VAT_7}
            )
        )

    @property
    def first_reduced_rate_vat_total(
        self,
    ) -> Annotated[
        Money, "p_14_2: VAT total for the first reduced VAT rate bucket (8%/7%)"
    ]:
        return self._sum_vat(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate in {VatRate.VAT_8, VatRate.VAT_7}
            )
        )

    @property
    def second_reduced_rate_net_total(
        self,
    ) -> Annotated[
        Money, "p_13_3: Net total for the second reduced VAT rate bucket (5%)"
    ]:
        return self._sum_net(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate == VatRate.VAT_5
            )
        )

    @property
    def second_reduced_rate_vat_total(
        self,
    ) -> Annotated[
        Money, "p_14_3: VAT total for the second reduced VAT rate bucket (5%)"
    ]:
        return self._sum_vat(
            lambda line: (
                line.sale_category == SaleCategory.STANDARD
                and line.vat_rate == VatRate.VAT_5
            )
        )

    @property
    def taxi_flat_rate_net_total(
        self,
    ) -> Annotated[Money, "p_13_4: Net total for the taxi flat-rate bucket"]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.TAXI_FLAT_RATE
        )

    @property
    def taxi_flat_rate_vat_total(
        self,
    ) -> Annotated[Money, "p_14_4: VAT total for the taxi flat-rate bucket"]:
        return self._sum_vat(
            lambda line: line.sale_category == SaleCategory.TAXI_FLAT_RATE
        )

    @property
    def special_procedure_xii_net_total(
        self,
    ) -> Annotated[
        Money, "p_13_5: Net total for the Title XII special procedure bucket"
    ]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.SPECIAL_XII
        )

    @property
    def special_procedure_xii_vat_total(
        self,
    ) -> Annotated[
        Money, "p_14_5: VAT total for the Title XII special procedure bucket"
    ]:
        return self._sum_vat(
            lambda line: line.sale_category == SaleCategory.SPECIAL_XII
        )

    @property
    def zero_rate_domestic_total(
        self,
    ) -> Annotated[
        Money, "p_13_6_1: Net total for domestic 0% sales excluding WDT/export"
    ]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.ZERO_DOMESTIC
        )

    @property
    def zero_rate_wdt_total(
        self,
    ) -> Annotated[
        Money, "p_13_6_2: Net total for intra-EU supply of goods (WDT) at 0%"
    ]:
        return self._sum_net(lambda line: line.sale_category == SaleCategory.ZERO_WDT)

    @property
    def zero_rate_export_total(
        self,
    ) -> Annotated[Money, "p_13_6_3: Net total for export sales at 0%"]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.ZERO_EXPORT
        )

    @property
    def exempt_total(
        self,
    ) -> Annotated[Money, "p_13_7: Net total for VAT-exempt sales"]:
        return self._sum_net(lambda line: line.sale_category == SaleCategory.EXEMPT)

    @property
    def out_of_territory_total(
        self,
    ) -> Annotated[
        Money, "p_13_8: Net total for out-of-scope foreign sales outside Poland"
    ]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.OUT_OF_TERRITORY
        )

    @property
    def article_100_services_total(
        self,
    ) -> Annotated[
        Money, "p_13_9: Net total for services reported under Article 100(1)(4)"
    ]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.ARTICLE_100
        )

    @property
    def reverse_charge_total(
        self,
    ) -> Annotated[Money, "p_13_10: Net total for reverse-charge sales"]:
        return self._sum_net(
            lambda line: line.sale_category == SaleCategory.REVERSE_CHARGE
        )

    @property
    def margin_total(
        self,
    ) -> Annotated[
        Money,
        "p_13_11: Total value of sales in the margin scheme under art. 119 and 120",
    ]:
        return self._sum_net(lambda line: line.sale_category == SaleCategory.MARGIN)

    @property
    def settlement_charges_total(self) -> Money:
        if self.settlement is None:
            return Decimal("0.00")

        if self.settlement.charges_total is not None:
            return self.settlement.charges_total

        return sum(
            (charge.amount for charge in self.settlement_charges),
            start=Decimal("0.00"),
        )

    @property
    def settlement_deductions_total(self) -> Money:
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
            for reference in self.advance_invoice_references
            if reference.deduction_amount is not None
        ]
        return sum(
            [explicit_deductions_total] + referenced_deductions,
            start=Decimal("0.00"),
        )

    @property
    def settlement_charges(self) -> list[SettlementCharge]:
        if self.settlement is None:
            return []
        return list(self.settlement.charges)

    @property
    def settlement_deductions(self) -> list[SettlementDeduction]:
        if self.settlement is None:
            return []
        return list(self.settlement.deductions)

    @property
    def settlement_balance(self) -> Money:
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
