"""Bulk Order / CSV — F4-081.

Satır satır doğrulama + kısmi hata raporu; birim dönüşümü yok.
Idempotency: aynı (firma, key) tekrarında mevcut Order döner (çift sipariş yok).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from fiyatlama.models import PriceQuote
from fiyatlama.services import pricing_service
from siparis.models import CartLine, CheckoutAttempt, Order
from siparis.services import checkout_servisi, order_servisi
from siparis.services.cart_servisi import (
    _assert_buyer_actor,
    al_veya_olustur_sepet,
    satir_ekle,
)
from siparis.services.checkout_servisi import _resolve_warehouse_for_teklif
from stok.models import StockBalance
from stok.services.birim import birim_from_teklif
from urunler.models import Varyant


@dataclass(frozen=True)
class BulkRowInput:
    satir_no: int
    sku: str
    miktar: Decimal
    birim: str | None = None


@dataclass(frozen=True)
class BulkRowError:
    satir_no: int
    sku: str
    hata: str


@dataclass(frozen=True)
class BulkRowOk:
    satir_no: int
    sku: str
    varyant_id: int
    miktar: Decimal
    birim: str
    quote_id: int


@dataclass
class BulkOrderResult:
    order: Order | None
    checkout_attempt: CheckoutAttempt | None
    accepted: list[BulkRowOk] = field(default_factory=list)
    errors: list[BulkRowError] = field(default_factory=list)
    replayed: bool = False


def parse_csv(text: str) -> list[BulkRowInput]:
    """CSV: zorunlu sütunlar sku, miktar; isteğe bağlı birim. Birim dönüşümü yok."""
    if text is None or not str(text).strip():
        raise ValidationError("CSV boş.")
    reader = csv.DictReader(io.StringIO(str(text).lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValidationError("CSV başlık satırı yok.")
    fields = {
        ((f or "").strip().lower()): (f or "").strip() for f in reader.fieldnames
    }
    if "sku" not in fields or "miktar" not in fields:
        raise ValidationError(
            "CSV sütunları zorunlu: sku, miktar (opsiyonel: birim)."
        )

    rows: list[BulkRowInput] = []
    for i, raw in enumerate(reader, start=2):
        sku = (raw.get(fields["sku"]) or "").strip()
        miktar_raw = (raw.get(fields["miktar"]) or "").strip()
        birim_raw = None
        if "birim" in fields:
            birim_raw = (raw.get(fields["birim"]) or "").strip() or None
        if not sku and not miktar_raw:
            continue
        try:
            miktar = Decimal(miktar_raw)
        except (InvalidOperation, TypeError):
            miktar = Decimal("0")
        rows.append(
            BulkRowInput(satir_no=i, sku=sku, miktar=miktar, birim=birim_raw)
        )
    if not rows:
        raise ValidationError("CSV'de işlenecek satır yok.")
    return rows


def _assert_atp(*, teklif, miktar: Decimal, birim: str) -> None:
    warehouse = _resolve_warehouse_for_teklif(teklif)
    bal = StockBalance.objects.filter(
        warehouse=warehouse, teklif=teklif, birim=birim
    ).first()
    available = bal.available if bal is not None else Decimal("0")
    if available < miktar:
        raise ValidationError(
            f"ATP yetersiz: available={available}, istenen={miktar} {birim}."
        )


def _prepare_rows(
    *,
    actor,
    alici_firma,
    satis_kanali,
    rows: list[BulkRowInput],
    now,
) -> tuple[list[BulkRowOk], list[BulkRowError]]:
    accepted: list[BulkRowOk] = []
    errors: list[BulkRowError] = []
    seen_sku: set[str] = set()

    for row in rows:
        sku = (row.sku or "").strip()
        try:
            if not sku:
                raise ValidationError("sku zorunlu.")
            if sku in seen_sku:
                raise ValidationError("Aynı CSV içinde tekrarlayan sku.")
            seen_sku.add(sku)
            if row.miktar <= 0:
                raise ValidationError("miktar pozitif olmalı.")

            varyant = (
                Varyant.objects.select_related("urun")
                .filter(sku=sku, aktif=True)
                .first()
            )
            if varyant is None:
                raise ValidationError("Varyant bulunamadı veya pasif.")

            quote = pricing_service.quote(
                alici_firma=alici_firma,
                satis_kanali=satis_kanali,
                varyant=varyant,
                kullanici=actor,
                now=now,
            )
            birim = birim_from_teklif(quote.teklif)
            if row.birim is not None and row.birim.strip():
                istenen = row.birim.strip().upper()
                if istenen != birim:
                    raise ValidationError(
                        f"Birim uyumsuz: CSV={istenen}, teklif={birim} "
                        "(dönüşüm yok)."
                    )
            _assert_atp(teklif=quote.teklif, miktar=row.miktar, birim=birim)
            accepted.append(
                BulkRowOk(
                    satir_no=row.satir_no,
                    sku=sku,
                    varyant_id=varyant.pk,
                    miktar=row.miktar,
                    birim=birim,
                    quote_id=quote.pk,
                )
            )
        except (ValidationError, PermissionDenied) as exc:
            reason = str(exc)
            if isinstance(exc, ValidationError) and getattr(exc, "messages", None):
                reason = "; ".join(str(m) for m in exc.messages)
            errors.append(
                BulkRowError(
                    satir_no=row.satir_no, sku=sku or "?", hata=reason[:255]
                )
            )
    return accepted, errors


def toplu_siparis(
    *,
    actor,
    satis_kanali,
    idempotency_key: str,
    rows: list[BulkRowInput] | None = None,
    csv_text: str | None = None,
    now=None,
    replace_cart: bool = True,
) -> BulkOrderResult:
    """CSV/satır → (kısmi) sepet → checkout → Order.

    Hiç geçerli satır yoksa Order oluşturulmaz; errors dolu döner.
    """
    now = now or timezone.now()
    key = (idempotency_key or "").strip()
    if not key:
        raise ValidationError("idempotency_key zorunlu.")
    if len(key) > 64:
        raise ValidationError(
            "idempotency_key en fazla 64 karakter (Order/Checkout)."
        )

    alici_firma = getattr(actor, "firma", None)
    try:
        _assert_buyer_actor(actor, alici_firma)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="order.bulk",
            entity_type="Order",
            entity_id="",
            success=False,
            reason=str(exc),
            detail={"idempotency_key": key},
        )
        raise

    existing = Order.objects.filter(
        alici_firma=alici_firma, idempotency_key=key
    ).first()
    if existing is not None:
        return BulkOrderResult(
            order=existing,
            checkout_attempt=existing.checkout_attempt,
            accepted=[],
            errors=[],
            replayed=True,
        )

    if rows is None:
        if csv_text is None:
            raise ValidationError("rows veya csv_text zorunlu.")
        rows = parse_csv(csv_text)

    accepted, errors = _prepare_rows(
        actor=actor,
        alici_firma=alici_firma,
        satis_kanali=satis_kanali,
        rows=rows,
        now=now,
    )
    if not accepted:
        record_audit_durable(
            actor=actor,
            action="order.bulk",
            entity_type="Order",
            entity_id="",
            success=False,
            reason="Geçerli satır yok.",
            detail={
                "idempotency_key": key,
                "error_count": len(errors),
                "errors": [
                    {"satir_no": e.satir_no, "sku": e.sku, "hata": e.hata}
                    for e in errors[:50]
                ],
            },
        )
        return BulkOrderResult(
            order=None,
            checkout_attempt=None,
            accepted=[],
            errors=errors,
            replayed=False,
        )

    try:
        with domain_atomic():
            cart = al_veya_olustur_sepet(actor=actor, alici_firma=alici_firma)
            if replace_cart:
                CartLine.objects.filter(cart=cart).delete()
            for ok in accepted:
                quote = PriceQuote.objects.get(pk=ok.quote_id)
                satir_ekle(
                    actor=actor, price_quote=quote, miktar=ok.miktar, now=now
                )
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and getattr(exc, "messages", None):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.bulk",
            entity_type="Order",
            entity_id="",
            success=False,
            reason=reason[:255],
            detail={"idempotency_key": key},
        )
        raise

    try:
        co = checkout_servisi.checkout(
            actor=actor, cart=cart, idempotency_key=key, now=now
        )
        order = order_servisi.olustur_from_checkout(
            actor=actor, checkout_attempt=co.attempt, now=now
        )
    except (ValidationError, PermissionDenied) as exc:
        reason = str(exc)
        if isinstance(exc, ValidationError) and getattr(exc, "messages", None):
            reason = "; ".join(str(m) for m in exc.messages)
        record_audit_durable(
            actor=actor,
            action="order.bulk",
            entity_type="Order",
            entity_id="",
            success=False,
            reason=reason[:255],
            detail={"idempotency_key": key},
        )
        raise

    record_audit(
        actor=actor,
        action="order.bulk",
        entity_type="Order",
        entity_id=str(order.pk),
        success=True,
        detail={
            "idempotency_key": key,
            "accepted": len(accepted),
            "errors": len(errors),
            "order_id": order.pk,
        },
    )
    return BulkOrderResult(
        order=order,
        checkout_attempt=co.attempt,
        accepted=accepted,
        errors=errors,
        replayed=False,
    )
