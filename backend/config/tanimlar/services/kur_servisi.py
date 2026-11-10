"""Kur politikası servisi (ADR-0008 Dilim 3.3 / K-019 + ADR-0018 CAP-PIYASA).

Resolve: tek aktif anlık sağlayıcı; soft provider hop yok.
Stale: sessiz LKG yasak — FEED_STALE_LKG + banner ile LKG kullanılabilir.
Manuel giriş: neden + dört göz + audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from firmalar.services.audit_servisi import domain_atomic, record_audit, record_audit_durable
from firmalar.services.yetki_servisi import require_perm
from tanimlar.fiyat_kaynagi import FeedHealth, FiyatKaynagi

from tanimlar.models import (
    DovizKuru,
    KurPolitikasi,
    KurSaglayici,
    KurTaraf,
    KurTipi,
    MetalKuru,
    SatisKanali,
)

P_MANAGE_KUR = "tanimlar.manage_kur"


class KurStaleError(ValidationError):
    """Gözlem max gecikmeyi aştı — sessiz fiyat yok."""


class KurYokError(ValidationError):
    """Aktif sağlayıcıda geçerli gözlem yok."""


def _deny(kullanici, *, action, entity_type, entity_id, exc, reason, detail=None):
    record_audit_durable(
        actor=kullanici,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _require_manage(kullanici, *, action, entity_type="KurSaglayici", entity_id=""):
    try:
        require_perm(
            kullanici,
            P_MANAGE_KUR,
            message="Kur yönetim yetkiniz yok.",
        )
    except PermissionDenied as exc:
        _deny(
            kullanici,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            exc=exc,
            reason="yetki_yok",
        )


def get_or_create_politikasi() -> KurPolitikasi:
    obj, _ = KurPolitikasi.objects.get_or_create(
        anahtar="default",
        defaults={
            "alici_kur_tipi": KurTipi.SATIS,
            "tedarikci_kur_tipi": KurTipi.ALIS,
            "fiyat_kaynagi": FiyatKaynagi.CANLI_PIYASA,
            "feed_health": FeedHealth.FEED_OK,
        },
    )
    return obj


def set_feed_health(
    *,
    health: str,
    banner: str = "",
) -> KurPolitikasi:
    """Feed health yüzeyi (LKG/banner); soft uydurma yok."""
    if health not in {c[0] for c in FeedHealth.CHOICES}:
        raise ValidationError({"feed_health": "Geçersiz feed_health."})
    pol = get_or_create_politikasi()
    pol.feed_health = health
    pol.feed_banner = (banner or "")[:255]
    pol.save(update_fields=["feed_health", "feed_banner", "guncelleme"])
    return pol


@dataclass(frozen=True)
class MetalKurResolve:
    gozlem: MetalKuru
    feed_health: str
    banner: str
    is_lkg: bool
    etkin_kaynak: str


def aktif_saglayici() -> KurSaglayici:
    try:
        return KurSaglayici.objects.get(aktif=True)
    except KurSaglayici.DoesNotExist as exc:
        raise KurYokError("Aktif kur sağlayıcı yok.") from exc


def gozlem_stale_mi(gozlem, *, now=None, max_gecikme_saniye: int | None = None) -> bool:
    """True = kullanılamaz (feed gecikmesi veya yaş)."""
    now = now or timezone.now()
    max_g = max_gecikme_saniye
    if max_g is None:
        max_g = gozlem.saglayici.max_gecikme_saniye
    if max_g <= 0:
        return True
    limit = timedelta(seconds=max_g)
    if gozlem.alinma_zamani - gozlem.zaman > limit:
        return True
    if now - gozlem.zaman > limit:
        return True
    return False


def _assert_ingest_fresh(*, zaman, alinma_zamani, max_gecikme_saniye: int):
    if alinma_zamani - zaman > timedelta(seconds=max_gecikme_saniye):
        raise KurStaleError(
            "Kur alınma gecikmesi sağlayıcı max gecikmesini aşıyor; kayıt reddedildi."
        )


def tarafa_kur_tipi(taraf: str) -> str:
    pol = get_or_create_politikasi()
    if taraf == KurTaraf.ALICI:
        return pol.alici_kur_tipi
    if taraf == KurTaraf.TEDARIKCI:
        return pol.tedarikci_kur_tipi
    raise ValidationError({"taraf": f"Geçersiz kur tarafı: {taraf}"})


def kanal_quote_ttl_saniye(kanal: SatisKanali) -> int:
    """B-03: değer yoksa quote yok (3.5 fail-closed)."""
    if kanal.quote_ttl_saniye is None:
        raise ValidationError(
            {"quote_ttl_saniye": "Kanal quote TTL tanımlı değil; quote üretilemez."}
        )
    return kanal.quote_ttl_saniye


@transaction.atomic
def aktif_saglayici_ayarla(kullanici, saglayici_id: int) -> KurSaglayici:
    """Tek aktif provider; diğerlerini kapatır. Otomatik fallback yok."""
    _require_manage(kullanici, action="kur.saglayici_aktif", entity_id=saglayici_id)
    hedef = KurSaglayici.objects.select_for_update().get(pk=saglayici_id)
    KurSaglayici.objects.select_for_update().filter(aktif=True).exclude(
        pk=hedef.pk
    ).update(aktif=False)
    if not hedef.aktif:
        hedef.aktif = True
        hedef.save(update_fields=["aktif", "guncelleme"])
    record_audit(
        actor=kullanici,
        action="kur.saglayici_aktif",
        entity_type="KurSaglayici",
        entity_id=str(hedef.pk),
        success=True,
        detail={"kod": hedef.kod},
    )
    return hedef


def politikayi_guncelle(
    kullanici,
    *,
    alici_kur_tipi: str,
    tedarikci_kur_tipi: str,
) -> KurPolitikasi:
    _require_manage(kullanici, action="kur.politika_guncelle", entity_type="KurPolitikasi")
    if alici_kur_tipi not in KurTipi.values:
        raise ValidationError({"alici_kur_tipi": "Geçersiz kur tipi."})
    if tedarikci_kur_tipi not in KurTipi.values:
        raise ValidationError({"tedarikci_kur_tipi": "Geçersiz kur tipi."})
    with domain_atomic():
        pol = get_or_create_politikasi()
        pol.alici_kur_tipi = alici_kur_tipi
        pol.tedarikci_kur_tipi = tedarikci_kur_tipi
        pol.save()
        record_audit(
            actor=kullanici,
            action="kur.politika_guncelle",
            entity_type="KurPolitikasi",
            entity_id=str(pol.pk),
            success=True,
            detail={
                "alici_kur_tipi": alici_kur_tipi,
                "tedarikci_kur_tipi": tedarikci_kur_tipi,
            },
        )
    return pol


def resolve_metal_kuru(
    metal, *, taraf: str, now=None, etkin_kaynak: str | None = None
) -> MetalKuru:
    """Geriye uyumlu: detaylı resolve'un gözlemi. Stale+LKG → gözlem döner (banner politika)."""
    return resolve_metal_kuru_detay(
        metal, taraf=taraf, now=now, etkin_kaynak=etkin_kaynak
    ).gozlem


