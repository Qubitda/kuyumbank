"""F4-002 / F4-070 — Legacy dual-stock alan envanteri + yazma kilidi.

`Varyant.stok` / `TedarikciTeklif.stok_adet` ledger truth değildir.
F4-070: güncelleme yazımı kapalı (save freeze); kolon kaldırma sonraki dilim.
Silent dual-write yok; birimler arası dönüşüm yok (U-002).
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError


# Envanter (kod taraması); yazma F4-070 ile model save + admin readonly kilitli.
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
        "write_surfaces": ("create-default only", "admin readonly"),
        "deprecation": "F4-070 yazma kapalı; kolon kaldırma ayrı dilim",
        "writes_closed": True,
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
        "write_surfaces": ("create/copy only", "admin readonly"),
        "deprecation": "F4-070 yazma kapalı; kolon kaldırma ayrı dilim",
        "writes_closed": True,
    },
)


def legacy_stock_inventory() -> list[dict[str, Any]]:
    """F4-002 kabul: okuma/yazma noktaları listesi (immutable tuple kopyası)."""
    return [dict(row) for row in LEGACY_STOCK_FIELDS]


def legacy_fields_are_adet_only() -> bool:
    """Legacy alanların tamamı ADET semantiğinde mi?"""
    return all(row["legacy_unit"] == "ADET" for row in LEGACY_STOCK_FIELDS)


def legacy_writes_closed() -> bool:
    """F4-070: tüm legacy alanlarda yazma kapatıldı mı?"""
    return all(row.get("writes_closed") for row in LEGACY_STOCK_FIELDS)


def assert_legacy_stock_unchanged(*, instance, field_name: str) -> None:
    """Güncellemede legacy stok alanını dondurur; değişirse ValidationError.

    QuerySet.update bu kilidi atlar — yasak (ledger dışı yazma yok).
    """
    if not getattr(instance, "pk", None):
        return
    prev = (
        type(instance)
        .objects.filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )
    if prev is None:
        return
    current = getattr(instance, field_name)
    if current != prev:
        label = f"{instance._meta.app_label}.{instance._meta.object_name}"
        raise ValidationError(
            {
                field_name: (
                    f"Legacy {label}.{field_name} yazımı kapalı (F4-070); "
                    "stok için ledger (StockMovement/Balance) kullanın."
                )
            }
        )
