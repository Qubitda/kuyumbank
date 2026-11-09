"""F5-013 — Finans audit zorunlu alan sözleşmesi.

Zorunlu: actor (başarılıda), success, detail.amount, detail.currency, detail.order_ref.
AuditOlay şeması değişmez; sözleşme detail JSON + actor/success alanlarında.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

from firmalar.services.audit_servisi import record_audit, record_audit_durable

REQUIRED_DETAIL_KEYS = ("amount", "currency", "order_ref")


def build_finans_detail(
    *,
    amount: Decimal | str,
    currency: str,
    order_ref: str = "",
    extra: dict | None = None,
) -> dict:
    if amount is None or amount == "":
        raise ValidationError({"amount": "Finans audit: amount zorunlu."})
    if isinstance(amount, Decimal):
        amount_s = str(amount)
    else:
        amount_s = str(amount).strip()
        if not amount_s:
            raise ValidationError({"amount": "Finans audit: amount zorunlu."})
    pb = (currency or "").strip().upper()
    if len(pb) != 3 or not pb.isalpha():
        raise ValidationError(
            {"currency": "Finans audit: currency ISO 4217 zorunlu."}
        )
    detail = {
        "amount": amount_s,
        "currency": pb,
        "order_ref": str(order_ref or ""),
    }
    if extra:
        # Zorunlu anahtarları ezmeye izin verme
        for k, v in extra.items():
            if k in REQUIRED_DETAIL_KEYS:
                continue
            detail[k] = v
    return detail


def assert_finans_detail(detail: dict) -> None:
    if not isinstance(detail, dict):
        raise ValidationError("Finans audit detail dict olmalı.")
    for key in REQUIRED_DETAIL_KEYS:
        if key not in detail:
            raise ValidationError({key: f"Finans audit: detail.{key} zorunlu."})


def record_finans_audit(
    *,
    actor,
    action: str,
    amount: Decimal | str,
    currency: str,
    order_ref: str = "",
    success: bool = True,
    entity_type: str = "",
    entity_id: str = "",
    reason: str = "",
    extra: dict | None = None,
):
    if success and (actor is None or not getattr(actor, "pk", None)):
        raise ValidationError("Finans audit: başarılı işlemde actor zorunlu.")
    detail = build_finans_detail(
        amount=amount, currency=currency, order_ref=order_ref, extra=extra
    )
    assert_finans_detail(detail)
    return record_audit(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        success=success,
        detail=detail,
        reason=reason,
    )


def record_finans_audit_durable(
    *,
    actor,
    action: str,
    amount: Decimal | str,
    currency: str,
    order_ref: str = "",
    success: bool = False,
    entity_type: str = "",
    entity_id: str = "",
    reason: str = "",
    extra: dict | None = None,
):
    """Fail/deny yolu — amount/currency/order_ref yine zorunlu (F5-013)."""
    detail = build_finans_detail(
        amount=amount, currency=currency, order_ref=order_ref, extra=extra
    )
    assert_finans_detail(detail)
    return record_audit_durable(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        success=success,
        detail=detail,
        reason=reason,
    )
