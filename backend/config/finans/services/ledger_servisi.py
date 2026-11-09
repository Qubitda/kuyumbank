"""Finans ledger yazımı — append-only + contra (ADR-0012 F5-K2…K4)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import Firma
from firmalar.services.audit_servisi import domain_atomic
from firmalar.services.yetki_servisi import has_perm
from finans.models import LedgerEntry
from finans.services.finans_audit import (
    record_finans_audit,
    record_finans_audit_durable,
)

POST_LEDGER = "finans.post_ledger"


def _assert_can_post(actor) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Ledger yazımı için kimlik gerekli.")
    if has_perm(actor, POST_LEDGER):
        return
    raise PermissionDenied("Finans ledger yazma yetkisi yok.")


def _normalize_tutar(tutar: Decimal) -> Decimal:
    if not isinstance(tutar, Decimal):
        tutar = Decimal(str(tutar))
    if tutar <= 0:
        raise ValidationError({"tutar": "Tutar sıfırdan büyük olmalı."})
    return tutar.quantize(Decimal("0.01"))


def _order_ref(referans_tip: str, referans_id: str) -> str:
    if (referans_tip or "") == "Order":
        return str(referans_id or "")
    return ""


def kaydet_hareket(
    *,
    actor,
    firma: Firma,
    tutar: Decimal,
    para_birimi: str,
    yon: str,
    hareket_tipi: str,
    idempotency_key: str,
    karsi_firma: Firma | None = None,
    referans_tip: str = "",
    referans_id: str = "",
    aciklama: str = "",
    contra_of: LedgerEntry | None = None,
) -> LedgerEntry:
    """Yeni ledger satırı. Aynı (firma, idempotency_key) → mevcut satır."""
    pb = (para_birimi or "").strip().upper() or "TRY"
    oref = _order_ref(referans_tip, referans_id)
    try:
        _assert_can_post(actor)
    except PermissionDenied as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.ledger.post_denied",
            amount=tutar if tutar is not None else Decimal("0.00"),
            currency=pb,
            order_ref=oref,
            entity_type="Firma",
            entity_id=str(getattr(firma, "pk", "")),
            success=False,
            reason=str(exc),
            extra={"firma_id": getattr(firma, "pk", None)},
        )
        raise

    key = (idempotency_key or "").strip()
    if not key:
        raise ValidationError({"idempotency_key": "Zorunlu."})

    existing = LedgerEntry.objects.filter(firma=firma, idempotency_key=key).first()
    if existing is not None:
        return existing

    tutar_n = _normalize_tutar(tutar)
    if yon not in LedgerEntry.Yon.values:
        raise ValidationError({"yon": "Geçersiz yön."})
    if hareket_tipi not in LedgerEntry.HareketTipi.values:
        raise ValidationError({"hareket_tipi": "Geçersiz hareket tipi."})

    try:
        with domain_atomic():
            entry = LedgerEntry(
                firma=firma,
                karsi_firma=karsi_firma,
                tutar=tutar_n,
                para_birimi=(para_birimi or "").strip().upper(),
                yon=yon,
                hareket_tipi=hareket_tipi,
                referans_tip=referans_tip or "",
                referans_id=str(referans_id or ""),
                contra_of=contra_of,
                idempotency_key=key,
                aciklama=aciklama or "",
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            entry.save()
            if entry.karsi_firma_id is not None:
                from finans.services import cari_servisi

                cari_servisi.uygula_ledger_entry(entry)
            record_finans_audit(
                actor=actor,
                action="finans.ledger.post",
                amount=tutar_n,
                currency=entry.para_birimi,
                order_ref=_order_ref(entry.referans_tip, entry.referans_id),
                entity_type="LedgerEntry",
                entity_id=str(entry.pk),
                success=True,
                extra={
                    "firma_id": firma.pk,
                    "yon": yon,
                    "hareket_tipi": hareket_tipi,
                    "referans_tip": referans_tip,
                    "referans_id": str(referans_id or ""),
                },
            )
            return entry
    except Exception as exc:
        record_finans_audit_durable(
            actor=actor,
            action="finans.ledger.post_failed",
            amount=tutar_n if "tutar_n" in locals() else tutar,
            currency=pb,
            order_ref=oref,
            entity_type="Firma",
            entity_id=str(firma.pk),
            success=False,
            reason=str(exc)[:255],
        )
        raise


def contra_hareket(
    *,
    actor,
    entry: LedgerEntry,
    idempotency_key: str,
    aciklama: str = "",
) -> LedgerEntry:
    """Ters kayıt: yön flip; tip CONTRA; silme yok."""
    if entry.hareket_tipi == LedgerEntry.HareketTipi.CONTRA:
        raise ValidationError("CONTRA satırı yeniden contra edilemez.")
    existing = LedgerEntry.objects.filter(contra_of=entry).first()
    if existing is not None:
        return existing

    opposite = (
        LedgerEntry.Yon.ALACAK
        if entry.yon == LedgerEntry.Yon.BORC
        else LedgerEntry.Yon.BORC
    )
    return kaydet_hareket(
        actor=actor,
        firma=entry.firma,
        karsi_firma=entry.karsi_firma,
        tutar=entry.tutar,
        para_birimi=entry.para_birimi,
        yon=opposite,
        hareket_tipi=LedgerEntry.HareketTipi.CONTRA,
        idempotency_key=idempotency_key,
        referans_tip=entry.referans_tip,
        referans_id=entry.referans_id,
        aciklama=aciklama or f"Contra of LE#{entry.pk}",
        contra_of=entry,
    )
