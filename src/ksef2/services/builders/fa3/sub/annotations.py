from datetime import date
from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import (
    InvoiceAnnotationsContext,
    InvoiceTaxExemption,
    MarginProcedure,
    NewTransportMeansItem,
    NewTransportSupply,
)


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

    def cash_accounting(self, enabled: bool = True) -> Self:
        self._state["cash_accounting"] = enabled
        return self

    def self_billing(self, enabled: bool = True) -> Self:
        self._state["self_billing"] = enabled
        return self

    def reverse_charge_annotation(self, enabled: bool = True) -> Self:
        self._state["reverse_charge_annotation"] = enabled
        return self

    def split_payment(self, enabled: bool = True) -> Self:
        self._state["split_payment"] = enabled
        return self

    def simplified_procedure(self, enabled: bool = True) -> Self:
        self._state["simplified_procedure"] = enabled
        return self

    def margin_procedure(self, procedure: MarginProcedure | str | None) -> Self:
        if procedure is None or isinstance(procedure, MarginProcedure):
            self._state["margin_procedure"] = procedure
        else:
            self._state["margin_procedure"] = MarginProcedure(procedure)
        return self

    def tax_exemption(
        self,
        *,
        legal_basis_act: str | None = None,
        legal_basis_eu_directive: str | None = None,
        legal_basis_other: str | None = None,
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
        self, *, article_42_5_required: bool | None = None
    ) -> Self:
        self._article_42_5_required = article_42_5_required
        return self

    def add_new_transport_item(
        self,
        *,
        available_from: date,
        row_number: int = 1,
        brand: str | None = None,
        model: str | None = None,
        color: str | None = None,
        registration_number: str | None = None,
        production_year: str | None = None,
        land_vehicle_mileage: str | None = None,
        vin: str | None = None,
        body_number: str | None = None,
        chassis_number: str | None = None,
        frame_number: str | None = None,
        land_vehicle_type: str | None = None,
        vessel_working_hours: str | None = None,
        hull_number: str | None = None,
        aircraft_working_hours: str | None = None,
        aircraft_serial_number: str | None = None,
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
