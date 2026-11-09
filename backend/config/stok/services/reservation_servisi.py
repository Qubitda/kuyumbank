"""StockReservation — hold/TTL/oversell (ADR-0011 F4-A5/A6).

Rezervasyon `reserved` günceller; fiziksel on_hand düşümü yalnız tüketmede
(SATIS movement). Create/iptal/expire StockMovement yazmaz.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import has_perm, is_platform_firm_user
from fiyatlama.models import TedarikciTeklif
from stok.models import StockMovement, StockReservation, Warehouse
from stok.services.birim import assert_ayni_birim, birim_from_teklif
from stok.services.ledger_servisi import (
    assert_teklif_warehouse,
    get_or_create_balance_locked,
    save_balance_fields,
)

DEFAULT_TTL_SECONDS = 900


def _assert_can_reserve(actor, warehouse: Warehouse, alici_firma) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Rezervasyon için kimlik gerekli.")

    if is_platform_firm_user(actor) and has_perm(actor, P["manage_warehouse"]):
        return

    firma = getattr(actor, "firma", None)
    firma_id = getattr(actor, "firma_id", None)
    if firma is None or not firma_id:
        raise PermissionDenied("Rezervasyon için firma bağlamı gerekli.")

    if (
        has_perm(actor, P["manage_own_warehouse"])
        and warehouse.sahip_tipi == Warehouse.SahipTipi.TEDARIKCI
        and firma_id == warehouse.sahip_firma_id
    ):
        return

    if getattr(firma, "alici_mi", False) and firma_id == getattr(
        alici_firma, "pk", None
    ):
        return

    raise PermissionDenied("Bu depo için rezervasyon yetkisi yok.")


def _return_or_reject_existing(res: StockReservation, *, now) -> StockReservation:
    if res.durum == StockReservation.Durum.AKTIF and now < res.gecerlilik_sonu:
        return res
    if res.durum == StockReservation.Durum.AKTIF and now >= res.gecerlilik_sonu:
        expire_reservation(res, now=now, actor=None)
        raise ValidationError(
            "Bu idempotency anahtarına ait rezervasyon süresi dolmuş; yeni key gerekli."
        )
    raise ValidationError(
        f"Bu idempotency anahtarı kapalı rezervasyona bağlı ({res.durum})."
    )


def _sweep_expired_on_balance(
    *,
    warehouse: Warehouse,
    teklif: TedarikciTeklif,
    birim: str,
    now,
) -> int:
    """Kilitli balance anahtarı için TTL dolmuş AKTIF hold'ları kapatır (lazy F4-022).

    Caller zaten domain_atomic + balance select_for_update tutuyor olmalı.
    """
    stale_ids = list(
        StockReservation.objects.select_for_update()
        .filter(
            warehouse=warehouse,
            teklif=teklif,
            birim=birim,
            durum=StockReservation.Durum.AKTIF,
            gecerlilik_sonu__lte=now,
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    n = 0
    for pk in stale_ids:
        locked = (
            StockReservation.objects.select_for_update()
            .select_related("warehouse", "teklif")
            .filter(pk=pk, durum=StockReservation.Durum.AKTIF)
            .first()
        )
        if locked is None:
            continue
        bal = get_or_create_balance_locked(
            warehouse=locked.warehouse,
            teklif=locked.teklif,
            birim=locked.birim,
        )
        if bal.reserved < locked.miktar:
            raise ValidationError(
                f"reserved tutarsız: {bal.reserved} < {locked.miktar}"
            )
        bal.reserved = bal.reserved - locked.miktar
        save_balance_fields(bal, update_fields=["reserved"])
        locked.durum = StockReservation.Durum.SURESI_DOLDU
        locked.kapanma_tarihi = now
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "kapanma_tarihi"])
        finally:
            locked._allow_status_transition = False
        record_audit(
            actor=None,
            action="stock_reservation.expire",
            entity_type="StockReservation",
            entity_id=str(locked.pk),
            success=True,
            detail={
                "durum": StockReservation.Durum.SURESI_DOLDU,
                "miktar": str(locked.miktar),
                "birim": locked.birim,
                "reserved_after": str(bal.reserved),
                "via": "lazy_create_sweep",
            },
        )
        n += 1
    return n


def olustur_rezervasyon(
    *,
    actor,
    warehouse: Warehouse,
    teklif: TedarikciTeklif,
    miktar: Decimal,
    alici_firma,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    now=None,
    idempotency_key: str | None = None,
) -> StockReservation:
    now = now or timezone.now()
    miktar = Decimal(miktar)
    if miktar <= 0:
        raise ValidationError("Rezervasyon miktarı pozitif olmalı.")
    if ttl_seconds <= 0:
        raise ValidationError("TTL pozitif olmalı.")

    key = (idempotency_key or "").strip() or None
    birim = birim_from_teklif(teklif)
    assert_teklif_warehouse(warehouse, teklif)

    try:
        _assert_can_reserve(actor, warehouse, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="stock_reservation.create",
            entity_type="StockReservation",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"warehouse_id": warehouse.pk, "teklif_id": teklif.pk},
        )
        raise

    if key is not None:
        existing = StockReservation.objects.filter(
            warehouse=warehouse, idempotency_key=key
        ).first()
        if existing is not None:
            return _return_or_reject_existing(existing, now=now)

    try:
        with domain_atomic():
            bal = get_or_create_balance_locked(
                warehouse=warehouse, teklif=teklif, birim=birim
            )
            assert_ayni_birim(bal.birim, birim, context="reservation")
            # F4-022: TTL dolmuş AKTIF hold'lar available'ı şişirmesin
            _sweep_expired_on_balance(
                warehouse=warehouse, teklif=teklif, birim=birim, now=now
            )
            bal.refresh_from_db()
            if bal.available < miktar:
                raise ValidationError(
                    f"Yetersiz available: {bal.available} < {miktar} ({birim})."
                )
            bal.reserved = bal.reserved + miktar
            save_balance_fields(bal, update_fields=["reserved"])

            res = StockReservation(
                warehouse=warehouse,
                teklif=teklif,
                varyant_id=teklif.varyant_id,
                birim=birim,
                miktar=miktar,
                durum=StockReservation.Durum.AKTIF,
                gecerlilik_sonu=now + timedelta(seconds=ttl_seconds),
                alici_firma=alici_firma,
                idempotency_key=key,
                olusturan=actor,
            )
            res.save()
            record_audit(
                actor=actor,
                action="stock_reservation.create",
                entity_type="StockReservation",
                entity_id=str(res.pk),
                success=True,
                detail={
                    "miktar": str(miktar),
                    "birim": birim,
                    "warehouse_id": warehouse.pk,
                    "teklif_id": teklif.pk,
                    "available_after": str(bal.available),
                    "gecerlilik_sonu": res.gecerlilik_sonu.isoformat(),
                    "idempotency_key": key,
                },
            )
            return res
    except IntegrityError:
        if key is None:
            raise
        existing = StockReservation.objects.filter(
            warehouse=warehouse, idempotency_key=key
        ).first()
        if existing is not None:
            return _return_or_reject_existing(existing, now=now)
        raise
    except ValidationError as exc:
        record_audit_durable(
            actor=actor,
            action="stock_reservation.create",
            entity_type="StockReservation",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"warehouse_id": warehouse.pk, "teklif_id": teklif.pk},
        )
        raise


def _close_aktif_hold(
    res: StockReservation,
    *,
    yeni_durum: str,
    actor,
    now,
    audit_action: str,
) -> StockReservation:
    """AKTIF hold'u kapatır; reserved serbest bırakır. on_hand'e dokunmaz."""
    with domain_atomic():
        locked = (
            StockReservation.objects.select_for_update()
            .select_related("warehouse", "teklif")
            .filter(pk=res.pk, durum=StockReservation.Durum.AKTIF)
            .first()
        )
        if locked is None:
            res.refresh_from_db()
            return res

        bal = get_or_create_balance_locked(
            warehouse=locked.warehouse,
            teklif=locked.teklif,
            birim=locked.birim,
        )
        if bal.reserved < locked.miktar:
            raise ValidationError(
                f"reserved tutarsız: {bal.reserved} < {locked.miktar}"
            )
        bal.reserved = bal.reserved - locked.miktar
        save_balance_fields(bal, update_fields=["reserved"])

        locked.durum = yeni_durum
        locked.kapanma_tarihi = now
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "kapanma_tarihi"])
        finally:
            locked._allow_status_transition = False

        record_audit(
            actor=actor,
            action=audit_action,
            entity_type="StockReservation",
            entity_id=str(locked.pk),
            success=True,
            detail={
                "durum": yeni_durum,
                "miktar": str(locked.miktar),
                "birim": locked.birim,
                "reserved_after": str(bal.reserved),
            },
        )
    res.refresh_from_db()
    return res


def iptal_rezervasyon(res: StockReservation, *, actor, now=None) -> StockReservation:
    now = now or timezone.now()
    if res.durum != StockReservation.Durum.AKTIF:
        raise ValidationError(f"İptal edilemez; durum={res.durum}")
    return _close_aktif_hold(
        res,
        yeni_durum=StockReservation.Durum.IPTAL,
        actor=actor,
        now=now,
        audit_action="stock_reservation.cancel",
    )


def expire_reservation(
    res: StockReservation, *, now=None, actor=None
) -> StockReservation:
    now = now or timezone.now()
    if res.durum != StockReservation.Durum.AKTIF:
        return res
    if now < res.gecerlilik_sonu:
        return res
    return _close_aktif_hold(
        res,
        yeni_durum=StockReservation.Durum.SURESI_DOLDU,
        actor=actor,
        now=now,
        audit_action="stock_reservation.expire",
    )


def sync_reservation_expiration(
    res: StockReservation, *, now=None
) -> StockReservation:
    now = now or timezone.now()
    return expire_reservation(res, now=now, actor=None)


def expire_stale_reservations(*, now=None, limit: int | None = None) -> int:
    """TTL dolmuş AKTIF rezervasyonları toplu kapatır (F4-022). actor=None audit."""
    now = now or timezone.now()
    qs = (
        StockReservation.objects.filter(
            durum=StockReservation.Durum.AKTIF,
            gecerlilik_sonu__lte=now,
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    if limit is not None:
        if limit <= 0:
            return 0
        qs = qs[:limit]
    ids = list(qs)
    n = 0
    for pk in ids:
        res = StockReservation.objects.filter(pk=pk).first()
        if res is None:
            continue
        before = res.durum
        expire_reservation(res, now=now, actor=None)
        res.refresh_from_db()
        if (
            before == StockReservation.Durum.AKTIF
            and res.durum == StockReservation.Durum.SURESI_DOLDU
        ):
            n += 1
    return n


def tuket_rezervasyon(
    res: StockReservation, *, actor, now=None
) -> StockReservation:
    """Hold → satış: reserved ve on_hand düşer; SATIS movement yazılır.

    Süre dolmuşsa önce expire (ayrı atomic). Order create gibi DIŞ atomic
    içinden çağrılıyorsa expire savepoint'i dış rollback ile silinir —
    `olustur_from_checkout` bu yüzden expire'ı atomic dışında önceden yapar.
    """
    now = now or timezone.now()
    sync_reservation_expiration(res, now=now)
    res.refresh_from_db()
    if res.durum != StockReservation.Durum.AKTIF:
        raise ValidationError(f"Tüketilemez; durum={res.durum}")

    with domain_atomic():
        locked = (
            StockReservation.objects.select_for_update()
            .select_related("warehouse", "teklif")
            .filter(pk=res.pk, durum=StockReservation.Durum.AKTIF)
            .first()
        )
        if locked is None:
            res.refresh_from_db()
            raise ValidationError("Rezervasyon aktif değil.")
        if now >= locked.gecerlilik_sonu:
            raise ValidationError("Rezervasyon süresi dolmuş; tüketilemez.")

        bal = get_or_create_balance_locked(
            warehouse=locked.warehouse,
            teklif=locked.teklif,
            birim=locked.birim,
        )
        if bal.reserved < locked.miktar:
            raise ValidationError("reserved tutarsız.")
        if bal.on_hand < locked.miktar:
            raise ValidationError("on_hand yetersiz (tüketim).")

        bal.reserved = bal.reserved - locked.miktar
        bal.on_hand = bal.on_hand - locked.miktar
        save_balance_fields(bal, update_fields=["reserved", "on_hand"])

        mv = StockMovement(
            warehouse=locked.warehouse,
            teklif=locked.teklif,
            varyant_id=locked.varyant_id,
            birim=locked.birim,
            miktar=-locked.miktar,
            tip=StockMovement.Tip.SATIS,
            neden=f"reservation:{locked.pk}",
            olusturan=actor,
        )
        mv.save()

        locked.durum = StockReservation.Durum.TUKETILDI
        locked.kapanma_tarihi = now
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "kapanma_tarihi"])
        finally:
            locked._allow_status_transition = False

        record_audit(
            actor=actor,
            action="stock_reservation.consume",
            entity_type="StockReservation",
            entity_id=str(locked.pk),
            success=True,
            detail={
                "miktar": str(locked.miktar),
                "birim": locked.birim,
                "movement_id": mv.pk,
                "on_hand": str(bal.on_hand),
                "reserved": str(bal.reserved),
            },
        )
    res.refresh_from_db()
    return res
