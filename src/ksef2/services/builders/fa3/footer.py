from typing import Callable, Self, TypedDict

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import FooterRegistry, InvoiceFooter


class InvoiceFooterState(TypedDict):
    additional_informations: list[str]
    registries: list[FooterRegistry]


adapter = TypeAdapter(InvoiceFooterState)


def _default_state() -> InvoiceFooterState:
    return {
        "additional_informations": [],
        "registries": [],
    }


class FooterBuilder[TParent]:
    def __init__(
        self,
        parent: TParent,
        on_done: Callable[[InvoiceFooter], None],
        existing_state: InvoiceFooter | None = None,
    ) -> None:
        self._parent = parent
        self._on_done = on_done
        self._state: InvoiceFooterState = adapter.validate_python(
            existing_state.model_dump() if existing_state else _default_state()
        )

    def from_model(self, footer: InvoiceFooter) -> Self:
        self._state = adapter.validate_python(footer.model_dump())
        return self

    def add_information(self, information: str) -> Self:
        self._state["additional_informations"].append(information)
        return self

    def clear_informations(self) -> Self:
        self._state["additional_informations"].clear()
        return self

    def add_registry(
        self,
        *,
        full_name: str | None = None,
        krs: str | None = None,
        regon: str | None = None,
        bdo: str | None = None,
    ) -> Self:
        self._state["registries"].append(
            FooterRegistry(
                full_name=full_name,
                krs=krs,
                regon=regon,
                bdo=bdo,
            )
        )
        return self

    def add_registry_model(self, registry: FooterRegistry) -> Self:
        self._state["registries"].append(registry)
        return self

    def clear_registries(self) -> Self:
        self._state["registries"].clear()
        return self

    def build(self) -> InvoiceFooter:
        return InvoiceFooter(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        if self._is_empty():
            raise ValueError(
                "Footer details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class FooterBuilderMixin:
    _footer: InvoiceFooter | None = None

    def footer(self) -> FooterBuilder[Self]:
        return FooterBuilder(self, self._set_footer, self._footer)

    def _set_footer(self, value: InvoiceFooter) -> None:
        self._footer = value
