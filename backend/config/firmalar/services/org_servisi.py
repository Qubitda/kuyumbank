"""F10-010 — OrgBirimi / OrgUyeligi yazımı (ADR-0015)."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.models import OrgBirimi, OrgUyeligi
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import (
    can_view_all_tenants,
    is_platform_firm_user,
    require_perm,
)


def _require_manage(actor, *, firma, action: str):
    try:
        require_perm(actor, P["manage_org"], message="Org yönetimi için manage_org gerekir.")
    except PermissionDenied:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="OrgBirimi",
            entity_id="",
            success=False,
            reason="yetki_yok",
        )
        raise
    if can_view_all_tenants(actor) or is_platform_firm_user(actor):
        return
    if getattr(actor, "firma_id", None) != firma.pk:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="OrgBirimi",
            entity_id="",
            success=False,
            reason="firma_uyumsuz",
        )
        raise PermissionDenied("Org yalnız kendi firmasında yönetilir.")


def olustur_birim(
    *,
    actor,
    firma,
    kod: str,
    ad: str,
    parent: OrgBirimi | None = None,
    aktif: bool = True,
) -> OrgBirimi:
    _require_manage(actor, firma=firma, action="firmalar.org.create_denied")
    kod_n = (kod or "").strip().upper()
    if not kod_n:
        raise ValidationError({"kod": "Zorunlu."})
    if parent is not None and parent.firma_id != firma.pk:
        raise ValidationError({"parent": "Parent aynı firmada olmalı."})

    with domain_atomic():
        ob = OrgBirimi(
            firma=firma,
            parent=parent,
            kod=kod_n,
            ad=(ad or "").strip() or kod_n,
            aktif=aktif,
        )
        ob.save()
        record_audit(
            actor=actor,
            action="firmalar.org.created",
            entity_type="OrgBirimi",
            entity_id=str(ob.pk),
            success=True,
            detail={"firma_id": firma.pk, "kod": ob.kod},
        )
        return ob


def uye_ekle(*, actor, org_birimi: OrgBirimi, kullanici) -> OrgUyeligi:
    _require_manage(
        actor, firma=org_birimi.firma, action="firmalar.org.uye_denied"
    )
    if kullanici.firma_id != org_birimi.firma_id:
        raise ValidationError("Kullanıcı org firmasına ait değil.")

    existing = OrgUyeligi.objects.filter(
        kullanici=kullanici, org_birimi=org_birimi
    ).first()
    if existing is not None:
        return existing

    with domain_atomic():
        uy = OrgUyeligi(kullanici=kullanici, org_birimi=org_birimi)
        uy.save()
        record_audit(
            actor=actor,
            action="firmalar.org.uye_eklendi",
            entity_type="OrgUyeligi",
            entity_id=str(uy.pk),
            success=True,
            detail={
                "org_birimi_id": org_birimi.pk,
                "kullanici_id": kullanici.pk,
            },
        )
        return uy


def assert_org_in_firma(*, org: OrgBirimi | None, firma) -> None:
    if org is None:
        return
    if org.firma_id != firma.pk:
        raise ValidationError({"sube": "Org birimi sipariş firmasına ait değil."})
    if not org.aktif:
        raise ValidationError({"sube": "Org birimi pasif."})
