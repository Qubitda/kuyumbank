"""F4-002 — Legacy dual-stock alan envanteri (ledger henüz yok).

Bu modül tek doğruluk kaynağı değildir; `Varyant.stok` / `TedarikciTeklif.stok_adet`
ledger gelene kadar yalnızca envanter + deprecation işaretidir.
Silent dual-write yok; birimler arası dönüşüm yok (U-002).
"""

from __future__ import annotations

from typing import Any


# Yazma yüzeyleri (kod taraması 2026-11-08): model alanı + admin form alanları.
# Servis katmanında merkezi stok yazımı yok — ORM/admin doğrudan yazar.
LEGACY_STOCK_FIELDS: tuple[dict[str, Any], ...] = (
    {
        "model": "urunler.Varyant",
        "field": "stok",
        "db_type": "PositiveIntegerField",
        "legacy_unit": "ADET",
        "note": (
            "Katalog varyant adet sayacı. Ledger truth değil. "
            "GRAM tekliflerle toplanmaz/dönüştürülmez."
        ),
        "write_surfaces": ("ORM", "admin (Varyant)"),
        "deprecation": "F4-011 sonrası yazma kapatma; F4-070 kaldırma",
    },
    {
        "model": "fiyatlama.TedarikciTeklif",
        "field": "stok_adet",
        "db_type": "PositiveIntegerField",
        "legacy_unit": "ADET",
        "note": (
            "Teklif adet sayacı (isim ADET). fiyat_modeli GRAM olsa bile "
            "bu alan gram değildir — ledger'a kör kopya yasak."
        ),
        "write_surfaces": ("ORM", "admin (TedarikciTeklif)"),
        "deprecation": "F4-011 sonrası yazma kapatma; F4-070 kaldırma",
    },
)


def legacy_stock_inventory() -> list[dict[str, Any]]:
    """F4-002 kabul: okuma/yazma noktaları listesi (immutable tuple kopyası)."""
    return [dict(row) for row in LEGACY_STOCK_FIELDS]


def legacy_fields_are_adet_only() -> bool:
    """Legacy alanların tamamı ADET semantiğinde mi?"""
    return all(row["legacy_unit"] == "ADET" for row in LEGACY_STOCK_FIELDS)
