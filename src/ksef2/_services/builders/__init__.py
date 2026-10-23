from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ksef2.fa3 import InvoiceBuilder

__all__ = ["InvoiceBuilder"]


def __getattr__(name: str) -> object:
    if name in {"InvoiceBuilder", "FA3InvoiceBuilder"}:
        from ksef2.fa3 import InvoiceBuilder

        return InvoiceBuilder

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
