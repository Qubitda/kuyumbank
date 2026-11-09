"""F6-011 — QC ölçüm kaydı + tolerans + otomatik FAIL / override (F6-K2…K4)."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from kalite.models import QualityInspection, QualityMeasurement
from kalite.services import inspection_servisi, tolerans_motoru
from siparis.birim_constants import SepetBirimi
from siparis.models import OrderLine

_OVERRIDE_MIN = 10


def _tol_settings() -> tuple[Decimal, Decimal]:
    pct = getattr(settings, "QC_GRAM_TOLERANCE_PCT", Decimal("0.50"))
    abs_t = getattr(settings, "QC_GRAM_TOLERANCE_ABS", Decimal("0"))
    return Decimal(str(pct)), Decimal(str(abs_t))


def beklenen_deger(order_line: OrderLine) -> tuple[Decimal, Decimal | None]:
    """F6-K2: beklenen = satır miktarı; GRAM için quote.gram zinciri zorunlu.

    Dönüş: (beklenen, quote_gram_veya_None). Birimler arası dönüşüm yok (U-002).
    """
    miktar = Decimal(order_line.miktar)
    if miktar <= 0:
        raise ValidationError({"miktar": "Beklenen miktar pozitif olmalı."})
    quote_gram = None
    if order_line.birim == SepetBirimi.GRAM:
        lock = order_line.price_lock
        quote = getattr(lock, "quote", None)
        if quote is None:
            raise ValidationError(
                "GRAM QC için PriceLock.quote zorunlu (F6-K2)."
            )
        if quote.gram is None or Decimal(quote.gram) <= 0:
            raise ValidationError(
                "GRAM QC için PriceQuote.gram pozitif olmalı (F6-K2)."
            )
        quote_gram = Decimal(quote.gram)
    return miktar, quote_gram


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_qc"],
            message="QC ölçüm için manage_qc gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="QualityMeasurement",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def _require_override(actor, *, gerekce: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_qc_override"],
            message="Tolerans override için manage_qc_override gerekir.",
        )
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action="kalite.qc.override_denied",
            entity_type="QualityMeasurement",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise
    if len((gerekce or "").strip()) < _OVERRIDE_MIN:
        record_audit_durable(
            actor=actor,
            action="kalite.qc.override_denied",
            entity_type="QualityMeasurement",
            entity_id=entity_id,
            success=False,
            reason="gerekce_kisa",
        )
        raise ValidationError(
            {"override_gerekce": f"Override gerekçesi en az {_OVERRIDE_MIN} karakter (F6-K4)."}
        )


def kaydet_olcum(
    *,
    actor,
    inspection: QualityInspection,
    order_line: OrderLine,
    olculen: Decimal,
    override_gerekce: str = "",
) -> QualityMeasurement:
    """Ölçüm yazar; tolerans dışı → otomatik FAIL (override yoksa)."""
    _require_manage(
        actor,
        action="kalite.qc.olcum_denied",
        entity_id=str(inspection.pk),
    )
    olculen = Decimal(str(olculen))
    if order_line.order_id != inspection.order_id:
        raise ValidationError("order_line bu inspection siparişine ait değil.")
    if (
        inspection.order_line_id
        and inspection.order_line_id != order_line.pk
    ):
        raise ValidationError(
            "Inspection satır-kısıtlı; farklı order_line ölçülemez."
        )

    pct, abs_t = _tol_settings()
    beklenen, quote_gram = beklenen_deger(order_line)
    sonuc = tolerans_motoru.degerlendir(
        beklenen=beklenen,
        olculen=olculen,
        birim=order_line.birim,
        tolerans_pct=pct,
        tolerans_abs=abs_t,
    )

    use_override = False
    gerekce = (override_gerekce or "").strip()
    if not sonuc.uygun:
        if gerekce:
            _require_override(
                actor,
                gerekce=gerekce,
                entity_id=str(inspection.pk),
            )
            use_override = True
        # override yoksa auto-FAIL aşağıda

    with domain_atomic():
        locked = QualityInspection.objects.select_for_update().get(
            pk=inspection.pk
        )
        if locked.durum != QualityInspection.Durum.OLCUMDE:
            raise ValidationError(
                f"Ölçüm yalnız OLCUMDE iken; şu an {locked.durum}."
            )
        m = QualityMeasurement(
            inspection=locked,
            order_line=order_line,
            birim=order_line.birim,
            beklenen=sonuc.beklenen,
            olculen=sonuc.olculen,
            sapma_abs=sonuc.sapma_abs,
            tolerans_pct=sonuc.tolerans_pct,
            tolerans_abs=sonuc.tolerans_abs,
            izin_verilen_sapma=sonuc.izin_verilen,
            sonuc=(
                QualityMeasurement.Sonuc.UYGUN
                if sonuc.uygun
                else QualityMeasurement.Sonuc.SAPMA
            ),
            override_uygulandi=use_override,
            override_gerekce=gerekce if use_override else "",
            quote_gram=quote_gram,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        m.save()
        detail = {
            "measurement_id": m.pk,
            "order_line_id": order_line.pk,
            "beklenen": str(m.beklenen),
            "olculen": str(m.olculen),
            "sonuc": m.sonuc,
            "override": use_override,
        }
        if use_override:
            record_audit(
                actor=actor,
                action="kalite.qc.olcum_override",
                entity_type="QualityMeasurement",
                entity_id=str(m.pk),
                success=True,
                detail={**detail, "gerekce": gerekce[:120]},
            )
        else:
            record_audit(
                actor=actor,
                action="kalite.qc.olcum",
                entity_type="QualityMeasurement",
                entity_id=str(m.pk),
                success=True,
                detail=detail,
            )

        if not sonuc.uygun and not use_override:
            # F6-K4: tolerans dışı → otomatik FAIL (iç içe atomic / savepoint)
            inspection_servisi.fail_et(
                actor=actor,
                inspection=locked,
                reason=f"tolerans_disi QM#{m.pk} sapma={m.sapma_abs}",
            )
        return m
