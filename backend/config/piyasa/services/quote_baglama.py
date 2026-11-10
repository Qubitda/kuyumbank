"""ADR-0020 PP-9 / ADR-0024 — PANO|MANUEL birim → PriceQuote (KS-6 hedef_toplam)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm, is_platform_firm_user
from fiyatlama.services import pricing_service
from piyasa.services import hesap
from piyasa.services.piyasa_fiyat_servisi import (
    KAYNAK_MANUEL,
    KAYNAK_PANO,
    cozumle_islem_birim_fiyati,
)


def _assert_baglama_yetkisi(actor) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Pano quote bağlama için kimlik gerekli.")
    if not is_platform_firm_user(actor):
        raise PermissionDenied("Pano quote bağlama yalnız platform kullanıcısı.")
    if has_perm(actor, P["manage_piyasa"]) or has_perm(actor, P["manage_sozlesme"]):
        return
    raise PermissionDenied(
        "Pano quote için manage_piyasa veya manage_sozlesme gerekir."
    )


def quote_from_islem_fiyati(
    *,
    actor,
    alici_firma,
    satis_kanali,
    varyant,
    kaynak: str,
    taraf: str = hesap.SATIS,
    urun_kod: str | None = None,
    manuel_birim_fiyat=None,
    kullanici_ekleri: dict | None = None,
    agirlik_gr=None,
    teklif_id: int | None = None,
    para_birimi: str = "TRY",
    now=None,
):
    """PANO|MANUEL etkin birim × gram → HEDEF_TOPLAM PriceQuote.

    OrderLine snapshot: sonraki `lock_quote` + checkout (L-11); bu fonksiyon
    yalnız quote üretir.
    """
    _assert_baglama_yetkisi(actor)
    kaynak = (kaynak or "").upper()
    if kaynak not in {KAYNAK_PANO, KAYNAK_MANUEL}:
        raise ValidationError({"kaynak": f"Geçersiz kaynak: {kaynak!r}."})

    if agirlik_gr is None:
        agirlik = varyant.gram
        if agirlik is None:
            raise ValidationError(
                {"agirlik_gr": "Gram yok; agirlik_gr verin veya varyant.gram doldurun."}
            )
    else:
        agirlik = Decimal(str(agirlik_gr))

    coz = cozumle_islem_birim_fiyati(
        kaynak=kaynak,
        taraf=taraf,
        urun_kod=urun_kod,
        manuel_birim_fiyat=manuel_birim_fiyat,
        kullanici_ekleri=kullanici_ekleri,
        agirlik_gr=agirlik,
        now=now,
    )
    etkin = Decimal(str(coz["etkin_birim"]))
    hedef = (etkin * Decimal(str(agirlik))).quantize(hesap.HASSASIYET)
    if hedef <= 0:
        raise ValidationError("Pano/manuel hedef toplam sıfır veya negatif.")

    extra: dict[str, Any] = {
        "birim_kaynak": coz["kaynak"],
        "piyasa_urun_kod": coz.get("urun_kod") or "",
        "islem_taraf": coz["taraf"],
        "baz_birim": str(coz["baz_birim"]),
        "etkin_birim": str(coz["etkin_birim"]),
        "pano_baglama": "ADR-0024",
    }
    if coz.get("feed_health"):
        extra["pano_feed_health"] = coz["feed_health"]
    if coz.get("banner"):
        extra["pano_feed_banner"] = coz["banner"]
    if coz.get("katman2"):
        extra["katman2"] = {k: str(v) for k, v in coz["katman2"].items()}

    return pricing_service.quote(
        alici_firma=alici_firma,
        satis_kanali=satis_kanali,
        varyant=varyant,
        kullanici=actor,
        teklif_id=teklif_id,
        para_birimi=para_birimi,
        hedef_toplam=hedef,
        hesap_girdisi_extra=extra,
        now=now,
    )
