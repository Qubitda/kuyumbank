"""Piyasa panosu baz fiyat + iç işlem fiyat seçimi (ADR-0020 / ADR-0022)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.utils import timezone

from firmalar.services.yetki_servisi import has_perm, require_perm
from tanimlar.models import KurTaraf
from tanimlar.services import kur_servisi

from piyasa.models import DarphaneIscilik, PiyasaMarjPolitikasi, PiyasaUrun
from piyasa.services import hesap

P_MANAGE = "piyasa.manage_piyasa"

KAYNAK_PANO = "PANO"
KAYNAK_MANUEL = "MANUEL"
KAYNAKLAR = frozenset({KAYNAK_PANO, KAYNAK_MANUEL})

_TARAFA_KUR = {
    hesap.ALIS: KurTaraf.TEDARIKCI,
    hesap.SATIS: KurTaraf.ALICI,
}


def _require_manage(actor):
    require_perm(actor, P_MANAGE, message="Piyasa panosu yetkisi yok.")


def get_marj_modu() -> str:
    pol, _ = PiyasaMarjPolitikasi.objects.get_or_create(
        anahtar="default",
        defaults={"marj_modu": PiyasaMarjPolitikasi.MarjModu.YUZDE},
    )
    return pol.marj_modu


def set_marj_modu(modu: str, *, actor=None) -> PiyasaMarjPolitikasi:
    if actor is not None:
        _require_manage(actor)
    modu = (modu or "").upper()
    if modu not in {PiyasaMarjPolitikasi.MarjModu.TL, PiyasaMarjPolitikasi.MarjModu.YUZDE}:
        raise ValidationError({"marj_modu": f"Geçersiz marj modu: {modu!r}."})
    pol, _ = PiyasaMarjPolitikasi.objects.get_or_create(anahtar="default")
    pol.marj_modu = modu
    pol.save(update_fields=["marj_modu", "guncelleme"])
    return pol


def _usd_try_for(taraf: str, *, now) -> Decimal | None:
    """USD çıktı için TRY/USD; yoksa None (çağıran hata verir)."""
    try:
        goz = kur_servisi.resolve_doviz_kuru("USD", taraf=_TARAFA_KUR[taraf], now=now)
    except (kur_servisi.KurYokError, kur_servisi.KurStaleError):
        return None
    return goz.kur


def _taraf_hesap(urun: PiyasaUrun, taraf: str, *, now, marj_modu: str) -> dict[str, Any]:
    taraf_kur = _TARAFA_KUR[taraf]
    detay = kur_servisi.resolve_metal_kuru_detay(
        urun.metal, taraf=taraf_kur, now=now
    )
    saf = detay.gozlem.saf_birim_fiyat
    usd_try = None
    if urun.cikti_pb == PiyasaUrun.CiktiPb.USD:
        usd_try = _usd_try_for(taraf, now=now)
        if usd_try is None:
            raise ValidationError(
                f"USD panosu için USDTRY yok/stale: {urun.kod}."
            )
    sonuc = hesap.hesapla_taraf(
        taraf=taraf,
        saf_birim_fiyat=saf,
        milyem=urun.etkin_milyem,
        gram=urun.gram,
        marj_modu=marj_modu,
        alis_marj=urun.alis_marj,
        satis_marj=urun.satis_marj,
        yuvarlama_adimi=urun.yuvarlama_adimi,
        yuvarlama_yontemi=urun.yuvarlama_yontemi,
        olcek=urun.olcek,
        cikti_pb=urun.cikti_pb,
        usd_try=usd_try,
    )
    sonuc["saf_birim_fiyat"] = saf
    sonuc["milyem"] = urun.etkin_milyem
    sonuc["gram"] = urun.gram
    sonuc["usd_try"] = usd_try
    sonuc["feed_health"] = detay.feed_health
    sonuc["banner"] = detay.banner
    sonuc["gozlem_id"] = detay.gozlem.pk
    return sonuc


def hesapla_urun(urun: PiyasaUrun, *, now=None, marj_modu: str | None = None) -> dict[str, Any]:
    now = now or timezone.now()
    modu = marj_modu or get_marj_modu()
    out: dict[str, Any] = {
        "ok": True,
        "kod": urun.kod,
        "ad": urun.ad,
        "grup": urun.grup,
        "varyant_etiket": urun.varyant_etiket or "",
        "olcek": urun.olcek,
        "cikti_pb": urun.cikti_pb,
        "marj_modu": modu,
        "alis_marj": urun.alis_marj,
        "satis_marj": urun.satis_marj,
        "alis": None,
        "satis": None,
        "alis_detay": None,
        "satis_detay": None,
        "guncelleme": now,
        "feed_health": "",
        "banner": "",
        "hata": "",
    }
    try:
        banners = []
        healths = []
        for taraf, key in ((hesap.ALIS, "alis"), (hesap.SATIS, "satis")):
            det = _taraf_hesap(urun, taraf, now=now, marj_modu=modu)
            out[key] = det["nihai"]
            out[f"{key}_detay"] = det
            healths.append(det["feed_health"])
            if det["banner"]:
                banners.append(det["banner"])
        out["feed_health"] = healths[0] if healths else ""
        out["banner"] = " | ".join(dict.fromkeys(banners))
    except (kur_servisi.KurYokError, kur_servisi.KurStaleError, ValidationError, ValueError) as exc:
        out["ok"] = False
        out["hata"] = str(exc)
    return out


def baz_fiyat(urun_kod: str, *, now=None) -> dict[str, Any]:
    urun = PiyasaUrun.objects.select_related("metal", "ayar").get(
        kod=urun_kod, aktif=True
    )
    sonuc = hesapla_urun(urun, now=now)
    if not sonuc["ok"]:
        raise ValidationError(sonuc["hata"] or "Piyasa fiyatı çözülemedi.")
    return {
        "kod": urun.kod,
        "grup": urun.grup,
        "varyant_etiket": urun.varyant_etiket or "",
        "olcek": urun.olcek,
        "cikti_pb": urun.cikti_pb,
        "marj_modu": sonuc["marj_modu"],
        "alis": sonuc["alis"],
        "satis": sonuc["satis"],
        "guncelleme": sonuc["guncelleme"],
        "feed_health": sonuc["feed_health"],
        "banner": sonuc["banner"],
        "alis_detay": sonuc["alis_detay"],
        "satis_detay": sonuc["satis_detay"],
    }


def pano_ozeti(*, only_aktif: bool = True, now=None) -> list[dict[str, Any]]:
    qs = PiyasaUrun.objects.select_related("metal", "ayar").order_by(
        "grup", "sira", "kod"
    )
    if only_aktif:
        qs = qs.filter(aktif=True)
    modu = get_marj_modu()
    return [hesapla_urun(u, now=now, marj_modu=modu) for u in qs]


def darphane_iscilik_listesi(*, only_aktif: bool = True) -> list[dict[str, Any]]:
    qs = DarphaneIscilik.objects.select_related("urun").order_by(
        "sira", "urun__sira", "kanal"
    )
    if only_aktif:
        qs = qs.filter(aktif=True, urun__aktif=True)
    return [
        {
            "urun_kod": row.urun.kod,
            "urun_ad": row.urun.ad,
            "kanal": row.kanal,
            "iscilik_tl": row.iscilik_tl,
            "sira": row.sira,
        }
        for row in qs
    ]


def cozumle_islem_birim_fiyati(
    *,
    kaynak: str,
    taraf: str,
    urun_kod: str | None = None,
    manuel_birim_fiyat=None,
    kullanici_ekleri: dict | None = None,
    agirlik_gr=Decimal("1"),
    now=None,
) -> dict[str, Any]:
    kaynak = (kaynak or "").upper()
    taraf = (taraf or "").upper()
    if kaynak not in KAYNAKLAR:
        raise ValidationError({"kaynak": f"Geçersiz kaynak: {kaynak!r} (PANO|MANUEL)."})
    if taraf not in hesap.TARAFLAR:
        raise ValidationError({"taraf": f"Geçersiz taraf: {taraf!r}."})

    banner = ""
    feed_health = ""
    kod = urun_kod or ""

    if kaynak == KAYNAK_MANUEL:
        if manuel_birim_fiyat is None:
            raise ValidationError(
                {"manuel_birim_fiyat": "MANUEL kaynakta birim fiyat zorunlu."}
            )
        birim = Decimal(str(manuel_birim_fiyat))
        if birim <= 0:
            raise ValidationError(
                {"manuel_birim_fiyat": "Manuel birim fiyat sıfırdan büyük olmalı."}
            )
    else:
        if not urun_kod:
            raise ValidationError({"urun_kod": "PANO kaynakta urun_kod zorunlu."})
        baz = baz_fiyat(urun_kod, now=now)
        birim = baz["alis"] if taraf == hesap.ALIS else baz["satis"]
        if birim is None:
            raise ValidationError(f"Pano {taraf} fiyatı yok: {urun_kod}.")
        banner = baz.get("banner") or ""
        feed_health = baz.get("feed_health") or ""
        kod = baz["kod"]

    ekler = kullanici_ekleri or {}
    if any(ekler.get(k) for k in ("iscilik", "servis_bedeli", "marj")):
        katman2 = hesap.kullanici_fiyati(
            baz_birim_fiyat=birim,
            agirlik_gr=agirlik_gr,
            iscilik=ekler.get("iscilik"),
            servis_bedeli=ekler.get("servis_bedeli"),
            marj=ekler.get("marj"),
        )
        etkin_birim = katman2["birim_toplam"]
    else:
        katman2 = None
        etkin_birim = Decimal(str(birim)).quantize(hesap.HASSASIYET)

    return {
        "kaynak": kaynak,
        "taraf": taraf,
        "urun_kod": kod,
        "baz_birim": Decimal(str(birim)).quantize(hesap.HASSASIYET),
        "etkin_birim": etkin_birim,
        "agirlik_gr": Decimal(str(agirlik_gr)).quantize(hesap.HASSASIYET),
        "katman2": katman2,
        "feed_health": feed_health,
        "banner": banner,
    }


def actor_manage_piyasa_mi(user) -> bool:
    return has_perm(user, P_MANAGE)
