from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ksef2.fa3 import FA3InvoiceBuilder

__all__ = ["FA3InvoiceBuilder"]


def __getattr__(name: str) -> object:
    if name == "FA3InvoiceBuilder":
        from ksef2.fa3 import FA3InvoiceBuilder

        return FA3InvoiceBuilder

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
