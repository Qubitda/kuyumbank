"""F5-031 — Platform finans ops okuma (view_all zorunlu)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied

from firmalar.services.yetki_servisi import can_view_all_tenants
from finans.models import CariHesap, LedgerEntry, PaymentIntent


def require_ops_finance(actor) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Ops finans için kimlik gerekli.")
    if not can_view_all_tenants(actor):
        raise PermissionDenied(
            "Finans ops yalnız view_all platform kullanıcıları içindir."
        )


def present_cari_ops(hesap: CariHesap) -> dict:
    return {
        "id": hesap.pk,
        "firma_id": hesap.firma_id,
        "karsi_firma_id": hesap.karsi_firma_id,
        "para_birimi": hesap.para_birimi,
        "bakiye": str(hesap.bakiye),
        "kredi_limiti": str(hesap.kredi_limiti),
        "guncelleme_tarihi": (
            hesap.guncelleme_tarihi.isoformat() if hesap.guncelleme_tarihi else None
        ),
    }


def present_ledger_ops(entry: LedgerEntry) -> dict:
    return {
        "id": entry.pk,
        "firma_id": entry.firma_id,
        "karsi_firma_id": entry.karsi_firma_id,
        "yon": entry.yon,
        "tutar": str(entry.tutar),
        "para_birimi": entry.para_birimi,
        "hareket_tipi": entry.hareket_tipi,
        "referans_tip": entry.referans_tip,
        "referans_id": entry.referans_id,
        "olusturma_tarihi": (
            entry.olusturma_tarihi.isoformat() if entry.olusturma_tarihi else None
        ),
    }


def present_payment_ops(pi: PaymentIntent) -> dict:
    return {
        "id": pi.pk,
        "order_id": pi.order_id,
        "alici_firma_id": pi.alici_firma_id,
        "durum": pi.durum,
        "tutar": str(pi.tutar),
        "para_birimi": pi.para_birimi,
        "olusturma_tarihi": (
            pi.olusturma_tarihi.isoformat() if pi.olusturma_tarihi else None
        ),
    }


def liste_cari(*, actor, limit: int = 100) -> list[dict]:
    require_ops_finance(actor)
    qs = CariHesap.objects.order_by("-guncelleme_tarihi", "-pk")[
        : max(1, min(limit, 200))
    ]
    return [present_cari_ops(h) for h in qs]


def liste_ledger(*, actor, limit: int = 100) -> list[dict]:
    require_ops_finance(actor)
    qs = LedgerEntry.objects.order_by("-olusturma_tarihi", "-pk")[
        : max(1, min(limit, 200))
    ]
    return [present_ledger_ops(e) for e in qs]


def liste_payments(*, actor, limit: int = 100) -> list[dict]:
    require_ops_finance(actor)
    qs = PaymentIntent.objects.order_by("-olusturma_tarihi", "-pk")[
        : max(1, min(limit, 200))
    ]
    return [present_payment_ops(p) for p in qs]


def ozet(*, actor) -> dict:
    require_ops_finance(actor)
    return {
        "ops": True,
        "cari_count": CariHesap.objects.count(),
        "ledger_count": LedgerEntry.objects.count(),
        "payment_intent_count": PaymentIntent.objects.count(),
        "recent_ledger": liste_ledger(actor=actor, limit=20),
        "recent_payments": liste_payments(actor=actor, limit=20),
    }
