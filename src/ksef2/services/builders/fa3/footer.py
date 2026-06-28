"""Fluent builders for FA(3) invoice footer blocks."""

from typing import Annotated, Self, TypedDict
from collections.abc import Callable

from pydantic import TypeAdapter

from ksef2.domain.models.fa3 import FooterRegistry, InvoiceFooter
from ksef2.services.builders.fa3.metadata import builder_param


class InvoiceFooterState(TypedDict):
    """Typed state for FA(3) footer fields."""

    additional_informations: list[str]
    registries: list[FooterRegistry]


adapter = TypeAdapter(InvoiceFooterState)


def _default_state() -> InvoiceFooterState:
    return {
        "additional_informations": [],
        "registries": [],
    }


class FooterBuilder[TParent]:
    """Fluent builder for FA(3) invoice footer details."""

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
        """Replace the builder state from an existing domain model."""
        self._state = adapter.validate_python(footer.model_dump())
        return self

    def add_information(
        self,
        information: Annotated[
            str,
            builder_param(
                "Additional footer information shown below the invoice body.",
                examples=["Invoice generated electronically."],
                priority="advanced",
            ),
        ],
    ) -> Self:
        """Add an invoice footer information entry."""
        self._state["additional_informations"].append(information)
        return self

    def clear_informations(self) -> Self:
        """Remove all informations entries."""
        self._state["additional_informations"].clear()
        return self

    def add_registry(
        self,
        *,
        full_name: Annotated[
            str | None,
            builder_param(
                "Full registry name shown in the footer.",
                examples=["District Court in Warsaw, 13th Commercial Division"],
                priority="advanced",
            ),
        ] = None,
        krs: Annotated[
            str | None,
            builder_param(
                "KRS number shown in the footer registry block.",
                examples=["0000123456"],
                priority="advanced",
            ),
        ] = None,
        regon: Annotated[
            str | None,
            builder_param(
                "REGON number shown in the footer registry block.",
                examples=["123456789"],
                priority="advanced",
            ),
        ] = None,
        bdo: Annotated[
            str | None,
            builder_param(
                "BDO number shown in the footer registry block.",
                examples=["000123456"],
                priority="advanced",
            ),
        ] = None,
    ) -> Self:
        """Add a registry entry to the invoice footer."""
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
        """Add an existing footer registry model."""
        self._state["registries"].append(registry)
        return self

    def clear_registries(self) -> Self:
        """Remove all footer registry entries."""
        self._state["registries"].clear()
        return self

    def build(self) -> InvoiceFooter:
        """Build the corresponding FA(3) domain model."""
        return InvoiceFooter(**self._state)

    def _is_empty(self) -> bool:
        return self._state == _default_state()

    def done(self) -> TParent:
        """Attach the built footer to the parent builder and return the parent.

        Raises:
            ValueError: If footer details are empty.
        """
        if self._is_empty():
            raise ValueError(
                "Footer details are empty. Set at least one field before calling done()."
            )
        self._on_done(self.build())
        return self._parent


class FooterBuilderMixin:
    """Mixin exposing the Footer sub-builder."""

    _footer: InvoiceFooter | None = None

    def footer(self) -> FooterBuilder[Self]:
        """Start a footer sub-builder."""
        return FooterBuilder(self, self._set_footer, self._footer)

    def _set_footer(self, value: InvoiceFooter) -> None:
        self._footer = value
