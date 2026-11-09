"""Cari bakiye projeksiyonu (F5-011; U-005 platform↔alıcı)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import Firma
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm
from finans.models import CariHesap, LedgerEntry
from finans.services.ledger_servisi import POST_LEDGER


def platform_karsi() -> Firma:
    return ensure_platform_firma()


def get_or_create_locked(
    *,
    firma: Firma,
    para_birimi: str,
    karsi_firma: Firma | None = None,
) -> CariHesap:
    karsi = karsi_firma or platform_karsi()
    pb = (para_birimi or "").strip().upper()
    row = (
        CariHesap.objects.select_for_update()
        .filter(firma=firma, karsi_firma=karsi, para_birimi=pb)
        .first()
    )
    if row is not None:
        return row
    row = CariHesap(
        firma=firma,
        karsi_firma=karsi,
        para_birimi=pb,
        bakiye=Decimal("0.00"),
        kredi_limiti=Decimal("0.00"),
    )
    row.save()
    return CariHesap.objects.select_for_update().get(pk=row.pk)


def _save_bakiye(hesap: CariHesap, *, bakiye: Decimal) -> None:
    hesap.bakiye = bakiye
    hesap._allow_cari_update = True
    try:
        hesap.save(update_fields=["bakiye", "guncelleme_tarihi"])
    finally:
        hesap._allow_cari_update = False


def uygula_ledger_entry(entry: LedgerEntry) -> CariHesap:
    """Ledger satırını cari projeksiyona yansıt (aynı atomic içinde çağrılmalı)."""
    if entry.karsi_firma_id is None:
        # Karşı taraf yoksa cari güncelleme yok
        raise ValidationError("Cari için karsi_firma zorunlu (U-005).")
    hesap = get_or_create_locked(
        firma=entry.firma,
        para_birimi=entry.para_birimi,
        karsi_firma=entry.karsi_firma,
    )
    delta = entry.tutar if entry.yon == LedgerEntry.Yon.BORC else -entry.tutar
    yeni = hesap.bakiye + delta
    if hesap.kredi_limiti > 0 and yeni > hesap.kredi_limiti:
        raise ValidationError(
            f"Kredi limiti aşıldı: bakiye={yeni}, limit={hesap.kredi_limiti}."
        )
    _save_bakiye(hesap, bakiye=yeni)
    return hesap


def set_kredi_limiti(*, actor, hesap: CariHesap, limit: Decimal) -> CariHesap:
    if not has_perm(actor, POST_LEDGER):
        raise PermissionDenied("Kredi limiti için finans yetkisi yok.")
    if not isinstance(limit, Decimal):
        limit = Decimal(str(limit))
    if limit < 0:
        raise ValidationError({"kredi_limiti": "Negatif olamaz."})
    hesap.kredi_limiti = limit.quantize(Decimal("0.01"))
    hesap._allow_cari_update = True
    try:
        hesap.save(update_fields=["kredi_limiti", "guncelleme_tarihi"])
    finally:
        hesap._allow_cari_update = False
    return hesap


def assert_can_view_cari(actor, hesap: CariHesap) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Cari görüntüleme için kimlik gerekli.")
    if can_view_all_tenants(actor):
        return
    if getattr(actor, "firma_id", None) == hesap.firma_id:
        return
    raise PermissionDenied("Başka firmanın carisini göremezsiniz.")
