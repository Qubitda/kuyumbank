"""CAP-ALERT — eşik bildirimi; stale’de tetik yok; checkout’a dokunmaz."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.outbox_servisi import enqueue
from firmalar.services.yetki_servisi import require_perm
from tanimlar.models import KurAlertKurali, KurTipi, MetalKuru
from tanimlar.services import kur_servisi

P_MANAGE_KUR = "tanimlar.manage_kur"


def _require(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(actor, P_MANAGE_KUR, message="Kur alert yetkiniz yok.")
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="KurAlertKurali",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def kural_olustur(
    *,
    actor,
    metal,
    esik_fiyat: Decimal,
    yon: str,
    kur_tipi: str = KurTipi.SATIS,
) -> KurAlertKurali:
    _require(actor, action="kur.alert.create")
    yon = (yon or "").strip().upper()
    if yon not in {KurAlertKurali.Yon.YUKARI, KurAlertKurali.Yon.ASAGI}:
        raise ValidationError({"yon": "YUKARI veya ASAGI."})
    if kur_tipi not in KurTipi.values:
        raise ValidationError({"kur_tipi": "Geçersiz."})
    esik = Decimal(str(esik_fiyat))
    if esik <= 0:
        raise ValidationError({"esik_fiyat": "0 yasak."})
    with domain_atomic():
        row = KurAlertKurali(
            metal=metal,
            kur_tipi=kur_tipi,
            yon=yon,
            esik_fiyat=esik,
            aktif=True,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        row.save()
        record_audit(
            actor=actor,
            action="kur.alert.created",
            entity_type="KurAlertKurali",
            entity_id=str(row.pk),
            success=True,
            detail={"esik": str(esik), "yon": yon},
        )
        return row


def _esik_asildi(*, yon: str, fiyat: Decimal, esik: Decimal) -> bool:
    if yon == KurAlertKurali.Yon.YUKARI:
        return fiyat >= esik
    return fiyat <= esik


def degerlendir(*, now=None, metal=None) -> list[dict]:
    """Aktif kuralları tara; yalnızca taze (non-stale) gözlemde outbox.

    Dönüş: tetiklenen olay özetleri. Checkout/quote yoluna bağlanmaz.
    """
    now = now or timezone.now()
    qs = KurAlertKurali.objects.filter(aktif=True).select_related("metal")
    if metal is not None:
        qs = qs.filter(metal_id=metal.pk if hasattr(metal, "pk") else metal)
    tetiklenen: list[dict] = []
    for kural in qs:
        gozlem = (
            MetalKuru.objects.filter(
                metal_id=kural.metal_id,
                kur_tipi=kural.kur_tipi,
                kaynak__in=["api", "websocket", "tcmb"],
            )
            .select_related("saglayici")
            .order_by("-zaman", "-pk")
            .first()
        )
        if gozlem is None or gozlem.saf_birim_fiyat <= 0:
            continue
        # Stale → alert yok (kabul kriteri)
        if kur_servisi.gozlem_stale_mi(gozlem, now=now):
            continue
        if kural.son_tetik_gozlem_id == gozlem.pk:
            continue  # aynı gözlem tekrar tetiklemez
        if not _esik_asildi(
            yon=kural.yon,
            fiyat=gozlem.saf_birim_fiyat,
            esik=kural.esik_fiyat,
        ):
            continue
        with domain_atomic():
            locked = KurAlertKurali.objects.select_for_update().get(pk=kural.pk)
            if locked.son_tetik_gozlem_id == gozlem.pk:
                continue
            locked.son_tetik_gozlem = gozlem
            locked.save(update_fields=["son_tetik_gozlem", "guncelleme_tarihi"])
            msg = enqueue(
                event_type="kur.alert",
                payload={
                    "kural_id": locked.pk,
                    "metal_id": locked.metal_id,
                    "kur_tipi": locked.kur_tipi,
                    "yon": locked.yon,
                    "esik_fiyat": str(locked.esik_fiyat),
                    "gozlem_id": gozlem.pk,
                    "saf_birim_fiyat": str(gozlem.saf_birim_fiyat),
                },
            )
            tetiklenen.append(
                {
                    "kural_id": locked.pk,
                    "outbox_id": msg.pk,
                    "gozlem_id": gozlem.pk,
                }
            )
    return tetiklenen
