"""HedgeEntry yazımı (ADR-0012 F5-K7)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import has_perm
from finans.models import HedgeEntry
from finans.services.ledger_servisi import POST_LEDGER


def _assert_can_hedge(actor) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Hedge yazımı için kimlik gerekli.")
    if has_perm(actor, POST_LEDGER):
        return
    raise PermissionDenied("Hedge yazma yetkisi yok.")


def kaydet_hedge(
    *,
    actor,
    grams: Decimal,
    idempotency_key: str,
    metal_kodu: str = "",
    aciklama: str = "",
) -> HedgeEntry:
    try:
        _assert_can_hedge(actor)
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="finans.hedge.post_denied",
            entity_type="HedgeEntry",
            entity_id="",
            success=False,
            reason=str(exc),
        )
        raise

    key = (idempotency_key or "").strip()
    if not key:
        raise ValidationError({"idempotency_key": "Zorunlu."})
    existing = HedgeEntry.objects.filter(idempotency_key=key).first()
    if existing is not None:
        return existing

    if not isinstance(grams, Decimal):
        grams = Decimal(str(grams))
    if grams == 0:
        raise ValidationError({"grams": "grams sıfır olamaz."})

    try:
        with domain_atomic():
            row = HedgeEntry(
                grams=grams,
                metal_kodu=(metal_kodu or "").strip(),
                idempotency_key=key,
                aciklama=aciklama or "",
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            row.save()
            record_audit(
                actor=actor,
                action="finans.hedge.post",
                entity_type="HedgeEntry",
                entity_id=str(row.pk),
                success=True,
                detail={"grams": str(grams), "metal_kodu": row.metal_kodu},
            )
            return row
    except Exception as exc:
        record_audit_durable(
            actor=actor,
            action="finans.hedge.post_failed",
            entity_type="HedgeEntry",
            entity_id="",
            success=False,
            reason=str(exc)[:255],
        )
        raise


def hedge_has_total() -> Decimal:
    from django.db.models import Sum

    total = HedgeEntry.objects.aggregate(s=Sum("grams"))["s"]
    return total if total is not None else Decimal("0")
