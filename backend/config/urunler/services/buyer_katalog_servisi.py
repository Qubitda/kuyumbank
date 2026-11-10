"""F9-011 — Alıcı katalog browse (yayınlı; kör havuz; maliyet/tedarikçi yok)."""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from api.masking import assert_masked
from urunler.models import Urun, Varyant


class BuyerCatalogNotFound(ObjectDoesNotExist):
    """404 — varlık / kapsam sızdırılmaz."""


def _published_qs():
    return (
        Urun.objects.filter(yayin_durumu="aktif", onay_durumu="onayli")
        .select_related("kategori", "ayar")
        .order_by("ad", "pk")
    )


def liste(*, q: str = "", limit: int = 50) -> list[dict]:
    qs = _published_qs()
    term = (q or "").strip()
    if term:
        qs = qs.filter(
            Q(ad__icontains=term) | Q(platform_kodu__icontains=term)
        ).order_by("ad", "pk")
    rows = []
    for u in qs[: max(1, min(limit, 100))]:
        row = {
            "id": u.pk,
            "ad": u.ad,
            "platform_kodu": u.platform_kodu or "",
            "kategori": getattr(u.kategori, "ad", "") or "",
            "ayar": getattr(u.ayar, "ayar_kodu", "") or "",
            "fiyat_tipi": u.fiyat_tipi,
            "varyant_count": u.varyantlar.filter(aktif=True).count(),
        }
        assert_masked(row)
        rows.append(row)
    return rows


def detay(*, urun_id: int) -> dict:
    try:
        u = _published_qs().get(pk=urun_id)
    except Urun.DoesNotExist as exc:
        raise BuyerCatalogNotFound("Ürün bulunamadı.") from exc
    varyantlar = []
    for v in (
        Varyant.objects.filter(urun=u, aktif=True)
        .select_related("renk", "beden")
        .order_by("pk")
    ):
        item = {
            "id": v.pk,
            "sku": v.sku,
            "gram": str(v.gram) if v.gram is not None else None,
            "renk": getattr(v.renk, "ad", "") if v.renk_id else "",
            "beden": str(v.beden) if v.beden_id else "",
        }
        assert_masked(item)
        varyantlar.append(item)
    data = {
        "id": u.pk,
        "ad": u.ad,
        "platform_kodu": u.platform_kodu or "",
        "aciklama": (u.aciklama or "")[:2000],
        "kategori": getattr(u.kategori, "ad", "") or "",
        "ayar": getattr(u.ayar, "ayar_kodu", "") or "",
        "fiyat_tipi": u.fiyat_tipi,
        "varyantlar": varyantlar,
    }
    assert_masked(data)
    return data
