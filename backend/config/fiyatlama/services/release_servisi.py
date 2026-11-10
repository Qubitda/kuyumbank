"""F5-041 / F5-041b — Contract release plan + sipariş tüketimi.

PriceQuote ve PriceLock’a yazmaz; yalnız release/consumption aggregate + audit.
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
    ContractReleaseConsumption,
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


def tuketilen(plan: ContractReleasePlan) -> Decimal:
    """Net tüketim = TUKETIM − IADE (F5-041b)."""
    tuk = (
        plan.consumptions.filter(yon=ContractReleaseConsumption.Yon.TUKETIM)
        .aggregate(s=Sum("miktar"))
        .get("s")
        or Decimal("0")
    )
    iade = (
        plan.consumptions.filter(yon=ContractReleaseConsumption.Yon.IADE)
        .aggregate(s=Sum("miktar"))
        .get("s")
        or Decimal("0")
    )
    return tuk - iade


def kullanilabilir(plan: ContractReleasePlan) -> Decimal:
    """Siparişe açık miktar = serbest bırakılan − net tüketim."""
    return serbest_birakilan(plan) - tuketilen(plan)


def _aktif_plan_qs(*, alici_firma_id: int, varyant_id: int, birim: str):
    return (
        ContractReleasePlan.objects.select_for_update()
        .filter(
            durum=ContractReleasePlan.Durum.AKTIF,
            varyant_id=varyant_id,
            birim=birim,
            sozlesme__firma_id=alici_firma_id,
            sozlesme__durum=FiyatSozlesmesi.Durum.AKTIF,
            sozlesme__kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
        )
        .order_by("pk")
    )


def tuket_order_line(*, actor, order_line) -> list[ContractReleaseConsumption]:
    """AKTIF plan varsa satır miktarını FIFO tüket; yetersizse ValidationError.

    Plan yoksa no-op (sözleşme zorunlu değil). Çağıran domain_atomic içinde olmalı.
    """
    if order_line.birim not in ContractReleasePlan.Birim.values:
        return []

    plans = list(
        _aktif_plan_qs(
            alici_firma_id=order_line.order.alici_firma_id,
            varyant_id=order_line.varyant_id,
            birim=order_line.birim,
        )
    )
    if not plans:
        return []

    remaining = Decimal(order_line.miktar)
    created: list[ContractReleaseConsumption] = []
    for plan in plans:
        if remaining <= 0:
            break
        avail = kullanilabilir(plan)
        if avail <= 0:
            continue
        take = remaining if remaining <= avail else avail
        cons = ContractReleaseConsumption(
            plan=plan,
            order_line=order_line,
            yon=ContractReleaseConsumption.Yon.TUKETIM,
            miktar=take,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        cons.save()
        created.append(cons)
        remaining -= take
        record_audit(
            actor=actor,
            action="fiyatlama.release.consumed",
            entity_type="ContractReleaseConsumption",
            entity_id=str(cons.pk),
            success=True,
            detail={
                "plan_id": plan.pk,
                "order_line_id": order_line.pk,
                "miktar": str(take),
                "kullanilabilir_sonra": str(kullanilabilir(plan)),
            },
        )

    if remaining > 0:
        raise ValidationError(
            "Contract release kullanılabilir miktar yetersiz: "
            f"kalan_ihtiyaç={remaining} varyant={order_line.varyant_id} "
            f"birim={order_line.birim}."
        )
    return created


def iade_order_line(*, actor, order_line) -> list[ContractReleaseConsumption]:
    """Order iptalinde satırdaki tüm TUKETIM kayıtları için IADE yazar (idempotent)."""
    tuketimler = list(
        ContractReleaseConsumption.objects.select_for_update()
        .filter(
            order_line_id=order_line.pk,
            yon=ContractReleaseConsumption.Yon.TUKETIM,
        )
        .order_by("pk")
    )
    if not tuketimler:
        return []

    created: list[ContractReleaseConsumption] = []
    for tuketim in tuketimler:
        existing = ContractReleaseConsumption.objects.filter(
            order_line_id=order_line.pk,
            plan_id=tuketim.plan_id,
            yon=ContractReleaseConsumption.Yon.IADE,
        ).first()
        if existing is not None:
            created.append(existing)
            continue
        iade = ContractReleaseConsumption(
            plan_id=tuketim.plan_id,
            order_line=order_line,
            yon=ContractReleaseConsumption.Yon.IADE,
            miktar=tuketim.miktar,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        iade.save()
        created.append(iade)
        record_audit(
            actor=actor,
            action="fiyatlama.release.consumption_reversed",
            entity_type="ContractReleaseConsumption",
            entity_id=str(iade.pk),
            success=True,
            detail={
                "plan_id": tuketim.plan_id,
                "order_line_id": order_line.pk,
                "miktar": str(tuketim.miktar),
                "tuketim_id": tuketim.pk,
            },
        )
    return created


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