def resolve_metal_kuru_detay(
    metal,
    *,
    taraf: str,
    now=None,
    etkin_kaynak: str | None = None,
) -> MetalKurResolve:
    """ADR-0018: CANLI → api; stale → LKG+banner; MANUEL → manuel kaynak; 0 fiyat yok."""
    now = now or timezone.now()
    kaynak = (etkin_kaynak or FiyatKaynagi.CANLI_PIYASA).strip()
    kur_tipi = tarafa_kur_tipi(taraf)
    metal_id = metal.pk if hasattr(metal, "pk") else metal

    if kaynak == FiyatKaynagi.MANUEL_GIRIS:
        gozlem = (
            MetalKuru.objects.filter(
                metal_id=metal_id,
                kur_tipi=kur_tipi,
                kaynak="manuel",
            )
            .select_related("saglayici", "metal")
            .order_by("-zaman", "-pk")
            .first()
        )
        if gozlem is None or gozlem.saf_birim_fiyat <= 0:
            set_feed_health(
                health=FeedHealth.FEED_FAIL,
                banner="Manuel metal kuru yok.",
            )
            raise KurYokError("Manuel metal kuru yok.")
        set_feed_health(
            health=FeedHealth.FEED_LOCKED_MANUEL,
            banner="Manuel kur kilidi aktif.",
        )
        return MetalKurResolve(
            gozlem=gozlem,
            feed_health=FeedHealth.FEED_LOCKED_MANUEL,
            banner="Manuel kur kilidi aktif.",
            is_lkg=False,
            etkin_kaynak=kaynak,
        )

    # CANLI_PIYASA — tek aktif anlık sağlayıcı; soft hop yok
    saglayici = aktif_saglayici()
    qs = (
        MetalKuru.objects.filter(
            metal_id=metal_id,
            saglayici=saglayici,
            kur_tipi=kur_tipi,
            kaynak__in=["api", "websocket", "tcmb"],
        )
        .select_related("saglayici", "metal")
        .order_by("-zaman", "-pk")
    )
    gozlem = qs.first()
    if gozlem is None or gozlem.saf_birim_fiyat <= 0:
        set_feed_health(
            health=FeedHealth.FEED_FAIL,
            banner="Canlı metal kuru yok.",
        )
        raise KurYokError(
            f"Metal kuru yok (sağlayıcı={saglayici.kod}, tip={kur_tipi})."
        )
    if not gozlem_stale_mi(gozlem, now=now):
        set_feed_health(health=FeedHealth.FEED_OK, banner="")
        return MetalKurResolve(
            gozlem=gozlem,
            feed_health=FeedHealth.FEED_OK,
            banner="",
            is_lkg=False,
            etkin_kaynak=kaynak,
        )

    # Stale → LKG = son bilinen gözlem; sessiz yasak — banner zorunlu (CP-3)
    banner = (
        f"Kur stale; LKG kullanılıyor (gözlem=#{gozlem.pk}, "
        f"max={saglayici.max_gecikme_saniye}s)."
    )
    set_feed_health(health=FeedHealth.FEED_STALE_LKG, banner=banner)
    return MetalKurResolve(
        gozlem=gozlem,
        feed_health=FeedHealth.FEED_STALE_LKG,
        banner=banner,
        is_lkg=True,
        etkin_kaynak=kaynak,
    )


