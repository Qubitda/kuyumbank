"""F7-010 — Kör havuz DTO maske assert."""

from __future__ import annotations

from typing import Any, Iterable

# Buyer/supplier yüzünde asla bulunmaması gereken anahtarlar (case-insensitive)
FORBIDDEN_KEYS = frozenset(
    {
        "tedarikci_id",
        "tedarikci_firma_id",
        "supplier_id",
        "supplier_firma_id",
        "maliyet",
        "cost",
        "cost_price",
        "alici_ad",
        "buyer_name",
        "alici_unvan",
        "supplier_name",
        "tedarikci_ad",
    }
)


def assert_masked(payload: Any, *, path: str = "$") -> None:
    """DTO içinde yasak anahtar yok; nested dict/list yürür."""
    if isinstance(payload, dict):
        for key, val in payload.items():
            lk = str(key).lower()
            if lk in FORBIDDEN_KEYS:
                raise AssertionError(f"Kör havuz sızıntısı: {path}.{key}")
            assert_masked(val, path=f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        for i, item in enumerate(payload):
            assert_masked(item, path=f"{path}[{i}]")


def strip_forbidden(payload: dict[str, Any]) -> dict[str, Any]:
    """Savunmacı: yasak anahtarları düşür (presenter sonrası)."""
    return {k: v for k, v in payload.items() if str(k).lower() not in FORBIDDEN_KEYS}
