from importlib import import_module

__all__ = [
    "AdvanceInvoiceBuilder",
    "BaseFA3Builder",
    "CorrectionAdvanceInvoiceBuilder",
    "CorrectionInvoiceBuilder",
    "CorrectionSettlementInvoiceBuilder",
    "FA3InvoiceBuilder",
    "MarginInvoiceBuilder",
    "SettlementInvoiceBuilder",
    "SimplifiedInvoiceBuilder",
    "StandardInvoiceBuilder",
]


def __getattr__(name: str) -> object:
    if name in __all__:
        return getattr(import_module("ksef2.services.builders.fa3"), name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