def resolve_doviz_kuru(para_birimi: str, *, taraf: str, now=None) -> DovizKuru:
    now = now or timezone.now()
    saglayici = aktif_saglayici()
    kur_tipi = tarafa_kur_tipi(taraf)
    gozlem = (
        DovizKuru.objects.filter(
            para_birimi=para_birimi,
            saglayici=saglayici,
            kur_tipi=kur_tipi,
        )
        .select_related("saglayici")
        .order_by("-zaman", "-pk")
        .first()
    )
    if gozlem is None:
        raise KurYokError(
            f"Döviz kuru yok (sağlayıcı={saglayici.kod}, tip={kur_tipi}, {para_birimi})."
        )
    if gozlem_stale_mi(gozlem, now=now):
        raise KurStaleError(
            f"Döviz kuru stale (id={gozlem.pk}, max={saglayici.max_gecikme_saniye}s)."
        )
    return gozlem


def _assert_dort_goz_manuel(giren, onaylayan, *, action, entity_type):
    if getattr(giren, "pk", None) == getattr(onaylayan, "pk", None):
        _deny(
            giren,
            action=action,
            entity_type=entity_type,
            entity_id="",
            exc=PermissionDenied("Dört göz: giren ile onaylayan aynı olamaz."),
            reason="dort_goz",
        )


def manuel_metal_kuru_gir(
    giren,
    onaylayan,
    *,
    metal,
    saf_birim_fiyat: Decimal,
    kur_tipi: str,
    zaman=None,
    neden: str,
) -> MetalKuru:
    action = "kur.manuel_metal"
    _require_manage(giren, action=action, entity_type="MetalKuru")
    _require_manage(onaylayan, action=action, entity_type="MetalKuru")
    _assert_dort_goz_manuel(giren, onaylayan, action=action, entity_type="MetalKuru")
    neden = (neden or "").strip()
    if not neden:
        raise ValidationError({"manuel_neden": "Manuel kur girişinde neden zorunludur."})
    if kur_tipi not in KurTipi.values:
        raise ValidationError({"kur_tipi": "Geçersiz kur tipi."})

    saglayici = aktif_saglayici()
    now = timezone.now()
    zaman = zaman or now
    _assert_ingest_fresh(
        zaman=zaman,
        alinma_zamani=now,
        max_gecikme_saniye=saglayici.max_gecikme_saniye,
    )

    with domain_atomic():
        obj = MetalKuru(
            metal=metal,
            saglayici=saglayici,
            kur_tipi=kur_tipi,
            zaman=zaman,
            alinma_zamani=now,
            saf_birim_fiyat=saf_birim_fiyat,
            kaynak="manuel",
            manuel_neden=neden,
            giren_kullanici=giren,
            onaylayan_kullanici=onaylayan,
            onay_zamani=now,
        )
        obj.full_clean()
        try:
            obj.save()
        except IntegrityError as exc:
            raise ValidationError(
                "Aynı metal/kur tipi/zaman için kur zaten var."
            ) from exc
        record_audit(
            actor=giren,
            action=action,
            entity_type="MetalKuru",
            entity_id=str(obj.pk),
            success=True,
            detail={
                "onaylayan_id": onaylayan.pk,
                "neden": neden,
                "kur_tipi": kur_tipi,
                "saglayici": saglayici.kod,
            },
        )
    return obj


