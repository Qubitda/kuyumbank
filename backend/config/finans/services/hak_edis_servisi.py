"""F5-022 — Tedarikçi hak ediş iskeleti (tetik: QC PASS; oran yok)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum
from django.utils import timezone

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import has_perm, require_perm
from finans.models import TedarikciHakEdis
from kalite.models import QualityInspection
from siparis.models import Order

Q4 = Decimal("0.0001")


def _q4(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Q4, rounding=ROUND_HALF_UP)


def _vade_gun() -> int:
    raw = getattr(settings, "SUPPLIER_ACCRUAL_VADE_GUN", 0)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def unpaid_supplier_has_total() -> Decimal:
    """HAKEDILDI + BEKLEMEDE gram toplamı (ödeme çıkışı yokken unpaid)."""
    total = (
        TedarikciHakEdis.objects.filter(
            durum__in=[
                TedarikciHakEdis.Durum.HAKEDILDI,
                TedarikciHakEdis.Durum.BEKLEMEDE,
            ]
        )
        .aggregate(s=Sum("gram"))
        .get("s")
    )
    return _q4(total if total is not None else Decimal("0"))


def _line_groups(order: Order) -> dict[int, dict]:
    """tedarikci_id → {gram, para_birimi}."""
    groups: dict[int, dict] = {}
    lines = list(
        order.lines.select_related(
            "stock_reservation__teklif",
            "price_lock__quote",
        )
    )
    single = len(lines) == 1
    for line in lines:
        tedarikci_id = line.stock_reservation.teklif.tedarikci_id
        bucket = groups.setdefault(
            tedarikci_id,
            {"gram": Decimal("0"), "para_birimi": line.para_birimi or ""},
        )
        if line.birim == "GRAM":
            bucket["gram"] += line.miktar
        elif single:
            # ADET/KARAT tek satır: quote.gram (HAS); çok satırda 0
            quote = getattr(line.price_lock, "quote", None)
            if quote is not None and getattr(quote, "gram", None):
                bucket["gram"] += Decimal(str(quote.gram))
        if not bucket["para_birimi"]:
            bucket["para_birimi"] = line.para_birimi or ""
    return groups


def kaydet_qc_pass(
    *,
    actor,
    inspection: QualityInspection,
    now=None,
) -> list[TedarikciHakEdis]:
    """QC PASS sonrası hak ediş kaydı (idempotent per inspection+tedarikçi)."""
    now = now or timezone.now()
    if inspection.durum != QualityInspection.Durum.PASS:
        raise ValidationError("Hak ediş yalnız PASS inspection için.")

    order = inspection.order
    groups = _line_groups(order)
    if not groups:
        raise ValidationError("Siparişte tedarikçi satırı yok.")

    vade_gun = _vade_gun()
    vade_tarihi = now + timedelta(days=vade_gun)
    hedef_durum = (
        TedarikciHakEdis.Durum.HAKEDILDI
        if vade_gun == 0
        else TedarikciHakEdis.Durum.BEKLEMEDE
    )

    created: list[TedarikciHakEdis] = []
    with domain_atomic():
        for tedarikci_id, meta in groups.items():
            key = f"he:insp:{inspection.pk}:ted:{tedarikci_id}"
            existing = TedarikciHakEdis.objects.filter(idempotency_key=key).first()
            if existing is not None:
                created.append(existing)
                continue
            row = TedarikciHakEdis(
                order=order,
                quality_inspection=inspection,
                tedarikci_firma_id=tedarikci_id,
                durum=hedef_durum,
                gram=_q4(meta["gram"]),
                tutar=None,
                para_birimi=(meta["para_birimi"] or "").strip().upper(),
                vade_tarihi=vade_tarihi,
                hak_edis_tarihi=now if hedef_durum == TedarikciHakEdis.Durum.HAKEDILDI else None,
                idempotency_key=key,
                aciklama=f"QC PASS inspection={inspection.pk}",
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            row.save()
            created.append(row)
            record_audit(
                actor=actor,
                action="finans.hak_edis.created",
                entity_type="TedarikciHakEdis",
                entity_id=str(row.pk),
                success=True,
                detail={
                    "order_id": order.pk,
                    "inspection_id": inspection.pk,
                    "tedarikci_id": tedarikci_id,
                    "durum": row.durum,
                    "gram": str(row.gram),
                    "vade_gun": vade_gun,
                },
            )
    return created


def hakedise_cevir(*, actor, hak_edis: TedarikciHakEdis, now=None) -> TedarikciHakEdis:
    """BEKLEMEDE → HAKEDILDI (vade sonrası veya manuel)."""
    now = now or timezone.now()
    try:
        require_perm(
            actor,
            P["manage_hak_edis"],
            message="Hak ediş için manage_hak_edis gerekir.",
        )
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="finans.hak_edis.transition_denied",
            entity_type="TedarikciHakEdis",
            entity_id=str(hak_edis.pk),
            success=False,
            reason=str(exc),
        )
        raise

    with domain_atomic():
        locked = TedarikciHakEdis.objects.select_for_update().get(pk=hak_edis.pk)
        if locked.durum == TedarikciHakEdis.Durum.HAKEDILDI:
            return locked
        if locked.durum != TedarikciHakEdis.Durum.BEKLEMEDE:
            raise ValidationError(f"Hak ediş geçilemez; durum={locked.durum}")
        locked.durum = TedarikciHakEdis.Durum.HAKEDILDI
        locked.hak_edis_tarihi = now
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "hak_edis_tarihi"])
        finally:
            locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="finans.hak_edis.hakedildi",
            entity_type="TedarikciHakEdis",
            entity_id=str(locked.pk),
            success=True,
            detail={"durum": locked.durum},
        )
        return locked


def actor_can_manage(actor) -> bool:
    return bool(actor and has_perm(actor, P["manage_hak_edis"]))
