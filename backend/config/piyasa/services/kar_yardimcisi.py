"""Piyasa kar hesaplama yardımcısı (ADR-0020 PP-8 + ADR-0022 V2-8…11).

ADR-0014 `karlilik_simulasyonu` + pano veya metal/ayar girişi.
Ledger / quote / order yazmaz.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.utils import timezone

from fiyatlama.services import karlilik_simulasyonu
from piyasa.models import PiyasaKarPolitikasi
from piyasa.services import hesap
from piyasa.services.piyasa_fiyat_servisi import baz_fiyat
from tanimlar.models import AyarMilyem, KiymetliMetal, KurTaraf
from tanimlar.services import kur_servisi

_TARAFA_KUR = {
    hesap.ALIS: KurTaraf.TEDARIKCI,
    hesap.SATIS: KurTaraf.ALICI,
}


def get_kar_politikasi() -> PiyasaKarPolitikasi:
    pol, _ = PiyasaKarPolitikasi.objects.get_or_create(anahtar="default")
    return pol


def _default_kesintiler(
    *,
    banka=None,
    isletme=None,
    gelir_vergisi=None,
    diger=None,
) -> dict[str, dict]:
    pol = get_kar_politikasi()
    base = pol.kesinti_dict()
    if banka is not None:
        base["banka"] = karlilik_simulasyonu.kesinti_from_any(
            banka, default_tip=base["banka"]["tip"], default_deger=base["banka"]["deger"]
        )
    if isletme is not None:
        base["isletme"] = karlilik_simulasyonu.kesinti_from_any(
            isletme,
            default_tip=base["isletme"]["tip"],
            default_deger=base["isletme"]["deger"],
        )
    if gelir_vergisi is not None:
        base["gelir_vergisi"] = karlilik_simulasyonu.kesinti_from_any(
            gelir_vergisi,
            default_tip=base["gelir_vergisi"]["tip"],
            default_deger=base["gelir_vergisi"]["deger"],
        )
    if diger is not None:
        base["diger"] = karlilik_simulasyonu.kesinti_from_any(
            diger, default_tip=base["diger"]["tip"], default_deger=base["diger"]["deger"]
        )
    return base


def _pack_sonuc(
    *,
    kaynak: str,
    taraf: str,
    birim: Decimal,
    feed_health: str,
    banner: str,
    urun_kod: str,
    metal_kod: str,
    ayar_kodu: str,
    sonuc: karlilik_simulasyonu.KarlilikSonuc,
) -> dict[str, Any]:
    return {
        "kaynak": kaynak,
        "urun_kod": urun_kod,
        "metal_kod": metal_kod,
        "ayar_kodu": ayar_kodu,
        "taraf": taraf,
        "baz_birim": birim,
        "feed_health": feed_health,
        "banner": banner,
        "mod": sonuc.mod,
        "maden_fiyati": sonuc.maden_fiyati,
        "iscilik_tl": sonuc.iscilik_tl,
        "gr_maliyet": sonuc.gr_maliyet,
        "kar_gr": sonuc.kar_gr,
        "gr_satis": sonuc.gr_satis,
        "agirlik_gr": sonuc.agirlik_gr,
        "toplam_satis": sonuc.toplam_satis,
        "brut_kar": sonuc.brut_kar,
        "brut_kar_marji_pct": sonuc.brut_kar_marji_pct,
        "banka_kesinti": sonuc.banka_kesinti,
        "isletme_gideri": sonuc.isletme_gideri,
        "gelir_vergisi": sonuc.gelir_vergisi,
        "diger_kesintiler": sonuc.diger_kesintiler,
        "net_kar": sonuc.net_kar,
        "net_kar_marji_pct": sonuc.net_kar_marji_pct,
        "banka_tipi": sonuc.banka_tipi,
        "isletme_tipi": sonuc.isletme_tipi,
        "gelir_vergisi_tipi": sonuc.gelir_vergisi_tipi,
        "diger_tipi": sonuc.diger_tipi,
    }


def _calistir_sim(
    *,
    birim: Decimal,
    agirlik_gr,
    kar_pct,
    iscilik_tl,
    hedef_toplam,
    kesintiler: dict,
):
    kwargs = {
        "maden_fiyati": birim,
        "iscilik_tl": iscilik_tl,
        "agirlik_gr": agirlik_gr,
        "banka": kesintiler["banka"],
        "isletme": kesintiler["isletme"],
        "gelir_vergisi": kesintiler["gelir_vergisi"],
        "diger": kesintiler["diger"],
    }
    if hedef_toplam is not None:
        return karlilik_simulasyonu.simule_hedef_toplam(
            hedef_toplam=hedef_toplam, **kwargs
        )
    return karlilik_simulasyonu.simule_marj_pct(kar_pct=kar_pct, **kwargs)


def simule_pano_urun(
    *,
    urun_kod: str,
    taraf: str = hesap.SATIS,
    agirlik_gr=Decimal("1"),
    kar_pct=Decimal("0"),
    iscilik_tl=Decimal("0"),
    banka=None,
    isletme=None,
    gelir_vergisi=None,
    diger=None,
    # legacy
    banka_pct=None,
    isletme_pct=None,
    gelir_vergisi_pct=None,
    diger_kesintiler=None,
    hedef_toplam=None,
    now=None,
) -> dict[str, Any]:
    """Pano baz birim fiyat + ADR-0014 A/B simülasyon."""
    taraf = (taraf or "").upper()
    if taraf not in hesap.TARAFLAR:
        raise ValidationError({"taraf": f"Geçersiz taraf: {taraf!r}."})

    baz = baz_fiyat(urun_kod, now=now)
    birim = baz["alis"] if taraf == hesap.ALIS else baz["satis"]
    if birim is None:
        raise ValidationError(f"Pano {taraf} fiyatı yok: {urun_kod}.")

    if banka is None and banka_pct is not None:
        banka = {"tip": "YUZDE", "deger": banka_pct}
    if isletme is None and isletme_pct is not None:
        isletme = {"tip": "YUZDE", "deger": isletme_pct}
    if gelir_vergisi is None and gelir_vergisi_pct is not None:
        gelir_vergisi = {"tip": "YUZDE", "deger": gelir_vergisi_pct}
    if diger is None and diger_kesintiler is not None:
        diger = {"tip": "TL", "deger": diger_kesintiler}

    kes = _default_kesintiler(
        banka=banka, isletme=isletme, gelir_vergisi=gelir_vergisi, diger=diger
    )
    sonuc = _calistir_sim(
        birim=birim,
        agirlik_gr=agirlik_gr,
        kar_pct=kar_pct,
        iscilik_tl=iscilik_tl,
        hedef_toplam=hedef_toplam,
        kesintiler=kes,
    )
    return _pack_sonuc(
        kaynak="PANO",
        taraf=taraf,
        birim=birim,
        feed_health=baz["feed_health"],
        banner=baz["banner"],
        urun_kod=baz["kod"],
        metal_kod="",
        ayar_kodu="",
        sonuc=sonuc,
    )


def simule_metal_ayar(
    *,
    metal_kod: str,
    ayar_kodu: str | None = None,
    taraf: str = hesap.SATIS,
    agirlik_gr=Decimal("1"),
    kar_pct=Decimal("0"),
    iscilik_tl=Decimal("0"),
    banka=None,
    isletme=None,
    gelir_vergisi=None,
    diger=None,
    hedef_toplam=None,
    now=None,
) -> dict[str, Any]:
    """Metal + ayar → kur × milyem (PiyasaUrun zorunlu değil)."""
    taraf = (taraf or "").upper()
    if taraf not in hesap.TARAFLAR:
        raise ValidationError({"taraf": f"Geçersiz taraf: {taraf!r}."})
    now = now or timezone.now()

    try:
        metal = KiymetliMetal.objects.get(kod=metal_kod)
    except KiymetliMetal.DoesNotExist as exc:
        raise ValidationError({"metal_kod": f"Metal yok: {metal_kod!r}."}) from exc

    milyem = Decimal("1")
    ayar_label = ""
    if ayar_kodu:
        try:
            ayar = AyarMilyem.objects.select_related("metal").get(
                metal=metal, ayar_kodu=ayar_kodu
            )
        except AyarMilyem.DoesNotExist as exc:
            raise ValidationError(
                {"ayar_kodu": f"Ayar yok: {metal_kod}/{ayar_kodu}."}
            ) from exc
        milyem = ayar.milyem
        ayar_label = ayar.ayar_kodu

    detay = kur_servisi.resolve_metal_kuru_detay(
        metal, taraf=_TARAFA_KUR[taraf], now=now
    )
    saf = detay.gozlem.saf_birim_fiyat
    birim = (saf * milyem).quantize(hesap.HASSASIYET)

    kes = _default_kesintiler(
        banka=banka, isletme=isletme, gelir_vergisi=gelir_vergisi, diger=diger
    )
    sonuc = _calistir_sim(
        birim=birim,
        agirlik_gr=agirlik_gr,
        kar_pct=kar_pct,
        iscilik_tl=iscilik_tl,
        hedef_toplam=hedef_toplam,
        kesintiler=kes,
    )
    return _pack_sonuc(
        kaynak="METAL_AYAR",
        taraf=taraf,
        birim=birim,
        feed_health=detay.feed_health,
        banner=detay.banner or "",
        urun_kod="",
        metal_kod=metal.kod,
        ayar_kodu=ayar_label,
        sonuc=sonuc,
    )
