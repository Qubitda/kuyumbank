"""ADR-0030 — ops ürün DTO (olusturan_firma ops'ta; tedarikçi maliyet/SKU yok)."""

from __future__ import annotations

from api.masking import assert_masked
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm


def _allowed_actions(urun, user) -> list[str]:
    actions: list[str] = ["view"]
    if has_perm(user, P["submit_urun"]) and urun.onay_durumu in (
        "taslak",
        "reddedildi",
    ):
        actions.append("submit")
        actions.append("add_variant")
    if has_perm(user, P["approve_urun"]) and urun.onay_durumu == "onay_bekliyor":
        actions.extend(["approve", "reject"])
    if has_perm(user, P["publish_urun"]) and urun.onay_durumu == "onayli":
        if urun.yayin_durumu != "aktif":
            actions.append("publish")
        if urun.yayin_durumu in ("aktif", "yakinda"):
            actions.append("unpublish")
    return actions


def present_ops_variant(v) -> dict:
    data = {
        "id": v.pk,
        "sku": v.sku or "",
        "gram": str(v.gram) if v.gram is not None else None,
        "renk_id": v.renk_id,
        "beden_id": v.beden_id,
        "ek_bedel": str(v.ek_bedel) if v.ek_bedel is not None else "0",
        "aktif": bool(v.aktif),
    }
    assert_masked(data)
    return data


def present_ops_product(urun, *, user, include_variants: bool = False) -> dict:
    varyant_count = getattr(urun, "varyant_count", None)
    if varyant_count is None:
        varyant_count = urun.varyantlar.filter(aktif=True).count()
    data = {
        "id": urun.pk,
        "ad": urun.ad,
        "platform_kodu": urun.platform_kodu or "",
        "aciklama": urun.aciklama or "",
        "kategori_id": urun.kategori_id,
        "kategori": getattr(getattr(urun, "kategori", None), "ad", "") or "",
        "ayar_id": urun.ayar_id,
        "ayar": getattr(getattr(urun, "ayar", None), "ayar_kodu", "") or "",
        "fiyat_tipi": urun.fiyat_tipi,
        "onay_durumu": urun.onay_durumu,
        "yayin_durumu": urun.yayin_durumu,
        "red_nedeni": urun.red_nedeni or "",
        "olusturan_firma_id": urun.olusturan_firma_id,
        "varyant_count": int(varyant_count),
        "allowed_actions": _allowed_actions(urun, user),
    }
    if include_variants:
        data["varyantlar"] = [
            present_ops_variant(v)
            for v in urun.varyantlar.all().order_by("pk")
        ]
    assert_masked(data)
    return data
