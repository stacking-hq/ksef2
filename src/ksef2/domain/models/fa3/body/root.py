from collections.abc import Callable
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self, assert_never

from pydantic import Field, model_validator

from ksef2.domain.models import KSeFBaseModel
from ksef2.domain.models.fa3.body.payment import InvoicePayment
from ksef2.domain.models.fa3.drafts import (
    AdvanceInvoiceReference,
    AdvanceOrderLine,
    CorrectedInvoiceReference,
    MarginProcedure,
    SettlementCharge,
    SettlementDeduction,
)

from decimal import Decimal, ROUND_HALF_UP


# Helper to round to 2 decimal places (standard Polish accounting rounding)
def round_pln(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


Money = Decimal

GtuCode = Literal[
    "GTU_01",
    "GTU_02",
    "GTU_03",
    "GTU_04",
    "GTU_05",
    "GTU_06",
    "GTU_07",
    "GTU_08",
    "GTU_09",
    "GTU_10",
    "GTU_11",
    "GTU_12",
    "GTU_13",
]

InvoiceProcedure = Literal[
    "WSTO_EE",
    "IED",
    "TT_D",
    "I_42",
    "I_63",
    "B_SPV",
    "B_SPV_DOSTAWA",
    "B_MPV_PROWIZJA",
]


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


class VatRate(StrEnum):
    VAT_23 = "23"
    VAT_22 = "22"
    VAT_8 = "8"
    VAT_7 = "7"
    VAT_5 = "5"
    VAT_4 = "4"
    VAT_3 = "3"
    VAT_0 = "0"
    EXEMPT = "zw"
    NOT_SUBJECT = "np"
    REVERSE_CHARGE = "oo"


class SaleCategory(StrEnum):
    STANDARD = "standard"
    TAXI_FLAT_RATE = "taxi_flat_rate"
    SPECIAL_XII = "special_xii"
    ZERO_DOMESTIC = "zero_domestic"
    ZERO_WDT = "zero_wdt"
    ZERO_EXPORT = "zero_export"
    EXEMPT = "exempt"
    OUT_OF_TERRITORY = "out_of_territory"
    ARTICLE_100 = "article_100"
    REVERSE_CHARGE = "reverse_charge"
    MARGIN = "margin"


class InvoiceLine(KSeFBaseModel):
    name: str = Field(description="p_7: Name of good/service")
    supply_date: date | None = Field(default=None, description="p_6_a: Date of supply")
    unit_price_net: Money = Field(description="p_9_a: Net unit price")
    vat_rate: VatRate | None = Field(
        default=None,
        description="p_12: VAT rate / formal tax marker where applicable",
    )
    unit_of_measure: str = Field(default="szt", description="p_8_a: Unit of measure")
    quantity: Decimal = Field(description="p_8_b: Quantity")
    discount_amount: Money | None = Field(
        default=Decimal("0.00"), description="p_10: Discount amount"
    )

    # --- computed fields ---
    unit_price_gross: Money | None = Field(
        default=None, description="p_9_b: Price with VAT"
    )
    gross_amount: Money | None = Field(
        default=None, description="p_11_a: Gross value of the line"
    )
    net_amount: Money | None = Field(
        default=None, description="p_11: Net value of the line"
    )
    vat_amount: Money | None = Field(
        default=None, description="p_11_vat: VAT amount of the line"
    )

    @model_validator(mode="after")
    def compute_financial_field(self):
        if self.net_amount is None:
            base_net = self.unit_price_net * self.quantity
            self.net_amount = round_pln(base_net) - (
                self.discount_amount or Decimal("0.00")
            )

        if self.vat_amount is None:
            if self.vat_rate in {
                VatRate.VAT_23,
                VatRate.VAT_22,
                VatRate.VAT_8,
                VatRate.VAT_7,
                VatRate.VAT_5,
                VatRate.VAT_4,
            }:
                decimal_vat_rate = (
                    Decimal(self.vat_rate.value) / Decimal("100")
                    if self.vat_rate
                    else Decimal("0.00")
                )
                rate_decimal = decimal_vat_rate
                self.vat_amount = round_pln(self.net_amount * rate_decimal)
            else:
                # for VAT_0, EXEMPT (zw), NOT_SUBJECT (np), REVERSE_CHARGE (oo)
                self.vat_amount = Decimal("0.00")

        if self.gross_amount is None:
            self.gross_amount = round_pln(self.net_amount + self.vat_amount)

        _ = self.validate_tax_logic()

        return self

    vat_rate_xii: Decimal | None = Field(
        default=None, description="p_12_XII: VAT rate XII"
    )
    annex_15_marker: bool | None = Field(
        default=None, description="p_12_ZAL_15: Annex 15 marker"
    )

    sale_category: SaleCategory = Field(
        default=SaleCategory.STANDARD,
        description=(
            "Logical classification used to map the line into KSeF summary buckets "
            "(e.g. standard, WDT 0%, export 0%, exempt, reverse charge, margin)."
        ),
    )

    excise_amount: Money | None = Field(
        default=None, description="kwota_akcyzy: Excise amount"
    )
    unique_id: str | None = Field(default=None, description="uu_id: Unique ID")
    sku: str | None = Field(
        default=None, description="indeks: Internal SKU or additional description"
    )
    gtin: str | None = Field(default=None, description="gtin: Global Trade Item Number")
    pkwiu: str | None = Field(
        default=None, description="pkwi_u: Polish Goods Classification"
    )
    cn: str | None = Field(default=None, description="cn: Nomenclature Code")
    pkob: str | None = Field(
        default=None, description="pkob: Polish Construction Object Classification"
    )

    gtu_code: GtuCode | None = Field(default=None, description="gtu: GTU code")
    procedure: InvoiceProcedure | None = Field(
        default=None, description="procedura: Procedure code"
    )
    currency_exchange_rate: Decimal | None = Field(
        default=None, description="kurs_waluty: Currency exchange rate"
    )
    before_correction: bool = Field(
        default=False,
        description="stan_przed: Marks the row as representing state before correction",
    )

    def validate_tax_logic(self) -> Self:
        self._validate_quantity()
        self._validate_sale_category_rules()
        self._validate_gross_amount_consistency()
        return self

    def _validate_quantity(self) -> None:
        if self.quantity == 0:
            raise ValueError("quantity cannot be zero")

    def _validate_sale_category_rules(self) -> None:
        match self.sale_category:
            case SaleCategory.STANDARD:
                self._validate_standard_sale()
            case SaleCategory.TAXI_FLAT_RATE:
                self._validate_taxi_flat_rate()
            case SaleCategory.ZERO_DOMESTIC:
                self._validate_zero_domestic()
            case SaleCategory.ZERO_WDT:
                self._validate_zero_wdt()
            case SaleCategory.ZERO_EXPORT:
                self._validate_zero_export()
            case SaleCategory.EXEMPT:
                self._validate_exempt()
            case SaleCategory.OUT_OF_TERRITORY:
                self._validate_out_of_territory()
            case SaleCategory.ARTICLE_100:
                self._validate_article_100()
            case SaleCategory.REVERSE_CHARGE:
                self._validate_reverse_charge()
            case SaleCategory.MARGIN:
                self._validate_margin()
            case SaleCategory.SPECIAL_XII:
                self._validate_special_xii()
            case _ as unreachable:  # pyright: ignore[reportUnnecessaryComparison]
                assert_never(unreachable)

    def _validate_standard_sale(self) -> None:
        # Standard domestic taxable sale using ordinary VAT rate buckets.
        # This category maps to the classic KSeF summary fields such as p_13_1..p_13_3 and p_14_1..p_14_3.
        if self.vat_rate not in {
            VatRate.VAT_23,
            VatRate.VAT_22,
            VatRate.VAT_8,
            VatRate.VAT_7,
            VatRate.VAT_5,
        }:
            raise ValueError(
                "STANDARD sale_category requires vat_rate equal to 23, 22, 8, 7, or 5"
            )

    def _validate_taxi_flat_rate(self) -> None:
        # Taxi flat-rate sale is a special tax regime.
        # It should be represented only with the dedicated 4% bucket.
        if self.vat_rate != VatRate.VAT_4:
            raise ValueError("TAXI_FLAT_RATE requires vat_rate='4'")

    def _validate_zero_domestic(self) -> None:
        # Domestic 0% sale, excluding intra-EU supply and export.
        # This maps to p_13_6_1.
        if self.vat_rate != VatRate.VAT_0:
            raise ValueError("ZERO_DOMESTIC requires vat_rate='0'")

    def _validate_zero_wdt(self) -> None:
        # Intra-EU supply of goods taxed at 0%.
        # This maps to p_13_6_2.
        if self.vat_rate != VatRate.VAT_0:
            raise ValueError("ZERO_WDT requires vat_rate='0'")

    def _validate_zero_export(self) -> None:
        # Export sale taxed at 0%.
        # This maps to p_13_6_3.
        if self.vat_rate != VatRate.VAT_0:
            raise ValueError("ZERO_EXPORT requires vat_rate='0'")

    def _validate_exempt(self) -> None:
        # VAT-exempt sale.
        # This maps to p_13_7 and must not be treated as a taxable rate bucket.
        if self.vat_rate != VatRate.EXEMPT:
            raise ValueError("EXEMPT category requires vat_rate='zw'")

    def _validate_out_of_territory(self) -> None:
        # Sale outside the territory of Poland.
        # Usually represented as not subject to Polish VAT and maps to p_13_8.
        if self.vat_rate not in {VatRate.NOT_SUBJECT, None}:
            raise ValueError("OUT_OF_TERRITORY requires vat_rate='np' or None")

    def _validate_article_100(self) -> None:
        # Services reported under Article 100(1)(4).
        # This is a reporting-specific bucket and should be marked as not subject in Poland.
        if self.vat_rate not in {VatRate.NOT_SUBJECT, None}:
            raise ValueError("ARTICLE_100 requires vat_rate='np' or None")

    def _validate_reverse_charge(self) -> None:
        # Reverse-charge sale where the buyer accounts for VAT.
        # This maps to p_13_10 and should not use ordinary VAT sale buckets.
        if self.vat_rate not in {VatRate.REVERSE_CHARGE, None}:
            raise ValueError("REVERSE_CHARGE requires vat_rate='oo' or None")

    def _validate_margin(self) -> None:
        # Margin scheme sale under the dedicated margin procedure.
        # It maps to p_13_11 and must not be represented as a normal VAT rate bucket.
        if self.vat_rate in {
            VatRate.VAT_23,
            VatRate.VAT_22,
            VatRate.VAT_8,
            VatRate.VAT_7,
            VatRate.VAT_5,
            VatRate.VAT_4,
            VatRate.VAT_0,
        }:
            raise ValueError("MARGIN category should not use standard VAT rates")

    def _validate_special_xii(self) -> None:
        # Special Title XII procedure.
        # This category requires the dedicated vat_rate_xii field instead of ordinary VAT rate handling.
        if self.vat_rate_xii is None:
            raise ValueError("SPECIAL_XII requires vat_rate_xii")

    def _validate_gross_amount_consistency(self) -> None:
        # Gross amount, when provided, must equal net amount plus VAT amount.
        if self.gross_amount is not None:
            assert self.net_amount is not None and self.vat_amount is not None, (
                "net_amount and vat_amount must be set when gross_amount is provided"
            )
            expected_gross = self.net_amount + self.vat_amount
            if self.gross_amount != expected_gross:
                raise ValueError(
                    f"gross_amount must equal net_amount + vat_amount ({expected_gross})"
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

    lines: list[InvoiceLine] = Field(
        default_factory=list,
        description="fa_wiersz: Detailed invoice line items.",
    )
    order_lines: list[AdvanceOrderLine] = Field(
        default_factory=list,
        description="zamowienie: Order rows used on advance invoices.",
    )
    correction_reason: str | None = Field(
        default=None, description="przyczyna_korekty: Optional correction reason."
    )
    corrected_invoices: list[CorrectedInvoiceReference] = Field(
        default_factory=list,
        description="dane_fa_korygowanej: References to corrected invoices.",
    )
    advance_invoice_references: list[AdvanceInvoiceReference] = Field(
        default_factory=list,
        description="faktura_zaliczkowa: Referenced advance invoices on settlements.",
    )
    settlement_charges: list[SettlementCharge] = Field(
        default_factory=list,
        description="rozliczenie/obciazenia",
    )
    settlement_deductions: list[SettlementDeduction] = Field(
        default_factory=list,
        description="rozliczenie/odliczenia",
    )
    payment: InvoicePayment | None = Field(
        default=None,
        description="platnosc: Payment details for the invoice.",
    )
    margin_procedure: MarginProcedure | None = Field(
        default=None,
        description="adnotacje/pmarzy: Margin procedure flag.",
    )

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
        if not self.lines and not self.order_lines:
            raise ValueError("At least one invoice line or order line is required")

        if self.invoice_type == InvoiceType.ZAL:
            if self.lines:
                raise ValueError("Advance invoices use order_lines instead of lines")
            if not self.order_lines:
                raise ValueError("Advance invoices require at least one order line")
        elif self.order_lines:
            raise ValueError("order_lines are only valid for advance invoices")
        elif not self.lines:
            raise ValueError("At least one invoice line is required")

    def _validate_intent_specific_data(self) -> None:
        if self.invoice_type == InvoiceType.CORRECTING and not self.corrected_invoices:
            raise ValueError("Correcting invoices require corrected_invoices data")
        if self.invoice_type == InvoiceType.ROZ and not self.advance_invoice_references:
            raise ValueError(
                "Settlement invoices require at least one advance invoice reference"
            )
        if self.margin_procedure is not None:
            if not self.lines:
                raise ValueError("Margin procedure requires invoice lines")
            non_margin_lines = [
                line for line in self.lines if line.sale_category != SaleCategory.MARGIN
            ]
            if non_margin_lines:
                raise ValueError(
                    "Margin procedure can only be used with MARGIN sale_category lines"
                )

    def _financial_rows(self) -> list[InvoiceLine | AdvanceOrderLine]:
        if self.invoice_type == InvoiceType.ZAL:
            return list(self.order_lines)
        return list(self.lines)

    def _sum_net(
        self, predicate: Callable[[InvoiceLine | AdvanceOrderLine], bool]
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
        self, predicate: Callable[[InvoiceLine | AdvanceOrderLine], bool]
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
        return sum(
            (charge.amount for charge in self.settlement_charges),
            start=Decimal("0.00"),
        )

    @property
    def settlement_deductions_total(self) -> Money:
        explicit_deductions = [
            deduction.amount for deduction in self.settlement_deductions
        ]
        referenced_deductions = [
            reference.deduction_amount
            for reference in self.advance_invoice_references
            if reference.deduction_amount is not None
        ]
        return sum(
            explicit_deductions + referenced_deductions,
            start=Decimal("0.00"),
        )

    @property
    def settlement_balance(self) -> Money:
        return (
            self.total_gross
            + self.settlement_charges_total
            - self.settlement_deductions_total
        )
