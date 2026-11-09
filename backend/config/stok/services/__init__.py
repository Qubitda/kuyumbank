"""Stok servisleri — alt modüller doğrudan import edilir."""

from importlib import import_module

__all__ = [
    "birim",
    "ledger_servisi",
    "reservation_servisi",
    "warehouse_servisi",
]


def __getattr__(name: str):
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
