from datetime import date
from typing import Annotated, Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import (
    InvoiceAnnotationsContext,
    InvoiceTaxExemption,
    MarginProcedure,
    NewTransportMeansItem,
    NewTransportSupply,
)
from ksef2.services.builders.fa3.metadata import builder_param


class InvoiceAnnotationsState(TypedDict):
    cash_accounting: bool
    self_billing: bool
    reverse_charge_annotation: bool
    split_payment: bool
    simplified_procedure: bool
    margin_procedure: MarginProcedure | None
    tax_exemption: InvoiceTaxExemption | None


adapter = TypeAdapter(InvoiceAnnotationsState)


def _default_state() -> InvoiceAnnotationsState:
    return {
        "cash_accounting": False,
        "self_billing": False,
        "reverse_charge_annotation": False,
        "split_payment": False,
        "simplified_procedure": False,
        "margin_procedure": None,
        "tax_exemption": None,
    }


class AnnotationsBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoiceAnnotationsContext], None],
        existing_state: InvoiceAnnotationsContext | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        if existing_state is None:
            self._state = adapter.validate_python(_default_state())
        else:
            self._state = adapter.validate_python(
                {
                    "cash_accounting": existing_state.cash_accounting,
                    "self_billing": existing_state.self_billing,
                    "reverse_charge_annotation": existing_state.reverse_charge_annotation,
                    "split_payment": existing_state.split_payment,
                    "simplified_procedure": existing_state.simplified_procedure,
                    "margin_procedure": existing_state.margin_procedure,
                    "tax_exemption": existing_state.tax_exemption,
                }
            )
        new_transport = existing_state.new_transport_supply if existing_state else None
        self._article_42_5_required: bool | None = (
            new_transport.article_42_5_required if new_transport else None
        )
        self._new_transport_items: list[NewTransportMeansItem] = (
            list(new_transport.items) if new_transport else []
        )

    def from_model(self, annotations: InvoiceAnnotationsContext) -> Self:
        self._state = adapter.validate_python(
            {
                "cash_accounting": annotations.cash_accounting,
                "self_billing": annotations.self_billing,
                "reverse_charge_annotation": annotations.reverse_charge_annotation,
                "split_payment": annotations.split_payment,
                "simplified_procedure": annotations.simplified_procedure,
                "margin_procedure": annotations.margin_procedure,
                "tax_exemption": annotations.tax_exemption,
            }
        )
        new_transport = annotations.new_transport_supply
        self._article_42_5_required = (
            new_transport.article_42_5_required if new_transport else None
        )
        self._new_transport_items = list(new_transport.items) if new_transport else []
        return self

    def cash_accounting(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice with the cash accounting annotation.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["cash_accounting"] = enabled
        return self

    def self_billing(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice as self-billing.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["self_billing"] = enabled
        return self

    def reverse_charge_annotation(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice with the reverse charge annotation.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["reverse_charge_annotation"] = enabled
        return self

    def split_payment(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice with the split payment annotation.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["split_payment"] = enabled
        return self

    def simplified_procedure(
        self,
        enabled: Annotated[
            bool,
            builder_param(
                "Marks the invoice with the simplified procedure annotation.",
                examples=[True],
                priority="advanced",
            ),
        ] = True,
    ) -> Self:
        self._state["simplified_procedure"] = enabled
        return self

    def margin_procedure(
        self,
        procedure: Annotated[
            MarginProcedure | str | None,
            builder_param(
                "Margin procedure applied to the invoice when the invoice uses margin taxation.",
                examples=["travel_agency", "used_goods"],
                format="enum-string",
                priority="advanced",
            ),
        ],
    ) -> Self:
        if procedure is None or isinstance(procedure, MarginProcedure):
            self._state["margin_procedure"] = procedure
        else:
            self._state["margin_procedure"] = MarginProcedure(procedure)
        return self

    def tax_exemption(
        self,
        *,
        legal_basis_act: Annotated[
            str | None,
            builder_param(
                "Legal basis from a domestic act used to justify the tax exemption.",
                examples=["art. 43 ust. 1 pkt 10 ustawy o VAT"],
                priority="advanced",
            ),
        ] = None,
        legal_basis_eu_directive: Annotated[
            str | None,
            builder_param(
                "Legal basis from an EU directive used to justify the tax exemption.",
                examples=["art. 132 Dyrektywy 2006/112/WE"],
                priority="advanced",
            ),
        ] = None,
        legal_basis_other: Annotated[
            str | None,
            builder_param(
                "Other legal basis used to justify the tax exemption.",
                examples=["International agreement"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        if (
            legal_basis_act is None
            and legal_basis_eu_directive is None
            and legal_basis_other is None
        ):
            self._state["tax_exemption"] = None
            return self
        self._state["tax_exemption"] = InvoiceTaxExemption(
            legal_basis_act=legal_basis_act,
            legal_basis_eu_directive=legal_basis_eu_directive,
            legal_basis_other=legal_basis_other,
        )
        return self

    def clear_tax_exemption(self) -> Self:
        self._state["tax_exemption"] = None
        return self

    def new_transport_supply(
        self,
        *,
        article_42_5_required: Annotated[
            bool | None,
            builder_param(
                "Set when the new means of transport supply requires the Article 42(5) marker.",
                examples=[True],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._article_42_5_required = article_42_5_required
        return self

    def add_new_transport_item(
        self,
        *,
        available_from: Annotated[
            date,
            builder_param(
                "Date from which the transport item was made available.",
                examples=["2026-04-01"],
                format="date",
                priority="advanced",
            ),
        ],
        row_number: Annotated[
            int,
            builder_param(
                "Row number used to identify the transport item inside the annotation block.",
                examples=[1],
                priority="advanced",
            ),
        ] = 1,
        brand: Annotated[
            str | None,
            builder_param(
                "Brand of the new means of transport.",
                examples=["Tesla"],
                priority="advanced",
            ),
        ] = None,
        model: Annotated[
            str | None,
            builder_param(
                "Model of the new means of transport.",
                examples=["Model Y"],
                priority="advanced",
            ),
        ] = None,
        color: Annotated[
            str | None,
            builder_param(
                "Color of the new means of transport.",
                examples=["black"],
                priority="advanced",
            ),
        ] = None,
        registration_number: Annotated[
            str | None,
            builder_param(
                "Registration number of the new means of transport.",
                examples=["WX12345"],
                priority="advanced",
            ),
        ] = None,
        production_year: Annotated[
            str | None,
            builder_param(
                "Production year of the new means of transport.",
                examples=["2026"],
                priority="advanced",
            ),
        ] = None,
        land_vehicle_mileage: Annotated[
            str | None,
            builder_param(
                "Mileage for a land vehicle.",
                examples=["1200"],
                priority="advanced",
            ),
        ] = None,
        vin: Annotated[
            str | None,
            builder_param(
                "VIN of the transport item.",
                examples=["5YJYGDEE0MF123456"],
                priority="advanced",
            ),
        ] = None,
        body_number: Annotated[
            str | None,
            builder_param(
                "Body number of the transport item.",
                examples=["BODY-123"],
                priority="advanced",
            ),
        ] = None,
        chassis_number: Annotated[
            str | None,
            builder_param(
                "Chassis number of the transport item.",
                examples=["CHASSIS-123"],
                priority="advanced",
            ),
        ] = None,
        frame_number: Annotated[
            str | None,
            builder_param(
                "Frame number of the transport item.",
                examples=["FRAME-123"],
                priority="advanced",
            ),
        ] = None,
        land_vehicle_type: Annotated[
            str | None,
            builder_param(
                "Type of land vehicle.",
                examples=["passenger car"],
                priority="advanced",
            ),
        ] = None,
        vessel_working_hours: Annotated[
            str | None,
            builder_param(
                "Working hours for a vessel.",
                examples=["25"],
                priority="advanced",
            ),
        ] = None,
        hull_number: Annotated[
            str | None,
            builder_param(
                "Hull number for a vessel.",
                examples=["HULL-123"],
                priority="advanced",
            ),
        ] = None,
        aircraft_working_hours: Annotated[
            str | None,
            builder_param(
                "Working hours for an aircraft.",
                examples=["40"],
                priority="advanced",
            ),
        ] = None,
        aircraft_serial_number: Annotated[
            str | None,
            builder_param(
                "Serial number for an aircraft.",
                examples=["AIR-123"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        self._new_transport_items.append(
            NewTransportMeansItem(
                available_from=available_from,
                row_number=row_number,
                brand=brand,
                model=model,
                color=color,
                registration_number=registration_number,
                production_year=production_year,
                land_vehicle_mileage=land_vehicle_mileage,
                vin=vin,
                body_number=body_number,
                chassis_number=chassis_number,
                frame_number=frame_number,
                land_vehicle_type=land_vehicle_type,
                vessel_working_hours=vessel_working_hours,
                hull_number=hull_number,
                aircraft_working_hours=aircraft_working_hours,
                aircraft_serial_number=aircraft_serial_number,
            )
        )
        return self

    def add_new_transport_item_model(self, item: NewTransportMeansItem) -> Self:
        self._new_transport_items.append(item)
        return self

    def clear_new_transport_items(self) -> Self:
        self._new_transport_items.clear()
        self._article_42_5_required = None
        return self

    def build(self) -> InvoiceAnnotationsContext:
        new_transport_supply = None
        if self._new_transport_items or self._article_42_5_required is not None:
            new_transport_supply = NewTransportSupply(
                article_42_5_required=self._article_42_5_required,
                items=self._new_transport_items,
            )
        return InvoiceAnnotationsContext(
            cash_accounting=self._state["cash_accounting"],
            self_billing=self._state["self_billing"],
            reverse_charge_annotation=self._state["reverse_charge_annotation"],
            split_payment=self._state["split_payment"],
            tax_exemption=self._state["tax_exemption"],
            new_transport_supply=new_transport_supply,
            simplified_procedure=self._state["simplified_procedure"],
            margin_procedure=self._state["margin_procedure"],
        )

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Annotation details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class AnnotationsBuilderMixin:
    _annotations: InvoiceAnnotationsContext | None = None

    def annotations(self) -> AnnotationsBuilder[Self]:
        return AnnotationsBuilder(self, self._set_annotations, self._annotations)

    def _set_annotations(self, value: InvoiceAnnotationsContext) -> None:
        self._annotations = value
