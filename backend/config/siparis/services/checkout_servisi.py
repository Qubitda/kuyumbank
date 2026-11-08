"""Checkout — PriceLock + StockReservation → sipariş adayı (F4-040/041).

Order oluşturmaz (F4-050). Ödeme yok. Fail audit durable (F4-A16).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from fiyatlama.services.pricing_service import lock_quote
from siparis.models import Cart, CartLine, CheckoutAttempt
from siparis.services.cart_servisi import _assert_buyer_actor
from stok.models import Warehouse
from stok.services.reservation_servisi import olustur_rezervasyon


@dataclass(frozen=True)
class CheckoutLineResult:
    cart_line_id: int
    quote_id: int
    lock_id: int
    reservation_id: int
    warehouse_id: int
    miktar: Decimal
    birim: str


@dataclass(frozen=True)
class CheckoutResult:
    attempt: CheckoutAttempt
    lines: tuple[CheckoutLineResult, ...]


def _resolve_warehouse_for_teklif(teklif) -> Warehouse:
    wh = (
        Warehouse.objects.filter(
            sahip_firma_id=teklif.tedarikci_id,
            sahip_tipi=Warehouse.SahipTipi.TEDARIKCI,
            aktif=True,
        )
        .order_by("pk")
        .first()
    )
    if wh is None:
        raise ValidationError(
            "Teklif tedarikçisinin aktif deposu yok; checkout yapılamaz."
        )
    return wh


def _record_failed_attempt(
    *,
    actor,
    alici_firma,
    cart,
    key: str,
    reason: str,
    detail: dict | None = None,
) -> None:
    record_audit_durable(
        actor=actor,
        action="checkout.fail",
        entity_type="CheckoutAttempt",
        entity_id="",
        success=False,
        reason=reason[:255],
        detail={
            "alici_firma_id": alici_firma.pk,
            "cart_id": getattr(cart, "pk", None),
            "idempotency_key": key,
            **(detail or {}),
        },
    )
    prior = CheckoutAttempt.objects.filter(
        alici_firma=alici_firma, idempotency_key=key
    ).first()
    if prior is not None and prior.durum == CheckoutAttempt.Durum.BASARILI:
        return
    CheckoutAttempt.objects.update_or_create(
        alici_firma=alici_firma,
        idempotency_key=key,
        defaults={
            "cart": cart,
            "durum": CheckoutAttempt.Durum.BASARISIZ,
            "sonuc": {},
            "hata_mesaji": reason[:255],
            "olusturan": actor,
        },
    )


def checkout(
    *,
    actor,
    cart: Cart | None = None,
    idempotency_key: str,
    now=None,
) -> CheckoutResult:
    """Sepeti kilitler ve rezerve eder; CheckoutAttempt (sipariş adayı) döner."""
    now = now or timezone.now()
    key = (idempotency_key or "").strip()
    if not key:
        raise ValidationError("idempotency_key zorunlu.")

    alici_firma = getattr(actor, "firma", None)
    try:
        _assert_buyer_actor(actor, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="checkout.fail",
            entity_type="CheckoutAttempt",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"idempotency_key": key},
        )
        raise

    if cart is None:
        cart = Cart.objects.filter(alici_firma=alici_firma).first()
    if cart is None or cart.alici_firma_id != alici_firma.pk:
        record_audit_durable(
            actor=actor,
            action="checkout.fail",
            entity_type="CheckoutAttempt",
            entity_id="",
            success=False,
            reason="Sepet bulunamadı.",
            detail={"idempotency_key": key},
        )
        raise ValidationError("Sepet bulunamadı.")

    existing = CheckoutAttempt.objects.filter(
        alici_firma=alici_firma, idempotency_key=key
    ).first()
    if existing is not None and existing.durum == CheckoutAttempt.Durum.BASARILI:
        lines = tuple(
            CheckoutLineResult(
                cart_line_id=int(row["cart_line_id"]),
                quote_id=int(row["quote_id"]),
                lock_id=int(row["lock_id"]),
                reservation_id=int(row["reservation_id"]),
                warehouse_id=int(row["warehouse_id"]),
                miktar=Decimal(row["miktar"]),
                birim=row["birim"],
            )
            for row in (existing.sonuc.get("lines") or [])
        )
        return CheckoutResult(attempt=existing, lines=lines)

    lines_qs = list(
        CartLine.objects.select_related(
            "price_quote",
            "price_quote__teklif",
            "price_quote__varyant",
            "price_quote__varyant__urun",
        ).filter(cart=cart)
    )
    if not lines_qs:
        _record_failed_attempt(
            actor=actor,
            alici_firma=alici_firma,
            cart=cart,
            key=key,
            reason="Sepet boş; checkout yapılamaz.",
        )
        raise ValidationError("Sepet boş; checkout yapılamaz.")

    try:
        with domain_atomic():
            line_results: list[CheckoutLineResult] = []
            for cl in lines_qs:
                quote = cl.price_quote
                if quote.alici_firma_id != alici_firma.pk:
                    raise ValidationError("Sepet satırı quote firması uyumsuz.")
                if now >= quote.gecerlilik_sonu:
                    raise ValidationError(
                        "PriceQuote süresi dolmuş; checkout fail."
                    )
                if not quote.varyant.aktif:
                    raise ValidationError("Varyant pasif; checkout fail.")
                urun = quote.varyant.urun
                if urun.onay_durumu != "onayli" or urun.yayin_durumu != "aktif":
                    raise ValidationError("Ürün yayınlı değil; checkout fail.")

                lock = lock_quote(
                    quote,
                    kullanici=actor,
                    now=now,
                    idempotency_key=f"{key}:lock:{quote.pk}",
                )
                if not lock.is_gecerli(now=now):
                    raise ValidationError(
                        "PriceLock geçersiz/süresi dolmuş; checkout fail."
                    )

                warehouse = _resolve_warehouse_for_teklif(quote.teklif)
                res = olustur_rezervasyon(
                    actor=actor,
                    warehouse=warehouse,
                    teklif=quote.teklif,
                    miktar=cl.miktar,
                    alici_firma=alici_firma,
                    now=now,
                    idempotency_key=f"{key}:res:{cl.pk}",
                )
                line_results.append(
                    CheckoutLineResult(
                        cart_line_id=cl.pk,
                        quote_id=quote.pk,
                        lock_id=lock.pk,
                        reservation_id=res.pk,
                        warehouse_id=warehouse.pk,
                        miktar=cl.miktar,
                        birim=cl.birim,
                    )
                )

            sonuc = {
                "lines": [
                    {
                        "cart_line_id": r.cart_line_id,
                        "quote_id": r.quote_id,
                        "lock_id": r.lock_id,
                        "reservation_id": r.reservation_id,
                        "warehouse_id": r.warehouse_id,
                        "miktar": str(r.miktar),
                        "birim": r.birim,
                    }
                    for r in line_results
                ]
            }
            attempt, _ = CheckoutAttempt.objects.update_or_create(
                alici_firma=alici_firma,
                idempotency_key=key,
                defaults={
                    "cart": cart,
                    "durum": CheckoutAttempt.Durum.BASARILI,
                    "sonuc": sonuc,
                    "hata_mesaji": "",
                    "olusturan": actor,
                },
            )
            record_audit(
                actor=actor,
                action="checkout.success",
                entity_type="CheckoutAttempt",
                entity_id=str(attempt.pk),
                success=True,
                detail={
                    "idempotency_key": key,
                    "line_count": len(line_results),
                    "lock_ids": [r.lock_id for r in line_results],
                    "reservation_ids": [r.reservation_id for r in line_results],
                },
            )
            return CheckoutResult(
                attempt=attempt, lines=tuple(line_results)
            )
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        # domain_atomic dışı durable fail (F4-041)
        record_audit_durable(
            actor=actor,
            action="checkout.fail",
            entity_type="CheckoutAttempt",
            entity_id="",
            success=False,
            reason=reason[:255],
            detail={
                "alici_firma_id": alici_firma.pk,
                "cart_id": cart.pk,
                "idempotency_key": key,
            },
        )
        # Başarısız attempt kaydı (başarılı üzerine yazılmaz)
        prior = CheckoutAttempt.objects.filter(
            alici_firma=alici_firma, idempotency_key=key
        ).first()
        if prior is None or prior.durum != CheckoutAttempt.Durum.BASARILI:
            CheckoutAttempt.objects.update_or_create(
                alici_firma=alici_firma,
                idempotency_key=key,
                defaults={
                    "cart": cart,
                    "durum": CheckoutAttempt.Durum.BASARISIZ,
                    "sonuc": {},
                    "hata_mesaji": reason[:255],
                    "olusturan": actor,
                },
            )
        raise
