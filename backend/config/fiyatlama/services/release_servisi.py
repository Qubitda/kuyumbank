"""F5-041 — Contract release plan / dönemsel serbest bırakma.

PriceQuote ve PriceLock’a yazmaz; yalnız release aggregate + audit.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from fiyatlama.models import (
    ContractReleaseEvent,
    ContractReleasePlan,
    FiyatSozlesmesi,
)
from urunler.models import Varyant


def _require_manage(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(
            actor,
            P["manage_sozlesme"],
            message="Release plan için manage_sozlesme gerekir.",
        )
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="ContractReleasePlan",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def serbest_birakilan(plan: ContractReleasePlan) -> Decimal:
    return plan.events.aggregate(s=Sum("miktar")).get("s") or Decimal("0")


def serbest_bakiye(plan: ContractReleasePlan) -> Decimal:
    """Taahhüt kalanı (henüz release edilmemiş)."""
    return plan.toplam_taahhut - serbest_birakilan(plan)


def kullanilabilir(plan: ContractReleasePlan) -> Decimal:
    """Siparişe açık miktar — tüketim takibi iskelet (consumed=0)."""
    return serbest_birakilan(plan) - Decimal("0")


def olustur_plan(
    *,
    actor,
    sozlesme: FiyatSozlesmesi,
    varyant: Varyant,
    birim: str,
    toplam_taahhut: Decimal,
    aciklama: str = "",
) -> ContractReleasePlan:
    _require_manage(actor, action="fiyatlama.release.plan_denied")
    if sozlesme.durum != FiyatSozlesmesi.Durum.AKTIF:
        raise ValidationError("Release plan yalnız AKTIF sözleşmeye bağlanır.")
    if sozlesme.kontrat_tipi != FiyatSozlesmesi.KontratTipi.ALICI:
        raise ValidationError("Release plan yalnız ALICI sözleşmesi için.")
    if not isinstance(toplam_taahhut, Decimal):
        toplam_taahhut = Decimal(str(toplam_taahhut))
    if toplam_taahhut <= 0:
        raise ValidationError({"toplam_taahhut": "Pozitif olmalı."})
    if birim not in ContractReleasePlan.Birim.values:
        raise ValidationError({"birim": "ADET veya GRAM."})

    with domain_atomic():
        plan = ContractReleasePlan(
            sozlesme=sozlesme,
            varyant=varyant,
            birim=birim,
            toplam_taahhut=toplam_taahhut,
            durum=ContractReleasePlan.Durum.TASLAK,
            aciklama=aciklama or "",
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        plan.save()
        record_audit(
            actor=actor,
            action="fiyatlama.release.plan_created",
            entity_type="ContractReleasePlan",
            entity_id=str(plan.pk),
            success=True,
            detail={
                "sozlesme_id": sozlesme.pk,
                "varyant_id": varyant.pk,
                "toplam_taahhut": str(toplam_taahhut),
                "birim": birim,
            },
        )
        return plan


def aktif_et(*, actor, plan: ContractReleasePlan) -> ContractReleasePlan:
    _require_manage(
        actor, action="fiyatlama.release.activate_denied", entity_id=str(plan.pk)
    )
    if plan.durum != ContractReleasePlan.Durum.TASLAK:
        raise ValidationError("Yalnız TASLAK plan aktif edilebilir.")
    with domain_atomic():
        locked = ContractReleasePlan.objects.select_for_update().get(pk=plan.pk)
        locked.durum = ContractReleasePlan.Durum.AKTIF
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "guncelleme_tarihi"])
        finally:
            locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="fiyatlama.release.plan_activated",
            entity_type="ContractReleasePlan",
            entity_id=str(locked.pk),
            success=True,
        )
        return locked


def kapat(*, actor, plan: ContractReleasePlan) -> ContractReleasePlan:
    _require_manage(
        actor, action="fiyatlama.release.close_denied", entity_id=str(plan.pk)
    )
    if plan.durum != ContractReleasePlan.Durum.AKTIF:
        raise ValidationError("Yalnız AKTIF plan kapatılabilir.")
    with domain_atomic():
        locked = ContractReleasePlan.objects.select_for_update().get(pk=plan.pk)
        locked.durum = ContractReleasePlan.Durum.KAPALI
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "guncelleme_tarihi"])
        finally:
            locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="fiyatlama.release.plan_closed",
            entity_type="ContractReleasePlan",
            entity_id=str(locked.pk),
            success=True,
        )
        return locked


def serbest_birak(
    *,
    actor,
    plan: ContractReleasePlan,
    miktar: Decimal,
    donem_baslangic: date,
    donem_bitis: date,
    aciklama: str = "",
) -> ContractReleaseEvent:
    """Dönemsel miktar serbest bırakır — PriceQuote/Lock’a dokunmaz."""
    _require_manage(
        actor, action="fiyatlama.release.event_denied", entity_id=str(plan.pk)
    )
    if not isinstance(miktar, Decimal):
        miktar = Decimal(str(miktar))
    if miktar <= 0:
        raise ValidationError({"miktar": "Pozitif olmalı."})

    try:
        with domain_atomic():
            locked = ContractReleasePlan.objects.select_for_update().get(pk=plan.pk)
            if locked.durum != ContractReleasePlan.Durum.AKTIF:
                raise ValidationError("Yalnız AKTIF plandan release yapılır.")
            kalan = serbest_bakiye(locked)
            if miktar > kalan:
                raise ValidationError(
                    f"Taahhüt aşıldı: kalan={kalan}, istenen={miktar}."
                )
            event = ContractReleaseEvent(
                plan=locked,
                miktar=miktar,
                donem_baslangic=donem_baslangic,
                donem_bitis=donem_bitis,
                aciklama=aciklama or "",
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            event.save()
            record_audit(
                actor=actor,
                action="fiyatlama.release.event_created",
                entity_type="ContractReleaseEvent",
                entity_id=str(event.pk),
                success=True,
                detail={
                    "plan_id": locked.pk,
                    "miktar": str(miktar),
                    "kalan_sonra": str(serbest_bakiye(locked)),
                    "donem_baslangic": str(donem_baslangic),
                    "donem_bitis": str(donem_bitis),
                },
            )
            return event
    except Exception as exc:
        if isinstance(exc, (ValidationError, PermissionDenied)):
            raise
        record_audit_durable(
            actor=actor,
            action="fiyatlama.release.event_failed",
            entity_type="ContractReleasePlan",
            entity_id=str(plan.pk),
            success=False,
            reason=str(exc)[:255],
        )
        raise
