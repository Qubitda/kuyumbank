"""PricingService.quote / lock_quote — Dilim 3.5–3.7 (ADR-0008 §2.4, ADR-0010).

Orkestrasyon: yayın → teklif seçimi → kur → sözleşme → hesap → immutable PriceQuote.
PriceLock: geçerli quote referansını kilitler; yeniden hesap yok; sipariş FK yok.
B-01 platform_servis yok. B-06 vergi yok.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.role_permissions import P
from firmalar.services.yetki_servisi import has_perm, is_platform_firm_user
from fiyatlama.models import (
    FiyatSozlesmesi,
    PriceLock,
    PriceQuote,
    PriceQuoteLine,
    TedarikciTeklif,
)
from fiyatlama.models.sozlesme_cozumleme import (
    CokluSozlesmeHatasi,
    SozlesmeYokHatasi,
    cozumle,
)
from fiyatlama.selectors.tenant import teklif_eslestirme_uygun_mu
from fiyatlama.services import fiyat_hesaplama, fiyat_motoru
from tanimlar.models import KurTaraf
from tanimlar.services import currency_conversion, kur_servisi

_ZERO = Decimal("0")


def _d(x) -> Decimal:
    if x is None:
        return _ZERO
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _assert_yayinli_varyant(varyant) -> None:
    urun = varyant.urun
    if getattr(urun, "yayin_durumu", None) != "aktif":
        raise ValidationError("Ürün yayında değil; quote üretilemez.")
    if getattr(urun, "onay_durumu", None) != "onayli":
        raise ValidationError("Ürün onaylı değil; quote üretilemez.")
    if not getattr(varyant, "aktif", True):
        raise ValidationError("Varyant aktif değil; quote üretilemez.")


def _teklif_gecerli_mi(teklif: TedarikciTeklif, *, bugun: date) -> bool:
    if teklif.durum != TedarikciTeklif.Durum.YAYINDA:
        return False
    if teklif.gecerlilik_baslangic is None or teklif.gecerlilik_bitis is None:
        return False
    if not (teklif.gecerlilik_baslangic <= bugun <= teklif.gecerlilik_bitis):
        return False
    return teklif_eslestirme_uygun_mu(teklif)


def _tas_toplami_try(teklif: TedarikciTeklif, *, now) -> tuple[Decimal, list[int]]:
    """Taş bedellerini TRY'ye çevir; gözlem id'lerini topla."""
    toplam = _ZERO
    gozlem_ids: list[int] = []
    for tas in teklif.taslar.all():
        pb = (tas.para_birimi or "TRY").upper()
        if pb == "TRY":
            toplam += _d(tas.bedel)
            continue
        conv = currency_conversion.to_try(
            tas.bedel,
            kaynak_pb=pb,
            taraf=KurTaraf.ALICI,
            now=now,
        )
        toplam += conv.tutar
        gozlem_ids.extend(conv.gozlem_idler)
    return toplam, gozlem_ids


def _cevir_try_hedefe(
    tutar_try: Decimal,
    *,
    hedef_pb: str,
    now,
) -> tuple[Decimal, list[int]]:
    if hedef_pb.upper() == "TRY":
        return _d(tutar_try), []
    conv = currency_conversion.convert(
        tutar_try,
        kaynak_pb="TRY",
        hedef_pb=hedef_pb,
        taraf=KurTaraf.ALICI,
        now=now,
    )
    return conv.tutar, list(conv.gozlem_idler)


def ic_maliyet_skoru(
    teklif: TedarikciTeklif,
    *,
    milyem: Decimal | None,
    metal_saf_try: Decimal | None,
    now,
) -> Decimal:
    """Seçim skoru (TRY). Alıcıya gösterilmez. Model bazlı iç maliyet."""
    gram = _d(teklif.gram)
    tas_try, _ = _tas_toplami_try(teklif, now=now)
    model = teklif.fiyat_modeli

    if model == TedarikciTeklif.FiyatModeli.METAL_BAZLI:
        if metal_saf_try is None or milyem is None:
            raise ValidationError(
                "METAL_BAZLI teklif seçimi için metal kuru / milyem gerekli."
            )
        metal = gram * _d(milyem) * _d(metal_saf_try)
        iscilik = (
            _d(teklif.iscilik_override)
            if teklif.iscilik_override is not None
            else _ZERO
        )
        return metal + iscilik + tas_try

    if model == TedarikciTeklif.FiyatModeli.GRAM_BIRIM:
        bf = _d(teklif.birim_fiyat)
        pb = (teklif.para_birimi or "TRY").upper()
        if pb != "TRY":
            conv = currency_conversion.to_try(
                bf, kaynak_pb=pb, taraf=KurTaraf.TEDARIKCI, now=now
            )
            bf = conv.tutar
        return gram * bf + tas_try

    if model == TedarikciTeklif.FiyatModeli.SABIT_PARCA:
        bf = _d(teklif.birim_fiyat)
        pb = (teklif.para_birimi or "TRY").upper()
        if pb != "TRY":
            conv = currency_conversion.to_try(
                bf, kaynak_pb=pb, taraf=KurTaraf.TEDARIKCI, now=now
            )
            bf = conv.tutar
        return bf + tas_try

    raise ValidationError(f"Bilinmeyen fiyat_modeli: {model}")


def _aday_teklifler(varyant, *, bugun: date):
    return list(
        TedarikciTeklif.objects.filter(
            varyant=varyant,
            durum=TedarikciTeklif.Durum.YAYINDA,
            gecerlilik_baslangic__lte=bugun,
            gecerlilik_bitis__gte=bugun,
            eslestirme_durumu="onaylandi",
            hedef_urun_id=varyant.urun_id,
        )
        .select_related("varyant", "varyant__urun", "varyant__urun__ayar")
        .prefetch_related("taslar")
    )


def sec_teklif(
    varyant,
    *,
    teklif_id: int | None = None,
    bugun: date | None = None,
    now=None,
    metal_saf_try: Decimal | None = None,
) -> TedarikciTeklif:
    """Çoklu YAYINDA: oncelik ↓ → iç maliyet ↑ → id ↑."""
    bugun = bugun or date.today()
    now = now or timezone.now()
    urun = varyant.urun
    milyem = getattr(getattr(urun, "ayar", None), "milyem", None)

    if teklif_id is not None:
        try:
            t = (
                TedarikciTeklif.objects.select_related(
                    "varyant", "varyant__urun", "varyant__urun__ayar"
                )
                .prefetch_related("taslar")
                .get(pk=teklif_id)
            )
        except TedarikciTeklif.DoesNotExist as exc:
            raise ValidationError({"teklif_id": "Teklif bulunamadı."}) from exc
        if t.varyant_id != varyant.pk:
            raise ValidationError({"teklif_id": "Teklif bu varyanta ait değil."})
        if not _teklif_gecerli_mi(t, bugun=bugun):
            raise ValidationError(
                {"teklif_id": "Teklif YAYINDA/geçerli/eşleşme onaylı değil."}
            )
        return t

    adaylar = [t for t in _aday_teklifler(varyant, bugun=bugun) if _teklif_gecerli_mi(t, bugun=bugun)]
    if not adaylar:
        raise ValidationError("Uygun yayında teklif yok; quote üretilemez.")

    scored: list[tuple[tuple, TedarikciTeklif]] = []
    for t in adaylar:
        maliyet = ic_maliyet_skoru(
            t, milyem=milyem, metal_saf_try=metal_saf_try, now=now
        )
        # oncelik ↓ (yüksek önce) → maliyet ↑ → id ↑
        scored.append(((-int(t.oncelik), maliyet, int(t.pk)), t))
    scored.sort(key=lambda x: x[0])
    return scored[0][1]


def _assert_ttl_vs_kur(ttl: int, gozlemler) -> None:
    """B-03: TTL ≤ kullanılan gözlemin sağlayıcı max gecikmesi."""
    max_list = []
    for g in gozlemler:
        if g is None:
            continue
        sag = getattr(g, "saglayici", None)
        if sag is not None:
            max_list.append(int(sag.max_gecikme_saniye))
    if not max_list:
        return
    limit = min(max_list)
    if ttl > limit:
        raise ValidationError(
            {
                "quote_ttl_saniye": (
                    f"Kanal TTL ({ttl}s) kur max gecikmesini ({limit}s) aşıyor; "
                    "quote üretilemez (B-03)."
                )
            }
        )


def _iscilik_coz(
    teklif: TedarikciTeklif,
    *,
    alici_kalem,
    tedarikci_kalem,
) -> Decimal:
    if teklif.iscilik_override is not None:
        return _d(teklif.iscilik_override)
    if tedarikci_kalem is not None:
        return _d(tedarikci_kalem.iscilik)
    return _d(alici_kalem.iscilik)


def quote(
    *,
    alici_firma,
    satis_kanali,
    varyant,
    kullanici=None,
    teklif_id: int | None = None,
    para_birimi: str = "TRY",
    hedef_toplam: Decimal | None = None,
    now=None,
) -> PriceQuote:
    """
    Proforma PriceQuote + Line üretir (immutable).

    Giriş: alıcı firma, satış kanalı, varyant; isteğe bağlı teklif_id.
    ADR-0014 KS-6: `hedef_toplam` verilirse toplam = hedef (platform
    `manage_sozlesme`); banka/GV quote'a girmez.
    """
    now = now or timezone.now()
    bugun = timezone.localdate(now) if timezone.is_aware(now) else now.date()
    hedef_pb = (para_birimi or "TRY").upper()

    _assert_yayinli_varyant(varyant)
    ttl = kur_servisi.kanal_quote_ttl_saniye(satis_kanali)

    urun = varyant.urun
    ayar = urun.ayar
    metal = ayar.metal if ayar is not None else None
    milyem = ayar.milyem if ayar is not None else None

    # Kurlar (B-05: alıcı + tedarikçi ayrı)
    metal_alici = None
    metal_tedarikci = None
    if metal is not None and getattr(metal, "gram_bazli", False):
        metal_alici = kur_servisi.resolve_metal_kuru(
            metal, taraf=KurTaraf.ALICI, now=now
        )
        metal_tedarikci = kur_servisi.resolve_metal_kuru(
            metal, taraf=KurTaraf.TEDARIKCI, now=now
        )

    teklif = sec_teklif(
        varyant,
        teklif_id=teklif_id,
        bugun=bugun,
        now=now,
        metal_saf_try=(
            _d(metal_tedarikci.saf_birim_fiyat) if metal_tedarikci else None
        ),
    )

    # ALICI sözleşme zorunlu
    try:
        alici_kalem = cozumle(
            firma=alici_firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            tarih=bugun,
            metal=metal,
            ayar=ayar,
            satis_kanali=satis_kanali,
        )
    except SozlesmeYokHatasi as exc:
        raise ValidationError(
            "Alıcı fiyat sözleşmesi çözülemedi; quote yok."
        ) from exc
    except CokluSozlesmeHatasi as exc:
        raise ValidationError(
            "Alıcı sözleşme belirsiz (eşit skor); quote yok."
        ) from exc

    alici_sozlesme = alici_kalem.sozlesme

    # TEDARIKCI sözleşme koşullu
    tedarikci_kalem = None
    tedarikci_sozlesme = None
    try:
        tedarikci_kalem = cozumle(
            firma=teklif.tedarikci,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.TEDARIKCI,
            tarih=bugun,
            metal=metal,
            ayar=ayar,
            satis_kanali=satis_kanali,
        )
        tedarikci_sozlesme = tedarikci_kalem.sozlesme
    except SozlesmeYokHatasi:
        tedarikci_kalem = None
        tedarikci_sozlesme = None
    except CokluSozlesmeHatasi as exc:
        raise ValidationError(
            "Tedarikçi sözleşme belirsiz (eşit skor); quote yok."
        ) from exc

    gram = teklif.gram if teklif.gram is not None else varyant.gram
    if gram is None and teklif.fiyat_modeli != TedarikciTeklif.FiyatModeli.SABIT_PARCA:
        raise ValidationError("Gram tanımlı değil; quote üretilemez.")

    tas_try, tas_fx_ids = _tas_toplami_try(teklif, now=now)
    ek_try = _d(varyant.ek_bedel)
    tas_hedef, tas_ids2 = _cevir_try_hedefe(tas_try, hedef_pb=hedef_pb, now=now)
    ek_hedef, ek_ids = _cevir_try_hedefe(ek_try, hedef_pb=hedef_pb, now=now)

    saf_birim_hedef = None
    metal_fx_ids: list[int] = []
    if teklif.fiyat_modeli == TedarikciTeklif.FiyatModeli.METAL_BAZLI:
        if metal_alici is None or milyem is None:
            raise ValidationError("METAL_BAZLI için metal kuru / ayar milyem zorunlu.")
        saf_try = _d(metal_alici.saf_birim_fiyat)
        saf_birim_hedef, metal_fx_ids = _cevir_try_hedefe(
            saf_try, hedef_pb=hedef_pb, now=now
        )

    iscilik = _iscilik_coz(
        teklif, alici_kalem=alici_kalem, tedarikci_kalem=tedarikci_kalem
    )
    iscilik_hedef, isc_ids = _cevir_try_hedefe(iscilik, hedef_pb=hedef_pb, now=now)

    doviz_ids = list(
        dict.fromkeys(tas_fx_ids + tas_ids2 + ek_ids + metal_fx_ids + isc_ids)
    )

    gozlemler = [metal_alici, metal_tedarikci]
    _assert_ttl_vs_kur(ttl, gozlemler)

    # Aktif sağlayıcı max (TTL assert — gözlem yoksa bile kanal TTL politikası)
    try:
        sag = kur_servisi.aktif_saglayici()
        if ttl > sag.max_gecikme_saniye:
            raise ValidationError(
                {
                    "quote_ttl_saniye": (
                        f"Kanal TTL ({ttl}s) aktif sağlayıcı max gecikmesini "
                        f"({sag.max_gecikme_saniye}s) aşıyor; quote yok (B-03)."
                    )
                }
            )
    except kur_servisi.KurYokError:
        # Döviz/metal gerekmeyen uç — yine de sağlayıcı beklenir (kur politikası)
        raise ValidationError("Aktif kur sağlayıcı yok; quote üretilemez.")

    maliyet_referans: dict[str, Any] | None = None
    quote_fiyat_modeli = teklif.fiyat_modeli

    if hedef_toplam is not None:
        # ADR-0014 KS-6 — platform hedef toplam → quote
        if kullanici is None or not (
            is_platform_firm_user(kullanici)
            and has_perm(kullanici, P["manage_sozlesme"])
        ):
            raise PermissionDenied(
                "HEDEF_TOPLAM quote için platform manage_sozlesme gerekir."
            )
        hedef_n = _d(hedef_toplam)
        if hedef_n <= 0:
            raise ValidationError({"hedef_toplam": "Pozitif olmalı."})
        if gram is None or _d(gram) <= 0:
            raise ValidationError("HEDEF_TOPLAM için gram zorunlu.")
        # Denetim: klasik model maliyeti (quote toplamına girmez)
        try:
            maliyet_referans = fiyat_motoru.hesapla_teklif_kalemleri(
                fiyat_modeli=teklif.fiyat_modeli,
                hedef_para_birimi=hedef_pb,
                gram=gram,
                milyem=milyem,
                saf_birim_fiyat=saf_birim_hedef,
                iscilik=iscilik_hedef,
                islcilik_dahil_mi=bool(alici_kalem.islcilik_dahil_mi),
                birim_fiyat=teklif.birim_fiyat,
                birim_fiyat_pb=teklif.para_birimi,
                marj_tipi=alici_kalem.marj_tipi,
                marj_degeri=alici_kalem.marj_degeri,
                tas_bedeli=tas_hedef,
                ek_bedel=ek_hedef,
                taraf=KurTaraf.ALICI,
                now=now,
            )
        except (ValidationError, ValueError):
            maliyet_referans = None
        sonuc = fiyat_hesaplama.hesapla_hedef_toplam(
            hedef_toplam=hedef_n,
            gram=_d(gram),
            para_birimi=hedef_pb,
        )
        quote_fiyat_modeli = "HEDEF_TOPLAM"
    else:
        sonuc = fiyat_motoru.hesapla_teklif_kalemleri(
            fiyat_modeli=teklif.fiyat_modeli,
            hedef_para_birimi=hedef_pb,
            gram=gram,
            milyem=milyem,
            saf_birim_fiyat=saf_birim_hedef,
            iscilik=iscilik_hedef,
            islcilik_dahil_mi=bool(alici_kalem.islcilik_dahil_mi),
            birim_fiyat=teklif.birim_fiyat,
            birim_fiyat_pb=teklif.para_birimi,
            marj_tipi=alici_kalem.marj_tipi,
            marj_degeri=alici_kalem.marj_degeri,
            tas_bedeli=tas_hedef,
            ek_bedel=ek_hedef,
            taraf=KurTaraf.ALICI,
            now=now,
        )
        if sonuc.get("pb_donusum"):
            doviz_ids.extend(sonuc["pb_donusum"].get("birim_fiyat_gozlem_idler") or [])
            doviz_ids = list(dict.fromkeys(doviz_ids))

    gecerlilik_sonu = now + timedelta(seconds=ttl)
    alici_kur_tipi = kur_servisi.tarafa_kur_tipi(KurTaraf.ALICI)
    tedarikci_kur_tipi = kur_servisi.tarafa_kur_tipi(KurTaraf.TEDARIKCI)

    hesap_girdisi: dict[str, Any] = {
        "fiyat_modeli": quote_fiyat_modeli,
        "teklif_fiyat_modeli": teklif.fiyat_modeli,
        "gram": str(gram) if gram is not None else None,
        "milyem": str(milyem) if milyem is not None else None,
        "marj_tipi": alici_kalem.marj_tipi,
        "marj_degeri": str(alici_kalem.marj_degeri),
        "islcilik_dahil_mi": bool(alici_kalem.islcilik_dahil_mi),
        "teklif_id": teklif.pk,
        "teklif_versiyon": teklif.versiyon,
        "alici_kalem_id": alici_kalem.pk,
        "tedarikci_kalem_id": tedarikci_kalem.pk if tedarikci_kalem else None,
        "kalemler_ham": {k: str(v) for k, v in sonuc["kalemler"].items()},
        "toplam_vergisiz": str(sonuc["toplam_vergisiz"]),
        "belge_turu": "PROFORMA",
        "platform_servis": None,  # B-01 kodlanmadı
        "vergi": None,  # B-06 yok
        "banka_gv_isletme": None,  # KS-4: simülasyon dışı
    }
    if hedef_toplam is not None and gram is not None:
        hesap_girdisi["hedef_toplam"] = str(_d(hedef_toplam))
        hesap_girdisi["gr_satis_ortuk"] = str(
            (_d(hedef_toplam) / _d(gram)).quantize(Decimal("0.01"))
        )
        if maliyet_referans is not None:
            hesap_girdisi["maliyet_referans_toplam"] = str(
                maliyet_referans["toplam_vergisiz"]
            )

    with domain_atomic():
        pq = PriceQuote(
            alici_firma=alici_firma,
            satis_kanali=satis_kanali,
            varyant=varyant,
            teklif=teklif,
            teklif_versiyon=teklif.versiyon,
            fiyat_modeli=quote_fiyat_modeli,
            alici_sozlesme=alici_sozlesme,
            alici_sozlesme_versiyon=alici_sozlesme.versiyon,
            alici_kalem=alici_kalem,
            tedarikci_sozlesme=tedarikci_sozlesme,
            tedarikci_sozlesme_versiyon=(
                tedarikci_sozlesme.versiyon if tedarikci_sozlesme else None
            ),
            tedarikci_kalem=tedarikci_kalem,
            para_birimi=hedef_pb,
            toplam_vergisiz=sonuc["toplam_vergisiz"],
            gram=gram,
            gecerlilik_sonu=gecerlilik_sonu,
            hesap_zamani=now,
            quote_ttl_saniye=ttl,
            alici_kur_tipi=alici_kur_tipi,
            tedarikci_kur_tipi=tedarikci_kur_tipi,
            metal_kuru_alici=metal_alici,
            metal_kuru_tedarikci=metal_tedarikci,
            doviz_gozlem_idler=doviz_ids,
            hesap_girdisi=hesap_girdisi,
            belge_turu=PriceQuote.BelgeTuru.PROFORMA,
            olusturan=kullanici,
        )
        pq.save()

        sira = 0
        for tip, tutar in sonuc["kalemler_yuvarlanmis"].items():
            if tip not in PriceQuoteLine.KalemTipi.values:
                continue
            if _d(tutar) == _ZERO and tip not in (
                PriceQuoteLine.KalemTipi.KANAL_MARJ,
                PriceQuoteLine.KalemTipi.TAS,
                PriceQuoteLine.KalemTipi.EK_BEDEL,
            ):
                # sıfır ana kalemler de yazılır (denetim); sıfır opsiyoneller atlanabilir
                pass
            PriceQuoteLine(
                quote=pq,
                kalem_tipi=tip,
                tutar=_d(tutar),
                sira=sira,
                meta={},
            ).save()
            sira += 1

        if kullanici is not None:
            record_audit(
                actor=kullanici,
                action="price_quote.create",
                entity_type="PriceQuote",
                entity_id=str(pq.pk),
                success=True,
                detail={
                    "alici_firma_id": alici_firma.pk,
                    "varyant_id": varyant.pk,
                    "teklif_id": teklif.pk,
                    "toplam_vergisiz": str(pq.toplam_vergisiz),
                    "para_birimi": hedef_pb,
                },
            )

    return pq


ON_BEHALF_GEREKCE_MIN_LEN = 10


def _resolve_lock_mode(kullanici, quote: PriceQuote) -> str:
    """L-07: 'on_behalf' | 'buyer'. view_all_tenants create yetkisi vermez."""
    if kullanici is None or not getattr(kullanici, "is_authenticated", False):
        raise PermissionDenied("PriceLock için kimlik doğrulama gerekli.")

    if is_platform_firm_user(kullanici) and has_perm(
        kullanici, P["lock_quote_on_behalf"]
    ):
        return "on_behalf"

    firma = getattr(kullanici, "firma", None)
    firma_id = getattr(kullanici, "firma_id", None)
    if firma is None or not firma_id:
        raise PermissionDenied("PriceLock için firma bağlamı gerekli.")
    if getattr(firma, "tedarikci_mi", False) and not getattr(firma, "alici_mi", False):
        raise PermissionDenied("Tedarikçi PriceLock oluşturamaz.")
    if (
        getattr(firma, "alici_mi", False)
        and firma_id == quote.alici_firma_id
        and has_perm(kullanici, P["lock_quote"])
    ):
        return "buyer"
    raise PermissionDenied("Bu PriceQuote için kilit yetkisi yok.")


def _normalize_on_behalf_gerekce(gerekce: str | None) -> str:
    return (gerekce or "").strip()


def sync_lock_expiration(lock: PriceLock, *, now=None) -> PriceLock:
    """AKTIF + süre dolmuş → SURESI_DOLDU (L-05). Testte `now` enjekte edilir."""
    now = now or timezone.now()
    if lock.durum != PriceLock.Durum.AKTIF:
        return lock
    if now < lock.gecerlilik_sonu:
        return lock

    with domain_atomic():
        locked = (
            PriceLock.objects.select_for_update()
            .filter(pk=lock.pk, durum=PriceLock.Durum.AKTIF)
            .first()
        )
        if locked is None:
            lock.refresh_from_db()
            return lock
        if now < locked.gecerlilik_sonu:
            return locked
        locked.durum = PriceLock.Durum.SURESI_DOLDU
        locked._allow_expire_transition = True
        try:
            locked.save(update_fields=["durum"])
        finally:
            locked._allow_expire_transition = False
        record_audit(
            actor=None,
            action="price_lock.expire",
            entity_type="PriceLock",
            entity_id=str(locked.pk),
            success=True,
            detail={
                "quote_id": locked.quote_id,
                "gecerlilik_sonu": locked.gecerlilik_sonu.isoformat(),
                "now": now.isoformat(),
            },
        )
    lock.refresh_from_db()
    return lock


def is_lock_gecerli(lock: PriceLock, *, now=None) -> bool:
    """Süre/durum tutarlılığı: gerekirse expire senkronlar, sonra geçerlilik."""
    now = now or timezone.now()
    sync_lock_expiration(lock, now=now)
    lock.refresh_from_db()
    return lock.is_gecerli(now=now)


def assert_lock_gecerli(lock: PriceLock, *, now=None) -> PriceLock:
    if not is_lock_gecerli(lock, now=now):
        raise ValidationError("PriceLock aktif/geçerli değil.")
    return lock


def lock_quote(
    quote: PriceQuote,
    *,
    kullanici,
    now=None,
    idempotency_key: str | None = None,
    gerekce: str | None = None,
) -> PriceLock:
    """
    Geçerli PriceQuote için PriceLock üretir (yeniden hesap yok).

    Idempotent: aynı quote tekrar kilitlenirse mevcut satır döner.
    Sipariş FK yok (Faz 4).
    L-07: buyer → lock_quote; platform → lock_quote_on_behalf + gerekçe.
    """
    now = now or timezone.now()
    key = (idempotency_key or "").strip() or None
    on_behalf = False
    gerekce_trimmed: str | None = None

    try:
        mode = _resolve_lock_mode(kullanici, quote)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=kullanici,
            action="price_lock.create",
            entity_type="PriceQuote",
            entity_id=str(getattr(quote, "pk", "") or ""),
            success=False,
            reason=str(exc),
            detail={"alici_firma_id": getattr(quote, "alici_firma_id", None)},
        )
        raise

    if mode == "on_behalf":
        on_behalf = True
        gerekce_trimmed = _normalize_on_behalf_gerekce(gerekce)
        if len(gerekce_trimmed) < ON_BEHALF_GEREKCE_MIN_LEN:
            record_audit_durable(
                actor=kullanici,
                action="price_lock.create",
                entity_type="PriceQuote",
                entity_id=str(quote.pk),
                success=False,
                reason=(
                    "On-behalf PriceLock için gerekçe en az "
                    f"{ON_BEHALF_GEREKCE_MIN_LEN} karakter olmalıdır."
                ),
                detail={
                    "alici_firma_id": quote.alici_firma_id,
                    "on_behalf": True,
                    "gerekce_len": len(gerekce_trimmed),
                },
            )
            raise ValidationError(
                "On-behalf PriceLock için gerekçe en az "
                f"{ON_BEHALF_GEREKCE_MIN_LEN} karakter olmalıdır."
            )

    if quote.gecerlilik_sonu <= now:
        record_audit_durable(
            actor=kullanici,
            action="price_lock.create",
            entity_type="PriceQuote",
            entity_id=str(quote.pk),
            success=False,
            reason="Quote süresi dolmuş; kilit üretilemez.",
            detail={
                "gecerlilik_sonu": quote.gecerlilik_sonu.isoformat(),
                "on_behalf": on_behalf,
            },
        )
        raise ValidationError("Quote süresi dolmuş; kilit üretilemez.")

    def _return_or_reject_existing(lock: PriceLock) -> PriceLock:
        sync_lock_expiration(lock, now=now)
        lock.refresh_from_db()
        if lock.is_gecerli(now=now):
            return lock
        raise ValidationError(
            "Bu quote için kilit süresi dolmuş; yeni quote gerekli."
        )

    if key is not None:
        existing_key = PriceLock.objects.filter(
            alici_firma_id=quote.alici_firma_id,
            idempotency_key=key,
        ).first()
        if existing_key is not None:
            if existing_key.quote_id != quote.pk:
                raise ValidationError(
                    {
                        "idempotency_key": (
                            "Bu anahtar başka bir quote kilidine bağlı."
                        )
                    }
                )
            try:
                return _return_or_reject_existing(existing_key)
            except ValidationError as exc:
                record_audit_durable(
                    actor=kullanici,
                    action="price_lock.create",
                    entity_type="PriceQuote",
                    entity_id=str(quote.pk),
                    success=False,
                    reason=str(exc),
                    detail={"on_behalf": on_behalf},
                )
                raise

    # Fast path: mevcut kilit (expire senkronu create atomic dışında)
    mevcut_dis = PriceLock.objects.filter(quote_id=quote.pk).first()
    if mevcut_dis is not None:
        try:
            return _return_or_reject_existing(mevcut_dis)
        except ValidationError as exc:
            record_audit_durable(
                actor=kullanici,
                action="price_lock.create",
                entity_type="PriceQuote",
                entity_id=str(quote.pk),
                success=False,
                reason=str(exc),
                detail={"on_behalf": on_behalf},
            )
            raise

    try:
        with domain_atomic():
            # Quote satır kilidi — eşzamanlı lock yarışını serileştir
            pq = (
                PriceQuote.objects.select_for_update()
                .select_related("alici_firma")
                .get(pk=quote.pk)
            )
            if pq.gecerlilik_sonu <= now:
                raise ValidationError("Quote süresi dolmuş; kilit üretilemez.")

            mevcut = (
                PriceLock.objects.select_for_update()
                .filter(quote_id=pq.pk)
                .first()
            )
            if mevcut is not None:
                # Başka işlem kazandı; expire yazma (outer rollback riski yok —
                # yalnızca okuma + karar). Expire atomic dışında yapılır.
                if (
                    mevcut.durum == PriceLock.Durum.AKTIF
                    and now < mevcut.gecerlilik_sonu
                ):
                    return mevcut
                raise ValidationError(
                    "Bu quote için kilit süresi dolmuş; yeni quote gerekli."
                )

            lock = PriceLock(
                quote=pq,
                alici_firma_id=pq.alici_firma_id,
                toplam_vergisiz=pq.toplam_vergisiz,
                para_birimi=pq.para_birimi,
                kilit_zamani=now,
                gecerlilik_sonu=pq.gecerlilik_sonu,
                durum=PriceLock.Durum.AKTIF,
                idempotency_key=key,
                olusturan=kullanici,
            )
            lock.save()
            audit_detail = {
                "quote_id": pq.pk,
                "alici_firma_id": pq.alici_firma_id,
                "toplam_vergisiz": str(lock.toplam_vergisiz),
                "para_birimi": lock.para_birimi,
                "gecerlilik_sonu": lock.gecerlilik_sonu.isoformat(),
                "idempotency_key": key,
                "on_behalf": on_behalf,
                "kilit_zamani": lock.kilit_zamani.isoformat(),
                "actor_id": getattr(kullanici, "pk", None),
            }
            if on_behalf:
                audit_detail["gerekce"] = gerekce_trimmed
            record_audit(
                actor=kullanici,
                action="price_lock.create",
                entity_type="PriceLock",
                entity_id=str(lock.pk),
                success=True,
                detail=audit_detail,
            )
            return lock
    except IntegrityError:
        mevcut = PriceLock.objects.filter(quote_id=quote.pk).first()
        if mevcut is not None:
            return _return_or_reject_existing(mevcut)
        if key is not None:
            mevcut = PriceLock.objects.filter(
                alici_firma_id=quote.alici_firma_id,
                idempotency_key=key,
            ).first()
            if mevcut is not None:
                return _return_or_reject_existing(mevcut)
        raise
    except ValidationError as exc:
        # Yarışta süresi dolmuş kilit görüldüyse durum senkronunu atomic dışında yap
        stale = PriceLock.objects.filter(quote_id=quote.pk).first()
        if stale is not None:
            sync_lock_expiration(stale, now=now)
        record_audit_durable(
            actor=kullanici,
            action="price_lock.create",
            entity_type="PriceQuote",
            entity_id=str(quote.pk),
            success=False,
            reason=str(exc),
            detail={"on_behalf": on_behalf},
        )
        raise

