"""F5-040 — Alıcı kredi / cari görünürlüğü (maskeli); checkout öncesi kontrol."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.services.yetki_servisi import can_view_all_tenants
from finans.models import CariHesap
from finans.services import cari_servisi


@dataclass(frozen=True)
class CreditSummary:
    para_birimi: str
    bakiye: Decimal
    kredi_limiti: Decimal
    kullanilabilir: Decimal | None  # None = limit kapalı (sınırsız görünüm)
    limit_aktif: bool


def require_buyer_firma(actor):
    """Alıcı-only tenant; ops/tedarikçi reddedilir (F5-040/030)."""
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Kredi özeti için kimlik gerekli.")
    if can_view_all_tenants(actor):
        raise PermissionDenied(
            "Ops kullanıcıları /credit/me yerine ops araçlarını kullanır."
        )
    firma = getattr(actor, "firma", None)
    if firma is None or not getattr(firma, "alici_mi", False):
        raise PermissionDenied("Yalnız alıcı firma kredi özetini görür.")
    return firma


def _buyer_firma(actor):
    return require_buyer_firma(actor)


def _get_or_empty(*, firma, para_birimi: str) -> CariHesap | None:
    pb = (para_birimi or "").strip().upper()
    karsi = cari_servisi.platform_karsi()
    return CariHesap.objects.filter(
        firma=firma, karsi_firma=karsi, para_birimi=pb
    ).first()


def ozet_for_actor(*, actor, para_birimi: str = "TRY") -> CreditSummary:
    """Maskeli özet: karsi_firma / ledger id yok."""
    firma = _buyer_firma(actor)
    pb = (para_birimi or "TRY").strip().upper()
    if len(pb) != 3:
        raise ValidationError({"para_birimi": "ISO 4217 zorunlu."})
    hesap = _get_or_empty(firma=firma, para_birimi=pb)
    bakiye = hesap.bakiye if hesap else Decimal("0.00")
    limit = hesap.kredi_limiti if hesap else Decimal("0.00")
    limit_aktif = limit > 0
    kullanilabilir = (limit - bakiye) if limit_aktif else None
    return CreditSummary(
        para_birimi=pb,
        bakiye=bakiye,
        kredi_limiti=limit,
        kullanilabilir=kullanilabilir,
        limit_aktif=limit_aktif,
    )


def present_credit(summary: CreditSummary) -> dict:
    return {
        "para_birimi": summary.para_birimi,
        "bakiye": str(summary.bakiye),
        "kredi_limiti": str(summary.kredi_limiti),
        "kullanilabilir": (
            str(summary.kullanilabilir) if summary.kullanilabilir is not None else None
        ),
        "limit_aktif": summary.limit_aktif,
    }


def assert_musait(*, actor, tutar: Decimal, para_birimi: str = "TRY") -> CreditSummary:
    """Checkout öncesi: limit aktifken bakiye+tutar > limit → net hata."""
    if not isinstance(tutar, Decimal):
        tutar = Decimal(str(tutar))
    if tutar <= 0:
        raise ValidationError({"tutar": "Tutar sıfırdan büyük olmalı."})
    summary = ozet_for_actor(actor=actor, para_birimi=para_birimi)
    if summary.limit_aktif:
        proje = summary.bakiye + tutar
        if proje > summary.kredi_limiti:
            raise ValidationError(
                f"Kredi limiti aşımı: bakiye={summary.bakiye}, "
                f"ek={tutar}, limit={summary.kredi_limiti}."
            )
    return summary
