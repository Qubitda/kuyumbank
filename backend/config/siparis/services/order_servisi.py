"""Order oluşturma / iptal — F4-050…053 (snapshot, tüketim, stok iade; finans yok)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services import outbox_servisi
from fiyatlama.models import PriceLock
from siparis.birim_constants import SepetBirimi
from siparis.models import CartLine, CheckoutAttempt, Order, OrderLine
from siparis.services.cart_servisi import _assert_buyer_actor
from stok.models import StockMovement, StockReservation
from stok.services.ledger_servisi import (
    get_or_create_balance_locked,
    save_balance_fields,
)
from stok.services.reservation_servisi import (
    expire_reservation,
    tuket_rezervasyon,
)

_CENT = Decimal("0.01")


def _q2(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP)


def _snapshot_from_lock(*, lock, miktar: Decimal, birim: str) -> tuple[Decimal, Decimal]:
    """Lock toplamı → satır snapshot.

    ADET: toplam = parça; × miktar.
    GRAM/KARAT: toplam = quote.gram için; gram başına ölçekle (çift sayım yok).
    """
    toplam = Decimal(lock.toplam_vergisiz)
    if birim == SepetBirimi.ADET:
        return toplam, _q2(toplam * miktar)

    quote_gram = getattr(lock.quote, "gram", None)
    if quote_gram is None or Decimal(quote_gram) <= 0:
        raise ValidationError(
            "GRAM sipariş için PriceQuote.gram zorunlu; satır tutarı hesaplanamaz."
        )
    qg = Decimal(quote_gram)
    birim_fiyat = _q2(toplam / qg)
    return birim_fiyat, _q2(birim_fiyat * miktar)


def olustur_from_checkout(
    *,
    actor,
    checkout_attempt: CheckoutAttempt,
    now=None,
) -> Order:
    """Başarılı checkout adayından sipariş üretir; rezervasyonları tüketir."""
    now = now or timezone.now()
    alici_firma = getattr(actor, "firma", None)

    try:
        _assert_buyer_actor(actor, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="order.create",
            entity_type="Order",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"checkout_attempt_id": checkout_attempt.pk},
        )
        raise

    if checkout_attempt.alici_firma_id != alici_firma.pk:
        record_audit_durable(
            actor=actor,
            action="order.create",
            entity_type="Order",
            entity_id="",
            success=False,
            reason="Checkout firması aktör ile uyumsuz.",
            detail={"checkout_attempt_id": checkout_attempt.pk},
        )
        raise PermissionDenied("Checkout firması aktör ile uyumsuz.")

    if checkout_attempt.durum != CheckoutAttempt.Durum.BASARILI:
        raise ValidationError("Yalnız başarılı checkout siparişe dönüşür.")

    existing = Order.objects.filter(checkout_attempt=checkout_attempt).first()
    if existing is not None:
        return existing

    rows = checkout_attempt.sonuc.get("lines") or []
    if not rows:
        raise ValidationError("Checkout sonucunda satır yok.")

    try:
        # F4-022: TTL expire, order domain_atomic DIŞINDA kalıcı yazılır.
        # (İç içe atomic/savepoint rollback expire'ı silerdi.)
        for row in rows:
            res = StockReservation.objects.filter(
                pk=int(row["reservation_id"])
            ).first()
            if res is None:
                continue
            if (
                res.durum == StockReservation.Durum.AKTIF
                and now >= res.gecerlilik_sonu
            ):
                expire_reservation(res, now=now, actor=None)

        for row in rows:
            res = StockReservation.objects.filter(
                pk=int(row["reservation_id"])
            ).first()
            if res is None or res.durum != StockReservation.Durum.AKTIF:
                raise ValidationError(
                    "Rezervasyon aktif değil veya süresi dolmuş; "
                    "sipariş oluşturulamaz."
                )
            if now >= res.gecerlilik_sonu:
                raise ValidationError(
                    "Rezervasyon süresi dolmuş; sipariş oluşturulamaz."
                )

        with domain_atomic():
            # Yarış: aynı attempt
            locked_attempt = (
                CheckoutAttempt.objects.select_for_update()
                .filter(pk=checkout_attempt.pk)
                .first()
            )
            existing = Order.objects.filter(
                checkout_attempt_id=locked_attempt.pk
            ).first()
            if existing is not None:
                return existing

            cart_sube = None
            cart = getattr(alici_firma, "cart", None)
            if cart is not None:
                cart_sube = cart.sube
            if cart_sube is not None and cart_sube.firma_id != alici_firma.pk:
                raise ValidationError("Sepet org birimi firma ile uyumsuz.")

            order = Order(
                alici_firma=alici_firma,
                sube=cart_sube,
                checkout_attempt=locked_attempt,
                durum=Order.Durum.OLUSTURULDU,
                idempotency_key=locked_attempt.idempotency_key,
                olusturan=actor,
            )
            order.save()

            for row in rows:
                lock = (
                    PriceLock.objects.select_for_update()
                    .select_related("quote")
                    .get(pk=int(row["lock_id"]))
                )
                if not lock.is_gecerli(now=now):
                    raise ValidationError(
                        "PriceLock süresi dolmuş; sipariş oluşturulamaz."
                    )
                if lock.alici_firma_id != alici_firma.pk:
                    raise ValidationError("PriceLock tenant uyumsuz.")

                res = StockReservation.objects.select_for_update().get(
                    pk=int(row["reservation_id"])
                )
                if res.durum != StockReservation.Durum.AKTIF:
                    raise ValidationError(
                        f"Rezervasyon aktif değil: {res.durum}"
                    )

                miktar = Decimal(row["miktar"])
                birim = row["birim"]
                birim_fiyat, satir_tutar = _snapshot_from_lock(
                    lock=lock, miktar=miktar, birim=birim
                )
                res_id = res.pk
                varyant_id = lock.quote.varyant_id

                # Rezervasyonu tüket (SATIS movement) — F4-052
                tuket_rezervasyon(res, actor=actor, now=now)

                line = OrderLine(
                    order=order,
                    varyant_id=varyant_id,
                    price_lock=lock,
                    stock_reservation_id=res_id,
                    miktar=miktar,
                    birim=birim,
                    snapshot_birim_fiyat_vergisiz=birim_fiyat,
                    snapshot_satir_tutari_vergisiz=satir_tutar,
                    para_birimi=lock.para_birimi,
                )
                line.save()

                # F5-041b: AKTIF contract release planı varsa serbest miktarı tüket
                from fiyatlama.services.release_servisi import tuket_order_line

                tuket_order_line(actor=actor, order_line=line)

            # F10-012: satır snapshot toplamı ≤ harcama limiti (onaysız aşım yok)
            from firmalar.services.limiti_servisi import assert_order_limit

            assert_order_limit(order)

            # Sepet satırlarını temizle (sipariş sonrası)
            if locked_attempt.cart_id:
                CartLine.objects.filter(cart_id=locked_attempt.cart_id).delete()

            record_audit(
                actor=actor,
                action="order.create",
                entity_type="Order",
                entity_id=str(order.pk),
                success=True,
                detail={
                    "checkout_attempt_id": locked_attempt.pk,
                    "line_count": len(rows),
                    "idempotency_key": order.idempotency_key,
                },
            )
            # F4-090: aynı atomic — rollback outbox'ı da siler
            outbox_servisi.enqueue(
                event_type="order.created",
                payload={
                    "order_id": order.pk,
                    "alici_firma_id": alici_firma.pk,
                    "idempotency_key": order.idempotency_key,
                    "line_count": len(rows),
                },
            )
            return order
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.create",
            entity_type="Order",
            entity_id="",
            success=False,
            reason=reason[:255],
            detail={"checkout_attempt_id": checkout_attempt.pk},
        )
        raise


def iptal_siparis(*, actor, order: Order, now=None) -> Order:
    """OLUSTURULDU → IPTAL; satır başına IADE movement (F4-053). Ödeme iadesi yok."""
    now = now or timezone.now()
    alici_firma = getattr(actor, "firma", None)

    try:
        _assert_buyer_actor(actor, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="order.cancel",
            entity_type="Order",
            entity_id=str(order.pk or ""),
            success=False,
            reason=str(exc),
            detail={"order_id": order.pk},
        )
        raise

    if order.alici_firma_id != alici_firma.pk:
        record_audit_durable(
            actor=actor,
            action="order.cancel",
            entity_type="Order",
            entity_id=str(order.pk or ""),
            success=False,
            reason="Sipariş firması aktör ile uyumsuz.",
            detail={"order_id": order.pk},
        )
        raise PermissionDenied("Sipariş firması aktör ile uyumsuz.")

    if order.durum == Order.Durum.IPTAL:
        return order

    if order.durum != Order.Durum.OLUSTURULDU:
        raise ValidationError(f"İptal edilemez; durum={order.durum}")

    try:
        with domain_atomic():
            locked = (
                Order.objects.select_for_update()
                .prefetch_related(
                    "lines__stock_reservation__warehouse",
                    "lines__stock_reservation__teklif",
                )
                .filter(pk=order.pk)
                .first()
            )
            if locked is None:
                raise ValidationError("Sipariş bulunamadı.")
            if locked.durum == Order.Durum.IPTAL:
                return locked
            if locked.durum != Order.Durum.OLUSTURULDU:
                raise ValidationError(
                    f"İptal edilemez; durum={locked.durum}"
                )

            # K1: aktif sevkiyat veya stok iadesi yapılmış iade → çift IADE engeli
            from lojistik.models import ReturnRequest, Shipment

            if (
                Shipment.objects.filter(order_id=locked.pk)
                .exclude(durum=Shipment.Durum.IPTAL)
                .exists()
            ):
                raise ValidationError(
                    "İptal edilemez: aktif sevkiyat var (IADE çakışması)."
                )
            if ReturnRequest.objects.filter(
                order_id=locked.pk, stok_iade_yapildi=True
            ).exists():
                raise ValidationError(
                    "İptal edilemez: stok iadesi yapılmış iade kaydı var."
                )

            iade_ids: list[int] = []
            for line in locked.lines.all():
                res = line.stock_reservation
                if res.durum != StockReservation.Durum.TUKETILDI:
                    raise ValidationError(
                        "İptal için satır rezervasyonu tüketilmiş olmalı."
                    )
                miktar = line.miktar
                if miktar <= 0:
                    raise ValidationError("İade miktarı pozitif olmalı.")

                bal = get_or_create_balance_locked(
                    warehouse=res.warehouse,
                    teklif=res.teklif,
                    birim=res.birim,
                )
                bal.on_hand = bal.on_hand + miktar
                save_balance_fields(bal, update_fields=["on_hand"])

                mv = StockMovement(
                    warehouse=res.warehouse,
                    teklif=res.teklif,
                    varyant_id=line.varyant_id,
                    birim=line.birim,
                    miktar=miktar,
                    tip=StockMovement.Tip.IADE,
                    neden=f"order_cancel:{locked.pk}:line:{line.pk}",
                    olusturan=actor,
                )
                mv.save()
                iade_ids.append(mv.pk)

                # F5-041b: release tüketimini geri al
                from fiyatlama.services.release_servisi import iade_order_line

                iade_order_line(actor=actor, order_line=line)

            locked.durum = Order.Durum.IPTAL
            locked._allow_status_transition = True
            try:
                locked.save(update_fields=["durum", "guncelleme_tarihi"])
            finally:
                locked._allow_status_transition = False

            record_audit(
                actor=actor,
                action="order.cancel",
                entity_type="Order",
                entity_id=str(locked.pk),
                success=True,
                detail={
                    "from": Order.Durum.OLUSTURULDU,
                    "to": Order.Durum.IPTAL,
                    "iade_movement_ids": iade_ids,
                    "now": now.isoformat(),
                },
            )
            return locked
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.cancel",
            entity_type="Order",
            entity_id=str(order.pk or ""),
            success=False,
            reason=reason[:255],
            detail={"order_id": order.pk},
        )
        raise
