"""Quick Reorder — geçmiş Order → güncel quote ile sepet (F4-080).

Eski PriceLock/snapshot yeniden kilitlenmez; checkout’ta yeni lock+rezerv.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from fiyatlama.services import pricing_service
from siparis.models import Cart, CartLine, Order
from siparis.services.cart_servisi import (
    _assert_buyer_actor,
    al_veya_olustur_sepet,
    satir_ekle,
)
from siparis.services.checkout_servisi import _resolve_warehouse_for_teklif
from stok.models import StockBalance
from stok.services.birim import birim_from_teklif


def _assert_atp(*, teklif, miktar: Decimal, birim: str) -> None:
    """Fail-closed: yeterli available yoksa sepete aktarım yok."""
    warehouse = _resolve_warehouse_for_teklif(teklif)
    bal = StockBalance.objects.filter(
        warehouse=warehouse, teklif=teklif, birim=birim
    ).first()
    available = bal.available if bal is not None else Decimal("0")
    if available < miktar:
        raise ValidationError(
            f"ATP yetersiz: available={available}, istenen={miktar} {birim}."
        )


def sepete_aktar(
    *,
    actor,
    order: Order,
    now=None,
    replace_cart: bool = True,
) -> Cart:
    """Order satırlarını güncel quote ile alıcı sepetine yazar.

    replace_cart=True ise mevcut sepet satırları silinir (deterministik reorder).
    """
    now = now or timezone.now()
    alici_firma = getattr(actor, "firma", None)

    try:
        _assert_buyer_actor(actor, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="order.reorder",
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
            action="order.reorder",
            entity_type="Order",
            entity_id=str(order.pk or ""),
            success=False,
            reason="Sipariş firması aktör ile uyumsuz.",
            detail={"order_id": order.pk},
        )
        raise PermissionDenied("Sipariş firması aktör ile uyumsuz.")

    lines = list(
        order.lines.select_related(
            "varyant",
            "price_lock__quote__satis_kanali",
            "price_lock__quote__teklif",
        ).order_by("pk")
    )
    if not lines:
        raise ValidationError("Siparişte satır yok; yeniden sipariş yapılamaz.")

    prepared: list[tuple] = []
    try:
        for line in lines:
            old_quote = line.price_lock.quote
            varyant = line.varyant
            miktar = Decimal(line.miktar)
            if miktar <= 0:
                raise ValidationError("Sipariş satır miktarı pozitif olmalı.")

            new_quote = pricing_service.quote(
                alici_firma=alici_firma,
                satis_kanali=old_quote.satis_kanali,
                varyant=varyant,
                kullanici=actor,
                para_birimi=old_quote.para_birimi or "TRY",
                now=now,
            )
            birim = birim_from_teklif(new_quote.teklif)
            if birim != line.birim:
                raise ValidationError(
                    f"Birim uyumsuz: sipariş={line.birim}, güncel teklif={birim}."
                )
            _assert_atp(teklif=new_quote.teklif, miktar=miktar, birim=birim)
            prepared.append((new_quote, miktar))
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.reorder",
            entity_type="Order",
            entity_id=str(order.pk),
            success=False,
            reason=reason[:255],
            detail={"order_id": order.pk},
        )
        raise

    try:
        with domain_atomic():
            cart = al_veya_olustur_sepet(actor=actor, alici_firma=alici_firma)
            if replace_cart:
                CartLine.objects.filter(cart=cart).delete()

            for new_quote, miktar in prepared:
                satir_ekle(
                    actor=actor, price_quote=new_quote, miktar=miktar, now=now
                )

            record_audit(
                actor=actor,
                action="order.reorder",
                entity_type="Order",
                entity_id=str(order.pk),
                success=True,
                detail={
                    "order_id": order.pk,
                    "cart_id": cart.pk,
                    "line_count": len(prepared),
                    "replace_cart": replace_cart,
                },
            )
            return Cart.objects.prefetch_related("lines").get(pk=cart.pk)
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and hasattr(exc, "messages"):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.reorder",
            entity_type="Order",
            entity_id=str(order.pk),
            success=False,
            reason=reason[:255],
            detail={"order_id": order.pk},
        )
        raise
