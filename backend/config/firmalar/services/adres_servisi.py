"""F9-017 — FirmaAdresi self-service yazımı (tenant = actor.firma).

Güvenli varsayımlar (ADR yok → FINAL-REPORT KARAR GEREKTİ kapandı uygulama ile):
- Yazma: manage_users (firma yöneticisi) veya manage_all_users (yalnız kendi firma).
- Silme: hard delete (modelde soft-delete yok; ticaret ledger değil).
- varsayilan=True: aynı firma+tip diğer varsayılanlar kapatılır.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import FirmaAdresi
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import can_manage_all_users, has_perm


_VALID_TIP = {c[0] for c in FirmaAdresi.TIP}


def _can_manage_addresses(actor) -> bool:
    return can_manage_all_users(actor) or has_perm(actor, P["manage_users"])


def _require_manage(actor, *, action: str):
    if _can_manage_addresses(actor):
        return
    record_audit_durable(
        actor=actor,
        action=action,
        entity_type="FirmaAdresi",
        entity_id="",
        success=False,
        reason="yetki_yok",
    )
    raise PermissionDenied("Adres yönetimi için manage_users gerekir.")


def _require_own_firma(actor, firma):
    if getattr(actor, "firma_id", None) != getattr(firma, "pk", None):
        record_audit_durable(
            actor=actor,
            action="firmalar.adres.firma_uyumsuz",
            entity_type="FirmaAdresi",
            entity_id="",
            success=False,
            reason="firma_uyumsuz",
        )
        raise PermissionDenied("Adres yalnız kendi firmasında yönetilir.")


def _normalize_tip(tip: str | None) -> str:
    t = (tip or "merkez").strip().lower()
    if t not in _VALID_TIP:
        raise ValidationError({"tip": f"Geçersiz tip. İzinli: {sorted(_VALID_TIP)}"})
    return t


def _clear_other_defaults(*, firma_id: int, tip: str, keep_pk: int | None = None):
    qs = FirmaAdresi.objects.filter(firma_id=firma_id, tip=tip, varsayilan=True)
    if keep_pk is not None:
        qs = qs.exclude(pk=keep_pk)
    qs.update(varsayilan=False)


def olustur(
    *,
    actor,
    tip: str | None = None,
    il: str,
    ilce: str = "",
    adres: str,
    varsayilan: bool = False,
) -> FirmaAdresi:
    _require_manage(actor, action="firmalar.adres.create_denied")
    firma = getattr(actor, "firma", None)
    if firma is None:
        raise PermissionDenied("Firma yok.")
    _require_own_firma(actor, firma)
    tip_n = _normalize_tip(tip)
    il_n = (il or "").strip()
    if not il_n:
        raise ValidationError({"il": "Zorunlu."})
    adres_n = (adres or "").strip()
    if not adres_n:
        raise ValidationError({"adres": "Zorunlu."})
    with domain_atomic():
        if varsayilan:
            _clear_other_defaults(firma_id=firma.pk, tip=tip_n)
        row = FirmaAdresi(
            firma=firma,
            tip=tip_n,
            il=il_n,
            ilce=(ilce or "").strip(),
            adres=adres_n,
            varsayilan=bool(varsayilan),
        )
        row.full_clean()
        row.save()
        record_audit(
            actor=actor,
            action="firmalar.adres.create",
            entity_type="FirmaAdresi",
            entity_id=str(row.pk),
            success=True,
        )
    return row


def guncelle(
    *,
    actor,
    row: FirmaAdresi,
    tip: str | None = None,
    il: str | None = None,
    ilce: str | None = None,
    adres: str | None = None,
    varsayilan: bool | None = None,
) -> FirmaAdresi:
    _require_manage(actor, action="firmalar.adres.update_denied")
    _require_own_firma(actor, row.firma)
    tip_n = _normalize_tip(tip) if tip is not None else row.tip
    il_n = row.il if il is None else (il or "").strip()
    if not il_n:
        raise ValidationError({"il": "Zorunlu."})
    adres_n = row.adres if adres is None else (adres or "").strip()
    if not adres_n:
        raise ValidationError({"adres": "Zorunlu."})
    ilce_n = row.ilce if ilce is None else (ilce or "").strip()
    vars_n = row.varsayilan if varsayilan is None else bool(varsayilan)
    with domain_atomic():
        if vars_n:
            _clear_other_defaults(firma_id=row.firma_id, tip=tip_n, keep_pk=row.pk)
        row.tip = tip_n
        row.il = il_n
        row.ilce = ilce_n
        row.adres = adres_n
        row.varsayilan = vars_n
        row.full_clean()
        row.save()
        record_audit(
            actor=actor,
            action="firmalar.adres.update",
            entity_type="FirmaAdresi",
            entity_id=str(row.pk),
            success=True,
        )
    return row


def sil(*, actor, row: FirmaAdresi) -> None:
    _require_manage(actor, action="firmalar.adres.delete_denied")
    _require_own_firma(actor, row.firma)
    pk = row.pk
    with domain_atomic():
        row.delete()
        record_audit(
            actor=actor,
            action="firmalar.adres.delete",
            entity_type="FirmaAdresi",
            entity_id=str(pk),
            success=True,
        )


def guncelle_profil(
    *,
    actor,
    first_name: str | None = None,
    last_name: str | None = None,
):
    """Kendi profil: yalnız first_name / last_name (e-posta ayrı verify akışı)."""
    if first_name is None and last_name is None:
        raise ValidationError({"detail": "Güncellenecek alan yok."})
    with domain_atomic():
        if first_name is not None:
            actor.first_name = str(first_name).strip()[:150]
        if last_name is not None:
            actor.last_name = str(last_name).strip()[:150]
        actor.save(update_fields=["first_name", "last_name"])
        record_audit(
            actor=actor,
            action="firmalar.profil.update",
            entity_type="Kullanici",
            entity_id=str(actor.pk),
            success=True,
        )
    return actor