def manuel_doviz_kuru_gir(
    giren,
    onaylayan,
    *,
    para_birimi: str,
    kur: Decimal,
    kur_tipi: str,
    zaman=None,
    neden: str,
) -> DovizKuru:
    action = "kur.manuel_doviz"
    _require_manage(giren, action=action, entity_type="DovizKuru")
    _require_manage(onaylayan, action=action, entity_type="DovizKuru")
    _assert_dort_goz_manuel(giren, onaylayan, action=action, entity_type="DovizKuru")
    neden = (neden or "").strip()
    if not neden:
        raise ValidationError({"manuel_neden": "Manuel kur girişinde neden zorunludur."})
    if kur_tipi not in KurTipi.values:
        raise ValidationError({"kur_tipi": "Geçersiz kur tipi."})
    if para_birimi not in dict(DovizKuru.PARA_BIRIMI):
        raise ValidationError({"para_birimi": "Geçersiz para birimi."})

    saglayici = aktif_saglayici()
    now = timezone.now()
    zaman = zaman or now
    _assert_ingest_fresh(
        zaman=zaman,
        alinma_zamani=now,
        max_gecikme_saniye=saglayici.max_gecikme_saniye,
    )

    with domain_atomic():
        obj = DovizKuru(
            para_birimi=para_birimi,
            saglayici=saglayici,
            kur_tipi=kur_tipi,
            zaman=zaman,
            alinma_zamani=now,
            kur=kur,
            kaynak="manuel",
            manuel_neden=neden,
            giren_kullanici=giren,
            onaylayan_kullanici=onaylayan,
            onay_zamani=now,
        )
        obj.full_clean()
        try:
            obj.save()
        except IntegrityError as exc:
            raise ValidationError(
                "Aynı para birimi/kur tipi/zaman için kur zaten var."
            ) from exc
        record_audit(
            actor=giren,
            action=action,
            entity_type="DovizKuru",
            entity_id=str(obj.pk),
            success=True,
            detail={
                "onaylayan_id": onaylayan.pk,
                "neden": neden,
                "kur_tipi": kur_tipi,
                "saglayici": saglayici.kod,
            },
        )
    return obj


def feed_metal_kuru_kaydet(
    *,
    saglayici: KurSaglayici,
    metal,
    saf_birim_fiyat: Decimal,
    kur_tipi: str,
    zaman,
    alinma_zamani=None,
    kaynak: str = "api",
) -> MetalKuru:
    """API/WebSocket gözlemi — dört göz yok; sağlayıcı aktif olmalı; stale ingest reddi."""
    if not saglayici.aktif:
        raise ValidationError("Yalnız aktif kur sağlayıcısına feed yazılır (fallback yok).")
    if kaynak == "manuel":
        raise ValidationError("Feed yolu manuel giriş için kullanılamaz.")
    alinma_zamani = alinma_zamani or timezone.now()
    _assert_ingest_fresh(
        zaman=zaman,
        alinma_zamani=alinma_zamani,
        max_gecikme_saniye=saglayici.max_gecikme_saniye,
    )
    obj = MetalKuru(
        metal=metal,
        saglayici=saglayici,
        kur_tipi=kur_tipi,
        zaman=zaman,
        alinma_zamani=alinma_zamani,
        saf_birim_fiyat=saf_birim_fiyat,
        kaynak=kaynak,
    )
    obj.full_clean()
    obj.save()
    return obj
